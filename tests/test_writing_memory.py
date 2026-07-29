from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.writing_memory import (
    CONFIG_RELATIVE,
    INDEX_RELATIVE,
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
        self.project_root = Path(self.temp_dir.name)
        self.blog_root = (
            self.project_root
            / "System Knowledge"
            / "20-Sources"
            / "Articles"
            / "Cheshire"
            / "Blog"
        )
        self.output_root = (
            self.project_root
            / "System Knowledge"
            / "40-Outputs"
            / "Writing"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_only_first_party_final_writing_enters_memory(self) -> None:
        _write(
            self.blog_root / "published.md",
            """---
authorship: "本人主导"
content_type: "教程与操作指南"
source_url: "https://example.com/published/"
---
# 已发布版本

旧正文。

<!-- content-case-index
reference_value: "case"
index_task: "教程"
index_topics: ["写作"]
index_moves: ["正文"]
-->
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

        self.assertEqual(1, len(records))
        self.assertEqual("用户确认版本", records[0].title)
        self.assertEqual("教程与操作指南", records[0].content_type)
        self.assertEqual("writing-output", records[0].source_kind)
        self.assertEqual(1, receipt.merged_by_url)

    def test_hidden_case_index_is_not_part_of_authored_evidence(self) -> None:
        _write(
            self.blog_root / "case.md",
            """---
authorship: "本人主导"
content_type: "个人观察与实测"
source_url: "https://example.com/case/"
---
# 本人文章

这是实际发布正文。

<!-- content-case-index
reference_value: "case"
index_task: "分享观察"
index_topics: ["观察"]
index_moves: ["正文"]
-->
""",
        )
        records, _ = discover_records(self.project_root)
        write_index(self.project_root, records)

        hits = search_memory(
            project_root=self.project_root,
            records=load_index(self.project_root),
            query="实际发布正文",
            format_name="article",
            content_type=None,
            limit=1,
        )
        self.assertIn("实际发布正文", hits[0].opening)
        self.assertNotIn("案例维护说明", hits[0].ending)

    def test_verified_source_first_social_case_enters_memory(self) -> None:
        _write(
            self.project_root / CONFIG_RELATIVE,
            json.dumps(
                {
                    "verified_first_party_url_prefixes": [
                        "https://x.com/author/status/"
                    ]
                },
                ensure_ascii=False,
            ),
        )
        social_root = (
            self.project_root
            / "System Knowledge"
            / "20-Sources"
            / "Social Posts"
            / "Content Cases"
            / "完整短内容"
        )
        _write(
            social_root / "个人观察与实测" / "本人帖子.md",
            """# 本人帖子

## 原帖全文

我真正想减少的是上下文切换，而不只是点击次数。

原帖链接：https://x.com/author/status/2053104321668239801

<!-- content-case-index
index_task: "分享一次真实观察"
index_topics: ["AI", "工作流"]
index_moves: ["观察", "机制"]
-->
""",
        )
        _write(
            social_root / "个人观察与实测" / "外部帖子.md",
            """# 外部帖子

## 原帖全文

这不是本人写作。

原帖链接：https://x.com/other/status/2053104321668239802

<!-- content-case-index
index_task: "外部参考"
index_topics: ["AI"]
index_moves: ["观察"]
-->
""",
        )

        records, receipt = discover_records(self.project_root)

        self.assertEqual(1, len(records))
        self.assertEqual("published-social", records[0].source_kind)
        self.assertEqual("short-post", records[0].format)
        self.assertEqual("个人观察与实测", records[0].content_type)
        self.assertEqual("2026-05-09", records[0].updated)
        self.assertEqual(1, receipt.accepted_social)
        write_index(self.project_root, records)
        hits = search_memory(
            project_root=self.project_root,
            records=load_index(self.project_root),
            query="减少上下文切换",
            format_name="short-post",
            content_type=None,
            limit=1,
        )
        self.assertIn("上下文切换", hits[0].opening)
        self.assertNotIn("content-case-index", hits[0].ending)

    def test_first_party_social_prefix_must_name_one_account(self) -> None:
        _write(
            self.project_root / CONFIG_RELATIVE,
            json.dumps(
                {
                    "verified_first_party_url_prefixes": [
                        "https://x.com/"
                    ]
                }
            ),
        )
        with self.assertRaisesRegex(ValueError, "每个本人入口"):
            discover_records(self.project_root)

    def test_index_output_is_consumed_by_same_format_search(self) -> None:
        _write(
            self.output_root / "Social" / "X" / "reply.md",
            """---
type: writing-output
status: final
source: user-confirmed
author: 柴郡
updated: 2026-07-29
format: reply
content_type: 个人观察与实测
---
# 回复

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
            project_root=self.project_root,
            records=indexed,
            query="工具如何减少上下文切换",
            format_name="reply",
            content_type=None,
            limit=3,
        )

        self.assertEqual(1, len(hits))
        self.assertEqual("reply", hits[0].record.format)
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
                "--project-root",
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
                "--project-root",
                str(self.project_root),
                "search",
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
                "--project-root",
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
                "--project-root",
                str(self.project_root),
                "search",
                "--query",
                "回复内容",
                "--format",
                "reply",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, search.returncode, search.stderr)
        self.assertIn("本人写作证据候选（0 条）", search.stdout)
        self.assertIn("不拿其它形态硬凑", search.stdout)


if __name__ == "__main__":
    unittest.main()
