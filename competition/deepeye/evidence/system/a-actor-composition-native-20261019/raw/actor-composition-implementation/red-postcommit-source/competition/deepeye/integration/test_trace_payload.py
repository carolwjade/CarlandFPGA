"""TRACE quarantine checks, not a codec or full R03 acceptance suite.

TRACE's inner payload has not been frozen. These tests exercise the existing
wire boundary: even a CRC-valid type-7 envelope must not become an observation.
They intentionally assign no offsets, enum values or Rice bitstream to TRACE.
"""
import binascii
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

spec = importlib.util.spec_from_file_location(
    'deepeye_trace_review_wire', Path(__file__).with_name('wire.py'))
wire = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wire
spec.loader.exec_module(wire)


def envelope(kind, payload=b'', *, declared_length=None, version=3):
    """Independent literal ABI3 header and stdlib CRC, never wire.encode."""
    length = len(payload) if declared_length is None else declared_length
    body = bytes([version, kind, length, 1, 0x34, 0x12,
                  0x78, 0x56, 0x34, 0x12]) + payload
    return b'\xa5\x5a' + body + struct.pack('<H', binascii.crc_hqx(body, 0xffff))


HELLO = envelope(6, b'\x04\x03\x02\x01')


class TraceQuarantineTests(unittest.TestCase):
    # Break caught: adding type 7 to the encoder/decoder allowlist without a
    # separately accepted payload contract, including via diagnostic mode.
    def test_encoder_rejects_all_in_budget_trace_lengths(self):
        for diagnostic in (False, True):
            for length in range(33):
                with self.subTest(diagnostic=diagnostic, length=length):
                    frame = wire.Frame(7, 1, 0x1234, 0x12345678, bytes(length))
                    with self.assertRaises(ValueError):
                        wire.encode(frame, allow_legacy_diagnostic=diagnostic)

    def test_crc_valid_trace_is_rejected_at_every_in_budget_length(self):
        for diagnostic in (False, True):
            for length in range(33):
                with self.subTest(diagnostic=diagnostic, length=length):
                    packet = envelope(7, bytes(length))
                    with self.assertRaises(ValueError):
                        wire.decode(packet, allow_legacy_diagnostic=diagnostic)

    # Break caught: a newly accepted TRACE leaking into streaming consumers,
    # or an unknown candidate eating valid subsequent frames after chunking.
    def test_stream_recovers_at_every_split_without_delivering_trace(self):
        for diagnostic in (False, True):
            stream = HELLO + envelope(7, b'\x11' * 32) + HELLO
            for split in range(len(stream) + 1):
                with self.subTest(diagnostic=diagnostic, split=split):
                    decoder = wire.FrameDecoder(allow_legacy_diagnostic=diagnostic)
                    found = decoder.feed(stream[:split]) + decoder.feed(stream[split:])
                    self.assertEqual([f.type_id for f in found], [6, 6])
                    self.assertEqual([f.payload for f in found],
                                     [b'\x04\x03\x02\x01'] * 2)
                    self.assertEqual(decoder.buffered_bytes, 0)

    # Break caught: an unknown type's oversized length blocking a good frame
    # while waiting for a body that cannot belong to the frozen wire contract.
    def test_trace_declared_length_does_not_block_a_following_hello(self):
        for length in (0, 1, 32, 33, 255):
            with self.subTest(length=length):
                decoder = wire.FrameDecoder()
                header_only = bytes([0xa5, 0x5a, 3, 7, length])
                found = decoder.feed(header_only + HELLO)
                self.assertEqual([f.type_id for f in found], [6])
                self.assertEqual(decoder.buffered_bytes, 0)

    # Break caught: corrupted/old-ABI TRACE or partial magic poisoning bounded
    # byte-at-a-time resynchronization; no inner codec semantics are assumed.
    def test_corrupt_old_and_magic_rich_trace_remain_bounded(self):
        bad_crc = bytearray(envelope(7, b'\x11' * 32))
        bad_crc[-1] ^= 1
        nested_magic = envelope(7, b'\xa5\x5a\x03\x07' * 8)
        stream = (bytes(bad_crc) + envelope(7, b'\x11' * 32, version=2)
                  + nested_magic + HELLO)
        decoder = wire.FrameDecoder()
        found = []
        for byte in stream:
            found.extend(decoder.feed(bytes([byte])))
            self.assertLessEqual(decoder.buffered_bytes, 46)
        self.assertEqual([f.type_id for f in found], [6])
        self.assertEqual(decoder.buffered_bytes, 0)

    # Break caught: repeated unknown candidates accumulating unbounded state
    # or emitting observations despite the absent codec contract.
    def test_repeated_trace_cannot_grow_storage_or_create_observations(self):
        decoder = wire.FrameDecoder()
        for _ in range(256):
            self.assertEqual(decoder.feed(envelope(7, b'\x11' * 32)), [])
            self.assertLessEqual(decoder.buffered_bytes, 46)
        found = decoder.feed(HELLO)
        self.assertEqual([f.type_id for f in found], [6])
        self.assertEqual(decoder.buffered_bytes, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
