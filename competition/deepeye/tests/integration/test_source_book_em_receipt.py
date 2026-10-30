"""NEW scoped EM/held association software controls; no producer/model runs."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
import math
from competition.deepeye.tests.integration import test_root_source_book as fixtures
from competition.deepeye.tests.integration import test_causal_source_book as wiring
from competition.deepeye.simulation.authority import root_source_book as books
from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal


class ScopedEmReceiptTests(unittest.TestCase):
    def fixture(self, enabled=True):
        self.assertTrue(callable(getattr(books._SourceBookCore, 'begin_em', None)),
                        'original scoped EM call receipt has not been implemented')
        self.clock = fixtures.Clock(); self.world = fixtures.World(self.clock)
        self.world._status = dict(state='BOUND_STOPPED', identity=self.world._epoch.identity)
        self.field = OwnedWorldField(self.world.executor,
            material_sigma=dict(casing=None, fault=.02, void=None, water=.1, hard_rock=.01),
            background_sigma=.005, max_pieces=1)
        self.source = causal.CausalSourcePump(self.field.pose_reader, self.field.sample_sigma)
        self.factory = loop._make_software_em_scope_factory_for_test(
            self.world, self.world._binding, self.field, self.source)
        # Deliberately different software owner/factory/book, never a Root grant.
        self.source._em_scope_factory = self.factory
        self.book = books._software_source_book_for_test(
            self.world, self.world._binding, self.field, self.source,
            scoped_em_receipts=enabled)
        self.clock.now += 1000000
        self.source.start(self.clock.now, self.clock); self.book.start()

    def open(self, tick):
        self.clock.now = self.source._origin + tick * 1000000
        self.source._high = self.clock.now; self.source._last_tick = tick
        self.source._count += 1; self.source._polling = True
        return self.book.open_sample(tick, self.clock.now)

    def em(self, token, tick=0, success=True, mutate=False):
        with self.factory.begin(tick) as scope:
            self.book.read_pose(token, 'em')
            h = self.book.begin_em(token, scope)
            self.clock.now += 1000
            # Explicit unit-fixture progression. acquire_em is never executed.
            p = self.source._profile
            p._last_em_tick = p._em_attempt_tick = tick; p._em_attempt_ok = success
            if success:
                p._em_success_tick = tick; p._em_values = (0.0, 0.0, 0.0)
                p._em_saturated = (False, False, False)
            self.book.end_em(token, h)
            if mutate:
                self.world.executor._root = replace(self.world.executor._root, revision=1)
        self.book.close_em(token, h, scope)
        return h, scope

    def finish(self, token, tick, good=True, wrong=False):
        self.book.read_pose(token, 'adc'); h = self.book.begin_adc(token)
        self.clock.now += 1000; self.source._profile._last_adc_tick = tick
        self.book.end_adc(token, h)
        payload = fixtures.fault_payload(tick)
        if good:
            em_tick = self.source._profile._em_success_tick
            payload.update(em_tick_ms=em_tick, channel_values=[1.0 if wrong else 0.0, 0.0, 0.0, None],
                channel_counts=[round(((1.0 if wrong else 0.0)-math.log10(.2))/4*4095),
                    2048, 2048, None], quality=7+(0x700 if tick > em_tick else 0))
        self.book.finish_sample(token, payload); self.source._polling = False

    def test_actual_bracket_and_original_held_reference(self):
        self.fixture(); token = self.open(0); self.em(token); self.finish(token, 0)
        first = self.book.evidence()['samples'][0]['held_em_association']
        token = self.open(10); self.finish(token, 10)
        second = self.book.evidence()['samples'][1]['held_em_association']
        self.assertEqual(first['original_em'], second['original_em'])
        self.assertFalse(first['held']); self.assertTrue(second['held'])
        em = first['original_em']
        self.assertEqual(0, em['tick_ms']); self.assertEqual(1, em['source_count'])
        self.assertLessEqual(em['call']['begin_qpc_ns'], em['call']['end_qpc_ns'])
        self.assertLessEqual(em['call']['end_qpc_ns'], em['scope_closed_qpc_ns'])
        self.assertEqual('original_scoped_em_call_v1', em['kind'])
        self.assertFalse(first['native_interval_atomic'])
        self.assertEqual('unavailable;fixed_revision_only', self.book.evidence()['action_association'])
        second['original_em']['tick_ms'] = 999
        self.assertEqual(0, self.book.evidence()['samples'][1]['held_em_association']['original_em']['tick_ms'])

    def test_close_before_actual_scope_exit_refuses(self):
        self.fixture(); token = self.open(0)
        with self.assertRaises((ValueError, RuntimeError)):
            with self.factory.begin(0) as scope:
                self.book.read_pose(token, 'em'); h = self.book.begin_em(token, scope)
                self.book.close_em(token, h, scope)
        self.assertEqual('FAILED', self.book.evidence()['state'])

    def test_changed_root_cannot_close_receipt(self):
        self.fixture(); token = self.open(0)
        with self.assertRaises((ValueError, RuntimeError)):
            self.em(token, mutate=True)
        self.assertEqual([], self.book.evidence()['samples'])

    def test_second_call_end_is_refused(self):
        self.fixture(); token = self.open(0)
        with self.assertRaises((ValueError, RuntimeError)):
            h, _ = self.em(token); self.book.end_em(token, h)
        self.assertEqual('FAILED', self.book.evidence()['state'])

    def test_payload_cannot_relabel_original_em_values(self):
        self.fixture(); token = self.open(0); self.em(token); self.finish(token, 0)
        token = self.open(10)
        with self.assertRaises(ValueError): self.finish(token, 10, wrong=True)
        evidence = self.book.evidence()
        self.assertEqual(1, len(evidence['samples'])); self.assertEqual('FAILED', evidence['state'])

    def test_failed_em_attempt_remains_unavailable(self):
        self.fixture(); token = self.open(0); self.em(token, success=False)
        self.finish(token, 0, good=False)
        item = self.book.evidence()['samples'][0]
        self.assertFalse(item['em']['profile_attempt_ok'])
        self.assertIsInstance(item['held_em_association'], str)
        self.assertTrue(item['held_em_association'].startswith('unavailable;'))

    def test_foreign_scope_is_not_a_receipt(self):
        self.fixture(); token = self.open(0)
        with self.assertRaises(ValueError): self.book.begin_em(token, object())
        self.assertEqual('FAILED', self.book.evidence()['state'])

    def test_default_keeps_schema1_and_refuses_new_receipt_calls(self):
        self.fixture(enabled=False)
        self.assertEqual(1, self.book.evidence()['schema'])
        token = self.open(0)
        with self.assertRaises(ValueError): self.book.begin_em(token, object())

    def test_v2_plan_requires_actual_original_scope_selection(self):
        plan = {'source_book_profile':{'name':'root_original_source_time_book_em_receipts_v2'}}
        with self.assertRaises(ValueError): causal.select_source_book_profile(plan)
        plan['source_acquisition_profile'] = {'name':'root_original_em_scope_v1'}
        self.assertTrue(causal.select_source_book_profile(plan))

    def test_new_preconsumed_em_slot_is_refused(self):
        self.fixture(); token = self.open(0); self.source._profile._last_em_tick = 0
        with self.assertRaises((ValueError, RuntimeError)):
            with self.factory.begin(0) as scope:
                self.book.read_pose(token, 'em'); self.book.begin_em(token, scope)
        self.assertEqual([], self.book.evidence()['samples'])

    def test_new_missing_actual_profile_progression_is_refused(self):
        self.fixture(); token = self.open(0)
        with self.assertRaises((ValueError, RuntimeError)):
            with self.factory.begin(0) as scope:
                self.book.read_pose(token, 'em'); handle = self.book.begin_em(token, scope)
                self.book.end_em(token, handle)
        self.assertEqual('FAILED', self.book.evidence()['state'])

    def test_new_second_fresh_receipt_preserves_old_held_records(self):
        self.fixture()
        for tick in range(0, 70, 10):
            token = self.open(tick)
            if tick % 50 == 0: self.em(token, tick=tick)
            self.finish(token, tick)
        rows = self.book.evidence()['samples']
        self.assertEqual(0, rows[1]['held_em_association']['original_em']['tick_ms'])
        self.assertEqual(50, rows[6]['held_em_association']['original_em']['tick_ms'])
        self.assertEqual(6, rows[6]['held_em_association']['original_em']['source_count'])
        self.assertEqual(0, rows[5]['em']['previous_em_tick_ms'])


class PumpScopedReceiptOrdering(unittest.TestCase):
    def test_receipt_closes_after_scope_and_before_adc(self):
        events = []; time = [1234567890000]
        source = causal._CausalSourcePump(wiring.Profile(events), lambda: 'software-pose', lambda *a: .02)
        class Book(wiring.Book):
            scoped_em_receipts = True
            def begin_em(self, token, scope): events.append(('begin_em',)); return 'software-handle'
            def end_em(self, token, h): events.append(('end_em',))
            def close_em(self, token, h, scope):
                if not scope.closed: raise AssertionError('scope must really close first')
                events.append(('close_em',))
        class Scope:
            closed = False
            sampler = staticmethod(lambda *a: .02)
            def __enter__(self): events.append(('scope_enter',)); return self
            def __exit__(self, *a): self.closed = True; events.append(('scope_exit',))
        class Factory:
            software_fixture_only = True
            _source = source
            def begin(self, tick): return Scope()
        source._bind_software_em_scope_for_test(Factory())
        source._bind_software_source_book_for_test(Book(source, events))
        source.start(time[0], lambda: time[0]); source.poll()
        names = [e[0] for e in events]
        self.assertLess(names.index('begin_em'), names.index('em'))
        self.assertLess(names.index('em'), names.index('end_em'))
        self.assertLess(names.index('end_em'), names.index('scope_exit'))
        self.assertLess(names.index('scope_exit'), names.index('close_em'))
        self.assertLess(names.index('close_em'), names.index('adc'))


if __name__ == '__main__': unittest.main()
