"""PC_DIRECT STATE 0x08 is a health/clock record, never motion evidence."""
import copy
import struct
import unittest

from test_host_envelope import CONTEXT, NOW_NS, encode, host_envelope, wire
from test_host_envelope import response_document, grant_document


PC = dict(CONTEXT, topology_id=2)


def heartbeat(**changes):
    fields = dict(session=PC['session'], last_control_seq=0, captured_yaw=0,
                  captured_speed=0, phase=0, remaining_ttl_ms=0, fault_flags=0,
                  capture_seq=0, control_epoch=PC['config_epoch'], capture_quality=0)
    fields.update(changes)
    payload = struct.pack('<IHhBBHHHBB', *fields.values())
    frame = wire.encode(wire.Frame(8, PC['config_epoch'], 42, 1000, payload))
    doc = response_document(frame)
    doc['context'] = copy.deepcopy(PC)
    return doc


def validate(doc, producer='hardware_bridge', consumer='world_authority'):
    return host_envelope.validate_message(encode(doc), producer=producer,
        consumer=consumer, context=PC, now_ns=NOW_NS)


class PcDirectHeartbeatTests(unittest.TestCase):
    def test_state8_reaches_authority_as_exact_32_byte_record(self):
        doc = heartbeat()
        record = validate(doc)
        self.assertEqual(len(bytes.fromhex(record.document['wire_frame_hex'])), 32)
        self.assertTrue(record.authority_only)
        self.assertEqual(record.kind, 'board_response')
        self.assertNotIn('observation', record.document)
        self.assertNotIn('deadline_monotonic_ns', record.document)

    def test_fault_is_transportable_for_authority_to_stop(self):
        self.assertEqual(validate(heartbeat(fault_flags=1, phase=4)).kind, 'board_response')

    def test_invalid_state_fields_are_rejected(self):
        for changes in ({'session': 8}, {'control_epoch': 3}, {'phase': 255},
                        {'fault_flags': 256}, {'capture_quality': 16}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(heartbeat(**changes))

    def test_crc_epoch_and_producer_are_checked(self):
        bad = heartbeat(); raw = bytearray.fromhex(bad['wire_frame_hex']); raw[-1] ^= 1
        bad['wire_frame_hex'] = raw.hex()
        with self.assertRaises(ValueError): validate(bad)
        bad = heartbeat(); frame = wire.decode(bytes.fromhex(bad['wire_frame_hex']))
        bad['wire_frame_hex'] = wire.encode(wire.Frame(8, 3, frame.sequence, frame.tick_ms, frame.payload)).hex()
        with self.assertRaises(ValueError): validate(bad)
        with self.assertRaises(ValueError): validate(heartbeat(), producer='ai_controller')

    def test_state8_cannot_be_routed_to_ai_or_claim_pc_board_motion_capture(self):
        with self.assertRaises(ValueError): validate(heartbeat(), consumer='ai_controller')
        doc = heartbeat(); doc['physical_capture_record_sha256'] = 'b' * 64
        with self.assertRaises(ValueError): validate(doc)
        doc = grant_document(context=PC, action_source='board_capture', capture_seq=42)
        with self.assertRaises(ValueError): validate(doc, producer='world_authority')


if __name__ == '__main__':
    unittest.main()
