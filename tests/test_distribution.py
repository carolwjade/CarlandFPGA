import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from fpga_mesh.distribution import build_archive


class DistributionTests(unittest.TestCase):
    def test_archive_contains_only_selected_source_and_verifiable_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "deploy").mkdir()
            (root / "deploy" / "Join.ps1").write_text("Write-Host ready", encoding="utf-8")
            (root / ".local").mkdir()
            (root / ".local" / "secret.txt").write_text("private", encoding="utf-8")
            target = root / "team.zip"
            build_archive(root, ["deploy/Join.ps1"], target, revision="test-rev")
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(sorted(archive.namelist()),
                                 ["MANIFEST.json", "deploy/Join.ps1"])
                manifest = json.loads(archive.read("MANIFEST.json"))
                entry = manifest["files"][0]
                self.assertEqual(entry["sha256"], hashlib.sha256(
                    archive.read("deploy/Join.ps1")
                ).hexdigest())
                self.assertEqual(manifest["revision"], "test-rev")

    def test_secret_path_or_key_material_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".local").mkdir()
            (root / ".local" / "secret.txt").write_text("private", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_archive(root, [".local/secret.txt"], root / "bad.zip")
            (root / "key.txt").write_text("sk-" + "a" * 40, encoding="utf-8")
            with self.assertRaises(ValueError):
                build_archive(root, ["key.txt"], root / "bad.zip")
