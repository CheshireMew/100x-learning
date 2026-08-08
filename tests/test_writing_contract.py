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

    def test_writing_has_one_direct_chain_without_old_routes(self) -> None:
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
        self.assertIn("默认搜索外部资料", skill)
        self.assertIn("删除式净化", skill)
        self.assertIn("读取当前可用的完整案例和钩子原文", skill)
        self.assertIn("再把同一份准备材料原样放一次", _read("references/content-writing.md"))
        self.assertIn("使用 `references/content-writing.md` 直接写成正文", skill)

    def test_search_is_default_except_explicit_local_edits(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        contract = "\n".join((skill, prewriting))
        self.assertIn("新写、扩写、改写和实质重组默认搜索外部资料", contract)
        self.assertIn("明确禁止联网", contract)
        self.assertIn("只使用给定材料", contract)
        self.assertIn("只改错字、格式和等义措辞", contract)
        self.assertNotIn("材料已经足以", prewriting)
        self.assertNotIn("内容缺口", prewriting)

    def test_material_purification_only_deletes_and_is_repeated_verbatim(self) -> None:
        skill = _read("SKILL.md")
        prewriting = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, prewriting, content))
        self.assertIn("净化只删除", prewriting)
        self.assertIn("来源原文、原有顺序、来源边界和必要上下文", contract)
        self.assertIn("不摘要、转述、重排、拼接、统一改写", prewriting)
        self.assertIn("唯一一份“写作准备材料”", contract)
        self.assertIn("两次内容必须完全相同", contract)
        self.assertIn("最终回答只展示一次完整版本", prewriting)
        self.assertIn("【本次写作要求】", content)
        self.assertIn("【通用写作注意】", content)
        self.assertIn("【净化后材料】", content)
        self.assertIn("通用写作注意只从该文件原样取得", skill)
        self.assertIn("不维护另一份同义要求", content)
        self.assertNotIn("写作简报", content)

    def test_general_writing_guidance_has_one_runtime_owner(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertEqual(1, content.count("【通用写作注意】"))
        self.assertNotIn("【通用写作注意】", skill)
        self.assertIn("这里是通用写作要求的唯一真源", content)
        self.assertIn("陌生对象第一次出现时", content)
        self.assertIn("篇幅跟随真实信息量，内容说完即停", content)

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
        for priming_example in (
            "以为……其实……",
            "不是……而是……",
            "不只是……而是……",
        ):
            self.assertNotIn(priming_example, runtime)

    def test_reference_libraries_are_optional_full_inputs(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("索引只帮助找到全文，不能代替全文", cases)
        self.assertIn("索引只帮助找到全文，不能代替全文", hooks)
        self.assertIn("不运行 `validate`", cases)
        self.assertIn("不运行 `validate`", hooks)
        self.assertIn("配置、索引或案例不可用时继续写作", cases)
        self.assertIn("配置、索引或钩子不可用时继续写作", hooks)
        self.assertIn("短内容浏览可用的短内容案例", cases)
        self.assertIn("文章和 Newsletter 浏览可用的文章案例", cases)
        self.assertIn("模型自行决定读哪些、读多少和怎样综合", skill)
        self.assertIn("读哪些、读多少和怎样综合", skill)

    def test_private_library_is_not_a_writing_gate(self) -> None:
        skill = _read("SKILL.md")
        private_library = _read("references/private-knowledge-library.md")
        self.assertIn("普通写作不运行私人库、案例库或钩子库的健康检查", skill)
        self.assertIn("位置、索引或参考不可用时直接根据现有材料继续", skill)
        self.assertIn("普通写作只在准备读取现有案例", private_library)
        self.assertIn("不运行 `validate`", private_library)
        self.assertIn("继续写作", private_library)

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
        self.assertIn("内容说完即停", contract)
        self.assertIn("不先分类、制定结构、分析案例或规划结尾", content)
        self.assertIn("必要的情绪、节奏、幽默和留白可以保留", content)

    def test_source_and_finished_languages_are_separate(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("直接回复和可发布文字默认使用中文", skill)
        self.assertIn("中文已有清楚说法时使用中文", content)
        self.assertIn("识别、搜索或操作需要时保留外文", content)

    def test_delivery_exposes_prepared_material_result_and_references(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("每次写作固定展示四部分", skill)
        for heading in (
            "**写作要求**",
            "**写作准备材料**",
            "**结果**",
            "**本次创作参考**",
        ):
            self.assertEqual(1, skill.count(heading))
        self.assertIn("在独立代码块中完整展示", skill)
        self.assertIn("与正式写作前重复使用的版本完全相同", skill)
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


if __name__ == "__main__":
    unittest.main()
