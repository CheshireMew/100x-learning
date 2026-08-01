from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.content_case_library import add_case, load_library, write_index
from scripts.private_library import initialize_library
from scripts.writing_memory import CONFIG_RELATIVE
from scripts.writing_memory import discover_records, search_memory


class PromotionWritingFlowTests(unittest.TestCase):
    def test_role_and_benefit_contract_reaches_cases_and_memory_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            layout, _, _ = initialize_library(
                base / "private-library",
                base / "config.json",
            )
            (layout.root / CONFIG_RELATIVE).write_text(
                json.dumps(
                    {
                        "verified_first_party_url_prefixes": [
                            "https://x.com/author/status/"
                        ],
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
                kind="short",
                input_path=raw,
                title="私人知识库进入写作链",
                content_type="项目与产品介绍",
                source="https://x.com/author/status/2053104321668239801",
                index_task="介绍私人知识库",
                topics=("知识库", "写作"),
                moves=("材料进入长期记忆",),
                index_roles=("promotion",),
                promotion_stages=("launch",),
                audience_actions=("visit",),
                benefit_recipients=("reader",),
                writing_format="product",
                writing_origin="human-edited",
                voice_eligible=True,
            )
            cases, issues = load_library(layout)
            self.assertFalse(issues)
            write_index(layout, cases)

            promotion = next(case for case in cases if case.path == created)
            self.assertEqual(("visit",), promotion.audience_actions)
            self.assertEqual(("reader",), promotion.benefit_recipients)

            records, receipt = discover_records(layout.root)
            self.assertEqual(1, receipt.accepted_social)
            self.assertEqual("product", records[0].format)
            self.assertTrue(records[0].voice_eligible)

            novelty_hits = search_memory(
                library_root=layout.root,
                records=records,
                purpose="novelty",
                query="材料如何进入长期写作记忆",
                format_name="product",
                content_type=None,
                limit=3,
            )
            self.assertEqual("私人知识库进入写作链", novelty_hits[0].record.title)
            voice_hits = search_memory(
                library_root=layout.root,
                records=records,
                purpose="voice",
                query="",
                format_name="product",
                content_type="项目与产品介绍",
                limit=3,
            )
            self.assertEqual("私人知识库进入写作链", voice_hits[0].record.title)


if __name__ == "__main__":
    unittest.main()
