"""NEW fixed-root software custody controls; no producer or native execution."""
import threading
import unittest
from dataclasses import replace
from competition.deepeye.tests.integration import test_root_source_book as fixtures

class FixedRootInterval(unittest.TestCase):
    setUp = fixtures.SourceBookTests.setUp
    start = fixtures.SourceBookTests.start
    open = fixtures.SourceBookTests.open
    complete = fixtures.SourceBookTests.complete

    def test_baseline_and_complete_sample_have_actual_closed_span(self):
        baseline = self.book.evidence()['fixed_root_interval']
        self.assertLessEqual(baseline['from_qpc_ns'], self.book.evidence()['baseline']['begin_qpc_ns'])
        self.start()
        self.complete()
        e = self.book.evidence(); s = e['samples'][0]; span = s['numerical_pose_span']
        self.assertLessEqual(span['from_qpc_ns'], s['nominal_qpc_ns'])
        for read in s['pose_reads'].values():
            self.assertLessEqual(span['from_qpc_ns'], read['begin_qpc_ns'])
            self.assertLessEqual(read['end_qpc_ns'], span['through_qpc_ns'])
        self.assertLessEqual(s['adc']['end_qpc_ns'], span['through_qpc_ns'])
        self.assertLessEqual(span['through_qpc_ns'], self.clock.now)
        self.assertFalse(e['native_interval_atomic'])
        self.assertEqual('unavailable;fixed_revision_only', e['action_association'])
        self.assertEqual('unavailable;original_native_em_association_not_implemented', s['held_em_association'])
        s['numerical_pose_span']['from_qpc_ns'] = -1
        self.assertGreaterEqual(self.book.evidence()['samples'][0]['numerical_pose_span']['from_qpc_ns'], 0)

    def test_current_view_is_actual_and_not_available_after_retire(self):
        self.start(); current = self.book.current_pose_interval()
        self.assertLessEqual(current['pose_read']['end_qpc_ns'], current['valid_span']['through_qpc_ns'])
        self.assertLessEqual(current['valid_span']['through_qpc_ns'], self.clock.now)
        self.book.retire('done'); calls = self.clock.calls
        with self.assertRaises(RuntimeError): self.book.current_pose_interval()
        self.assertEqual(calls, self.clock.calls)

    def test_new_root_same_pose_and_revoke_cannot_preserve_interval(self):
        self.start(); original = self.world.executor._root
        self.world.executor.revoke('stop')
        self.assertIsNot(original, self.world.executor._root)
        self.assertEqual(original.pose, self.world.executor._root.pose)
        calls = self.clock.calls
        with self.assertRaises(ValueError): self.book.current_pose_interval()
        self.assertEqual(calls, self.clock.calls)

    def test_backward_clock_and_veto_fail_closed(self):
        self.start(); self.clock.now -= 1
        with self.assertRaises(ValueError): self.book.current_pose_interval()
        self.setUp(); self.start(); self.world._vetoed = True; calls = self.clock.calls
        with self.assertRaises(ValueError): self.book.current_pose_interval()
        self.assertEqual(calls, self.clock.calls)

    def test_foreign_and_reentry_do_not_read_time(self):
        self.start(); calls = self.clock.calls; errors=[]
        def foreign():
            try: self.book.current_pose_interval()
            except RuntimeError as e: errors.append(str(e))
        t=threading.Thread(target=foreign); t.start(); t.join()
        self.assertTrue(errors); self.assertEqual(calls, self.clock.calls)
        self.setUp(); self.start(); self.book._busy=True; calls=self.clock.calls
        with self.assertRaises(RuntimeError): self.book.current_pose_interval()
        self.assertEqual(calls,self.clock.calls)

    def test_outside_nominal_is_explicitly_unavailable(self):
        self.start(); token=self.open(); self.book.read_pose(token,'em'); self.book.read_pose(token,'adc')
        h=self.book.begin_adc(token); self.source._profile._last_adc_tick=0; self.book.end_adc(token,h)
        token._draft['nominal_qpc_ns'] = self.book.evidence()['fixed_root_interval']['from_qpc_ns']-1
        self.book.finish_sample(token, fixtures.fault_payload(0))
        s=self.book.evidence()['samples'][0]
        self.assertIsNone(s['numerical_pose_span'])
        self.assertEqual('unavailable;nominal_or_actual_outside_fixed_root_span',s['numerical_pose_span_status'])

    def test_incomplete_sample_has_no_span_and_failed_current_no_time(self):
        self.start(); self.open(); self.book.fail('explicit'); calls=self.clock.calls
        with self.assertRaises(RuntimeError): self.book.current_pose_interval()
        self.assertEqual(calls,self.clock.calls)
        self.assertNotIn('numerical_pose_span',self.book.evidence()['partial_samples'][0])

if __name__ == '__main__': unittest.main()
