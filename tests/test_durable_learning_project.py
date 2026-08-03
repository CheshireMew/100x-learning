from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "durable_learning_project.py"


class DurableLearningProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.project_root = self.root / "learning-project"
        self.source = self.root / "source.md"
        self.source.write_text("# Source\n\nStable source content.\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return json.loads(result.stdout) if result.stdout else {"stderr": result.stderr}

    def test_cli_tracks_real_source_output_and_final_artifact(self) -> None:
        initialized = self._run(
            "init",
            "--project-root",
            str(self.project_root),
            "--type",
            "long-material",
            "--title",
            "Durable study",
        )
        self.assertEqual("initialized", initialized["action"])

        added = self._run(
            "add-unit",
            "--project-root",
            str(self.project_root),
            "--source",
            str(self.source),
            "--label",
            "Opening argument",
            "--locator",
            "section 1",
        )
        self.assertEqual("unit-added", added["action"])
        unit = added["unit"]
        self.assertEqual(str(self.source.resolve()), unit["source"]["path"])

        output = self.project_root / "units" / "unit-0001.md"
        output.parent.mkdir(parents=True)
        output.write_text(
            "# Unit result\n\nA completed result derived from the registered source.\n",
            encoding="utf-8",
        )
        self._run(
            "record-unit",
            "--project-root",
            str(self.project_root),
            "--unit",
            "unit-0001",
            "--output",
            str(output),
        )

        status = self._run("status", "--project-root", str(self.project_root))
        self.assertEqual(1, status["complete_units"])
        self.assertEqual(0, status["pending_units"])
        self.assertTrue(status["ready_to_finalize"])

        aggregate = self.project_root / "final.md"
        aggregate.write_text(
            "# Final\n\nThe aggregate reads the completed unit.\n",
            encoding="utf-8",
        )
        finalized = self._run(
            "finalize",
            "--project-root",
            str(self.project_root),
            "--aggregate",
            str(aggregate),
        )
        self.assertEqual("finalized", finalized["action"])

        complete = self._run("status", "--project-root", str(self.project_root))
        self.assertTrue(complete["final_valid"])
        self.assertTrue(complete["project_complete"])

        manifest = json.loads(
            (self.project_root / "learning-project.json").read_text(encoding="utf-8")
        )
        self.assertEqual("unit-0001", manifest["units"][0]["id"])
        self.assertEqual("units/unit-0001.md", manifest["units"][0]["output"]["path"])
        self.assertEqual("final.md", manifest["final"]["path"])

        aggregate.write_text("# Final\n\nChanged aggregate.\n", encoding="utf-8")
        drifted = self._run("status", "--project-root", str(self.project_root))
        self.assertFalse(drifted["final_valid"])
        self.assertFalse(drifted["project_complete"])
        self.assertTrue(drifted["ready_to_finalize"])
        self.assertIn("final", [issue["kind"] for issue in drifted["issues"]])

        self._run(
            "finalize",
            "--project-root",
            str(self.project_root),
            "--aggregate",
            str(aggregate),
        )
        restored = self._run("status", "--project-root", str(self.project_root))
        self.assertTrue(restored["project_complete"])

    def test_source_drift_is_visible_and_blocks_finalization(self) -> None:
        self._run(
            "init",
            "--project-root",
            str(self.project_root),
            "--type",
            "bulk-ingestion",
            "--title",
            "Source audit",
        )
        self._run(
            "add-unit",
            "--project-root",
            str(self.project_root),
            "--source",
            str(self.source),
            "--label",
            "Document",
            "--locator",
            "whole file",
        )
        self.source.write_text("# Source\n\nChanged source content.\n", encoding="utf-8")

        status = self._run("status", "--project-root", str(self.project_root))

        self.assertFalse(status["ready_to_finalize"])
        self.assertEqual("source", status["issues"][0]["kind"])
        failed = self._run(
            "finalize",
            "--project-root",
            str(self.project_root),
            "--aggregate",
            str(self.project_root / "final.md"),
            expected=1,
        )
        self.assertIn("不能完成项目", failed["stderr"])


if __name__ == "__main__":
    unittest.main()
