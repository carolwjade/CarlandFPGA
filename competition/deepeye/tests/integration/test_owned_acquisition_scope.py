"""NEW literal scalar/custody controls; no kernel, model, engine or board."""
from dataclasses import replace
from pathlib import Path
import random
import sys
import threading
from types import SimpleNamespace
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[4]),
    'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps']
from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.authority import motion_executor as motion
from competition.deepeye.simulation.authority.motion import solid_clearance as geom
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic.causal_pl_exchange import CausalSourcePump


class Clock:
    software_fixture_only = True

    def __init__(self):
        self.now = 100_000_000
        self.failure = None

    def _check(self):
        if self.failure is not None:
            raise self.failure

    def __call__(self):
        self._check()
        return self.now


def complete_scene():
    descriptions = (
        ('water', 'box', (0, 0, 0), (4, 4, 4)),
        ('hard_rock', 'box', (6, 0, 0), (1, 1, 1)),
        ('fault', 'cylinder', (0, 6, 0), (2, 2, 2)),
        ('casing', 'box', (0, 0, 0), (1, 1, 1)),
        ('void', 'box', (10, 0, 0), (1, 1, 1)),
    )
    objects = tuple(geom.SceneObject(kind, kind, (
        geom.Solid(kind+'-piece', 'literal-v1', shape, centre, size,
                   (0, 0, 0, 1)),))
        for kind, shape, centre, size in descriptions)
    return geom.Scene('literal-scene', 'v1',
        tuple((obj.object_id, (obj.parts[0].model_id,)) for obj in objects), objects)


class World:
    software_fixture_only = True
    _known_epoch = loop._RootWorldOwner._known_epoch
    _known_binding = loop._RootWorldOwner._known_binding

    def __init__(self, clock):
        self._test = True
        self._clock = clock
        self._thread = threading.get_ident()
        self._busy = False
        self._em_scope_active = None
        self._foreign = threading.Event()
        self._vetoed = False
        self._veto_generation = 0
        self._initialized = True
        self._publication = None
        self._freeze_request = None
        self._native = SimpleNamespace(clock_binding=clock,
            _containment_deadline=5_000_000_000, _retired=False,
            state='AUTHENTICATED')
        scene = complete_scene()
        executor = object.__new__(motion.OwnedMotionExecutor)
        executor._owner = self._thread
        executor._busy = False
        executor._pending = {}
        executor._scene = scene
        executor._world_binding = 'literal-binding'
        pose = SimpleNamespace(position_m=(0., 0., 0.),
                               orientation_xyzw=(0., 0., 0., 1.))
        phase = SimpleNamespace(context=SimpleNamespace(run_id='literal-run', epoch=1))
        executor._root = motion._Root(0, 0, pose, 0, phase, None, None, None,
                                     True, False, False, 0)
        self.executor = executor
        self._epoch = loop._FrozenEpoch(self, 1, 'literal-freeze',
            {'freeze_id': 'literal-freeze', 'geometry_state_sha256': scene.digest},
            b'', None, 0)
        self._epochs = {id(self._epoch): self._epoch}
        self._retired_epochs = set()
        self._binding = loop._Binding(self, self._epoch,
            SimpleNamespace(scene=scene), executor, 0, 1)
        self._bindings = {id(self._binding): self._binding}
        self._status = dict(identity=self._epoch.identity, state='BOUND_STOPPED')
        self._native_observation = SimpleNamespace(alive=True)
        self.polls = 0
        self.hook = None

    def poll(self):
        if self._busy:
            raise AssertionError('explicit poll must be outside owner._busy')
        self.polls += 1
        self._clock()
        if self.hook:
            self.hook(self)
        return 'BOUND_STOPPED'

    def close(self):
        raise AssertionError('scope cannot own cleanup')


class AcquisitionScopeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(loop, '_make_original_em_scope_factory'),
                        'original EM scope feature is missing')
        self.clock = Clock()
        self.world = World(self.clock)
        self.field = OwnedWorldField(self.world.executor,
            material_sigma=dict(casing=3., fault=.7, void=None,
                                water=.2, hard_rock=.1),
            background_sigma=.5, max_pieces=5)
        self.source = CausalSourcePump(self.field.pose_reader,
                                      self.field.sample_sigma)
        self.factory = loop._make_software_em_scope_factory_for_test(
            self.world, self.world._binding, self.field, self.source)

    def consume(self, tick=100):
        if self.source.state == 'NEW':
            self.source.start(0, self.clock)
        # Pure schedule fixture. No acquire_em, source.poll or numerical kernel.
        self.source._last_tick = tick
        self.source._count += 1
        self.source._high = self.clock.now
        return tick

    def assert_failed(self):
        self.assertTrue(self.field._retired)
        self.assertEqual('FAILED', self.source.state)

    def test_literal_complete_pieces(self):
        self.assertEqual(5, len(self.field._pieces))
        points = (((0, 0, 0), 3.), ((2, 0, 0), .2), ((6, 0, 0), .1),
                  ((0, 6, 0), .7), ((10, 0, 0), None), ((12, 0, 0), .5),
                  ((1, 0, 0), None), ((2, 6, 0), None),
                  ((float('nan'), 0, 0), None), ((True, 0, 0), None))
        with self.factory.begin(self.consume()) as scope:
            for point, expected in points:
                self.assertEqual(expected, self.field.sample_sigma(*point))
                self.assertEqual(expected, scope.sampler(*point))

    def test_public_check_still_retires_changed_world_during_scope(self):
        with self.assertRaises(RuntimeError):
            with self.factory.begin(self.consume()) as scope:
                root = self.world.executor._root
                self.world.executor._root = replace(root, world_invalid=True)
                with self.assertRaises(ValueError):
                    self.field.sample_sigma(0, 0, 0)
                self.world.executor._root = root
                # A full public check retired the field; no private escape.
                with self.assertRaises(ValueError):
                    scope.sampler(0, 0, 0)

    def test_success_polls_twice_and_does_not_replace_source_sampler(self):
        original = self.source._sampler
        with self.factory.begin(self.consume()) as scope:
            self.assertEqual(.5, scope.sampler(12, 0, 0))
            escaped = scope.sampler
        self.assertEqual(2, self.world.polls)
        self.assertIs(original, self.source._sampler)
        self.assertEqual('RUNNING', self.source.state)
        with self.assertRaises(RuntimeError):
            escaped(12, 0, 0)
        self.assert_failed()

    def test_enter_requires_running_consumed_em_tick_and_same_clock(self):
        changes = (lambda: None,
            lambda: self.source.start(0, self.clock),
            lambda: (self.consume(), setattr(self.source, '_last_tick', 90)),
            lambda: (self.consume(), setattr(self.source, '_clock', Clock())))
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                change()
                with self.assertRaises(ValueError):
                    with self.factory.begin(100):
                        pass
                self.assert_failed()

    def test_tick_is_consumed_no_reentry_or_same_slot_reuse(self):
        tick = self.consume()
        with self.factory.begin(tick):
            pass
        with self.assertRaises(ValueError):
            self.factory.begin(tick)
        self.assertEqual(tick, self.source._last_tick)
        self.assert_failed()

    def test_nested_scope_is_sticky_even_if_inner_failure_is_caught(self):
        with self.assertRaises(RuntimeError):
            with self.factory.begin(self.consume()):
                with self.assertRaises(RuntimeError):
                    self.factory.begin(150)
        self.assert_failed()

    def test_revision_revoke_and_pose_aba_are_not_accepted(self):
        for change in ('revision', 'revoke', 'pose'):
            with self.subTest(change=change):
                self.setUp()
                with self.assertRaises(ValueError):
                    with self.factory.begin(self.consume()):
                        root = self.world.executor._root
                        if change == 'revoke':
                            self.world.executor.revoke('literal STOP')
                        elif change == 'revision':
                            self.world.executor._root = replace(root,
                                revision=root.revision+2)
                        else:
                            self.world.executor._root = replace(root,
                                revision=root.revision+2, pose_revision=2)
                self.assert_failed()

    def test_original_owner_veto_generation_aba_rejects(self):
        with self.assertRaises(ValueError):
            with self.factory.begin(self.consume()):
                self.world._veto_generation += 2
                self.world._vetoed = False
        self.assert_failed()

    def test_changed_binding_epoch_native_compiled_policy_or_digest_rejects(self):
        changes = (
            lambda: self.world._bindings.clear(),
            lambda: self.world._retired_epochs.add(1),
            lambda: setattr(self.world, '_native', SimpleNamespace()),
            lambda: setattr(self.world._native, '_retired', True),
            lambda: setattr(self.source, '_profile', object()),
            lambda: setattr(self.field, '_pieces', tuple(reversed(self.field._pieces))),
            lambda: setattr(self.field, '_background', .6),
            lambda: object.__setattr__(self.field._scene.objects[0].parts[0],
                                      'centre', (1, 0, 0)),
        )
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                with self.assertRaises(ValueError):
                    with self.factory.begin(self.consume()):
                        change()
                self.assert_failed()

    def test_foreign_sampler_attempt_contaminates_exit_without_owner_call(self):
        errors = []
        with self.assertRaises(RuntimeError):
            with self.factory.begin(self.consume()) as scope:
                def foreign():
                    try:
                        scope.sampler(12, 0, 0)
                    except BaseException as error:
                        errors.append(error)
                t = threading.Thread(target=foreign)
                t.start()
                t.join(1)
                self.assertFalse(t.is_alive())
                self.assertEqual(1, self.world.polls)
        self.assertEqual(1, len(errors))
        self.assert_failed()

    def test_before_expiry_and_after_expiry_fail_without_clock_extension(self):
        for after in (False, True):
            with self.subTest(after=after):
                self.setUp()
                self.consume()
                if not after:
                    self.clock.now = self.world._native._containment_deadline
                with self.assertRaises(ValueError):
                    with self.factory.begin(100):
                        self.clock.now = self.world._native._containment_deadline
                self.assert_failed()
                self.assertEqual(5_000_000_000,
                                 self.world._native._containment_deadline)

    def test_post_poll_failure_suppresses_success_and_retains_original_error(self):
        original = LookupError('original post poll failure')
        def post(world):
            if world.polls == 2:
                raise original
        self.world.hook = post
        with self.assertRaises(LookupError) as caught:
            with self.factory.begin(self.consume()):
                pass
        self.assertIs(original, caught.exception)
        self.assert_failed()

    def test_body_exception_primary_even_when_exit_poll_also_fails(self):
        primary = KeyboardInterrupt('literal body cancellation')
        secondary = LookupError('literal secondary post failure')
        def post(world):
            if world.polls == 2:
                raise secondary
        self.world.hook = post
        with self.assertRaises(KeyboardInterrupt) as caught:
            with self.factory.begin(self.consume()) as scope:
                raise primary
        self.assertIs(primary, caught.exception)
        self.assertIn(secondary, scope.secondary_errors)
        self.assert_failed()

    def test_failed_postcheck_does_not_rollback_body_rng_or_allow_replay(self):
        rng, control = random.Random(321), random.Random(321)
        first = control.random()
        expected_next = control.random()
        with self.assertRaises(ValueError):
            with self.factory.begin(self.consume()):
                self.assertEqual(first, rng.random())
                self.world._veto_generation += 1
        self.assertEqual(expected_next, rng.random())
        with self.assertRaises(RuntimeError):
            self.factory.begin(150)
        self.assertEqual(100, self.source._last_tick)
        self.assert_failed()

    def test_factory_cannot_adopt_new_source_or_public_fake_authority(self):
        with self.assertRaises(ValueError):
            loop._make_original_em_scope_factory(self.world,
                self.world._binding, self.field, self.source)
        with self.assertRaises(ValueError):
            loop._make_software_em_scope_factory_for_test(self.world,
                self.world._binding, self.field,
                CausalSourcePump(self.field.pose_reader, self.field.sample_sigma))
        with self.assertRaises(ValueError):
            loop._make_software_em_scope_factory_for_test(
                object.__new__(loop._RootWorldOwner), self.world._binding,
                self.field, self.source)
        self.assertIsNot(type(self.factory), loop._OriginalEmScopeFactory)


if __name__ == '__main__':
    unittest.main()
