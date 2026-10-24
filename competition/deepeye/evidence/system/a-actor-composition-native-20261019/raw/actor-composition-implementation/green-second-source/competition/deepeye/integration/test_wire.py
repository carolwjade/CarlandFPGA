"""Independent ABI3 wire vectors. No hardware or controller acceptance."""
import binascii
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

spec = importlib.util.spec_from_file_location('deepeye_wire', Path(__file__).with_name('wire.py'))
wire = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wire
spec.loader.exec_module(wire)


def reference_frame(kind=6, payload=b'\x04\x03\x02\x01', epoch=1, seq=0x1234, tick=0x12345678):
    body = bytes([3, kind, len(payload), epoch]) + struct.pack('<HI', seq, tick) + payload
    return b'\xa5\x5a' + body + struct.pack('<H', binascii.crc_hqx(body, 0xffff))


class WireTests(unittest.TestCase):
    def test_crc_independent_vectors(self):
        for data in (b'', b'123456789', bytes(range(256)), bytes(1024)):
            self.assertEqual(wire.crc16(data), binascii.crc_hqx(data, 0xffff))

    def test_exact_hello_frame(self):
        frame = wire.Frame(6, 1, 0x1234, 0x12345678, b'\x04\x03\x02\x01')
        self.assertEqual(wire.encode(frame), reference_frame())
        self.assertEqual(wire.decode(reference_frame()), frame)

    def test_all_fixed_lengths(self):
        lengths = {1:18, 2:6, 5:10, 6:4, 8:18, 9:18, 10:10, 11:18, 12:27, 13:27, 14:16, 15:20, 16:20}
        for kind, size in lengths.items():
            with self.subTest(kind=kind):
                blob = reference_frame(kind, bytes(size))
                self.assertEqual(wire.encode(wire.decode(blob)), blob)
                with self.assertRaises(ValueError):
                    wire.decode(reference_frame(kind, bytes(size-1)))

    def test_motion_signed_payload_is_preserved(self):
        payload = struct.pack('<IHBhhBHH', 1, 7, 2, -57, 40, 20, 12000, 6)
        frame = wire.decode(reference_frame(14, payload, seq=7))
        self.assertEqual(struct.unpack('<IHBhhBHH', frame.payload)[3:5], (-57,40))
        # Parsing bytes alone deliberately does not authorize this motion.

    def test_crc_version_magic_size_and_unknown_rejected(self):
        good = reference_frame()
        invalid = [good[:-1], good+b'\0', b'\0\0'+good[2:], good[:2]+b'\x02'+good[3:], reference_frame(0x77, b'')]
        for pos in range(2, len(good)):
            changed=bytearray(good); changed[pos]^=1; invalid.append(bytes(changed))
        for blob in invalid:
            with self.subTest(blob=blob.hex()), self.assertRaises(ValueError):
                wire.decode(blob)

    def test_legacy_is_explicit_diagnostic_only(self):
        for kind,size in ((3,14),(4,18)):
            blob=reference_frame(kind,bytes(size))
            with self.assertRaises(ValueError): wire.decode(blob)
            self.assertEqual(wire.decode(blob, allow_legacy_diagnostic=True).type_id,kind)

    def test_unfrozen_trace_rejected(self):
        with self.assertRaises(ValueError): wire.decode(reference_frame(7,bytes(32)))

    def test_integer_overflow_does_not_wrap(self):
        for frame in (wire.Frame(6,256,0,0,bytes(4)),wire.Frame(6,0,65536,0,bytes(4)),wire.Frame(6,0,0,2**32,bytes(4)),wire.Frame(6,0,-1,0,bytes(4))):
            with self.assertRaises(ValueError): wire.encode(frame)

    def test_every_chunk_boundary(self):
        blob=reference_frame(15,bytes(20))
        for split in range(len(blob)+1):
            decoder=wire.FrameDecoder()
            frames=decoder.feed(blob[:split])+decoder.feed(blob[split:])
            self.assertEqual(frames,[wire.decode(blob)])
            self.assertEqual(decoder.buffered_bytes,0)

    def test_bounded_resynchronization_and_embedded_magic(self):
        payload=b'\xa5\x5a'+bytes(18)
        good=reference_frame(15,payload)
        bad=bytearray(reference_frame()); bad[-1]^=0x80
        stream=b'noise\xa5'+bytes(bad)+b'\xa5\x5a\x03\x06\xff\0'+good+reference_frame()
        decoder=wire.FrameDecoder()
        output=[]
        for b in stream:
            output.extend(decoder.feed(bytes([b])))
            self.assertLessEqual(decoder.buffered_bytes,46)
        self.assertEqual([f.type_id for f in output],[15,6])
        self.assertGreater(decoder.rejected_candidates,0)

    def test_input_cap_preserves_partial_state(self):
        decoder=wire.FrameDecoder()
        decoder.feed(b'\xa5')
        with self.assertRaises(ValueError): decoder.feed(bytes(4097))
        self.assertEqual(decoder.buffered_bytes,1)


if __name__=='__main__': unittest.main(verbosity=2)
