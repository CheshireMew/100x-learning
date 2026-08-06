from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.private_library import initialize_library


class ContentLearningLoopTests(unittest.TestCase):
    def test_initialization_preserves_existing_strategy_and_templates(self) -> None:
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
