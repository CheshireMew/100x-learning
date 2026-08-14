from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"


def _declared_resources(text: str, skill_name: str) -> set[str]:
    direct = re.findall(r"`((?:references|scripts)/[^`\s]+)`", text)
    qualified = re.findall(
        rf"<{re.escape(skill_name)}-skill>/((?:references|scripts)/[^`\s]+)",
        text,
    )
    return set(direct + qualified)


class SkillBoundaryTests(unittest.TestCase):
    def test_repository_exposes_exactly_three_active_skills(self) -> None:
        names = sorted(
            path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")
        )
        self.assertEqual(
            ["100x-learning", "content-system", "private-knowledge"],
            names,
        )

    def test_every_direct_reference_and_script_exists(self) -> None:
        for skill_file in SKILLS_ROOT.glob("*/SKILL.md"):
            skill_root = skill_file.parent
            text = skill_file.read_text(encoding="utf-8")
            for relative in _declared_resources(text, skill_root.name):
                self.assertTrue(
                    (skill_root / relative).is_file(),
                    f"{skill_file} references missing {relative}",
                )

    def test_every_active_reference_and_script_is_routed(self) -> None:
        for skill_file in SKILLS_ROOT.glob("*/SKILL.md"):
            skill_root = skill_file.parent
            text = skill_file.read_text(encoding="utf-8")
            declared = _declared_resources(text, skill_root.name)
            active = {
                path.relative_to(skill_root).as_posix()
                for folder, pattern in (("references", "*.md"), ("scripts", "*.py"))
                for path in (skill_root / folder).glob(pattern)
            }
            self.assertEqual(
                active,
                declared,
                f"{skill_file} has an inactive or missing resource route",
            )

    def test_interfaces_match_their_skill_names(self) -> None:
        for skill_file in SKILLS_ROOT.glob("*/SKILL.md"):
            skill_root = skill_file.parent
            name = skill_root.name
            metadata = (skill_root / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn(f"${name}", metadata)
            match = re.search(r'^  short_description: "([^"]+)"$', metadata, re.M)
            self.assertIsNotNone(match)
            description = match.group(1)
            self.assertGreaterEqual(len(description), 25)
            self.assertLessEqual(len(description), 64)

    def test_writing_production_left_the_active_100x_skill(self) -> None:
        learning = (SKILLS_ROOT / "100x-learning" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("$prep-this", learning)
        self.assertIn("$write-this", learning)
        self.assertNotIn("三份完整案例和三份完整钩子参与写作", learning)
        self.assertFalse(
            (SKILLS_ROOT / "100x-learning" / "references" / "content-writing.md").exists()
        )

    def test_private_library_keeps_the_existing_machine_contract(self) -> None:
        private_library = (
            SKILLS_ROOT / "private-knowledge" / "scripts" / "private_library.py"
        ).read_text(encoding="utf-8")
        self.assertIn('Path(".100x-learning/config.json")', private_library)
        self.assertIn('"100x-learning-private-library"', private_library)

    def test_content_system_uses_the_sibling_private_library_contract(self) -> None:
        for name in (
            "content_case_library.py",
            "hook_library.py",
            "writing_memory.py",
        ):
            text = (
                SKILLS_ROOT / "content-system" / "scripts" / name
            ).read_text(encoding="utf-8")
            self.assertIn('"private-knowledge" / "scripts"', text)

    def test_migrated_writing_material_remains_archived(self) -> None:
        archive = (
            REPOSITORY_ROOT
            / "archive"
            / "writing-capability-migrated-2026-08-14"
            / "references"
        )
        expected = {
            "article-from-practice.md",
            "content-audit.md",
            "content-writing.md",
            "github-project-list.md",
            "github-project-short-content.md",
            "natural-writing.md",
            "project-promotion-materials.md",
            "publication-requirements.md",
            "writing-material-preparation.md",
        }
        self.assertEqual(expected, {path.name for path in archive.glob("*.md")})


if __name__ == "__main__":
    unittest.main()
