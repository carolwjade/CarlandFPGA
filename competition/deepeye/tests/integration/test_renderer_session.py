"""New bounded renderer-file transport tests; not control/source authentication."""
import importlib
import json
from pathlib import Path
import tempfile
import time
import unittest

try:
    adapter = importlib.import_module('competition.deepeye.tools.diagnostic.renderer_session')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.tools.diagnostic.renderer_session':
        raise
    adapter = None


def frame(revision=1):
    return {'run_id': 'run-1', 'authority_revision': revision,
            'pose_revision': revision, 'position_m': [0, 0, 1],
            'orientation_xyzw': [0, 0, 0, 1], 'stopped': False}


class RendererSessionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(adapter, 'renderer session adapter is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'owned'

    def session(self, **kw):
        return adapter.RendererSession(self.path, 'run-1', **kw)

    def ack(self, session, **change):
        doc = {'nonce': session.nonce, 'run_id': 'run-1', 'sequence': 1,
               'accepted': True, 'error': '', 'native': frame(), 'gates_closed': True}
        doc.update(change)
        (self.path / 'ack-000001.json').write_text(json.dumps(doc), encoding='utf-8')

    def test_new_directory_and_original_files_are_never_reused(self):
        s = self.session()
        before = (self.path / 'bootstrap.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.session()
        self.assertEqual(before, (self.path / 'bootstrap.json').read_bytes())
        self.assertEqual(32, len(s.nonce))

    def test_publish_is_complete_write_once_and_requires_one_ack(self):
        s = self.session()
        self.assertEqual(1, s.publish(frame()))
        raw = (self.path / 'frame-000001.json').read_bytes()
        message = json.loads(raw)
        self.assertEqual({'sequence', 'nonce', 'run_id', 'kind', 'frame'}, set(message))
        self.assertEqual(frame(), message['frame'])
        self.assertIsNone(s.read_ack())
        with self.assertRaises(RuntimeError):
            s.publish(frame(2))
        self.assertEqual(raw, (self.path / 'frame-000001.json').read_bytes())
        self.ack(s)
        self.assertTrue(s.read_ack()['accepted'])
        self.assertEqual(2, s.publish(frame(2)))
        self.assertEqual([], list(self.path.glob('*.tmp')))

    def test_bad_ack_is_retired_and_cannot_turn_into_a_motion_result(self):
        s = self.session()
        s.publish(frame())
        self.ack(s, nonce='0' * 32)
        with self.assertRaises(ValueError):
            s.read_ack()
        other = adapter.RendererSession(Path(self.temp.name) / 'oversize', 'run-1')
        other.publish(frame())
        (other.path / 'ack-000001.json').write_bytes(b' ' * 4097)
        with self.assertRaises(ValueError):
            other.read_ack()
        with self.assertRaises(RuntimeError):
            s.publish(frame(2))

    def test_whitelist_duplicate_json_and_oversize_ack_refused(self):
        s = self.session()
        with self.assertRaises(ValueError):
            s.publish(dict(frame(), seed=1))
        self.assertFalse((self.path / 'frame-000001.json').exists())
        s.publish(frame())
        (self.path / 'ack-000001.json').write_text('{"nonce":"a","nonce":"b"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            s.read_ack()

    def test_count_close_and_lifetime_are_bounded(self):
        with self.assertRaises(ValueError):
            self.session(max_messages=17)
        with self.assertRaises(ValueError):
            self.session(lifetime_ms=8001)
        s = self.session(max_messages=2)
        s.publish(frame())
        self.ack(s)
        s.read_ack()
        with self.assertRaises(RuntimeError):
            s.publish(frame(2))
        self.assertEqual(2, s.close())
        self.assertEqual('close', json.loads((self.path / 'frame-000002.json').read_text())['kind'])
        with self.assertRaises(RuntimeError):
            s.publish(frame(2))
        expired = adapter.RendererSession(Path(self.temp.name) / 'expired', 'run-1', lifetime_ms=1)
        time.sleep(0.01)
        with self.assertRaises(TimeoutError):
            expired.read_ready()

    def test_existing_target_refuses_overwrite_and_retires_unknown_publish(self):
        s = self.session()
        target = self.path / 'frame-000001.json'
        target.write_bytes(b'original unknown bytes')
        with self.assertRaises(FileExistsError):
            s.publish(frame())
        self.assertEqual(b'original unknown bytes', target.read_bytes())
        with self.assertRaises(RuntimeError):
            s.publish(frame())


if __name__ == '__main__':
    unittest.main()
