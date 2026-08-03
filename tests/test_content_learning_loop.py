from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.private_library import initialize_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ContentLearningLoopTests(unittest.TestCase):
    def test_skill_routes_strategy_topics_and_published_review_directly(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("references/content-strategy-and-topic-selection.md", skill)
        self.assertIn("references/published-content-review.md", skill)
        self.assertIn("references/practice-led-learning.md", skill)
        self.assertIn("当前请求始终覆盖长期内容策略", skill)
        self.assertIn("只有明确的持续系列才维护项目状态", skill)

    def test_strategy_and_topic_contract_keeps_distinct_sources_of_truth(self) -> None:
        reference = (
            PROJECT_ROOT
            / "references"
            / "content-strategy-and-topic-selection.md"
        ).read_text(encoding="utf-8")

        self.assertIn("60-Systems/Writing/content-strategy.md", reference)
        self.assertIn("60-Systems/Writing/style-guide/voice.md", reference)
        self.assertIn("当前请求是最高优先级", reference)
        self.assertIn("只问“这次写什么”", reference)
        self.assertIn("稳定 `topic_id`", reference)
        self.assertIn("不要给选题打分", reference)
        self.assertIn("不要求每批凑齐", reference)
        self.assertIn("只吸收可迁移机制", reference)

    def test_published_review_contract_uses_real_evidence_and_human_gate(self) -> None:
        reference = (
            PROJECT_ROOT / "references" / "published-content-review.md"
        ).read_text(encoding="utf-8")

        self.assertIn("唯一成品路径或规范链接", reference)
        self.assertIn("统计时间和观察窗口", reference)
        self.assertIn("观察到的结果", reference)
        self.assertIn("候选解释", reference)
        self.assertIn("其它可能解释", reference)
        self.assertIn("下一次验证", reference)
        self.assertIn("一次发布结果默认只是待验证假设", reference)
        self.assertIn("用户明确确认", reference)
        self.assertIn("发布表现不直接更新", reference)
        self.assertIn("不创建第二份指标数据库", reference)

    def test_initialization_instantiates_templates_without_overwriting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "library"
            config = Path(temporary) / "config" / "config.json"
            layout, _, created = initialize_library(root, config)

            self.assertTrue(created)
            self.assertTrue(layout.content_strategy.is_file())
            self.assertTrue(layout.topic_portfolio_template.is_file())
            self.assertTrue(layout.published_review_template.is_file())
            self.assertIn(
                "status: unconfigured",
                layout.content_strategy.read_text(encoding="utf-8"),
            )

            marker = "\n用户确认的长期策略。\n"
            layout.content_strategy.write_text(
                layout.content_strategy.read_text(encoding="utf-8") + marker,
                encoding="utf-8",
            )
            layout.topic_portfolio_template.write_text(
                "用户自己的选题模板。\n",
                encoding="utf-8",
            )

            repeated, _, created_again = initialize_library(root, config)

            self.assertFalse(created_again)
            self.assertIn(
                marker.strip(),
                repeated.content_strategy.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "用户自己的选题模板。\n",
                repeated.topic_portfolio_template.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
