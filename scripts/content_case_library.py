from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

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

ASSET_DIRECTORIES = {"完整短内容": "short"}
ASSET_LABELS = {
    "short": "完整短内容",
    "article": "完整文章",
}
SUPPORTED_ROLES = {"promotion"}
SUPPORTED_BENEFIT_RECIPIENTS = {"reader", "publisher", "partner", "none"}
SUPPORTED_CASE_STATUS = {"active", "history-only"}
CONTENT_TYPE_ORDER = {
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
    index_roles: tuple[str, ...] = ()
    promotion_stages: tuple[str, ...] = ()
    audience_actions: tuple[str, ...] = ()
    benefit_recipients: tuple[str, ...] = ()

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


def _reject_hook_metadata(metadata: dict[str, str]) -> None:
    hook_fields = {
        "hook_pattern_id",
        "hook_techniques",
        "reader_effects",
        "source_case_file",
    }
    present = sorted(hook_fields & set(metadata))
    if present:
        raise CaseError(
            "完整内容不能声明钩子字段；案例库与钩子库使用独立生产入口："
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


def _parse_social(path: Path, layout: LibraryLayout) -> ContentCase | None:
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
    title, _ = _title(body)
    original = _section(body, "原帖全文")
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


def load_library(layout: LibraryLayout) -> tuple[list[ContentCase], list[str]]:
    cases: list[ContentCase] = []
    issues: list[str] = []
    text_paths: dict[str, Path] = {}
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
        previous = text_paths.get(case.original_text)
        if previous is not None:
            issues.append(f"{path}: 案例全文与 {previous} 重复")
            continue
        text_paths[case.original_text] = path
        cases.append(case)
    return cases, issues


def _supports_asset(case: ContentCase, asset: str) -> bool:
    return case.asset == asset


def build_index(cases: Sequence[ContentCase], layout: LibraryLayout) -> str:
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
        f"当前共有 {len(cases)} 条完整案例：{counts['short']} 条完整短内容，{counts['article']} 篇完整文章。",
        f"其中 {promotion_count} 条带有宣发角色；这些元数据用于定位相近的宣发机制，不限制宣传内容读取其它相关案例，也不能替代当前任务的利益事实。",
        "",
        "文章库不等于文章案例库。只有正文写法本身提供了现有案例没有的可复用方法，才标记为案例；其它文章继续留在原目录作为归档。",
        "",
        "写作时先浏览本索引，再按标题、主题、任务或写法用普通文本检索缩小范围，然后打开多个完整原文。索引只负责定位，不能替代原文；参考数量由内容差异和上下文容量决定，不预设唯一模仿对象。",
        "下面只是定位示例。找不到更贴合的案例时，可以根据现有事实和作者判断继续写，不为满足数量强行加入无关参考。",
        "",
        "```powershell",
        'rg -n -i "项目|结果|痛点" "20-Sources/Social Posts/Content Cases/完整短内容"',
        "```",
        "",
    ]
    groups: dict[tuple[str, str], list[ContentCase]] = {}
    for case in cases:
        groups.setdefault((case.asset, case.content_type), []).append(case)

    for asset in ("short", "article"):
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
    existing: Sequence[ContentCase],
    *,
    kind: str,
    input_path: Path,
    title: str,
    content_type: str,
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
    try:
        original = input_path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise CaseError(f"输入文件不存在：{input_path}") from exc
    _check_text(original)
    if any(item.original_text == original for item in existing):
        raise CaseError("这份案例全文已经存在")
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
                        "type: content-case",
                        "status: active",
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


def write_index(
    layout: LibraryLayout,
    cases: Sequence[ContentCase],
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
                f"案例库有效：{len(cases)} 条；完整短内容 {counts['short']} 条，"
                f"完整文章 {counts['article']} 篇。"
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
