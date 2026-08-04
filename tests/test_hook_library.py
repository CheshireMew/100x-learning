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
    write_index as write_case_index,
)
from scripts.hook_library import HookExample, load_library, main as hook_main, write_index
from scripts.private_library import initialize_library


class HookLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library_root = Path(self.temp_dir.name) / "private-library"
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.layout, _, _ = initialize_library(self.library_root, self.config_path)
        write_case_index(self.layout, [])
        write_index(self.layout, [])

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
            content_type="项目与产品介绍",
            source="https://example.com/case",
            index_task="介绍项目",
            topics=("项目",),
            moves=("说明结果",),
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
                    "--writing-format",
                    "短帖",
                    "--context",
                    "项目介绍",
                    "--source",
                    "https://example.com/hook",
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
        self.assertFalse(case_path.is_relative_to(self.layout.hook_root))
        self.assertIn("材料直接变成下一步", self.layout.hook_index.read_text(encoding="utf-8"))
        self.assertNotIn("完整案例", self.layout.hook_index.read_text(encoding="utf-8"))

    def test_hook_resource_contains_only_raw_text_source_and_addressing_metadata(self) -> None:
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
                    "--writing-format",
                    "文章",
                    "--context",
                    "开篇",
                    "--source",
                    "https://example.com/original",
                ]
            ),
        )
        hooks, issues = load_library(self.layout)
        self.assertFalse(issues)
        text = hooks[0].path.read_text(encoding="utf-8")
        metadata_text = text.split("<!-- hook-library-index\n", 1)[1].split("\n-->", 1)[0]
        metadata = json.loads(metadata_text)
        self.assertEqual(
            {"resource_type", "hook_id", "writing_format", "contexts"},
            set(metadata),
        )
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


if __name__ == "__main__":
    unittest.main()
