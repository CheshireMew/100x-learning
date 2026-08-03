from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_SCHEMA = "100x-learning-durable-project"
PROJECT_VERSION = 1
MANIFEST_NAME = "learning-project.json"
PROJECT_TYPES = ("long-material", "bulk-ingestion")


class ProjectError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _absolute(path: Path) -> Path:
    return path.expanduser().resolve()


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_identity(path: Path) -> dict[str, Any]:
    path = _absolute(path)
    if not path.is_file():
        raise ProjectError(f"来源文件不存在：{path}")
    stat = path.stat()
    return {
        "path": str(path),
        "sha256": _hash(path),
        "size": stat.st_size,
        "modified_ns": stat.st_mtime_ns,
    }


def _project_root(path: Path) -> Path:
    root = _absolute(path)
    if root.exists() and not root.is_dir():
        raise ProjectError(f"项目根不是目录：{root}")
    return root


def _manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def _write_manifest(root: Path, value: dict[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = _manifest_path(root)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def _load_manifest(root: Path) -> dict[str, Any]:
    path = _manifest_path(root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectError(f"学习项目尚未初始化：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectError(f"学习项目清单不是有效 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectError(f"学习项目清单必须是 JSON 对象：{path}")
    if value.get("schema") != PROJECT_SCHEMA or value.get("version") != PROJECT_VERSION:
        raise ProjectError(f"学习项目清单版本不受支持：{path}")
    if value.get("project_type") not in PROJECT_TYPES:
        raise ProjectError(f"学习项目类型无效：{path}")
    if not isinstance(value.get("units"), list):
        raise ProjectError(f"学习项目 units 必须是数组：{path}")
    return value


def initialize_project(root: Path, project_type: str, title: str) -> tuple[dict[str, Any], bool]:
    root = _project_root(root)
    title = title.strip()
    if not title:
        raise ProjectError("学习项目标题不能为空")
    path = _manifest_path(root)
    if path.exists():
        current = _load_manifest(root)
        if current["project_type"] != project_type or current["title"] != title:
            raise ProjectError(f"目标目录已经属于另一个学习项目：{path}")
        return current, False
    if root.exists() and any(root.iterdir()):
        raise ProjectError(f"目标目录已有其它内容，不能初始化学习项目：{root}")
    now = _now()
    value: dict[str, Any] = {
        "schema": PROJECT_SCHEMA,
        "version": PROJECT_VERSION,
        "project_type": project_type,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "units": [],
        "final": None,
    }
    _write_manifest(root, value)
    return value, True


def _unit(value: dict[str, Any], unit_id: str) -> dict[str, Any]:
    matches = [unit for unit in value["units"] if unit.get("id") == unit_id]
    if len(matches) != 1:
        raise ProjectError(f"找不到唯一工作单元：{unit_id}")
    return matches[0]


def add_unit(
    root: Path,
    source: Path,
    label: str,
    locator: str,
) -> tuple[dict[str, Any], bool]:
    root = _project_root(root)
    value = _load_manifest(root)
    label = label.strip()
    locator = locator.strip()
    if not label or not locator:
        raise ProjectError("工作单元的 label 和 locator 都不能为空")
    source_identity = _file_identity(source)
    duplicate = next(
        (
            unit
            for unit in value["units"]
            if unit["source"]["path"] == source_identity["path"]
            and unit["locator"] == locator
        ),
        None,
    )
    if duplicate is not None:
        if duplicate["source"]["sha256"] != source_identity["sha256"]:
            raise ProjectError(
                f"同一定位的来源内容已经变化，不能覆盖原工作单元：{duplicate['id']}"
            )
        return duplicate, False
    unit_id = f"unit-{len(value['units']) + 1:04d}"
    unit = {
        "id": unit_id,
        "label": label,
        "locator": locator,
        "source": source_identity,
        "status": "pending",
        "output": None,
        "completed_at": None,
    }
    value["units"].append(unit)
    value["updated_at"] = _now()
    value["final"] = None
    _write_manifest(root, value)
    return unit, True


def _inside(root: Path, path: Path) -> Path:
    path = path if path.is_absolute() else root / path
    resolved = _absolute(path)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectError(f"工作单元输出必须位于学习项目根目录内：{resolved}") from exc
    return resolved


def _check_source(unit: dict[str, Any]) -> str | None:
    source = Path(unit["source"]["path"])
    if not source.is_file():
        return f"来源文件不存在：{source}"
    current = _hash(source)
    if current != unit["source"]["sha256"]:
        return f"来源内容已经变化：{source}"
    return None


def record_unit(root: Path, unit_id: str, output: Path) -> dict[str, Any]:
    root = _project_root(root)
    value = _load_manifest(root)
    unit = _unit(value, unit_id)
    source_issue = _check_source(unit)
    if source_issue:
        raise ProjectError(source_issue)
    output_path = _inside(root, output)
    if not output_path.is_file():
        raise ProjectError(f"工作单元输出不存在：{output_path}")
    unit["status"] = "complete"
    unit["output"] = {
        "path": output_path.relative_to(root).as_posix(),
        "sha256": _hash(output_path),
        "size": output_path.stat().st_size,
    }
    unit["completed_at"] = _now()
    value["updated_at"] = unit["completed_at"]
    value["final"] = None
    _write_manifest(root, value)
    return unit


def project_status(root: Path) -> dict[str, Any]:
    root = _project_root(root)
    value = _load_manifest(root)
    issues: list[dict[str, str]] = []
    unit_issues: list[dict[str, str]] = []
    complete = 0
    for unit in value["units"]:
        source_issue = _check_source(unit)
        if source_issue:
            unit_issues.append(
                {"unit": unit["id"], "kind": "source", "message": source_issue}
            )
        if unit.get("status") != "complete":
            continue
        output = unit.get("output")
        if not isinstance(output, dict):
            unit_issues.append(
                {"unit": unit["id"], "kind": "output", "message": "完成单元缺少输出记录"}
            )
            continue
        output_path = _inside(root, Path(output["path"]))
        if not output_path.is_file():
            unit_issues.append(
                {
                    "unit": unit["id"],
                    "kind": "output",
                    "message": f"工作单元输出不存在：{output_path}",
                }
            )
        elif _hash(output_path) != output.get("sha256"):
            unit_issues.append(
                {
                    "unit": unit["id"],
                    "kind": "output",
                    "message": f"工作单元输出已经变化：{output_path}",
                }
            )
        else:
            complete += 1
    issues.extend(unit_issues)
    total = len(value["units"])
    ready_to_finalize = total > 0 and complete == total and not unit_issues
    final = value.get("final")
    final_valid = False
    if final is not None:
        if not isinstance(final, dict) or not isinstance(final.get("path"), str):
            issues.append(
                {"unit": "final", "kind": "final", "message": "最终成品记录无效"}
            )
        else:
            try:
                final_path = _inside(root, Path(final["path"]))
            except ProjectError as exc:
                issues.append(
                    {"unit": "final", "kind": "final", "message": str(exc)}
                )
            else:
                if not final_path.is_file():
                    issues.append(
                        {
                            "unit": "final",
                            "kind": "final",
                            "message": f"最终成品不存在：{final_path}",
                        }
                    )
                elif _hash(final_path) != final.get("sha256"):
                    issues.append(
                        {
                            "unit": "final",
                            "kind": "final",
                            "message": f"最终成品已经变化：{final_path}",
                        }
                    )
                else:
                    final_valid = True
    return {
        "schema": PROJECT_SCHEMA,
        "version": PROJECT_VERSION,
        "project_root": str(root),
        "project_type": value["project_type"],
        "title": value["title"],
        "total_units": total,
        "complete_units": complete,
        "pending_units": total - complete,
        "ready_to_finalize": ready_to_finalize,
        "final_valid": final_valid,
        "project_complete": ready_to_finalize and final_valid,
        "issues": issues,
        "final": final,
    }


def finalize_project(root: Path, aggregate: Path) -> dict[str, Any]:
    root = _project_root(root)
    status = project_status(root)
    if not status["ready_to_finalize"]:
        raise ProjectError("仍有未完成、来源变化或输出失效的工作单元，不能完成项目")
    aggregate_path = _inside(root, aggregate)
    if not aggregate_path.is_file():
        raise ProjectError(f"汇总成品不存在：{aggregate_path}")
    value = _load_manifest(root)
    value["final"] = {
        "path": aggregate_path.relative_to(root).as_posix(),
        "sha256": _hash(aggregate_path),
        "size": aggregate_path.stat().st_size,
        "finalized_at": _now(),
    }
    value["updated_at"] = value["final"]["finalized_at"]
    _write_manifest(root, value)
    return value["final"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="维护可恢复的长材料与批量知识接入项目")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="初始化一个空的学习项目")
    init.add_argument("--project-root", type=Path, required=True)
    init.add_argument("--type", choices=PROJECT_TYPES, required=True)
    init.add_argument("--title", required=True)

    add = commands.add_parser("add-unit", help="把真实来源及其语义定位加入项目")
    add.add_argument("--project-root", type=Path, required=True)
    add.add_argument("--source", type=Path, required=True)
    add.add_argument("--label", required=True)
    add.add_argument("--locator", required=True)

    record = commands.add_parser("record-unit", help="登记工作单元的真实输出")
    record.add_argument("--project-root", type=Path, required=True)
    record.add_argument("--unit", required=True)
    record.add_argument("--output", type=Path, required=True)

    status = commands.add_parser("status", help="核对来源、输出与当前完成状态")
    status.add_argument("--project-root", type=Path, required=True)

    finalize = commands.add_parser("finalize", help="在全部单元有效后登记汇总成品")
    finalize.add_argument("--project-root", type=Path, required=True)
    finalize.add_argument("--aggregate", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            value, created = initialize_project(args.project_root, args.type, args.title)
            payload = {
                "ok": True,
                "action": "initialized" if created else "already-initialized",
                "project_root": str(_project_root(args.project_root)),
                "project_type": value["project_type"],
                "title": value["title"],
            }
        elif args.command == "add-unit":
            unit, created = add_unit(
                args.project_root,
                args.source,
                args.label,
                args.locator,
            )
            payload = {
                "ok": True,
                "action": "unit-added" if created else "unit-already-exists",
                "unit": unit,
            }
        elif args.command == "record-unit":
            payload = {
                "ok": True,
                "action": "unit-recorded",
                "unit": record_unit(args.project_root, args.unit, args.output),
            }
        elif args.command == "status":
            payload = {"ok": True, "action": "status", **project_status(args.project_root)}
        else:
            payload = {
                "ok": True,
                "action": "finalized",
                "final": finalize_project(args.project_root, args.aggregate),
            }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (ProjectError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
