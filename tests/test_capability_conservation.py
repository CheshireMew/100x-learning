from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8-sig")


class CapabilityConservationTests(unittest.TestCase):
    def test_material_analysis_keeps_previous_high_value_behaviors(self) -> None:
        material = _read("references/material-analysis.md")
        subtitles = _read("scripts/normalize_subtitles.py")

        for marker in (
            "标题用于定位，正文是内容真源",
            "多条主线",
            "计算片段总时长并保持在用户预算内",
            "讲者主张",
            "本金、投入、回报率、期限、费用、税务或取用假设",
        ):
            self.assertIn(marker, material)
        self.assertIn("without inventing timing", subtitles)

    def test_research_keeps_source_roles_and_evidence_boundaries(self) -> None:
        research = _read("references/research-led-learning.md")

        for marker in (
            "来源没有固定高低顺序",
            "高质量博客常是更好的解释源或案例源",
            "对准备采用的关键主张分别检查",
            "会改变概念原貌、文章核心结论、数据可信度",
            "资料不足时保留未知",
        ):
            self.assertIn(marker, research)

    def test_concept_and_learning_paths_remain_low_pressure(self) -> None:
        concept = _read("references/concept-deconstruction.md")
        learning = _read("references/learning-process-and-method-selection.md")

        self.assertIn("现实问题或来源故事 → 核心含义 → 机制链 → 具体场景", concept)
        self.assertIn("用户选择闭卷形式时再使用闭卷", learning)
        self.assertIn("低压力", learning)

    def test_practice_and_article_keep_user_authority_and_truth_boundaries(self) -> None:
        practice = _read("references/practice-led-learning.md")
        article = _read("references/article-from-practice.md")

        self.assertIn("模拟用于降低风险，结果明确标记为模拟结果", practice)
        self.assertIn("用共同操作、演示和选择代替闭卷回答", practice)
        self.assertIn("具体个人经历、使用时长、测试结果和感受只有在当前作者材料明确提供时进入草稿", article)
        self.assertIn("案例中的第一人称和经历不能转移给当前作者", article)
        self.assertIn("用户同时要求大纲和全文时", article)
        self.assertIn("每一部分说明", article)

    def test_voice_migration_keeps_previous_voice_contract(self) -> None:
        memory = _read("references/personal-writing-memory.md")
        home = _read("assets/private-library/Home.md")

        self.assertIn("当前要求可以改变本次写法，但不会自动改写长期声音", memory)
        self.assertIn("当前有效正文", memory)
        self.assertIn("长期声音真源", memory)
        self.assertIn("voice_eligible: true", memory)
        self.assertIn("内容案例库", memory)
        self.assertIn("不能证明用户身份、经历、立场或个人声音", memory)
        self.assertIn("发布历史、声音资格和内容案例承担不同用途", home)

    def test_existing_result_routes_remain_reachable_after_promotion_branch(self) -> None:
        skill = _read("SKILL.md")

        for marker in (
            "references/learning-process-and-method-selection.md",
            "references/material-analysis.md",
            "references/shareable-content-selection.md",
            "references/research-led-learning.md",
            "references/concept-deconstruction.md",
            "references/practice-led-learning.md",
            "references/content-audit.md",
            "references/private-knowledge-library.md",
            "references/knowledge-base-workflow.md",
            "单个 GitHub 项目介绍",
            "个人写作记忆",
            "内容案例",
        ):
            self.assertIn(marker, skill)

    def test_adjacent_boundaries_and_requested_output_remain_intact(self) -> None:
        skill = _read("SKILL.md")
        article = _read("references/article-from-practice.md")

        for marker in ("翻译", "普通计划", "广告投放", "销售页与落地页"):
            self.assertIn(marker, skill)
        self.assertIn("上层已经确定写作动作、精确成品形态、表达任务", article)
        self.assertIn("达到用户要求且由上层选定的大纲、局部、草稿或终稿层级后停止", article)


if __name__ == "__main__":
    unittest.main()
