from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOCIAL_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Social Posts"
    / "Content Cases"
)
ARTICLE_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Articles"
    / "Cheshire"
    / "Blog"
)
INDEX_ROOT = PROJECT_ROOT / "System Knowledge" / "20-Sources" / "Content Cases"
INDEX_PATH = INDEX_ROOT / "内容案例索引.md"

ASSET_DIRECTORIES = {"钩子与开头": "hook", "完整短内容": "short"}
ASSET_LABELS = {
    "hook": "钩子与开头",
    "short": "完整短内容",
    "article": "完整文章",
}
MIN_RELEVANCE = 0.4
MAX_QUERY_TERMS_FOR_COVERAGE = 24
CONTENT_TYPE_ORDER = {
    "hook": ["反常识钩子", "痛点钩子", "结果钩子", "问题钩子"],
    "short": [
        "项目与产品介绍",
        "概念与机制解释",
        "教程与操作指南",
        "清单与资源推荐",
        "事件与商业故事",
        "观点与趋势判断",
        "行业与投资分析",
        "个人观察与实测",
    ],
    "article": [
        "项目与产品介绍",
        "概念与机制解释",
        "教程与操作指南",
        "清单与资源推荐",
        "事件与商业故事",
        "观点与趋势判断",
        "行业与投资分析",
        "个人观察与实测",
    ],
}


class CaseError(ValueError):
    pass


@dataclass(frozen=True)
class ContentCase:
    path: Path
    asset: str
    content_type: str
    title: str
    index_task: str
    index_topics: tuple[str, ...]
    index_moves: tuple[str, ...]
    original_text: str
    source: str
    hook_family: str | None = None
    hook_techniques: tuple[str, ...] = ()
    reader_effects: tuple[str, ...] = ()
    required_material: tuple[str, ...] = ()
    authorship: str | None = None

    @property
    def supports_hook(self) -> bool:
        return bool(
            self.hook_family
            and self.hook_techniques
            and self.reader_effects
            and self.required_material
        )


@dataclass(frozen=True)
class SearchHit:
    case: ContentCase
    matched_asset: str
    score: float


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def _parse_list(value: str, field: str) -> tuple[str, ...]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        raise CaseError(f"{field} 必须使用单行数组")
    try:
        items = next(csv.reader([value[1:-1]], skipinitialspace=True))
    except (csv.Error, StopIteration) as exc:
        raise CaseError(f"{field} 无法解析") from exc
    result = tuple(_strip_quotes(item) for item in items if _strip_quotes(item))
    if not result:
        raise CaseError(f"{field} 不能为空")
    return result


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise CaseError("缺少 frontmatter")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise CaseError("frontmatter 缺少结束标记") from exc

    values: dict[str, str] = {}
    for raw_line in lines[1:end]:
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            raise CaseError(f"无法解析 frontmatter：{raw_line}")
        key, value = raw_line.split(":", 1)
        values[key.strip()] = value.strip()
    return values, "\n".join(lines[end + 1 :]).lstrip()


def _parse_case_index(text: str) -> tuple[dict[str, str], str]:
    pattern = re.compile(
        r"\n?<!-- content-case-index\s*\n(?P<metadata>.*?)\n-->\s*$",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise CaseError("缺少 content-case-index")

    values: dict[str, str] = {}
    for raw_line in match.group("metadata").splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            raise CaseError(f"无法解析 content-case-index：{raw_line}")
        key, value = raw_line.split(":", 1)
        values[key.strip()] = value.strip()
    return values, text[: match.start()].rstrip()


def _required(metadata: dict[str, str], key: str) -> str:
    value = _strip_quotes(metadata.get(key, ""))
    if not value:
        raise CaseError(f"缺少 {key}")
    return value


def _metadata_list(metadata: dict[str, str], key: str) -> tuple[str, ...]:
    if key not in metadata:
        raise CaseError(f"缺少 {key}")
    return _parse_list(metadata[key], key)


def _hook_metadata(
    metadata: dict[str, str],
    *,
    required: bool,
    default_family: str | None = None,
) -> tuple[str | None, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    list_fields = ("hook_techniques", "reader_effects", "required_material")
    present = [key for key in list_fields if key in metadata]
    family = _strip_quotes(metadata.get("hook_family", "")) or default_family

    if not present:
        if required:
            raise CaseError("开头案例缺少 hook_techniques、reader_effects 和 required_material")
        if "hook_family" in metadata:
            raise CaseError("只有 hook_family，缺少完整的开头元数据")
        return None, (), (), ()

    if len(present) != len(list_fields):
        missing = "、".join(key for key in list_fields if key not in metadata)
        raise CaseError(f"开头元数据不完整，缺少 {missing}")
    if not family:
        raise CaseError("提供开头元数据时必须填写 hook_family")

    return (
        family,
        _metadata_list(metadata, "hook_techniques"),
        _metadata_list(metadata, "reader_effects"),
        _metadata_list(metadata, "required_material"),
    )


def _title(body: str) -> tuple[str, int]:
    match = re.search(r"^# (.+?)\s*$", body, re.MULTILINE)
    if not match:
        raise CaseError("缺少一级标题")
    return match.group(1).strip(), match.end()


def _section(body: str, heading: str, next_heading: str | None = None) -> str:
    start = re.search(rf"^## {re.escape(heading)}\s*$", body, re.MULTILINE)
    if not start:
        raise CaseError(f"缺少“{heading}”")
    end = (
        re.search(
            rf"^## {re.escape(next_heading)}\s*$",
            body[start.end() :],
            re.MULTILINE,
        )
        if next_heading
        else None
    )
    stop = start.end() + end.start() if end else len(body)
    return body[start.end() : stop].strip()


def _check_text(original: str) -> None:
    if not original:
        raise CaseError("正文全文不能为空")


def _source_from_social_body(body: str) -> tuple[str, str]:
    source_matches = list(
        re.finditer(r"^(?:原帖链接|来源)：\s*(.+?)\s*$", body, re.MULTILINE)
    )
    if not source_matches:
        raise CaseError("缺少原帖链接或来源说明")
    match = source_matches[-1]
    source = match.group(1).strip()
    visible = (body[: match.start()] + body[match.end() :]).strip()
    return source, visible


def _parse_social(path: Path) -> ContentCase:
    relative = path.relative_to(SOCIAL_ROOT)
    if len(relative.parts) != 3:
        raise CaseError("案例必须放在“成品形态/内容类型/文件”三级路径")
    asset_directory, content_type, _ = relative.parts
    asset = ASSET_DIRECTORIES.get(asset_directory)
    if asset is None:
        raise CaseError("未知的成品形态目录")

    metadata, body = _parse_case_index(path.read_text(encoding="utf-8-sig"))
    title, _ = _title(body)
    source, original = _source_from_social_body(_section(body, "原帖全文"))
    _check_text(original)
    hook_family, hook_techniques, reader_effects, required_material = (
        _hook_metadata(
            metadata,
            required=asset == "hook",
            default_family=content_type if asset == "hook" else None,
        )
    )

    return ContentCase(
        path=path,
        asset=asset,
        content_type=content_type,
        title=title,
        index_task=_required(metadata, "index_task"),
        index_topics=_metadata_list(metadata, "index_topics"),
        index_moves=_metadata_list(metadata, "index_moves"),
        original_text=original,
        source=source,
        hook_family=hook_family,
        hook_techniques=hook_techniques,
        reader_effects=reader_effects,
        required_material=required_material,
    )


def _parse_article(path: Path) -> ContentCase:
    article_metadata, indexed_body = _parse_frontmatter(
        path.read_text(encoding="utf-8-sig")
    )
    metadata, body = _parse_case_index(indexed_body)
    if _strip_quotes(metadata.get("reference_value", "")) != "case":
        raise CaseError("这篇文章没有标记为活动案例")
    title, title_end = _title(body)
    original = body[title_end:].strip()
    _check_text(original)
    hook_family, hook_techniques, reader_effects, required_material = (
        _hook_metadata(metadata, required=False)
    )

    return ContentCase(
        path=path,
        asset="article",
        content_type=_required(article_metadata, "content_type"),
        title=title,
        index_task=_required(metadata, "index_task"),
        index_topics=_metadata_list(metadata, "index_topics"),
        index_moves=_metadata_list(metadata, "index_moves"),
        original_text=original,
        source=_required(article_metadata, "source_url"),
        hook_family=hook_family,
        hook_techniques=hook_techniques,
        reader_effects=reader_effects,
        required_material=required_material,
        authorship=_required(article_metadata, "authorship"),
    )


def _article_is_case(path: Path) -> bool:
    return "<!-- content-case-index" in path.read_text(encoding="utf-8-sig")


def _case_paths() -> list[Path]:
    social = [
        path
        for directory in ASSET_DIRECTORIES
        for path in (SOCIAL_ROOT / directory).rglob("*.md")
    ]
    articles = [
        path
        for path in ARTICLE_ROOT.glob("*.md")
        if _article_is_case(path)
    ]
    return sorted([*social, *articles])


def load_library() -> tuple[list[ContentCase], list[str]]:
    cases: list[ContentCase] = []
    issues: list[str] = []
    source_paths: dict[str, Path] = {}
    for path in _case_paths():
        try:
            case = (
                _parse_article(path)
                if path.is_relative_to(ARTICLE_ROOT)
                else _parse_social(path)
            )
        except (CaseError, OSError, UnicodeError) as exc:
            issues.append(f"{path}: {exc}")
            continue
        if re.match(r"https?://", case.source):
            previous = source_paths.get(case.source)
            if previous is not None:
                issues.append(f"{path}: 来源链接与 {previous} 重复")
                continue
            source_paths[case.source] = path
        cases.append(case)
    if not cases:
        issues.append("没有找到活动案例")
    return cases, issues


def _terms(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", value).lower()
    terms = set(re.findall(r"[a-z0-9][a-z0-9._+-]*", normalized))
    for sequence in re.findall(r"[\u3400-\u9fff]+", normalized):
        terms.add(sequence)
        if len(sequence) == 1:
            terms.add(sequence)
        else:
            terms.update(
                sequence[index : index + 2]
                for index in range(len(sequence) - 1)
            )
    return terms


def _coverage(query: str, candidates: Iterable[str]) -> float:
    query_terms = _terms(query)
    if not query_terms:
        return 0.0
    candidate_text = " ".join(candidates)
    candidate_terms = _terms(candidate_text)
    denominator = min(len(query_terms), MAX_QUERY_TERMS_FOR_COVERAGE)
    score = len(query_terms & candidate_terms) / denominator
    normalized_query = unicodedata.normalize("NFKC", query).lower().strip()
    if normalized_query and normalized_query in candidate_text.lower():
        score += 0.35
    return score


def _score_content(case: ContentCase, query: str) -> float:
    score = _coverage(query, (case.title, case.index_task)) * 7
    score += _coverage(query, case.index_moves) * 5
    score += _coverage(query, case.index_topics) * 2
    score += _coverage(query, _content_style_terms(case.original_text)) * 8
    score += _coverage(query, (case.original_text,)) * 0.5
    return score


def _content_style_terms(original_text: str) -> tuple[str, ...]:
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", original_text)
        if paragraph.strip()
    ]
    lines = [line.strip() for line in original_text.splitlines() if line.strip()]
    has_list = any(
        bool(re.match(r"^(?:[-*•]|\d+[.)、])\s*", line))
        for line in lines
    )

    terms: list[str] = []
    if len(paragraphs) <= 6 and len(original_text) <= 500:
        terms.extend(("短篇", "短内容", "很短", "快速收束", "迅速收束"))
    if has_list:
        terms.extend(("列表", "列点", "并列事实", "具体事实"))
    return tuple(terms)


def _score_hook(case: ContentCase, query: str) -> float:
    score = _coverage(query, case.hook_techniques) * 8
    score += _coverage(query, case.reader_effects) * 6
    score += _coverage(query, case.required_material) * 5
    score += _coverage(query, (case.hook_family or "",)) * 4
    score += _coverage(query, case.index_moves) * 3
    score += _coverage(query, (case.index_task,))
    return score


def _supports_asset(case: ContentCase, asset: str) -> bool:
    if asset == "hook":
        return case.supports_hook
    return case.asset == asset


def _score_for_asset(case: ContentCase, query: str, asset: str) -> float:
    if asset == "hook":
        return _score_hook(case, query)
    return _score_content(case, query)


def search_library(
    query: str,
    assets: Sequence[str],
    content_type: str | None,
    limit: int,
) -> tuple[list[SearchHit], list[str]]:
    selected_assets = tuple(dict.fromkeys(assets))
    invalid = sorted(set(selected_assets) - set(ASSET_LABELS))
    if invalid:
        raise CaseError("asset 只能是 hook、short 或 article")
    if not selected_assets:
        raise CaseError("至少选择一种 asset")
    if limit < 1:
        raise CaseError("limit 必须大于 0")

    cases, issues = load_library()
    ranked: dict[str, list[SearchHit]] = {}
    for asset in selected_assets:
        hits = []
        for case in cases:
            if not _supports_asset(case, asset):
                continue
            relevance = _score_for_asset(case, query, asset)
            if relevance < MIN_RELEVANCE:
                continue
            preferred_type_bonus = (
                2.0
                if content_type
                and asset != "hook"
                and case.content_type == content_type
                else 0.0
            )
            hits.append(
                SearchHit(case, asset, relevance + preferred_type_bonus)
            )
        hits.sort(key=lambda hit: (-hit.score, hit.case.title))
        ranked[asset] = hits
        if not ranked[asset]:
            issues.append(f"没有足够贴合的{ASSET_LABELS[asset]}案例")

    selected: list[SearchHit] = []
    used: set[tuple[Path, str]] = set()
    for asset in selected_assets:
        if ranked[asset]:
            selected.append(ranked[asset][0])
            used.add(
                (
                    ranked[asset][0].case.path,
                    ranked[asset][0].matched_asset,
                )
            )
    remaining = sorted(
        (
            hit
            for asset in selected_assets
            for hit in ranked[asset]
            if (hit.case.path, hit.matched_asset) not in used
        ),
        key=lambda hit: (
            -hit.score,
            selected_assets.index(hit.matched_asset),
            hit.case.title,
        ),
    )
    effective_limit = max(limit, len(selected))
    selected.extend(remaining[: effective_limit - len(selected)])
    if not selected:
        raise CaseError("没有可读取的案例")
    return selected, issues


def render_search_results(hits: Sequence[SearchHit]) -> str:
    lines = [
        f"# 内容案例候选（{len(hits)} 条）",
        "",
        "原文是主要写作输入。先完整阅读它怎样措辞、换行、递进、制造情绪和收束，再把能成立的整套写法映射到本次事实。路径和匹配角色只说明案例从哪里被找到，不限制它能用于什么题材，也不代表只能学习某一项技巧。",
        "",
    ]
    for index, hit in enumerate(hits, start=1):
        case = hit.case
        lines.extend(
            [
                f"## {index}. {case.title}",
                "",
                "### 原文全文",
                "",
                case.original_text,
                "",
                f"来源：{case.source}",
                "",
                "### 检索记录",
                "",
                f"- 本地路径：{case.path}",
                f"- 本次匹配角色：{ASSET_LABELS[hit.matched_asset]}",
            ]
        )
        if case.authorship:
            lines.append(f"- 来源性质：{case.authorship}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_index(cases: Sequence[ContentCase]) -> str:
    counts = {
        asset: sum(_supports_asset(case, asset) for case in cases)
        for asset in ASSET_LABELS
    }
    lines = [
        "# 内容案例索引",
        "",
        "这是给人浏览的统一索引。目录、成品类型、主题和技巧都只负责帮助找到候选，不限制案例的表达方法可以迁移到什么题材。",
        "",
        f"当前共有 {len(cases)} 条案例：{counts['hook']} 条钩子与开头，{counts['short']} 条完整短内容，{counts['article']} 篇完整文章。",
        "",
        "案例原文只保存一份：开头和短内容位于 `../Social Posts/Content Cases/`；文章位于 `../Articles/Cheshire/Blog/`。完整案例声明开头元数据后可以同时承担开头角色，不复制原文。",
        "",
        "文章库不等于文章案例库。只有正文写法本身提供了现有案例没有的可复用方法，才标记为案例；其它文章继续留在原目录作为归档。",
        "",
        "检索结果先给原文，再给路径和匹配角色。写作时从原文自行学习措辞、句段职责、节奏、格式、情绪推进和收束，不使用一条预先写好的总结替代阅读全文。",
        "",
        "```powershell",
        'python scripts/content_case_library.py search --asset short --content-type "清单与资源推荐" --query "盘点并锐评同类项目" --limit 2',
        'python scripts/content_case_library.py search --asset article --content-type "教程与操作指南" --query "从真实实践写完整教程" --limit 2',
        "```",
        "",
    ]
    groups: dict[tuple[str, str], list[ContentCase]] = {}
    for case in cases:
        groups.setdefault((case.asset, case.content_type), []).append(case)
        if case.supports_hook and case.asset != "hook":
            groups.setdefault(("hook", case.hook_family or ""), []).append(case)

    for asset in ("hook", "short", "article"):
        lines.extend([f"## {ASSET_LABELS[asset]}", ""])
        content_types = {
            content_type
            for group_asset, content_type in groups
            if group_asset == asset
        }
        order = {name: index for index, name in enumerate(CONTENT_TYPE_ORDER[asset])}
        for content_type in sorted(
            content_types, key=lambda name: (order.get(name, 999), name)
        ):
            lines.extend([f"### {content_type}", ""])
            for case in sorted(
                groups[(asset, content_type)], key=lambda item: item.title
            ):
                link = Path(os.path.relpath(case.path, INDEX_ROOT)).as_posix()
                lines.append(f"- [{case.title}](<{link}>)")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="检索和维护 100x Learning 内容案例")
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search", help="读取最接近当前任务的案例全文")
    search.add_argument(
        "--query",
        required=True,
        help="完整案例传本次要实现的表达与内容关系；开头案例传技巧、读者感受和所需材料",
    )
    search.add_argument(
        "--asset",
        action="append",
        choices=tuple(ASSET_LABELS),
        required=True,
        help="可重复；必须由上层显式选择 hook、short 或 article",
    )
    search.add_argument(
        "--content-type",
        help="用于提高同类案例排序，不会排除其它题材或类型",
    )
    search.add_argument("--limit", type=int, default=2)

    commands.add_parser("validate", help="检查案例能否被读取")
    index = commands.add_parser("build-index", help="重建或核对浏览索引")
    index.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "search":
        try:
            hits, issues = search_library(
                query=args.query,
                assets=args.asset,
                content_type=args.content_type,
                limit=args.limit,
            )
        except CaseError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if issues:
            print("案例库提示：\n" + "\n".join(issues), file=sys.stderr)
        print(render_search_results(hits), end="")
        return 0

    cases, issues = load_library()
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    counts = {
        asset: sum(_supports_asset(case, asset) for case in cases)
        for asset in ASSET_LABELS
    }
    if args.command == "validate":
        print(
            f"案例库有效：{len(cases)} 条；钩子 {counts['hook']} 条，"
            f"完整短内容 {counts['short']} 条，完整文章 {counts['article']} 篇。"
        )
        return 0

    expected = build_index(cases)
    if args.check:
        if not INDEX_PATH.exists():
            print(f"索引不存在：{INDEX_PATH}", file=sys.stderr)
            return 1
        if INDEX_PATH.read_text(encoding="utf-8") != expected:
            print(f"索引需要更新：{INDEX_PATH}", file=sys.stderr)
            return 1
        print(f"索引有效：{INDEX_PATH}")
        return 0
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(expected, encoding="utf-8")
    print(f"索引已更新：{INDEX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
