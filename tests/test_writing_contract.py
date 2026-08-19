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
        self.assertIn("三个完整案例和三个完整钩子参与文章写作", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("材料准备和成文在同一次回复中连续完成", skill)
        self.assertIn("材料准备、直接成文和最终交付在同一次处理中连续完成", contract)
        self.assertIn("材料准备与联网补充只执行一次", contract)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertNotIn("正式交接文件", contract)
        self.assertNotIn("第一轮：交出正式准备文件", contract)
        self.assertNotIn("第二轮：只读交接文件成文", contract)

    def test_writing_browses_for_supplement_without_prewrite_fact_check(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        contract = "\n".join((skill, preparation))
        self.assertIn("写作前可以联网发现", contract)
        self.assertIn("用户明确要求联网补充时直接执行", contract)
        self.assertIn("明确禁止联网", contract)
        self.assertIn("只使用给定材料", contract)
        self.assertIn("只改错字、格式和等义措辞", contract)
        self.assertIn("联网补充不是研究或事实核查", skill)
        self.assertIn("不是逐项验证用户已经给出的说法", preparation)
        self.assertIn("不生成事实核查报告", preparation)
        self.assertIn("不以核查完成作为开始写作的前置条件", skill)
        self.assertIn("写作中的联网补充不调用这两份研究说明", skill)
        self.assertIn("没有增加理解或传播价值时不加入", preparation)
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
        self.assertIn("必须先完成本次需要的联网补充", plan)
        self.assertIn("再使用 `request_user_input` 开始访谈", plan)
        self.assertLess(
            plan.index("必须先完成本次需要的联网补充"),
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
        self.assertIn("材料准备与联网补充只执行一次", preparation)
        self.assertIn("【用户要求】", content)
        self.assertNotIn("【写作规则】", content)
        self.assertNotIn("【通用写作注意】", content)
        self.assertIn("【材料】", content)
        self.assertIn("【参考案例】", content)
        self.assertIn("【参考开头】", content)
        self.assertNotIn("【完整案例】", content)
        self.assertNotIn("【完整钩子】", content)
        self.assertNotIn("【其它实际写作输入】", content)
        self.assertIn("【作者声音】", content)
        self.assertIn("不带案例库生成的标题", content)
        self.assertIn("不带钩子库生成的标题", content)
        self.assertIn("依次完整放入实际读取的三份写作案例正文", content)
        self.assertIn("依次完整放入实际读取的三份开头钩子正文", content)
        self.assertIn("相邻正文之间单独放一行 `---`", content)
        self.assertIn("相邻案例之间和相邻钩子之间各用一行 `---`", content)
        self.assertIn("“原文全文”等栏目名", content)
        self.assertIn("“钩子原文”等栏目名", content)
        self.assertIn("只保留实际参考正文", content)
        self.assertIn("专项说明、材料取舍理由、搜索记录和维护规则", preparation)
        self.assertIn("说明文件本身、维护理由、字段名和检查过程不进入成文输入", skill)
        self.assertNotIn("留下足以准确成文的最少内容", contract)
        self.assertNotIn("写作简报", content)

    def test_writer_input_is_minimal_without_generic_style_rules(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertEqual(1, content.count("【用户要求】"))
        self.assertEqual(1, content.count("【材料】"))
        self.assertEqual(1, content.count("【参考案例】"))
        self.assertEqual(1, content.count("【参考开头】"))
        self.assertEqual(1, content.count("【作者声音】"))
        self.assertNotIn("【写作规则】", content)
        self.assertNotIn("【其它实际写作输入】", content)
        self.assertNotIn("【通用写作注意】", skill)
        self.assertIn("这里是文章成文输入的唯一模板", content)
        self.assertNotIn("当前对象的事实和作者身份以本次材料为准", content)
        self.assertIn(
            "完整阅读当前材料、三份案例和三份钩子，把它们作为参考，直接写出用户要的内容。",
            content,
        )
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
            "参考已经足够",
            "互补价值",
        ):
            self.assertNotIn(retired_prewrite_contract, runtime)

    def test_normal_writing_reads_references_without_loading_maintenance_rules(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("文章和 Newsletter 优先从本地私人库读取三份完整文章案例和三份完整开头钩子", skill)
        self.assertIn("文章和 Newsletter 从文章案例索引", skill)
        self.assertIn("从统一钩子索引打开多份有帮助的参考开头钩子", skill)
        self.assertIn("分别从活动案例索引和钩子索引选择三个不同的写作技巧分组", skill)
        self.assertIn("从每个分组沿一个稳定编号链接打开完整原文", skill)
        self.assertIn("以原文是否值得参考、是否适合当前写作为准", skill)
        self.assertIn("优先在原分组换读", skill)
        self.assertIn("原分组没有可用正文时再从相邻分组换读", skill)
        self.assertNotIn("只在原分组中换读另一份", skill)
        self.assertIn("索引标签只负责确定候选分组，完整原文决定最终取舍", skill)
        self.assertIn("题材、行业和具体对象相同都不是前提", skill)
        self.assertIn("候选发现只通过索引分组及其中的稳定编号链接进行", skill)
        self.assertIn("不对案例或钩子正文目录运行 `rg`、`Select-String` 或其它全文检索", skill)
        self.assertIn("不把句式、修辞词组、题材、行业、对象或具体情节作为候选搜索词", skill)
        self.assertIn("正常文章写作正好选入三份彼此不同的完整案例和三份完整钩子", skill)
        self.assertIn("不增加第四份", skill)
        self.assertIn("只有本地索引无法提供足够的完整参考", skill)
        self.assertIn("完整内容补足三份", skill)
        self.assertIn("临时参考不自动保存进私人库", skill)
        self.assertNotIn("活动案例与钩子正文中全文搜索", skill)
        self.assertIn("选入的六份参考来自六个独立文件", skill)
        self.assertIn("文件不同不等于参考不同", skill)
        self.assertIn("已选案例开头的节选或近似改写", skill)
        self.assertIn("任意两份参考实际重复同一种写法", skill)
        self.assertIn("不让同一内容同时充当两种参考", skill)
        content = _read("references/content-writing.md")
        self.assertIn("默认选入的三份案例和三份钩子都完整进入这份成文输入", skill)
        self.assertIn(
            "完整阅读当前材料、三份案例和三份钩子，把它们作为参考，直接写出用户要的内容。",
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

    def test_explicit_rewrite_reuses_confirmed_material_without_reusing_the_previous_draft(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("“重新写”“重写”“从头写”或等义表达", skill)
        self.assertIn("沿用已经确认的当前对象材料、表达边界和仍然适用的硬要求", skill)
        self.assertIn("不再联网", skill)
        self.assertIn("不把上一稿及其句子、结构或纠错过程放入成文输入", skill)
        self.assertIn("重新选择案例与钩子，从零独立成文", skill)
        self.assertIn("用户另有明确要求时，以当前要求为准", skill)

    def test_private_library_is_not_a_writing_gate(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("运行 `python scripts/private_library.py show`", skill)
        self.assertIn("私人库或参考不可用时直接继续写作", skill)

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
        self.assertIn("普通文章写作只允许读取文章案例索引", skill)
        self.assertIn("沿索引打开的完整文章案例", skill)
        self.assertIn("钩子索引和沿索引打开的完整钩子", skill)
        self.assertIn("不读取 `Home.md`、`10-Knowledge`、其它来源、项目、成果、作者声音、发布历史、内容策略或任何同主题笔记", skill)
        self.assertIn("即使项目名、机构名或产品名命中也不搜索", skill)
        self.assertIn("取得路径后只打开案例索引", private_library)
        self.assertIn("普通写作不从这里读取主题知识或启动知识补全", knowledge)
        self.assertIn("普通文章写作不从私人库读取作者声音或发布历史", skill)
        self.assertIn("不因为成品较长就读取私人库中的作者声音", article)
        self.assertIn("普通写作不自动进入本流程", memory)
        self.assertIn("用户明确要求读取私人库中的既有声音", memory)
        self.assertIn("不自动并入其它普通写作", memory)
        self.assertIn("用户给出的文字默认是来源材料，不是用户本人写的现稿", content)
        self.assertIn("只放用户在当前请求中直接提供的声音样稿", content)
        self.assertNotIn("文章和 Newsletter 默认读取", contract)
        self.assertNotIn("文章和 Newsletter 默认尝试", contract)
        self.assertNotIn("当前对象的事实和作者身份以本次材料为准", content)
        self.assertIn("第一人称经历、使用体验", skill)
        self.assertIn("第一人称经历、使用体验", content)

    def test_model_controls_creation_without_outline_or_review_route(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("由它决定角度、取舍、结构、语言、篇幅和结束位置", skill)
        self.assertIn("直接写出用户要的内容", content)
        self.assertIn("没有指定数量时只生成一个", content)
        self.assertIn("不自动评审、融合或润色", content)
        self.assertIn("提纲或写法清单", content)

    def test_source_and_finished_languages_are_separate(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("直接回复、文章和 Newsletter 默认使用中文", skill)

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

    def test_delivery_exposes_prepared_material_result_and_references(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("每次文章写作在同一次回复中固定展示四部分", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("只放用户要生成的成品", skill)
        self.assertIn("用户提供的内容说明进入写作准备材料", skill)
        self.assertIn("用户提供的事实、关系、判断、猜测、问题、宣发角度和内容主次属于材料", skill)
        self.assertIn("同一条消息里的对象事实、关系、观点、疑问、猜测、内容主次和角度说明进入材料", content)
        self.assertNotIn("写作要求能直接摘录用户原话时不改写", skill)
        self.assertNotIn("只放用户本次明确提出的写作要求", content)
        self.assertIn("用户没有提出限制时不擅自补上“不要搜索外部资料”等要求", skill)
        self.assertIn("文章写作前可以联网发现新的写作材料", _read("references/writing-material-preparation.md"))
        self.assertIn("多份案例之间和多份钩子之间分别用单独一行 `---` 分隔", skill)
        for heading in (
            "**写作要求**",
            "**写作准备材料**",
            "**结果**",
            "**本次创作参考**",
        ):
            self.assertEqual(1, skill.count(heading))
        self.assertIn("在独立代码块中完整展示本次实际选入的成文输入", skill)
        self.assertIn("而不是复制完整来源", skill)
        self.assertIn("不另建临时文件", skill)
        self.assertIn("每份结果分别放在独立代码块中", skill)
        self.assertIn("不重新摘要或改写已选内容", skill)
        self.assertIn("只列出真正进入本次成文输入的案例与钩子", skill)
        self.assertIn("不列候选阶段读过但没有送入成文模型的内容", skill)
        self.assertIn("本地参考使用可点击的绝对文件路径", skill)
        self.assertIn("临时公开参考使用原始网页链接", skill)
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
