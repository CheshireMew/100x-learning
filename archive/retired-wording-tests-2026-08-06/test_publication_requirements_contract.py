from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class PublicationRequirementsContractTests(unittest.TestCase):
    def test_promotion_intent_keeps_the_normal_writing_route(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")

        identity = skill.index("### 2. 选择写作动作和成品身份")
        publication = skill.index("### 3. 按需叠加发布事实")
        self.assertLess(identity, publication)
        self.assertIn("继续使用已经选定的成品身份", skill)
        self.assertIn("不选择另一种写作路线", skill)
        self.assertIn("不提供另一套语气和结构", content)

    def test_publication_facts_are_loaded_only_when_the_copy_needs_them(self) -> None:
        skill = _read("SKILL.md")
        method = _read("references/publication-requirements.md")

        for marker in ("折扣", "奖励", "抽奖", "有效时间", "行动入口", "披露"):
            self.assertIn(marker, skill)
            self.assertIn(marker, method)
        self.assertIn("普通介绍、分享、推荐和产品帖没有这些事实时不读取", method)

    def test_offer_owner_trigger_dates_and_entry_remain_distinct(self) -> None:
        method = _read("references/publication-requirements.md")

        for marker in ("实际获得者", "生效或领取动作", "开始与结束时间", "真实入口"):
            self.assertIn(marker, method)
        self.assertIn("发布者或合作方获得的返佣不能写成读者折扣", method)
        self.assertIn("相对时长没有起算锚点", method)

    def test_publication_facts_do_not_own_voice_structure_or_reveal(self) -> None:
        method = _read("references/publication-requirements.md")
        content = _read("references/content-writing.md")

        self.assertIn("不选择成品形态、写作动作、开头、语气、叙事身份、结构和产品揭示位置", method)
        self.assertIn("发布事实不提供默认表达风格", method)
        self.assertIn("先让作品体验成立", content)
        self.assertIn("自然揭示产品", content)

    def test_internal_cooperation_language_enters_copy_only_for_required_disclosure(self) -> None:
        method = _read("references/publication-requirements.md")
        audit = _read("references/content-audit.md")

        self.assertIn("没有披露要求时", method)
        self.assertIn("不把合作关系、内容制作过程", method)
        self.assertIn("没有明确披露要求时进入公开正文", audit)

    def test_missing_dedicated_entry_is_not_replaced_by_a_homepage(self) -> None:
        method = _read("references/publication-requirements.md")
        content = _read("references/content-writing.md")

        self.assertIn("保留一个清楚的待替换位置", method)
        self.assertIn("不能用只能介绍产品的普通页面冒充", method)
        self.assertIn("不能用普通产品首页或事实来源冒充", content)
        self.assertIn("只保留一个最有用的主要入口", content)

    def test_plan_is_an_output_level_not_a_promotional_writing_branch(self) -> None:
        skill = _read("SKILL.md")
        method = _read("references/publication-requirements.md")

        self.assertIn("把方案作为本次成品", skill)
        self.assertIn("交付方案后停止", skill)
        self.assertIn("不生成另一套宣发模板", method)

    def test_general_cases_remain_available_for_copy_with_publication_facts(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")

        self.assertIn("仍可读取普通案例", skill)
        self.assertIn("不构成阅读门槛", skill)
        self.assertIn("不能因此排除普通案例", cases)
        self.assertIn("不能把这些索引字段交给写作者", cases)

    def test_retired_promotional_reference_is_not_active(self) -> None:
        skill = _read("SKILL.md")
        active = PROJECT_ROOT / "references" / "promotional-content-writing.md"
        archived = PROJECT_ROOT / "archive" / "promotional-content-writing-retired-2026-08-04.md"

        self.assertNotIn("references/promotional-content-writing.md", skill)
        self.assertFalse(active.exists())
        self.assertTrue(archived.exists())


if __name__ == "__main__":
    unittest.main()
