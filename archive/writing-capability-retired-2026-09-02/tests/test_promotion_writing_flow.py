from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.content_case_library import add_case, load_library, write_indexes
from scripts.private_library import initialize_library
from scripts.writing_memory import CONFIG_RELATIVE
from scripts.writing_memory import discover_records, search_memory


class PromotionWritingFlowTests(unittest.TestCase):
    def test_writing_technique_index_and_voice_memory_remain_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            layout, _, _ = initialize_library(
                base / "private-library",
                base / "config.json",
            )
            (layout.root / CONFIG_RELATIVE).write_text(
                json.dumps(
                    {
                        "published_article_roots": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            raw = base / "promotion.md"
            raw.write_text(
                "把材料交给私人知识库，它会保留真源，并让下一次写作真正读到。",
                encoding="utf-8",
            )
            created = add_case(
                layout,
                [],
                kind="social",
                input_path=raw,
                title="私人知识库进入写作链",
                techniques=("利益先行", "行动收束"),
                writing_format="short-post",
                writing_purpose="product",
                writing_origin="human-edited",
                voice_eligible=True,
            )
            cases, issues = load_library(layout)
            self.assertFalse(issues)
            write_indexes(layout, cases)

            example = next(case for case in cases if case.path == created)
            self.assertEqual(("利益先行", "行动收束"), example.writing_techniques)
            social_index = layout.social_case_index.read_text(encoding="utf-8")
            self.assertIn("## 利益先行", social_index)
            self.assertIn("## 行动收束", social_index)
            self.assertIn(example.case_id, social_index)
            self.assertNotIn(example.title, social_index)
            self.assertNotIn(
                example.case_id,
                layout.article_case_index.read_text(encoding="utf-8"),
            )

            records, receipt = discover_records(layout.root)
            self.assertEqual(1, receipt.accepted_cases)
            self.assertEqual("short-post", records[0].format)
            self.assertEqual("product", records[0].content_type)
            self.assertTrue(records[0].voice_eligible)

            novelty_hits = search_memory(
                library_root=layout.root,
                records=records,
                purpose="novelty",
                query="材料如何进入长期写作记忆",
                format_name="short-post",
                content_type=None,
                limit=3,
            )
            self.assertEqual("私人知识库进入写作链", novelty_hits[0].record.title)
            voice_hits = search_memory(
                library_root=layout.root,
                records=records,
                purpose="voice",
                query="",
                format_name="short-post",
                content_type="product",
                limit=3,
            )
            self.assertEqual("私人知识库进入写作链", voice_hits[0].record.title)


if __name__ == "__main__":
    unittest.main()
