"""New OS-pipe receipt controls, not FPGA or source-timing acceptance."""
import binascii
import dataclasses
import importlib
import importlib.util
import json
import os
import struct
import tempfile
import threading
import time
import unittest

NAME = __package__ + '.live_board_receipts'
receipts = importlib.import_module(NAME) if importlib.util.find_spec(NAME) else None


def packet(kind=8, sequence=2, payload=None):
    if payload is None:
        payload = struct.pack('<IHhBBHHHBB', 7, 0, 0, 0, 0, 0, 0, 0, 2, 0)
    body = struct.pack('<2sBBBBHI', b'\xa5\x5a', 3, kind, len(payload), 2, sequence, 1234) + payload
    return body + struct.pack('<H', binascii.crc_hqx(body[2:], 0xffff))


class LiveBoardReceiptTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(receipts, 'new OS receipt provider not implemented')
        self.reader, self.writer = os.pipe()
        os.set_blocking(self.reader, False)
        self.ledger = receipts.ReceiptLedger(self.reader, receipts.CaptureIdentity(
            'new-operation', 'a' * 64, 'b' * 40, 'c' * 64, 1),
            max_bytes=8192, max_reads=20)
        self.addCleanup(self.ledger.close)
        self.addCleanup(os.close, self.reader)
        self.addCleanup(os.close, self.writer)

    def test_preserves_split_original_frame_and_unknown_availability(self):
        raw = packet()
        os.write(self.writer, b'noise' + raw[:9])
        self.assertEqual(self.ledger.read_once(), ())
        os.write(self.writer, raw[9:])
        event, = self.ledger.read_once()
        self.assertEqual(event.raw, raw)
        self.assertIsNone(event.availability_interval_ns)
        self.assertEqual(event.stream_start, 5)
        self.assertEqual(event.stream_end, 5 + len(raw))
        snapshot = self.ledger.snapshot()
        recovered = b''.join(bytes.fromhex(row['raw_hex']) for row in snapshot['reads'])
        self.assertEqual(recovered, b'noise' + raw)
        self.assertEqual([span['read_index'] for span in snapshot['frames'][0]['spans']], [0, 1])

    def test_empty_os_read_bounds_availability_without_claiming_sample_time(self):
        self.assertEqual(self.ledger.read_once(), ())
        before_write = time.monotonic_ns()
        os.write(self.writer, packet())
        event, = self.ledger.read_once()
        after_read = time.monotonic_ns()
        lo, hi = event.availability_interval_ns
        self.assertLessEqual(lo, before_write)
        self.assertLessEqual(before_write, hi)
        self.assertLessEqual(hi, after_read)
        row = self.ledger.snapshot()['frames'][0]
        self.assertIsNone(row['sample_interval_ns'])
        self.assertIsNone(row['physical_capture_record_sha256'])

    def test_recovers_original_good_packet_after_corrupt_and_coalesced_data(self):
        bad = bytearray(packet(sequence=1)); bad[-1] ^= 0x80
        good, second = packet(sequence=8), packet(sequence=9)
        os.write(self.writer, bytes(bad) + good + second)
        events = self.ledger.read_once()
        self.assertEqual([e.raw for e in events], [good, second])
        self.assertEqual(self.ledger.snapshot()['frames'][0]['stream_start'], len(bad))
        self.assertGreater(self.ledger.snapshot()['decoder']['rejected_candidates'], 0)

    def test_unknown_availability_cannot_be_promoted_to_board_envelope(self):
        os.write(self.writer, packet()); event, = self.ledger.read_once()
        with self.assertRaises(ValueError):
            self.ledger.claim_board_response(event, context=self.context())

    @staticmethod
    def context():
        return dict(session=7, config_epoch=2, boot_sha256='d'*64,
            transport_profile_id=1, source_id=4, topology_id=2, acquisition_profile_id=1)

    def test_original_event_only_and_one_claim_with_existing_validator(self):
        self.ledger.read_once(); os.write(self.writer, packet())
        event, = self.ledger.read_once()
        forged = dataclasses.replace(event)
        with self.assertRaises(ValueError):
            self.ledger.claim_board_response(forged, context=self.context())
        raw = self.ledger.claim_board_response(event, context=self.context())
        document = json.loads(raw)
        self.assertEqual(document['wire_frame_hex'], packet().hex())
        self.assertIsNone(document['physical_capture_record_sha256'])
        self.assertIsNone(document['timing_record_sha256'])
        with self.assertRaises(ValueError):
            self.ledger.claim_board_response(event, context=self.context())

    def test_invalid_state_session_and_telem_are_not_board_heartbeat(self):
        self.ledger.read_once()
        wrong_session = struct.pack('<IHhBBHHHBB', 8, 0, 0, 0, 0, 0, 0, 0, 2, 0)
        os.write(self.writer, packet(payload=wrong_session) + packet(kind=1))
        events = self.ledger.read_once()
        for event in events:
            with self.assertRaises(ValueError):
                self.ledger.claim_board_response(event, context=self.context())

    def test_budget_stops_before_an_extra_os_read_and_original_fd_survives_close(self):
        small = receipts.ReceiptLedger(self.reader, self.ledger.identity,
            max_bytes=3, max_reads=1, read_size=3)
        self.addCleanup(small.close)
        os.write(self.writer, b'abcdef')
        small.read_once()
        with self.assertRaises(ValueError): small.read_once()
        small.close()
        self.assertEqual(os.read(self.reader, 3), b'def')

    def test_regular_file_replay_is_refused_and_foreign_thread_cannot_read(self):
        with tempfile.TemporaryFile() as stream:
            with self.assertRaises(ValueError):
                receipts.ReceiptLedger(stream.fileno(), self.ledger.identity,
                    max_bytes=8192, max_reads=20)
        errors=[]
        def foreign():
            try: self.ledger.read_once()
            except ValueError as error: errors.append(error)
        thread=threading.Thread(target=foreign); thread.start(); thread.join()
        self.assertEqual(len(errors), 1)
        os.write(self.writer, packet())
        self.assertEqual(len(self.ledger.read_once()), 1)

    def test_snapshot_mutation_does_not_change_capture(self):
        os.write(self.writer, packet()); event, = self.ledger.read_once()
        snapshot=self.ledger.snapshot(); snapshot['reads'][0]['raw_hex']='00'
        self.assertEqual(bytes.fromhex(self.ledger.snapshot()['reads'][0]['raw_hex']), event.raw)

    def test_embedded_recovery_uses_original_packet_offset_and_counts_whole_read(self):
        small = receipts.ReceiptLedger(self.reader, self.ledger.identity,
            max_bytes=73, max_reads=5)
        self.addCleanup(small.close)
        raw = bytes.fromhex('a55a030c1b') + packet() + b'JUNK' + packet(sequence=3)
        self.assertEqual(len(raw), 73)
        os.write(self.writer, raw)
        events = small.read_once()
        self.assertEqual([(e.stream_start, e.stream_end) for e in events], [(5, 37), (41, 73)])
        self.assertEqual([e.raw for e in events], [packet(), packet(sequence=3)])
        self.assertEqual(small.snapshot()['bytes_read'], 73)
        os.write(self.writer, b'x')
        with self.assertRaises(ValueError): small.read_once()
        self.assertEqual(os.read(self.reader, 1), b'x')

    def test_delayed_recovery_cannot_borrow_later_empty_read_timing(self):
        os.write(self.writer, bytes.fromhex('a55a030c1b') + packet())
        self.assertEqual(self.ledger.read_once(), ())
        first_read = self.ledger.snapshot()['reads'][0]['read_call_interval_ns']
        self.assertEqual(self.ledger.read_once(), ())  # Real empty read AFTER the embedded packet.
        os.write(self.writer, b'JUNK')
        event, = self.ledger.read_once()
        self.assertEqual(event.raw, packet())
        self.assertEqual((event.stream_start, event.stream_end), (5, 37))
        self.assertIsNone(event.availability_interval_ns)
        self.assertLessEqual(first_read[1], self.ledger.snapshot()['reads'][1]['read_call_interval_ns'][0])


if __name__ == '__main__': unittest.main()
