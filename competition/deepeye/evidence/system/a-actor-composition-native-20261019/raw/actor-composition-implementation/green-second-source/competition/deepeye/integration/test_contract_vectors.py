"""Consume independently packed, saved ABI vectors and check field coverage."""
import json
from pathlib import Path
import unittest

import wire
import motion

PRODUCT = Path(__file__).resolve().parents[1]


class ContractVectorTests(unittest.TestCase):
    def test_layout_is_contiguous_and_matches_encoder(self):
        spec = json.loads((PRODUCT / 'docs/interface.json').read_bytes())
        self.assertEqual({x['type'] for x in spec['frames'].values()}, set(wire.PAYLOAD_LENGTHS))
        for name, entry in spec['frames'].items():
            with self.subTest(name=name):
                offset = 0
                for field in entry['fields']:
                    self.assertEqual(field['payload_offset'], offset)
                    offset += field['bytes']
                self.assertEqual(offset, entry['payload_bytes'])
                self.assertEqual(offset, wire.PAYLOAD_LENGTHS[entry['type']])
                self.assertEqual(offset + 14, entry['frame_bytes'])

    def test_saved_frames_and_corruption(self):
        vectors = json.loads((PRODUCT / 'tests/vectors/abi3_reference.json').read_bytes())
        self.assertEqual({x['type_id'] for x in vectors['valid_frames']}, set(wire.PAYLOAD_LENGTHS))
        for case in vectors['valid_frames']:
            with self.subTest(name=case['name']):
                expected = wire.Frame(case['type_id'], case['config_epoch'], case['sequence'],
                                      case['tick_ms'], bytes.fromhex(case['payload_hex']))
                raw = bytes.fromhex(case['frame_hex'])
                self.assertEqual(wire.decode(raw, allow_legacy_diagnostic=case['legacy_diagnostic']), expected)
                self.assertEqual(wire.encode(expected, allow_legacy_diagnostic=case['legacy_diagnostic']), raw)
        for case in vectors['invalid_frames']:
            with self.subTest(name=case['name']), self.assertRaises(ValueError):
                wire.decode(bytes.fromhex(case['frame_hex']))

    def test_saved_quantized_curvature_boundaries(self):
        vectors = json.loads((PRODUCT / 'tests/vectors/abi3_reference.json').read_bytes())
        for case in vectors['motion_vectors']:
            args = (case['profile'], case['speed_code'], case['yaw_q'], case['pitch_q'])
            with self.subTest(case=case):
                if case['accepted']:
                    motion.validate(*args)
                else:
                    with self.assertRaises(ValueError): motion.validate(*args)


if __name__ == '__main__': unittest.main()
