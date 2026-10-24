"""Read-only inventory boundary tests; no real hardware queries or target imports."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "preflight.py"
spec = importlib.util.spec_from_file_location("preflight_under_test", SOURCE)
if SOURCE.exists():
    preflight = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight)
else:
    preflight = None


def inventory():
    rows = {
        "cpu": [{"name": "CPU", "architecture": "9", "address_width": 64,
                 "cores": 8, "logical_processors": 16}],
        "os": [{"name": "Windows", "version": "10.0", "build": "12345",
                "architecture": "64-bit", "total_memory_bytes": 17179869184}],
        "gpu": [], "npu_candidates": [], "drivers": [],
        "disks": [{"device_id": "C:", "filesystem": "NTFS",
                   "total_bytes": 1000, "free_bytes": 400}],
    }
    return {"schema": 1, "observed_at_utc": "2026-10-20T01:02:03Z",
            "groups": {key: {"status": "ok", "rows": value, "error": None}
                       for key, value in rows.items()}}


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(preflight, "missing required tools/preflight.py entrypoint")

    def run_cli(self, args=(), data=None):
        output = io.StringIO()
        with patch.object(preflight.platform, "system", return_value="Windows"), \
             patch.object(preflight, "collect_windows", return_value=data or inventory()), \
             patch.object(preflight, "package_metadata", return_value={"complete": True, "packages": {}}), \
             patch.object(preflight.sys, "stdout", output):
            code = preflight.main(list(args))
        self.last_stdout = output.getvalue()
        return code, json.loads(output.getvalue())

    def test_command_is_required(self):
        self.assertTrue(SOURCE.is_file())

    def test_inventory_complete_does_not_close_r02(self):
        code, result = self.run_cli(["--inventory-only"])
        self.assertEqual(code, 0)
        self.assertTrue(result["inventory_complete"])
        self.assertEqual(result["R02"], "not_run")
        self.assertFalse(result["formal_acceptance"])
        self.assertTrue(all(v in ("unknown", "not_run") for v in result["gates"].values()))
        self.assertEqual(result["observations"]["groups"]["gpu"]["rows"], [])
        self.assertEqual(result["contract"]["actual_requirements_sha256"],
                         "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804")
        self.assertEqual(len(result["collector_source_sha256"]), 64)

    def test_default_command_cannot_exit_success(self):
        code, result = self.run_cli()
        self.assertEqual(code, 2)
        self.assertTrue(result["inventory_complete"])

    def test_required_groups_fields_and_integer_types(self):
        cases = []
        for group in ("cpu", "os", "disks"):
            data = inventory()
            data["groups"][group]["rows"] = []
            cases.append(data)
        data = inventory()
        data["groups"]["cpu"]["rows"][0]["cores"] = True
        cases.append(data)
        data = inventory()
        del data["groups"]["gpu"]
        cases.append(data)
        data = inventory()
        data["observed_at_utc"] = "yesterday"
        cases.append(data)
        data = inventory()
        data["groups"]["disks"]["rows"][0]["free_bytes"] = 1001
        cases.append(data)
        for data in cases:
            with self.subTest(data=data):
                code, result = self.run_cli(["--inventory-only"], data)
                self.assertEqual(code, 2)
                self.assertFalse(result["inventory_complete"])
                self.assertTrue(result["errors"])

    def test_partial_query_preserves_actual_error(self):
        data = inventory()
        data["groups"]["gpu"] = {"status": "error", "rows": [], "error": "CIM denied"}
        code, result = self.run_cli(["--inventory-only"], data)
        self.assertEqual(code, 2)
        self.assertIn("CIM denied", json.dumps(result))
        self.assertEqual(result["observations"], data)

    def test_npu_candidates_are_not_input_devices_or_tested_accelerators(self):
        for name, device_id, expected in [
            ("USB Input Device", "USB\\INPUT", False),
            ("AMD IPU Device", "PCI\\VEN_1022&DEV_1502", True),
            ("IPU", "PCI\\OTHER", True),
            ("Neural Processor", "PCI\\OTHER", True),
            ("NPU accelerator", "PCI\\OTHER", True),
            ("Unknown device", "PCI\\VEN_1022&DEV_17F0&SUBSYS_0000", True),
        ]:
            with self.subTest(name=name):
                self.assertEqual(preflight.is_npu_candidate(name, device_id), expected)
        data = inventory()
        data["groups"]["npu_candidates"]["rows"] = [
            {"name": "USB Input Device", "device_id": "USB\\INPUT", "status": "OK"}]
        self.assertEqual(self.run_cli(["--inventory-only"], data)[0], 2)

    def test_forged_contract_never_invokes_collector(self):
        original = json.loads(preflight.CONTRACT_PATH.read_text(encoding="utf-8"))
        variants = []
        forged = copy.deepcopy(original)
        forged["requirements"][0]["must"] += " forged"
        variants.append(forged)
        for field, value in [("revision", True), ("contract_id", "other")]:
            forged = copy.deepcopy(original)
            forged[field] = value
            variants.append(forged)
        forged = copy.deepcopy(original)
        forged["requirements"][1]["id"] = "H01"
        variants.append(forged)
        with tempfile.TemporaryDirectory() as folder:
            for index, forged in enumerate(variants):
                path = Path(folder) / str(index)
                path.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
                output = io.StringIO()
                with patch.object(preflight, "CONTRACT_PATH", path), \
                     patch.object(preflight, "collect_windows", side_effect=AssertionError("must not query")), \
                     patch.object(preflight.sys, "stdout", output):
                    self.assertEqual(preflight.main(["--inventory-only"]), 2)
                self.assertEqual(json.loads(output.getvalue())["errors"][0]["code"], "contract_invalid")

    def test_json_rejects_duplicates_nonfinite_oversize_and_bad_utf8(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e400}',
                    b' ' * (1048576 + 1), b'\xff', b'[]'):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(ValueError):
                    preflight.decode_json(raw)

    def test_metadata_is_current_interpreter_only_and_does_not_import_packages(self):
        def version(name):
            if name == "torch":
                raise preflight.metadata.PackageNotFoundError(name)
            if name == "onnx":
                raise RuntimeError("damaged metadata")
            return "1.2.3"
        with patch.object(preflight.metadata, "version", side_effect=version):
            result = preflight.package_metadata()
        self.assertFalse(result["complete"])
        self.assertEqual(result["packages"]["torch"]["status"], "not_installed")
        self.assertEqual(result["packages"]["onnx"]["status"], "metadata_error")
        self.assertIn("damaged metadata", result["packages"]["onnx"]["error"])
        self.assertEqual(result["packages"]["numpy"]["version"], "1.2.3")

    def test_metadata_error_prevents_success(self):
        with patch.object(preflight.platform, "system", return_value="Windows"), \
             patch.object(preflight, "collect_windows", return_value=inventory()), \
             patch.object(preflight, "package_metadata", return_value={"complete": False, "packages": {}}), \
             patch.object(preflight.sys, "stdout", io.StringIO()) as output:
            self.assertEqual(preflight.main(["--inventory-only"]), 2)
        self.assertFalse(json.loads(output.getvalue())["inventory_complete"])

    def test_unsupported_platform_never_queries(self):
        with patch.object(preflight.platform, "system", return_value="Linux"), \
             patch.object(preflight, "collect_windows", side_effect=AssertionError("must not query")), \
             patch.object(preflight.sys, "stdout", io.StringIO()) as output:
            self.assertEqual(preflight.main(["--inventory-only"]), 2)
        self.assertEqual(json.loads(output.getvalue())["errors"][0]["code"], "unsupported_platform")

    def test_exclusive_output_is_identical_and_refuses_before_query(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            code, result = self.run_cli(["--inventory-only", "--output", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), result)
            self.assertEqual(path.read_bytes(), self.last_stdout.encode("utf-8"))
            before = path.read_bytes()
            with patch.object(preflight, "collect_windows", side_effect=AssertionError("must not query")), \
                 patch.object(preflight.sys, "stdout", io.StringIO()) as output:
                self.assertEqual(preflight.main(["--output", str(path)]), 2)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(json.loads(output.getvalue())["errors"][0]["code"], "output_refused")
            absent = Path(folder) / "absent" / "result.json"
            self.assertEqual(self.run_cli(["--output", str(absent)])[0], 2)
            self.assertFalse(absent.parent.exists())

    def test_timeout_kills_waits_owned_process_once_and_retains_diagnostics(self):
        class Process:
            stdout = io.BytesIO(b'partial output')
            stderr = io.BytesIO(b'CIM stalled')
            returncode = None
            waits = 0
            killed = False
            def wait(self, timeout=None):
                self.waits += 1
                if self.waits == 1:
                    raise subprocess.TimeoutExpired("powershell", timeout)
                self.returncode = -9
                return -9
            def kill(self):
                self.killed = True
        process = Process()
        with patch.object(preflight.subprocess, "Popen", return_value=process) as spawn:
            with self.assertRaises(preflight.CollectionError) as caught:
                preflight.collect_windows()
        self.assertTrue(process.killed)
        self.assertEqual(process.waits, 2)
        self.assertEqual(caught.exception.code, "collector_timeout")
        self.assertIn("CIM stalled", caught.exception.details["stderr"])
        self.assertEqual(spawn.call_count, 1)
        options = spawn.call_args.kwargs
        self.assertEqual(options["creationflags"] & 0x08004000, 0x08004000)
        self.assertEqual(options["stdin"], subprocess.DEVNULL)
        self.assertIn("-NonInteractive", spawn.call_args.args[0])

    def test_nonzero_exit_is_not_a_successful_inventory(self):
        class Process:
            stdout = io.BytesIO(b'{"partial":true}')
            stderr = io.BytesIO(b'query failed')
            returncode = 7
            def wait(self, timeout=None):
                return 7
        with patch.object(preflight.subprocess, "Popen", return_value=Process()):
            with self.assertRaises(preflight.CollectionError) as caught:
                preflight.collect_windows()
        self.assertEqual(caught.exception.code, "collector_exit")
        self.assertEqual(caught.exception.details["exit_code"], 7)


if __name__ == "__main__":
    unittest.main()
