from __future__ import annotations

import argparse
import csv
import hashlib
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

ASSET_LABELS = {"short": "短内容", "article": "文章"}
TECHNIQUE_ORDER = (
    "利益先行",
    "结果先行",
    "变化先行",
    "问题切入",
    "场景切入",
    "亲历切入",
    "观点先行",
    "时间推进",
    "因果推进",
    "对比推进",
    "递进推进",
    "机制拆解",
    "案例推进",
    "步骤推进",
    "清单推进",
    "故事推进",
    "实测推进",
    "复盘推进",
    "行动收束",
    "开放收束",
)
SUPPORTED_TECHNIQUES = set(TECHNIQUE_ORDER)
WRITING_FIELDS = {
    "writing_format",
    "writing_purpose",
    "writing_origin",
    "voice_eligible",
}


class CaseError(ValueError):
    pass


@dataclass(frozen=True)
class ContentCase:
    path: Path
    case_id: str
    asset: str
    title: str
    writing_techniques: tuple[str, ...]
    original_text: str

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


def _metadata_list(metadata: dict[str, str], key: str) -> tuple[str, ...]:
    if key not in metadata:
        raise CaseError(f"缺少 {key}")
    return _parse_list(metadata[key], key)


def _writing_techniques(metadata: dict[str, str]) -> tuple[str, ...]:
    techniques = _metadata_list(metadata, "writing_techniques")
    invalid = sorted(set(techniques) - SUPPORTED_TECHNIQUES)
    if invalid:
        raise CaseError("不支持的写作技巧：" + "、".join(invalid))
    return techniques


def _case_id(value: str) -> str:
    normalized = _strip_quotes(value)
    if not re.fullmatch(r"case-[0-9a-f]{16}", normalized):
        raise CaseError("case_id 必须使用 case- 加 16 位小写十六进制字符")
    return normalized


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
    if re.search(
        r"^(?:原帖链接|来源)：[^\r\n]+[ \t]*\Z",
        original,
        re.MULTILINE,
    ):
        raise CaseError("案例不保存原帖链接或来源字段")


def _parse_case(path: Path, asset: str, layout: LibraryLayout) -> ContentCase:
    relative = path.relative_to(
        layout.social_cases if asset == "short" else layout.article_cases
    )
    expected_parts = 2 if asset == "short" else 1
    if len(relative.parts) != expected_parts:
        raise CaseError("案例目录只能区分成品形式，不能再按题材或内容类别分层")
    if asset == "short" and relative.parts[0] != "完整短内容":
        raise CaseError("短内容案例必须位于“完整短内容”目录")

    metadata, body = _parse_case_index(path.read_text(encoding="utf-8-sig"))
    unknown = sorted(
        set(metadata) - ({"case_id", "writing_techniques"} | WRITING_FIELDS)
    )
    if unknown:
        raise CaseError("案例元数据含有旧检索字段或未知字段：" + "、".join(unknown))
    case_id = _case_id(metadata.get("case_id", ""))
    if path.stem != case_id:
        raise CaseError("案例文件名必须与 case_id 一致，不能暴露题材或对象")
    title, _ = _title(body)
    original = _section(body, "原文全文")
    _check_text(original)
    return ContentCase(
        path=path,
        case_id=case_id,
        asset=asset,
        title=title,
        writing_techniques=_writing_techniques(metadata),
        original_text=original,
    )


def _case_paths(layout: LibraryLayout) -> list[Path]:
    social = list((layout.social_cases / "完整短内容").rglob("*.md"))
    articles = list(layout.article_cases.rglob("*.md"))
    return sorted([*social, *articles])


def load_library(layout: LibraryLayout) -> tuple[list[ContentCase], list[str]]:
    cases: list[ContentCase] = []
    issues: list[str] = []
    text_paths: dict[str, Path] = {}
    for path in _case_paths(layout):
        try:
            asset = "article" if path.is_relative_to(layout.article_cases) else "short"
            case = _parse_case(path, asset, layout)
        except (CaseError, OSError, UnicodeError) as exc:
            issues.append(f"{path}: {exc}")
            continue
        previous = text_paths.get(case.original_text)
        if previous is not None:
            issues.append(f"{path}: 案例全文与 {previous} 重复")
            continue
        text_paths[case.original_text] = path
        cases.append(case)
    return cases, issues


def _index_path(layout: LibraryLayout, asset: str) -> Path:
    return layout.short_case_index if asset == "short" else layout.article_case_index


def build_index(
    cases: Sequence[ContentCase], layout: LibraryLayout, asset: str
) -> str:
    if asset not in ASSET_LABELS:
        raise CaseError("asset 必须是 short 或 article")
    selected = [case for case in cases if case.asset == asset]
    lines = [
        f"# {ASSET_LABELS[asset]}案例索引",
        "",
        f"本索引只包含{ASSET_LABELS[asset]}，并且只按可迁移的写作技巧分组。条目和文件名只显示不带题材含义的稳定编号；当前对象、行业、主题和专名不参与案例选择。先按技巧选编号，再打开完整原文；索引不能替代正文。",
        "",
        f"当前共有 {len(selected)} 条{ASSET_LABELS[asset]}案例。",
        "",
    ]
    groups = {
        technique: [
            case for case in selected if technique in case.writing_techniques
        ]
        for technique in TECHNIQUE_ORDER
    }
    for technique, group in groups.items():
        if not group:
            continue
        lines.extend([f"## {technique}", ""])
        for case in sorted(group, key=lambda item: item.case_id):
            link = Path(os.path.relpath(case.path, layout.case_index_root)).as_posix()
            lines.append(f"- [参考 {case.case_id}](<{link}>)")
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
    case_id: str,
    techniques: Sequence[str],
    extra: Sequence[tuple[str, str]] = (),
) -> str:
    lines = ["<!-- content-case-index"]
    lines.extend(f"{key}: {value}" for key, value in extra)
    lines.extend(
        [
            f"case_id: {_quoted(case_id)}",
            f"writing_techniques: {_list_value(techniques)}",
            "-->",
        ]
    )
    return "\n".join(lines)


def _writing_index_fields(
    *,
    writing_format: str | None,
    writing_purpose: str | None,
    writing_origin: str | None,
    voice_eligible: bool | None,
) -> tuple[tuple[str, str], ...]:
    if (
        writing_format is None
        and writing_purpose is None
        and writing_origin is None
        and voice_eligible is None
    ):
        return ()
    if not writing_format:
        raise CaseError("保存本人发布案例时必须提供 writing_format")
    fields: list[tuple[str, str]] = [
        ("writing_format", _quoted(writing_format.strip()))
    ]
    if writing_purpose:
        fields.append(("writing_purpose", _quoted(writing_purpose.strip())))
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
    techniques: Sequence[str],
    writing_format: str | None = None,
    writing_purpose: str | None = None,
    writing_origin: str | None = None,
    voice_eligible: bool | None = None,
    config_path: Path | None = None,
) -> Path:
    title = _safe_segment(title, "title")
    normalized_techniques = tuple(value.strip() for value in techniques if value.strip())
    invalid = sorted(set(normalized_techniques) - SUPPORTED_TECHNIQUES)
    if not normalized_techniques:
        raise CaseError("至少提供一种写作技巧")
    if invalid:
        raise CaseError("不支持的写作技巧：" + "、".join(invalid))
    try:
        original = input_path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise CaseError(f"输入文件不存在：{input_path}") from exc
    _check_text(original)
    if any(item.original_text == original for item in existing):
        raise CaseError("这份案例全文已经存在")
    case_id = "case-" + hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
    writing_fields = _writing_index_fields(
        writing_format=writing_format,
        writing_purpose=writing_purpose,
        writing_origin=writing_origin,
        voice_eligible=voice_eligible,
    )

    if kind == "short":
        path = layout.social_cases / "完整短内容" / f"{case_id}.md"
    elif kind == "article":
        path = layout.article_cases / f"{case_id}.md"
    else:
        raise CaseError("kind 必须是 short 或 article")

    body = "\n\n".join(
        [
            f"# {title}",
            "## 原文全文",
            original,
            _case_index_block(
                case_id=case_id,
                techniques=normalized_techniques,
                extra=writing_fields,
            ),
        ]
    ) + "\n"

    if path.exists():
        raise CaseError(f"内容案例已经存在：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_write_text(layout.root, path, body, config_path=config_path)
    _parse_case(path, kind, layout)
    return path


def write_indexes(
    layout: LibraryLayout,
    cases: Sequence[ContentCase],
    config_path: Path | None = None,
) -> tuple[Path, Path]:
    layout.case_index_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for asset in ("short", "article"):
        path = _index_path(layout, asset)
        managed_write_text(
            layout.root,
            path,
            build_index(cases, layout, asset),
            config_path=config_path,
        )
        paths.append(path)
    return paths[0], paths[1]


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
    add_case_parser.add_argument(
        "--technique", action="append", required=True, choices=TECHNIQUE_ORDER
    )
    add_case_parser.add_argument("--writing-format")
    add_case_parser.add_argument("--writing-purpose")
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
                techniques=args.technique,
                writing_format=args.writing_format,
                writing_purpose=args.writing_purpose,
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
            index_paths = write_indexes(layout, cases, args.config)
            print(
                f"内容案例已保存：{created}\n索引已更新："
                + "、".join(str(path) for path in index_paths)
            )
            return 0

        counts = {
            asset: sum(case.asset == asset for case in cases)
            for asset in ASSET_LABELS
        }
        if args.command == "validate":
            for asset in ("short", "article"):
                path = _index_path(layout, asset)
                expected = build_index(cases, layout, asset)
                if not path.exists():
                    raise CaseError(f"索引不存在：{path}")
                if path.read_text(encoding="utf-8") != expected:
                    raise CaseError(f"索引需要更新：{path}")
            print(
                f"案例库有效：{len(cases)} 条；短内容 {counts['short']} 条，"
                f"文章 {counts['article']} 篇；两个索引按写作技巧独立生成。"
            )
            return 0

        if args.check:
            for asset in ("short", "article"):
                path = _index_path(layout, asset)
                if not path.exists():
                    raise CaseError(f"索引不存在：{path}")
                if path.read_text(encoding="utf-8") != build_index(
                    cases, layout, asset
                ):
                    raise CaseError(f"索引需要更新：{path}")
            print("短内容与文章案例索引有效")
            return 0
        index_paths = write_indexes(layout, cases, args.config)
        print("索引已更新：" + "、".join(str(path) for path in index_paths))
        return 0
    except (CaseError, LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
