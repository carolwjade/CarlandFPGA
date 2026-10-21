"""New private byte framing contract; no actor, clock or endpoint authority."""
import ast
import importlib
from pathlib import Path
import unittest

NAME = 'competition.deepeye.simulation.isolation.ipc_framing'
try:
    framing = importlib.import_module(NAME)
except ModuleNotFoundError as exc:
    if exc.name != NAME:
        raise
    framing = None


class IpcFramingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(framing, 'bounded byte framing has not been implemented')

    def assert_retired(self, decoder):
        for call in (lambda: decoder.feed(b''),
                     lambda: decoder.feed(b'\x01\x00\x00\x00a'), decoder.finish):
            with self.assertRaises(ValueError):
                call()

    def test_every_split_and_one_byte_feeds(self):
        raw = b'\x03\x00\x00\x00abc'
        self.assertEqual(framing.encode_frame(b'abc'), raw)
        for split in range(len(raw) + 1):
            with self.subTest(split=split):
                decoder = framing.FrameDecoder()
                self.assertEqual(decoder.feed(raw[:split]) + decoder.feed(raw[split:]), (b'abc',))
                decoder.finish()
                self.assert_retired(decoder)
        decoder = framing.FrameDecoder()
        out = ()
        for value in raw:
            out += decoder.feed(bytes([value]))
        self.assertEqual(out, (b'abc',))
        decoder.finish()

    def test_binary_coalescing_order_and_empty_feed(self):
        decoder = framing.FrameDecoder()
        self.assertEqual(decoder.feed(b''), ())
        out = decoder.feed(b'\x03\x00\x00\x00\x00\xff\n\x01\x00\x00\x00z')
        self.assertEqual(out, (b'\x00\xff\n', b'z'))
        self.assertTrue(all(type(item) is bytes for item in out))
        self.assertEqual(decoder.feed(b''), ())
        decoder.finish()

    def test_maximum_payload_fragmented(self):
        payload = bytes(range(256)) * 64
        raw = framing.encode_frame(payload)
        self.assertEqual(raw[:4], b'\x00\x40\x00\x00')
        decoder = framing.FrameDecoder()
        self.assertEqual(decoder.feed(raw[:8192]), ())
        self.assertEqual(decoder.feed(raw[8192:16384]), ())
        self.assertEqual(decoder.feed(raw[16384:]), (payload,))
        decoder.finish()

    def test_illegal_length_retires_at_header(self):
        for value in (0, 16385, 0xffffffff):
            with self.subTest(length=value):
                decoder = framing.FrameDecoder()
                self.assertEqual(decoder.feed(value.to_bytes(4, 'little')[:3]), ())
                with self.assertRaises(ValueError):
                    decoder.feed(value.to_bytes(4, 'little')[3:])
                self.assert_retired(decoder)

    def test_chunk_limit_rejects_even_after_valid_partial(self):
        decoder = framing.FrameDecoder()
        decoder.feed(b'\x05\x00\x00\x00a')
        with self.assertRaises(ValueError):
            decoder.feed(b'x' * 8193)
        self.assert_retired(decoder)

    def test_per_call_frame_limit_and_no_partial_return(self):
        frame = b'\x01\x00\x00\x00q'
        decoder = framing.FrameDecoder()
        self.assertEqual(decoder.feed(frame * 4), (b'q',) * 4)
        self.assertEqual(decoder.feed(frame), (b'q',))
        decoder.finish()
        decoder = framing.FrameDecoder()
        self.assertEqual(decoder.feed(frame), (b'q',))
        with self.assertRaises(ValueError):
            decoder.feed(frame * 5)
        self.assert_retired(decoder)
        decoder = framing.FrameDecoder()
        with self.assertRaises(ValueError):
            decoder.feed(frame + b'\x00\x00\x00\x00')
        self.assert_retired(decoder)

    def test_truncated_eof_retires_and_boundary_eof_closes(self):
        for raw in (b'\x03', b'\x03\x00', b'\x03\x00\x00',
                    b'\x03\x00\x00\x00', b'\x03\x00\x00\x00ab'):
            with self.subTest(raw=raw):
                decoder = framing.FrameDecoder()
                self.assertEqual(decoder.feed(raw), ())
                with self.assertRaises(ValueError):
                    decoder.finish()
                self.assert_retired(decoder)
        decoder = framing.FrameDecoder()
        decoder.finish()
        self.assert_retired(decoder)

    def test_only_exact_bytes_and_payload_bounds(self):
        class Bytes(bytes):
            pass
        for invalid in (None, True, 'abc', bytearray(b'abc'), memoryview(b'abc'), Bytes(b'abc')):
            with self.subTest(type=type(invalid).__name__):
                with self.assertRaises(ValueError):
                    framing.encode_frame(invalid)
                decoder = framing.FrameDecoder()
                with self.assertRaises(ValueError):
                    decoder.feed(invalid)
                self.assert_retired(decoder)
        for invalid in (b'', b'x' * 16385):
            with self.assertRaises(ValueError):
                framing.encode_frame(invalid)

    def test_no_provider_or_io_imports(self):
        tree = ast.parse(Path(framing.__file__).read_text(encoding='utf-8'))
        imports = [item for item in ast.walk(tree) if isinstance(item, (ast.Import, ast.ImportFrom))]
        self.assertEqual(imports, [])


if __name__ == '__main__':
    unittest.main()
