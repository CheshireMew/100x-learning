from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.content_case_library import add_case, load_library as load_cases
from scripts.private_library import initialize_library
from scripts.writing_memory import (
    CONFIG_RELATIVE,
    INDEX_RELATIVE,
    MemoryError,
    discover_records,
    index_is_current,
    load_index,
    search_memory,
    write_index,
)


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "writing_memory.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class WritingMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.layout, _, _ = initialize_library(
            self.temp_root / "private-library",
            self.temp_root / "config.json",
        )
        self.project_root = self.layout.root
        self.blog_root = self.project_root / "20-Sources" / "Articles" / "Published"
        self.output_root = self.layout.writing_outputs
        self.blog_root.mkdir(parents=True, exist_ok=True)
        (self.project_root / CONFIG_RELATIVE).write_text(
            json.dumps(
                {
                    "published_article_roots": ["20-Sources/Articles/Published"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_publication_history_keeps_ai_work_but_does_not_inherit_voice(self) -> None:
        _write(
            self.blog_root / "published.md",
            """---
authorship: "本人主导"
content_type: "教程与操作指南"
source_url: "https://example.com/published/"
---
# 已发布版本

旧正文。
""",
        )
        _write(
            self.blog_root / "ai-draft.md",
            """---
authorship: "AI 主笔"
content_type: "教程与操作指南"
source_url: "https://example.com/ai/"
---
# AI 草稿

不能进入作者证据。
""",
        )
        _write(
            self.output_root / "Articles" / "confirmed.md",
            """---
type: writing-output
status: final
source: published-article
author: 柴郡
updated: 2026-07-29
published_url: "https://example.com/published/"
---
# 用户确认版本

新正文，应该成为唯一活动记录。
""",
        )
        _write(
            self.output_root / "Drafts" / "draft.md",
            """---
type: writing-output
status: draft
source: user-confirmed
format: original
---
# 未完成草稿

不能进入作者证据。
""",
        )

        records, receipt = discover_records(self.project_root)

        self.assertEqual(2, len(records))
        by_url = {record.source_url: record for record in records}
        confirmed = by_url["https://example.com/published/"]
        ai_work = by_url["https://example.com/ai/"]
        self.assertEqual("用户确认版本", confirmed.title)
        self.assertEqual("教程与操作指南", confirmed.content_type)
        self.assertEqual("writing-output", confirmed.source_kind)
        self.assertEqual("unknown", confirmed.writing_origin)
        self.assertFalse(confirmed.voice_eligible)
        self.assertEqual("ai-generated", ai_work.writing_origin)
        self.assertFalse(ai_work.voice_eligible)
        self.assertEqual(2, receipt.accepted_blog)
        self.assertEqual(1, receipt.merged_by_url)

    def test_formal_article_body_is_consumed_as_authored_evidence(self) -> None:
        _write(
            self.blog_root / "case.md",
            """---
authorship: "本人主导"
content_type: "个人观察与实测"
source_url: "https://example.com/case/"
---
# 本人文章

这是实际发布正文。
""",
        )
        records, _ = discover_records(self.project_root)
        write_index(self.project_root, records)

        hits = search_memory(
            library_root=self.project_root,
            records=load_index(self.project_root),
            purpose="novelty",
            query="实际发布正文",
            format_name="article",
            content_type=None,
            limit=1,
        )
        self.assertIn("实际发布正文", hits[0].opening)

    def test_explicit_writing_metadata_adds_a_case_without_account_or_source(self) -> None:
        case_inputs = self.temp_root / "case-inputs"
        eligible_input = case_inputs / "eligible.md"
        unknown_input = case_inputs / "unknown.md"
        ordinary_input = case_inputs / "ordinary.md"
        _write(eligible_input, "我真正想减少的是上下文切换，而不只是点击次数。")
        _write(unknown_input, "这条内容明确保存为写作记录，但没有标注写法来源。")
        _write(ordinary_input, "这只是普通参考案例，不进入写作记忆。")
        existing: list = []
        add_case(
            self.layout,
            existing,
            kind="short",
            input_path=eligible_input,
            title="写作案例",
            techniques=("亲历切入", "机制拆解"),
            writing_format="product",
            writing_purpose="个人观察与实测",
            writing_origin="human-edited",
            voice_eligible=True,
        )
        existing, issues = load_cases(self.layout)
        self.assertFalse(issues)
        add_case(
            self.layout,
            existing,
            kind="short",
            input_path=unknown_input,
            title="写法未知",
            techniques=("结果先行",),
            writing_format="product",
            writing_purpose="个人观察与实测",
        )
        existing, issues = load_cases(self.layout)
        self.assertFalse(issues)
        add_case(
            self.layout,
            existing,
            kind="short",
            input_path=ordinary_input,
            title="普通案例",
            techniques=("观点先行",),
        )

        records, receipt = discover_records(self.project_root)

        self.assertEqual(2, len(records))
        eligible = next(record for record in records if record.title == "写作案例")
        unknown = next(record for record in records if record.title == "写法未知")
        self.assertEqual("writing-case", eligible.source_kind)
        self.assertEqual("product", eligible.format)
        self.assertEqual("个人观察与实测", eligible.content_type)
        self.assertEqual("", eligible.updated)
        self.assertEqual("", eligible.source_url)
        self.assertEqual("human-edited", eligible.writing_origin)
        self.assertTrue(eligible.voice_eligible)
        self.assertEqual("unknown", unknown.writing_origin)
        self.assertFalse(unknown.voice_eligible)
        self.assertEqual(3, receipt.scanned_cases)
        self.assertEqual(2, receipt.accepted_cases)
        write_index(self.project_root, records)
        novelty_hits = search_memory(
            library_root=self.project_root,
            records=load_index(self.project_root),
            purpose="novelty",
            query="减少上下文切换",
            format_name="product",
            content_type=None,
            limit=1,
        )
        self.assertIn("上下文切换", novelty_hits[0].opening)
        self.assertNotIn("content-case-index", novelty_hits[0].ending)
        voice_hits = search_memory(
            library_root=self.project_root,
            records=load_index(self.project_root),
            purpose="voice",
            query="",
            format_name="product",
            content_type="个人观察与实测",
            limit=3,
        )
        self.assertEqual(["写作案例"], [hit.record.title for hit in voice_hits])

    def test_marked_writing_case_requires_its_actual_writing_format(self) -> None:
        case = (
            self.project_root
            / "20-Sources"
            / "Social Posts"
            / "Content Cases"
            / "完整短内容"
            / "缺少形态.md"
        )
        _write(
            case,
            """# 缺少形态

## 原文全文

这是本人发布的产品介绍。

<!-- content-case-index
writing_origin: "human"
writing_techniques: ["结果先行"]
-->
""",
        )

        with self.assertRaisesRegex(MemoryError, "缺少 writing_format"):
            discover_records(self.project_root)

    def test_unknown_writing_memory_configuration_is_rejected(self) -> None:
        _write(
            self.project_root / CONFIG_RELATIVE,
            json.dumps(
                {
                    "unexpected_field": [],
                    "published_article_roots": ["20-Sources/Articles/Published"],
                }
            ),
        )
        with self.assertRaisesRegex(ValueError, "不受支持的字段"):
            discover_records(self.project_root)

    def test_index_output_is_consumed_by_same_format_search(self) -> None:
        _write(
            self.output_root / "Articles" / "article.md",
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
updated: 2026-07-29
format: article
content_type: 个人观察与实测
---
# 文章

这个工具真正省下来的不是点击次数，而是来回切换上下文。
""",
        )
        _write(
            self.output_root / "Social" / "X" / "original.md",
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
updated: 2026-07-28
format: original
content_type: 项目与产品介绍
---
# 独立帖

我试了一个新的写作工具，最后留下的是更完整的工作流。
""",
        )

        records, _ = discover_records(self.project_root)
        index_path = write_index(self.project_root, records)
        self.assertEqual(self.project_root / INDEX_RELATIVE, index_path)
        self.assertTrue(index_is_current(self.project_root, records))

        indexed = load_index(self.project_root)
        hits = search_memory(
            library_root=self.project_root,
            records=indexed,
            purpose="novelty",
            query="工具如何减少上下文切换",
            format_name="article",
            content_type=None,
            limit=3,
        )

        self.assertEqual(1, len(hits))
        self.assertEqual("article", hits[0].record.format)
        self.assertIn("上下文", hits[0].opening)

    def test_cli_build_then_search_reads_generated_index(self) -> None:
        _write(
            self.output_root / "Social" / "X" / "thread.md",
            """---
type: writing-output
status: final
source: published-thread
author: 柴郡
updated: 2026-07-29
format: thread
published_url: "https://x.com/example/status/1"
---
# 一条旧 Thread

先看问题怎样发生，再看哪个机制真正改变了结果。
""",
        )

        build = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--library-root",
                str(self.project_root),
                "build-index",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, build.returncode, build.stderr)
        receipt = json.loads(build.stdout)
        self.assertEqual(1, receipt["records"])

        search = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--library-root",
                str(self.project_root),
                "search",
                "--purpose",
                "novelty",
                "--query",
                "问题发生后哪个机制改变结果",
                "--format",
                "thread",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, search.returncode, search.stderr)
        self.assertIn("数据来源：发布记录索引", search.stdout)
        self.assertIn("一条旧 Thread", search.stdout)

    def test_changed_source_makes_index_stale(self) -> None:
        output = self.output_root / "Articles" / "article.md"
        _write(
            output,
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
---
# 原文

第一版。
""",
        )
        records, _ = discover_records(self.project_root)
        write_index(self.project_root, records)
        self.assertTrue(index_is_current(self.project_root, records))

        _write(
            output,
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
---
# 原文

第二版。
""",
        )
        current, _ = discover_records(self.project_root)
        self.assertFalse(index_is_current(self.project_root, current))

    def test_missing_same_format_is_a_normal_empty_result(self) -> None:
        _write(
            self.output_root / "Articles" / "article.md",
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
format: article
---
# 文章

只有文章证据。
""",
        )
        build = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--library-root",
                str(self.project_root),
                "build-index",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, build.returncode, build.stderr)

        search = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--library-root",
                str(self.project_root),
                "search",
                "--purpose",
                "voice",
                "--format",
                "thread",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, search.returncode, search.stderr)
        self.assertIn("作者声音候选（0 条）", search.stdout)
        self.assertIn("不拿发布历史硬凑", search.stdout)

    def test_voice_search_rejects_topic_queries(self) -> None:
        _write(
            self.output_root / "Social" / "X" / "voice.md",
            """---
type: writing-output
status: final
source: user-confirmed
format: product
writing_origin: human-edited
voice_eligible: true
---
# 可用声音

这是经过确认的表达。
""",
        )
        records, _ = discover_records(self.project_root)

        with self.assertRaisesRegex(MemoryError, "主题词只用于 novelty"):
            search_memory(
                library_root=self.project_root,
                records=records,
                purpose="voice",
                query="币安 Robinhood Chain",
                format_name="product",
                content_type=None,
                limit=1,
            )

    def test_removed_writing_formats_are_rejected_by_the_cli(self) -> None:
        for removed_format in ("reply", "newsletter"):
            with self.subTest(removed_format=removed_format):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT_PATH),
                        "--library-root",
                        str(self.project_root),
                        "search",
                        "--purpose",
                        "novelty",
                        "--query",
                        "任意内容",
                        "--format",
                        removed_format,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(2, result.returncode)
                self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
