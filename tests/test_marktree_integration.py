from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.marktree_integration import (
    ManagedWrite,
    MarktreeIntegrationError,
    managed_write_batch,
    managed_write_text,
)
from scripts.private_library import initialize_library


class MarktreeIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.library_root = self.root / "library"
        self.config = self.root / "config.json"
        initialize_library(self.library_root, self.config)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_unconfigured_library_keeps_standalone_exact_write_behavior(self) -> None:
        target = self.library_root / "10-Knowledge" / "Marktree.md"

        result = managed_write_text(
            self.library_root,
            target,
            "# Marktree\n\n独立模式。\n",
            config_path=self.config,
        )

        self.assertEqual(target.resolve(), result)
        self.assertEqual(
            b"# Marktree\n\n\xe7\x8b\xac\xe7\xab\x8b\xe6\xa8\xa1\xe5\xbc\x8f\xe3\x80\x82\n",
            target.read_bytes(),
        )

    def test_batch_rejects_duplicate_and_outside_paths_before_writing(self) -> None:
        target = self.library_root / "10-Knowledge" / "Duplicate.md"
        with self.assertRaisesRegex(MarktreeIntegrationError, "重复写入"):
            managed_write_batch(
                self.library_root,
                [
                    ManagedWrite(target, "first"),
                    ManagedWrite(target, "second"),
                ],
                config_path=self.config,
            )
        self.assertFalse(target.exists())

        with self.assertRaisesRegex(MarktreeIntegrationError, "不在私人知识库内"):
            managed_write_text(
                self.library_root,
                self.root / "outside.md",
                "outside",
                config_path=self.config,
            )

    def test_invalid_configured_cli_is_reported_instead_of_silent_fallback(self) -> None:
        value = json.loads(self.config.read_text(encoding="utf-8"))
        value["marktree_cli"] = str(self.root / "missing.exe")
        self.config.write_text(json.dumps(value), encoding="utf-8")

        with self.assertRaisesRegex(MarktreeIntegrationError, "不可用"):
            managed_write_text(
                self.library_root,
                self.library_root / "10-Knowledge" / "Failure.md",
                "must not write",
                config_path=self.config,
            )


if __name__ == "__main__":
    unittest.main()
