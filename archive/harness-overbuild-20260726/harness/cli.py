from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from .knowledge import validate_knowledge_note
from .policies import (
    validate_content_audit,
    validate_distribution_contract,
    validate_evidence_bundle,
    validate_task_contract,
    validate_writing_packet,
    validate_write_plan,
)
from .repository import validate_repository
from .result import ValidationReport


def _load_json(source: str, root: Path) -> dict[str, Any]:
    if source == "-":
        text = sys.stdin.read()
    else:
        path = Path(source)
        if not path.is_absolute():
            path = root / path
        text = path.read_text(encoding="utf-8-sig")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("JSON 顶层必须是对象")
    return value


def _emit(report: ValidationReport) -> int:
    json.dump(report.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if report.ok else 1


def _validation_command(
    source: str,
    root: Path,
    validator: Callable[[dict[str, Any]], ValidationReport],
) -> int:
    try:
        data = _load_json(source, root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        report = ValidationReport()
        report.error("input.invalid_json", str(exc), source)
        return _emit(report)
    return _emit(validator(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="100x-learning deterministic harness")
    parser.add_argument("--root", default=".", help="skill repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="validate repository structure")

    for name in (
        "validate-task",
        "validate-writing",
        "validate-audit",
        "validate-distribution",
        "validate-write",
        "validate-evidence",
    ):
        command = subparsers.add_parser(name)
        command.add_argument("input", help="JSON file path, or - for stdin")
    note = subparsers.add_parser(
        "validate-note",
        help="validate a persisted 10-Knowledge Markdown note",
    )
    note.add_argument("path", help="knowledge note path, relative to repository root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "doctor":
        return _emit(validate_repository(root))
    if args.command == "validate-task":
        return _validation_command(args.input, root, validate_task_contract)
    if args.command == "validate-evidence":
        return _validation_command(args.input, root, validate_evidence_bundle)
    if args.command == "validate-writing":
        return _validation_command(args.input, root, validate_writing_packet)
    if args.command == "validate-audit":
        return _validation_command(args.input, root, validate_content_audit)
    if args.command == "validate-distribution":
        return _validation_command(
            args.input,
            root,
            validate_distribution_contract,
        )
    if args.command == "validate-write":
        return _validation_command(
            args.input,
            root,
            lambda data: validate_write_plan(data, root),
        )
    if args.command == "validate-note":
        note_path = Path(args.path)
        if not note_path.is_absolute():
            note_path = root / note_path
        return _emit(validate_knowledge_note(note_path, root / "System Knowledge"))
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
