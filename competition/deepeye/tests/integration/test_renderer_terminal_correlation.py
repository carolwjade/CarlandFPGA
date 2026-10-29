"""NEW terminal-correlation delta controls; no process/renderer adoption."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, 'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps')
from competition.deepeye.tools.diagnostic.renderer_session import RendererSession


class TerminalCorrelationTests(unittest.TestCase):
    def terminal(self, session, native_run):
        value = {'nonce': session.nonce, 'run_id': session.run_id, 'status': 'closed',
                 'last_sequence': 1, 'gates_closed': True, 'native': {
                 'run_id': native_run, 'authority_revision': 2, 'pose_revision': 1,
                 'position_m': [0, 0, 1], 'orientation_xyzw': [0, 0, 0, 1],
                 'stopped': True}}
        (session.path/'terminal.json').write_text(json.dumps(value), encoding='utf-8')
        return value

    def test_outer_match_cannot_hide_foreign_native_run_after_deadline(self):
        with tempfile.TemporaryDirectory() as folder:
            session = RendererSession(Path(folder)/'new-owner', 'run-1')
            self.terminal(session, 'foreign-run')
            session._deadline = 0  # Observation is allowed; foreign state is not.
            with self.assertRaisesRegex(ValueError, 'native run mismatch'):
                session.read_terminal()

    def test_correlated_terminal_remains_observable_after_send_deadline(self):
        with tempfile.TemporaryDirectory() as folder:
            session = RendererSession(Path(folder)/'new-owner', 'run-1')
            expected = self.terminal(session, 'run-1')
            session._deadline = 0
            self.assertEqual(expected, session.read_terminal())


if __name__ == '__main__': unittest.main()
