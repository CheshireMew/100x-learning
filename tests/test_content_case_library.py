from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import tempfile
from pathlib import Path

from scripts.content_case_library import (
    ContentCase,
    HookPattern,
    add_case,
    add_hook,
    build_index,
    load_library,
    main,
    write_index,
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
        write_index(self.layout, [])
        self.short, self.article, self.hook = self._seed_library()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _input(self, name: str, text: str) -> Path:
        path = Path(self.temp_dir.name) / name
        path.write_text(text, encoding="utf-8")
        return path

    def _seed_library(self) -> tuple[Path, Path, Path]:
        existing, issues = load_library(self.layout)
        self.assertFalse(issues)
        short = add_case(
            self.layout,
            existing,
            kind="short",
            input_path=self._input(
                "short.md",
                "把一份长材料交给工具，它会先恢复主线，再生成可以继续使用的知识。",
            ),
            title="材料变成可复用知识",
            content_type="项目与产品介绍",
            source="https://example.com/short",
            index_task="介绍项目结果",
            topics=("学习", "知识库"),
            moves=("输入变成结果",),
            index_roles=("promotion",),
            promotion_stages=("launch",),
            audience_actions=("visit",),
            benefit_recipients=("reader",),
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
            content_type="概念与机制解释",
            source="https://example.com/article",
            index_task="解释知识库边界",
            topics=("知识库",),
            moves=("先区分消费者",),
        )
        existing, issues = load_library(self.layout)
        self.assertFalse(issues)
        source_relative = short.relative_to(self.layout.root).as_posix()
        hook = add_hook(
            self.layout,
            existing,
            title="输入直接变成可见结果",
            pattern_id="result-visible-output",
            content_type="结果钩子",
            source_case=source_relative,
            index_task="从结果进入",
            topics=("学习",),
            moves=("结果前置",),
            techniques=("直接展示输入到结果",),
            reader_effects=("迅速理解变化",),
        )
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        write_index(self.layout, cases)
        return short, article, hook

    def test_library_loads_all_three_resource_types(self) -> None:
        cases, issues = load_library(self.layout)

        self.assertFalse(issues)
        self.assertTrue(any(isinstance(case, HookPattern) for case in cases))
        self.assertTrue(
            any(
                isinstance(case, ContentCase) and case.asset == "short"
                for case in cases
            )
        )
        self.assertTrue(
            any(
                isinstance(case, ContentCase) and case.asset == "article"
                for case in cases
            )
        )

    def test_hook_pattern_can_reference_a_full_case_without_mixing_resources(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        pattern = next(
            item
            for item in cases
            if isinstance(item, HookPattern) and item.source_case_file is not None
        )
        source = next(
            item
            for item in cases
            if isinstance(item, ContentCase) and item.path == pattern.source_case_file
        )

        self.assertEqual(pattern.source_text, source.original_text)
        self.assertIn("钩子与开头", pattern.path.parts)
        self.assertNotIn("钩子与开头", source.path.parts)

    def test_all_hook_patterns_have_lightweight_creative_metadata(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        hook_cases = [case for case in cases if isinstance(case, HookPattern)]

        self.assertTrue(hook_cases)
        self.assertTrue(all(case.pattern_id for case in hook_cases))
        self.assertTrue(all(case.hook_techniques for case in hook_cases))
        self.assertTrue(all(case.reader_effects for case in hook_cases))
        for case in hook_cases:
            text = case.path.read_text(encoding="utf-8-sig")
            for retired_field in (
                "required_material:",
                "required_relations:",
                "optional_amplifiers:",
                "hook_context_blocks:",
                "hook_family:",
            ):
                self.assertNotIn(retired_field, text, case.path)

    def test_all_promotion_resources_name_the_actor_and_action(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        promotion_cases = [
            case for case in cases if "promotion" in case.index_roles
        ]

        self.assertTrue(promotion_cases)
        self.assertTrue(all(case.promotion_stages for case in promotion_cases))
        self.assertTrue(all(case.audience_actions for case in promotion_cases))
        self.assertTrue(all(case.benefit_recipients for case in promotion_cases))
        reader_cases = [
            case
            for case in promotion_cases
            if "reader" in case.benefit_recipients
        ]
        self.assertTrue(reader_cases)
        self.assertTrue(
            all("publisher" not in case.benefit_recipients for case in reader_cases)
        )

    def test_case_files_are_source_first_without_editorial_limits(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)

        for case in cases:
            text = case.path.read_text(encoding="utf-8-sig")
            self.assertIn("<!-- content-case-index", text, case.path)
            self.assertNotIn("## 可以参考什么", text, case.path)
            self.assertNotIn("## 适用场景", text, case.path)
            self.assertNotIn("<!-- content-case-notes -->", text, case.path)
            if isinstance(case, HookPattern) and case.source_case_file is not None:
                self.assertIn("## 来源示例", text)
                self.assertIn("source_case_file:", text)
            elif not isinstance(case, ContentCase) or case.asset != "article":
                self.assertTrue(text.startswith("# "), case.path)
                self.assertLess(
                    text.index("## 原帖全文"),
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
                    "short",
                    "--input",
                    str(raw),
                    "--title",
                    "正式入口保存材料",
                    "--content-type",
                    "教程与操作指南",
                    "--source",
                    "https://example.com/another",
                    "--index-task",
                    "说明沉淀流程",
                    "--topic",
                    "私人知识库",
                    "--move",
                    "材料进入真源",
                ]
            )
        self.assertEqual(0, result, stdout.getvalue())
        self.assertIn("内容案例已保存", stdout.getvalue())
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        created = next(case for case in cases if case.title == "正式入口保存材料")
        self.assertIn("正式生产入口保存全文", created.original_text)
        self.assertIn(created.title, self.layout.case_index.read_text(encoding="utf-8"))

    def test_generated_index_matches_every_active_resource(self) -> None:
        cases, issues = load_library(self.layout)
        self.assertFalse(issues)
        generated = build_index(cases, self.layout)

        self.assertEqual(self.layout.case_index.read_text(encoding="utf-8"), generated)
        for case in cases:
            self.assertIn(case.title, generated)

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


if __name__ == "__main__":
    unittest.main()
