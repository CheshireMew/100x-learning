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
    "结果钩子",
    "痛点钩子",
    "问题钩子",
    "反常识钩子",
    "冲突钩子",
    "故事钩子",
    "信息缺口钩子",
    "对象亮相钩子",
    "数字钩子",
    "清单钩子",
    "亲历钩子",
    "热点钩子",
)


class HookError(ValueError):
    pass


@dataclass(frozen=True)
class HookExample:
    path: Path
    hook_id: str
    title: str
    writing_format: str
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
    return text


def _parse_hook(path: Path, layout: LibraryLayout) -> HookExample:
    try:
        relative = path.relative_to(layout.hook_root)
    except ValueError as exc:
        raise HookError("钩子必须位于独立 Hook Library 目录") from exc
    if len(relative.parts) != 3:
        raise HookError("钩子必须使用“成品形态/开头手法/文件”三级路径")
    metadata, body = _parse_metadata(path.read_text(encoding="utf-8-sig"))
    allowed = {"resource_type", "hook_id", "writing_format"}
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        raise HookError("钩子元数据含有非寻址字段：" + "、".join(unknown))
    if metadata.get("resource_type") != "hook-example":
        raise HookError("resource_type 必须是 hook-example")
    writing_format = _required_string(metadata, "writing_format")
    if writing_format != relative.parts[0]:
        raise HookError("writing_format 必须与钩子目录一致")
    text = _hook_text(_section(body, "钩子原文"))
    return HookExample(
        path=path,
        hook_id=_required_string(metadata, "hook_id"),
        title=_title(body),
        writing_format=writing_format,
        technique=relative.parts[1],
        text=text,
    )


def load_library(layout: LibraryLayout) -> tuple[list[HookExample], list[str]]:
    hooks: list[HookExample] = []
    issues: list[str] = []
    ids: dict[str, Path] = {}
    texts: dict[str, Path] = {}
    paths = sorted(layout.hook_root.rglob("*.md")) if layout.hook_root.is_dir() else []
    for path in paths:
        if path == layout.hook_index:
            continue
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


def _index_label(hook: HookExample) -> str:
    first = re.split(r"[。！？!?\n]", hook.text, maxsplit=1)[0].strip()
    title_key = hook.title.rstrip("。！？!?：:… ")
    first_key = first.rstrip("。！？!?：:… ")
    if title_key != first_key or len(first) >= 24:
        return hook.title
    collapsed = re.sub(r"\s+", " ", hook.text).strip()
    if len(collapsed) > 90:
        collapsed = collapsed[:89].rstrip() + "…"
    return collapsed


def build_index(hooks: Sequence[HookExample], layout: LibraryLayout) -> str:
    lines = [
        "# 开头钩子索引",
        "",
        "本索引先按开头手法、再按原始成品形态定位独立钩子。主题不参与分组；成品形态只标明来源，不限制文章、短帖或 Thread 跨形态使用。写作时打开实际文件，索引不能替代原文。",
        "",
        f"当前共有 {len(hooks)} 条独立钩子。",
        "",
    ]
    groups: dict[tuple[str, str], list[HookExample]] = {}
    for hook in hooks:
        groups.setdefault((hook.writing_format, hook.technique), []).append(hook)
    technique_order = {
        technique: index for index, technique in enumerate(TECHNIQUE_ORDER)
    }
    techniques = sorted(
        {technique for _, technique in groups},
        key=lambda technique: (
            technique_order.get(technique, len(technique_order)),
            technique,
        ),
    )
    for technique in techniques:
        lines.extend([f"## {technique}", ""])
        writing_formats = sorted(
            writing_format
            for writing_format, group_technique in groups
            if group_technique == technique
        )
        for writing_format in writing_formats:
            lines.extend([f"### {writing_format}", ""])
            for hook in sorted(
                groups[(writing_format, technique)], key=lambda item: item.title
            ):
                relative = Path(
                    os.path.relpath(hook.path, layout.hook_root)
                ).as_posix()
                lines.append(f"- [{_index_label(hook)}](<{relative}>)")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_index(
    layout: LibraryLayout,
    hooks: Sequence[HookExample],
    config_path: Path | None = None,
) -> Path:
    layout.hook_root.mkdir(parents=True, exist_ok=True)
    managed_write_text(
        layout.root,
        layout.hook_index,
        build_index(hooks, layout),
        config_path=config_path,
    )
    return layout.hook_index


def add_hook(
    layout: LibraryLayout,
    existing: Sequence[HookExample],
    *,
    input_path: Path,
    title: str,
    hook_id: str,
    writing_format: str,
    technique: str,
    config_path: Path | None = None,
) -> Path:
    title = _safe_segment(title, "title")
    writing_format = _safe_segment(writing_format, "writing_format")
    technique = _safe_segment(technique, "technique")
    hook_id = hook_id.strip()
    if not hook_id:
        raise HookError("hook_id 不能为空")
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
        "writing_format": writing_format,
    }
    path = layout.hook_root / writing_format / technique / f"{title}.md"
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
    add.add_argument("--writing-format", required=True)
    add.add_argument("--technique", required=True)
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
                writing_format=args.writing_format,
                technique=args.technique,
                config_path=args.config,
            )
            hooks, issues = load_library(layout)
            if issues:
                raise HookError("\n".join(issues))
            index_path = write_index(layout, hooks, args.config)
            print(f"钩子已保存：{created}\n索引已更新：{index_path}")
            return 0
        expected = build_index(hooks, layout)
        if args.command == "validate":
            if not layout.hook_index.is_file():
                raise HookError(f"钩子索引不存在：{layout.hook_index}")
            if layout.hook_index.read_text(encoding="utf-8") != expected:
                raise HookError(f"钩子索引需要更新：{layout.hook_index}")
            print(f"钩子库有效：{len(hooks)} 条；索引：{layout.hook_index}")
            return 0
        if args.check:
            if not layout.hook_index.is_file():
                raise HookError(f"钩子索引不存在：{layout.hook_index}")
            if layout.hook_index.read_text(encoding="utf-8") != expected:
                raise HookError(f"钩子索引需要更新：{layout.hook_index}")
            print(f"钩子索引有效：{layout.hook_index}")
            return 0
        index_path = write_index(layout, hooks, args.config)
        print(f"钩子索引已更新：{index_path}")
        return 0
    except (HookError, LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
