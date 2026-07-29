from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8-sig")


class WritingContractTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = _read("SKILL.md")
        references = set(re.findall(r"references/[a-z0-9-]+\.md", skill))
        self.assertIn("references/personal-writing-memory.md", references)
        active_references = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }
        self.assertEqual(active_references, references)
        for reference in references:
            self.assertTrue((PROJECT_ROOT / reference).is_file(), reference)

    def test_references_do_not_route_other_references(self) -> None:
        for path in (PROJECT_ROOT / "references").glob("*.md"):
            text = path.read_text(encoding="utf-8-sig")
            self.assertNotRegex(
                text,
                r"`references/[a-z0-9-]+\.md`",
                path.name,
            )

    def test_audit_and_modify_does_not_reselect_the_writing_type(self) -> None:
        skill = _read("SKILL.md")
        audit = _read("references/content-audit.md")

        self.assertIn("用户要求“检查并修改”现有正文时", skill)
        self.assertIn("再回到同一个写作合同", skill)
        self.assertIn("不能重新选择类型、模板或后续步骤", audit)
        self.assertIn("不在审查类型之间重新选择", audit)
        self.assertNotIn("先确定用户要检查什么", audit)

    def test_ai_flavor_audit_is_explicitly_composed_by_the_upper_route(self) -> None:
        skill = _read("SKILL.md")
        audit = _read("references/content-audit.md")

        self.assertIn("AI 味审查还读取 `references/natural-writing.md`", skill)
        self.assertIn("事实与内容、结构、场景与声音、句子", skill)
        self.assertIn("上层已经同时加载的自然写作检查", audit)

    def test_writing_delivery_is_investigable_and_copyable(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        project_list = _read("references/github-project-list.md")

        self.assertIn("### 4. 实际写作统一交付格式", skill)
        self.assertIn("本节只作用于实际起草、改写、扩写、压缩或重组出的写作正文", skill)
        for field in (
            "写作动作",
            "成品形态",
            "表达任务",
            "使用模板",
            "事实来源",
            "选材依据",
            "完整案例",
            "钩子参考",
            "作者声音",
            "其它要求",
        ):
            self.assertIn(f"**{field}**", skill)
        self.assertLess(skill.index("**写作调查信息。**"), skill.index("**写作正文。**"))
        self.assertIn("把纯正文完整放进一个代码块", skill)
        self.assertIn("没有采用案例时写“未采用”", skill)
        self.assertIn("已经独立检索钩子库", skill)
        self.assertIn("只有成稿能够清楚对回来源原句时才能写“沿用”", skill)
        self.assertIn("不展示隐藏推理", skill)
        self.assertIn("上层负责把可核对的调查信息和代码块正文分开交付", content)
        self.assertIn("纯正文放进代码块", natural)
        self.assertNotIn("代码块外不附说明", project_list)

    def test_personal_memory_has_a_real_producer_and_consumer(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")
        knowledge = _read("references/knowledge-base-workflow.md")

        self.assertIn("scripts/writing_memory.py search", memory)
        self.assertIn("scripts/writing_memory.py build-index", memory)
        self.assertIn("scripts/writing_memory.py validate", knowledge)
        self.assertIn("### 3. 写作动作、精确成品形态和表达任务确定后，按这个顺序写", skill)
        task = skill.index("**锁定写作合同和当前材料。**")
        platform = skill.index("**锁定平台合同。**")
        research = skill.index("**先联网研究并筛选写作材料。**")
        author = skill.index("**再站到作者和读者的位置想清楚怎么讲。**")
        template = skill.index("**再读取已选专项模板。**")
        self.assertLess(task, platform)
        self.assertLess(platform, research)
        self.assertLess(research, author)
        self.assertLess(author, template)
        self.assertLess(
            template,
            skill.index("**匹配并近距离学习完整案例。**"),
        )
        self.assertTrue((PROJECT_ROOT / "scripts/writing_memory.py").is_file())

    def test_single_project_and_project_list_have_separate_templates(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        github = _read("references/github-project-short-content.md")
        project_list = _read("references/github-project-list.md")

        self.assertIn("单个 GitHub 项目介绍", skill)
        self.assertIn("GitHub 项目清单", skill)
        self.assertIn("两者不共用模板", skill)
        self.assertIn("# 单个 GitHub 项目介绍写作模板", github)
        self.assertIn("# GitHub 项目清单模板", project_list)
        self.assertIn("本模板只负责写法", github)
        self.assertIn("完整案例负责正文从头到尾的主要写法", github)
        self.assertIn("逐句判断案例每句话怎样说", github)
        self.assertIn("100% 开源，完全免费。", github)
        self.assertIn("这句话是正文最后一行", github)
        self.assertIn("清单与资源推荐", project_list)
        self.assertNotIn("项目推荐清单", github)
        self.assertNotIn("单个 GitHub 项目介绍模板", project_list)
        self.assertIn("让匹配案例与当前材料承担实际推进", content)
        self.assertIn("本节不在形态之间作选择", content)
        self.assertNotIn("才在下面选择具体形态", content)
        for technical_checklist in (
            "至少回答",
            "二至四项",
            "六项职责不能丢失",
            "项目在完整工作流中承担什么角色",
        ):
            self.assertNotIn(technical_checklist, github)

        forbidden = (
            "所有可发布正文从钩子直接开始",
            "所有完整可发布正文使用同一入口和出口",
            "每条可发布内容都用 CTA",
            "最后用符合作者声音的 CTA 收束",
            "正文前不加标题",
        )
        active_text = "\n".join(
            _read(path)
            for path in (
                "SKILL.md",
                "references/article-from-practice.md",
                "references/content-writing.md",
                "references/github-project-short-content.md",
                "references/github-project-list.md",
                "references/natural-writing.md",
                "references/social-content-distribution.md",
            )
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, active_text)

    def test_viral_goal_uses_cases_without_becoming_a_fixed_template(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        github = _read("references/github-project-short-content.md")
        project_list = _read("references/github-project-list.md")
        natural = _read("references/natural-writing.md")
        active_text = "\n".join((skill, content, github, project_list, natural))

        self.assertIn("用户希望内容获得更广泛传播", skill)
        self.assertIn("案例是成文输入", content)
        self.assertIn("起草时再把原文的句段逐项映射到当前材料", content)
        self.assertIn("不规定固定模板", content)
        self.assertIn("从选中的钩子原句落笔", github)
        self.assertIn("传播目标改变的是选材优先级和表达力度", content)
        self.assertIn("正文沿用精选材料包中的事实输入", content)
        self.assertIn("不强制使用判断、反差或固定句式", project_list)
        self.assertIn("结果、问题、场景、代价、冲突、反差、意外、规模", skill)
        self.assertIn("痛点和冲突不是必经步骤，具体事实也不是唯一默认入口", content)
        self.assertNotIn("读者愿意复述的具体判断作为开头", active_text)
        self.assertNotIn("开头直接写这个判断或变化", active_text)

    def test_case_library_roles_are_routed_and_kept_distinct(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")

        self.assertIn("references/content-case-library.md", skill)
        self.assertIn("完整内容案例", cases)
        self.assertIn("开头案例", cases)
        self.assertIn("索引只负责把原文找出来", cases)
        self.assertIn("写作技巧可以跨题材迁移", cases)
        self.assertIn("成品类型可以提高同类案例的排序，但不能排除其它类型", cases)
        self.assertIn("不提前压缩成案例文件中的一句标准答案", cases)
        self.assertIn("不为角色或题材复制正文", cases)
        self.assertIn("两个角色分别检索或进入候选、分别映射、分别确认采用", cases)

    def test_viral_hook_search_cannot_be_skipped_by_the_full_case_opening(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        github = _read("references/github-project-short-content.md")
        project_list = _read("references/github-project-list.md")
        active_text = "\n".join((skill, cases, github, project_list))

        self.assertIn("无论完整案例有没有开头，都必须另外运行", skill)
        self.assertIn("search --asset hook ... --limit 3", skill)
        self.assertIn("库中能返回多个结果时至少比较两个", skill)
        self.assertIn("完整案例的开头可以加入候选，但不能代替这次独立检索", skill)
        self.assertIn("始终单独运行 `search --asset hook --limit 3`", cases)
        self.assertIn("完整案例的开头只能作为候选之一", github)
        self.assertIn("完整案例的开头不能替代病毒式内容的独立钩子检索", project_list)
        self.assertNotIn("完整案例的开头适用时，直接把它同时作为开头参考", active_text)
        self.assertNotIn("同一案例可以同时作为开头参考，不必再找一条独立开头案例", active_text)

    def test_project_identity_and_supported_relations_reach_every_writer(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        natural = _read("references/natural-writing.md")
        content = _read("references/content-writing.md")
        github = _read("references/github-project-short-content.md")

        self.assertIn("来源怎样说明它是什么", skill)
        self.assertIn("没有可靠来源支持某个任务名称或人群叫法时，直接写具体动作", skill)
        self.assertIn("对象事实：名称；来源怎样说明它是什么", prewriting)
        self.assertIn("材料已有的内容关系", prewriting)
        self.assertIn("受众实际说法", prewriting)
        self.assertIn("对象是什么、直接做什么和作用于什么", natural)
        self.assertIn("项目可以通过材料支持的使用场景、结果或后果进入", content)
        self.assertIn("没有自然的任务名称时直接写具体动作", github)

    def test_hook_use_starts_from_the_source_and_is_verified_after_drafting(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        github = _read("references/github-project-short-content.md")

        self.assertIn("已经选中外部钩子时，第一句从钩子的原句开始", skill)
        self.assertIn("从选中钩子的原句开始写第一句", content)
        self.assertIn("把原文放在草稿旁边", cases)
        self.assertIn("不能只留下案例的技巧名称后重新自由写一个开头", natural)
        self.assertIn("只借“痛点”“反差”“制造好奇”这类技巧名称", github)
        self.assertIn("不能在调查信息中写“沿用”", cases)

    def test_unsupported_rhetorical_relations_are_content_errors(self) -> None:
        prewriting = _read("references/prewriting-research.md")
        natural = _read("references/natural-writing.md")
        audit = _read("references/content-audit.md")

        self.assertIn("没有进入这份列表的关系，后续钩子检索和成文不能补造", prewriting)
        self.assertIn("纠正、反转和对照只有在材料同时提供", natural)
        self.assertIn("即使只出现一次，缺少对应内容也要改", natural)
        self.assertIn("修辞只出现一次，但已经改变项目用途或制造材料中不存在的双方关系", audit)

    def test_selected_case_structure_is_not_cleaned_away(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("以案例为主要写作示范", skill)
        self.assertIn("不为了显示原创而主动改开", skill)
        self.assertIn("默认近距离保留原案例的具体进入方式", content)
        self.assertIn("能够被当前内容承接的具体说法、结构、节奏和格式相似不能被当作 AI 味清除", natural)
        self.assertIn("不能为了让新稿看起来“不像案例”而重新打散", natural)
        self.assertIn("条目数、段落数和具体数值不是自动继承的结构", content)
        self.assertIn("当前材料只有一项真正有力的内容就写一项，有三项同样重要就写三项", _read("references/content-case-library.md"))
        self.assertIn("案例影响它们放在哪里、怎样形成力度和节奏，不决定条目数量", _read("references/github-project-short-content.md"))

    def test_prewrite_research_and_author_thinking_precede_templates_and_cases(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        prewriting = _read("references/prewriting-research.md")

        platform = skill.index("**锁定平台合同。**")
        research = skill.index("**先联网研究并筛选写作材料。**")
        expression = skill.index("**再站到作者和读者的位置想清楚怎么讲。**")
        template = skill.index("**再读取已选专项模板。**")
        case = skill.index("**匹配并近距离学习完整案例。**")
        self.assertLess(platform, research)
        self.assertLess(research, expression)
        self.assertLess(expression, template)
        self.assertLess(template, case)
        self.assertIn("先站到作者和读者的位置", natural)
        self.assertIn("看精选材料，先想清楚这次怎么讲", natural)
        self.assertIn("新写、扩写或会改变主张与选材的改写默认进入", prewriting)
        self.assertIn("根据表达任务决定搜索什么", prewriting)
        self.assertIn("场景、一项结果、一段经历、一条解释链、一个做法、一次推荐", skill)
        self.assertIn("不要求所有内容先提出一个观点再论证", skill)

    def test_prewrite_research_selects_only_material_the_chosen_task_consumes(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        github = _read("references/github-project-short-content.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("先联网研究并筛选写作材料", skill)
        self.assertIn("材料缺口由写作分支自己的前置研究补齐", skill)
        self.assertIn("不让独立研究的输出合同接管正文", skill)
        self.assertIn("正面介绍或推荐只向后续阶段交付正面结果", prewriting)
        self.assertIn("它就是后续正文的唯一事实输入", prewriting)
        self.assertIn("本阶段只消费上层交来的精选材料包", content)
        self.assertIn("精选材料包是正文唯一的事实输入", github)
        self.assertIn("本阶段只消费精选材料包", natural)
        self.assertIn("不重新打开来源或增加包外事实", skill)
        self.assertIn("不把资料类别、检索过程或“大家意见不一”写成开场", content)
        self.assertIn("从项目和最值得传播的变化本身开始", github)
        self.assertIn("不从开场套话、文章意义、检索过程或“外界怎样评价”开始", natural)
        self.assertIn("只写实际采用的网络材料怎样帮助确定正文重点", skill)
        self.assertNotIn("补足支撑当前主张或选择的事实、故事、反方和实际差异", skill)

    def test_source_matching_leaves_editorial_expression_to_the_writing_stage(self) -> None:
        prewriting = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("逐项对应", prewriting)
        self.assertIn("保留关系", prewriting)
        self.assertIn("作者表达", prewriting)
        self.assertIn("用户没有指定时，根据作者位置、目标读者和材料支持的叙事关系选择", prewriting)
        self.assertIn("对象的类别、主要用途、直接动作和作用对象属于事实含义", prewriting)
        self.assertIn("项目可以通过材料支持的使用场景、结果或后果进入", content)
        self.assertIn("对象类别、主要用途、直接动作和作用对象保留事实含义", natural)

    def test_chinese_wording_uses_natural_verb_object_pairs(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        content = _read("references/content-writing.md")
        github = _read("references/github-project-short-content.md")

        self.assertIn("中文里通常和当前对象搭配的动词", natural)
        self.assertIn("先确定谁做了什么、作用于什么", natural)
        self.assertIn("搭配生硬时直接重写整句", natural)
        self.assertIn("具体措辞沿用写作前已经确定的成文语言", content)
        self.assertIn("具体措辞沿用写作前已经确定的成文语言", github)
        self.assertIn("**成稿回读。**", skill)
        self.assertIn("### 第一遍：核对材料、关系和语气", natural)

    def test_upper_route_owns_every_writing_choice_and_case_asset_mapping(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        article = _read("references/article-from-practice.md")
        platform = _read("references/social-content-distribution.md")

        for marker in (
            "大纲",
            "起草",
            "改写",
            "扩写",
            "压缩",
            "重组",
            "审查后修改",
            "回复 `reply`",
            "独立帖 `original`",
            "引用帖 `quote`",
            "资源分享 `resource`",
            "产品帖 `product`",
            "Thread `thread`",
            "通用短帖 `short-post`",
            "单个 GitHub 项目介绍",
            "GitHub 项目清单",
            "文章 `article`",
            "Newsletter `newsletter`",
        ):
            self.assertIn(marker, skill)
        self.assertIn("案例资源", skill)
        self.assertIn("search --asset short", skill)
        self.assertIn("search --asset article", skill)
        self.assertIn("search --asset hook", skill)
        self.assertIn("不能省略 `--asset`", skill)
        self.assertIn("本节不在形态之间作选择", content)
        self.assertIn("不重新选择声音分析、内容审查、研究或其它主结果", article)
        self.assertIn("不选择读者、主任务、角度、主要材料、模板或正文主线", platform)
        self.assertNotIn("每条先选择一个主任务", platform)

    def test_voice_resource_only_supplies_voice_evidence(self) -> None:
        voice = _read("System Knowledge/60-Systems/Writing/style-guide/voice.md")

        self.assertIn("这份文件只保存当前个人写作声音", voice)
        self.assertIn("不选择写作任务、成品形态、模板、案例、文章结构或保存动作", voice)
        self.assertIn("写作声音", voice)
        for legacy in (
            "先判断自己要完成哪种内容任务",
            "选择对应结构",
            "两至五个短段落",
            "2026-",
            "更新方式",
            "logs/decisions.md",
            "内容案例索引",
            "0xCheshire",
            "_FORAB",
        ):
            self.assertNotIn(legacy, voice)

    def test_legacy_voice_entry_is_not_referenced(self) -> None:
        active_text = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in [
                PROJECT_ROOT / "SKILL.md",
                *(PROJECT_ROOT / "references").glob("*.md"),
            ]
        )
        self.assertNotIn("references/author-voice.md", active_text)


if __name__ == "__main__":
    unittest.main()
