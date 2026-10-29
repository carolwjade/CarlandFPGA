"""NEW feedback hook controls; synthetic board/source, no CPU/SSH/board operation."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_causal_pl_exchange as fixture
from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal
from competition.deepeye.tools.diagnostic import run_private_pl_live as host


class CausalFeedbackTests(unittest.TestCase):
    def test_selection_requires_same_explicit_root_profile_in_all_records(self):
        self.assertIn('_causal_feedback', __import__('inspect').signature(host.main).parameters)
        callback = lambda candidate: None
        profile = copy.deepcopy(causal.FEEDBACK_PROFILE)
        rows = [dict(candidate_feedback_profile=copy.deepcopy(profile)) for _ in range(3)]
        self.assertIs(causal.select_feedback_mode(*rows, callback, causal_mode=True), callback)
        self.assertIsNone(causal.select_feedback_mode({}, {}, {}, None, causal_mode=False))
        for index in range(3):
            bad = copy.deepcopy(rows); bad[index].clear()
            with self.assertRaises(ValueError):
                causal.select_feedback_mode(*bad, callback, causal_mode=True)
        for callback_value, mode in ((None, True), (callback, False), (42, True)):
            with self.assertRaises(ValueError):
                causal.select_feedback_mode(*rows, callback_value, causal_mode=mode)
        rows[2]['candidate_feedback_profile']['max_calls'] = 16.0
        with self.assertRaises(ValueError):
            causal.select_feedback_mode(*rows, callback, causal_mode=True)

    def test_returned_board_candidate_updates_next_source_and_is_detached(self):
        class ControlledPump(fixture.Pump):
            level = 0
            held_level = 0
            def poll(self):
                value = super().poll()
                if value is not None:
                    if value['adc_tick_ms'] % 50 == 0: self.held_level = self.level
                    value['channel_values'][1] = float(self.held_level)
                    value['channel_counts'][1] = 2048 if self.held_level == 0 else 3071
                return value
        with tempfile.TemporaryDirectory() as folder:
            channel, transport, _, clock = fixture.CausalExchangeTests().core(folder)
            source = ControlledPump(clock)
            seen = []
            def consume(candidate):
                index = len(seen)
                root = Path(folder)/'causal-exchange'
                intent = json.loads((root/('feedback-%02d-started.json' % index)).read_bytes())
                self.assertEqual('started_unknown_before_root_consumer', intent['state'])
                self.assertEqual(index+1, candidate['observation_identity']['request_seq'])
                self.assertFalse(candidate['diagnostic_flags']['CPU_completion_created'])
                self.assertNotIn('channel_values', candidate)
                seen.append(copy.deepcopy(candidate))
                candidate['channel_counts'][1] = 999
                source.level = 1
                # Advance only the controlled test schedule to next real EM slot.
                # Missing source slots remain honest gaps, never invented records.
                if index == 0:
                    clock.value = fixture.ORIGIN+((clock.value-fixture.ORIGIN)//50_000_000+1)*50_000_000
            result = causal._exchange_causal_core(channel, transport, source,
                clock=clock, origin_ns=fixture.ORIGIN, scans=2, out=folder,
                on_candidate=consume)
            self.assertEqual([2048, 3071], [row['channel_counts'][1] for row in seen])
            self.assertEqual([2048, 3071], [row['channel_counts'][1] for row in result['captures']])
            requests = [fixture.pl.decode(raw) for raw in transport.sent]
            self.assertEqual([2048, 3071], [row['values'][1] for row in requests])
            self.assertEqual(2, len(result['root_feedback_calls']))
            self.assertFalse(result['CPU_completion_created'])
            self.assertFalse(result['movement_authorized'])
            self.assertEqual(transport.closes, 1)

    def test_throwing_or_nonempty_consumer_is_never_retried(self):
        for mode in ('throw', 'result'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                channel, transport, source, clock = fixture.CausalExchangeTests().core(folder)
                calls = []
                def consume(candidate):
                    calls.append(candidate)
                    if mode == 'throw': raise RuntimeError('new consumer failed after possible action')
                    return {'movement_authorized': True}
                with self.assertRaises(RuntimeError if mode == 'throw' else ValueError):
                    causal._exchange_causal_core(channel, transport, source,
                        clock=clock, origin_ns=fixture.ORIGIN, scans=2, out=folder,
                        on_candidate=consume)
                root = Path(folder)/'causal-exchange'
                self.assertEqual(1, len(calls))
                self.assertEqual(1, len(transport.sent))
                self.assertTrue((root/'feedback-00-started.json').is_file())
                self.assertFalse((root/'feedback-00-returned.json').exists())
                self.assertTrue((root/'candidate-00.json').is_file())
                self.assertEqual(source.state, 'RETIRED')
                self.assertEqual(transport.closes, 1)

    def test_slow_final_consumer_cannot_turn_expired_session_into_success(self):
        with tempfile.TemporaryDirectory() as folder:
            channel, transport, source, clock = fixture.CausalExchangeTests().core(folder)
            def consume(candidate): clock.value = fixture.ORIGIN+10_000_000_001
            with self.assertRaises(TimeoutError):
                causal._exchange_causal_core(channel, transport, source,
                    clock=clock, origin_ns=fixture.ORIGIN, scans=1, out=folder,
                    on_candidate=consume)
            self.assertFalse((Path(folder)/'causal-exchange/HOST_CAUSAL_RESULT.json').exists())
            self.assertEqual(transport.closes, 1)

    def test_expired_session_never_starts_consumer_for_late_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            channel, transport, source, clock = fixture.CausalExchangeTests().core(folder)
            calls = []
            # Scale just the injected core session cap to exercise its ordering;
            # production policy and100ms source ledger are never changed.
            profile = dict(causal.SOURCE_PROFILE, session_max_ns=300_000_000)
            original_poll = transport.poll_line
            def late_return():
                raw, eof = original_poll()
                if raw is not None: clock.value += 400_000_000
                return raw, eof
            transport.poll_line = late_return
            with patch.object(causal, '_source_profile', return_value=profile):
                with self.assertRaises(TimeoutError):
                    causal._exchange_causal_core(channel, transport, source,
                        clock=clock, origin_ns=fixture.ORIGIN, scans=1, out=folder,
                        on_candidate=lambda candidate: calls.append(candidate))
            self.assertEqual([], calls)
            self.assertFalse((Path(folder)/'causal-exchange/feedback-00-started.json').exists())


if __name__ == '__main__': unittest.main()
