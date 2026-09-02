from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.private_library import initialize_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LearningContractTests(unittest.TestCase):
    def test_durable_projects_are_used_only_when_the_task_needs_them(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "只有任务确实无法在当前轮可靠完成，或者用户明确要求跨任务恢复时",
            skill,
        )
        self.assertIn("连续学习每轮完成一个当前有用的结果", skill)

    def test_active_skill_does_not_route_to_retired_writing_methods(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        retired_routes = (
            "references/content-writing.md",
            "references/writing-material-preparation.md",
            "references/content-audit.md",
            "references/content-case-library.md",
            "references/hook-library.md",
            "references/personal-writing-memory.md",
            "references/published-content-review.md",
        )

        for route in retired_routes:
            self.assertNotIn(route, skill)

    def test_new_library_contains_only_active_learning_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "library"
            config = Path(temporary) / "config" / "config.json"
            layout, _, created = initialize_library(root, config)

            self.assertTrue(created)
            self.assertTrue((layout.root / "10-Knowledge").is_dir())
            self.assertTrue((layout.root / "20-Sources").is_dir())
            self.assertTrue((layout.root / "30-Projects").is_dir())
            self.assertTrue((layout.root / "40-Outputs").is_dir())
            self.assertFalse((layout.root / "40-Outputs/Writing").exists())
            self.assertFalse((layout.root / "60-Systems/Writing").exists())


if __name__ == "__main__":
    unittest.main()
