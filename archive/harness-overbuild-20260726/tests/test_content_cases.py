from __future__ import annotations

import unittest

from harness.content_cases import (
    ContentCaseError,
    INDEX_PATH,
    build_index,
    load_library,
    render_search_results,
    search_library,
)


class ContentCaseLibraryTests(unittest.TestCase):
    def test_activity_library_is_structurally_valid(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        self.assertTrue(any(case.asset == "hook" for case in cases))
        self.assertTrue(any(case.asset == "short" for case in cases))
        self.assertTrue(any(case.asset == "article" for case in cases))

    def test_short_search_returns_the_full_case_body(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        source = next(case for case in cases if case.asset == "short")
        hits = search_library(
            writing_task=source.writing_task,
            content_type=source.content_type,
            topics=source.topics[:1],
            structures=source.structure[:1],
            assets=["short"],
            limit=1,
        )
        self.assertEqual(len(hits), 1)
        rendered = render_search_results(hits)
        self.assertIn(hits[0].case.original_text, rendered)
        self.assertIn(hits[0].case.source_url, rendered)

    def test_article_search_returns_body_and_authorship_boundary(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        source = next(case for case in cases if case.asset == "article")
        hits = search_library(
            writing_task=source.writing_task,
            content_type=source.content_type,
            topics=source.topics[:1],
            structures=source.structure[:1],
            assets=["article"],
            limit=1,
        )
        self.assertEqual(len(hits), 1)
        rendered = render_search_results(hits)
        self.assertIn(hits[0].case.original_text, rendered)
        self.assertIn(f"来源性质：{hits[0].case.authorship}", rendered)

    def test_mixed_search_cannot_replace_body_with_a_hook(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        source = next(case for case in cases if case.asset == "article")
        hits = search_library(
            writing_task="介绍项目",
            content_type=source.content_type,
            topics=["AI"],
            structures=["用户结果"],
            assets=["hook", "article"],
            limit=2,
        )
        self.assertEqual({hit.case.asset for hit in hits}, {"hook", "article"})

    def test_unmatched_words_still_return_a_same_type_full_case(self) -> None:
        hits = search_library(
            writing_task="zzzz-unmatched-task",
            topics=["zzzz-unmatched-topic"],
            structures=["zzzz-unmatched-structure"],
            assets=["article"],
            content_type="项目与产品介绍",
            limit=1,
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].case.asset, "article")
        self.assertEqual(hits[0].case.content_type, "项目与产品介绍")

    def test_missing_content_type_stops_before_drafting(self) -> None:
        with self.assertRaises(ContentCaseError):
            search_library(
                writing_task="介绍项目",
                topics=["AI"],
                structures=["用户结果"],
                assets=["short"],
                content_type="不存在的正文类型",
                limit=1,
            )

    def test_index_matches_the_activity_library(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        actual = INDEX_PATH.read_text(encoding="utf-8")
        self.assertEqual(actual, build_index(cases))


if __name__ == "__main__":
    unittest.main()
