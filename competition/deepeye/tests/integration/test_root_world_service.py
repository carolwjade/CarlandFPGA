"""NEW software-only original-world service controls; no engine or clock factory."""
import importlib
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT),
    'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps']
from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic.causal_pl_exchange import CausalSourcePump
try:
    service = importlib.import_module(
        'competition.deepeye.simulation.authority.root_world_service')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.authority.root_world_service':
        raise
    service = None


class Clock:
    software_fixture_only = True

    def __init__(self):
        self.calls = 0
        self.failure = None

    def _check(self):
        if self.failure is not None:
            raise self.failure

    def __call__(self):
        self._check()
        self.calls += 1
        return 10


class Executor:
    def __init__(self):
        self._scene = SimpleNamespace(scene_id='scene-1', digest='geometry-1')
        self._world_binding = 'binding-1'
        self.root = SimpleNamespace(world_invalid=False, phase=SimpleNamespace(
            context=SimpleNamespace(run_id='run-1', epoch=1)))

    def authority_snapshot(self):
        return self.root


class World:
    software_fixture_only = True
    _known_binding = loop._RootWorldOwner._known_binding
    _known_epoch = loop._RootWorldOwner._known_epoch

    def __init__(self, clock):
        self._test = True
        self._clock = clock
        self._thread = threading.get_ident()
        self._foreign = threading.Event()
        self._busy = False
        self._vetoed = False
        self._initialized = True
        self._state = 'BOUND_STOPPED'
        self._native = SimpleNamespace(clock_binding=clock,
            _containment_deadline=1000, _retired=False, state='AUTHENTICATED')
        self.executor = Executor()
        self._epoch = loop._FrozenEpoch(self, 1, 'freeze-1', {}, b'',
                                        None, 0)
        self._epochs = {id(self._epoch): self._epoch}
        self._retired_epochs = set()
        self._binding = loop._Binding(self, self._epoch,
            SimpleNamespace(scene=self.executor._scene), self.executor, 0, 1)
        self._bindings = {id(self._binding): self._binding}
        self.polls = 0
        self.closes = 0
        self.hook = None

    def poll(self):
        self.polls += 1
        self._clock()
        if self.hook is not None:
            self.hook(self)
        return self._state

    def close(self):
        self.closes += 1
        raise AssertionError('service must not own world cleanup')


def field_for(world):
    # Identity-only fixture: never invokes geometry sampling or a model.
    field = object.__new__(OwnedWorldField)
    field._executor = world.executor
    field._scene = world.executor._scene
    field._scene_id = 'scene-1'
    field._scene_digest = 'geometry-1'
    field._binding = 'binding-1'
    field._run = 'run-1'
    field._epoch = 1
    field._retired = False
    return field


class RootWorldServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(service, 'RootWorldService feature is missing')
        self.clock = Clock()
        self.world = World(self.clock)
        self.field = field_for(self.world)
        self.source = CausalSourcePump(self.field.pose_reader,
                                      self.field.sample_sigma)

    def borrowed(self):
        return service._software_service_for_test(
            self.clock, self.world, self.source)

    def test_clock_and_fixed_deadline_are_readonly_without_hidden_poll(self):
        borrowed = self.borrowed()
        self.assertIs(borrowed.clock, self.clock)
        self.assertIs(borrowed.source, self.source)
        self.assertEqual(1000, borrowed.deadline_ns)
        self.assertEqual((0, 0), (self.clock.calls, self.world.polls))
        with self.assertRaises(AttributeError):
            borrowed.clock = Clock()
        with self.assertRaises(AttributeError):
            borrowed.deadline_ns = 2000
        with self.assertRaises(AttributeError):
            borrowed.source = object()
        self.assertEqual('BOUND_STOPPED', borrowed.poll())
        self.assertEqual((1, 1), (self.clock.calls, self.world.polls))

    def test_new_to_running_source_does_not_replace_any_owner(self):
        borrowed = self.borrowed()
        borrowed.poll()
        self.source.start(0, self.clock)
        borrowed.poll()
        self.assertEqual(2, self.world.polls)
        self.assertEqual('RUNNING', self.source.state)
        self.assertEqual(0, self.world.closes)

    def test_pre_poll_veto_is_sticky_after_external_flag_repair(self):
        borrowed = self.borrowed()
        self.world._vetoed = True
        with self.assertRaises(ValueError):
            borrowed.poll()
        self.world._vetoed = False
        with self.assertRaises(RuntimeError):
            borrowed.poll()
        self.assertEqual(0, self.world.polls)
        self.assertEqual('NEW', self.source.state)

    def test_original_poll_exception_survives_without_cleanup_or_retry(self):
        borrowed = self.borrowed()
        original = LookupError('original world business failure')
        def fail(world):
            raise original
        self.world.hook = fail
        with self.assertRaises(LookupError) as caught:
            borrowed.poll()
        self.assertIs(original, caught.exception)
        self.world.hook = None
        with self.assertRaises(RuntimeError):
            borrowed.poll()
        self.assertEqual((1, 0), (self.world.polls, self.world.closes))
        self.assertEqual('NEW', self.source.state)

    def test_new_registered_binding_after_poll_is_not_adopted(self):
        borrowed = self.borrowed()
        original = self.world._binding
        def replace(world):
            replacement = loop._Binding(world, world._epoch,
                original.world_values, original.executor, 0, 1)
            world._binding = replacement
            world._bindings[id(replacement)] = replacement
        self.world.hook = replace
        with self.assertRaises(ValueError):
            borrowed.poll()
        self.assertEqual(1, self.world.polls)
        self.world._binding = original
        with self.assertRaises(RuntimeError):
            borrowed.poll()

    def test_registry_loss_rejects_before_external_poll(self):
        borrowed = self.borrowed()
        del self.world._bindings[id(self.world._binding)]
        with self.assertRaises(ValueError):
            borrowed.poll()
        self.assertEqual(0, self.world.polls)

    def test_retired_field_scene_world_and_source_reject_before_poll(self):
        changes = (
            lambda: setattr(self.field, '_retired', True),
            lambda: setattr(self.field, '_scene', SimpleNamespace()),
            lambda: setattr(self.world.executor.root, 'world_invalid', True),
            lambda: setattr(self.source, 'state', 'RETIRED'),
        )
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                borrowed = self.borrowed()
                change()
                with self.assertRaises(ValueError):
                    borrowed.poll()
                self.assertEqual(0, self.world.polls)

    def test_source_callbacks_must_be_exact_original_same_field_methods(self):
        changes = (
            lambda: setattr(self.source, '_pose_reader', lambda: None),
            lambda: setattr(self.source, '_sampler',
                            field_for(self.world).sample_sigma),
            lambda: setattr(self.source, '_pose_reader',
                            self.field.sample_sigma),
        )
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                borrowed = self.borrowed()
                change()
                with self.assertRaises(ValueError):
                    borrowed.poll()
                self.assertEqual(0, self.world.polls)

    def test_clock_native_deadline_and_source_thread_replacements_reject(self):
        changes = (
            lambda: setattr(self.world, '_clock', Clock()),
            lambda: setattr(self.world, '_native', SimpleNamespace()),
            lambda: setattr(self.world._native, 'clock_binding', Clock()),
            lambda: setattr(self.world._native, '_containment_deadline', 2000),
            lambda: setattr(self.source, '_thread', -1),
            lambda: setattr(self.world, '_initialized', False),
        )
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                borrowed = self.borrowed()
                change()
                self.assertEqual(1000, borrowed.deadline_ns)
                with self.assertRaises(ValueError):
                    borrowed.poll()
                self.assertEqual(0, self.world.polls)

    def test_post_poll_veto_clock_and_source_failure_are_not_success(self):
        hooks = (
            lambda w: setattr(w, '_vetoed', True),
            lambda w: setattr(w, '_clock', Clock()),
            lambda w: setattr(self.source, 'state', 'FAILED'),
        )
        for hook in hooks:
            with self.subTest(hook=hook):
                self.setUp()
                borrowed = self.borrowed()
                self.world.hook = hook
                with self.assertRaises(ValueError):
                    borrowed.poll()
                self.assertEqual(1, self.world.polls)

    def test_post_poll_clock_error_is_original_and_sticky(self):
        borrowed = self.borrowed()
        original = ArithmeticError('original clock binding failed')
        self.world.hook = lambda w: setattr(self.clock, 'failure', original)
        with self.assertRaises(ArithmeticError) as caught:
            borrowed.poll()
        self.assertIs(original, caught.exception)
        self.clock.failure = None
        with self.assertRaises(RuntimeError):
            borrowed.poll()

    def test_swallowed_reentrant_poll_still_retires_outer_call(self):
        borrowed = self.borrowed()
        def reenter(world):
            with self.assertRaises(RuntimeError):
                borrowed.poll()
        self.world.hook = reenter
        with self.assertRaises(RuntimeError):
            borrowed.poll()
        self.assertEqual(1, self.world.polls)

    def test_public_entry_rejects_software_and_cannot_be_subclassed(self):
        with self.assertRaises(ValueError):
            service.RootWorldService(self.clock, self.world, self.source)
        class Derived(service.RootWorldService):
            pass
        with self.assertRaises(ValueError):
            Derived(self.clock, self.world, self.source)
        self.assertIsNot(type(self.borrowed()), service.RootWorldService)
        self.assertEqual(0, self.world.polls)

    def test_software_seam_refuses_actual_root_owner_type(self):
        production_like = object.__new__(loop._RootWorldOwner)
        production_like._test = False
        production_like._native = self.world._native
        with self.assertRaises(ValueError):
            service._software_service_for_test(
                self.clock, production_like, self.source)
        self.assertEqual(0, self.world.polls)

    def test_foreign_thread_permanently_retires_without_world_poll(self):
        borrowed = self.borrowed()
        errors = []
        def foreign():
            try:
                borrowed.poll()
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(1)
        self.assertFalse(thread.is_alive())
        self.assertEqual(1, len(errors))
        with self.assertRaises(RuntimeError):
            borrowed.poll()
        self.assertEqual(0, self.world.polls)

    def test_explicit_retired_source_drain_only_polls_original_world(self):
        borrowed = self.borrowed()
        self.source.retire('Root finished source work')
        self.assertEqual('BOUND_STOPPED', borrowed.poll_retired_source())
        self.assertEqual((1, 1), (self.clock.calls, self.world.polls))
        self.assertEqual('RETIRED', self.source.state)
        self.assertEqual(0, self.source._count)
        self.assertEqual(0, self.world.closes)
        self.world._vetoed = True
        with self.assertRaises(ValueError):
            borrowed.poll_retired_source()
        self.world._vetoed = False
        with self.assertRaises(RuntimeError):
            borrowed.poll_retired_source()

    def test_retired_source_drain_cannot_start_fresh_work_or_revive_failure(self):
        borrowed = self.borrowed()
        with self.assertRaises(ValueError):
            borrowed.poll_retired_source()
        self.source.retire('Root finished source work')
        with self.assertRaises(RuntimeError):
            borrowed.poll_retired_source()
        self.assertEqual(0, self.world.polls)


if __name__ == '__main__':
    unittest.main()
