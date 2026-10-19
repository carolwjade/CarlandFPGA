"""Fault injection at the trusted-owner cleanup boundary; no OS fixtures."""
from dataclasses import FrozenInstanceError
import unittest

try:
    from simulation.isolation import resource_cleanup as rc
except ImportError:
    rc = None


class FakeBackend:
    def __init__(self, outcomes=None):
        self.outcomes = outcomes or {}
        self.calls = []
        self.hook = None

    def call(self, action, resource):
        self.calls.append((action, resource.resource_id, resource.identity))
        if self.hook:
            self.hook(action, resource)
        value = self.outcomes.get((action, resource.resource_id),
                                  True if action == 'wait_terminal' else rc.Outcome.CONFIRMED)
        if isinstance(value, BaseException):
            raise value
        return value

    def terminate(self, resource):
        return self.call('terminate', resource)

    def wait_terminal(self, resource):
        return self.call('wait_terminal', resource)

    def close(self, resource):
        return self.call('close', resource)

    def remove_profile(self, resource):
        return self.call('remove_profile', resource)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rc, 'resource-cleanup coordinator has not been implemented')
        self.provenance = rc.Provenance('task/v1', 'work', 'owner', (('launcher', 'a' * 64),))
        self.identities = {name: object() for name in ('child', 'control', 'fixture', 'thread', 'socket', 'profile')}
        self.plan = (
            rc.Resource('child', 'owner', 'process', self.identities['child'], profile_id='profile'),
            rc.Resource('control', 'owner', 'handle', self.identities['control'], profile_id='profile', recovery_for=('child',)),
            rc.Resource('fixture', 'owner', 'handle', self.identities['fixture'], profile_id='profile'),
            rc.Resource('thread', 'owner', 'thread', self.identities['thread'], profile_id='profile'),
            rc.Resource('socket', 'owner', 'socket', self.identities['socket'], profile_id='profile'),
            rc.Resource('profile', 'owner', 'profile', self.identities['profile']),
        )

    def coordinator(self, outcomes=None, sink=None, plan=None):
        self.backend = FakeBackend(outcomes)
        self.events = []
        return rc.CleanupCoordinator(self.provenance, self.plan if plan is None else plan,
                                     self.backend, self.events.append if sink is None else sink)

    def calls(self):
        return [(action, name) for action, name, _ in self.backend.calls]

    def test_success_closes_exact_owned_identities_before_profile_removal(self):
        result = self.coordinator().cleanup()
        self.assertEqual(self.calls(), [('terminate', 'child'), ('wait_terminal', 'child'), ('close', 'child'),
                                       ('close', 'control'), ('close', 'fixture'), ('close', 'thread'),
                                       ('close', 'socket'), ('remove_profile', 'profile')])
        for _, name, identity in self.backend.calls:
            self.assertIs(identity, self.identities[name])
        self.assertTrue(result.resources_complete)
        self.assertTrue(result.evidence_complete)
        self.assertTrue(result.success)
        self.assertEqual(result.unresolved, ())
        self.assertEqual([event.sequence for event in self.events], list(range(1, len(self.events) + 1)))

    def test_each_sink_boundary_failure_cannot_skip_any_safe_action(self):
        self.coordinator().cleanup()
        count = len(self.events)
        for fail_at in range(1, count + 1):
            with self.subTest(fail_at=fail_at):
                seen = []
                def sink(event):
                    seen.append(event)
                    if len(seen) == fail_at:
                        raise OSError('fsync failed')
                result = self.coordinator(sink=sink).cleanup()
                self.assertEqual(self.calls(), [('terminate', 'child'), ('wait_terminal', 'child'), ('close', 'child'),
                                               ('close', 'control'), ('close', 'fixture'), ('close', 'thread'),
                                               ('close', 'socket'), ('remove_profile', 'profile')])
                self.assertTrue(result.resources_complete)
                self.assertFalse(result.evidence_complete)
                self.assertFalse(result.success)
                self.assertEqual(len(result.audit_errors), 1)
                self.assertEqual(len(seen), count)

    def test_serialization_failure_every_time_retains_primary_and_all_audit_errors(self):
        def broken_sink(event):
            raise ValueError('serialize failed')
        original = RuntimeError('original model failure')
        result = self.coordinator(sink=broken_sink).cleanup(original)
        self.assertEqual(result.primary_error.type_name, 'RuntimeError')
        self.assertEqual(result.primary_error.message, 'original model failure')
        self.assertTrue(result.resources_complete)
        self.assertFalse(result.evidence_complete)
        self.assertGreater(len(result.audit_errors), 8)
        self.assertEqual(self.calls()[-1], ('remove_profile', 'profile'))

    def test_terminate_failure_does_not_skip_terminal_readback_or_safe_closes(self):
        result = self.coordinator({('terminate', 'child'): OSError('terminate raised')}).cleanup()
        self.assertEqual(self.calls()[:3], [('terminate', 'child'), ('wait_terminal', 'child'), ('close', 'child')])
        self.assertTrue(result.resources_complete)
        self.assertFalse(result.success)
        self.assertEqual(result.resources[0].operations[0].outcome, rc.Outcome.UNKNOWN)
        self.assertTrue(result.resources[0].terminal_confirmed)
        self.assertEqual(result.cleanup_errors[0].message, 'terminate raised')

    def test_nonterminal_readback_preserves_process_and_recovery_handle(self):
        for termination in (rc.Outcome.FAILED, rc.Outcome.UNKNOWN, OSError('terminate failed')):
            with self.subTest(termination=termination):
                result = self.coordinator({('terminate', 'child'): termination, ('wait_terminal', 'child'): False}).cleanup()
                self.assertEqual(self.calls(), [('terminate', 'child'), ('wait_terminal', 'child'),
                                               ('close', 'fixture'), ('close', 'thread'), ('close', 'socket')])
                self.assertEqual(result.unresolved, ('child', 'control', 'profile'))
                self.assertFalse(result.resources_complete)

    def test_wait_exception_or_unknown_or_malformed_is_never_terminal_confirmation(self):
        for value in (OSError('wait failed'), None, 1, 'terminal'):
            with self.subTest(value=value):
                result = self.coordinator({('wait_terminal', 'child'): value}).cleanup()
                self.assertEqual(result.unresolved, ('child', 'control', 'profile'))
                self.assertNotIn(('close', 'child'), self.calls())
                self.assertNotIn(('close', 'control'), self.calls())
                self.assertIn(('close', 'socket'), self.calls())

    def test_close_failed_unknown_exception_and_malformed_retain_ownership_and_gate_profile(self):
        for value in (rc.Outcome.FAILED, rc.Outcome.UNKNOWN, OSError('close failed'), True, None):
            with self.subTest(value=value):
                result = self.coordinator({('close', 'fixture'): value}).cleanup()
                self.assertEqual(result.unresolved, ('fixture', 'profile'))
                self.assertEqual(self.calls()[-1], ('close', 'socket'))
                self.assertFalse(result.resources_complete)

    def test_failed_process_handle_close_blocks_profile_but_not_other_closes(self):
        result = self.coordinator({('close', 'child'): rc.Outcome.UNKNOWN}).cleanup()
        self.assertEqual(result.unresolved, ('child', 'profile'))
        self.assertIn(('close', 'control'), self.calls())
        self.assertIn(('close', 'socket'), self.calls())
        self.assertNotIn(('remove_profile', 'profile'), self.calls())

    def test_mixed_cleanup_and_sink_errors_preserve_all_failures_and_later_closes(self):
        def sink(event):
            raise OSError('audit failed')
        result = self.coordinator({('close', 'fixture'): OSError('fixture failure'),
                                   ('close', 'thread'): rc.Outcome.UNKNOWN}, sink).cleanup(ValueError('primary'))
        self.assertEqual(result.primary_error.message, 'primary')
        self.assertEqual(result.unresolved, ('fixture', 'thread', 'profile'))
        self.assertEqual(len(result.cleanup_errors), 2)
        self.assertGreater(len(result.audit_errors), 0)
        self.assertIn(('close', 'socket'), self.calls())

    def test_profile_delete_unknown_is_retained_and_never_replayed(self):
        for value in (rc.Outcome.UNKNOWN, rc.Outcome.FAILED, OSError('delete uncertain')):
            with self.subTest(value=value):
                coordinator = self.coordinator({('remove_profile', 'profile'): value})
                result = coordinator.cleanup()
                self.assertEqual(result.unresolved, ('profile',))
                before = list(self.backend.calls)
                with self.assertRaises(rc.CleanupRejected):
                    coordinator.cleanup()
                self.assertEqual(self.backend.calls, before)

    def test_completed_cleanup_is_not_replayed(self):
        coordinator = self.coordinator()
        coordinator.cleanup()
        before = list(self.backend.calls)
        with self.assertRaises(rc.CleanupRejected):
            coordinator.cleanup()
        self.assertEqual(self.backend.calls, before)

    def test_unknown_close_is_not_replayed_even_when_new_sink_is_healthy(self):
        coordinator = self.coordinator({('close', 'socket'): rc.Outcome.UNKNOWN})
        coordinator.cleanup()
        with self.assertRaises(rc.CleanupRejected):
            coordinator.cleanup()
        self.assertEqual(self.calls().count(('close', 'socket')), 1)

    def test_backend_reentry_is_rejected_without_disrupting_outer_cleanup(self):
        coordinator = self.coordinator()
        rejected = []
        def reenter(action, resource):
            try:
                coordinator.cleanup()
            except rc.CleanupRejected:
                rejected.append((action, resource.resource_id))
        self.backend.hook = reenter
        self.assertTrue(coordinator.cleanup().success)
        self.assertEqual(len(rejected), 8)

    def test_sink_reentry_is_rejected_and_cannot_replace_original_failure(self):
        def sink(event):
            with self.assertRaises(rc.CleanupRejected):
                coordinator.cleanup(RuntimeError('replacement'))
        coordinator = self.coordinator(sink=sink)
        result = coordinator.cleanup(ValueError('original'))
        self.assertEqual(result.primary_error.message, 'original')
        self.assertTrue(result.resources_complete)
        self.assertFalse(result.success)

    def test_profile_gates_are_independent_and_do_not_remove_unresolved_profile(self):
        plan = self.plan + (rc.Resource('other-profile', 'owner', 'profile', object()),)
        result = self.coordinator({('close', 'socket'): rc.Outcome.UNKNOWN}, plan=plan).cleanup()
        self.assertEqual(result.unresolved, ('socket', 'profile'))
        self.assertIn(('remove_profile', 'other-profile'), self.calls())
        self.assertNotIn(('remove_profile', 'profile'), self.calls())

    def test_invalid_plan_is_rejected_before_any_callbacks(self):
        invalid = [self.plan + (self.plan[0],),
                   (rc.Resource('foreign', 'other-owner', 'handle', object()),),
                   (rc.Resource('missing-profile', 'owner', 'handle', object(), profile_id='absent'),),
                   (rc.Resource('bad-control', 'owner', 'handle', object(), recovery_for=('absent',)),),
                   (rc.Resource('unknown-kind', 'owner', 'pid', object()),)]
        for plan in invalid:
            backend = FakeBackend()
            events = []
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                rc.CleanupCoordinator(self.provenance, plan, backend, events.append)
            self.assertEqual(backend.calls, [])
            self.assertEqual(events, [])

    def test_same_exact_reference_cannot_be_registered_for_two_closes(self):
        identity = object()
        plan = (rc.Resource('first', 'owner', 'handle', identity),
                rc.Resource('alias', 'owner', 'handle', identity))
        backend = FakeBackend()
        with self.assertRaises(ValueError):
            rc.CleanupCoordinator(self.provenance, plan, backend, lambda event: None)
        self.assertEqual(backend.calls, [])

    def test_failure_at_each_backend_boundary_preserves_expected_ownership(self):
        cases = [
            ('terminate', 'child', ()),
            ('wait_terminal', 'child', ('child', 'control', 'profile')),
            ('close', 'child', ('child', 'profile')),
            ('close', 'control', ('control', 'profile')),
            ('close', 'fixture', ('fixture', 'profile')),
            ('close', 'thread', ('thread', 'profile')),
            ('close', 'socket', ('socket', 'profile')),
            ('remove_profile', 'profile', ('profile',)),
        ]
        for action, name, unresolved in cases:
            with self.subTest(action=action, resource=name):
                result = self.coordinator({(action, name): OSError('injected boundary failure')}).cleanup()
                self.assertEqual(result.unresolved, unresolved)
                self.assertFalse(result.success)
                self.assertEqual(len(result.cleanup_errors), 1)
                self.assertEqual(self.calls().count((action, name)), 1)
                if name != 'profile':
                    self.assertIn(('close', 'socket'), self.calls())

    def test_first_unconfirmed_process_does_not_prevent_second_process_cleanup(self):
        plan = self.plan + (rc.Resource('second-child', 'owner', 'process', object(), profile_id='profile'),)
        result = self.coordinator({('wait_terminal', 'child'): False}, plan=plan).cleanup()
        self.assertEqual(self.calls()[:5], [('terminate', 'child'), ('wait_terminal', 'child'),
                                          ('terminate', 'second-child'), ('wait_terminal', 'second-child'),
                                          ('close', 'second-child')])
        self.assertEqual(result.unresolved, ('child', 'control', 'profile'))

    def test_provenance_and_result_are_frozen_snapshots(self):
        bindings = [('source', 'b' * 64)]
        provenance = rc.Provenance('task/v1', 'work', 'owner', bindings)
        bindings.clear()
        self.assertEqual(provenance.source_hashes, (('source', 'b' * 64),))
        coordinator = self.coordinator()
        result = coordinator.cleanup()
        self.assertIs(result.provenance, self.provenance)
        with self.assertRaises(FrozenInstanceError):
            result.resources_complete = False
        with self.assertRaises(FrozenInstanceError):
            self.provenance.owner_id = 'other'

    def test_broken_exception_formatting_cannot_abort_cleanup(self):
        class BrokenError(Exception):
            def __str__(self):
                raise RuntimeError('broken string')
        result = self.coordinator({('close', 'fixture'): BrokenError()}).cleanup(BrokenError())
        self.assertEqual(result.primary_error.type_name, 'BrokenError')
        self.assertEqual(result.cleanup_errors[0].type_name, 'BrokenError')
        self.assertIn(('close', 'socket'), self.calls())

    def test_primary_is_captured_before_first_sink_or_backend_call(self):
        original = ValueError('first')
        def sink(event):
            original.args = ('changed by sink',)
        result = self.coordinator(sink=sink).cleanup(original)
        self.assertEqual(result.primary_error.message, 'first')

    def test_missing_explicit_backend_or_sink_is_rejected(self):
        with self.assertRaises(ValueError):
            rc.CleanupCoordinator(self.provenance, self.plan, None, self.events.append if hasattr(self, 'events') else lambda e: None)
        with self.assertRaises(ValueError):
            rc.CleanupCoordinator(self.provenance, self.plan, FakeBackend(), None)


if __name__ == '__main__':
    unittest.main()
