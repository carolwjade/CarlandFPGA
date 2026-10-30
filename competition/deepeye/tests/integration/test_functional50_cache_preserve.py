import json
import tempfile
import unittest
from pathlib import Path
from competition.deepeye.tools.diagnostic import functional50_board_a as board

class VendorStateControls(unittest.TestCase):
    def test_existing_state_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/"global_pl_state.json").write_bytes(b"{}")
            with self.assertRaises(ValueError): board._require_no_global_state(root)

    def test_metadata_raw_copy(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);vendor=root/"vendor";vendor.mkdir();operation=root/"operation";operation.mkdir()
            data=b"not a pickle\x00\xff";(vendor/"_current_metadata.pkl").write_bytes(data)
            board._preserve_vendor_state(operation,vendor)
            self.assertEqual((operation/"vendor-before"/"_current_metadata.pkl").read_bytes(),data)
            receipt=json.loads((operation/"vendor-before"/"receipt.json").read_bytes())
            self.assertTrue(receipt["metadata_exists"]);self.assertEqual(receipt["metadata_bytes"],len(data));self.assertEqual(receipt["metadata_sha256"],board._hash(data))

    def test_absent_recorded(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);vendor=root/"vendor";vendor.mkdir();operation=root/"operation";operation.mkdir()
            board._preserve_vendor_state(operation,vendor)
            receipt=json.loads((operation/"vendor-before"/"receipt.json").read_bytes())
            self.assertFalse(receipt["metadata_exists"]);self.assertTrue(receipt["global_state_absent"])
            self.assertFalse((operation/"vendor-before"/"_current_metadata.pkl").exists())
