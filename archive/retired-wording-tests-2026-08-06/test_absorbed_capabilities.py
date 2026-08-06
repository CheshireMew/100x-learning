from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AbsorbedCapabilityContractTests(unittest.TestCase):
    def test_new_capabilities_are_directly_routed_from_skill(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for reference in (
            "references/knowledge-base-health.md",
            "references/durable-learning-projects.md",
            "references/research-context-reuse.md",
            "references/source-ingestion.md",
        ):
            self.assertIn(reference, skill)
        self.assertIn("用户确认修复后", skill)
        self.assertIn("私人库已配置时", skill)

    def test_health_check_is_read_only_until_repair_is_authorized(self) -> None:
        reference = (
            PROJECT_ROOT / "references" / "knowledge-base-health.md"
        ).read_text(encoding="utf-8")
        self.assertIn("默认只读", reference)
        self.assertIn("修复需要单独授权", reference)
        self.assertIn("实际文档", reference)
        self.assertIn("真实消费任务", reference)

    def test_source_ingestion_uses_outcome_driven_video_depth_and_normalized_social_semantics(self) -> None:
        reference = (
            PROJECT_ROOT / "references" / "source-ingestion.md"
        ).read_text(encoding="utf-8")
        self.assertIn("转写层", reference)
        self.assertIn("转写加关键画面层", reference)
        self.assertIn("完整多模态层", reference)
        self.assertIn("不要按固定秒数机械抽帧", reference)
        self.assertIn("Thread 顺序或引用上下文", reference)
        self.assertIn("未取得", reference)
        self.assertNotIn("Gemini", reference)
        self.assertNotIn("MLX", reference)

    def test_research_reuse_and_durable_state_do_not_create_parallel_truths(self) -> None:
        reuse = (
            PROJECT_ROOT / "references" / "research-context-reuse.md"
        ).read_text(encoding="utf-8")
        durable = (
            PROJECT_ROOT / "references" / "durable-learning-projects.md"
        ).read_text(encoding="utf-8")
        self.assertIn("直接继续当前研究", reuse)
        self.assertIn("默认只读", reuse)
        self.assertIn("外部研究只补足缺口", reuse)
        self.assertIn("唯一机器真源", durable)
        self.assertIn("来源变化", durable)
        self.assertIn("不能写进 Skill 目录", durable)


if __name__ == "__main__":
    unittest.main()
