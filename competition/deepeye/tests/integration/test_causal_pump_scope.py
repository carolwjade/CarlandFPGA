"""New private software pump controls; no real field/kernel/native acquisition."""
import threading
import unittest

from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal


class Profile:
    def __init__(self, events, failure=None):
        self.events, self.failure = events, failure
        self.em_calls = self.adc_calls = 0

    def acquire_em(self, tick, pose, *, context, sampler):
        self.events.append(('em', tick, sampler(1., 2., 3.)))
        self.em_calls += 1  # Stand-in consumed random/filter work, never rollback.
        if self.failure:
            raise self.failure

    def sample_adc(self, tick, *, contact_accel_g):
        self.adc_calls += 1
        self.events.append(('adc', tick))
        return type('Sample', (), {'to_payload': lambda self: {'adc_tick_ms': tick}})()


class Scope:
    def __init__(self, factory):
        self.factory = factory

    def __enter__(self):
        self.factory.active = True
        self.factory.events.append(('enter',))
        return self

    def sampler(self, x, y, z):
        if not self.factory.active:
            raise AssertionError('scoped sampler escaped')
        return .04

    def __exit__(self, kind, error, traceback):
        self.factory.active = False
        self.factory.events.append(('exit',))
        if error is None and self.factory.exit_failure:
            raise self.factory.exit_failure
        return False


class Factory:
    software_fixture_only = True
    def __init__(self, source, events, exit_failure=None):
        self._source, self.events, self.exit_failure = source, events, exit_failure
        self.active = False

    def begin(self, tick):
        if self._source._last_tick != tick or self._source._count != 1:
            raise AssertionError('slot was not consumed before scope')
        self.events.append(('begin', tick))
        return Scope(self)


class CausalPumpScopeTests(unittest.TestCase):
    def fixture(self, failure=None, exit_failure=None):
        events = []
        profile = Profile(events, failure)
        def pose():
            events.append(('pose',))
            return 'software-pose'
        source = causal._CausalSourcePump(profile, pose, lambda *args: .02)
        factory = Factory(source, events, exit_failure)
        bind = getattr(source, '_bind_software_em_scope_for_test', None)
        self.assertTrue(callable(bind), 'private software scope seam missing')
        bind(factory)
        clock = lambda: 0
        source.start(0, clock)
        return source, profile, factory, events

    def test_scope_wraps_pose_and_em_but_original_sampler_identity_remains(self):
        source, profile, factory, events = self.fixture()
        original = source._sampler
        self.assertEqual({'adc_tick_ms': 0}, source.poll())
        self.assertEqual([('begin',0),('enter',),('pose',),('em',0,.04),
                          ('exit',),('adc',0)], events)
        self.assertIs(original, source._sampler)
        self.assertEqual('RUNNING', source.state)
        self.assertFalse(factory.active)

    def test_body_failure_consumes_slot_without_adc_or_replay(self):
        failure = RuntimeError('software body failure')
        source, profile, factory, events = self.fixture(failure=failure)
        with self.assertRaises(RuntimeError) as caught:
            source.poll()
        self.assertIs(failure, caught.exception)
        self.assertEqual('FAILED', source.state)
        self.assertEqual((0,1), (source._last_tick,source._count))
        self.assertEqual((1,0), (profile.em_calls,profile.adc_calls))
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual(1, profile.em_calls)

    def test_post_scope_failure_drops_payload_without_random_work_rollback(self):
        failure = RuntimeError('software post failure')
        source, profile, factory, events = self.fixture(exit_failure=failure)
        with self.assertRaises(RuntimeError) as caught:
            source.poll()
        self.assertIs(failure, caught.exception)
        self.assertEqual('FAILED', source.state)
        self.assertEqual((1,0), (profile.em_calls,profile.adc_calls))
        self.assertFalse(factory.active)

    def test_public_source_refuses_software_factory_without_native_adoption(self):
        source = causal.CausalSourcePump(lambda: None, lambda *args: .02)
        bind = getattr(source, 'bind_original_em_scope', None)
        self.assertTrue(callable(bind), 'original-only binding missing')
        with self.assertRaises(ValueError): bind(Factory(source, []))
        self.assertEqual('FAILED', source.state)

    def test_software_seam_refuses_public_source_and_late_rebind(self):
        public = causal.CausalSourcePump(lambda: None, lambda *args: .02)
        bind = getattr(public, '_bind_software_em_scope_for_test', None)
        self.assertTrue(callable(bind), 'software seam missing')
        with self.assertRaises(ValueError): bind(Factory(public, []))
        source, profile, factory, events = self.fixture()
        with self.assertRaises(ValueError): source._bind_software_em_scope_for_test(factory)
        self.assertEqual('FAILED', source.state)

    def test_scope_profile_is_exact_and_opt_in(self):
        select = getattr(causal, 'select_em_scope_profile', None)
        self.assertTrue(callable(select), 'hash-bound scope profile selector missing')
        self.assertFalse(select({}))
        self.assertTrue(select({'source_acquisition_profile': {'name':'root_original_em_scope_v1'}}))
        for value in (None, True, {}, {'name':'other'},
                      {'name':'root_original_em_scope_v1','timeout':2000}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select({'source_acquisition_profile':value})

    def test_reentered_poll_is_sticky_even_if_inner_error_is_swallowed(self):
        source, profile, factory, events = self.fixture()
        original = profile.acquire_em
        def reenter(*args, **kwargs):
            original(*args, **kwargs)
            try: source.poll()
            except ValueError: pass
        profile.acquire_em = reenter
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual('FAILED', source.state)
        self.assertEqual((1,0), (profile.em_calls,profile.adc_calls))

    def test_scope_profile_refuses_contact_callback_before_sampling(self):
        source, profile, factory, events = self.fixture()
        source._contact_reader = lambda tick: self.fail('unsupported contact callback ran')
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual('FAILED', source.state)
        self.assertEqual((0,0), (profile.em_calls,profile.adc_calls))

    def test_callback_retirement_cannot_return_an_adc_record(self):
        source, profile, factory, events = self.fixture()
        original = profile.acquire_em
        def retire(*args, **kwargs):
            original(*args, **kwargs)
            source.retire('software callback retired the source')
        profile.acquire_em = retire
        with self.assertRaises(ValueError): source.poll()
        self.assertEqual('FAILED', source.state)
        self.assertEqual((1,0), (profile.em_calls,profile.adc_calls))


if __name__ == '__main__':
    unittest.main()
