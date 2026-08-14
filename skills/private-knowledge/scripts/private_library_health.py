from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTENT_SYSTEM_SCRIPTS = SKILL_ROOT.parent / "content-system" / "scripts"
if not CONTENT_SYSTEM_SCRIPTS.is_dir():
    raise RuntimeError(
        "private-knowledge health checks require the sibling content-system skill"
    )
sys.path.insert(0, str(CONTENT_SYSTEM_SCRIPTS))

from content_case_library import (
    build_index as build_case_index,
    load_library as load_case_library,
)
from hook_library import (
    build_index as build_hook_index,
    load_library as load_hook_library,
)
from private_library import (
    LibraryError,
    LibraryLayout,
    resolve_library_root,
    validate_library,
)
from writing_memory import discover_records, index_is_current


REPORT_SCHEMA = "100x-learning-private-library-health"
REPORT_VERSION = 1
ACTIVE_ROOTS = (
    "10-Knowledge",
    "20-Sources",
    "30-Projects",
    "40-Outputs",
    "50-Areas",
    "60-Systems",
)
WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\[\]]+)\]\]")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
PLAIN_SOURCE_RE = re.compile(r"20-Sources/[^\r\n\])>`\"']+?\.md", re.I)


class HealthError(ValueError):
    pass


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _io_path(path: Path) -> Path:
    """Return a Windows extended-length path without changing its identity."""
    resolved = str(path.resolve())
    if os.name != "nt" or resolved.startswith("\\\\?\\"):
        return Path(resolved)
    if resolved.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + resolved[2:])
    return Path("\\\\?\\" + resolved)


def _read(path: Path) -> str:
    try:
        return _io_path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise HealthError(f"无法读取 {path}：{exc}") from exc


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def _title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _identity(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value).casefold()


def _active_markdown(layout: LibraryLayout) -> list[Path]:
    paths: list[Path] = []
    for relative in ACTIVE_ROOTS:
        root = layout.root / relative
        if root.exists():
            paths.extend(root.rglob("*.md"))
    return sorted({path.resolve() for path in paths})


def _active_resources(layout: LibraryLayout) -> list[Path]:
    paths: set[Path] = set()
    for relative in ACTIVE_ROOTS:
        root = layout.root / relative
        if root.exists():
            paths.add(root.resolve())
            paths.update(path.resolve() for path in root.rglob("*"))
    if layout.home.is_file():
        paths.add(layout.home.resolve())
    return sorted(paths)


def _active_link_targets(layout: LibraryLayout) -> list[Path]:
    paths = set(_active_markdown(layout))
    if layout.home.is_file():
        paths.add(layout.home.resolve())
    return sorted(paths)


def _maps(paths: Iterable[Path], root: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    by_relative: dict[str, Path] = {}
    by_stem: dict[str, list[Path]] = {}
    for path in paths:
        relative = _relative(path, root)
        without_suffix = relative[:-3] if relative.lower().endswith(".md") else relative
        by_relative[without_suffix.casefold()] = path
        by_stem.setdefault(path.stem.casefold(), []).append(path)
    return by_relative, by_stem


def _clean_link(value: str) -> str:
    value = value.strip().strip("<>")
    value = value.split("|", 1)[0].split("#", 1)[0].strip()
    return value.replace("\\", "/")


def _resolve_wikilink(
    value: str,
    current: Path,
    root: Path,
    by_relative: dict[str, Path],
    by_stem: dict[str, list[Path]],
) -> tuple[str, Path | None]:
    target = _clean_link(value)
    if not target:
        return "ignored", None
    if target.lower().endswith(".md"):
        target = target[:-3]
    if "/" in target:
        candidates = (current.parent / target, root / target.lstrip("/"))
        for candidate in candidates:
            try:
                relative = candidate.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
            resolved = by_relative.get(relative.casefold())
            if resolved:
                return "resolved", resolved
        return "missing", None
    candidates = by_stem.get(Path(target).name.casefold(), [])
    if len(candidates) == 1:
        return "resolved", candidates[0]
    if len(candidates) > 1:
        return "ambiguous", None
    return "missing", None


def _resolve_markdown_link(
    value: str,
    current: Path,
    root: Path,
    active_resources: set[Path],
) -> tuple[str, Path | None]:
    target = _clean_link(value)
    if not target or re.match(r"^[a-z][a-z0-9+.-]*://", target, re.I):
        return "ignored", None
    candidate = Path(target)
    if candidate.is_absolute():
        candidates = (candidate.resolve(),)
    else:
        candidates = (
            (current.parent / candidate).resolve(),
            (root / candidate).resolve(),
        )
    inside_library = False
    inside_active_root = False
    for resolved in candidates:
        try:
            relative = resolved.relative_to(root.resolve())
        except ValueError:
            continue
        inside_library = True
        if relative.parts and relative.parts[0] in ACTIVE_ROOTS:
            inside_active_root = True
        if resolved in active_resources:
            return "resolved", resolved
    if inside_active_root:
        return "missing", None
    if inside_library:
        return "inactive", None
    return "ignored", None


def _is_reference_source(path: Path, layout: LibraryLayout) -> bool:
    relative = _relative(path, layout.root)
    return "Content Cases/" in relative or relative.startswith("20-Sources/Hook Library/")


def _index_issues(layout: LibraryLayout) -> list[Issue]:
    issues: list[Issue] = []
    cases, case_errors = load_case_library(layout)
    for error in case_errors:
        issues.append(Issue("error", "content_case_invalid", "20-Sources", error))
    if not case_errors:
        for asset, path in (
            ("social", layout.social_case_index),
            ("article", layout.article_case_index),
        ):
            expected = build_case_index(cases, layout, asset)
            current = _read(path) if path.exists() else ""
            if current != expected:
                issues.append(
                    Issue(
                        "warning",
                        "content_case_index_stale",
                        _relative(path, layout.root),
                        "对应成品形式的案例索引缺失或与当前案例原文不一致。",
                    )
                )

    hooks, hook_errors = load_hook_library(layout)
    for error in hook_errors:
        issues.append(Issue("error", "hook_invalid", "20-Sources/Hook Library", error))
    if not hook_errors:
        expected = build_hook_index(hooks, layout)
        current = _read(layout.hook_index) if layout.hook_index.exists() else ""
        if current != expected:
            issues.append(
                Issue(
                    "warning",
                    "hook_index_stale",
                    _relative(layout.hook_index, layout.root),
                    "钩子统一索引缺失或与当前独立钩子原文不一致。",
                )
            )

    records, _ = discover_records(layout.root)
    if not index_is_current(layout.root, records):
        issues.append(
            Issue(
                "warning",
                "writing_index_stale",
                _relative(layout.writing_index, layout.root),
                "发布历史索引缺失或与当前正式正文不一致。",
            )
        )
    return issues


def scan_library(root: Path) -> dict[str, object]:
    layout = validate_library(root)
    paths = _active_markdown(layout)
    active_resources = set(_active_resources(layout))
    active_targets = set(_active_link_targets(layout))
    by_relative, by_stem = _maps(active_targets, layout.root)
    issues: list[Issue] = []
    texts: dict[Path, str] = {}
    referenced_sources: set[Path] = set()
    knowledge_sources: set[Path] = set()
    topics: dict[str, list[Path]] = {}
    today = date.today()

    for path in paths:
        relative = _relative(path, layout.root)
        try:
            text = _read(path)
        except HealthError as exc:
            issues.append(Issue("error", "unreadable_markdown", relative, str(exc)))
            continue
        texts[path] = text
        metadata = _frontmatter(text)

        if relative.startswith("10-Knowledge/"):
            topic = metadata.get("topic") or _title(text, path)
            topics.setdefault(_identity(topic), []).append(path)

        review_by = metadata.get("review_by", "")
        if review_by:
            try:
                due = date.fromisoformat(review_by)
            except ValueError:
                issues.append(
                    Issue(
                        "warning",
                        "invalid_review_date",
                        relative,
                        f"review_by 不是有效日期：{review_by}",
                    )
                )
            else:
                if due <= today:
                    issues.append(
                        Issue(
                            "warning",
                            "review_due",
                            relative,
                            f"这份活动内容已到复核日期：{review_by}。",
                        )
                    )

        for raw_link in WIKILINK_RE.findall(text):
            state, resolved = _resolve_wikilink(
                raw_link,
                path,
                layout.root,
                by_relative,
                by_stem,
            )
            if state == "missing":
                issues.append(
                    Issue(
                        "warning",
                        "broken_wikilink",
                        relative,
                        f"找不到内部链接目标：[[{raw_link}]]。",
                    )
                )
            elif state == "ambiguous":
                issues.append(
                    Issue(
                        "warning",
                        "ambiguous_wikilink",
                        relative,
                        f"内部链接存在多个同名目标：[[{raw_link}]]。",
                    )
                )
            elif resolved and _relative(resolved, layout.root).startswith("20-Sources/"):
                referenced_sources.add(resolved.resolve())
                if relative.startswith("10-Knowledge/"):
                    knowledge_sources.add(path.resolve())

        for raw_link in MARKDOWN_LINK_RE.findall(text):
            state, resolved = _resolve_markdown_link(
                raw_link,
                path,
                layout.root,
                active_resources,
            )
            if state == "missing":
                issues.append(
                    Issue(
                        "warning",
                        "broken_local_link",
                        relative,
                        f"找不到本地链接目标：{raw_link}。",
                    )
                )
            elif state == "inactive":
                issues.append(
                    Issue(
                        "warning",
                        "inactive_local_link",
                        relative,
                        f"本地链接目标不属于活动资源：{raw_link}。",
                    )
                )
            elif (
                state == "resolved"
                and resolved is not None
                and _relative(resolved, layout.root).startswith("20-Sources/")
            ):
                referenced_sources.add(resolved.resolve())
                if relative.startswith("10-Knowledge/"):
                    knowledge_sources.add(path.resolve())

        for raw_source in PLAIN_SOURCE_RE.findall(text):
            candidate = (layout.root / _clean_link(raw_source)).resolve()
            if candidate.exists() and candidate.is_file():
                referenced_sources.add(candidate)
                if relative.startswith("10-Knowledge/"):
                    knowledge_sources.add(path.resolve())

    for identity, duplicates in topics.items():
        if identity and len(duplicates) > 1:
            locations = "、".join(_relative(path, layout.root) for path in duplicates)
            for path in duplicates:
                issues.append(
                    Issue(
                        "error",
                        "duplicate_topic",
                        _relative(path, layout.root),
                        f"主题身份与其它活动文档重复：{locations}。",
                    )
                )

    for path, text in texts.items():
        relative = _relative(path, layout.root)
        if not relative.startswith("10-Knowledge/"):
            continue
        has_external = bool(re.search(r"https?://", text))
        if not has_external and path.resolve() not in knowledge_sources:
            issues.append(
                Issue(
                    "info",
                    "knowledge_without_source",
                    relative,
                    "这份知识文档没有可见来源入口，需要人工确认它是独立知识、待补来源还是旧迁移内容。",
                )
            )

    source_paths = sorted(layout.sources.rglob("*.md"))
    for path in source_paths:
        if _is_reference_source(path, layout) or path.resolve() in referenced_sources:
            continue
        issues.append(
            Issue(
                "info",
                "unprocessed_source",
                _relative(path, layout.root),
                "这份来源尚未被任何活动知识文档引用。",
            )
        )

    try:
        issues.extend(_index_issues(layout))
    except (LibraryError, ValueError, OSError, UnicodeError) as exc:
        issues.append(Issue("error", "index_check_failed", "60-Systems", str(exc)))

    order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda item: (order[item.severity], item.code, item.path))
    summary = {
        severity: sum(issue.severity == severity for issue in issues)
        for severity in ("error", "warning", "info")
    }
    return {
        "schema": REPORT_SCHEMA,
        "version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "library_root": str(layout.root),
        "scanned": {
            "markdown": len(paths),
            "knowledge": sum(
                _relative(path, layout.root).startswith("10-Knowledge/")
                for path in paths
            ),
            "sources": len(source_paths),
        },
        "summary": summary,
        "issues": [asdict(issue) for issue in issues],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="只读检查 100x-learning 私人知识库健康状态")
    parser.add_argument("--library-root", type=Path, help="私人知识库根目录")
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    parser.add_argument(
        "--fail-on",
        choices=("never", "error", "warning"),
        default="never",
        help="报告成功生成后，按问题严重度决定退出状态",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = resolve_library_root(args.library_root, args.config)
        report = scan_library(root)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        summary = report["summary"]
        if args.fail_on == "error" and summary["error"]:
            return 2
        if args.fail_on == "warning" and (summary["error"] or summary["warning"]):
            return 2
        return 0
    except (HealthError, LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
