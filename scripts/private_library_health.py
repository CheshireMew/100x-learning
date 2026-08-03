from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from scripts.content_case_library import build_index, load_library
    from scripts.private_library import (
        LibraryError,
        LibraryLayout,
        resolve_library_root,
        validate_library,
    )
    from scripts.writing_memory import discover_records, index_is_current
except ModuleNotFoundError:
    from content_case_library import build_index, load_library
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


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
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


def _link_targets(layout: LibraryLayout) -> list[Path]:
    return sorted(
        path.resolve()
        for path in layout.root.rglob("*.md")
        if ".git" not in path.relative_to(layout.root).parts
    )


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


def _resolve_markdown_link(value: str, current: Path, root: Path) -> Path | None:
    target = _clean_link(value)
    if not target or re.match(r"^[a-z][a-z0-9+.-]*://", target, re.I):
        return None
    candidate = Path(target)
    if candidate.is_absolute():
        return candidate.resolve()
    local = (current.parent / candidate).resolve()
    if local.exists():
        return local
    return (root / candidate).resolve()


def _is_case_source(path: Path, layout: LibraryLayout) -> bool:
    relative = _relative(path, layout.root)
    return "Content Cases/" in relative


def _index_issues(layout: LibraryLayout) -> list[Issue]:
    issues: list[Issue] = []
    cases, case_errors = load_library(layout)
    for error in case_errors:
        issues.append(Issue("error", "content_case_invalid", "20-Sources", error))
    if cases and not case_errors:
        expected = build_index(cases, layout)
        current = _read(layout.case_index) if layout.case_index.exists() else ""
        if current != expected:
            issues.append(
                Issue(
                    "warning",
                    "content_case_index_stale",
                    _relative(layout.case_index, layout.root),
                    "内容案例索引缺失或与当前案例原文不一致。",
                )
            )

    records, _ = discover_records(layout.root)
    if records and not index_is_current(layout.root, records):
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
    by_relative, by_stem = _maps(_link_targets(layout), layout.root)
    issues: list[Issue] = []
    texts: dict[Path, str] = {}
    referenced_sources: set[Path] = set()
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

        for raw_link in MARKDOWN_LINK_RE.findall(text):
            resolved = _resolve_markdown_link(raw_link, path, layout.root)
            if resolved is None:
                continue
            try:
                resolved.relative_to(layout.root.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                issues.append(
                    Issue(
                        "warning",
                        "broken_local_link",
                        relative,
                        f"找不到本地链接目标：{raw_link}。",
                    )
                )
            elif _relative(resolved, layout.root).startswith("20-Sources/"):
                referenced_sources.add(resolved.resolve())

        for raw_source in PLAIN_SOURCE_RE.findall(text):
            candidate = (layout.root / _clean_link(raw_source)).resolve()
            if candidate.exists() and candidate.is_file():
                referenced_sources.add(candidate)

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
        has_source_path = "20-Sources/" in text.replace("\\", "/")
        if not has_external and not has_source_path:
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
        if _is_case_source(path, layout) or path.resolve() in referenced_sources:
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
