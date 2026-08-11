from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.select_writing_examples import load_component_sources, select_sources


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WritingExampleSelectorTests(unittest.TestCase):
    def test_every_component_has_a_mapped_source(self) -> None:
        mapping = load_component_sources(
            PROJECT_ROOT / "references" / "writing-template-coverage.md"
        )
        components = {
            path.stem
            for path in (PROJECT_ROOT / "references" / "writing-templates").rglob("*.md")
            if path.name != "index.md"
        }
        self.assertEqual(components, set(mapping))
        self.assertTrue(all(mapping[component] for component in components))

    def test_hook_prefers_a_human_short_example(self) -> None:
        mapping = {"H02": ["thread-hook-a", "case-a", "short-hook-human-01"]}
        cases = {
            "case-a": SimpleNamespace(asset="social", original_text="完整社交案例")
        }
        hooks = {
            "thread-hook-a": SimpleNamespace(text="翻译式 Thread 钩子"),
            "short-hook-human-01": SimpleNamespace(text="自然中文钩子"),
        }
        self.assertEqual(
            [("H02", "short-hook-human-01")],
            select_sources(["H02"], mapping, cases, hooks, "short"),
        )

    def test_short_body_prefers_social(self) -> None:
        mapping = {"P24": ["case-article", "case-social"]}
        cases = {
            "case-social": SimpleNamespace(asset="social", original_text="社交案例"),
            "case-article": SimpleNamespace(asset="article", original_text="文章案例"),
        }
        self.assertEqual(
            [("P24", "case-social")],
            select_sources(["P24"], mapping, cases, {}, "short"),
        )

    def test_article_hook_and_section_prefer_article_cases(self) -> None:
        mapping = {
            "H02": ["thread-hook-a", "case-social", "case-article"],
            "S01": ["case-social", "case-article"],
        }
        cases = {
            "case-social": SimpleNamespace(asset="social", original_text="社交案例"),
            "case-article": SimpleNamespace(asset="article", original_text="文章案例"),
        }
        hooks = {"thread-hook-a": SimpleNamespace(text="中性钩子案例")}
        self.assertEqual(
            [("H02", "case-article"), ("S01", "case-article")],
            select_sources(["H02", "S01"], mapping, cases, hooks, "article"),
        )

    def test_curated_format_neutral_hook_beats_article_case(self) -> None:
        mapping = {"H02": ["case-article", "short-hook-human-01"]}
        cases = {
            "case-article": SimpleNamespace(asset="article", original_text="文章案例")
        }
        hooks = {"short-hook-human-01": SimpleNamespace(text="自然中文钩子")}
        self.assertEqual(
            [("H02", "short-hook-human-01")],
            select_sources(["H02"], mapping, cases, hooks, "article"),
        )

    def test_distinct_sources_are_preferred_when_available(self) -> None:
        mapping = {
            "P24": ["case-a", "case-b"],
            "E04": ["case-a", "case-b"],
        }
        cases = {
            "case-a": SimpleNamespace(asset="social", original_text="短"),
            "case-b": SimpleNamespace(asset="social", original_text="稍长一点"),
        }
        self.assertEqual(
            [("P24", "case-a"), ("E04", "case-b")],
            select_sources(["P24", "E04"], mapping, cases, {}, "short"),
        )

    def test_form_match_beats_source_uniqueness(self) -> None:
        mapping = {
            "P03": ["case-social"],
            "E03": ["case-article", "case-social"],
        }
        cases = {
            "case-social": SimpleNamespace(asset="social", original_text="社交案例"),
            "case-article": SimpleNamespace(asset="article", original_text="文章案例"),
        }
        self.assertEqual(
            [("P03", "case-social"), ("E03", "case-social")],
            select_sources(["P03", "E03"], mapping, cases, {}, "short"),
        )

    def test_missing_or_invalid_component_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "无效组件 ID"):
            select_sources(["X01"], {}, {}, {}, "short")
        for component in ("C01", "B01"):
            with self.assertRaisesRegex(ValueError, "无效组件 ID"):
                select_sources([component], {component: ["case-a"]}, {}, {}, "short")
        with self.assertRaisesRegex(ValueError, "不能为章节组件"):
            select_sources(["S01"], {"S01": ["case-a"]}, {}, {}, "short")
        with self.assertRaisesRegex(ValueError, "没有可读取的活动模仿来源"):
            select_sources(["H01"], {"H01": ["missing"]}, {}, {}, "short")


if __name__ == "__main__":
    unittest.main()
