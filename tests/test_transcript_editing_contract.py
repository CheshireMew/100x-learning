from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TranscriptEditingContractTests(unittest.TestCase):
    def test_transcripts_are_edited_before_material_explanation(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

        editing_position = skill.index("references/transcript-editing.md")
        analysis_position = skill.index("再读取 `references/material-analysis.md`", editing_position)

        self.assertLess(editing_position, analysis_position)
        self.assertIn("这是字幕输入的默认完整结果", skill)
        self.assertIn("写入私人知识库", skill)
        self.assertNotIn("需要规范化时，使用 `scripts/normalize_subtitles.py`", skill)

    def test_editing_contract_preserves_wording_and_real_timestamps(self) -> None:
        contract = (PROJECT_ROOT / "references" / "transcript-editing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("不摘要、不压缩、不改写成新的表达", contract)
        self.assertIn("明确删除广告、赞助口播", contract)
        self.assertIn("删减说明", contract)
        self.assertIn("拿不准是否相关时保留", contract)
        self.assertIn("原转录 → 校正后", contract)
        self.assertIn("只显示本段首条字幕的开始时间", contract)
        self.assertIn("不得用下一条字幕", contract)
        self.assertIn("整理后的字幕", contract)
        self.assertIn("材料讲解", contract)
        self.assertIn("20-Sources/Transcripts", contract)
        self.assertIn("10-Knowledge", contract)
        self.assertIn("知识库更新", contract)


if __name__ == "__main__":
    unittest.main()
