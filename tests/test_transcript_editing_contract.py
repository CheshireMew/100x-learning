from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TranscriptEditingContractTests(unittest.TestCase):
    def test_transcripts_default_to_one_clean_source_document(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("输入主体是 SRT、VTT、带时间戳文本", skill)
        self.assertIn("20-Sources/Transcripts", skill)
        self.assertIn("整理并校正为忠实、连续、可读的完整来源", skill)
        self.assertIn("不摘要、不压缩、不重排论证", skill)
        self.assertIn("材料讲解、摘要、研究和知识笔记都不是字幕整稿的默认附加结果", skill)

    def test_editing_contract_cleans_without_extra_research_or_notes(self) -> None:
        contract = (PROJECT_ROOT / "references" / "transcript-editing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("不摘要、不压缩、不改写成新的表达", contract)
        self.assertIn("能够明确圈定的广告、片头片尾推广和与主题无关插入", contract)
        self.assertIn("删减说明", contract)
        self.assertIn("无法确定时保留", contract)
        self.assertIn("只修正能够从上下文高置信确认的错误", contract)
        self.assertIn("不重新创作", contract)
        self.assertIn("20-Sources/Transcripts", contract)
        self.assertIn("材料讲解、摘要、研究和知识笔记都不是字幕整稿的默认产物", contract)
        self.assertNotIn("10-Knowledge", contract)


if __name__ == "__main__":
    unittest.main()
