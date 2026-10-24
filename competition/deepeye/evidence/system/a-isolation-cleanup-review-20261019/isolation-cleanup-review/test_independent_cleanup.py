"""Independent pure callback tests; no OS backend or native fixture imports."""
import sys
import unittest
from simulation.isolation import resource_cleanup as rc


class Backend:
    def __init__(self, answers=None):
        self.answers = answers or {}
        self.calls = []
        self.hook = None

    def invoke(self, action, resource):
        key = (action, resource.resource_id)
        self.calls.append(key)
        if self.hook:
            self.hook()
        answer = self.answers.get(key, True if action == 'wait_terminal' else rc.Outcome.CONFIRMED)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    def terminate(self, r): return self.invoke('terminate', r)
    def wait_terminal(self, r): return self.invoke('wait_terminal', r)
    def close(self, r): return self.invoke('close', r)
    def remove_profile(self, r): return self.invoke('remove_profile', r)


class IndependentCleanupTests(unittest.TestCase):
    def setUp(self):
        self.provenance = rc.Provenance('task/v1', 'independent', 'owner', (('source', 'a' * 64),))
        self.plan = (
            rc.Resource('profile', 'owner', 'profile', object()),
            rc.Resource('recovery', 'owner', 'handle', object(), 'profile', ('process',)),
            rc.Resource('fixture', 'owner', 'socket', object(), 'profile'),
            rc.Resource('process', 'owner', 'process', object(), 'profile'),
        )
        self.order = [('terminate', 'process'), ('wait_terminal', 'process'),
                      ('close', 'process'), ('close', 'recovery'),
                      ('close', 'fixture'), ('remove_profile', 'profile')]

    def test_partial_write_and_unknown_side_effect_are_never_replayed(self):
        backend = Backend({('close', 'fixture'): rc.Outcome.UNKNOWN})
        seen = []
        def sink(event):
            seen.append(event.sequence)  # partial persistence before failure
            raise OSError('partial write')
        coordinator = rc.CleanupCoordinator(self.provenance, self.plan, backend, sink)
        result = coordinator.cleanup(RuntimeError('original'))
        self.assertEqual(backend.calls, self.order[:-1])
        self.assertEqual(result.unresolved, ('profile', 'fixture'))
        self.assertEqual(result.primary_error.message, 'original')
        self.assertEqual(len(result.audit_errors), len(seen))
        self.assertEqual(seen, list(range(1, len(seen) + 1)))
        self.assertFalse(result.success)
        self.assertFalse(result.evidence_complete)
        with self.assertRaises(rc.CleanupRejected): coordinator.cleanup()
        self.assertEqual(backend.calls, self.order[:-1])

    def test_termination_confirmation_alone_cannot_release_recovery_or_profile(self):
        backend = Backend({('wait_terminal', 'process'): False})
        result = rc.CleanupCoordinator(self.provenance, self.plan, backend, lambda e: None).cleanup()
        self.assertEqual(backend.calls, [self.order[0], self.order[1], ('close', 'fixture')])
        self.assertEqual(result.unresolved, ('profile', 'recovery', 'process'))
        self.assertFalse(result.resources_complete)

    def test_base_exception_logging_and_effect_do_not_skip_readback_or_later_closes(self):
        backend = Backend({('terminate', 'process'): KeyboardInterrupt('unknown')})
        def sink(event): raise SystemExit('sink failed')
        result = rc.CleanupCoordinator(self.provenance, self.plan, backend, sink).cleanup()
        self.assertEqual(backend.calls, self.order)
        self.assertTrue(result.resources_complete)
        self.assertFalse(result.evidence_complete)
        self.assertFalse(result.success)
        self.assertEqual(result.cleanup_errors[0].type_name, 'KeyboardInterrupt')

    def test_finish_event_snapshot_is_provisional_when_final_persistence_fails(self):
        backend = Backend()
        events = []
        def sink(event):
            events.append(event)
            if event.phase == 'finish': raise OSError('final fsync')
        result = rc.CleanupCoordinator(self.provenance, self.plan, backend, sink).cleanup()
        self.assertTrue(events[-1].result.evidence_complete)
        self.assertFalse(result.evidence_complete)
        self.assertEqual(result.audit_errors[-1].stage, 'audit:finish:cleanup')
        self.assertTrue(result.resources_complete)
        self.assertFalse(result.success)
        self.assertEqual(backend.calls, self.order)

    def test_two_process_recovery_gate_requires_all_terminal_readbacks(self):
        plan = self.plan + (rc.Resource('process2', 'owner', 'process', object(), 'profile'),
                            rc.Resource('shared', 'owner', 'handle', object(), 'profile', ('process', 'process2')))
        backend = Backend({('wait_terminal', 'process2'): None})
        result = rc.CleanupCoordinator(self.provenance, plan, backend, lambda e: None).cleanup()
        self.assertEqual(backend.calls, self.order[:3] + [('terminate', 'process2'), ('wait_terminal', 'process2'),
                                                       ('close', 'recovery'), ('close', 'fixture')])
        self.assertEqual(result.unresolved, ('profile', 'process2', 'shared'))

    def test_sink_and_backend_reentry_cannot_add_attempts_or_replace_primary(self):
        backend = Backend()
        rejected = []
        coordinator = None
        def attempt():
            try: coordinator.cleanup(ValueError('replacement'))
            except rc.CleanupRejected: rejected.append(True)
            else: self.fail('nested cleanup accepted')
        backend.hook = attempt
        coordinator = rc.CleanupCoordinator(self.provenance, self.plan, backend, lambda e: attempt())
        result = coordinator.cleanup(RuntimeError('outer'))
        self.assertEqual(backend.calls, self.order)
        self.assertEqual(result.primary_error.message, 'outer')
        self.assertEqual(len(rejected), len(self.order) + 2 * len(self.order) + 2)
        self.assertTrue(result.resources_complete)

    def test_duplicate_reference_rejected_before_any_backend_or_sink_call(self):
        backend = Backend()
        events = []
        plan = self.plan + (rc.Resource('alias', 'owner', 'thread', self.plan[2].identity),)
        with self.assertRaisesRegex(ValueError, 'same exact owned reference'):
            rc.CleanupCoordinator(self.provenance, plan, backend, events.append)
        self.assertEqual(backend.calls, [])
        self.assertEqual(events, [])

    def test_no_native_actor_modules_loaded(self):
        forbidden = ('simulation.isolation.win32', 'simulation.isolation.prototype', 'ctypes')
        self.assertEqual([name for name in forbidden if name in sys.modules], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
