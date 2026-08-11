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

    def test_normal_writing_uses_one_full_template(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        catalog = _read("references/writing-template-catalog.md")
        contract = "\n".join((skill, content, catalog))

        self.assertIn("先选一个完整模板，再填材料", skill)
        self.assertIn("每篇只选择一个完整模板", catalog)
        self.assertIn("禁止跨模板拼装", catalog)
        self.assertIn("模板 ID：<只允许一个", content)
        self.assertIn("完整模板：", content)
        self.assertIn("必填槽绑定", content)
        self.assertIn("停止点", content)
        self.assertIn("正文每句话只能完成一个已绑定槽位", content)
        self.assertIn("每句话必须对应一个槽位和当前材料", skill)
        self.assertIn("模型负责判断，模板负责限制", skill)
        self.assertNotIn("由它决定角度、取舍、结构、语言、篇幅和结束位置", contract)

    def test_old_case_and_hook_mixing_runtime_is_gone(self) -> None:
        runtime_paths = ["SKILL.md"] + [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in sorted((PROJECT_ROOT / "references").glob("*.md"))
        ]
        runtime = "\n".join(_read(path) for path in runtime_paths)
        for retired in (
            "【参考案例】",
            "【参考开头】",
            "默认选入三份",
            "三个不同的写作技巧分组",
            "沿索引打开的完整案例",
            "沿索引打开的完整钩子",
            "临时参考不自动保存",
            "重新选择案例与钩子",
            "完整案例和开头钩子实际参与表达",
            "选入的每份案例和钩子都应当真实参与写作",
            "每次写作在同一次回复中固定展示四部分",
            "本次创作参考",
        ):
            self.assertNotIn(retired, runtime)

        self.assertIn("案例与钩子只用于明确发起的模板维护", skill := _read("SKILL.md"))
        self.assertIn("普通写作没有运行私人库定位", skill)
        self.assertIn("普通写作不运行 `show`", _read("references/private-knowledge-library.md"))

    def test_writer_input_has_only_material_template_and_optional_voice(self) -> None:
        content = _read("references/content-writing.md")
        for heading in ("【用户要求】", "【材料】", "【写作模板】", "【作者声音】"):
            self.assertEqual(1, content.count(heading), heading)
        for retired in ("【参考案例】", "【参考开头】", "【完整案例】", "【完整钩子】"):
            self.assertNotIn(retired, content)
        self.assertIn("案例、钩子、专项说明、维护规则、检索过程、外部写作范例和与当前对象无关的旧稿不进入", content)
        self.assertIn("可选槽没有材料时直接跨过", content)
        self.assertIn("无法同时找到二者的句子删除", content)

    def test_catalog_has_complete_short_and_long_templates(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        matches = list(
            re.finditer(r"^### ([TA]\d{2}) [^\n]+$", catalog, flags=re.MULTILINE)
        )
        ids = [match.group(1) for match in matches]
        self.assertEqual([f"T{i:02d}" for i in range(1, 11)], ids[:10])
        self.assertEqual([f"A{i:02d}" for i in range(1, 10)], ids[10:])
        self.assertEqual(len(ids), len(set(ids)))

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(catalog)
            block = catalog[match.start():end]
            for field in ("适用条件", "必须事实", "钩子", "承接", "收尾"):
                self.assertIn(f"- {field}：", block, match.group(1))
            if match.group(1).startswith("T"):
                for field in ("禁用条件", "推进", "连接", "删除项"):
                    self.assertIn(f"- {field}：", block, match.group(1))
            else:
                for field in ("全文推进", "章节块", "章节连接", "禁止"):
                    self.assertIn(f"- {field}：", block, match.group(1))

            fields = re.findall(r"^- ([^：\n]+)：([^\n]+)$", block, flags=re.MULTILINE)
            self.assertTrue(fields, match.group(1))
            self.assertTrue(all(value.strip() for _, value in fields), match.group(1))
            required_line = next(value for name, value in fields if name == "必须事实")
            required_slots = re.findall(r"`([^`]+)`", required_line)
            self.assertGreaterEqual(len(required_slots), 4, match.group(1))
            self.assertEqual(len(required_slots), len(set(required_slots)), match.group(1))

    def test_template_selection_rejects_missing_facts(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((catalog, skill, content))
        self.assertIn("只保留满足“适用条件”且“必须事实”齐全的模板", catalog)
        self.assertIn("缺少必填槽就换模板", catalog)
        self.assertIn("不能把缺口交给模型发明", skill)
        self.assertIn("没有材料的可选槽省略", content)
        self.assertIn("第一人称、亲历、测试、时间、数字、引语、因果、比较和最高级", contract)
        self.assertIn("不补故事、痛点、情绪、使用体验、读者心理或价值判断", catalog)
        self.assertIn("没有任何同形态模板满足必填事实时不跨形态回退", catalog)
        self.assertIn("短帖或 Thread 只能选择 `T` 模板", skill)
        self.assertIn("文章或 Newsletter 只能选择 `A` 模板", skill)
        self.assertIn("没有任何同形态模板合格时不成文", skill)

    def test_user_structure_cannot_bypass_a_complete_template(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((catalog, skill, content))
        self.assertIn("同时规定了开头或进入方式、紧接开头怎样承接、正文推进顺序", catalog)
        self.assertIn("段落怎样连接或明确不加连接，以及停止位置", catalog)
        self.assertIn("长文还规定了章节内部写法", catalog)
        self.assertIn("局部约束时，仍从目录选择一个完整模板", catalog)
        self.assertIn("用户结构约束", content)
        self.assertIn("局部结构要求进入“用户结构约束”", content)
        self.assertIn("局部结构要求继续绑定到一个目录模板", skill)
        self.assertIn("`USER` 把用户给出的完整结构展开成同样字段", content)
        self.assertNotIn("用户已经给出结构时，把它视为本次唯一模板", contract)

    def test_sources_and_current_drafts_are_not_mistaken_for_style_examples(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((catalog, skill, content))
        self.assertIn("外部写作范例和与当前对象无关的旧稿", catalog)
        self.assertIn("本次任务的事实来源、用户明确交付的待改正文和来源消化对象", catalog)
        self.assertIn("本次任务的事实来源、待改正文和来源消化对象仍作为材料使用", skill)
        self.assertIn("用户明确交付的待改正文和来源消化对象仍作为材料使用", content)
        self.assertNotIn("外部文章和旧稿都不能代替", contract)

    def test_workflow_demo_is_a_first_class_route(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        block = catalog.split("### T02 工作流演示", 1)[1].split("### T03", 1)[0]
        self.assertIn("真实命令、自然语言输入、输入到输出的操作链", block)
        self.assertIn("你只要说/输入", block)
        self.assertIn("可见输出", block)
        self.assertIn("二至四个自动步骤", block)
        self.assertIn("凭空补用户痛点", block)
        self.assertIn("工具存在真实输入、处理和输出链时，优先工作流演示", catalog)

    def test_long_writing_constrains_each_section(self) -> None:
        catalog = _read("references/writing-template-catalog.md")
        content = _read("references/content-writing.md")
        article = _read("references/article-from-practice.md")
        contract = "\n".join((catalog, content, article))
        self.assertIn("每个章节只选择模板规定的一种章节块", catalog)
        self.assertIn("每个段落只承担", catalog)
        self.assertIn("小标题直接写本节对象", catalog)
        self.assertIn("每个章节必须使用所选 `A` 模板规定的章节块", content)
        self.assertIn("不能把多个模板当成多个章节拼接", article)
        self.assertIn("CTA 与逻辑结尾分开", article)
        self.assertIn("最多一个", article)

    def test_case_and_hook_libraries_are_maintenance_corpus_only(self) -> None:
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        maintenance = _read("references/writing-template-maintenance.md")
        home = _read("assets/private-library/Home.md")
        self.assertIn("只作为重新蒸馏和验证写作模板的原始语料", cases)
        self.assertIn("不直接进入普通成文输入", cases)
        self.assertIn("只作为重新蒸馏和验证写作模板的原始语料", hooks)
        self.assertIn("普通写作不读取钩子库", hooks)
        self.assertIn("普通写作不读取本文件", maintenance)
        self.assertIn("同一模板必须覆盖完整内容链", maintenance)
        self.assertIn("不能分别建立可任意组合的钩子库、推进库和结尾库", maintenance)
        self.assertIn("普通写作使用 Skill 源码中的完整写作模板", home)

    def test_material_preparation_preserves_source_boundaries(self) -> None:
        preparation = _read("references/writing-material-preparation.md")
        promotion = _read("references/project-promotion-materials.md")
        self.assertIn("准备后的材料是成文输入，不是正文提纲", preparation)
        self.assertIn("事实、关系、判断、猜测、问题、宣发角度和内容主次作为材料保留原话", preparation)
        self.assertIn("来源身份和原有确定程度", preparation)
        self.assertIn("不摘要、转述、重排、拼接或统一改写", preparation)
        self.assertIn("当前仍成立的开放问题和候选机制继续保留", promotion)
        self.assertIn("项目方发给作者邀请码", promotion)
        self.assertIn("只有能绑定到选中模板槽位的信息才进入正文", promotion)

    def test_writing_completes_in_one_turn_without_handoff(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, preparation, content))
        self.assertIn("材料准备、模板选择和成文在同一次回复中连续完成", skill)
        self.assertIn("材料准备与联网补充只执行一次", preparation)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertNotIn("正式交接文件", contract)
        self.assertNotIn("第一轮：交出正式准备文件", contract)

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
        self.assertIn("新增内容保持来源身份和原有确定程度", preparation)

    def test_plan_mode_supplements_before_interviewing(self) -> None:
        skill = _read("SKILL.md")
        plan = skill.split("### Plan 模式下先补充再访谈", 1)[1].split(
            "### 默认模式下准备并直接成文", 1
        )[0]
        self.assertIn("用户主动开启 Plan 模式视为明确的深度访谈请求", plan)
        self.assertIn("必须先完成本次需要的联网补充", plan)
        self.assertIn("再使用 `request_user_input` 开始访谈", plan)
        self.assertLess(
            plan.index("必须先完成本次需要的联网补充"),
            plan.index("再使用 `request_user_input` 开始访谈"),
        )
        self.assertIn("每轮只集中推进一个问题", plan)
        self.assertIn("不按固定问卷机械遍历", plan)

    def test_explicit_rewrite_reuses_facts_and_reselects_one_template(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("“重新写”“重写”“从头写”或等义表达", skill)
        self.assertIn("沿用已经确认的当前对象材料、表达边界和仍然适用的硬要求", skill)
        self.assertIn("不把上一稿及其句子、结构或纠错过程放入成文输入", skill)
        self.assertIn("重新选择一个合格模板，从零独立成文", skill)
        self.assertIn("只要求改字词、格式或等义措辞", skill)

    def test_default_delivery_returns_the_result_not_internal_inputs(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("默认只交付可直接使用的完整成品", skill)
        self.assertIn("不展示内部材料、模板选择、槽位绑定、检查过程", skill)
        self.assertIn("用户明确要求查看依据、写作过程或模板时", skill)
        self.assertIn("只把完整成品交回主流程", content)
        self.assertNotIn("**写作准备材料**", skill)
        self.assertNotIn("**本次创作参考**", skill)

    def test_author_voice_and_fact_checks_remain_opt_in_and_grounded(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")
        content = _read("references/content-writing.md")
        self.assertIn("普通写作不从私人库读取作者声音或发布历史", skill)
        self.assertIn("用户明确要求读取私人库中的既有声音", memory)
        self.assertIn("用户给出的文字默认是来源材料，不是用户本人写的现稿", content)
        self.assertIn("第一人称经历、使用体验", skill)
        self.assertIn("第一人称、亲历、测试、时间、数字、引语、因果、比较和最高级", content)

    def test_ai_flavor_audit_edits_only_confirmed_problems(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        audit = _read("references/content-audit.md")
        self.assertEqual(1, skill.count("references/natural-writing.md"))
        self.assertIn("用户要求检查或清理 AI 味时", skill)
        self.assertIn("没有内容作用的句子可以删除", natural)
        self.assertIn("删除后不补抽象总结", natural)
        self.assertIn("只修改已经确认的问题", audit)
        self.assertIn("不借审查重新设计全文", audit)

    def test_reference_admission_and_indexes_remain_maintainable(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("信息量与篇幅相称", cases)
        self.assertIn("可回查归档并重建索引", cases)
        self.assertIn("自然接入后文", hooks)
        self.assertIn("可回查归档并重建索引", hooks)
        self.assertIn("短帖和 Thread 都使用 `social`", skill)
        self.assertIn("独立短帖和 Thread 不再区分", cases)
        self.assertIn("不保存适用形式字段", hooks)
        for retired in ("短内容钩子索引.md", "Thread钩子索引.md", "文章钩子索引.md"):
            self.assertNotIn(retired, "\n".join((skill, cases, hooks)))

    def test_readmes_describe_template_runtime(self) -> None:
        self.assertIn("普通写作使用仓库内经过验证的完整写作模板", _read("README.md"))
        self.assertIn("validated full-piece templates", _read("README.en.md"))
        self.assertIn("検証済みの全文テンプレート", _read("README.ja.md"))

    def test_source_and_finished_languages_are_separate(self) -> None:
        self.assertIn("直接回复和可发布文字默认使用中文", _read("SKILL.md"))


if __name__ == "__main__":
    unittest.main()
