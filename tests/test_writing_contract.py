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

    def test_output_identity_is_selected_before_publication_facts(self) -> None:
        skill = _read("SKILL.md")

        identity = skill.index("### 2. 选择写作动作和成品身份")
        publication = skill.index("### 3. 按需叠加发布事实")
        self.assertLess(identity, publication)
        self.assertIn("单个 GitHub 项目介绍", skill)
        self.assertIn("普通写作流程完成", skill)

    def test_multiple_cases_and_hooks_share_the_creative_context(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        content = _read("references/content-writing.md")

        self.assertIn("多个完整案例", skill)
        self.assertIn("多个独立钩子原文", skill)
        self.assertIn("多份方向不同且真正相关的完整案例", skill)
        self.assertIn("多份钩子和多份完整案例", hooks)
        self.assertIn("它不管理钩子", cases)
        self.assertIn("多个相关完整案例与多个独立钩子的原文", content)

    def test_hooks_are_selected_by_technique_across_output_formats(self) -> None:
        skill = _read("SKILL.md")
        hooks = _read("references/hook-library.md")

        self.assertIn("按开头手法跨成品形态定位", skill)
        self.assertIn("先按开头手法、再按原始成品形态", hooks)
        self.assertIn("不能把 `writing_format` 当成阅读资格", hooks)

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

    def test_user_selected_speaking_situation_is_a_writing_requirement(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("说话身份、叙事关系、产品揭示位置", content)
        self.assertIn("先建立一种期待再反转", skill)
        self.assertIn("先建立一种期待再揭示真实制作方式", natural)
        self.assertIn("保持用户已经指定的说话身份", content)

    def test_first_person_presentation_is_distinct_from_borrowed_experience(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("不等于从案例借来一段个人经历", skill)
        self.assertIn("案例中的个人经历仍属于原作者", content)
        self.assertIn("案例中的经历不能迁移给当前作者", natural)

    def test_visible_actions_keep_familiar_names_without_invented_taxonomy(self) -> None:
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("读者已有熟悉名称的动作使用普通说法", content)
        self.assertIn("不为了显得像某个行业而临时发明", content)
        self.assertIn("读者熟悉的名字时直接使用", natural)
        self.assertIn("不把普通交互改写成临时分类", natural)

    def test_unfamiliar_object_is_defined_before_workflow_details(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        for text in (skill, content, natural):
            self.assertIn("第一次遇到", text)
            self.assertIn("它是什么", text)
            self.assertIn("直接能做什么", text)
        self.assertIn("再展开组件、工作流、功能和例子", content)
        self.assertIn("直接从组件、功能或工作流开始", natural)

    def test_delivery_lists_only_actually_read_creative_references_by_default(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("除非用户明确只要正文", skill)
        self.assertIn("本次创作参考（实际阅读）", skill)
        self.assertIn("只列真正阅读全文的完整案例和钩子", skill)
        self.assertIn("可点击的绝对文件路径", skill)
        self.assertIn("本次实际阅读的案例与钩子文件", natural)

    def test_material_based_writing_remains_creative(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        prewrite = _read("references/prewriting-research.md")

        self.assertIn("不把它解释成忠实摘要合同", skill)
        self.assertIn("不联网只限制信息来源", skill)
        self.assertIn("材料提供内容，不表示沿用材料的措辞、顺序和结论", content)
        self.assertIn("模型看到完整材料后自行决定讲什么", prewrite)

    def test_action_entry_has_one_reader_goal_based_owner(self) -> None:
        content = _read("references/content-writing.md")
        publication = _read("references/publication-requirements.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("根据已经建立的读者下一步", content)
        self.assertIn("只保留一个最有用的主要入口", content)
        self.assertIn("事实来源或素材页被当成了", natural)
        self.assertIn("行动入口由正文已经建立的读者下一步决定", publication)

    def test_language_defaults_to_chinese_once(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("没有指定时，直接回复和可发布文字默认使用中文", skill)

    def test_voice_and_novelty_remain_separate(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")

        self.assertIn("内容查重只在用户要求查重", skill)
        self.assertIn("voice", skill)
        self.assertIn("novelty", skill)
        self.assertIn("两条检索结果不能互相代用", memory)


if __name__ == "__main__":
    unittest.main()
