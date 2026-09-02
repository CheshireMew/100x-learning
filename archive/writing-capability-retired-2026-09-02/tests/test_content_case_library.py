from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import tempfile
from pathlib import Path

from scripts.content_case_library import (
    ContentCase,
    add_case,
    build_index,
    load_library,
    main,
    write_indexes,
)
from scripts.private_library import initialize_library


class ContentCaseLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library_root = Path(self.temp_dir.name) / "private-library"
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.layout, _, _ = initialize_library(
            self.library_root,
            self.config_path,
        )
        write_indexes(self.layout, [])
        self.social, self.article = self._seed_library()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _input(self, name: str, text: str) -> Path:
        path = Path(self.temp_dir.name) / name
        path.write_text(text, encoding="utf-8")
        return path

    def _seed_library(self) -> tuple[Path, Path]:
        existing, issues = load_library(self.layout)
        self.assertFalse(issues)
        social = add_case(
            self.layout,
            existing,
            kind="social",
            input_path=self._input(
                "social.md",
                "把一份长材料交给工具，它会先恢复主线，再生成可以继续使用的知识。",
            ),
            title="材料变成可复用知识",
            techniques=("结果先行", "因果推进"),
        )
        existing, issues = load_library(self.layout)
        self.assertFalse(issues)
        article = add_case(
            self.layout,
            existing,
            kind="article",
            input_path=self._input(
                "article.md",
                "这篇文章完整解释了材料、知识、案例和钩子为什么需要不同的保存边界。",
            ),
            title="私人知识库的四种内容",
            techniques=("问题切入", "机制拆解"),
        )
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        write_indexes(self.layout, cases)
        return social, article

    def test_library_loads_only_complete_case_types(self) -> None:
        cases, issues = load_library(self.layout)

        self.assertFalse(issues)
        self.assertTrue(
            any(
                isinstance(case, ContentCase) and case.asset == "social"
                for case in cases
            )
        )
        self.assertTrue(
            any(
                isinstance(case, ContentCase) and case.asset == "article"
                for case in cases
            )
        )
        self.assertTrue(self.article.is_relative_to(self.layout.article_cases))

    def test_formal_article_is_not_a_case_without_an_independent_copy(self) -> None:
        formal = self.layout.article_sources / "Published" / "formal.md"
        formal.parent.mkdir(parents=True, exist_ok=True)
        formal.write_text(
            """---
type: source-article
content_type: "概念与机制解释"
source_url: "https://example.com/formal"
---
# 正式文章

正式文章正文。
""",
            encoding="utf-8",
        )

        cases, issues = load_library(self.layout)

        self.assertFalse(issues)
        self.assertNotIn(formal, [case.path for case in cases])

    def test_cases_expose_only_form_and_writing_techniques(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)

        social = next(case for case in cases if case.asset == "social")
        self.assertEqual(("结果先行", "因果推进"), social.writing_techniques)
        self.assertFalse(hasattr(social, "index_task"))
        self.assertFalse(hasattr(social, "topics"))
        self.assertFalse(hasattr(social, "promotion_stages"))

    def test_case_files_keep_complete_text_without_source_or_editorial_limits(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)

        for case in cases:
            text = case.path.read_text(encoding="utf-8-sig")
            self.assertIn("<!-- content-case-index", text, case.path)
            self.assertNotIn("## 可以参考什么", text, case.path)
            self.assertNotIn("## 适用场景", text, case.path)
            self.assertNotIn("<!-- content-case-notes -->", text, case.path)
            self.assertNotIn("来源：", text, case.path)
            self.assertNotIn("原帖链接：", text, case.path)
            self.assertNotIn("source_url:", text, case.path)
            self.assertTrue(text.startswith("# "), case.path)
            self.assertLess(
                text.index("## 原文全文"),
                text.index("<!-- content-case-index"),
                case.path,
            )

    def test_cli_creates_a_case_from_real_input_and_updates_the_index(self) -> None:
        raw = self._input(
            "another.md",
            "用户给出一段完整材料，正式生产入口保存全文并更新索引。",
        )
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-case",
                    "--kind",
                    "social",
                    "--input",
                    str(raw),
                    "--title",
                    "正式入口保存材料",
                    "--technique",
                    "步骤推进",
                ]
            )
        self.assertEqual(0, result, stdout.getvalue())
        self.assertIn("内容案例已保存", stdout.getvalue())
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        created = next(case for case in cases if case.title == "正式入口保存材料")
        self.assertIn("正式生产入口保存全文", created.original_text)
        social_index = self.layout.social_case_index.read_text(encoding="utf-8")
        self.assertIn(created.case_id, social_index)
        self.assertNotIn(created.title, social_index)
        self.assertIn("## 步骤推进", social_index)
        self.assertNotIn(
            created.case_id,
            self.layout.article_case_index.read_text(encoding="utf-8"),
        )

    def test_generated_index_matches_every_active_resource(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        social_generated = build_index(cases, self.layout, "social")
        article_generated = build_index(cases, self.layout, "article")

        self.assertEqual(
            self.layout.social_case_index.read_text(encoding="utf-8"),
            social_generated,
        )
        self.assertEqual(
            self.layout.article_case_index.read_text(encoding="utf-8"),
            article_generated,
        )
        self.assertIn("只按可迁移的写作技巧分组", social_generated)
        self.assertIn("每个条目指向一份完整原文", social_generated)
        self.assertNotIn("先按技巧选编号", social_generated + article_generated)
        self.assertNotIn("浏览当前可用条目", social_generated + article_generated)
        social_case = next(case for case in cases if case.asset == "social")
        article_case = next(case for case in cases if case.asset == "article")
        self.assertIn(social_case.case_id, social_generated)
        self.assertNotIn(social_case.title, social_generated)
        self.assertNotIn(article_case.case_id, social_generated)
        self.assertIn(article_case.case_id, article_generated)
        self.assertNotIn(article_case.title, article_generated)
        self.assertNotIn(social_case.case_id, article_generated)
        for forbidden in ("index_task", "topics", "promotion", "项目与产品介绍"):
            self.assertNotIn(forbidden, social_generated + article_generated)

    def test_cli_only_maintains_and_validates_resources(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(
                0,
                main(["--library-root", str(self.library_root), "validate"]),
            )
        self.assertIn("案例库有效", stdout.getvalue())

        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            main(["--library-root", str(self.library_root), "search"])
        self.assertEqual(2, error.exception.code)
        self.assertIn("invalid choice", stderr.getvalue())

    def test_retired_short_kind_is_rejected(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-case",
                    "--kind",
                    "short",
                    "--input",
                    str(self._input("retired-short.md", "旧短内容类型不能继续生效。")),
                    "--title",
                    "旧短内容类型",
                    "--technique",
                    "结果先行",
                ]
            )
        self.assertEqual(2, error.exception.code)
        self.assertIn("invalid choice", stderr.getvalue())

    def test_case_parser_rejects_source_metadata(self) -> None:
        text = self.social.read_text(encoding="utf-8")
        self.social.write_text(
            text.replace(
                "<!-- content-case-index",
                "来源：https://example.com/source\n\n<!-- content-case-index",
            ),
            encoding="utf-8",
        )

        _, issues = load_library(self.layout)

        self.assertTrue(any("不保存原帖链接或来源字段" in issue for issue in issues))

    def test_parser_rejects_old_fields_and_nested_content_categories(self) -> None:
        old = self.social.read_text(encoding="utf-8").replace(
            "writing_techniques:", 'index_task: "旧任务"\nwriting_techniques:'
        )
        self.social.write_text(old, encoding="utf-8")
        _, issues = load_library(self.layout)
        self.assertTrue(any("旧检索字段或未知字段" in issue for issue in issues))

        self.social.write_text(
            old.replace('index_task: "旧任务"\n', ""), encoding="utf-8"
        )
        nested = self.layout.social_cases / "完整社交内容" / "按题材" / "嵌套.md"
        nested.parent.mkdir(parents=True)
        nested.write_text(self.social.read_text(encoding="utf-8"), encoding="utf-8")
        _, issues = load_library(self.layout)
        self.assertTrue(any("不能再按题材或内容类别分层" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
