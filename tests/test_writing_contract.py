from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class SkillStructureTests(unittest.TestCase):
    def test_skill_references_every_active_reference(self) -> None:
        skill = _read("SKILL.md")
        referenced = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }
        self.assertEqual(active, referenced)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in referenced))

    def test_references_do_not_route_to_sibling_references(self) -> None:
        paths = sorted((PROJECT_ROOT / "references").glob("*.md"))
        active_names = {path.name for path in paths}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            mentioned = sorted(
                name for name in active_names if name != path.name and name in text
            )
            self.assertEqual([], mentioned, path)

    def test_writing_completes_in_one_turn_without_old_routes_or_handoff(self) -> None:
        contract = "\n".join(
            (
                _read("SKILL.md"),
                _read("references/writing-material-preparation.md"),
                _read("references/content-writing.md"),
                _read("references/private-knowledge-library.md"),
                _read("references/content-case-library.md"),
                _read("references/hook-library.md"),
            )
        )
        for retired in (
            "材料完备短内容",
            "发现式新写",
            "局部修改路线",
            "一份合格主案例",
            "至少一份、最多两份",
            "固定两份",
        ):
            self.assertNotIn(retired, contract)

        skill = _read("SKILL.md")
        self.assertIn("只用一份最好的完整参考", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("材料准备和成文在同一次回复中连续完成", skill)
        self.assertIn("材料准备、补充或研究、直接成文和最终交付在同一次处理中连续完成", contract)
        self.assertIn("材料准备、补充和研究只执行一次", contract)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertNotIn("正式交接文件", contract)
        self.assertNotIn("第一轮：交出正式准备文件", contract)
        self.assertNotIn("第二轮：只读交接文件成文", contract)

    def test_writing_researches_content_when_needed_and_still_finds_references(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        contract = "\n".join((skill, preparation))
        self.assertIn("写作前可以联网发现", contract)
        self.assertIn("用户明确要求联网补充时直接执行", contract)
        self.assertIn("明确禁止联网", contract)
        self.assertIn("只使用给定材料", contract)
        self.assertIn("只改错字、格式和等义措辞", contract)
        self.assertIn("文章材料要足以支撑成文", skill)
        self.assertIn("用户只给出主题、问题，或者现有材料无法支撑文章的核心判断时", skill)
        self.assertIn("当前材料无法支撑核心判断时", preparation)
        self.assertIn("支持、限制或推翻主要解释的来源", preparation)
        self.assertIn("不逐项验证用户已经给出的所有说法", preparation)
        self.assertIn("不生成事实核查报告", preparation)
        self.assertIn("不调用这两份研究交付格式", skill)
        self.assertIn("既不能增加理解、校正判断和支持具体表达，也不值得作为写作参考时不加入", preparation)
        self.assertIn("内容材料已经足够不等于写作参考已经足够", skill)
        self.assertIn("即使事实材料已经足够", skill)
        self.assertIn("仍然进行这项参考发现", skill)
        self.assertIn("不单独生成研究报告、中心句、因果简报、大纲或段落任务", skill)
        self.assertIn("草稿完成后只核对正文实际写出的", skill)
        self.assertIn("成稿完成后只检查正文实际使用的", _read("references/content-writing.md"))
        self.assertNotIn("搜索服从材料缺口", contract)
        self.assertNotIn("两篇普通短内容或一篇中等篇幅文章", contract)

        writing = skill.split("## 写作", 1)[1].split("## 知识库与持久化", 1)[0]
        self.assertNotIn("research-context-reuse.md", writing)
        self.assertNotIn("research-led-learning.md", writing)

    def test_plan_mode_supplements_before_interviewing_for_subjective_material(self) -> None:
        skill = _read("SKILL.md")
        plan = skill.split("### Plan 模式下先补充再访谈", 1)[1].split(
            "### 默认模式下准备并直接成文", 1
        )[0]

        self.assertIn("用户主动开启 Plan 模式视为明确的深度访谈请求", plan)
        self.assertIn("不论现有材料是否已经足够成文", plan)
        self.assertIn("必须先完成本次需要的材料查找", plan)
        self.assertIn("再使用 `request_user_input` 开始访谈", plan)
        self.assertLess(
            plan.index("必须先完成本次需要的材料查找"),
            plan.index("再使用 `request_user_input` 开始访谈"),
        )
        self.assertIn("不先询问能够从现有材料或公开来源自行取得的客观信息", plan)
        self.assertIn("真实情绪、感受、观点和立场", plan)
        self.assertIn("每轮只集中推进一个问题", plan)
        self.assertIn("不按固定问卷机械遍历", plan)
        self.assertIn("不重复询问用户已经回答过的问题", plan)
        self.assertIn("默认模式下资料已经足够时停止", skill)

    def test_material_preparation_reads_full_sources_then_selects_relevant_originals(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        content = _read("references/content-writing.md")
        promotion = _read("references/project-promotion-materials.md")
        contract = "\n".join((skill, preparation, content, promotion))
        self.assertIn("先完整阅读每份来源", preparation)
        self.assertIn("再区分来源原文与本次成文材料", preparation)
        self.assertIn("不是整份来源的副本，也不是正文提纲", preparation)
        self.assertIn("不因为来源中的每项内容彼此不同，就机械纳入整份来源", preparation)
        self.assertIn("事实、关系、判断、猜测、问题、宣发角度和内容主次作为材料保留原话", preparation)
        self.assertIn("帮助理解对象、比较可能写法、支持具体表达或保证行动准确", preparation)
        self.assertIn("不改变本次理解、表达或行动的穷举细节", preparation)
        self.assertIn("材料取舍也不替模型预先决定最终角度", preparation)
        self.assertIn("旧成品或示例文案", preparation)
        self.assertIn("用户把事实列入材料，不等于要求正文逐项覆盖", preparation)
        self.assertIn("主次、已确认事实、可讨论信息、开放问题、猜测边界和补充内容", preparation)
        self.assertIn("会改变理解、表达或行动的新条件、参与者、原因或结果", preparation)
        self.assertIn("没有固定材料条数", preparation)
        self.assertIn("不要求所有内容都归结为一个变化、卖点或中心句", preparation)
        self.assertNotIn("即使最终正文可能不用", preparation)
        self.assertNotIn("每项不同的事实、关系、动作、阶段、数字、限制、利益、邀请条件和行动入口", preparation)
        self.assertIn("宣发重点、内容主次、讨论问题、猜测方向和补充信息继续作为材料", promotion)
        self.assertNotIn("选题清单和内部宣传建议只作为准备侧信息", promotion)
        self.assertIn("来源原文、原有顺序、来源边界和必要上下文", contract)
        self.assertIn("不摘要、转述、重排、拼接或统一改写", preparation)
        self.assertIn("## 写作输入", content)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertIn("材料准备、补充和研究只执行一次", preparation)
        for retired_heading in (
            "【用户要求】",
            "【材料】",
            "【写作参考】",
            "【作者声音】",
            "【写作规则】",
            "【通用写作注意】",
            "【参考案例】",
            "【参考开头】",
            "【完整案例】",
            "【完整钩子】",
            "【其它实际写作输入】",
        ):
            self.assertNotIn(retired_heading, content)
        self.assertIn("不为了展示写作过程而重新复制成带有固定栏目或标签的材料包", content)
        self.assertIn("案例库为了保存内容生成的标题、栏目名及其它包装也不参与成文", content)
        self.assertIn("实际选用的唯一完整写作参考", content)
        self.assertNotIn("相邻正文之间", content)
        self.assertNotIn("相邻参考之间", content)
        self.assertIn("只使用唯一一份实际参考正文", content)
        self.assertIn("专项说明、材料取舍理由、搜索记录和维护规则", preparation)
        self.assertIn("说明文件本身、维护理由、字段名和检查过程不进入成文输入", skill)
        self.assertNotIn("留下足以准确成文的最少内容", contract)
        self.assertNotIn("写作简报", content)
        self.assertIn("区分内容来源与写作参考", preparation)
        self.assertIn("字幕、访谈、同主题文章和研究资料", preparation)
        self.assertIn("写法真正优秀的完整内容也可以同时作为写作参考", preparation)
        self.assertIn("本地文章案例和用户明确要求参考写法的样稿只帮助表达", preparation)
        self.assertIn("不替当前对象提供事实", preparation)
        self.assertIn("组织松散、论证薄弱或信息混杂时", preparation)
        self.assertIn("不把来源的结构、语气和叙述缺陷变成成品要求", preparation)
        self.assertIn("没有内容来源时", preparation)
        self.assertIn("写作参考不是事实缺口", preparation)
        self.assertIn("只选一份最值得当前文章深入模仿的完整参考", preparation)
        self.assertIn("不把研究结果改写成中心句、因果简报、内容路线、大纲或段落任务", preparation)
        self.assertIn("证据暂时不能支持唯一结论时保留这种不确定性", preparation)

    def test_writer_uses_current_context_without_visible_material_package(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        for retired_heading in (
            "【用户要求】",
            "【材料】",
            "【写作参考】",
            "【作者声音】",
        ):
            self.assertNotIn(retired_heading, content)
        self.assertIn("不为了展示写作过程而重新复制成带有固定栏目或标签的材料包", content)
        self.assertIn("用户指定的对象、问题、文章重心和成品类型", content)
        self.assertIn("不能把解释、研究或评论改造成题材相近但重心不同的人物故事", content)
        self.assertIn("不为了缩短或展示材料而重写成二手摘要", content)
        self.assertIn("借鉴参考时不照抄原句", content)
        for retired_reference_check in (
            "叙述推进、信息安排、详略、段落节奏、转折、语气和收束方式",
            "如果拿掉参考也大概率会得到几乎相同的通用文章",
            "继续返修当前稿",
            "同一个成文模型检查唯一参考",
        ):
            self.assertNotIn(retired_reference_check, content)
        self.assertNotIn("让故事和分析共同推进", content)
        self.assertNotIn("材料没有可信故事时", content)
        self.assertNotIn("不退化成提纲、说明书或研究资料汇编", content)
        self.assertNotIn("当前成品从哪里进入、展开哪些内容以及怎样组合", content)
        self.assertNotIn("不预设它必须归结为", content)
        self.assertNotIn("不先替正文规定读者必须得到", content)
        self.assertNotIn("确定一个读者能感受到的核心变化", content)
        for retired_style_rule in (
            "按用户强调的内容分清主次",
            "正文只放核心关系和必要事实",
            "开头从具体变化、冲突、结果或真实情绪",
            "每句话增加新事实",
            "普通名词不加装饰性引号",
            "不反复使用“不是……而是……”",
            "不强补总结、金句、问题或结尾",
        ):
            self.assertNotIn(retired_style_rule, content)

        runtime = "\n".join(
            _read(path)
            for path in (
                "SKILL.md",
                "references/content-writing.md",
                "references/natural-writing.md",
                "references/content-audit.md",
                "references/article-from-practice.md",
                "references/publication-requirements.md",
                "references/project-promotion-materials.md",
            )
        )
        self.assertNotIn("以为……其实……", runtime)
        self.assertNotIn("不只是……而是……", runtime)

        for retired_prewrite_contract in (
            "准备材料的信息范围与拟写正文保持一致",
            "最值得传播的变化",
            "直接影响所需",
            "不先搭次要说法再转折",
            "抽象结论、口号或问题",
            "互补价值",
        ):
            self.assertNotIn(retired_prewrite_contract, runtime)

    def test_normal_writing_reads_references_without_loading_maintenance_rules(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("当前用户提供或点名的材料、私人库中的同主题完整来源、公开网络中的同主题或相近写作任务原文、文章案例库中的通用案例依次发现", skill)
        self.assertIn("中文成稿优先寻找自然的中文原文", skill)
        self.assertIn("同主题本地来源可以在上述活动原始来源范围内使用 `rg`、`Select-String` 或等效工具", skill)
        self.assertIn("搜索文件路径、标题、来源元数据和正文", skill)
        self.assertIn("文章案例仍只通过文章案例索引分组及其中的稳定编号链接发现", skill)
        self.assertIn("沿链接阅读全文后再判断", skill)
        self.assertIn("通用案例与当前题材、行业或对象相同都不是前提", skill)
        self.assertIn("不对案例正文目录进行全文检索", skill)
        self.assertIn("不把句式、修辞词组、题材、行业、对象或具体情节作为通用案例搜索词", skill)
        self.assertIn("同时作为内容来源与唯一写作参考", skill)
        self.assertIn("不能被题材无关的通用案例替代", skill)
        self.assertIn("即使事实材料已经足够", skill)
        self.assertIn("仍然进行这项参考发现", skill)
        self.assertIn("只选一份最好的完整原文", skill)
        self.assertIn("不为成文输入增加第二份写作参考", skill)
        self.assertIn("不自动保存进私人库", skill)
        self.assertNotIn("活动案例与钩子正文中全文搜索", skill)
        self.assertIn("孤立钩子不是普通文章的默认候选", skill)
        self.assertIn("选中后同样占用唯一写作参考位置", skill)
        content = _read("references/content-writing.md")
        self.assertIn("实际选用的唯一完整写作参考", skill)
        self.assertIn("它可以帮助表达和组织", skill)
        self.assertIn("认真寻找后仍没有合适参考", skill)
        self.assertIn(
            "写作参考只帮助表达与组织",
            content,
        )
        for retired_creative_instruction in (
            "直接模仿原文里的具体表达",
            "三份案例共同影响",
            "三份钩子共同影响",
            "词序、句长、停顿",
            "不先把参考概括成技巧标签或写法清单",
            "不另造概括性开场",
            "在六份完整原文的共同影响下",
            "当前成品从哪里进入",
            "主要靠翻译腔、通用夸张或悬念套话",
        ):
            self.assertNotIn(retired_creative_instruction, "\n".join((skill, content)))
        self.assertNotIn("每份案例都承接一种", content)
        self.assertNotIn("每份钩子都承接一种", content)
        self.assertNotIn("不要求模型逐条模仿", content)
        self.assertNotIn("偶然细节或连续措辞", content)
        self.assertNotIn("主参考", "\n".join((skill, content)))
        self.assertIn("用户要求维护完整案例或钩子时", skill)
        self.assertNotIn("## 普通写作读取", cases)
        self.assertNotIn("## 普通写作读取", hooks)
        self.assertNotIn("至少三份", skill)
        for retired_quota in (
            "三个完整案例和三个完整钩子",
            "三份完整文章案例和三份完整开头钩子",
            "三个不同的写作技巧分组",
            "正好选入三份",
            "不增加第四份",
            "补足三份",
            "选入的六份参考",
        ):
            self.assertNotIn(retired_quota, "\n".join((skill, content)))

    def test_continuous_rewrite_preserves_unaffected_strengths_unless_reset_is_explicit(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("“重新写”“重写”或等义修改时，不自动清空上一稿", skill)
        self.assertIn("保留用户已经明确认可", skill)
        self.assertIn("不受当前问题影响、仍有助于成品的事实、关系、叙事和表达", skill)
        self.assertIn("只有用户明确要求完全换方向，或者明确要求从头写且不沿用上一稿", skill)
        self.assertIn("才不把上一稿放入成文输入并重新独立成文", skill)
        self.assertIn("连续修改不重复联网和准备材料", skill)
        self.assertNotIn("重新选择案例与钩子，从零独立成文", skill)

    def test_private_library_is_not_a_writing_gate(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("运行 `python scripts/private_library.py show`", skill)
        self.assertIn("私人库不可用时继续从当前材料和公开网络准备参考", skill)

    def test_normal_writing_private_library_allowlist_and_author_voice_opt_in(self) -> None:
        skill = _read("SKILL.md")
        private_library = _read("references/private-knowledge-library.md")
        knowledge = _read("references/knowledge-base-workflow.md")
        article = _read("references/article-from-practice.md")
        memory = _read("references/personal-writing-memory.md")
        content = _read("references/content-writing.md")
        contract = "\n".join(
            (skill, private_library, knowledge, article, memory, content)
        )
        self.assertIn("普通文章写作先在 `<私人知识库>/20-Sources` 的活动原始来源中发现", skill)
        self.assertIn("排除 `Archive`、`Content Cases` 和 `Hook Library`", skill)
        self.assertIn("不读取 `Home.md`、`10-Knowledge`、项目、成果、作者声音、发布历史、内容策略或同主题知识笔记", skill)
        self.assertIn("通用文章案例只从文章案例索引及其指向的完整案例取得", private_library)
        self.assertIn("用户明确要求专门设计或修改开头时，才读取钩子索引", private_library)
        self.assertIn("孤立钩子不作为普通文章的默认候选", article)
        self.assertIn("在 `20-Sources` 的活动原始来源中按当前主题实体及其中英文名称或常见别名搜索", private_library)
        self.assertIn("排除 `Archive`、`Content Cases` 与 `Hook Library`", private_library)
        self.assertIn("不读取库首页、`10-Knowledge`、项目、成果、作者声音、发布历史、内容策略或同主题知识笔记", private_library)
        self.assertIn("普通写作不从这里读取主题知识或启动知识补全", knowledge)
        self.assertIn("普通文章写作不从私人库读取作者声音或发布历史", skill)
        self.assertIn("不因为成品较长就读取私人库中的作者声音", article)
        self.assertIn("普通文章写作不自动进入本流程", memory)
        self.assertIn("用户明确要求读取私人库中的既有声音", memory)
        self.assertIn("不自动并入其它普通写作", memory)
        self.assertIn("用户给出的文字默认是来源材料，不是用户本人写的现稿", content)
        self.assertIn("只放用户在当前请求中直接提供的声音样稿", content)
        self.assertNotIn("Newsletter", contract)
        self.assertNotIn("当前对象的事实和作者身份以本次材料为准", content)
        self.assertIn("第一人称经历、使用体验", skill)
        self.assertIn("第一人称经历、使用体验", content)

    def test_model_controls_creation_without_outline_or_review_route(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("由它决定角度、取舍、结构、语言、篇幅和结束位置", skill)
        self.assertIn("直接写出用户要的内容", content)
        self.assertIn("没有指定数量时只生成一个", content)
        self.assertIn("不再启动独立评审、融合或润色", content)
        self.assertNotIn("由同一个成文模型检查唯一参考是否真实改变了文章", content)
        self.assertIn("提纲或写法清单", content)

    def test_source_and_finished_languages_are_separate(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("直接回复和文章默认使用中文", skill)

    def test_short_form_generation_is_retired_without_removing_analysis_or_history(self) -> None:
        skill = _read("SKILL.md")

        self.assertIn(
            "本 Skill 不生成短帖、Thread、GitHub 项目短介绍或清单，以及项目或产品的短宣发文案",
            skill,
        )
        self.assertIn("理解、研究、分享筛选、内容审查、发布复盘或文章写作", skill)
        self.assertIn("不自动把短内容请求改成材料包", skill)
        self.assertIn("也不转交其它写作模型", skill)
        self.assertNotIn("references/github-project-short-content.md", skill)
        self.assertNotIn("references/github-project-list.md", skill)
        self.assertIn("短帖和 Thread 都使用 `social`", skill)

    def test_delivery_exposes_code_block_result_and_reference_only(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("每次文章写作在同一次回复中只展示两部分", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("用户没有提出限制时不擅自补上“不要搜索外部资料”等要求", skill)
        self.assertIn("文章写作前可以联网发现新的内容材料和完整写作参考", _read("references/writing-material-preparation.md"))
        self.assertNotIn("**写作要求**", skill)
        self.assertNotIn("**写作准备材料**", skill)
        self.assertEqual(1, skill.count("**结果**"))
        self.assertEqual(1, skill.count("**本次创作参考**"))
        self.assertIn("每份最终成稿分别放在独立代码块中", skill)
        self.assertIn("默认不展示写作要求、准备材料、成文输入、搜索过程或其它内部处理说明", skill)
        self.assertIn("只列出真正用于本次成文的唯一完整写作参考", skill)
        self.assertIn("不列候选阶段读过但没有采用的内容", skill)
        self.assertIn("本地参考使用可点击的绝对文件路径", skill)
        self.assertIn("临时公开参考使用原始网页链接", skill)
        self.assertIn("本次未找到合适的完整写作参考", skill)
        self.assertNotIn("writing-handoff.md", "\n".join((skill, content)))
        self.assertNotIn("**修改前**", skill)
        self.assertNotIn("**修改后**", skill)
        self.assertNotIn("本次信息来源", skill)

    def test_ai_flavor_audit_edits_only_confirmed_problems(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        audit = _read("references/content-audit.md")
        self.assertEqual(1, skill.count("references/natural-writing.md"))
        self.assertIn("用户要求检查或清理 AI 味时", skill)
        self.assertIn("没有内容作用的句子可以删除", natural)
        self.assertIn("删除后不补抽象总结", natural)
        self.assertIn("不把失败句式和禁用示例重新放进创作输入", natural)
        self.assertIn("只修改已经确认的问题", audit)
        self.assertIn("不借审查重新设计全文", audit)

    def test_publication_facts_do_not_prescribe_activity_copy_structure(self) -> None:
        publication = _read("references/publication-requirements.md")
        promotion = _read("references/project-promotion-materials.md")
        self.assertNotIn("活动发布型短内容使用同一条内容关系", publication)
        self.assertNotIn("最后落在参与结果", publication)
        self.assertIn("它只准备事实", publication)
        self.assertIn("文件正文、栏目、字段名和检查过程不进入成文输入", publication)
        self.assertIn("不规定开头、身份、语气、结构、篇幅和结尾", promotion)
        self.assertIn("融资、支持方、钱包入口、基础设施合作", promotion)
        self.assertIn("本文件不生成摘要、提纲、角度方案或写法要求", promotion)

    def test_reference_admission_keeps_quality_maintenance(self) -> None:
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("信息量与篇幅相称", cases)
        self.assertIn("空泛总结", cases)
        self.assertIn("重新阅读全文", cases)
        self.assertIn("可回查归档并重建索引", cases)
        self.assertIn("具体事实、动作、冲突、结果、问题或真实情绪", hooks)
        self.assertIn("自然接入后文", hooks)
        self.assertIn("可回查归档并重建索引", hooks)

    def test_reference_resources_keep_social_history_without_restoring_generation(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("本 Skill 不生成短帖、Thread", skill)
        self.assertIn("短帖和 Thread 都使用 `social`", skill)
        self.assertIn("社交内容案例索引.md", cases)
        self.assertIn("独立短帖和 Thread 不再区分", cases)
        self.assertNotIn("--kind short", cases)
        self.assertIn("Hook Library/钩子索引.md", hooks)
        self.assertIn("不保存适用形式字段", hooks)
        self.assertNotIn("--format", hooks)
        for retired in ("短内容钩子索引.md", "Thread钩子索引.md", "文章钩子索引.md"):
            self.assertNotIn(retired, "\n".join((skill, cases, hooks)))


if __name__ == "__main__":
    unittest.main()
