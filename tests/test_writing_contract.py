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
                _read("references/prewriting-research.md"),
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
        self.assertIn("默认搜索外部资料", contract)
        self.assertIn("删除式净化", contract)
        self.assertIn("正常写作读取有帮助的参考写作案例和参考开头钩子", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("材料准备和成文在同一次回复中连续完成", skill)
        self.assertIn("材料准备、直接成文和最终交付在同一次处理中连续完成", contract)
        self.assertIn("材料发现与净化只执行一次", contract)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertNotIn("正式交接文件", contract)
        self.assertNotIn("第一轮：交出正式准备文件", contract)
        self.assertNotIn("第二轮：只读交接文件成文", contract)

    def test_search_is_default_except_explicit_local_edits(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        contract = "\n".join((skill, prewriting))
        self.assertIn("新写、扩写、改写和实质重组默认搜索外部资料", contract)
        self.assertIn("明确禁止联网", contract)
        self.assertIn("只使用给定材料", contract)
        self.assertIn("只改错字、格式和等义措辞", contract)
        self.assertIn("补充现有内容或增强传播力", prewriting)
        self.assertIn("搜索到的内容与现有材料重复时不加入", prewriting)
        self.assertNotIn("搜索和事实核对只补充、修正材料", skill)
        self.assertNotIn("材料已经足以", prewriting)
        self.assertNotIn("内容缺口", prewriting)

    def test_material_purification_only_deletes_and_enters_writing_inputs(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, prewriting, content))
        self.assertIn("净化只通过删除完成", prewriting)
        self.assertIn("净化后的材料是成文输入，不是备查资料包", prewriting)
        self.assertIn("以用户明确要求为边界", prewriting)
        self.assertIn("删除无关、重复、误导创作的内容", prewriting)
        self.assertIn("用户把事实列入材料，不等于要求正文逐项覆盖", prewriting)
        self.assertIn("同一变化、关系或结论出现多次时", prewriting)
        self.assertIn("只保留一处最直接的来源原文", prewriting)
        self.assertIn("留下足以准确成文的最少内容，其余删除", prewriting)
        self.assertIn("不因为提供了另一份佐证就进入写作输入", prewriting)
        self.assertIn("不在这里预选正文角度、结构或句子", prewriting)
        self.assertIn("不因为内容准确就自动保留", prewriting)
        self.assertIn("来源原文、原有顺序、来源边界和必要上下文", contract)
        self.assertIn("写作输入只放实际写作内容", prewriting)
        self.assertIn("不写来源名称、原始文件名、路径或链接", prewriting)
        self.assertIn("不摘要、转述、重排、拼接或统一改写", prewriting)
        self.assertIn("## 写作输入", content)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertIn("材料发现与净化只执行一次", prewriting)
        self.assertIn("【本次写作要求】", content)
        self.assertIn("【写作规则】", content)
        self.assertNotIn("【通用写作注意】", content)
        self.assertIn("【净化后材料】", content)
        self.assertIn("【参考写作案例】", content)
        self.assertIn("【参考开头钩子】", content)
        self.assertNotIn("【完整案例】", content)
        self.assertNotIn("【完整钩子】", content)
        self.assertIn("【其它实际写作输入】", content)
        self.assertIn(
            "净化后原文，不写来源名称、原始文件名、路径或链接", content
        )
        self.assertIn("写作案例正文，不带案例库生成的标题", content)
        self.assertIn("开头钩子正文，不带钩子库生成的标题", content)
        self.assertIn("“原文全文”等栏目名", content)
        self.assertIn("“钩子原文”等栏目名", content)
        self.assertIn("只保留实际参考正文", content)
        self.assertIn(
            "写作规则只从 `references/content-writing.md` 原样取得", skill
        )
        self.assertNotIn("写作简报", content)

    def test_general_writing_guidance_has_one_runtime_owner(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertEqual(1, content.count("【写作规则】"))
        self.assertNotIn("【通用写作注意】", skill)
        self.assertIn("这里是写作规则的唯一真源", content)
        self.assertIn("按用户强调的内容分清主次", content)
        self.assertIn("正文只放核心关系和必要事实", content)
        self.assertIn("开头从具体变化、冲突、结果或真实情绪中给出继续阅读的理由", content)
        self.assertIn("用普通中文直接写清事实和关系", content)
        self.assertIn("每句话增加新事实、新关系、必要判断或衔接", content)
        self.assertIn("删掉没有影响的句子不要写", content)
        self.assertIn("普通名词不加装饰性引号", content)
        self.assertIn("冒号和破折号只在真实句法需要时使用", content)
        self.assertIn("不反复使用“不是……而是……”", content)
        self.assertIn("篇幅跟随真实信息量", content)
        self.assertIn("核心关系和必要事实说完立即停止", content)
        self.assertIn("不强补总结、金句、问题或结尾", content)
        self.assertIn("案例和钩子只帮助写法", content)
        self.assertIn("不增加正文需要覆盖的信息，也不延长篇幅", content)
        self.assertIn("中文有清楚说法时不用外文", content)
        self.assertNotIn("引号、冒号和破折号", content)

        runtime = "\n".join(
            _read(path)
            for path in (
                "SKILL.md",
                "references/content-writing.md",
                "references/natural-writing.md",
                "references/content-audit.md",
                "references/article-from-practice.md",
                "references/github-project-list.md",
                "references/github-project-short-content.md",
                "references/publication-requirements.md",
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
        self.assertIn("读取有帮助的参考写作案例和参考开头钩子", skill)
        self.assertIn("短帖和 Thread 从社交内容案例索引", skill)
        self.assertIn("所有成品从同一份钩子索引", skill)
        self.assertIn("参考写作案例和参考开头钩子必须来自不同文件", skill)
        self.assertIn("完整原文也不能相同", skill)
        self.assertIn("不让同一内容同时充当两种参考", skill)
        self.assertIn("用户要求维护完整案例或钩子时", skill)
        self.assertNotIn("## 普通写作读取", cases)
        self.assertNotIn("## 普通写作读取", hooks)

    def test_private_library_is_not_a_writing_gate(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("运行 `python scripts/private_library.py show`", skill)
        self.assertIn("私人库或参考不可用时直接继续写作", skill)

    def test_author_voice_defaults_do_not_inherit_source_identity(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, memory, content))
        self.assertIn("用户给出的文字默认是来源材料，不是用户本人写的现稿", content)
        self.assertIn("短内容默认不读取作者声音", contract)
        self.assertIn("文章和 Newsletter 默认", contract)
        self.assertIn("没有可用材料时直接继续", memory)
        self.assertIn("不提供当前对象的事实、人物、经历、立场或作者身份", content)

    def test_model_controls_creation_and_length_follows_information(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, content))
        self.assertIn("由它决定角度、取舍、结构、语言、篇幅和结束位置", skill)
        self.assertIn("篇幅跟随真实信息量", contract)
        self.assertIn("核心关系和必要事实说完立即停止", contract)
        self.assertIn("直接写成可使用的成品", content)
        self.assertIn("没有指定数量时只生成一个", content)
        self.assertIn("不自动评审、融合或润色", content)

    def test_source_and_finished_languages_are_separate(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("直接回复和可发布文字默认使用中文", skill)
        self.assertIn("中文有清楚说法时不用外文", content)

    def test_delivery_exposes_prepared_material_result_and_references(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("每次写作在同一次回复中固定展示四部分", skill)
        self.assertIn("在同一次回复中直接成文", skill)
        self.assertIn("只放用户本次明确提出的要求", skill)
        self.assertIn("能直接摘录时不改写，也不加入系统推断", skill)
        self.assertIn("不加入材料数量、预选重点、身份说明、篇幅判断或覆盖范围", skill)
        for heading in (
            "**写作要求**",
            "**写作准备材料**",
            "**结果**",
            "**本次创作参考**",
        ):
            self.assertEqual(1, skill.count(heading))
        self.assertIn("在独立代码块中完整展示本次实际使用的写作输入", skill)
        self.assertIn("不另建临时文件", skill)
        self.assertIn("每个完整成品分别放在独立代码块中", skill)
        self.assertIn("不重新摘要或改写内容", skill)
        self.assertIn("只列出本次实际读取的案例与钩子名称", skill)
        self.assertIn("不显示文件名、路径、原始材料来源", skill)
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
        self.assertNotIn("活动发布型短内容使用同一条内容关系", publication)
        self.assertNotIn("最后落在参与结果", publication)
        self.assertIn("它只补充事实", publication)

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

    def test_reference_indexes_do_not_split_threads_from_short_posts(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
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
