from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class PromotionalWritingContractTests(unittest.TestCase):
    def test_explicit_promotion_intent_has_a_distinct_route(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("只有明确提出宣发、推广、招募、预热、发布期传播", skill)
        self.assertIn("普通介绍、分享、推荐、产品帖", skill)
        self.assertNotIn("只有明确传播目的", skill)

    def test_plan_only_route_delivers_a_plan_and_stops_before_drafting(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("只要求方案，或提出宽泛推广目标却没有指定文字成品", skill)
        self.assertIn("交付可确认方案并停止", skill)
        self.assertIn("只交付宣发方案时不读取写作案例与钩子", skill)

    def test_specific_promotional_copy_enters_writing_without_an_intermediate_plan(self) -> None:
        skill = _read("SKILL.md")
        method = _read("references/promotional-content-writing.md")
        self.assertIn("已经要求起草具体宣发文字", skill)
        self.assertIn("直接带着同一份写作要求进入写作", skill)
        self.assertIn("上层已经选择起草具体文字", method)
        self.assertNotIn("默认先交付下面这份可确认方案", method)

    def test_virality_is_a_writing_effect_not_a_promotion_trigger(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("先选择成品身份，再判断是否叠加宣发要求", skill)
        self.assertIn("“病毒式传播”“更有传播力”“爆款”等效果要求", skill)
        self.assertIn("不触发宣发方案", skill)
        self.assertIn("这是效果目标，不是模板", content)

    def test_offer_owner_trigger_and_dates_are_locked(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        prewrite = _read("references/prewriting-research.md")

        for text in (skill, content, prewrite):
            self.assertIn("领取者", text)
            self.assertIn("触发动作", text)
        self.assertIn("有效时间", prewrite)
        self.assertIn("发布者因发布或邀请得到的返佣不能写成读者优惠", content)

    def test_public_copy_is_separate_from_internal_constraints(self) -> None:
        content = _read("references/content-writing.md")
        prewrite = _read("references/prewriting-research.md")
        self.assertIn("公开成文", content)
        self.assertIn("正文只使用公开成文材料造句", content)
        self.assertIn("内部信息不进入公开写作材料", prewrite)

    def test_single_output_is_not_split_by_multiple_angles(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn("多个卖点和角度只是选材，不自动拆成多篇", skill)
        self.assertIn("单篇只生成一个完整正文", content)

    def test_promotion_reference_selection_keeps_role_and_recipient_boundaries(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        self.assertIn("`index_roles` 包含 `promotion`", skill)
        self.assertIn("`index_roles` 包含 `promotion`", cases)
        self.assertIn("`benefit_recipients`", cases)

    def test_evidence_and_real_entry_reach_copy(self) -> None:
        method = _read("references/promotional-content-writing.md")
        content = _read("references/content-writing.md")
        prewrite = _read("references/prewriting-research.md")
        self.assertIn("能把这项变化写具体", prewrite)
        self.assertIn("有效时间和真实入口", prewrite)
        self.assertIn("草稿完成后，再核查正文实际作出的主要承诺", method)
        self.assertIn("入口、利益、时间和资格一致", content)

    def test_promotional_copy_uses_shared_creative_flow(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("多个完整案例", skill)
        self.assertIn("多个钩子示例", skill)
        self.assertIn("先交付正文或大纲", skill)
        self.assertNotIn("scripts/writing_delivery.py", skill)

    def test_archived_compiler_is_not_an_active_route(self) -> None:
        active = "\n".join(
            [_read("SKILL.md")]
            + [path.read_text(encoding="utf-8") for path in (PROJECT_ROOT / "references").glob("*.md")]
        )
        self.assertNotIn("writing-execution-record", active)
        self.assertNotIn("scripts/writing_delivery.py", active)
        self.assertTrue(
            (PROJECT_ROOT / "archive" / "writing-compiler-retired-2026-08-01" / "writing_delivery.py").exists()
        )


if __name__ == "__main__":
    unittest.main()
