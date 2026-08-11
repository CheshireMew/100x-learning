from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.select_writing_examples import (
    list_candidates,
    load_component_sources,
    parse_selections,
    render_candidates,
    render_examples,
    validate_selections,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WritingExampleSelectorTests(unittest.TestCase):
    def test_mappings_reference_existing_components_and_allow_no_example(self) -> None:
        mapping = load_component_sources(
            PROJECT_ROOT / "references" / "writing-template-coverage.md"
        )
        components = {
            path.stem
            for path in (PROJECT_ROOT / "references" / "writing-templates").rglob("*.md")
            if path.name != "index.md"
        }
        self.assertTrue(set(mapping).issubset(components))
        self.assertTrue(all(mapping.values()))
        self.assertNotIn("H23", mapping)

    def test_candidates_preserve_every_active_mapped_source(self) -> None:
        mapping = {"H02": ["thread-hook-a", "case-a", "short-hook-human-01"]}
        cases = {
            "case-a": SimpleNamespace(asset="social", original_text="完整社交案例")
        }
        hooks = {
            "thread-hook-a": SimpleNamespace(text="翻译式 Thread 钩子"),
            "short-hook-human-01": SimpleNamespace(text="自然中文钩子"),
        }
        self.assertEqual(
            [("H02", ["thread-hook-a", "case-a", "short-hook-human-01"])],
            list_candidates(["H02"], mapping, cases, hooks, "short"),
        )

    def test_candidates_do_not_auto_select_by_form_or_length(self) -> None:
        mapping = {"P24": ["case-article", "case-social"]}
        cases = {
            "case-social": SimpleNamespace(asset="social", original_text="社交案例"),
            "case-article": SimpleNamespace(asset="article", original_text="文章案例"),
        }
        self.assertEqual(
            [("P24", ["case-article", "case-social"])],
            list_candidates(["P24"], mapping, cases, {}, "short"),
        )

    def test_candidate_output_exposes_titles_without_full_text(self) -> None:
        mapping = {"H02": ["thread-hook-a", "case-social"]}
        cases = {
            "case-social": SimpleNamespace(
                asset="social", title="社交标题", original_text="不应出现在候选清单的完整正文"
            ),
        }
        hooks = {
            "thread-hook-a": SimpleNamespace(title="钩子标题", text="不应出现的钩子全文")
        }
        output = render_candidates(
            list_candidates(["H02"], mapping, cases, hooks, "short"), cases, hooks
        )
        self.assertIn("钩子标题", output)
        self.assertIn("社交标题", output)
        self.assertNotIn("不应出现", output)

    def test_render_requires_an_explicit_mapped_selection(self) -> None:
        mapping = {"H02": ["case-a", "case-b"]}
        cases = {
            "case-a": SimpleNamespace(asset="social", title="A", original_text="正文 A"),
            "case-b": SimpleNamespace(asset="social", title="B", original_text="正文 B"),
        }
        self.assertEqual(
            [("H02", "case-b")],
            validate_selections([("H02", "case-b")], mapping, cases, {}, "short"),
        )
        with self.assertRaisesRegex(ValueError, "没有被覆盖账本映射"):
            validate_selections(
                [("H02", "case-c")],
                mapping,
                {**cases, "case-c": cases["case-a"]},
                {},
                "short",
            )

    def test_render_returns_the_complete_explicitly_selected_source(self) -> None:
        cases = {
            "case-a": SimpleNamespace(
                asset="social", title="完整案例", original_text="第一段\n\n第二段"
            )
        }
        output = render_examples([("P01", "case-a")], cases, {})
        self.assertIn("第一段\n\n第二段", output)
        self.assertIn("来源：`case-a`", output)

    def test_same_component_can_render_multiple_distinct_candidates(self) -> None:
        mapping = {"P01": ["case-a", "case-b"]}
        cases = {
            "case-a": SimpleNamespace(asset="social", title="A", original_text="A"),
            "case-b": SimpleNamespace(asset="social", title="B", original_text="B"),
        }
        self.assertEqual(
            [("P01", "case-a"), ("P01", "case-b")],
            validate_selections(
                [("P01", "case-a"), ("P01", "case-b")],
                mapping,
                cases,
                {},
                "short",
            ),
        )

    def test_exact_same_component_source_pair_is_rejected(self) -> None:
        mapping = {"P01": ["case-a"]}
        cases = {
            "case-a": SimpleNamespace(asset="social", title="A", original_text="A"),
        }
        with self.assertRaisesRegex(ValueError, "模仿来源重复选择"):
            validate_selections(
                [("P01", "case-a"), ("P01", "case-a")],
                mapping,
                cases,
                {},
                "short",
            )

    def test_selection_parser_requires_component_source_pair(self) -> None:
        self.assertEqual(
            [("H23", "short-hook-human-01"), ("P01", "case-a")],
            parse_selections(["H23=short-hook-human-01", "P01=case-a"]),
        )
        with self.assertRaisesRegex(ValueError, "选择格式无效"):
            parse_selections(["H23"])

    def test_missing_or_invalid_component_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "无效组件 ID"):
            list_candidates(["X01"], {}, {}, {}, "short")
        for component in ("C01", "B01"):
            with self.assertRaisesRegex(ValueError, "无效组件 ID"):
                list_candidates([component], {component: ["case-a"]}, {}, {}, "short")
        with self.assertRaisesRegex(ValueError, "不能为章节组件"):
            list_candidates(["S01"], {"S01": ["case-a"]}, {}, {}, "short")
        self.assertEqual(
            [("H01", [])],
            list_candidates(["H01"], {"H01": ["missing"]}, {}, {}, "short"),
        )


if __name__ == "__main__":
    unittest.main()
