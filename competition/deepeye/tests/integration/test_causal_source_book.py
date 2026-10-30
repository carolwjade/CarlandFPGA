"""NEW software pump/book ordering controls; no real kernel, engine or board."""
import unittest

from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal


class Profile:
    def __init__(self, events):
        self.events = events
        self.em_calls = self.adc_calls = 0
        self.failure = None

    def acquire_em(self, tick, pose, *, context, sampler):
        self.em_calls += 1
        self.events.append(('em', tick, pose, sampler(1., 2., 3.)))
        if self.failure is not None:
            raise self.failure

    def sample_adc(self, tick, *, contact_accel_g):
        self.adc_calls += 1
        self.events.append(('adc', tick))
        events = self.events
        class Sample:
            def to_payload(self):
                events.append(('payload', tick))
                return {'adc_tick_ms': tick}
        return Sample()


class Book:
    software_fixture_only = True
    def __init__(self, source, events):
        self.source, self.events = source, events
        self.clock = None
        self.failure = self.cleanup_failure = None
        self.on_open = None

    def start(self):
        if self.source.state != 'RUNNING':
            raise AssertionError('book started before original source')
        self.clock = self.source._clock
        self.events.append(('book_start', self.source._origin))

    def open_sample(self, tick, observed):
        if self.source._last_tick != tick or not self.source._polling:
            raise AssertionError('sample slot was not reserved')
        self.events.append(('open', tick, observed))
        if self.on_open:
            self.on_open()
        return ('token', tick)

    def read_pose(self, token, kind):
        self.events.append(('read_pose', kind, token[1]))
        return self.source._pose_reader()

    def begin_adc(self, token):
        self.events.append(('begin_adc', token[1]))
        return object()

    def end_adc(self, token, handle):
        self.events.append(('end_adc', token[1]))

    def finish_sample(self, token, payload):
        self.events.append(('finish', token[1], payload['adc_tick_ms']))
        if self.failure:
            raise self.failure

    def fail(self, reason):
        self.events.append(('book_failed',))
        if self.cleanup_failure:
            raise self.cleanup_failure

    def retire(self, reason):
        self.events.append(('book_retired', reason))


class CausalSourceBookTests(unittest.TestCase):
    def fixture(self):
        events, time = [], [1_234_567_890_000]
        profile = Profile(events)
        def pose():
            events.append(('original_pose',))
            return 'software-own-pose'
        source = causal._CausalSourcePump(profile, pose, lambda *args: .02)
        book = Book(source, events)
        bind = getattr(source, '_bind_software_source_book_for_test', None)
        self.assertTrue(callable(bind), 'software-only book seam missing')
        bind(book)
        source.start(time[0], lambda: time[0])
        return source, profile, book, events, time

    def test_nominal_slot_and_actual_instrument_call_order_are_distinct(self):
        source, profile, book, events, time = self.fixture()
        sampler, pose = source._sampler, source._pose_reader
        self.assertEqual({'adc_tick_ms': 0}, source.poll())
        self.assertEqual([('book_start', time[0]), ('open', 0, time[0]),
            ('read_pose', 'em', 0), ('original_pose',),
            ('em', 0, 'software-own-pose', .02),
            ('read_pose', 'adc', 0), ('original_pose',), ('begin_adc', 0),
            ('adc', 0), ('end_adc', 0), ('payload', 0), ('finish', 0, 0)], events)
        self.assertIs(sampler, source._sampler)
        self.assertIs(pose, source._pose_reader)

    def test_adc_only_slot_does_not_requery_or_relabel_em_pose(self):
        source, profile, book, events, time = self.fixture()
        source.poll(); events.clear(); time[0] += 10_700_000
        self.assertEqual({'adc_tick_ms': 10}, source.poll())
        self.assertEqual([('open', 10, time[0]), ('read_pose', 'adc', 10),
            ('original_pose',), ('begin_adc', 10), ('adc', 10),
            ('end_adc', 10), ('payload', 10), ('finish', 10, 10)], events)
        self.assertEqual((1, 2), (profile.em_calls, profile.adc_calls))

    def test_book_finish_failure_preserves_consumed_instrument_work(self):
        source, profile, book, events, time = self.fixture()
        failure = book.failure = RuntimeError('book completion failed')
        with self.assertRaises(RuntimeError) as caught:
            source.poll()
        self.assertIs(failure, caught.exception)
        self.assertEqual('FAILED', source.state)
        self.assertEqual((0, 1, 1, 1), (source._last_tick, source._count,
                                      profile.em_calls, profile.adc_calls))
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual((1, 1), (profile.em_calls, profile.adc_calls))

    def test_original_failure_stays_primary_when_book_failure_hook_raises(self):
        source, profile, book, events, time = self.fixture()
        primary = profile.failure = RuntimeError('original EM failure')
        book.cleanup_failure = OSError('secondary book failure')
        with self.assertRaises(RuntimeError) as caught:
            source.poll()
        self.assertIs(primary, caught.exception)
        self.assertEqual('FAILED', source.state)
        self.assertEqual(0, profile.adc_calls)
        self.assertTrue(getattr(primary, '_causal_exchange_secondary_errors', ()))

    def test_swallowed_reentry_during_book_open_cannot_reach_instrument(self):
        source, profile, book, events, time = self.fixture()
        def reenter():
            try: source.poll()
            except ValueError: pass
        book.on_open = reenter
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual('FAILED', source.state)
        self.assertEqual((0, 0), (profile.em_calls, profile.adc_calls))

    def test_retirement_is_forwarded_without_new_sample_or_world_cleanup(self):
        source, profile, book, events, time = self.fixture()
        source.retire('bounded original source finished')
        self.assertEqual(('book_retired', 'bounded original source finished'), events[-1])
        self.assertEqual('RETIRED', source.state)
        self.assertEqual((0, 0), (profile.em_calls, profile.adc_calls))

    def test_public_source_refuses_software_book_and_software_seam(self):
        source = causal.CausalSourcePump(lambda: None, lambda *args: .02)
        bind = getattr(source, 'bind_original_source_book', None)
        self.assertTrue(callable(bind), 'production-only book binding missing')
        with self.assertRaises(ValueError): bind(Book(source, []))
        self.assertEqual('FAILED', source.state)
        other = causal.CausalSourcePump(lambda: None, lambda *args: .02)
        bind = getattr(other, '_bind_software_source_book_for_test', None)
        self.assertTrue(callable(bind))
        with self.assertRaises(ValueError): bind(Book(other, []))

    def test_book_binding_cannot_restart_or_switch_source(self):
        source, profile, book, events, time = self.fixture()
        with self.assertRaises(ValueError):
            source._bind_software_source_book_for_test(book)
        self.assertEqual('FAILED', source.state)

    def test_profile_selection_is_exact_and_opt_in(self):
        select = getattr(causal, 'select_source_book_profile', None)
        self.assertTrue(callable(select), 'source book selector missing')
        self.assertFalse(select({}))
        self.assertTrue(select({'source_book_profile': {'name': 'root_original_source_time_book_v1'}}))
        for value in (None, True, {}, {'name': 'other'},
                      {'name': 'root_original_source_time_book_v1', 'clock': 'replacement'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select({'source_book_profile': value})


class CausalBookFailureRecordingTests(unittest.TestCase):
    def test_unprintable_secondary_cannot_replace_original_instrument_error(self):
        source, profile, book, events, time = CausalSourceBookTests.fixture(self)
        primary = profile.failure = RuntimeError('original instrument error')
        class Unprintable(Exception):
            def __str__(self):
                raise RuntimeError('secondary rendering failed')
        book.cleanup_failure = Unprintable()
        with self.assertRaises(RuntimeError) as caught:
            source.poll()
        self.assertIs(primary, caught.exception)
        self.assertEqual('FAILED', source.state)
        self.assertEqual(0, profile.adc_calls)


if __name__ == '__main__':
    unittest.main()
