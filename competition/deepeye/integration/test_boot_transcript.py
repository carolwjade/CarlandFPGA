"""New local OS-pipe BOOT controls; no board or authentication acceptance."""
import binascii
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from unittest.mock import patch

from . import boot_profile as boot
from .live_board_receipts import CaptureIdentity, ReceiptLedger

NAME = __package__ + '.boot_transcript'
transcript = importlib.import_module(NAME) if importlib.util.find_spec(NAME) else None
PROFILE = Path(__file__).resolve().parents[1] / 'docs/boot_profiles.json'


def ack_for(request, *, epoch=None, sequence=None, payload=None, tick=987654):
    """Independent CRC packet; never use host encoder for received ACK evidence."""
    _, _, _, _, req_epoch, req_seq, _ = struct.unpack('<2sBBBBHI', request[:12])
    data = request[12:-2] if payload is None else payload
    body = struct.pack('<2sBBBBHI', b'\xa5\x5a', 3, 13, len(data),
        req_epoch if epoch is None else epoch, req_seq if sequence is None else sequence, tick) + data
    return body + struct.pack('<H', binascii.crc_hqx(body[2:], 0xffff))


class BootTranscriptTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(transcript, 'new BOOT transcript not implemented')
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.instances = []
        self.out_reader, self.out_writer = os.pipe()
        self.in_reader, self.in_writer = os.pipe()
        for fd in (self.out_reader, self.in_reader):
            os.set_blocking(fd, False)
        for fd in (self.out_reader, self.out_writer, self.in_reader, self.in_writer):
            self.addCleanup(self.safe_close, fd)
        self.manifest = b'{"diagnostic":"opaque original main build manifest"}'
        self.identity = CaptureIdentity('boot-pipe-control', 'a'*64, 'b'*40,
            hashlib.sha256(self.manifest).hexdigest(), 1)
        self.ledger = ReceiptLedger(self.in_reader, self.identity, max_bytes=8192, max_reads=40)
        self.addCleanup(self.ledger.close)
        self.profile = boot.load_document(PROFILE)
        self.args = dict(identity=self.identity, profile=self.profile,
            profile_sha256=boot.canonical_sha256(self.profile).hex(),
            build_manifest=self.manifest, bit_sha256='d'*64, hwh_sha256='e'*64,
            session=777, mode=boot.compose_boot_mode('fast_9600', 'software_fixture', 'pc_direct'),
            config_epoch=2, sequence=123, tick_ms=345, max_ack_checks=12,
            journal_path=Path(self.directory.name)/'attempt.jsonl')

    def tearDown(self):
        destination = os.environ.get('BOOT_TRANSCRIPT_CONTROL_OUT')
        if destination and hasattr(self, 'instances'):
            output = Path(destination) / self._testMethodName
            output.mkdir(parents=True, exist_ok=False)
            for index, instance in enumerate(self.instances):
                (output / ('snapshot-%d.json' % index)).write_text(
                    json.dumps(instance.snapshot(), indent=2), encoding='utf-8')
            (output / 'receive-ledger.json').write_text(
                json.dumps(self.ledger.snapshot(), indent=2), encoding='utf-8')
            for journal in Path(self.directory.name).glob('*.jsonl'):
                (output / journal.name).write_bytes(journal.read_bytes())

    @staticmethod
    def safe_close(fd):
        try:
            os.close(fd)
        except OSError:
            pass

    def make(self, **changes):
        args = self.args | changes
        instance = transcript.BootTranscript(self.out_writer, self.ledger, **args)
        self.instances.append(instance)
        self.addCleanup(instance.close)
        return instance

    def receive(self, raw):
        os.write(self.in_writer, raw)
        return self.ledger.read_once()

    def test_actual_pipe_write_and_original_split_ack_match(self):
        tx = self.make()
        attempt = tx.send_once()
        request = os.read(self.out_reader, 4096)
        self.assertEqual(request.hex(), attempt['raw_hex'])
        self.assertEqual(attempt['outcome'], 'written')
        raw = ack_for(request)
        self.assertEqual(self.receive(b'noise' + raw[:8]), ())
        event, = self.receive(raw[8:])
        result = tx.check_ack(event)
        self.assertTrue(result['echo']['ok'])
        self.assertEqual(result['raw_hex'], raw.hex())
        self.assertIsNone(result['sample_interval_ns'])
        self.assertFalse(result['authenticated'])
        self.assertFalse(result['motion_authorized'])
        self.assertEqual(len(result['spans']), 2)
        self.assertIsNone(result['availability_interval_ns'])
        self.assertEqual(result['echo'], boot.verify_boot_ack(request, raw))
        with self.assertRaises(ValueError):
            tx.send_once()
        with self.assertRaises(ValueError):
            tx.check_ack(event)
        saved = [json.loads(x) for x in self.args['journal_path'].read_bytes().splitlines()]
        self.assertEqual([x['kind'] for x in saved], ['prepared', 'write_started', 'write_result', 'ack_check'])
        self.assertEqual(saved[0]['build_manifest_hex'], self.manifest.hex())
        self.assertEqual(saved[0]['profile_sha256'], self.args['profile_sha256'])
        self.assertEqual(saved[1]['outcome'], 'started_unknown')
        self.assertEqual(saved[2]['raw_hex'], request.hex())
        for start, end in (attempt['write_call_interval_ns'], result['read_call_intervals_ns'][0]):
            self.assertLessEqual(start, end)

    def test_frozen_echo_rejects_sequence_epoch_and_every_payload_field(self):
        tx = self.make(); tx.send_once()
        request = os.read(self.out_reader, 4096)
        cases = [('sequence', ack_for(request, sequence=124)),
                 ('config_epoch', ack_for(request, epoch=3))]
        for offset, label in [(0, 'session'), (4, 'mode'), (5, 'slot_profile_sha128'),
                              (21, 'guard_total_ms'), (23, 'primary_slot_ms'), (25, 'config_slot_ms')]:
            payload = bytearray(request[12:-2]); payload[offset] ^= 1 if offset != 4 else 3
            cases.append((label, ack_for(request, payload=bytes(payload))))
        for label, raw in cases:
            with self.subTest(field=label):
                event, = self.receive(raw)
                result = tx.check_ack(event)
                self.assertFalse(result['echo']['ok'])
                self.assertIn(label, result['echo']['mismatches'])

    def test_stale_copied_and_foreign_receipts_are_rejected(self):
        request = boot.boot_frame(self.profile, 777, self.args['mode'], 2, 123, 345)
        stale, = self.receive(ack_for(request))
        tx = self.make(); tx.send_once(); os.read(self.out_reader, 4096)
        with self.assertRaises(ValueError): tx.check_ack(stale)
        event, = self.receive(ack_for(request))
        with self.assertRaises(ValueError): tx.check_ack(dataclasses.replace(event))
        reader, writer = os.pipe()
        try:
            other = ReceiptLedger(reader, self.identity, max_bytes=4096, max_reads=2)
            try:
                os.write(writer, ack_for(request)); foreign, = other.read_once()
                with self.assertRaises(ValueError): tx.check_ack(foreign)
            finally:
                other.close()
        finally:
            os.close(reader); os.close(writer)
        self.assertTrue(tx.check_ack(event)['echo']['ok'])

    def test_partial_packet_started_before_write_cannot_be_fresh_ack(self):
        request = boot.boot_frame(self.profile, 777, self.args['mode'], 2, 123, 345)
        raw = ack_for(request)
        self.receive(raw[:8])
        tx = self.make(); tx.send_once(); os.read(self.out_reader, 4096)
        event, = self.receive(raw[8:])
        with self.assertRaises(ValueError): tx.check_ack(event)

    def test_close_only_owns_duplicate_and_snapshots_are_detached(self):
        tx = self.make(); tx.send_once(); os.read(self.out_reader, 4096)
        snap = tx.snapshot(); snap['attempt']['raw_hex'] = '00'
        snap['profile']['profiles'].clear()
        self.assertNotEqual(tx.snapshot()['attempt']['raw_hex'], '00')
        self.assertTrue(tx.snapshot()['profile']['profiles'])
        tx.close(); tx.close()
        os.write(self.out_writer, b'caller-lives')
        self.assertEqual(os.read(self.out_reader, 4096), b'caller-lives')
        with self.assertRaises(ValueError): tx.send_once()

    def test_real_broken_pipe_preserves_unknown_failure_without_retry(self):
        tx = self.make(); os.close(self.out_reader)
        with self.assertRaises(OSError): tx.send_once()
        attempt = tx.snapshot()['attempt']
        self.assertEqual(attempt['outcome'], 'write_error_unknown')
        self.assertIsNone(attempt['bytes_written'])
        self.assertTrue(attempt['error_type'])
        with self.assertRaises(ValueError): tx.send_once()

    def test_injected_short_write_uses_real_pipe_prefix_and_never_completes(self):
        tx = self.make(); actual_write = os.write
        def short(fd, raw):
            return actual_write(fd, raw[:9])
        with patch.object(transcript.os, 'write', short):
            attempt = tx.send_once()
        self.assertEqual(attempt['outcome'], 'partial_unknown')
        self.assertEqual(attempt['bytes_written'], 9)
        self.assertEqual(os.read(self.out_reader, 4096).hex(), attempt['raw_hex'][:18])
        with self.assertRaises(ValueError): tx.send_once()
        with self.assertRaises(ValueError): tx.check_ack(object())

    def test_injected_exception_after_real_write_is_unknown(self):
        for failure in (TimeoutError('injected after write'), KeyboardInterrupt()):
            with self.subTest(error=type(failure).__name__):
                tx = self.make(journal_path=Path(self.directory.name)/(type(failure).__name__+'.jsonl'))
                actual_write = os.write
                def unknown(fd, raw):
                    actual_write(fd, raw)
                    raise failure
                with patch.object(transcript.os, 'write', unknown):
                    with self.assertRaises(type(failure)): tx.send_once()
                attempt = tx.snapshot()['attempt']
                self.assertEqual(os.read(self.out_reader, 4096).hex(), attempt['raw_hex'])
                self.assertEqual(attempt['outcome'], 'write_error_unknown')
                with self.assertRaises(ValueError): tx.send_once()

    def test_existing_journal_including_crash_marker_never_reopens(self):
        self.args['journal_path'].write_text('{"kind":"write_started","outcome":"started_unknown"}\n')
        with self.assertRaises(FileExistsError): self.make()
        with self.assertRaises(BlockingIOError): os.read(self.out_reader, 1)

    def test_invalid_contracts_fail_before_write(self):
        cases = [dict(profile_sha256='f'*64), dict(build_manifest=b'wrong'),
                 dict(bit_sha256='D'*64), dict(hwh_sha256='e'*63), dict(session=True),
                 dict(config_epoch=256), dict(sequence=65536), dict(tick_ms=-1),
                 dict(mode=0), dict(max_ack_checks=True), dict(max_ack_checks=0),
                 dict(identity=dataclasses.replace(self.identity, connection_generation=2)),
                 dict(profile={'fake': True})]
        for change in cases:
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError): self.make(**change)
        with self.assertRaises(BlockingIOError): os.read(self.out_reader, 1)
        self.assertFalse(self.args['journal_path'].exists())

    def test_regular_file_descriptor_is_rejected(self):
        path = Path(self.directory.name)/'replay.bin'
        with path.open('w+b') as file:
            with self.assertRaises(ValueError):
                transcript.BootTranscript(file.fileno(), self.ledger, **self.args)

    def test_identity_change_before_send_is_rejected_without_write(self):
        tx = self.make()
        self.ledger.identity = dataclasses.replace(self.identity, connection_generation=2)
        with self.assertRaises(ValueError): tx.send_once()
        with self.assertRaises(BlockingIOError): os.read(self.out_reader, 1)

    def test_prequeued_unread_ack_remains_only_unauthenticated_diagnostic(self):
        expected = boot.boot_frame(self.profile, 777, self.args['mode'], 2, 123, 345)
        os.write(self.in_writer, ack_for(expected))
        tx = self.make(); tx.send_once(); os.read(self.out_reader, 4096)
        event, = self.ledger.read_once()
        result = tx.check_ack(event)
        self.assertTrue(result['echo']['ok'])
        self.assertFalse(result['authenticated'])
        self.assertFalse(result['motion_authorized'])
        self.assertIsNone(result['availability_interval_ns'])
        self.assertIsNone(result['sample_interval_ns'])

    def test_ack_check_budget_and_wrong_owner_are_bounded(self):
        tx = self.make(max_ack_checks=1); tx.send_once()
        request = os.read(self.out_reader, 4096)
        bad, = self.receive(ack_for(request, epoch=3))
        self.assertFalse(tx.check_ack(bad)['echo']['ok'])
        good, = self.receive(ack_for(request))
        with self.assertRaises(ValueError): tx.check_ack(good)
        errors = []
        def foreign_owner():
            for action in (tx.send_once, tx.snapshot, tx.close):
                try: action()
                except ValueError: errors.append('owner')
        worker = threading.Thread(target=foreign_owner); worker.start(); worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ['owner']*3)

    def test_journal_failure_before_os_write_is_terminal(self):
        tx = self.make()
        with patch.object(transcript.os, 'fsync', side_effect=OSError('injected fsync failure')):
            with self.assertRaises(OSError): tx.send_once()
        self.assertEqual(tx.snapshot()['attempt']['outcome'], 'journal_error_no_write')
        with self.assertRaises(BlockingIOError): os.read(self.out_reader, 1)
        with self.assertRaises(ValueError): tx.send_once()

    def test_journal_failure_after_os_write_preserves_attempt(self):
        tx = self.make(); actual_fsync = os.fsync; calls = []
        def fail_second(fd):
            calls.append(fd)
            if len(calls) == 2: raise OSError('injected result persistence failure')
            return actual_fsync(fd)
        with patch.object(transcript.os, 'fsync', fail_second):
            with self.assertRaises(OSError): tx.send_once()
        attempt = tx.snapshot()['attempt']
        self.assertEqual(os.read(self.out_reader, 4096).hex(), attempt['raw_hex'])
        self.assertEqual(attempt['outcome'], 'journal_error_after_write')
        self.assertEqual(attempt['bytes_written'], 41)
        with self.assertRaises(ValueError): tx.send_once()


if __name__ == '__main__':
    unittest.main()
