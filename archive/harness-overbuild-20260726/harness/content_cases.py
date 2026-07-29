from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOCIAL_CASE_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Social Posts"
    / "Content Cases"
)
ARTICLE_CASE_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Articles"
    / "Cheshire"
    / "Blog"
)
ACTIVE_INDEX_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Content Cases"
)
INDEX_NAME = "内容案例索引.md"
INDEX_PATH = ACTIVE_INDEX_ROOT / INDEX_NAME
SOCIAL_CASE_FIELDS = {"writing_task", "topics", "structure"}
ARTICLE_CASE_FIELDS = {
    "authorship",
    "reference_value",
    "content_type",
    "source_url",
    "writing_task",
    "topics",
    "structure",
}
ASSET_DIRECTORIES = {
    "钩子与开头": "hook",
    "完整短内容": "short",
}
ASSET_LABELS = {
    "hook": "钩子与开头",
    "short": "完整短内容",
    "article": "完整文章",
}
ALLOWED_ASSETS = frozenset(ASSET_LABELS)
CONTENT_TYPE_ORDER = {
    "hook": {
        "反常识钩子": 0,
        "痛点钩子": 1,
        "结果钩子": 2,
        "问题钩子": 3,
    },
    "short": {
        "项目与产品介绍": 0,
        "概念与机制解释": 1,
        "教程与操作指南": 2,
        "清单与资源推荐": 3,
        "事件与商业故事": 4,
        "观点与趋势判断": 5,
        "行业与投资分析": 6,
        "个人观察与实测": 7,
    },
    "article": {
        "项目与产品介绍": 0,
        "概念与机制解释": 1,
        "教程与操作指南": 2,
        "清单与资源推荐": 3,
        "事件与商业故事": 4,
        "观点与趋势判断": 5,
        "行业与投资分析": 6,
        "个人观察与实测": 7,
    },
}
SOCIAL_SOURCE_URL_RE = re.compile(
    r"^原帖链接：(https://x\.com/[^/\s]+/status/\d+)\s*$",
    re.MULTILINE,
)
SOCIAL_SECTION_RE = re.compile(
    r"^# (?P<title>.+?)\s*$"
    r".*?"
    r"^## 原帖全文\s*$\n+"
    r"(?P<original>.*?)"
    r"\n+^## 可以参考什么\s*$\n+"
    r"(?P<borrow>.*?)"
    r"\n+^## 适用场景\s*$\n+"
    r"(?P<use>.*?)(?=\n+原帖链接：)",
    re.MULTILINE | re.DOTALL,
)
ARTICLE_SECTION_RE = re.compile(
    r"^# (?P<title>.+?)\s*$\n+"
    r"(?P<original>.*?)"
    r"\n+^<!-- content-case-notes -->\s*$"
    r"\n+^## 可以参考什么\s*$\n+"
    r"(?P<borrow>.*?)"
    r"\n+^## 适用场景\s*$\n+"
    r"(?P<use>.*?)\s*$",
    re.MULTILINE | re.DOTALL,
)


class ContentCaseError(ValueError):
    pass


@dataclass(frozen=True)
class ContentCase:
    path: Path
    relative_path: Path
    asset: str
    content_type: str
    title: str
    writing_task: str
    topics: tuple[str, ...]
    structure: tuple[str, ...]
    original_text: str
    borrow_notes: str
    use_cases: str
    source_url: str
    authorship: str | None = None


@dataclass(frozen=True)
class SearchHit:
    case: ContentCase
    score: float


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def _parse_list(value: str, field: str) -> tuple[str, ...]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        raise ContentCaseError(f"{field} 必须使用单行数组，例如 [主题一, 主题二]")
    items = tuple(
        item
        for item in (_strip_quotes(part) for part in value[1:-1].split(","))
        if item
    )
    if not items:
        raise ContentCaseError(f"{field} 至少需要一个值")
    return items


def _parse_frontmatter(
    text: str,
    expected_fields: set[str],
) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ContentCaseError("文件必须以 frontmatter 开始")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ContentCaseError("frontmatter 缺少结束标记")
    values: dict[str, object] = {}
    for raw_line in text[4:end].splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ContentCaseError(f"无法解析 frontmatter：{raw_line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key in values:
            raise ContentCaseError(f"frontmatter 字段重复：{key}")
        if key in {"writing_task", "authorship", "reference_value", "content_type", "source_url"}:
            value = _strip_quotes(raw_value)
            if not value:
                raise ContentCaseError(f"{key} 不能为空")
            values[key] = value
        elif key in {"topics", "structure"}:
            values[key] = _parse_list(raw_value, key)
        else:
            values[key] = raw_value.strip()
    actual = set(values)
    if actual != expected_fields:
        missing = sorted(expected_fields - actual)
        extra = sorted(actual - expected_fields)
        details = []
        if missing:
            details.append(f"缺少 {', '.join(missing)}")
        if extra:
            details.append(f"多出 {', '.join(extra)}")
        raise ContentCaseError(
            "案例字段不符合当前资产格式；" + "；".join(details)
        )
    return values, text[end + 5 :]


def _validate_sections(
    original_text: str,
    borrow_notes: str,
    use_cases: str,
) -> None:
    if not original_text:
        raise ContentCaseError("正文全文不能为空")
    if not borrow_notes:
        raise ContentCaseError("可以参考什么不能为空")
    if not use_cases:
        raise ContentCaseError("适用场景不能为空")


def _parse_social_case(path: Path) -> ContentCase:
    path = path.resolve()
    try:
        relative = path.relative_to(SOCIAL_CASE_ROOT.resolve())
    except ValueError as exc:
        raise ContentCaseError("路径不在短内容案例源中") from exc
    if len(relative.parts) != 3:
        raise ContentCaseError(
            "案例必须位于“资产类型/内容类型/案例文件.md”三级路径"
        )
    asset_directory, content_type, _ = relative.parts
    asset = ASSET_DIRECTORIES.get(asset_directory)
    if asset is None:
        raise ContentCaseError(
            "第一级目录只能是“钩子与开头”或“完整短内容”"
        )

    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text, SOCIAL_CASE_FIELDS)
    section_match = SOCIAL_SECTION_RE.search(body)
    if not section_match:
        raise ContentCaseError(
            "正文必须依次包含一级标题、原帖全文、可以参考什么和适用场景"
        )
    source_matches = SOCIAL_SOURCE_URL_RE.findall(body)
    if len(source_matches) != 1:
        raise ContentCaseError("正文末尾必须且只能有一个 X 原帖链接")

    original_text = section_match.group("original").strip()
    borrow_notes = section_match.group("borrow").strip()
    use_cases = section_match.group("use").strip()
    _validate_sections(original_text, borrow_notes, use_cases)

    return ContentCase(
        path=path,
        relative_path=path.relative_to(PROJECT_ROOT),
        asset=asset,
        content_type=content_type,
        title=section_match.group("title").strip(),
        writing_task=str(frontmatter["writing_task"]),
        topics=tuple(frontmatter["topics"]),
        structure=tuple(frontmatter["structure"]),
        original_text=original_text,
        borrow_notes=borrow_notes,
        use_cases=use_cases,
        source_url=source_matches[0],
    )


def _parse_article_case(path: Path) -> ContentCase:
    path = path.resolve()
    try:
        path.relative_to(ARTICLE_CASE_ROOT.resolve())
    except ValueError as exc:
        raise ContentCaseError("路径不在博客文章源中") from exc
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text, ARTICLE_CASE_FIELDS)
    if frontmatter["reference_value"] != "case":
        raise ContentCaseError("该文章只保存正文，没有进入活动案例库")
    section_match = ARTICLE_SECTION_RE.search(body)
    if not section_match:
        raise ContentCaseError(
            "文章必须包含一级标题、完整正文、可以参考什么和适用场景"
        )
    original_text = section_match.group("original").strip()
    borrow_notes = section_match.group("borrow").strip()
    use_cases = section_match.group("use").strip()
    _validate_sections(original_text, borrow_notes, use_cases)
    source_url = str(frontmatter["source_url"])
    if not re.fullmatch(r"https://blog\.blacknico\.com/\S+", source_url):
        raise ContentCaseError("source_url 必须是个人博客文章链接")
    return ContentCase(
        path=path,
        relative_path=path.relative_to(PROJECT_ROOT),
        asset="article",
        content_type=str(frontmatter["content_type"]),
        title=section_match.group("title").strip(),
        writing_task=str(frontmatter["writing_task"]),
        topics=tuple(frontmatter["topics"]),
        structure=tuple(frontmatter["structure"]),
        original_text=original_text,
        borrow_notes=borrow_notes,
        use_cases=use_cases,
        source_url=source_url,
        authorship=str(frontmatter["authorship"]),
    )


def parse_case(path: Path) -> ContentCase:
    path = path.resolve()
    if path.name == INDEX_NAME:
        raise ContentCaseError("索引不是案例文件")
    try:
        path.relative_to(SOCIAL_CASE_ROOT.resolve())
    except ValueError:
        pass
    else:
        return _parse_social_case(path)
    try:
        path.relative_to(ARTICLE_CASE_ROOT.resolve())
    except ValueError:
        pass
    else:
        return _parse_article_case(path)
    raise ContentCaseError("案例路径不在活动案例源中")


def _is_article_case(path: Path) -> bool:
    prefix = path.read_text(encoding="utf-8")[:1200]
    return bool(re.search(r'^reference_value:\s*"case"\s*$', prefix, re.MULTILINE))


def case_paths() -> list[Path]:
    social_paths = (
        [
            path
            for path in SOCIAL_CASE_ROOT.rglob("*.md")
            if path.name != INDEX_NAME
        ]
        if SOCIAL_CASE_ROOT.exists()
        else []
    )
    article_paths = (
        [
            path
            for path in ARTICLE_CASE_ROOT.glob("*.md")
            if _is_article_case(path)
        ]
        if ARTICLE_CASE_ROOT.exists()
        else []
    )
    return sorted([*social_paths, *article_paths])


def load_library() -> tuple[list[ContentCase], list[str]]:
    cases: list[ContentCase] = []
    issues: list[str] = []
    seen_urls: dict[str, Path] = {}
    for path in case_paths():
        try:
            case = parse_case(path)
        except (ContentCaseError, OSError, UnicodeError) as exc:
            issues.append(f"{path}: {exc}")
            continue
        previous = seen_urls.get(case.source_url)
        if previous is not None:
            issues.append(
                f"{path}: 原帖链接与 {previous} 重复：{case.source_url}"
            )
            continue
        seen_urls[case.source_url] = path
        cases.append(case)
    if not cases:
        issues.append("没有找到活动案例文件")
    return cases, issues


def validate_library() -> list[str]:
    _, issues = load_library()
    return issues


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
    candidate_terms: set[str] = set()
    for candidate in candidates:
        candidate_terms.update(_terms(candidate))
    score = len(query_terms & candidate_terms) / len(query_terms)
    normalized_query = unicodedata.normalize("NFKC", query).lower().strip()
    normalized_candidates = " ".join(candidates).lower()
    if normalized_query and normalized_query in normalized_candidates:
        score += 0.35
    return score


def _score_case(
    case: ContentCase,
    writing_task: str,
    topics: Sequence[str],
    structures: Sequence[str],
) -> float:
    task_score = _coverage(
        writing_task,
        (case.writing_task, case.content_type, case.title),
    )
    topic_score = sum(
        _coverage(topic, (*case.topics, case.title))
        for topic in topics
    )
    structure_score = sum(
        _coverage(structure, case.structure)
        for structure in structures
    )
    return task_score * 6 + topic_score * 4 + structure_score * 3


def search_library(
    writing_task: str,
    content_type: str,
    topics: Sequence[str] = (),
    structures: Sequence[str] = (),
    assets: Sequence[str] = ("short",),
    limit: int = 3,
) -> list[SearchHit]:
    selected_assets = tuple(dict.fromkeys(assets))
    if not selected_assets:
        raise ContentCaseError("assets 至少需要一种资产")
    invalid_assets = sorted(set(selected_assets) - ALLOWED_ASSETS)
    if invalid_assets:
        raise ContentCaseError(
            "assets 只能使用 hook、short 或 article："
            + ", ".join(invalid_assets)
        )
    if limit < 1:
        raise ContentCaseError("limit 必须大于 0")
    if limit < len(selected_assets):
        raise ContentCaseError("limit 不能小于所选资产类型数量")
    cases, issues = load_library()
    if issues:
        raise ContentCaseError("\n".join(issues))

    def ranked(selected_asset: str) -> list[SearchHit]:
        hits = []
        for case in cases:
            if case.asset != selected_asset:
                continue
            if (
                selected_asset != "hook"
                and case.content_type != content_type
            ):
                continue
            hit = SearchHit(
                case=case,
                score=_score_case(
                    case,
                    writing_task=writing_task,
                    topics=topics,
                    structures=structures,
                ),
            )
            hits.append(hit)
        hits.sort(
            key=lambda hit: (
                -hit.score,
                hit.case.content_type,
                hit.case.title,
            )
        )
        return hits

    ranked_by_asset = {
        asset: ranked(asset)
        for asset in selected_assets
    }
    missing_assets = [
        asset
        for asset, hits in ranked_by_asset.items()
        if not hits
    ]
    if missing_assets:
        raise ContentCaseError(
            "案例库缺少当前成文所需的"
            + "、".join(ASSET_LABELS[asset] for asset in missing_assets)
            + f"、内容类型“{content_type}”"
        )
    selected: list[SearchHit] = []
    selected_paths: set[Path] = set()
    for asset in selected_assets:
        if ranked_by_asset[asset]:
            hit = ranked_by_asset[asset][0]
            selected.append(hit)
            selected_paths.add(hit.case.path)
    remaining = sorted(
        (
            hit
            for asset in selected_assets
            for hit in ranked_by_asset[asset]
            if hit.case.path not in selected_paths
        ),
        key=lambda hit: (
            -hit.score,
            selected_assets.index(hit.case.asset),
            hit.case.content_type,
            hit.case.title,
        ),
    )
    selected.extend(remaining[: max(0, limit - len(selected))])
    return selected


def render_search_results(hits: Sequence[SearchHit]) -> str:
    if not hits:
        raise ContentCaseError("成文前必须取得至少一条完整案例")
    lines = [f"# 检索结果（{len(hits)} 条）", ""]
    for index, hit in enumerate(hits, start=1):
        case = hit.case
        lines.extend(
            [
                f"## {index}. {case.title}",
                "",
                f"- 本地路径：{case.path}",
                f"- 资产类型：{ASSET_LABELS[case.asset]}",
                f"- 内容类型：{case.content_type}",
                f"- 写作任务：{case.writing_task}",
                f"- 主题：{', '.join(case.topics)}",
                f"- 结构：{', '.join(case.structure)}",
                f"- 匹配分：{hit.score:.2f}",
            ]
        )
        if case.authorship is not None:
            lines.append(f"- 来源性质：{case.authorship}")
        body_label = "完整正文" if case.asset == "article" else "原帖全文"
        lines.extend(
            [
                "",
                f"### {body_label}",
                "",
                case.original_text,
                "",
                "### 可以参考什么",
                "",
                case.borrow_notes,
                "",
                "### 适用场景",
                "",
                case.use_cases,
                "",
                f"来源链接：{case.source_url}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_index(cases: Sequence[ContentCase]) -> str:
    counts = {
        asset: sum(case.asset == asset for case in cases)
        for asset in ASSET_LABELS
    }
    lines = [
        "# 内容案例索引",
        "",
        "这是 100x Learning 唯一的活动案例入口。案例按成品形态和内容类型组织，不按作者分库；检索只使用写作任务、主题和结构。",
        "",
        f"当前共有 {len(cases)} 条案例：{counts['hook']} 条钩子与开头，{counts['short']} 条完整短内容，{counts['article']} 篇完整文章。",
        "",
        "短帖或 Thread 检索 `short`，文章或 Newsletter 检索 `article`，明确要求加强传播时在正文案例之外同时检索 `hook`。用 `--content-type` 锁定正文案例类型；结果会直接给出本地全文、可借鉴结构和适用场景，不需要打开外部链接判断。",
        "",
        "```powershell",
        'python scripts/content_case_library.py search --writing-task "介绍开源项目" --content-type "项目与产品介绍" --topic "AI" --structure "用户结果" --asset short --limit 3',
        'python scripts/content_case_library.py search --writing-task "解释投资机制" --content-type "行业与投资分析" --topic "资产配置" --structure "方案比较" --asset article --limit 3',
        "```",
        "",
    ]
    groups: dict[tuple[str, str], list[ContentCase]] = {}
    for case in cases:
        groups.setdefault((case.asset, case.content_type), []).append(case)
    for asset in ("hook", "short", "article"):
        lines.extend([f"## {ASSET_LABELS[asset]}", ""])
        content_groups = [
            (content_type, group_cases)
            for (group_asset, content_type), group_cases in groups.items()
            if group_asset == asset
        ]
        content_groups.sort(
            key=lambda item: (
                CONTENT_TYPE_ORDER.get(asset, {}).get(
                    item[0],
                    999,
                ),
                item[0],
            )
        )
        for content_type, group_cases in content_groups:
            lines.extend([f"### {content_type}", ""])
            for case in sorted(group_cases, key=lambda item: item.title):
                link = Path(
                    os.path.relpath(case.path, ACTIVE_INDEX_ROOT)
                ).as_posix()
                lines.append(f"- [{case.title}](<{link}>)")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
