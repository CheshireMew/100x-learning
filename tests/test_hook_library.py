from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.content_case_library import (
    add_case,
    load_library as load_cases,
    main as case_main,
    write_indexes as write_case_indexes,
)
from scripts.hook_library import (
    HookExample,
    build_index,
    load_library,
    main as hook_main,
    write_indexes,
)
from scripts.private_library import initialize_library


class HookLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library_root = Path(self.temp_dir.name) / "private-library"
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.layout, _, _ = initialize_library(self.library_root, self.config_path)
        write_case_indexes(self.layout, [])
        write_indexes(self.layout, [])

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _input(self, name: str, text: str) -> Path:
        path = Path(self.temp_dir.name) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_real_case_and_hook_producers_remain_independent_but_both_are_readable(self) -> None:
        case_path = add_case(
            self.layout,
            [],
            kind="short",
            input_path=self._input("case.md", "完整案例从第一句保留到最后一句。"),
            title="完整案例",
            techniques=("结果先行",),
        )
        hook_text = "把一份长材料放进去。\n几秒后，主线和下一步都排好了。"
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = hook_main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-hook",
                    "--input",
                    str(self._input("hook.md", hook_text)),
                    "--title",
                    "材料直接变成下一步",
                    "--hook-id",
                    "material-to-next-step",
                    "--format",
                    "short",
                    "--technique",
                    "结果先行",
                ]
            )

        self.assertEqual(0, result, stdout.getvalue())
        cases, case_issues = load_cases(self.layout)
        hooks, hook_issues = load_library(self.layout)
        self.assertFalse(case_issues)
        self.assertFalse(hook_issues)
        self.assertEqual([case_path], [item.path for item in cases])
        self.assertEqual(1, len(hooks))
        self.assertIsInstance(hooks[0], HookExample)
        self.assertEqual(hook_text, hooks[0].text)
        self.assertTrue(hooks[0].path.is_relative_to(self.layout.hook_root))
        self.assertEqual("结果先行", hooks[0].technique)
        self.assertEqual(("short",), hooks[0].writing_formats)
        self.assertFalse(case_path.is_relative_to(self.layout.hook_root))
        index = self.layout.short_hook_index.read_text(encoding="utf-8")
        self.assertIn("## 结果先行", index)
        self.assertIn("material-to-next-step", index)
        self.assertNotIn("材料直接变成下一步", index)
        self.assertNotIn("完整案例", index)
        self.assertNotIn(
            "material-to-next-step",
            self.layout.article_hook_index.read_text(encoding="utf-8"),
        )

    def test_each_format_has_an_independent_technique_index(self) -> None:
        inputs = (
            (
                "thread.md",
                "短帖开头原文。\n这是紧接着的短帖内容。",
                "短帖开头",
                "contrast-thread",
                "thread",
            ),
            (
                "article.md",
                "文章开头原文。\n这是紧接着的文章内容。",
                "文章开头",
                "contrast-article",
                "article",
            ),
        )
        for filename, body, title, hook_id, writing_format in inputs:
            with redirect_stdout(StringIO()):
                result = hook_main(
                    [
                        "--library-root",
                        str(self.library_root),
                        "add-hook",
                        "--input",
                        str(self._input(filename, body)),
                        "--title",
                        title,
                        "--hook-id",
                        hook_id,
                        "--format",
                        writing_format,
                        "--technique",
                        "反常识切入",
                    ]
                )
            self.assertEqual(0, result)

        thread_index = self.layout.thread_hook_index.read_text(encoding="utf-8")
        article_index = self.layout.article_hook_index.read_text(encoding="utf-8")
        short_index = self.layout.short_hook_index.read_text(encoding="utf-8")
        self.assertIn("## 反常识切入", thread_index)
        self.assertIn("contrast-thread", thread_index)
        self.assertNotIn("短帖开头", thread_index)
        self.assertNotIn("contrast-article", thread_index)
        self.assertIn("contrast-article", article_index)
        self.assertNotIn("文章开头", article_index)
        self.assertNotIn("contrast-thread", article_index)
        self.assertNotIn("contrast-thread", short_index)
        self.assertNotIn("contrast-article", short_index)
        self.assertEqual(
            build_index(load_library(self.layout)[0], self.layout, "thread"),
            thread_index,
        )

    def test_hook_resource_contains_only_raw_text_and_addressing_metadata(self) -> None:
        raw = self._input("raw.md", "第一句原文。\n这是紧接着的第二句。")
        self.assertEqual(
            0,
            hook_main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-hook",
                    "--input",
                    str(raw),
                    "--title",
                    "连续原文",
                    "--hook-id",
                    "contiguous-original",
                    "--format",
                    "article",
                    "--technique",
                    "问题切入",
                ]
            ),
        )
        hooks, issues = load_library(self.layout)
        self.assertFalse(issues)
        text = hooks[0].path.read_text(encoding="utf-8")
        metadata_text = text.split("<!-- hook-library-index\n", 1)[1].split("\n-->", 1)[0]
        metadata = json.loads(metadata_text)
        self.assertEqual(
            {"resource_type", "hook_id", "writing_formats"},
            set(metadata),
        )
        self.assertEqual("问题切入", hooks[0].path.parent.name)
        self.assertEqual("Examples", hooks[0].path.parent.parent.name)
        self.assertNotIn("来源：", text)
        self.assertNotIn("source_url", text)
        for polluted in (
            "source_case",
            "source_case_file",
            "hook_techniques",
            "reader_effects",
            "listener_effects",
            "evidence",
            "qualification",
            "formula",
        ):
            self.assertNotIn(polluted, text)

    def test_one_hook_can_appear_in_multiple_explicit_format_indexes(self) -> None:
        raw = self._input("news.md", "新功能已经可以用了。\n下面是最直接的使用方法。")
        self.assertEqual(
            0,
            hook_main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-hook",
                    "--input",
                    str(raw),
                    "--title",
                    "新功能已经可以用了",
                    "--hook-id",
                    "breaking-product-update",
                    "--format",
                    "short",
                    "--format",
                    "thread",
                    "--technique",
                    "变化先行",
                ]
            ),
        )
        short_index = self.layout.short_hook_index.read_text(encoding="utf-8")
        thread_index = self.layout.thread_hook_index.read_text(encoding="utf-8")
        article_index = self.layout.article_hook_index.read_text(encoding="utf-8")
        self.assertIn("breaking-product-update", short_index)
        self.assertIn("breaking-product-update", thread_index)
        self.assertNotIn("新功能已经可以用了", short_index + thread_index)
        self.assertNotIn("breaking-product-update", article_index)
        self.assertNotIn("为什么有效", short_index + thread_index)

    def test_case_cli_cannot_create_hooks_and_hook_cli_cannot_reference_cases(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            hook_main(["--library-root", str(self.library_root), "add-case"])
        self.assertEqual(2, error.exception.code)
        self.assertIn("invalid choice", stderr.getvalue())

        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            case_main(
                [
                    "--library-root",
                    str(self.library_root),
                    "add-case",
                    "--source-case",
                    "some-case.md",
                ]
            )
        self.assertEqual(2, error.exception.code)
        self.assertIn("required", stderr.getvalue())

    def test_hook_parser_rejects_source_metadata(self) -> None:
        raw = self._input("source-field.md", "第一句原文。\n这是紧接着的第二句。")
        with redirect_stdout(StringIO()):
            self.assertEqual(
                0,
                hook_main(
                    [
                        "--library-root",
                        str(self.library_root),
                        "add-hook",
                        "--input",
                        str(raw),
                        "--title",
                        "来源字段",
                        "--hook-id",
                        "forbidden-source-field",
                        "--format",
                        "short",
                        "--technique",
                        "结果先行",
                    ]
                ),
            )
        hooks, issues = load_library(self.layout)
        self.assertFalse(issues)
        path = hooks[0].path
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "<!-- hook-library-index",
                "来源：https://example.com/source\n\n<!-- hook-library-index",
            ),
            encoding="utf-8",
        )

        _, issues = load_library(self.layout)

        self.assertTrue(any("钩子不保存来源字段" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
