from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.content_cases import (  # noqa: E402
    INDEX_PATH,
    ContentCaseError,
    build_index,
    load_library,
    render_search_results,
    search_library,
)


def _split_values(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(
            item.strip()
            for item in value.split(",")
            if item.strip()
        )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="校验、检索并维护 100x Learning 的本地内容案例库。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="校验案例结构和重复来源")
    validate.add_argument("--json", action="store_true")

    search = subparsers.add_parser(
        "search",
        help="按写作任务、主题和结构检索，并直接输出案例全文",
    )
    search.add_argument("--writing-task", required=True)
    search.add_argument(
        "--content-type",
        required=True,
        help="正文案例的内容类型；钩子仍按写作任务、主题和结构匹配。",
    )
    search.add_argument("--topic", action="append")
    search.add_argument("--structure", action="append")
    search.add_argument(
        "--asset",
        action="append",
        choices=("hook", "short", "article"),
        help="要读取的成品形态，可重复；默认 short。",
    )
    search.add_argument("--limit", type=int, default=3)
    search.add_argument("--json", action="store_true")

    index = subparsers.add_parser("build-index", help="生成或核对案例索引")
    index.add_argument(
        "--check",
        action="store_true",
        help="只核对索引是否与案例目录一致，不写入",
    )
    return parser


def _case_payload(hit) -> dict[str, object]:
    case = hit.case
    return {
        "path": str(case.path),
        "asset": case.asset,
        "content_type": case.content_type,
        "title": case.title,
        "writing_task": case.writing_task,
        "topics": list(case.topics),
        "structure": list(case.structure),
        "score": round(hit.score, 4),
        "original_text": case.original_text,
        "borrow_notes": case.borrow_notes,
        "use_cases": case.use_cases,
        "source_url": case.source_url,
        "authorship": case.authorship,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        cases, issues = load_library()
        payload = {
            "ok": not issues,
            "case_count": len(cases),
            "hook_count": sum(case.asset == "hook" for case in cases),
            "short_count": sum(case.asset == "short" for case in cases),
            "article_count": sum(case.asset == "article" for case in cases),
            "issues": issues,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif issues:
            print("\n".join(issues), file=sys.stderr)
        else:
            print(
                f"案例库有效：{payload['case_count']} 条，"
                f"其中钩子 {payload['hook_count']} 条，"
                f"完整短内容 {payload['short_count']} 条，"
                f"完整文章 {payload['article_count']} 篇。"
            )
        return 0 if not issues else 1

    if args.command == "search":
        try:
            hits = search_library(
                writing_task=args.writing_task,
                topics=_split_values(args.topic),
                structures=_split_values(args.structure),
                assets=args.asset or ["short"],
                content_type=args.content_type,
                limit=args.limit,
            )
        except ContentCaseError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(
                json.dumps(
                    [_case_payload(hit) for hit in hits],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(render_search_results(hits), end="")
        return 0

    cases, issues = load_library()
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
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
