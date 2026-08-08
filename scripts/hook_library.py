from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

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


METADATA_PATTERN = re.compile(
    r"\n?<!-- hook-library-index\s*\n(?P<metadata>\{.*\})\n-->\s*$",
    re.DOTALL,
)

TECHNIQUE_ORDER = (
    "利益先行",
    "结果先行",
    "变化先行",
    "问题切入",
    "冲突切入",
    "反常识切入",
    "场景切入",
    "故事切入",
    "信息缺口",
    "对象亮相",
    "数字切入",
    "清单承诺",
    "亲历切入",
    "观点先行",
)
SUPPORTED_TECHNIQUES = set(TECHNIQUE_ORDER)
FORMAT_LABELS = {"short": "短内容", "thread": "Thread", "article": "文章"}


class HookError(ValueError):
    pass


@dataclass(frozen=True)
class HookExample:
    path: Path
    hook_id: str
    title: str
    writing_formats: tuple[str, ...]
    technique: str
    text: str


def _safe_segment(value: str, field: str) -> str:
    cleaned = value.strip()
    if (
        not cleaned
        or cleaned in {".", ".."}
        or any(character in cleaned for character in '<>:"/\\|?*')
    ):
        raise HookError(f"{field} 不能作为目录或文件名：{value}")
    return cleaned


def _metadata_block(value: dict[str, Any]) -> str:
    return "\n".join(
        [
            "<!-- hook-library-index",
            json.dumps(value, ensure_ascii=False, sort_keys=True),
            "-->",
        ]
    )


def _parse_metadata(text: str) -> tuple[dict[str, Any], str]:
    match = METADATA_PATTERN.search(text.lstrip("\ufeff"))
    if not match:
        raise HookError("缺少 hook-library-index")
    try:
        metadata = json.loads(match.group("metadata"))
    except json.JSONDecodeError as exc:
        raise HookError(f"hook-library-index 不是有效 JSON：{exc}") from exc
    if not isinstance(metadata, dict):
        raise HookError("hook-library-index 必须是 JSON 对象")
    return metadata, text[: match.start()].rstrip()


def _required_string(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HookError(f"缺少 {key}")
    return value.strip()


def _writing_formats(metadata: dict[str, Any]) -> tuple[str, ...]:
    value = metadata.get("writing_formats")
    if not isinstance(value, list) or not value:
        raise HookError("writing_formats 必须是非空数组")
    formats = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(formats) != len(value):
        raise HookError("writing_formats 只能包含非空字符串")
    invalid = sorted(set(formats) - set(FORMAT_LABELS))
    if invalid:
        raise HookError("不支持的适用成品形式：" + "、".join(invalid))
    return formats


def _title(body: str) -> str:
    match = re.search(r"^# (.+?)\s*$", body, re.MULTILINE)
    if not match:
        raise HookError("缺少一级标题")
    return match.group(1).strip()


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", body, re.MULTILINE)
    if not match:
        raise HookError(f"缺少“{heading}”")
    return body[match.end() :].strip()


def _hook_text(section: str) -> str:
    text = section.strip()
    if not text:
        raise HookError("钩子原文不能为空")
    if re.search(r"^来源：[^\r\n]+[ \t]*\Z", text, re.MULTILINE):
        raise HookError("钩子不保存来源字段")
    return text


def _parse_hook(path: Path, layout: LibraryLayout) -> HookExample:
    try:
        relative = path.relative_to(layout.hook_root)
    except ValueError as exc:
        raise HookError("钩子必须位于独立 Hook Library 目录") from exc
    if len(relative.parts) != 3 or relative.parts[0] != "Examples":
        raise HookError("钩子必须使用“Examples/写作技巧/文件”路径")
    metadata, body = _parse_metadata(path.read_text(encoding="utf-8-sig"))
    allowed = {"resource_type", "hook_id", "writing_formats"}
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        raise HookError("钩子元数据含有非寻址字段：" + "、".join(unknown))
    if metadata.get("resource_type") != "hook-example":
        raise HookError("resource_type 必须是 hook-example")
    technique = relative.parts[1]
    if technique not in SUPPORTED_TECHNIQUES:
        raise HookError(f"不支持的写作技巧：{technique}")
    hook_id = _required_string(metadata, "hook_id")
    if path.stem != hook_id:
        raise HookError("钩子文件名必须与 hook_id 一致，不能暴露题材或对象")
    text = _hook_text(_section(body, "钩子原文"))
    return HookExample(
        path=path,
        hook_id=hook_id,
        title=_title(body),
        writing_formats=_writing_formats(metadata),
        technique=technique,
        text=text,
    )


def load_library(layout: LibraryLayout) -> tuple[list[HookExample], list[str]]:
    hooks: list[HookExample] = []
    issues: list[str] = []
    ids: dict[str, Path] = {}
    texts: dict[str, Path] = {}
    example_root = layout.hook_root / "Examples"
    paths = sorted(example_root.rglob("*.md")) if example_root.is_dir() else []
    for path in paths:
        try:
            hook = _parse_hook(path, layout)
            previous_id = ids.get(hook.hook_id)
            if previous_id is not None:
                raise HookError(f"hook_id 与 {previous_id} 重复")
            previous_text = texts.get(hook.text)
            if previous_text is not None:
                raise HookError(f"钩子原文与 {previous_text} 重复")
            ids[hook.hook_id] = path
            texts[hook.text] = path
            hooks.append(hook)
        except (HookError, OSError, UnicodeError) as exc:
            issues.append(f"{path}: {exc}")
    return hooks, issues


def _index_path(layout: LibraryLayout, writing_format: str) -> Path:
    return {
        "short": layout.short_hook_index,
        "thread": layout.thread_hook_index,
        "article": layout.article_hook_index,
    }[writing_format]


def build_index(
    hooks: Sequence[HookExample], layout: LibraryLayout, writing_format: str
) -> str:
    if writing_format not in FORMAT_LABELS:
        raise HookError("writing_format 必须是 short、thread 或 article")
    selected = [hook for hook in hooks if writing_format in hook.writing_formats]
    lines = [
        f"# {FORMAT_LABELS[writing_format]}钩子索引",
        "",
        f"本索引只包含明确适用于{FORMAT_LABELS[writing_format]}的钩子，并且只按写作技巧分组。条目和文件名只显示不带题材含义的稳定编号；主题、行业和对象名称不参与选择。先按技巧选编号，再打开实际文件；索引不能替代原文。",
        "",
        f"当前共有 {len(selected)} 条独立钩子。",
        "",
    ]
    for technique in TECHNIQUE_ORDER:
        group = [hook for hook in selected if hook.technique == technique]
        if not group:
            continue
        lines.extend([f"## {technique}", ""])
        for hook in sorted(group, key=lambda item: item.hook_id):
            relative = Path(os.path.relpath(hook.path, layout.hook_root)).as_posix()
            lines.append(f"- [参考 {hook.hook_id}](<{relative}>)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_indexes(
    layout: LibraryLayout,
    hooks: Sequence[HookExample],
    config_path: Path | None = None,
) -> tuple[Path, Path, Path]:
    layout.hook_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for writing_format in FORMAT_LABELS:
        path = _index_path(layout, writing_format)
        managed_write_text(
            layout.root,
            path,
            build_index(hooks, layout, writing_format),
            config_path=config_path,
        )
        paths.append(path)
    return paths[0], paths[1], paths[2]


def add_hook(
    layout: LibraryLayout,
    existing: Sequence[HookExample],
    *,
    input_path: Path,
    title: str,
    hook_id: str,
    writing_formats: Sequence[str],
    technique: str,
    config_path: Path | None = None,
) -> Path:
    title = _safe_segment(title, "title")
    technique = _safe_segment(technique, "technique")
    if technique not in SUPPORTED_TECHNIQUES:
        raise HookError(f"不支持的写作技巧：{technique}")
    normalized_formats = tuple(
        value.strip() for value in writing_formats if value.strip()
    )
    invalid_formats = sorted(set(normalized_formats) - set(FORMAT_LABELS))
    if not normalized_formats:
        raise HookError("至少提供一种适用成品形式")
    if invalid_formats:
        raise HookError("不支持的适用成品形式：" + "、".join(invalid_formats))
    hook_id = hook_id.strip()
    if not hook_id:
        raise HookError("hook_id 不能为空")
    _safe_segment(hook_id, "hook_id")
    if any(item.hook_id == hook_id for item in existing):
        raise HookError(f"hook_id 已经存在：{hook_id}")
    try:
        text = input_path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise HookError(f"输入文件不存在：{input_path}") from exc
    if not text:
        raise HookError("钩子原文不能为空")
    if any(item.text == text for item in existing):
        raise HookError("这份钩子原文已经存在")
    metadata = {
        "resource_type": "hook-example",
        "hook_id": hook_id,
        "writing_formats": list(normalized_formats),
    }
    path = layout.hook_root / "Examples" / technique / f"{hook_id}.md"
    if path.exists():
        raise HookError(f"钩子已经存在：{path}")
    body = "\n\n".join(
        [
            f"# {title}",
            "## 钩子原文",
            text,
            _metadata_block(metadata),
        ]
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_write_text(layout.root, path, body, config_path=config_path)
    _parse_hook(path, layout)
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="维护 100x Learning 独立钩子库")
    parser.add_argument("--library-root", type=Path, help="私人知识库根目录")
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="检查钩子原文与独立索引")
    index = commands.add_parser("build-index", help="重建或核对独立钩子索引")
    index.add_argument("--check", action="store_true")
    add = commands.add_parser("add-hook", help="从用户明确指定的独立原文建立钩子")
    add.add_argument("--input", type=Path, required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--hook-id", required=True)
    add.add_argument(
        "--format", action="append", required=True, choices=tuple(FORMAT_LABELS)
    )
    add.add_argument("--technique", required=True, choices=TECHNIQUE_ORDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = resolve_library_root(args.library_root, args.config)
        layout = validate_library(root)
        hooks, issues = load_library(layout)
        if issues:
            raise HookError("\n".join(issues))
        if args.command == "add-hook":
            created = add_hook(
                layout,
                hooks,
                input_path=args.input,
                title=args.title,
                hook_id=args.hook_id,
                writing_formats=args.format,
                technique=args.technique,
                config_path=args.config,
            )
            hooks, issues = load_library(layout)
            if issues:
                raise HookError("\n".join(issues))
            index_paths = write_indexes(layout, hooks, args.config)
            print(
                f"钩子已保存：{created}\n索引已更新："
                + "、".join(str(path) for path in index_paths)
            )
            return 0
        if args.command == "validate":
            for writing_format in FORMAT_LABELS:
                path = _index_path(layout, writing_format)
                expected = build_index(hooks, layout, writing_format)
                if not path.is_file():
                    raise HookError(f"钩子索引不存在：{path}")
                if path.read_text(encoding="utf-8") != expected:
                    raise HookError(f"钩子索引需要更新：{path}")
            print(f"钩子库有效：{len(hooks)} 条；三个索引按写作技巧独立生成。")
            return 0
        if args.check:
            for writing_format in FORMAT_LABELS:
                path = _index_path(layout, writing_format)
                if not path.is_file():
                    raise HookError(f"钩子索引不存在：{path}")
                if path.read_text(encoding="utf-8") != build_index(
                    hooks, layout, writing_format
                ):
                    raise HookError(f"钩子索引需要更新：{path}")
            print("短内容、Thread 与文章钩子索引有效")
            return 0
        index_paths = write_indexes(layout, hooks, args.config)
        print("钩子索引已更新：" + "、".join(str(path) for path in index_paths))
        return 0
    except (HookError, LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
