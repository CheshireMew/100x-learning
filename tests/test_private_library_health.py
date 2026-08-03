from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.private_library import initialize_library
from scripts.private_library_health import REPORT_SCHEMA, scan_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "private_library_health.py"


class PrivateLibraryHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.library_root = root / "library"
        self.config_path = root / "config" / "config.json"
        self.layout, _, _ = initialize_library(self.library_root, self.config_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write(self, relative: str, content: str) -> Path:
        path = self.library_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_scan_reads_real_library_files_and_does_not_modify_them(self) -> None:
        self._write(
            "20-Sources/Articles/used.md",
            "# Used source\n\nOriginal evidence.\n",
        )
        self._write(
            "20-Sources/Articles/unprocessed.md",
            "# Unprocessed source\n\nWaiting for synthesis.\n",
        )
        self._write("90-Archive/old.md", "# Archived target\n")
        self._write(
            "10-Knowledge/first.md",
            """---
topic: Shared topic
review_by: 2000-01-01
---
# First

Evidence: [[20-Sources/Articles/used]]
Archive: [[90-Archive/old]]
Broken: [[10-Knowledge/missing]]
""",
        )
        self._write(
            "10-Knowledge/second.md",
            """---
topic: Shared_topic
review_by: not-a-date
---
# Second

An unsupported claim.
""",
        )
        before = {
            path.relative_to(self.library_root).as_posix(): path.read_bytes()
            for path in self.library_root.rglob("*")
            if path.is_file()
        }

        report = scan_library(self.library_root)

        self.assertEqual(REPORT_SCHEMA, report["schema"])
        codes = [issue["code"] for issue in report["issues"]]
        self.assertIn("duplicate_topic", codes)
        self.assertIn("review_due", codes)
        self.assertIn("invalid_review_date", codes)
        self.assertIn("broken_wikilink", codes)
        self.assertIn("knowledge_without_source", codes)
        self.assertIn("unprocessed_source", codes)
        self.assertNotIn(
            "找不到内部链接目标：[[90-Archive/old]]。",
            [issue["message"] for issue in report["issues"]],
        )
        self.assertNotIn(
            "20-Sources/Articles/used.md",
            [
                issue["path"]
                for issue in report["issues"]
                if issue["code"] == "unprocessed_source"
            ],
        )
        after = {
            path.relative_to(self.library_root).as_posix(): path.read_bytes()
            for path in self.library_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_cli_resolves_config_and_returns_machine_readable_severity(self) -> None:
        self._write(
            "10-Knowledge/one.md",
            "---\ntopic: Duplicate\n---\n# One\n",
        )
        self._write(
            "10-Knowledge/two.md",
            "---\ntopic: Duplicate\n---\n# Two\n",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--config",
                str(self.config_path),
                "--fail-on",
                "error",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(2, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(REPORT_SCHEMA, payload["schema"])
        self.assertGreaterEqual(payload["summary"]["error"], 2)
        self.assertEqual(str(self.library_root.resolve()), payload["library_root"])


if __name__ == "__main__":
    unittest.main()
