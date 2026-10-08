"""Behavioral tests for the standalone PYNQ-Z2 handoff helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fpga_mesh.hardware import HardwareRequest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "pynq-z2-single-node" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreflightTests(unittest.TestCase):
    def test_reports_only_local_tool_discovery_and_no_board_claim(self):
        preflight = load_script("preflight")

        def which(name: str):
            return {"vivado": "C:/tools/Vivado/bin/vivado.bat"}.get(name)

        result = preflight.collect_preflight(which=which, environ={})
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(
            result["tools"]["vivado"],
            {"available": True, "path": "C:/tools/Vivado/bin/vivado.bat"},
        )
        self.assertEqual(result["tools"]["modelsim"], {"available": False, "path": None})
        self.assertEqual(result["board"], {"status": "not_checked"})

    def test_cli_prints_valid_json_without_needing_vendor_tools(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "preflight.py")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["board"]["status"], "not_checked")
        self.assertEqual(set(payload["tools"]), {"vivado", "modelsim"})

    def test_cli_help_describes_the_static_probe(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "preflight.py"), "--help"],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("local", result.stdout.lower())
        self.assertIn("board", result.stdout.lower())


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "rtl").mkdir()
        (self.root / "logs").mkdir()
        (self.root / "rtl" / "top.v").write_bytes(b"module top; endmodule\n")
        (self.root / "logs" / "sim.log").write_bytes(b"PASS: 4 vectors\n")
        (self.root / "logs" / "timing.log").write_bytes(b"FAIL: slack -0.3\n")
        self.request = {
            "operation_id": "single-op-1",
            "task_id": "fpga-task-1",
            "task_version": 2,
            "requester": "local/Astra",
            "code_commit": "abc123",
            "test_steps": ["simulate four vectors", "inspect timing"],
            "expected_result": "all vectors pass and timing closes",
        }
        self.payload = {
            "request": self.request,
            "artifacts": ["rtl/top.v"],
            "stages": {
                "simulation": {"status": "passed", "log": "logs/sim.log"},
                "timing": {"status": "failed", "log": "logs/timing.log"},
                "synthesis": {"status": "not_run"},
                "hardware": {"status": "blocked"},
            },
        }
        self.input_path = self.root / "handoff-input.json"
        self.output_path = self.root / "handoff-manifest.json"

    def create(self):
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        return load_script("handoff").create_manifest(
            self.root, self.input_path, self.output_path
        )

    def test_create_preserves_separate_stage_outcomes_and_hashes_evidence(self):
        manifest = self.create()
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["request"], self.request)
        self.assertEqual(manifest["request_hash"], HardwareRequest(**self.request).request_hash)
        self.assertEqual(manifest["stages"], self.payload["stages"])
        self.assertEqual(
            manifest["files"]["rtl/top.v"]["sha256"],
            hashlib.sha256(b"module top; endmodule\n").hexdigest(),
        )
        self.assertEqual(manifest["files"]["logs/sim.log"]["size"], 16)
        self.assertEqual(set(manifest["files"]), {"rtl/top.v", "logs/sim.log", "logs/timing.log"})
        self.assertEqual(json.loads(self.output_path.read_text(encoding="utf-8")), manifest)
        self.assertEqual(load_script("handoff").verify_manifest(self.root, self.output_path), manifest)

    def test_verify_detects_changed_and_missing_evidence(self):
        self.create()
        handoff = load_script("handoff")
        (self.root / "rtl" / "top.v").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash|size"):
            handoff.verify_manifest(self.root, self.output_path)
        (self.root / "rtl" / "top.v").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            handoff.verify_manifest(self.root, self.output_path)

    def test_create_rejects_path_traversal_and_success_without_log(self):
        handoff = load_script("handoff")
        for bad_path in ("../escape.v", "/absolute.v", "C:/escape.v", "rtl\\top.v"):
            with self.subTest(path=bad_path):
                self.payload["artifacts"] = [bad_path]
                self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    handoff.create_manifest(self.root, self.input_path, self.output_path)
        self.payload["artifacts"] = ["rtl/top.v"]
        self.payload["stages"]["simulation"] = {"status": "passed"}
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "log"):
            handoff.create_manifest(self.root, self.input_path, self.output_path)

    def test_verify_rejects_forged_success_without_log_and_manifest_escape(self):
        manifest = self.create()
        manifest["stages"]["simulation"] = {"status": "passed"}
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "log"):
            load_script("handoff").verify_manifest(self.root, self.output_path)
        outside = self.root.parent / "outside-handoff.json"
        with self.assertRaisesRegex(ValueError, "root"):
            load_script("handoff").verify_manifest(self.root, outside)

    def test_verify_rejects_manifest_path_escape_even_when_hash_matches(self):
        manifest = self.create()
        manifest["artifacts"] = ["../escape.v"]
        manifest["files"]["../escape.v"] = manifest["files"].pop("rtl/top.v")
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "path|root"):
            load_script("handoff").verify_manifest(self.root, self.output_path)

    def test_rejects_invalid_hardware_request_fields(self):
        handoff = load_script("handoff")
        for invalid in (0, -1, True, "1"):
            with self.subTest(task_version=invalid):
                self.payload["request"]["task_version"] = invalid
                self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "task_version"):
                    handoff.create_manifest(self.root, self.input_path, self.output_path)

    def test_verify_rejects_corrupted_request_hash_and_malformed_stage_status(self):
        manifest = self.create()
        handoff = load_script("handoff")
        manifest["request_hash"] = "0" * 64
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "request_hash"):
            handoff.verify_manifest(self.root, self.output_path)
        manifest["request_hash"] = HardwareRequest(**self.request).request_hash
        manifest["stages"]["hardware"]["status"] = ["passed"]
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "status"):
            handoff.verify_manifest(self.root, self.output_path)

    def test_verify_rejects_boolean_schema_version(self):
        manifest = self.create()
        manifest["schema_version"] = True
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema"):
            load_script("handoff").verify_manifest(self.root, self.output_path)

    def test_create_rejects_passed_stage_with_empty_log(self):
        (self.root / "logs" / "sim.log").write_bytes(b"")
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "empty log"):
            load_script("handoff").create_manifest(
                self.root, self.input_path, self.output_path
            )

    def test_verify_rejects_passed_stage_with_empty_log_even_if_hash_matches(self):
        manifest = self.create()
        (self.root / "logs" / "sim.log").write_bytes(b"")
        manifest["files"]["logs/sim.log"] = {
            "sha256": hashlib.sha256(b"").hexdigest(), "size": 0
        }
        self.output_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "empty log"):
            load_script("handoff").verify_manifest(self.root, self.output_path)

    def test_create_rejects_manifest_output_outside_root(self):
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "root"):
            load_script("handoff").create_manifest(
                self.root, self.input_path, self.root.parent / "escaped-manifest.json"
            )

    def test_relative_manifest_path_is_resolved_under_root_for_create_and_verify(self):
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        handoff = load_script("handoff")
        created = handoff.create_manifest(self.root, self.input_path, "handoff-manifest.json")
        self.assertTrue(self.output_path.is_file())
        self.assertEqual(
            handoff.verify_manifest(self.root, "handoff-manifest.json"), created
        )

    def test_create_reuses_identical_manifest_but_rejects_changed_evidence(self):
        handoff = load_script("handoff")
        first = self.create()
        original_bytes = self.output_path.read_bytes()
        self.assertEqual(
            handoff.create_manifest(self.root, self.input_path, self.output_path), first
        )
        self.assertEqual(self.output_path.read_bytes(), original_bytes)
        (self.root / "logs" / "sim.log").write_bytes(b"PASS: changed evidence\n")
        with self.assertRaisesRegex(ValueError, "already exists|overwrite"):
            handoff.create_manifest(self.root, self.input_path, self.output_path)
        self.assertEqual(self.output_path.read_bytes(), original_bytes)

    def test_cli_create_and_verify_produce_machine_readable_results(self):
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        create = subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff.py"), "create", "--root", str(self.root),
             "--input", str(self.input_path), "--output", str(self.output_path)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(create.returncode, 0, create.stderr)
        self.assertEqual(json.loads(create.stdout)["manifest"], str(self.output_path))
        verify = subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff.py"), "verify", "--root", str(self.root),
             "--manifest", str(self.output_path)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)
        self.assertEqual(json.loads(verify.stdout)["valid"], True)


if __name__ == "__main__":
    unittest.main()
