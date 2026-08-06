from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.private_library import (
    MANIFEST_RELATIVE,
    REQUIRED_DIRECTORIES,
    adopt_library,
    initialize_library,
    resolve_library_root,
    validate_library,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "private_library.py"


class PrivateLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.library_root = self.temp_root / "private-library"
        self.config_path = self.temp_root / "user-config" / "config.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_init_can_be_resolved_and_validated_by_a_new_process(self) -> None:
        init = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--config",
                str(self.config_path),
                "init",
                "--root",
                str(self.library_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, init.returncode, init.stderr)
        payload = json.loads(init.stdout)
        self.assertEqual("initialized", payload["action"])
        self.assertEqual(str(self.library_root.resolve()), payload["library_root"])

        validate = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--config",
                str(self.config_path),
                "validate",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, validate.returncode, validate.stderr)
        self.assertIn(str(self.library_root.resolve()), validate.stdout)

        show = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--config",
                str(self.config_path),
                "show",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, show.returncode, show.stderr)
        self.assertEqual(
            self.library_root.resolve(),
            Path(json.loads(show.stdout)["library_root"]),
        )

        layout = validate_library(resolve_library_root(config_path=self.config_path))
        self.assertTrue(layout.manifest.is_file())
        self.assertTrue(layout.home.is_file())
        self.assertNotIn("Codex", layout.home.read_text(encoding="utf-8"))
        for relative in REQUIRED_DIRECTORIES:
            self.assertTrue((layout.root / relative).is_dir(), relative)

    def test_repeated_init_preserves_existing_content(self) -> None:
        layout, _, created = initialize_library(
            self.library_root,
            self.config_path,
        )
        self.assertTrue(created)
        marker = "\n用户已经写入的内容。\n"
        layout.home.write_text(
            layout.home.read_text(encoding="utf-8") + marker,
            encoding="utf-8",
        )

        repeated, _, created_again = initialize_library(
            self.library_root,
            self.config_path,
        )
        self.assertFalse(created_again)
        self.assertIn(marker.strip(), repeated.home.read_text(encoding="utf-8"))

    def test_existing_non_library_requires_adopt(self) -> None:
        self.library_root.mkdir(parents=True)
        (self.library_root / "notes.md").write_text("existing", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--config",
                str(self.config_path),
                "init",
                "--root",
                str(self.library_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("使用 adopt", result.stderr)
        self.assertFalse((self.library_root / MANIFEST_RELATIVE).exists())

    def test_invalid_adopt_does_not_leave_a_library_manifest(self) -> None:
        self.library_root.mkdir(parents=True)
        (self.library_root / "Home.md").write_text("# Existing", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "缺少目录"):
            adopt_library(self.library_root, self.config_path)

        self.assertFalse((self.library_root / MANIFEST_RELATIVE).exists())
        self.assertFalse(self.config_path.exists())

if __name__ == "__main__":
    unittest.main()
