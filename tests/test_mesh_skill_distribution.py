"""Two portable role packages, with project-only install and intact provenance."""
import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

from fpga_mesh.distribution import build_mesh_skill_archive
from fpga_mesh.distribution import select_package_paths

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ".agents/skills/fpga-multi-node/"


class MeshSkillTests(unittest.TestCase):
    def test_controller_package_does_not_ship_host_role_to_clients(self):
        self.assertEqual(select_package_paths(["fpga_mesh/runtime.py", PREFIX + "SKILL.md",
                                              "packaging/multi-node-client/SKILL.md"], "mesh"),
                         ["fpga_mesh/runtime.py"])

    def make_package(self, root, role):
        output = root / f"{role}.zip"
        build_mesh_skill_archive(ROOT, role, output, revision="test-revision")
        destination = root / role
        with zipfile.ZipFile(output) as archive:
            archive.extractall(destination)
        return destination

    def installer(self, package):
        spec = importlib.util.spec_from_file_location(
            "mesh_skill_install_test", package / PREFIX / "scripts/install.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def project(self, root, node):
        project = root / f"project-{node}"
        project.mkdir()
        (project / ".git").mkdir()
        config = project / f".local/deployment/node-{node.lower()}/node-{node.lower()}.toml"
        config.parent.mkdir(parents=True)
        config.write_text(f'node_id = "{node}"\n', encoding="utf-8")
        (project / "AGENTS.md").write_bytes(b"# Existing project\r\nKeep this rule.\r\n")
        return project

    def test_two_packages_share_protocol_but_enforce_distinct_roles(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = self.make_package(root, "a")
            bc = self.make_package(root, "bc")
            for package, nodes in ((a, ["A"]), (bc, ["B", "C"])):
                role = json.loads((package / PREFIX / "skill-role.json").read_text())
                self.assertEqual(role["allowed_nodes"], nodes)
                manifest = json.loads((package / "MANIFEST.json").read_text())
                self.assertEqual(manifest["revision"], "test-revision")
                for entry in manifest["files"]:
                    self.assertEqual(entry["sha256"], hashlib.sha256(
                        (package / entry["path"]).read_bytes()).hexdigest())
                for document in (package / PREFIX).rglob("*.md"):
                    for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                        self.assertTrue((document.parent / link).is_file(), link)
                self.assertFalse(list(package.rglob("board_run.py")))
            self.assertEqual((a / PREFIX / "references/protocol.md").read_bytes(),
                             (bc / PREFIX / "references/protocol.md").read_bytes())
            self.assertIn("客机 B/C", (bc / PREFIX / "SKILL.md").read_text(encoding="utf-8"))

    def test_install_both_clients_preserves_rules_config_and_reinstall_is_noop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            installer = self.installer(package)
            for node in ("B", "C"):
                project = self.project(root, node)
                before = (project / "AGENTS.md").read_bytes()
                config = project / f".local/deployment/node-{node.lower()}/node-{node.lower()}.toml"
                config_before = config.read_bytes()
                installer.install(package / PREFIX, project, node)
                rules = (project / "AGENTS.md").read_bytes()
                backups = list((project / ".local").glob("skill-backups/*"))
                self.assertTrue(rules.startswith(before))
                installer.install(package / PREFIX, project, node)
                self.assertEqual((project / "AGENTS.md").read_bytes(), rules)
                self.assertEqual(config.read_bytes(), config_before)
                self.assertEqual(list((project / ".local").glob("skill-backups/*")), backups)

    def test_host_install_preserves_previous_skill_in_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "a")
            project = self.project(root, "A")
            previous = project / PREFIX / "SKILL.md"
            previous.parent.mkdir(parents=True)
            previous.write_bytes(b"previous local skill")
            result = self.installer(package).install(package / PREFIX, project, "A")
            self.assertEqual((Path(result["backup"]) / "skill/SKILL.md").read_bytes(),
                             b"previous local skill")
            self.assertEqual(previous.read_bytes(), (package / PREFIX / "SKILL.md").read_bytes())

    def test_losing_install_preserves_a_concurrently_published_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "a")
            project = self.project(root, "A")
            target = project / PREFIX
            target.mkdir(parents=True)
            (target / "SKILL.md").write_bytes(b"old")
            installer = self.installer(package)
            original = installer.payloads
            target_reads = 0

            def concurrent_writer(path):
                nonlocal target_reads
                if path == target:
                    target_reads += 1
                    if target_reads == 2:
                        shutil.copytree(package / PREFIX, target, dirs_exist_ok=True)
                return original(path)

            with mock.patch.object(installer, "payloads", side_effect=concurrent_writer):
                with self.assertRaisesRegex(RuntimeError, "changed during install"):
                    installer.install(package / PREFIX, project, "A")
            self.assertEqual((target / "SKILL.md").read_bytes(),
                             (package / PREFIX / "SKILL.md").read_bytes())

    def test_wrong_role_and_tampered_package_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            installer = self.installer(package)
            project = self.project(root, "A")
            before = (project / "AGENTS.md").read_bytes()
            with self.assertRaisesRegex(ValueError, "role"):
                installer.install(package / PREFIX, project, "A")
            (package / PREFIX / "references/protocol.md").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                installer.install(package / PREFIX, self.project(root, "B"), "B")
            self.assertEqual((project / "AGENTS.md").read_bytes(), before)
            self.assertFalse((project / ".agents").exists())

    def test_second_install_is_rejected_by_os_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "a")
            project = self.project(root, "A")
            installer = self.installer(package)
            before = (project / "AGENTS.md").read_bytes()
            with installer.installation_lock(project):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    installer.install(package / PREFIX, project, "A")
            self.assertEqual((project / "AGENTS.md").read_bytes(), before)
            self.assertFalse((project / ".agents").exists())

    def test_saved_config_snapshot_is_not_an_extra_node(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "a")
            project = self.project(root, "A")
            snapshot = project / ".local/deployment/node-a/node-a-before-reload-v2.toml"
            snapshot.write_text('node_id = "A"\n', encoding="utf-8")
            result = self.installer(package).install(package / PREFIX, project, "A")
            self.assertEqual(result["status"], "installed")
            self.assertEqual(snapshot.read_text(), 'node_id = "A"\n')


if __name__ == "__main__":
    unittest.main()
