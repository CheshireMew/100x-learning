from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class WritingContractTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = _read("SKILL.md")
        routed = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }

        self.assertEqual(active, routed)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in routed))

    def test_references_do_not_route_other_references(self) -> None:
        for path in (PROJECT_ROOT / "references").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"读取 `references/[^`]+\.md`", path)

    def test_single_project_and_project_list_keep_separate_templates(self) -> None:
        skill = _read("SKILL.md")
        project = _read("references/github-project-short-content.md")
        self.assertIn("references/github-project-short-content.md", skill)
        self.assertIn("references/github-project-list.md", skill)
        self.assertIn("不再使用固定结尾", project)
        self.assertIn("许可证、平台、免费范围", project)
        self.assertNotIn("正文最后一行永远逐字写", project)
        self.assertIn("统一选择标准", _read("references/github-project-list.md"))

    def test_output_identity_is_selected_before_promotional_requirements(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")

        identity = skill.index("### 2. 选择写作动作和成品身份")
        promotion = skill.index("### 3. 判断是否叠加内容型宣发")
        self.assertLess(identity, promotion)
        self.assertIn("单个 GitHub 项目介绍", skill)
        self.assertIn("传播效果由 `references/content-writing.md` 实现", skill)
        self.assertIn("这是效果目标，不是模板", content)

    def test_github_search_discovers_and_cleans_material_before_drafting(self) -> None:
        skill = _read("SKILL.md")
        research = _read("references/prewriting-research.md")
        project = _read("references/github-project-short-content.md")

        for marker in ("媒体", "KOL", "创作者", "真实用户", "社区讨论"):
            self.assertIn(marker, skill)
            self.assertIn(marker, research)
        self.assertIn("搜索是为了扩充创作可能性", skill)
        self.assertIn("打开实际来源阅读全文或相关上下文", skill)
        self.assertIn("新来源开始重复已有角度时停止", skill)
        self.assertIn("搜索摘要、转帖标题和自动摘要不代替原内容", research)
        self.assertIn("没有固定来源数量", research)
        self.assertIn("不在本模板里重新建立官方事实底座", project)
        self.assertIn("官方免责声明、通用风险提醒、保守陈词", skill)

    def test_multiple_cases_and_hooks_share_the_creative_context(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        content = _read("references/content-writing.md")

        for text in (skill, cases, content):
            self.assertIn("多个", text)
            self.assertIn("共同", text)
        self.assertIn("完整案例与钩子技巧分开存放、分别定位", cases)
        self.assertIn("不要求只选择一个案例或一个钩子", cases)
        self.assertIn("模型结合净化后的可写材料、外部真实声音、作者位置、专项模板、多个完整案例和多个钩子", skill)

    def test_creative_flow_has_no_compiler_or_adoption_ledger(self) -> None:
        active_text = "\n".join(
            [_read("SKILL.md")]
            + [path.read_text(encoding="utf-8") for path in (PROJECT_ROOT / "references").glob("*.md")]
        )
        for retired in (
            "scripts/writing_delivery.py",
            "writing-execution-record.schema.json",
            "content-case-search.schema.json",
            "required_relations",
            "optional_amplifiers",
        ):
            self.assertNotIn(retired, active_text)
        self.assertFalse((PROJECT_ROOT / "scripts" / "writing_delivery.py").exists())
        self.assertFalse((PROJECT_ROOT / "schemas").exists())

    def test_hook_library_is_a_distinct_lightweight_resource(self) -> None:
        cases = _read("references/content-case-library.md")
        self.assertIn("钩子技巧只位于 `钩子与开头`", cases)
        self.assertIn("hook_pattern_id", cases)
        self.assertIn("hook_techniques", cases)
        self.assertIn("reader_effects", cases)
        self.assertIn("完整短内容与文章只能成为来源示例", cases)

    def test_first_person_entry_is_not_rejected_as_fake_experience(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("刷到、打开、丢进去试试", skill)
        self.assertIn("直接作为叙事进入方式", content)
        self.assertIn("具体亲历或证据", content)
        self.assertIn("不必先证明它逐字发生过", natural)

    def test_reader_result_stays_distinct_from_proof_and_mechanism(self) -> None:
        prewrite = _read("references/prewriting-research.md")
        github = _read("references/github-project-short-content.md")

        self.assertIn("能直接感受到的变化", prewrite)
        self.assertIn("产物、演示或反馈", prewrite)
        self.assertIn("组件、工作流、数据结构", prewrite)
        self.assertIn("MP4、时间线、工作流、组件或格式", github)

    def test_writing_explanation_is_detailed_but_not_a_validator(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("先给可复制的正文或大纲", skill)
        self.assertIn("足够详细的写作说明", skill)
        self.assertIn("多个案例与钩子共同带来了哪些方向", skill)
        self.assertIn("本次创作参考（实际阅读）", skill)
        self.assertIn("完整案例和钩子文件路径", skill)
        self.assertIn("不输出分数、候选状态、JSON、隐藏推理或检查日志", skill)

    def test_case_library_has_no_creative_search_or_scoring_architecture(self) -> None:
        script = _read("scripts/content_case_library.py")
        cases = _read("references/content-case-library.md")

        for retired in (
            "SearchHit",
            "search_library",
            "render_search_results",
            "_score_content",
            "_score_hook",
            "SEARCH_SCHEMA_VERSION",
            "build_search_receipt",
            "render_search_receipt",
            "candidate_id",
            'add_parser("search"',
            '"--limit"',
        ):
            self.assertNotIn(retired, script)
        self.assertIn("用普通文本搜索直接查标题、正文和隐藏索引", cases)
        self.assertIn("搜索只负责定位文件，不给创作价值打分", cases)

    def test_natural_writing_uses_semantics_not_phrase_blacklists(self) -> None:
        natural = _read("references/natural-writing.md")
        self.assertIn("不要建立“不是……而是……”或其它固定句式黑名单", natural)
        self.assertIn("直接从内容写起", natural)
        self.assertIn("叙事动作可以自由使用", _read("SKILL.md"))

    def test_all_writing_discovers_cleans_drafts_then_checks_the_draft(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("用户要任何文字成品时", skill)
        self.assertIn("发现材料 → 净化材料 → 自由成文 → 核查成品", prewrite)
        self.assertIn("不在动笔前逐项证明资料是否准确", prewrite)
        self.assertIn("只核查成品实际使用的重要事实", natural)
        self.assertIn("不为了逐字严谨改回官方语言", natural)
        self.assertIn("不在段尾补", natural)

    def test_language_defaults_to_chinese_once(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("没有指定时，直接回复和可发布文字默认使用中文", skill)

    def test_voice_and_novelty_remain_separate(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")
        self.assertIn("声音检索与内容查重分开使用", skill)
        self.assertIn("两条检索结果不能互相代用", memory)


if __name__ == "__main__":
    unittest.main()
