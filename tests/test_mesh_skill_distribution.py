"""Two project skills, atomic role installation and exact legacy cleanup boundaries."""
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

from fpga_mesh.distribution import build_project_skills_archive, select_package_paths

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ".agents/skills/"
SKILLS = ("fpga-multi-node", "pynq-z2-single-node")


class MeshSkillTests(unittest.TestCase):
    def make_package(self, root, role="a"):
        output = root / f"{role}.zip"
        build_project_skills_archive(ROOT, role, output, revision="a" * 40)
        destination = root / role
        with zipfile.ZipFile(output) as archive:
            archive.extractall(destination)
        return destination

    def installer(self, package):
        spec = importlib.util.spec_from_file_location(
            "project_skills_install_test", package / PREFIX / SKILLS[0] / "scripts/install.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def project(self, root, node="A"):
        project = root / f"project-{node}"
        project.mkdir()
        (project / ".git").mkdir()
        config = project / f".local/deployment/node-{node.lower()}/node-{node.lower()}.toml"
        config.parent.mkdir(parents=True)
        config.write_text(f'node_id = "{node}"\n', encoding="utf-8")
        (project / "AGENTS.md").write_bytes(b"# Existing project\r\nKeep this rule.\r\n")
        return project

    def old_skills(self, project):
        for skill in SKILLS:
            target = project / PREFIX / skill
            target.mkdir(parents=True)
            (target / "SKILL.md").write_bytes(b"previous " + skill.encode())

    def rehash(self, package):
        path = package / "MANIFEST.json"
        manifest = json.loads(path.read_text())
        for entry in manifest["files"]:
            data = (package / entry["path"]).read_bytes()
            entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        path.write_text(json.dumps(manifest), encoding="utf-8")

    def legacy(self, root, name="pynq-z2-single-node", declared="pynq-z2-single-node"):
        target = root / name
        target.mkdir(parents=True)
        (target / "SKILL.md").write_bytes(f"---\nname: {declared}\ndescription: old\n---\nold\n".encode())
        (target / "tool.py").write_bytes(b"# old tool\r\n")
        return target

    def test_controller_excludes_project_and_obsolete_skill_install_files(self):
        paths = ["fpga_mesh/runtime.py", PREFIX + SKILLS[0] + "/SKILL.md",
                 PREFIX + SKILLS[1] + "/SKILL.md", "skills/pynq-z2-single-node/Install.ps1",
                 "packaging/multi-node-client/SKILL.md", "packaging/pynq-client/SKILL.md"]
        self.assertEqual(select_package_paths(paths, "mesh"), ["fpga_mesh/runtime.py"])

    def test_role_packages_have_exactly_two_skills_and_hash_matched_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packages = {role: self.make_package(root, role) for role in ("a", "bc")}
            for role, package in packages.items():
                nodes = ["A"] if role == "a" else ["B", "C"]
                manifest = json.loads((package / "MANIFEST.json").read_text())
                self.assertEqual(manifest["profile"], "project-skills-" + role)
                self.assertEqual(manifest["version"], "2026.10.13.2")
                self.assertEqual(manifest["revision"], "a" * 40)
                self.assertEqual({p.parent.name for p in (package / PREFIX).glob("*/SKILL.md")}, set(SKILLS))
                for skill in SKILLS:
                    declaration = json.loads((package / PREFIX / skill / "skill-role.json").read_text())
                    self.assertEqual(declaration["allowed_nodes"], nodes)
                for entry in manifest["files"]:
                    data = (package / entry["path"]).read_bytes()
                    self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())
                    self.assertEqual(entry["size"], len(data))
                self.assertEqual(bool(list(package.rglob("board_run.py"))), role == "a")
                self.assertEqual(bool(list(package.rglob("board_probe.py"))), role == "a")
                self.assertEqual(len(list(package.rglob("handoff.py"))), 1)
            shared = PREFIX + SKILLS[0] + "/references/protocol.md"
            self.assertEqual((packages["a"] / shared).read_bytes(), (packages["bc"] / shared).read_bytes())

    def test_install_clients_preserves_configuration_rules_and_reinstall_is_noop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            installer = self.installer(package)
            for node in ("B", "C"):
                project = self.project(root, node)
                before = (project / "AGENTS.md").read_bytes()
                config = project / f".local/deployment/node-{node.lower()}/node-{node.lower()}.toml"
                config_before = config.read_bytes()
                first = installer.install(package, project, node)
                self.assertTrue((project / "AGENTS.md").read_bytes().startswith(before))
                self.assertEqual(first["version"], "2026.10.13.2")
                self.assertTrue(first["new_conversation_required"])
                backups = list((project / ".local/skill-backups").iterdir())
                second = installer.install(package / PREFIX / SKILLS[0], project, node,
                                           cleanup_legacy=True, legacy_roots=[root / "empty-global"])
                self.assertEqual(second["status"], "unchanged")
                self.assertEqual(config.read_bytes(), config_before)
                self.assertEqual(list((project / ".local/skill-backups").iterdir()), backups)
                self.assertEqual({p.parent.name for p in (project / PREFIX).glob("*/SKILL.md")}, set(SKILLS))

    def test_host_preserves_old_skill_bytes_in_nondiscoverable_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            self.old_skills(project)
            result = self.installer(package).install(package, project, "A")
            backup = Path(result["backup"])
            self.assertEqual(backup.suffix, ".zip")
            self.assertEqual(result["backup_sha256"], hashlib.sha256(backup.read_bytes()).hexdigest())
            with zipfile.ZipFile(backup) as archive:
                for skill in SKILLS:
                    self.assertEqual(archive.read("project/" + PREFIX + skill + "/SKILL.md"),
                                     b"previous " + skill.encode())
            self.assertFalse(list((project / ".local/skill-backups").rglob("SKILL.md")))

    def test_legacy_managed_entry_migrates_and_unrelated_rules_keep_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            installer = self.installer(package)
            before = b"prefix\r\n" + installer.OLD_BEGIN.encode() + b"old" + installer.OLD_END.encode() + b"\r\nsuffix\r\n"
            (project / "AGENTS.md").write_bytes(before)
            installer.install(package, project, "A")
            current = (project / "AGENTS.md").read_bytes()
            self.assertTrue(current.startswith(b"prefix\r\n"))
            self.assertTrue(current.endswith(b"\r\nsuffix\r\n"))
            self.assertNotIn(installer.OLD_BEGIN.encode(), current)
            self.assertEqual(current.count(installer.BEGIN.encode()), 1)

    def test_only_exact_old_project_skill_pointer_is_migrated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            rules = (b"use `skills/pynq-z2-single-node/SKILL.md`\r\n"
                     b"existing `.agents/skills/pynq-z2-single-node/SKILL.md`\r\n"
                     b"external `other/skills/pynq-z2-single-node/SKILL.md`\r\nKeep all other rules.\r\n")
            (project / "AGENTS.md").write_bytes(rules)
            self.installer(package).install(package, project, "A")
            actual = (project / "AGENTS.md").read_bytes()
            self.assertIn(b"use `.agents/skills/pynq-z2-single-node/SKILL.md`\r\n", actual)
            self.assertIn(b"existing `.agents/skills/pynq-z2-single-node/SKILL.md`\r\n", actual)
            self.assertIn(b"external `other/skills/pynq-z2-single-node/SKILL.md`\r\n", actual)
            self.assertNotIn(b".agents/.agents", actual)

    def test_wrong_role_and_tampered_package_fail_before_skill_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            project = self.project(root)
            installer = self.installer(package)
            before = (project / "AGENTS.md").read_bytes()
            with self.assertRaisesRegex(ValueError, "role"):
                installer.install(package, project, "A")
            (package / PREFIX / SKILLS[0] / "references/protocol.md").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                installer.install(package, self.project(root, "B"), "B")
            self.assertEqual((project / "AGENTS.md").read_bytes(), before)
            self.assertFalse((project / ".agents").exists())

    def test_matching_hash_but_mismatched_second_role_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            role_path = package / PREFIX / SKILLS[1] / "skill-role.json"
            role = json.loads(role_path.read_text())
            role["allowed_nodes"] = ["A"]
            role_path.write_text(json.dumps(role), encoding="utf-8")
            self.rehash(package)
            project = self.project(root, "B")
            with self.assertRaisesRegex(ValueError, "roles"):
                self.installer(package).install(package, project, "B")
            self.assertFalse((project / ".agents").exists())

    def test_missing_revision_extra_files_and_unsafe_manifest_paths_rejected(self):
        for mode in ("revision", "extra", "traversal", "duplicate"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                package = self.make_package(root)
                manifest_path = package / "MANIFEST.json"
                manifest = json.loads(manifest_path.read_text())
                if mode == "revision":
                    manifest["revision"] = "uncommitted"
                elif mode == "extra":
                    (package / "unlisted.txt").write_bytes(b"unlisted")
                elif mode == "traversal":
                    manifest["files"][0]["path"] = "../escape"
                else:
                    manifest["files"].append(dict(manifest["files"][0]))
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                project = self.project(root)
                with self.assertRaises(ValueError):
                    self.installer(package).install(package, project, "A")
                self.assertFalse((project / ".agents").exists())

    def test_second_publish_failure_rolls_back_both_skills_and_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            self.old_skills(project)
            installer = self.installer(package)
            before = (project / "AGENTS.md").read_bytes()
            original = Path.rename

            def fail_second(path, target):
                if path.name == SKILLS[1] and path.parent.name == "new":
                    raise OSError("injected second publish failure")
                return original(path, target)

            with mock.patch.object(Path, "rename", fail_second):
                with self.assertRaisesRegex(OSError, "second publish"):
                    installer.install(package, project, "A")
            for skill in SKILLS:
                self.assertEqual((project / PREFIX / skill / "SKILL.md").read_bytes(), b"previous " + skill.encode())
            self.assertEqual((project / "AGENTS.md").read_bytes(), before)
            self.assertEqual(len(list((project / ".local/skill-backups").glob("*.zip"))), 1)

    def test_concurrent_target_change_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            self.old_skills(project)
            target = project / PREFIX / SKILLS[0]
            installer = self.installer(package)
            original = installer.payloads
            reads = 0

            def change(path):
                nonlocal reads
                if path == target:
                    reads += 1
                    if reads == 2:
                        (path / "SKILL.md").write_bytes(b"concurrent writer")
                return original(path)

            with mock.patch.object(installer, "payloads", side_effect=change):
                with self.assertRaisesRegex(RuntimeError, "changed during install"):
                    installer.install(package, project, "A")
            self.assertEqual((target / "SKILL.md").read_bytes(), b"concurrent writer")
            self.assertEqual((project / PREFIX / SKILLS[1] / "SKILL.md").read_bytes(), b"previous " + SKILLS[1].encode())

    def test_os_lock_rejects_second_installer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            installer = self.installer(package)
            with installer.installation_lock(project):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    installer.install(package, project, "A")
            self.assertFalse((project / ".agents").exists())

    def test_saved_config_snapshot_is_ignored_but_actual_identity_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            snapshot = project / ".local/deployment/node-a/node-a-before-reload.toml"
            snapshot.write_text('node_id = "C"\n', encoding="utf-8")
            installer = self.installer(package)
            self.assertEqual(installer.install(package, project, "A")["status"], "installed")
            (snapshot.parent / "node-a.toml").write_text('node_id = "B"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identity"):
                installer.install(package, project, "A")

    def test_cleanup_deletes_only_confirmed_named_legacy_skills_and_hashes_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            global_root = root / "global-skills"
            legacy = self.legacy(global_root)
            obsolete_backup = self.legacy(global_root, "pynq-z2-single-node.backup-old")
            unrelated = self.legacy(global_root, "fpga-something-else", "fpga-something-else")
            original = (legacy / "SKILL.md").read_bytes()
            result = self.installer(package).install(package, project, "A", cleanup_legacy=True,
                                                       legacy_roots=[global_root, global_root])
            self.assertFalse(legacy.exists())
            self.assertFalse(obsolete_backup.exists())
            self.assertTrue(unrelated.exists())
            self.assertEqual(len(result["cleaned_legacy"]), 2)
            with zipfile.ZipFile(result["backup"]) as archive:
                backup_manifest = json.loads(archive.read("BACKUP.json"))
                for entry in backup_manifest["files"]:
                    self.assertEqual(entry["sha256"], hashlib.sha256(archive.read(entry["path"])).hexdigest())
                self.assertIn(original, [archive.read(name) for name in archive.namelist()])

    def test_exact_legacy_directory_with_wrong_skill_identity_is_never_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            legacy = self.legacy(root / "global", declared="unrelated-personal-skill")
            with self.assertRaisesRegex(ValueError, "identity is not confirmed"):
                self.installer(package).install(package, project, "A", cleanup_legacy=True, legacy_roots=[legacy.parent])
            self.assertTrue(legacy.exists())
            self.assertFalse((project / ".agents").exists())

    def test_client_cleanup_migrates_old_project_directories_without_deleting_canonical_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root, "bc")
            project = self.project(root, "B")
            installer = self.installer(package)
            installer.install(package, project, "B")
            canonical = {skill: installer.payloads(project / PREFIX / skill) for skill in SKILLS}
            old_single = self.legacy(project / "skills")
            old_coordination = self.legacy(project / PREFIX, "fpga-mesh-coordination", "fpga-mesh-coordination")
            result = installer.install(package, project, "B", cleanup_legacy=True, legacy_roots=[])
            self.assertEqual(set(result["cleaned_legacy"]), {str(old_single), str(old_coordination)})
            self.assertFalse(old_single.exists())
            self.assertFalse(old_coordination.exists())
            for skill, data in canonical.items():
                self.assertEqual(installer.payloads(project / PREFIX / skill), data)
            self.assertEqual({p.parent.name for p in (project / PREFIX).glob("*/SKILL.md")}, set(SKILLS))

    def test_cleanup_never_removes_a_legacy_directory_containing_runtime_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            legacy = self.legacy(root / "global")
            (legacy / "auth.json").write_bytes(b"preserved credential configuration")
            with self.assertRaisesRegex(ValueError, "runtime identity or state"):
                self.installer(package).install(package, project, "A", cleanup_legacy=True, legacy_roots=[legacy.parent])
            self.assertEqual((legacy / "auth.json").read_bytes(), b"preserved credential configuration")
            self.assertFalse((project / ".agents").exists())

    def test_receipt_write_failure_rolls_back_both_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            self.old_skills(project)
            old_agents = (project / "AGENTS.md").read_bytes()
            write = Path.write_text

            def fail_receipt(path, *args, **kwargs):
                if path.parent.name == "skill-backups" and path.suffix == ".json":
                    raise OSError("injected receipt write failure")
                return write(path, *args, **kwargs)

            with mock.patch.object(Path, "write_text", fail_receipt):
                with self.assertRaisesRegex(OSError, "receipt write failure"):
                    self.installer(package).install(package, project, "A")
            self.assertEqual((project / "AGENTS.md").read_bytes(), old_agents)
            for skill in SKILLS:
                self.assertEqual((project / PREFIX / skill / "SKILL.md").read_bytes(), b"previous " + skill.encode())

    def test_partial_cleanup_failure_restores_legacy_and_project_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            self.old_skills(project)
            global_root = root / "global"
            first = self.legacy(global_root, "pynq-z2-single-node")
            second = self.legacy(global_root, "pynq-z2-single-node.backup-old")
            installer = self.installer(package)
            originals = {p: installer.payloads(p) for p in (first, second)}
            old_agents = (project / "AGENTS.md").read_bytes()
            remove = shutil.rmtree

            def fail_partial(path, *args, **kwargs):
                if Path(path) == second:
                    (second / "SKILL.md").unlink()
                    raise OSError("injected cleanup failure")
                return remove(path, *args, **kwargs)

            with mock.patch.object(installer.shutil, "rmtree", side_effect=fail_partial):
                with self.assertRaisesRegex(OSError, "cleanup failure"):
                    installer.install(package, project, "A", cleanup_legacy=True, legacy_roots=[global_root])
            self.assertEqual((project / "AGENTS.md").read_bytes(), old_agents)
            for target, data in originals.items():
                self.assertEqual(installer.payloads(target), data)
            for skill in SKILLS:
                self.assertEqual((project / PREFIX / skill / "SKILL.md").read_bytes(), b"previous " + skill.encode())

    def test_symlinked_legacy_target_is_rejected_without_touching_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self.make_package(root)
            project = self.project(root)
            destination = self.legacy(root / "elsewhere")
            global_root = root / "global"
            global_root.mkdir()
            link = global_root / destination.name
            if os.name == "nt":
                # Directory junctions need no administrator privilege. Use native
                # PowerShell directly, with literal paths supplied in the process env.
                environment = dict(os.environ, FPGA_TEST_JUNCTION_LINK=str(link),
                                   FPGA_TEST_JUNCTION_TARGET=str(destination))
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                "New-Item -ItemType Junction -Path $env:FPGA_TEST_JUNCTION_LINK -Target $env:FPGA_TEST_JUNCTION_TARGET | Out-Null"],
                               env=environment, check=True, capture_output=True)
            else:
                link.symlink_to(destination, target_is_directory=True)
            try:
                with self.assertRaisesRegex(ValueError, "symlink or reparse"):
                    self.installer(package).install(package, project, "A", cleanup_legacy=True, legacy_roots=[global_root])
                self.assertTrue((destination / "SKILL.md").exists())
            finally:
                if os.name == "nt":
                    os.rmdir(link)  # Remove only the junction, never its destination.
                else:
                    link.unlink()


if __name__ == "__main__":
    unittest.main()
