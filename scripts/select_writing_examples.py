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


def _source_rank(
    component: str,
    source_id: str,
    form: str,
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
    used: set[str],
) -> tuple[int, int, int]:
    prefix = component[0]
    duplicate_penalty = 1 if source_id in used else 0
    if source_id in hooks:
        hook = hooks[source_id]
        if source_id.startswith("short-hook-human-"):
            source_kind = 0
        elif prefix == "H":
            source_kind = 2
        else:
            source_kind = 6
        return source_kind, duplicate_penalty, len(hook.text)

    case = cases[source_id]
    if prefix == "H":
        if form in {"article", "newsletter"}:
            source_kind = 1 if case.asset == "article" else 3
        else:
            source_kind = 1 if case.asset == "social" else 4
    elif prefix == "S":
        source_kind = 0 if case.asset == "article" else 3
    elif form in {"article", "newsletter"}:
        source_kind = 0 if case.asset == "article" else 2
    else:
        source_kind = 0 if case.asset == "social" else 2
    return source_kind, duplicate_penalty, len(case.original_text)


def select_sources(
    components: Iterable[str],
    mapping: dict[str, list[str]],
    cases: dict[str, ContentCase],
    hooks: dict[str, HookExample],
    form: str,
) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    used: set[str] = set()
    known_sources = set(cases) | set(hooks)
    for component in components:
        if not EXAMPLE_COMPONENT_PATTERN.fullmatch(component):
            raise ValueError(f"无效组件 ID：{component}")
        if component.startswith("S") and form not in {"article", "newsletter"}:
            raise ValueError(f"{form} 形式不能为章节组件 {component} 取例")
        candidates = [source_id for source_id in mapping.get(component, ()) if source_id in known_sources]
        if not candidates:
            raise ValueError(f"{component} 没有可读取的活动模仿来源")
        source_id = min(
            candidates,
            key=lambda candidate: _source_rank(component, candidate, form, cases, hooks, used),
        )
        selected.append((component, source_id))
        used.add(source_id)
    return selected


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="为独立写作组件选择完整真实模仿例子")
    parser.add_argument("components", nargs="+", help="组件 ID，例如 H02 P24 E04；文章可再加入 S01")
    parser.add_argument(
        "--form",
        choices=("short", "thread", "article", "newsletter"),
        default="short",
        help="目标内容形态",
    )
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE, help="组件来源覆盖账本")
    parser.add_argument("--library-root", type=Path, help="私人知识库根目录")
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    return parser


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
        selected = select_sources(args.components, mapping, cases, hooks, args.form)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(render_examples(selected, cases, hooks), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
