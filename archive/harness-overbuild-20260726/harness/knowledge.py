from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from .result import ValidationReport


KNOWLEDGE_STATUSES = {"active", "review"}
REQUIRED_FRONTMATTER = {"type", "status", "created", "updated", "topic", "aliases"}
GENERIC_TITLES = {
    "readme",
    "temp",
    "temporary",
    "untitled",
    "newnote",
    "未命名",
    "临时",
    "新建笔记",
    "知识笔记",
}
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


def _plain_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, str | None]:
    """Parse the flat frontmatter shape used by knowledge notes.

    The knowledge contract intentionally uses only scalar fields and string lists,
    so the harness does not need a second YAML implementation or dependency.
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, "缺少起始 frontmatter 分隔线"

    try:
        end_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        return {}, text, "frontmatter 缺少结束分隔线"

    data: dict[str, Any] = {}
    current_list: str | None = None
    for index, raw_line in enumerate(lines[1:end_index], start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            item = raw_line.strip()
            if current_list and item.startswith("- "):
                value = _plain_scalar(item[2:])
                if value:
                    data[current_list].append(value)
                continue
            return {}, text, f"frontmatter 第 {index} 行不是支持的字符串列表"
        if ":" not in raw_line:
            return {}, text, f"frontmatter 第 {index} 行缺少冒号"
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            return {}, text, f"frontmatter 第 {index} 行缺少字段名"
        if key in data:
            return {}, text, f"frontmatter 字段重复：{key}"
        value = raw_value.strip()
        if value == "":
            data[key] = []
            current_list = key
        elif value == "[]":
            data[key] = []
            current_list = None
        else:
            data[key] = _plain_scalar(value)
            current_list = None

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return data, body, None


def knowledge_note_terms(path: Path) -> list[str]:
    """Return exact terms that can identify a canonical knowledge note."""

    terms = [path.stem]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return terms
    frontmatter, _, error = parse_frontmatter(text)
    if error:
        return terms
    topic = frontmatter.get("topic")
    if isinstance(topic, str) and topic.strip():
        terms.append(topic.strip())
    aliases = frontmatter.get("aliases")
    if isinstance(aliases, list):
        terms.extend(alias.strip() for alias in aliases if isinstance(alias, str) and alias.strip())
    return terms


def _valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _normalized_title(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _section_body(body: str, match: re.Match[str], next_start: int) -> str:
    return body[match.end() : next_start].strip()


def _resolve_wiki_link(kb_root: Path, target: str) -> list[Path]:
    target = target.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")
    if not target or "://" in target:
        return []
    if target.startswith("System Knowledge/"):
        target = target.removeprefix("System Knowledge/")
    if "/" in target:
        candidate = kb_root / target
        if candidate.suffix.lower() != ".md":
            candidate = Path(f"{candidate}.md")
        return [candidate] if candidate.is_file() else []
    return sorted(path for path in kb_root.rglob("*.md") if path.stem == target)


def validate_knowledge_note(note_path: Path, kb_root: Path) -> ValidationReport:
    """Validate a persisted 10-Knowledge note against Home.md's contract."""

    report = ValidationReport()
    kb_root = kb_root.resolve()
    note_path = note_path.resolve()
    knowledge_root = (kb_root / "10-Knowledge").resolve()

    try:
        note_path.relative_to(knowledge_root)
    except ValueError:
        report.error(
            "note.outside_knowledge",
            "validate-note 只校验 System Knowledge/10-Knowledge 内的文档",
            str(note_path),
        )
        return report
    if note_path.suffix.lower() != ".md":
        report.error("note.not_markdown", "知识文档必须使用 .md 扩展名", str(note_path))
        return report
    if not note_path.is_file():
        report.error("note.missing", "知识文档不存在", str(note_path))
        return report

    try:
        text = note_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        report.error("note.unreadable", str(exc), str(note_path))
        return report

    frontmatter, body, parse_error = parse_frontmatter(text)
    if parse_error:
        report.error("note.invalid_frontmatter", parse_error, str(note_path))
        return report

    for field in sorted(REQUIRED_FRONTMATTER - frontmatter.keys()):
        report.error("note.missing_frontmatter_field", f"缺少必需字段：{field}", field)
    if frontmatter.get("type") != "knowledge-note":
        report.error("note.invalid_type", "type 必须是 knowledge-note", "type")
    if frontmatter.get("status") not in KNOWLEDGE_STATUSES:
        report.error(
            "note.invalid_status",
            "10-Knowledge 中的 status 必须是 active 或 review",
            "status",
        )
    for field in ("created", "updated"):
        if not _valid_iso_date(frontmatter.get(field)):
            report.error("note.invalid_date", "必须是 YYYY-MM-DD 日期", field)
    if _valid_iso_date(frontmatter.get("created")) and _valid_iso_date(frontmatter.get("updated")):
        if date.fromisoformat(frontmatter["updated"]) < date.fromisoformat(frontmatter["created"]):
            report.error("note.updated_before_created", "updated 不能早于 created", "updated")
    topic = frontmatter.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        report.error("note.invalid_topic", "topic 必须是稳定的非空主题标识", "topic")
    aliases = frontmatter.get("aliases")
    if not isinstance(aliases, list) or not all(
        isinstance(alias, str) and alias.strip() for alias in aliases
    ):
        report.error("note.invalid_aliases", "aliases 必须是字符串数组，可以为空", "aliases")
        aliases = []

    h1_matches = list(H1_RE.finditer(body))
    if len(h1_matches) != 1:
        report.error("note.h1_count", "知识文档必须且只能有一个一级标题", str(note_path))
        title = ""
    else:
        title = h1_matches[0].group(1).strip()
        if title != note_path.stem:
            report.error("note.title_filename_mismatch", "一级标题必须与文件名一致", title)
        if _normalized_title(title) in GENERIC_TITLES:
            report.error("note.generic_title", "标题不能使用未命名、Temp 或 README 等占位名称", title)

        first_h2 = H2_RE.search(body, h1_matches[0].end())
        scope_end = first_h2.start() if first_h2 else len(body)
        scope = body[h1_matches[0].end() : scope_end].strip()
        scope_lines = [line.strip() for line in scope.splitlines() if line.strip()]
        if not scope_lines or len("".join(scope_lines)) < 12 or scope_lines[0].startswith(("-", "*", "|")):
            report.error(
                "note.missing_scope",
                "一级标题后必须先用完整文字说明文档回答什么问题和当前判断",
                title,
            )

    if isinstance(aliases, list):
        normalized_terms = [_normalized_title(value) for value in [title, *aliases] if value]
        if len(normalized_terms) != len(set(normalized_terms)):
            report.warning("note.duplicate_term", "标题、topic 或 aliases 中存在重复检索词", "aliases")

    h2_matches = list(H2_RE.finditer(body))
    if not h2_matches:
        report.error("note.missing_sections", "知识文档至少需要一个二级章节", str(note_path))
    section_titles: list[str] = []
    for index, match in enumerate(h2_matches):
        title_text = match.group(1).strip()
        section_titles.append(title_text)
        next_start = h2_matches[index + 1].start() if index + 1 < len(h2_matches) else len(body)
        if not _section_body(body, match, next_start):
            report.error("note.empty_section", "二级章节不能为空", title_text)

    if not any(
        keyword in heading.casefold()
        for heading in section_titles
        for keyword in ("来源", "证据", "原始材料", "source", "evidence", "provenance")
    ):
        report.error(
            "note.missing_provenance",
            "知识文档必须有来源或证据章节，说明认识从哪里来",
            str(note_path),
        )
    if not any(
        keyword in heading.casefold()
        for heading in section_titles
        for keyword in (
            "边界",
            "限制",
            "开放问题",
            "暂不采用",
            "boundary",
            "boundaries",
            "limitation",
            "open question",
            "rejected",
        )
    ):
        report.error(
            "note.missing_boundaries",
            "知识文档必须记录适用边界、开放问题或暂不采用的主张",
            str(note_path),
        )

    broken_links: list[str] = []
    ambiguous_links: list[str] = []
    for raw_target in WIKI_LINK_RE.findall(body):
        clean_target = raw_target.split("|", 1)[0].split("#", 1)[0].strip()
        if not clean_target:
            continue
        matches = _resolve_wiki_link(kb_root, raw_target)
        if not matches:
            broken_links.append(clean_target)
        elif "/" not in clean_target.replace("\\", "/") and len(matches) > 1:
            ambiguous_links.append(clean_target)
    for target in sorted(set(broken_links)):
        report.error("note.broken_wiki_link", "Obsidian 链接找不到目标", target)
    for target in sorted(set(ambiguous_links)):
        report.warning("note.ambiguous_wiki_link", "短链接对应多个文件，建议写完整路径", target)

    report.details.update(
        {
            "path": str(note_path.relative_to(kb_root)),
            "title": title,
            "topic": topic,
            "aliases": aliases,
            "section_count": len(h2_matches),
            "wiki_link_count": len(WIKI_LINK_RE.findall(body)),
        }
    )
    return report
