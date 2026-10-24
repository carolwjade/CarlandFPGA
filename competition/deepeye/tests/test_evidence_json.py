"""Small report fixtures; no numerical model, service or board operations."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

try:
    import numpy as np
except ImportError:
    np = None

SCRIPT = Path(os.environ.get(
    "DEEPEYE_REPORT_HELPER",
    str(Path(__file__).resolve().parents[1] / "tools/evidence_json.py"),
))


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("evidence_json", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            dir=os.environ.get("DEEPEYE_REPORT_TEST_ROOT")
        )
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @unittest.skipIf(np is None, "scientific report fixture requires NumPy")
    def test_real_numpy_comparison_and_utf8(self):
        target = self.root / "report.json"
        value = {"校验": {"passed": np.float64(0.2) <= np.float64(0.1),
                         "count": np.int64(7), "large": np.uint64(2**63),
                         "value": np.float32(0.25)}}
        self.mod.write_new_report(target, value)
        raw = target.read_bytes()
        result = json.loads(raw)
        self.assertIs(result["校验"]["passed"], False)
        self.assertEqual(result["校验"]["count"], 7)
        self.assertEqual(result["校验"]["large"], 2**63)
        self.assertEqual(result["校验"]["value"], 0.25)
        self.assertIn("校验".encode("utf-8"), raw)
        self.assertTrue(raw.endswith(b"\n"))

    def test_unsupported_values_never_create_output(self):
        values = [object(), 1 + 2j]
        if np is not None:
            values += [np.array([1, 2]), np.complex64(1 + 2j),
                       np.datetime64("2026-10-23"), np.timedelta64(3, "D")]
        for i, value in enumerate(values):
            with self.subTest(kind=type(value).__name__):
                target = self.root / f"unsupported-{i}.json"
                with self.assertRaises(TypeError):
                    self.mod.write_new_report(target, {"ok": 1, "bad": value})
                self.assertFalse(target.exists())

    def test_nonfinite_values_never_create_output(self):
        values = [float("nan"), float("inf"), -float("inf")]
        if np is not None:
            values.append(np.float32("inf"))
        for i, value in enumerate(values):
            with self.subTest(index=i):
                target = self.root / f"nonfinite-{i}.json"
                with self.assertRaises(ValueError):
                    self.mod.write_new_report(target, {"ok": 1, "bad": value})
                self.assertFalse(target.exists())

    def test_existing_report_remains_byte_identical(self):
        target = self.root / "original.json"
        original = b'{"original":true}\n'
        target.write_bytes(original)
        with self.assertRaises(FileExistsError):
            self.mod.write_new_report(target, {"replacement": True})
        self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
