from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from private_library import (
    LibraryError,
    default_config_path,
    resolve_library_root,
    validate_library,
)


class MarktreeIntegrationError(ValueError):
    pass


@dataclass(frozen=True)
class ManagedWrite:
    path: Path
    content: str


def configured_marktree_cli(
    config_path: Path | None = None,
    explicit: Path | None = None,
    library_root: Path | None = None,
) -> Path | None:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    environment = os.environ.get("MARKTREE_CLI", "").strip()
    if environment:
        candidates.append(Path(environment))
    config = (config_path or default_config_path()).expanduser().resolve()
    if config.is_file():
        try:
            value = json.loads(config.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MarktreeIntegrationError(f"无法读取私人库配置：{config}") from exc
        configured = value.get("marktree_cli") if isinstance(value, dict) else None
        raw_root = value.get("library_root") if isinstance(value, dict) else None
        same_library = library_root is None or (
            isinstance(raw_root, str)
            and Path(raw_root).expanduser().resolve() == library_root.expanduser().resolve()
        )
        if same_library and isinstance(configured, str) and configured.strip():
            candidates.append(Path(configured))
    discovered = shutil.which("marktree-cli")
    if discovered:
        candidates.append(Path(discovered))

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.is_file():
            return resolved
    if candidates:
        raise MarktreeIntegrationError(
            "已配置的 marktree-cli 不可用：" + "、".join(str(path) for path in candidates)
        )
    return None


def run_marktree(
    arguments: Sequence[str],
    *,
    config_path: Path | None = None,
    marktree_cli: Path | None = None,
    library_root: Path | None = None,
    stdin: str | None = None,
) -> dict[str, Any]:
    executable = configured_marktree_cli(config_path, marktree_cli, library_root)
    if executable is None:
        raise MarktreeIntegrationError(
            "尚未配置 marktree-cli；先运行 private_library.py configure-marktree --cli <路径>"
        )
    result = subprocess.run(
        [str(executable), *arguments],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MarktreeIntegrationError(
            f"marktree-cli 没有返回有效 JSON：{result.stdout or result.stderr}"
        ) from exc
    if not isinstance(payload, dict):
        raise MarktreeIntegrationError("marktree-cli 返回值必须是 JSON 对象")
    if result.returncode != 0 or payload.get("ok") is not True:
        error = payload.get("error")
        message = error.get("message") if isinstance(error, dict) else None
        raise MarktreeIntegrationError(message or result.stderr or "Marktree 操作失败")
    return payload


def managed_write_text(
    library_root: Path,
    path: Path,
    content: str,
    *,
    config_path: Path | None = None,
    marktree_cli: Path | None = None,
) -> Path:
    return managed_write_batch(
        library_root,
        [ManagedWrite(path=path, content=content)],
        config_path=config_path,
        marktree_cli=marktree_cli,
    )[0]


def managed_write_batch(
    library_root: Path,
    writes: Sequence[ManagedWrite],
    *,
    config_path: Path | None = None,
    marktree_cli: Path | None = None,
) -> list[Path]:
    root = library_root.expanduser().resolve()
    executable = configured_marktree_cli(config_path, marktree_cli, root)
    targets: list[Path] = []
    requests: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for write in writes:
        target = write.path.expanduser().resolve()
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise MarktreeIntegrationError(f"写入路径不在私人知识库内：{target}") from exc
        if target in seen:
            raise MarktreeIntegrationError(f"同一批次不能重复写入：{relative}")
        seen.add(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = target.read_bytes() if target.is_file() else None
        encoding = "utf8Bom" if raw is not None and raw.startswith(b"\xef\xbb\xbf") else "utf8"
        request: dict[str, Any] = {
            "path": relative.as_posix(),
            "content": write.content,
            "encoding": encoding,
        }
        if raw is None:
            request["expectedMissing"] = True
        else:
            request["expectedSha256"] = hashlib.sha256(raw).hexdigest()
        targets.append(target)
        requests.append(request)

    if not requests:
        raise MarktreeIntegrationError("写入批次不能为空")
    if executable is None:
        for target, write in zip(targets, writes, strict=True):
            target.write_bytes(write.content.encode("utf-8"))
        return targets

    run_marktree(
        ["document", "write-batch"],
        config_path=config_path,
        marktree_cli=executable,
        library_root=root,
        stdin=json.dumps(
            {"root": str(root), "writes": requests},
            ensure_ascii=False,
        ),
    )
    for target, request in zip(targets, requests, strict=True):
        expected = request["content"].encode("utf-8")
        if request["encoding"] == "utf8Bom":
            expected = b"\xef\xbb\xbf" + expected
        if target.read_bytes() != expected:
            raise MarktreeIntegrationError(f"Marktree 写后字节核对失败：{target}")
    return targets


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通过 Marktree 管理私人知识库文件和可选 Git")
    parser.add_argument("--library-root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--marktree-cli", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="检查当前私人库的 Marktree 能力")
    write = commands.add_parser("write", help="从标准输入安全写入一个 UTF-8 文档")
    write.add_argument("--path", type=Path, required=True)
    commands.add_parser("write-batch", help="从标准输入接收 writes JSON 批量写入")
    commands.add_parser("changes", help="读取 Marktree 精确变更清单")
    commands.add_parser("sync-plan", help="预览 Marktree Git 同步路径")
    commands.add_parser("sync", help="提交并同步 Marktree 管理的精确路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = resolve_library_root(args.library_root, args.config)
        validate_library(root)
        if args.command == "status":
            payload = run_marktree(
                ["workspace", "inspect", "--root", str(root)],
                config_path=args.config,
                marktree_cli=args.marktree_cli,
                library_root=root,
            )
        elif args.command == "write":
            target = (root / args.path).resolve()
            managed_write_text(
                root,
                target,
                sys.stdin.read(),
                config_path=args.config,
                marktree_cli=args.marktree_cli,
            )
            payload = {"ok": True, "command": "knowledge.write", "data": str(target)}
        elif args.command == "write-batch":
            value = json.loads(sys.stdin.read())
            raw_writes = value.get("writes") if isinstance(value, dict) else None
            if not isinstance(raw_writes, list):
                raise MarktreeIntegrationError("write-batch 需要 writes 数组")
            writes = [
                ManagedWrite(
                    path=(root / item["path"]).resolve(),
                    content=item["content"],
                )
                for item in raw_writes
                if isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and isinstance(item.get("content"), str)
            ]
            if len(writes) != len(raw_writes):
                raise MarktreeIntegrationError("每个 writes 项都必须包含 path 和 content 字符串")
            targets = managed_write_batch(
                root,
                writes,
                config_path=args.config,
                marktree_cli=args.marktree_cli,
            )
            payload = {
                "ok": True,
                "command": "knowledge.writeBatch",
                "data": [str(path) for path in targets],
            }
        else:
            command = {
                "changes": ["changes", "--root", str(root)],
                "sync-plan": ["sync", "plan", "--root", str(root)],
                "sync": ["sync", "run", "--root", str(root)],
            }[args.command]
            payload = run_marktree(
                command,
                config_path=args.config,
                marktree_cli=args.marktree_cli,
                library_root=root,
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (
        LibraryError,
        MarktreeIntegrationError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
