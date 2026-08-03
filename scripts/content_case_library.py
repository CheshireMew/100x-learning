from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TypeAlias

try:
    from scripts.marktree_integration import managed_write_text
    from scripts.private_library import (
        LibraryError,
        LibraryLayout,
        resolve_library_root,
        validate_library,
    )
except ModuleNotFoundError:
    from marktree_integration import managed_write_text
    from private_library import (
        LibraryError,
        LibraryLayout,
        resolve_library_root,
        validate_library,
    )

ASSET_DIRECTORIES = {"钩子与开头": "hook", "完整短内容": "short"}
ASSET_LABELS = {
    "hook": "钩子与开头",
    "short": "完整短内容",
    "article": "完整文章",
}
SUPPORTED_ROLES = {"promotion"}
SUPPORTED_BENEFIT_RECIPIENTS = {"reader", "publisher", "partner", "none"}
SUPPORTED_CASE_STATUS = {"active", "history-only"}
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
    index_roles: tuple[str, ...] = ()
    promotion_stages: tuple[str, ...] = ()
    audience_actions: tuple[str, ...] = ()
    benefit_recipients: tuple[str, ...] = ()



@dataclass(frozen=True)
class HookPattern:
    path: Path
    pattern_id: str
    content_type: str
    title: str
    index_task: str
    index_topics: tuple[str, ...]
    index_moves: tuple[str, ...]
    source_text: str
    source: str
    source_case_file: Path | None
    hook_techniques: tuple[str, ...]
    reader_effects: tuple[str, ...]
    index_roles: tuple[str, ...] = ()
    promotion_stages: tuple[str, ...] = ()
    audience_actions: tuple[str, ...] = ()
    benefit_recipients: tuple[str, ...] = ()


LibraryResource: TypeAlias = ContentCase | HookPattern


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


def _case_status(metadata: dict[str, str]) -> str:
    status = _strip_quotes(metadata.get("case_status", "active"))
    if status not in SUPPORTED_CASE_STATUS:
        raise CaseError("case_status 只能是 active 或 history-only")
    return status


def _hook_metadata(
    metadata: dict[str, str],
    *,
    required: bool,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
]:
    required_fields = ("hook_techniques", "reader_effects")
    present = [key for key in required_fields if key in metadata]

    if not present:
        if required:
            raise CaseError("开头案例缺少 hook_techniques 和 reader_effects")
        return (), ()

    missing_fields = [key for key in required_fields if key not in metadata]
    if missing_fields:
        missing = "、".join(missing_fields)
        raise CaseError(f"开头元数据不完整，缺少 {missing}")
    return (
        _metadata_list(metadata, "hook_techniques"),
        _metadata_list(metadata, "reader_effects"),
    )


def _reject_hook_metadata(metadata: dict[str, str]) -> None:
    legacy_fields = {
        "hook_techniques",
        "reader_effects",
    }
    present = sorted(legacy_fields & set(metadata))
    if present:
        raise CaseError(
            "完整内容不能再声明钩子技巧；请把这些字段迁入“钩子与开头”中的 HookPattern："
            + "、".join(present)
        )


def _promotion_metadata(
    metadata: dict[str, str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    roles = (
        _metadata_list(metadata, "index_roles")
        if "index_roles" in metadata
        else ()
    )
    invalid_roles = sorted(set(roles) - SUPPORTED_ROLES)
    if invalid_roles:
        raise CaseError(f"不支持的 index_roles：{'、'.join(invalid_roles)}")

    promotion_fields = (
        "promotion_stages",
        "audience_actions",
        "benefit_recipients",
    )
    present = [field for field in promotion_fields if field in metadata]
    if "promotion" not in roles:
        if present:
            raise CaseError("宣发元数据只能用于 index_roles 包含 promotion 的案例")
        return roles, (), (), ()

    missing = [field for field in promotion_fields if field not in metadata]
    if missing:
        raise CaseError(f"宣发案例缺少 {'、'.join(missing)}")
    stages = _metadata_list(metadata, "promotion_stages")
    actions = _metadata_list(metadata, "audience_actions")
    recipients = _metadata_list(metadata, "benefit_recipients")
    invalid_recipients = sorted(
        set(recipients) - SUPPORTED_BENEFIT_RECIPIENTS
    )
    if invalid_recipients:
        raise CaseError(
            "不支持的 benefit_recipients："
            + "、".join(invalid_recipients)
        )
    if "none" in recipients and len(recipients) > 1:
        raise CaseError("benefit_recipients 使用 none 时不能再填写其它领取者")
    return roles, stages, actions, recipients


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


def _resolve_source_case(path_value: str, layout: LibraryLayout) -> ContentCase:
    source_path = (layout.root / path_value).resolve()
    try:
        source_path.relative_to(layout.root)
    except ValueError as exc:
        raise CaseError("source_case_file 必须位于当前私人知识库内") from exc
    if not source_path.exists():
        raise CaseError(f"source_case_file 不存在：{source_path}")
    if source_path.is_relative_to(layout.article_sources):
        return _parse_article(source_path)
    if source_path.is_relative_to(layout.social_cases):
        resource = _parse_social(source_path, layout)
        if isinstance(resource, ContentCase):
            return resource
    raise CaseError("source_case_file 必须指向完整短内容或活动文章案例")


def _parse_hook_pattern(
    path: Path,
    *,
    layout: LibraryLayout,
    content_type: str,
    metadata: dict[str, str],
    body: str,
) -> HookPattern:
    title, _ = _title(body)
    source_case_value = _strip_quotes(metadata.get("source_case_file", ""))
    if source_case_value:
        source_case = _resolve_source_case(source_case_value, layout)
        source_text = source_case.original_text
        source = source_case.source
        source_case_file = source_case.path
    else:
        source, source_text = _source_from_social_body(
            _section(body, "原帖全文")
        )
        source_case_file = None
    _check_text(source_text)
    hook_techniques, reader_effects = _hook_metadata(
        metadata,
        required=True,
    )
    index_roles, promotion_stages, audience_actions, benefit_recipients = (
        _promotion_metadata(metadata)
    )
    return HookPattern(
        path=path,
        pattern_id=_required(metadata, "hook_pattern_id"),
        content_type=content_type,
        title=title,
        index_task=_required(metadata, "index_task"),
        index_topics=_metadata_list(metadata, "index_topics"),
        index_moves=_metadata_list(metadata, "index_moves"),
        source_text=source_text,
        source=source,
        source_case_file=source_case_file,
        hook_techniques=hook_techniques,
        reader_effects=reader_effects,
        index_roles=index_roles,
        promotion_stages=promotion_stages,
        audience_actions=audience_actions,
        benefit_recipients=benefit_recipients,
    )


def _parse_social(path: Path, layout: LibraryLayout) -> LibraryResource | None:
    relative = path.relative_to(layout.social_cases)
    if len(relative.parts) != 3:
        raise CaseError("案例必须放在“成品形态/内容类型/文件”三级路径")
    asset_directory, content_type, _ = relative.parts
    asset = ASSET_DIRECTORIES.get(asset_directory)
    if asset is None:
        raise CaseError("未知的成品形态目录")

    metadata, body = _parse_case_index(path.read_text(encoding="utf-8-sig"))
    if _case_status(metadata) == "history-only":
        return None
    if asset == "hook":
        return _parse_hook_pattern(
            path,
            layout=layout,
            content_type=content_type,
            metadata=metadata,
            body=body,
        )
    title, _ = _title(body)
    source, original = _source_from_social_body(_section(body, "原帖全文"))
    _check_text(original)
    _reject_hook_metadata(metadata)
    index_roles, promotion_stages, audience_actions, benefit_recipients = (
        _promotion_metadata(metadata)
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
        index_roles=index_roles,
        promotion_stages=promotion_stages,
        audience_actions=audience_actions,
        benefit_recipients=benefit_recipients,
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
    _reject_hook_metadata(metadata)
    index_roles, promotion_stages, audience_actions, benefit_recipients = (
        _promotion_metadata(metadata)
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
        index_roles=index_roles,
        promotion_stages=promotion_stages,
        audience_actions=audience_actions,
        benefit_recipients=benefit_recipients,
    )


def _article_is_case(path: Path) -> bool:
    return "<!-- content-case-index" in path.read_text(encoding="utf-8-sig")


def _case_paths(layout: LibraryLayout) -> list[Path]:
    social = [
        path
        for directory in ASSET_DIRECTORIES
        for path in (layout.social_cases / directory).rglob("*.md")
    ]
    articles = [
        path
        for path in layout.article_sources.rglob("*.md")
        if _article_is_case(path)
    ]
    return sorted([*social, *articles])


def load_library(layout: LibraryLayout) -> tuple[list[LibraryResource], list[str]]:
    cases: list[LibraryResource] = []
    issues: list[str] = []
    source_paths: dict[str, Path] = {}
    pattern_ids: dict[str, Path] = {}
    for path in _case_paths(layout):
        try:
            case = (
                _parse_article(path)
                if path.is_relative_to(layout.article_sources)
                else _parse_social(path, layout)
            )
        except (CaseError, OSError, UnicodeError) as exc:
            issues.append(f"{path}: {exc}")
            continue
        if case is None:
            continue
        if isinstance(case, HookPattern):
            previous_pattern = pattern_ids.get(case.pattern_id)
            if previous_pattern is not None:
                issues.append(
                    f"{path}: hook_pattern_id 与 {previous_pattern} 重复"
                )
                continue
            pattern_ids[case.pattern_id] = path
        elif re.match(r"https?://", case.source):
            previous = source_paths.get(case.source)
            if previous is not None:
                issues.append(f"{path}: 来源链接与 {previous} 重复")
                continue
            source_paths[case.source] = path
        cases.append(case)
    return cases, issues


def _supports_asset(case: LibraryResource, asset: str) -> bool:
    if isinstance(case, HookPattern):
        return asset == "hook"
    return case.asset == asset


def build_index(cases: Sequence[LibraryResource], layout: LibraryLayout) -> str:
    counts = {
        asset: sum(_supports_asset(case, asset) for case in cases)
        for asset in ASSET_LABELS
    }
    promotion_count = sum("promotion" in case.index_roles for case in cases)
    lines = [
        "# 内容案例索引",
        "",
        "这是给人浏览的统一索引。目录、成品类型、主题和技巧都只负责帮助定位原文，不限制案例的表达方法可以迁移到什么题材。",
        "",
        f"当前共有 {len(cases)} 条案例：{counts['hook']} 条钩子与开头，{counts['short']} 条完整短内容，{counts['article']} 篇完整文章。",
        f"其中 {promotion_count} 条带有宣发角色；用于宣发时，只打开利益领取者与当前任务一致的原文。",
        "",
        "完整案例与钩子技巧是两种资源：完整内容保留全文；`钩子与开头` 保存可迁移技巧及其来源示例。技巧可以引用完整案例的开头，但不会把完整案例再次当作钩子资源，也不复制完整正文。",
        "",
        "文章库不等于文章案例库。只有正文写法本身提供了现有案例没有的可复用方法，才标记为案例；其它文章继续留在原目录作为归档。",
        "",
        "写作时先浏览本索引，再按标题、主题、任务或写法用普通文本检索缩小范围，然后打开多个完整原文和多个钩子文件。索引只负责定位，不能替代原文；参考数量由内容差异和上下文容量决定，不预设唯一模仿对象。",
        "下面只是定位示例。找不到更贴合的案例时，可以根据现有事实和作者判断继续写，不为满足数量强行加入无关参考。",
        "",
        "```powershell",
        'rg -n -i "项目|结果|痛点" "20-Sources/Social Posts/Content Cases/完整短内容"',
        'rg -n -i "结果|痛点|问题|反常识" "20-Sources/Social Posts/Content Cases/钩子与开头"',
        "```",
        "",
    ]
    groups: dict[tuple[str, str], list[LibraryResource]] = {}
    for case in cases:
        asset = "hook" if isinstance(case, HookPattern) else case.asset
        groups.setdefault((asset, case.content_type), []).append(case)

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
                link = Path(
                    os.path.relpath(case.path, layout.case_index_root)
                ).as_posix()
                lines.append(f"- [{case.title}](<{link}>)")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _safe_segment(value: str, field: str) -> str:
    normalized = value.strip()
    if (
        not normalized
        or normalized in {".", ".."}
        or any(character in normalized for character in '<>:"/\\|?*')
    ):
        raise CaseError(f"{field} 不能作为目录或文件名：{value}")
    return normalized


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _list_value(values: Sequence[str]) -> str:
    cleaned = [value.strip() for value in values if value.strip()]
    if not cleaned:
        raise CaseError("索引数组不能为空")
    return json.dumps(cleaned, ensure_ascii=False)


def _case_index_block(
    *,
    index_task: str,
    topics: Sequence[str],
    moves: Sequence[str],
    extra: Sequence[tuple[str, str]] = (),
) -> str:
    lines = ["<!-- content-case-index"]
    lines.extend(f"{key}: {value}" for key, value in extra)
    lines.extend(
        [
            f"index_task: {_quoted(index_task.strip())}",
            f"index_topics: {_list_value(topics)}",
            f"index_moves: {_list_value(moves)}",
            "-->",
        ]
    )
    return "\n".join(lines)


def _promotion_index_fields(
    *,
    roles: Sequence[str],
    stages: Sequence[str],
    actions: Sequence[str],
    recipients: Sequence[str],
) -> tuple[tuple[str, str], ...]:
    cleaned_roles = tuple(value.strip() for value in roles if value.strip())
    cleaned_stages = tuple(value.strip() for value in stages if value.strip())
    cleaned_actions = tuple(value.strip() for value in actions if value.strip())
    cleaned_recipients = tuple(
        value.strip() for value in recipients if value.strip()
    )
    if not any((cleaned_roles, cleaned_stages, cleaned_actions, cleaned_recipients)):
        return ()
    metadata = {
        "index_roles": _list_value(cleaned_roles),
        "promotion_stages": _list_value(cleaned_stages),
        "audience_actions": _list_value(cleaned_actions),
        "benefit_recipients": _list_value(cleaned_recipients),
    }
    _promotion_metadata(metadata)
    return tuple(metadata.items())


def _writing_index_fields(
    *,
    writing_format: str | None,
    writing_origin: str | None,
    voice_eligible: bool | None,
) -> tuple[tuple[str, str], ...]:
    if writing_format is None and writing_origin is None and voice_eligible is None:
        return ()
    if not writing_format:
        raise CaseError("保存本人发布案例时必须提供 writing_format")
    fields: list[tuple[str, str]] = [
        ("writing_format", _quoted(writing_format.strip()))
    ]
    if writing_origin:
        fields.append(("writing_origin", _quoted(writing_origin.strip())))
    if voice_eligible is not None:
        fields.append(("voice_eligible", "true" if voice_eligible else "false"))
    return tuple(fields)


def add_case(
    layout: LibraryLayout,
    existing: Sequence[LibraryResource],
    *,
    kind: str,
    input_path: Path,
    title: str,
    content_type: str,
    source: str,
    index_task: str,
    topics: Sequence[str],
    moves: Sequence[str],
    index_roles: Sequence[str] = (),
    promotion_stages: Sequence[str] = (),
    audience_actions: Sequence[str] = (),
    benefit_recipients: Sequence[str] = (),
    writing_format: str | None = None,
    writing_origin: str | None = None,
    voice_eligible: bool | None = None,
    config_path: Path | None = None,
) -> Path:
    title = _safe_segment(title, "title")
    content_type = _safe_segment(content_type, "content_type")
    source = source.strip()
    if not source:
        raise CaseError("source 不能为空")
    if any(
        isinstance(item, ContentCase) and item.source == source
        for item in existing
    ):
        raise CaseError(f"这个来源已经存在于内容案例库：{source}")
    try:
        original = input_path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise CaseError(f"输入文件不存在：{input_path}") from exc
    _check_text(original)
    promotion_fields = _promotion_index_fields(
        roles=index_roles,
        stages=promotion_stages,
        actions=audience_actions,
        recipients=benefit_recipients,
    )
    writing_fields = _writing_index_fields(
        writing_format=writing_format,
        writing_origin=writing_origin,
        voice_eligible=voice_eligible,
    )

    if kind == "short":
        path = (
            layout.social_cases / "完整短内容" / content_type / f"{title}.md"
        )
        body = "\n\n".join(
            [
                f"# {title}",
                "## 原帖全文",
                original,
                f"来源：{source}",
                _case_index_block(
                    index_task=index_task,
                    topics=topics,
                    moves=moves,
                    extra=(*writing_fields, *promotion_fields),
                ),
            ]
        ) + "\n"
    elif kind == "article":
        path = (
            layout.article_sources
            / "Content Cases"
            / content_type
            / f"{title}.md"
        )
        body = "\n\n".join(
            [
                "\n".join(
                    [
                        "---",
                        "type: source-article",
                        "status: active",
                        f"source_url: {_quoted(source)}",
                        f"content_type: {_quoted(content_type)}",
                        "---",
                    ]
                ),
                f"# {title}",
                original,
                _case_index_block(
                    index_task=index_task,
                    topics=topics,
                    moves=moves,
                    extra=(
                        ("reference_value", '"case"'),
                        *writing_fields,
                        *promotion_fields,
                    ),
                ),
            ]
        ) + "\n"
    else:
        raise CaseError("kind 必须是 short 或 article")

    if path.exists():
        raise CaseError(f"内容案例已经存在：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_write_text(layout.root, path, body, config_path=config_path)
    if kind == "short":
        parsed = _parse_social(path, layout)
        if not isinstance(parsed, ContentCase):
            raise CaseError(f"没有生成完整内容案例：{path}")
    else:
        _parse_article(path)
    return path


def add_hook(
    layout: LibraryLayout,
    existing: Sequence[LibraryResource],
    *,
    title: str,
    pattern_id: str,
    content_type: str,
    source_case: str,
    index_task: str,
    topics: Sequence[str],
    moves: Sequence[str],
    techniques: Sequence[str],
    reader_effects: Sequence[str],
    index_roles: Sequence[str] = (),
    promotion_stages: Sequence[str] = (),
    audience_actions: Sequence[str] = (),
    benefit_recipients: Sequence[str] = (),
    config_path: Path | None = None,
) -> Path:
    title = _safe_segment(title, "title")
    content_type = _safe_segment(content_type, "content_type")
    pattern_id = pattern_id.strip()
    if not pattern_id:
        raise CaseError("pattern_id 不能为空")
    if any(
        isinstance(item, HookPattern) and item.pattern_id == pattern_id
        for item in existing
    ):
        raise CaseError(f"hook_pattern_id 已经存在：{pattern_id}")
    source_case_path = Path(source_case)
    if source_case_path.is_absolute() or ".." in source_case_path.parts:
        raise CaseError("source_case 必须是私人知识库根目录下的相对路径")
    _resolve_source_case(source_case_path.as_posix(), layout)
    promotion_fields = _promotion_index_fields(
        roles=index_roles,
        stages=promotion_stages,
        actions=audience_actions,
        recipients=benefit_recipients,
    )

    path = layout.social_cases / "钩子与开头" / content_type / f"{title}.md"
    if path.exists():
        raise CaseError(f"钩子技巧已经存在：{path}")
    body = "\n\n".join(
        [
            f"# {title}",
            "## 来源示例\n\n完整原文见引用案例。",
            _case_index_block(
                index_task=index_task,
                topics=topics,
                moves=moves,
                extra=(
                    ("hook_pattern_id", _quoted(pattern_id)),
                    ("hook_techniques", _list_value(techniques)),
                    ("reader_effects", _list_value(reader_effects)),
                    ("source_case_file", _quoted(source_case_path.as_posix())),
                    *promotion_fields,
                ),
            ),
        ]
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_write_text(layout.root, path, body, config_path=config_path)
    parsed = _parse_social(path, layout)
    if not isinstance(parsed, HookPattern):
        raise CaseError(f"没有生成钩子技巧：{path}")
    return path


def write_index(
    layout: LibraryLayout,
    cases: Sequence[LibraryResource],
    config_path: Path | None = None,
) -> Path:
    layout.case_index_root.mkdir(parents=True, exist_ok=True)
    managed_write_text(
        layout.root,
        layout.case_index,
        build_index(cases, layout),
        config_path=config_path,
    )
    return layout.case_index


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="维护 100x Learning 内容案例")
    parser.add_argument("--library-root", type=Path, help="私人知识库根目录")
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="检查案例能否被读取")
    index = commands.add_parser("build-index", help="重建或核对浏览索引")
    index.add_argument("--check", action="store_true")

    add_case_parser = commands.add_parser(
        "add-case", help="从完整原文建立内容案例并更新索引"
    )
    add_case_parser.add_argument("--kind", choices=("short", "article"), required=True)
    add_case_parser.add_argument("--input", type=Path, required=True)
    add_case_parser.add_argument("--title", required=True)
    add_case_parser.add_argument("--content-type", required=True)
    add_case_parser.add_argument("--source", required=True)
    add_case_parser.add_argument("--index-task", required=True)
    add_case_parser.add_argument("--topic", action="append", required=True)
    add_case_parser.add_argument("--move", action="append", required=True)
    add_case_parser.add_argument("--index-role", action="append", default=[])
    add_case_parser.add_argument("--promotion-stage", action="append", default=[])
    add_case_parser.add_argument("--audience-action", action="append", default=[])
    add_case_parser.add_argument("--benefit-recipient", action="append", default=[])
    add_case_parser.add_argument("--writing-format")
    add_case_parser.add_argument("--writing-origin")
    add_case_parser.add_argument(
        "--voice-eligible",
        choices=("true", "false"),
    )

    add_hook_parser = commands.add_parser(
        "add-hook", help="引用完整案例建立钩子技巧并更新索引"
    )
    add_hook_parser.add_argument("--title", required=True)
    add_hook_parser.add_argument("--pattern-id", required=True)
    add_hook_parser.add_argument("--content-type", required=True)
    add_hook_parser.add_argument("--source-case", required=True)
    add_hook_parser.add_argument("--index-task", required=True)
    add_hook_parser.add_argument("--topic", action="append", required=True)
    add_hook_parser.add_argument("--move", action="append", required=True)
    add_hook_parser.add_argument("--technique", action="append", required=True)
    add_hook_parser.add_argument("--reader-effect", action="append", required=True)
    add_hook_parser.add_argument("--index-role", action="append", default=[])
    add_hook_parser.add_argument("--promotion-stage", action="append", default=[])
    add_hook_parser.add_argument("--audience-action", action="append", default=[])
    add_hook_parser.add_argument("--benefit-recipient", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = resolve_library_root(args.library_root, args.config)
        layout = validate_library(root)
        cases, issues = load_library(layout)
        if issues:
            raise CaseError("\n".join(issues))

        if args.command == "add-case":
            created = add_case(
                layout,
                cases,
                kind=args.kind,
                input_path=args.input,
                title=args.title,
                content_type=args.content_type,
                source=args.source,
                index_task=args.index_task,
                topics=args.topic,
                moves=args.move,
                index_roles=args.index_role,
                promotion_stages=args.promotion_stage,
                audience_actions=args.audience_action,
                benefit_recipients=args.benefit_recipient,
                writing_format=args.writing_format,
                writing_origin=args.writing_origin,
                voice_eligible=(
                    args.voice_eligible == "true"
                    if args.voice_eligible is not None
                    else None
                ),
                config_path=args.config,
            )
            cases, issues = load_library(layout)
            if issues:
                raise CaseError("\n".join(issues))
            index_path = write_index(layout, cases, args.config)
            print(f"内容案例已保存：{created}\n索引已更新：{index_path}")
            return 0

        if args.command == "add-hook":
            created = add_hook(
                layout,
                cases,
                title=args.title,
                pattern_id=args.pattern_id,
                content_type=args.content_type,
                source_case=args.source_case,
                index_task=args.index_task,
                topics=args.topic,
                moves=args.move,
                techniques=args.technique,
                reader_effects=args.reader_effect,
                index_roles=args.index_role,
                promotion_stages=args.promotion_stage,
                audience_actions=args.audience_action,
                benefit_recipients=args.benefit_recipient,
                config_path=args.config,
            )
            cases, issues = load_library(layout)
            if issues:
                raise CaseError("\n".join(issues))
            index_path = write_index(layout, cases, args.config)
            print(f"钩子技巧已保存：{created}\n索引已更新：{index_path}")
            return 0

        counts = {
            asset: sum(_supports_asset(case, asset) for case in cases)
            for asset in ASSET_LABELS
        }
        if args.command == "validate":
            expected = build_index(cases, layout)
            if not layout.case_index.exists():
                raise CaseError(f"索引不存在：{layout.case_index}")
            if layout.case_index.read_text(encoding="utf-8") != expected:
                raise CaseError(f"索引需要更新：{layout.case_index}")
            print(
                f"案例库有效：{len(cases)} 条；钩子 {counts['hook']} 条，"
                f"完整短内容 {counts['short']} 条，完整文章 {counts['article']} 篇。"
            )
            return 0

        expected = build_index(cases, layout)
        if args.check:
            if not layout.case_index.exists():
                raise CaseError(f"索引不存在：{layout.case_index}")
            if layout.case_index.read_text(encoding="utf-8") != expected:
                raise CaseError(f"索引需要更新：{layout.case_index}")
            print(f"索引有效：{layout.case_index}")
            return 0
        index_path = write_index(layout, cases, args.config)
        print(f"索引已更新：{index_path}")
        return 0
    except (CaseError, LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
