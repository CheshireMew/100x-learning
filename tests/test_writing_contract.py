from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        routed = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }

        self.assertEqual(active, routed)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in routed))

    def test_references_do_not_select_sibling_references(self) -> None:
        paths = sorted((PROJECT_ROOT / "references").glob("*.md"))
        active_names = {path.name for path in paths}

        for path in paths:
            text = path.read_text(encoding="utf-8")
            mentioned = sorted(
                name for name in active_names if name != path.name and name in text
            )
            self.assertEqual([], mentioned, path)

    def test_writing_materials_are_filtered_without_being_rewritten(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        prewriting = (PROJECT_ROOT / "references" / "prewriting-research.md").read_text(
            encoding="utf-8"
        )
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("写作使用的任务与材料", skill)
        self.assertIn("材料净化只做删除", prewriting)
        self.assertIn("这些改写只发生在成品中", content_writing)
        self.assertNotIn("传给写作 AI", skill)
        self.assertNotIn("写作 AI 的成品内容", skill)


if __name__ == "__main__":
    unittest.main()
