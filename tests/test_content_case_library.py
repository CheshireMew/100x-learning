from __future__ import annotations

import unittest

from scripts.content_case_library import (
    CaseError,
    load_library,
    main,
    render_search_results,
    search_library,
)


class ContentCaseLibraryTests(unittest.TestCase):
    def test_content_type_cannot_make_an_unrelated_case_pass(self) -> None:
        with self.assertRaisesRegex(CaseError, "没有可读取的案例"):
            search_library(
                query="中子星潮汐形变引力波参数Lambda",
                assets=["short"],
                content_type="项目与产品介绍",
                limit=2,
            )

    def test_single_project_type_prefers_project_cases(self) -> None:
        hits, _ = search_library(
            query="AI 智能体帮助普通人管理助手任务和工作流",
            assets=["short"],
            content_type="项目与产品介绍",
            limit=2,
        )

        self.assertTrue(hits)
        self.assertEqual("项目与产品介绍", hits[0].case.content_type)

    def test_project_list_type_prefers_list_cases(self) -> None:
        hits, _ = search_library(
            query="盘点去除 AI 味的写作工具，帮助普通创作者选择",
            assets=["short"],
            content_type="清单与资源推荐",
            limit=2,
        )

        self.assertTrue(hits)
        self.assertEqual("清单与资源推荐", hits[0].case.content_type)

    def test_content_type_is_an_index_hint_not_a_usage_gate(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues)
        candidate = next(
            case
            for case in cases
            if case.asset == "short"
            and case.content_type != "项目与产品介绍"
        )
        hits, _ = search_library(
            query=candidate.title,
            assets=["short"],
            content_type="项目与产品介绍",
            limit=1,
        )

        self.assertEqual(candidate.path, hits[0].case.path)
        self.assertNotEqual("项目与产品介绍", hits[0].case.content_type)

    def test_hook_search_uses_technique_instead_of_topic(self) -> None:
        ai_hits, _ = search_library(
            query="AI 项目先点出目标读者熟悉的痛点，立即给出项目带来的明确变化，让人共鸣和兴奋",
            assets=["hook"],
            content_type="项目与产品介绍",
            limit=1,
        )
        travel_hits, _ = search_library(
            query="旅行产品先点出目标读者熟悉的痛点，立即给出项目带来的明确变化，让人共鸣和兴奋",
            assets=["hook"],
            content_type="项目与产品介绍",
            limit=1,
        )

        self.assertEqual(ai_hits[0].case.path, travel_hits[0].case.path)
        self.assertEqual("hook", ai_hits[0].matched_asset)
        self.assertTrue(ai_hits[0].case.supports_hook)

    def test_same_topic_with_different_hook_technique_changes_result(self) -> None:
        pain_hits, _ = search_library(
            query="开源 AI 项目先点出主要痛点，立即给出项目和变化，让人共鸣",
            assets=["hook"],
            content_type=None,
            limit=1,
        )
        suspense_hits, _ = search_library(
            query="开源 AI 项目连续叠加困境，留下结果悬念，让人紧张和期待",
            assets=["hook"],
            content_type=None,
            limit=1,
        )

        self.assertNotEqual(pain_hits[0].case.path, suspense_hits[0].case.path)
        self.assertTrue(pain_hits[0].case.supports_hook)
        self.assertTrue(suspense_hits[0].case.supports_hook)

    def test_topic_words_alone_cannot_select_a_hook(self) -> None:
        with self.assertRaisesRegex(CaseError, "没有可读取的案例"):
            search_library(
                query="Twitter 高级搜索",
                assets=["hook"],
                content_type=None,
                limit=2,
            )

    def test_one_source_can_supply_full_case_and_hook_roles(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues)
        candidate = next(
            case
            for case in cases
            if case.asset == "short" and case.supports_hook
        )
        hits, _ = search_library(
            query=" ".join(
                (
                    candidate.index_task,
                    *candidate.index_moves,
                    *candidate.hook_techniques,
                    *candidate.reader_effects,
                    *candidate.required_material,
                )
            ),
            assets=["short", "hook"],
            content_type=candidate.content_type,
            limit=20,
        )
        same_source_hits = [
            hit
            for hit in hits
            if hit.case.path == candidate.path
        ]

        self.assertEqual(
            {"short", "hook"},
            {hit.matched_asset for hit in same_source_hits},
        )
        self.assertEqual(1, len({hit.case.path for hit in same_source_hits}))

    def test_all_hook_roles_have_consumer_metadata(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues)
        hook_cases = [case for case in cases if case.supports_hook]

        self.assertGreater(len(hook_cases), 0)
        self.assertTrue(all(case.hook_family for case in hook_cases))
        self.assertTrue(all(case.hook_techniques for case in hook_cases))
        self.assertTrue(all(case.reader_effects for case in hook_cases))
        self.assertTrue(all(case.required_material for case in hook_cases))

    def test_case_files_are_source_first_without_editorial_limits(self) -> None:
        cases, issues = load_library()
        self.assertFalse(issues)

        for case in cases:
            text = case.path.read_text(encoding="utf-8-sig")
            self.assertIn("<!-- content-case-index", text, case.path)
            self.assertNotIn("## 可以参考什么", text, case.path)
            self.assertNotIn("## 适用场景", text, case.path)
            self.assertNotIn("<!-- content-case-notes -->", text, case.path)
            if case.asset != "article":
                self.assertTrue(text.startswith("# "), case.path)
                self.assertLess(
                    text.index("## 原帖全文"),
                    text.index("<!-- content-case-index"),
                    case.path,
                )

    def test_search_output_leads_with_original_and_hides_index_fields(self) -> None:
        hits, _ = search_library(
            query="让不懂技术的人迅速感到项目变化，用短句和紧凑的并列事实增加力度",
            assets=["short"],
            content_type="项目与产品介绍",
            limit=1,
        )
        rendered = render_search_results(hits)

        self.assertLess(
            rendered.index("### 原文全文"),
            rendered.index("### 检索记录"),
        )
        for hidden_label in (
            "内容类型：",
            "写作任务：",
            "主题：",
            "结构：",
            "开头技巧：",
            "可以参考什么",
            "适用场景",
        ):
            self.assertNotIn(hidden_label, rendered)

    def test_long_natural_description_is_not_diluted_by_query_length(self) -> None:
        hits, _ = search_library(
            query=(
                "让使用 AI 编程工具的人马上感到工作方式被改变；"
                "第一句直接击中常见不满，第二句交代项目和变化，"
                "再用紧凑的并列内容加强，最后迅速收束"
            ),
            assets=["short"],
            content_type="项目与产品介绍",
            limit=1,
        )

        self.assertEqual("short", hits[0].matched_asset)
        self.assertTrue(hits[0].case.original_text)

    def test_cli_requires_the_upper_layer_to_choose_an_asset(self) -> None:
        with self.assertRaises(SystemExit) as error:
            main(["search", "--query", "介绍一个项目"])

        self.assertEqual(2, error.exception.code)

    def test_article_asset_never_silently_falls_back_to_short(self) -> None:
        hits, _ = search_library(
            query="从一次真实实践写成长文，按过程推进并解释结果",
            assets=["article"],
            content_type="教程与操作指南",
            limit=2,
        )

        self.assertTrue(hits)
        self.assertTrue(all(hit.matched_asset == "article" for hit in hits))
        self.assertTrue(all(hit.case.asset == "article" for hit in hits))

    def test_style_index_does_not_turn_example_item_count_into_a_contract(self) -> None:
        from scripts.content_case_library import _content_style_terms

        terms = _content_style_terms(
            "先交代变化。\n\n• 第一项\n• 第二项\n\n最后收束。"
        )

        self.assertIn("并列事实", terms)
        self.assertNotIn("两条", terms)
        self.assertNotIn("两项", terms)
        self.assertNotIn("两个具体事实", terms)


if __name__ == "__main__":
    unittest.main()
