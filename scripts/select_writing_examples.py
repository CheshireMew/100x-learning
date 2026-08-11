from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

try:
    from scripts.content_case_library import ContentCase, load_library as load_cases
    from scripts.hook_library import HookExample, load_library as load_hooks
    from scripts.private_library import resolve_library_root, validate_library
except ModuleNotFoundError:
    from content_case_library import ContentCase, load_library as load_cases
    from hook_library import HookExample, load_library as load_hooks
    from private_library import resolve_library_root, validate_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COVERAGE = PROJECT_ROOT / "references" / "writing-template-coverage.md"
COMPONENT_PATTERN = re.compile(r"^[HCPBES]\d{2}$")
EXAMPLE_COMPONENT_PATTERN = re.compile(r"^[HPES]\d{2}$")
SOURCE_PATTERN = re.compile(r"case-[0-9a-f]+|(?:short|thread)-hook-[0-9a-z-]+")


def _append_unique(mapping: dict[str, list[str]], component: str, source_id: str) -> None:
    if source_id not in mapping[component]:
        mapping[component].append(source_id)


def load_component_sources(path: Path) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        columns = line.split("|")
        if len(columns) < 5:
            continue
        first = columns[1].strip().strip("`")
        if SOURCE_PATTERN.fullmatch(first):
            for component in re.findall(r"[HCPBES]\d{2}", columns[3]):
                _append_unique(mapping, component, first)
            continue
        if COMPONENT_PATTERN.fullmatch(first):
            for source_id in SOURCE_PATTERN.findall(columns[2]):
                _append_unique(mapping, first, source_id)
    return dict(mapping)


def _validate_component(component: str, form: str) -> None:
    if not EXAMPLE_COMPONENT_PATTERN.fullmatch(component):
        raise ValueError(f"无效组件 ID：{component}")
    if component.startswith("S") and form not in {"article", "newsletter"}:
        raise ValueError(f"{form} 形式不能为章节组件 {component} 取例")


def list_candidates(
    components: Iterable[str],
    mapping: dict[str, list[str]],
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
    form: str,
) -> list[tuple[str, list[str]]]:
    listed: list[tuple[str, list[str]]] = []
    known_sources = set(cases) | set(hooks)
    for component in components:
        _validate_component(component, form)
        candidates = [source_id for source_id in mapping.get(component, ()) if source_id in known_sources]
        listed.append((component, candidates))
    return listed


def validate_selections(
    selected: Iterable[tuple[str, str]],
    mapping: dict[str, list[str]],
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
    form: str,
) -> list[tuple[str, str]]:
    validated: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    known_sources = set(cases) | set(hooks)
    for component, source_id in selected:
        _validate_component(component, form)
        selection = (component, source_id)
        if selection in seen:
            raise ValueError(f"模仿来源重复选择：{component}={source_id}")
        if source_id not in known_sources:
            raise ValueError(f"{source_id} 不是可读取的活动模仿来源")
        if source_id not in mapping.get(component, ()):
            raise ValueError(f"{source_id} 没有被覆盖账本映射到 {component}")
        validated.append(selection)
        seen.add(selection)
    return validated


def _source_summary(
    source_id: str,
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
) -> tuple[str, str]:
    if source_id in cases:
        source = cases[source_id]
        kind = "完整社交案例" if source.asset == "social" else "完整文章案例"
        return kind, source.title
    source = hooks[source_id]
    return "完整钩子案例", source.title


def render_candidates(
    candidates: Iterable[tuple[str, list[str]]],
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
) -> str:
    blocks: list[str] = []
    for component, source_ids in candidates:
        lines = [f"## {component} 可选模仿来源"]
        if not source_ids:
            lines.append("- 没有活动候选；直接省略这个组件的模仿例子")
        for source_id in source_ids:
            kind, title = _source_summary(source_id, cases, hooks)
            lines.append(f"- `{source_id}` · {kind} · {title}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def render_examples(
    selected: Iterable[tuple[str, str]],
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
) -> str:
    blocks: list[str] = []
    for component, source_id in selected:
        if source_id in cases:
            source = cases[source_id]
            title = source.title
            kind = "完整社交案例" if source.asset == "social" else "完整文章案例"
            body = source.original_text.strip()
        else:
            source = hooks[source_id]
            title = source.title
            kind = "完整钩子案例"
            body = source.text.strip()
        blocks.append(
            f"## {component} 模仿例子\n\n"
            f"来源：`{source_id}` · {kind} · {title}\n\n"
            f"{body}"
        )
    return "\n\n".join(blocks) + "\n"


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--form",
        choices=("short", "thread", "article", "newsletter"),
        default="short",
        help="目标内容形态",
    )
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE, help="组件来源覆盖账本")
    parser.add_argument("--library-root", type=Path, help="私人知识库根目录")
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="查看候选来源并完整读取显式选择的候选例子")
    commands = parser.add_subparsers(dest="command", required=True)

    candidates = commands.add_parser("candidates", help="列出组件的全部活动候选标题，不自动选择")
    candidates.add_argument("components", nargs="+", help="组件 ID，例如 H23 P01 E04")
    _add_source_arguments(candidates)

    render = commands.add_parser("render", help="完整读取显式指定的候选；同一组件可比较多个来源")
    render.add_argument(
        "selections",
        nargs="+",
        help="组件与来源，例如 H02=short-hook-human-01 H02=case-1234 P01=case-5678",
    )
    _add_source_arguments(render)
    return parser


def parse_selections(values: Iterable[str]) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    for value in values:
        component, separator, source_id = value.partition("=")
        if not separator or not component or not source_id:
            raise ValueError(f"选择格式无效：{value}；应写成 Hxx=source-id")
        selected.append((component, source_id))
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    library_root = args.library_root or resolve_library_root(config_path=args.config)
    layout = validate_library(library_root)
    case_records, case_issues = load_cases(layout)
    hook_records, hook_issues = load_hooks(layout)
    if case_issues or hook_issues:
        issues = "\n".join((*case_issues, *hook_issues))
        raise SystemExit(f"私人写作语料未通过读取检查：\n{issues}")
    cases = {record.case_id: record for record in case_records}
    hooks = {record.hook_id: record for record in hook_records}
    mapping = load_component_sources(args.coverage)
    try:
        if args.command == "candidates":
            candidates = list_candidates(args.components, mapping, cases, hooks, args.form)
            output = render_candidates(candidates, cases, hooks)
        else:
            requested = parse_selections(args.selections)
            selected = validate_selections(requested, mapping, cases, hooks, args.form)
            output = render_examples(selected, cases, hooks)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
