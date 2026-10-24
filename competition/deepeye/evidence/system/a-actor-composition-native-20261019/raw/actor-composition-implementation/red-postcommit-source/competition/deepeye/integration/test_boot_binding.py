"""Independent regressions for actual BOOT dependency binding and rolling IO."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import boot_profile as boot

PRODUCT = Path(__file__).resolve().parents[1]


class BootBindingTests(unittest.TestCase):
    def test_each_actual_protocol_file_changes_boot_identity(self):
        doc = boot.load_document(PRODUCT / 'docs/boot_profiles.json')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for _, rel in boot.RUNTIME_DIGEST_FILES:
                f = root / rel; f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PRODUCT / rel, f)
            original = boot.bind_software_documents(doc, root)
            self.assertFalse(original['hardware_enable_eligible'])
            self.assertEqual(boot.validate_document(original), [])
            self.assertEqual(boot.verify_software_bindings(original, root), [])
            for _, rel in boot.RUNTIME_DIGEST_FILES:
                f = root / rel; before = f.read_bytes()
                f.write_bytes(before + b'\n')
                try:
                    changed = boot.bind_software_documents(doc, root)
                    self.assertNotEqual(boot.canonical_sha256(original), boot.canonical_sha256(changed), rel)
                    self.assertTrue(boot.verify_software_bindings(original, root), rel)
                finally:
                    f.write_bytes(before)

    def test_changed_layout_disagrees_with_wire_and_cannot_bind(self):
        doc = boot.load_document(PRODUCT / 'docs/boot_profiles.json')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for _, rel in boot.RUNTIME_DIGEST_FILES:
                f = root / rel; f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PRODUCT / rel, f)
            p = root / 'docs/interface.json'; interface = json.loads(p.read_bytes())
            interface['frames']['STATE']['payload_bytes'] += 1
            p.write_text(json.dumps(interface), encoding='utf8')
            with self.assertRaises(boot.ProfileError): boot.bind_software_documents(doc, root)

    def test_sliding_window_counts_partial_frames(self):
        # 10 bytes/ms, a frame crossing the left edge contributes 5 bytes.
        segments = [{'start_ms': Fraction(0), 'end_ms': Fraction(2), 'bytes': 20},
                    {'start_ms': Fraction(3), 'end_ms': Fraction(4), 'bytes': 10}]
        self.assertEqual(boot.occupied_bytes(segments, Fraction(3, 2), Fraction(4)), Fraction(15))
        self.assertEqual(boot.occupied_bytes(segments, Fraction(2), Fraction(3)), 0)

    def test_boot_ack_matches_request_sequence_and_epoch_by_default(self):
        doc = boot.load_document(PRODUCT / 'docs/boot_profiles.json')
        request = boot.boot_frame(doc, 7, 45, config_epoch=2, sequence=100)
        for epoch, seq in [(3, 100), (2, 101)]:
            ack = boot.boot_ack_frame(doc, 7, 45, config_epoch=epoch, sequence=seq)
            self.assertFalse(boot.verify_boot_ack(request, ack)['ok'])

    def test_all_mode_directions_bytes_and_mixed_window_boundaries(self):
        doc = boot.load_document(PRODUCT / 'docs/boot_profiles.json')
        for profile in boot.PROFILE_NAMES:
            pc = boot.mode_segments(doc, profile, 'pc_direct_normal')
            self.assertEqual([x['frame'] for x in pc], ['EVENT', 'TELEM', 'STATE'])
            self.assertEqual(sum(x['bytes'] for x in pc), 84)
            self.assertTrue(all(x['direction'] == 'uplink' for x in pc))
            retry = boot.mode_segments(doc, profile, 'event_retry')[-1]
            self.assertEqual((retry['frame'], retry['direction']), ('EVENT', 'uplink'))
        proof = boot.verify_all_mode_schedules(doc)
        for item in proof['profiles'].values():
            self.assertEqual(item['mixed_triples_checked'], 216)
            self.assertEqual(item['maximum_sliding_byte_equivalents'], '214')


if __name__ == '__main__': unittest.main()
