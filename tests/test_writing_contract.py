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
        self.assertIn("默认留在研究材料中", project)
        self.assertIn("都不足以让它进入正文", project)
        self.assertIn("不在项目入口附近或结尾合并成一组稳妥说明", project)
        self.assertNotIn("适合保留时可以压缩进项目入口附近或结尾", project)
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
        self.assertIn("是效果目标，不是修辞模板", content)

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
        hooks = _read("references/hook-library.md")
        content = _read("references/content-writing.md")

        for text in (skill, cases, content):
            self.assertIn("多个", text)
            self.assertIn("共同", text)
        self.assertIn("多份钩子和多份完整案例", hooks)
        self.assertIn("它不管理钩子", cases)
        self.assertIn("不同目录、脚本、数据类型与索引", skill)
        self.assertIn("多个完整案例与多个独立钩子原文共同参与写作", content)

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
        hooks = _read("references/hook-library.md")
        self.assertIn("案例文件不存在钩子字段，也不能通过案例路径生成钩子", cases)
        self.assertIn("连续开头与紧接内容", hooks)
        self.assertIn("只有连续原文、来源和寻址字段", hooks)
        for polluted in ("hook_techniques", "reader_effects", "source_case_file"):
            self.assertNotIn(polluted, hooks)

    def test_first_person_experience_cannot_be_borrowed_from_references(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("不能转写成本次作者经历", skill)
        self.assertIn("第一人称属于原作者", content)
        self.assertIn("案例中的“我”不能迁移给当前作者", natural)

    def test_reader_result_stays_distinct_from_proof_and_mechanism(self) -> None:
        prewrite = _read("references/prewriting-research.md")
        github = _read("references/github-project-short-content.md")

        self.assertIn("能直接感受到的变化", prewrite)
        self.assertIn("产物、演示或反馈", prewrite)
        self.assertIn("组件、工作流、数据结构", prewrite)
        self.assertIn("MP4、时间线、工作流、组件或格式", github)

    def test_delivery_follows_reader_use_and_keeps_the_explanation_by_default(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("表达任务只说明内容讲什么，不决定长短", skill)
        self.assertIn("单个代码块仍便于通读和整段复制", skill)
        self.assertIn("内容较长、结构复杂或需要继续修改时使用 Markdown 文件", skill)
        self.assertIn("先交付正文或大纲", skill)
        self.assertIn("提示词不是默认组成", skill)
        self.assertIn("只是介绍、推荐、制造兴趣或提供项目入口时不加提示词", skill)
        self.assertNotIn("具备目标环境操作能力的 AI 能完成核心动作时，正文给出", skill)
        self.assertIn("普通读者不需要先理解技术实现", content)
        self.assertIn("除非用户明确只要正文", skill)
        self.assertIn("本次创作参考（实际阅读）", skill)
        self.assertIn("本次实际阅读的案例与钩子路径", natural)

    def test_actionable_copy_uses_ai_prompts_only_when_they_are_the_real_next_step(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        project = _read("references/github-project-short-content.md")
        natural = _read("references/natural-writing.md")

        for text in (skill, content, project):
            self.assertIn("一至三句", text)
        self.assertIn("提示词不是正文的固定部分", content)
        self.assertIn("提示词不是项目介绍的固定部分", project)
        self.assertIn("没有因为 AI 可以代办而机械加入", skill)
        self.assertIn("因为 AI 理论上能够代办某个动作而机械增加", natural)
        self.assertNotIn("AI 能完成正文任务却没有给出", natural)
        self.assertNotIn("AI 能完成本篇任务时已经给出", project)
        self.assertIn("AI 提示词可执行性", natural)

    def test_action_entry_has_one_goal_based_owner(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        project = _read("references/github-project-short-content.md")
        project_list = _read("references/github-project-list.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("具体选择和呈现统一由 `references/content-writing.md` 执行", skill)
        self.assertIn("本阶段也不根据命令外形替正文选择最终入口", prewrite)
        self.assertIn("行动入口的唯一选择规则", content)
        self.assertIn("普通介绍、推荐、分享或制造兴趣", content)
        self.assertIn("不包含完整的 HTTP(S) URL", content)
        self.assertIn("没有隐藏前置步骤", content)
        self.assertIn("`npx package-name`", content)
        self.assertIn("`curl`、`wget` 或 `iwr`", content)
        self.assertIn("属于链接式安装路线，不算直接指令", content)
        self.assertIn("先用自然语言说明这条指令会完成什么", content)
        self.assertIn("本模板不根据命令外形重选行动入口", project)
        self.assertIn("本模板不为每个项目重新选择行动入口", project_list)
        self.assertIn("已选行动入口不能完成正文承诺的下一步", natural)

        for text in (skill, prewrite, content, project, project_list, natural):
            self.assertNotIn("一行安装或启用指令", text)
            self.assertNotIn("不再放项目链接", text)

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
        self.assertIn("用普通文本搜索标题、正文和隐藏索引", cases)
        self.assertIn("索引只负责定位", cases)

    def test_natural_writing_uses_semantic_contribution_not_style_menus(self) -> None:
        natural = _read("references/natural-writing.md")
        self.assertIn("不用一个抽象动词代替几个具体动作", natural)
        self.assertIn("一个正常人会不会在聊天中直接这样说", natural)
        self.assertIn("谁做了什么、结果怎样", natural)
        self.assertIn("不靠建立词语黑名单判断", natural)
        self.assertIn("直接从内容写起", natural)
        self.assertIn("增加了事实、关系或推进", natural)
        active = "\n".join(
            [_read("SKILL.md")]
            + [path.read_text(encoding="utf-8") for path in (PROJECT_ROOT / "references").glob("*.md")]
        )
        for polluted in (
            "口语概括、假设场景、轻微泛化",
            "反差、设问、排比、比喻、短句和口语都可以用",
            "可以自由使用",
        ):
            self.assertNotIn(polluted, active)

    def test_all_writing_discovers_cleans_drafts_then_checks_the_draft(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("用户要任何文字成品时", skill)
        self.assertIn("发现材料 → 净化材料 → 围绕具体关系成文 → 核查成品", prewrite)
        self.assertIn("不在动笔前逐项证明资料是否准确", prewrite)
        self.assertIn("只核查成品实际使用的重要事实", natural)
        self.assertIn("不要为了形式上的严谨改回官方套话", natural)
        self.assertIn("不在段尾补", natural)

    def test_material_based_writing_is_creative_for_short_and_long_outputs(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("不把它解释成忠实摘要合同", skill)
        self.assertIn("这一判断同时适用于短帖、Thread、项目介绍、文章和 Newsletter", skill)
        self.assertIn("不联网只限制信息来源", skill)
        self.assertIn("事实锚点", prewrite)
        self.assertIn("不把每条时间片依次改写成正文", prewrite)
        self.assertIn("恢复成完整互动", content)
        self.assertIn("短内容围绕一条最值得复述的关系", content)
        self.assertIn("长内容可以继续展开机制、例子、反面情况、现实意义和行动框架", content)
        self.assertIn("不当作等待换词的句子库", natural)
        self.assertIn("没有逐字出处但有场景依据的作者判断", natural)
        self.assertIn("已经建立的读者收获", natural)

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
