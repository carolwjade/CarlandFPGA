"""NEW review-derived controls; imports helpers without running the prior14."""
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_live_chain_candidate_channel import (CandidateChannelTests, Clock,
    ORIGIN, CTX, PROFILE, ready, sample, capture, pl)


class PreservationControls(unittest.TestCase):
    def channel(self):
        # Reuse component construction only; do not discover/run the old class.
        return CandidateChannelTests().channel()

    def test_held_em_expiry_is_checked_before_new_request_even_with_fresh_adc(self):
        channel, clock = self.channel()
        channel.admit_sample(sample())
        clock.tick(10); channel.admit_sample(sample(10))
        clock.value = ORIGIN + 100_000_001
        with self.assertRaises(ValueError): channel.next_request()
        self.assertEqual(channel.state, 'FAILED')
        self.assertEqual(channel._scans, 0)

    def test_held_em_exact100ms_may_reserve_but_capture_never_renews_that_age(self):
        channel, clock = self.channel()
        channel.admit_sample(sample())
        clock.tick(10); channel.admit_sample(sample(10))
        clock.value = ORIGIN + 100_000_000
        raw = channel.next_request()
        result = channel.accept_capture(pl.encode(capture(raw)))
        self.assertEqual(result['source_time']['adc_tick_ms'], 10)
        self.assertGreater(result['source_time']['em_source_age_ns'], 100_000_000)
        self.assertFalse(result['diagnostic_flags']['source_fresh_at_capture'])

    def test_bad_admission_bad_capture_and_clock_failure_preserve_pending_and_history(self):
        for fault in ('admission', 'capture', 'clock'):
            channel, clock = self.channel(); channel.admit_sample(sample())
            request = channel.next_request()
            history = channel.source_history()
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                if fault == 'admission':
                    bad = sample(10); bad['quality'] = True
                    channel.admit_sample(bad)
                elif fault == 'capture':
                    bad = capture(request); bad['captures'][0]['ack_returned'] = False
                    channel.accept_capture(pl.encode(bad))
                else:
                    clock.value = ORIGIN-1
                    channel.accept_capture(pl.encode(capture(request)))
            self.assertEqual(channel.state, 'FAILED')
            self.assertEqual(channel._pending.request_raw, request)
            self.assertEqual(channel.source_history(), history)
            self.assertEqual(channel._owner._pending[0], request)
            with self.assertRaises(ValueError): channel.next_request()
            with self.assertRaises(ValueError): channel.accept_capture(pl.encode(capture(request)))
            self.assertEqual(channel._pending.request_raw, request)

    def test_mutating_ready_return_and_history_export_cannot_change_owner_state(self):
        from competition.deepeye.simulation.authority import live_chain_channels as module
        clock = Clock()
        owner = pl._HostOwner(dict(CTX), clock, max_age_ns=2_000_000_000,
                              functional_timing_profile=dict(PROFILE))
        channel = module._CandidateChannel(owner, clock=clock,
            start_tick_ms=0, start_monotonic_ns=ORIGIN)
        exported = channel.accept_ready(ready())
        exported['baseline_counters'][0] = 999
        channel.admit_sample(sample())
        history = channel.source_history(); history[0]['adc_tick_ms'] = 999
        self.assertEqual(channel.source_history()[0]['adc_tick_ms'], 0)
        result = channel.accept_capture(pl.encode(capture(channel.next_request())))
        self.assertEqual(result['observation_identity']['request_seq'], 1)

    def test_actual_source_gaps_remain_in_history_and_do_not_create_fake_admissions(self):
        channel, clock = self.channel(); channel.admit_sample(sample())
        clock.tick(50); channel.admit_sample(sample(50))
        history = channel.source_history()
        self.assertEqual([r['adc_tick_ms'] for r in history], [0, 50])
        self.assertEqual([r['adc_gap_ms'] for r in history], [None, 50])
        self.assertEqual(len(history), 2)

    def test_cross_thread_request_cannot_acquire_or_move_pending_state(self):
        channel, clock = self.channel(); channel.admit_sample(sample())
        errors = []
        def other():
            try: channel.next_request()
            except ValueError as error: errors.append(str(error))
        thread = threading.Thread(target=other)
        thread.start(); thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertEqual(channel.state, 'FAILED')
        self.assertIsNone(channel._pending)
        self.assertEqual(channel._scans, 0)

    def test_source_history_fixed1001_cap_retains_all_actual_admissions(self):
        channel, clock = self.channel()
        for tick in range(0, 10010, 10):
            clock.tick(tick)
            payload = sample(tick)
            if tick >= 90:
                payload['channel_values'][3] = 0.
                payload['channel_counts'][3] = 0
                payload['quality'] |= 8
            channel.admit_sample(payload)
        self.assertEqual(len(channel.source_history()), 1001)
        clock.tick(10010)
        with self.assertRaises(ValueError): channel.admit_sample(sample(10010))
        self.assertEqual(channel.state, 'FAILED')
        self.assertEqual(len(channel.source_history()), 1001)


if __name__ == '__main__':
    unittest.main(defaultTest='PreservationControls', verbosity=2)
