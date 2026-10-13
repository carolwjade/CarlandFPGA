"""Legacy B/C profile names map to one project-local, board-free skill pair."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from fpga_mesh.distribution import build_client_archive, build_project_skills_archive

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ".agents/skills/"
SINGLE = PREFIX + "pynq-z2-single-node/"
MULTI = PREFIX + "fpga-multi-node/"


class ClientDistributionTests(unittest.TestCase):
    def test_b_c_compatibility_builders_share_identical_payloads_and_role(self):
        host = ROOT / SINGLE / "SKILL.md"
        before = hashlib.sha256(host.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            outputs = []
            for node in ("B", "C"):
                output = Path(temp) / f"client-{node}.zip"
                build_client_archive(ROOT, node, output, revision="a" * 40)
                with zipfile.ZipFile(output) as archive:
                    names = set(archive.namelist())
                    self.assertIsNone(archive.testzip())
                    self.assertEqual({name for name in names if name.endswith("/SKILL.md")},
                                     {MULTI + "SKILL.md", SINGLE + "SKILL.md"})
                    self.assertTrue(all(name == "MANIFEST.json" or name.startswith((SINGLE, MULTI)) for name in names))
                    self.assertFalse(any(name.endswith(("board_run.py", "board_probe.py", "Install.ps1", "requirements-board.txt")) for name in names))
                    self.assertIn(MULTI + "scripts/install.py", names)
                    self.assertIn(MULTI + "scripts/handoff.py", names)
                    self.assertIn(SINGLE + "scripts/preflight.py", names)
                    self.assertNotIn(SINGLE + "scripts/handoff.py", names)
                    for prefix in (SINGLE, MULTI):
                        role = json.loads(archive.read(prefix + "skill-role.json"))
                        self.assertEqual(role["allowed_nodes"], ["B", "C"])
                        self.assertEqual(role["scope"], "project")
                        self.assertNotIn("@NODE@", archive.read(prefix + "SKILL.md").decode())
                    manifest = json.loads(archive.read("MANIFEST.json"))
                    self.assertEqual(manifest["profile"], "project-skills-bc")
                    self.assertEqual({item["path"] for item in manifest["files"]}, names - {"MANIFEST.json"})
                    outputs.append({name: archive.read(name) for name in names - {"MANIFEST.json"}})
            self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(hashlib.sha256(host.read_bytes()).hexdigest(), before)

    def test_build_client_rejects_host_node(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "B or C"):
                build_client_archive(ROOT, "A", Path(temp) / "invalid.zip")

    def test_tracked_builder_rejects_untracked_replacement_source(self):
        paths = [path.relative_to(ROOT).as_posix() for path in (ROOT / PREFIX).rglob("*")
                 if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"]
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "not tracked"):
                build_project_skills_archive(ROOT, "bc", Path(temp) / "invalid.zip", revision="a" * 40, paths=paths)

    def test_client_template_redirected_outside_project_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            temporary = Path(temp)
            fake = temporary / "project"
            shutil.copytree(ROOT / PREFIX, fake / PREFIX, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(ROOT / "packaging/multi-node-client", fake / "packaging/multi-node-client")
            outside = temporary / "outside-client-template"
            shutil.copytree(ROOT / "packaging/pynq-client", outside)
            link = fake / "packaging/pynq-client"
            if os.name == "nt":
                environment = dict(os.environ, FPGA_TEST_TEMPLATE_LINK=str(link),
                                   FPGA_TEST_TEMPLATE_TARGET=str(outside))
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                "New-Item -ItemType Junction -Path $env:FPGA_TEST_TEMPLATE_LINK -Target $env:FPGA_TEST_TEMPLATE_TARGET | Out-Null"],
                               env=environment, check=True, capture_output=True)
            else:
                link.symlink_to(outside, target_is_directory=True)
            try:
                paths = [path.relative_to(fake).as_posix() for path in (fake / PREFIX).rglob("*") if path.is_file()]
                for directory in ("multi-node-client", "pynq-client"):
                    paths.extend("packaging/" + directory + "/" + name for name in
                                 ("SKILL.md", "skill-role.json", "openai.yaml"))
                with self.assertRaisesRegex(ValueError, "outside package root|symlink or reparse"):
                    build_project_skills_archive(fake, "bc", temporary / "invalid.zip", revision="a" * 40, paths=paths)
                self.assertFalse((temporary / "invalid.zip").exists())
                self.assertTrue((outside / "SKILL.md").exists())
            finally:
                if os.name == "nt":
                    os.rmdir(link)
                else:
                    link.unlink()


if __name__ == "__main__":
    unittest.main()
