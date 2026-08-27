from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TranscriptEditingContractTests(unittest.TestCase):
    def test_transcripts_default_to_one_clean_source_document(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("完整字幕或自动转写稿优先于其中附带的视频或社交链接", skill)
        self.assertIn("20-Sources/Transcripts", skill)
        self.assertIn("默认整理、校正并写入一份完整来源文档", skill)
        self.assertIn("不等同于生成知识笔记", skill)
        self.assertNotIn("再读取 `references/material-analysis.md` 讲清材料", skill)
        self.assertNotIn("需要规范化时，使用 `scripts/normalize_subtitles.py`", skill)

    def test_editing_contract_cleans_without_extra_research_or_notes(self) -> None:
        contract = (PROJECT_ROOT / "references" / "transcript-editing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("不摘要、不压缩、不改写成新的表达", contract)
        self.assertIn("明确删除广告、赞助口播", contract)
        self.assertIn("删减说明", contract)
        self.assertIn("删减说明默认同样不保留时间戳", contract)
        self.assertIn("拿不准是否相关时保留", contract)
        self.assertIn("原转录 → 校正后", contract)
        self.assertIn("不主动查询、补齐或验证", contract)
        self.assertIn("默认不为纠错搜索原视频页面", contract)
        self.assertIn("时间戳只用于恢复字幕顺序", contract)
        self.assertIn("不进入默认成品正文", contract)
        self.assertIn("20-Sources/Transcripts", contract)
        self.assertIn("只检查目标目录中是否已经存在同一来源或同名文档", contract)
        self.assertIn("不运行全库健康检查", contract)
        self.assertIn("材料讲解、摘要、研究和知识笔记都不是字幕整稿的默认产物", contract)
        self.assertNotIn("10-Knowledge", contract)


if __name__ == "__main__":
    unittest.main()
