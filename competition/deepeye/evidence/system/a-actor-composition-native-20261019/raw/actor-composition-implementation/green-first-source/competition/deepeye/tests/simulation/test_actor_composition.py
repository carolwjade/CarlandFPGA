"""Offline composition counterexamples. No genuine AI/readiness/native effects."""
from dataclasses import replace
import importlib
import threading
from types import SimpleNamespace
from unittest.mock import patch

from competition.deepeye.tests.simulation.test_actor_owner import OwnerFixture, a
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt
from competition.deepeye.tests.simulation import test_motion_executor as mt

try:
    c = importlib.import_module('competition.deepeye.simulation.authority.actor_composition')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.authority.actor_composition': raise
    c = None


class FakeChannels:
    """Private test verifier only: original opaque object identity, no authentication."""
    def __init__(self, fixture):
        self.fixture, self.ready, self.used, self.records = fixture, object(), False, []
        self.healthy, self.hook = True, None
    def checkpoint(self):
        hook, self.hook = self.hook, None
        if hook: hook()
        if not self.healthy: raise ValueError('synthetic inference progress expired')
    def verify_boot(self, event, *, run_id, instance_id):
        self.checkpoint()
        if event is not self.ready or self.used: raise ValueError('original synthetic readiness missing')
        self.used = True
        return replace(self.fixture.boot_binding(), run_id=run_id, ai_instance=instance_id)
    def event(self, record):
        opaque = object(); self.records.append((opaque, record)); return opaque
    def _verify(self, event):
        self.checkpoint()
        for original, record in self.records:
            if event is original: return record
        raise ValueError('not an original synthetic channel event')
    def verify_board(self, event, boot): return self._verify(event)
    def verify_observation(self, event, boot): return self._verify(event)
    def verify_command(self, event, boot): return self._verify(event)


class ActorCompositionTests(OwnerFixture):
    def setUp(self):
        super().setUp()
        self.assertIsNotNone(c, 'trusted actor composition is not implemented')
        self.f = rt.PcDirectRuntimeTests(); self.f.setUp(); self.f.clock = self.clock
        self.channels = FakeChannels(self.f)
        geom = mt.MotionExecutorTests(); geom.setUp()
        initial = mt.p.initialize(geom.ctx, mt.RigidState((0, 0, 15.6), (0, 1, 0, 0), .25),
            mt.gc.ErrorBounds(0., 0., 0.), pose_revision=0, monotonic_ns=0,
            error_budget_reference='explicit offline composition fixture').state
        self.config = c.AuthorityConfig(actor_policy=self.policy, initial_state=initial,
            scene=geom.scene, model=geom.model, budget=geom.budget,
            heartbeat_timeout_ns=500_000_000, max_slices=16)
        self.clock_patch = patch.object(c, 'monotonic_ns', self.clock)
        self.clock_patch.start(); self.addCleanup(self.clock_patch.stop)
        self.comp = None
        self.addCleanup(self.close_fixture)

    def close_fixture(self):
        if self.comp is not None: self.comp.close('offline fixture teardown')

    def create(self):
        with patch.object(c, '_production_channels', return_value=self.channels):
            self.comp = c.create_authority(self.config)
        return self.comp

    def activate(self):
        if self.comp is None: self.create()
        self.comp.accept_boot(self.channels.ready)
        self.f.binding = self.comp._boot
        self.f.owner = SimpleNamespace(
            board=lambda record: self.comp.accept_board(self.channels.event(record)),
            observe=lambda record: self.comp.accept_observation(self.channels.event(record)),
            command=lambda record: self.comp.accept_command(self.channels.event(record)))
        self.f.beat()

    def arm(self):
        self.activate(); self.f.observe(); self.f.command()

    def step(self): return self.comp.step(expected_pose_revision=0, dt_ns=1_000_000)

    def assert_no_pose(self):
        self.assertEqual(self.comp._executor.renderer_view().pose_revision, 0)
        self.assertTrue(self.comp._executor.controller_view().stopped)
        self.assertNotEqual(self.comp.status().state, 'ACTIVE')

    def test_missing_production_verifier_rejects_before_registry_construction(self):
        self.api.calls.clear()
        with patch.object(c, 'ActorRegistry', wraps=a.ActorRegistry) as constructor:
            with self.assertRaises(c.ActivationUnavailable): c.create_authority(self.config)
        self.assertEqual(constructor.call_count, 0)
        self.assertEqual(self.api.calls, [])

    def test_public_factory_has_no_provider_actor_or_lease_injection(self):
        for name in ('dependencies', 'actor', 'ai_lease', 'verifier', 'registry', 'executor'):
            with self.subTest(name=name), self.assertRaises((TypeError, ValueError)):
                c.create_authority(self.config, **{name: object()})

    def test_registry_is_retained_before_construction_and_failed_launch(self):
        original = a.ActorRegistry
        seen = []
        def construct():
            seen.append(c._RETAINED[-1]); return original()
        self.api.fail = 'process'
        with patch.object(c, '_production_channels', return_value=self.channels), patch.object(c, 'ActorRegistry', construct):
            with self.assertRaises(c.CompositionRejected): c.create_authority(self.config)
        holder = seen[0]
        self.assertIs(c._RETAINED[-1], holder)
        self.assertEqual(len(holder._registry._owners), 1)
        self.assertNotEqual(holder._registry._owners[0].state, 'BOUND_ACTIVE')
        self.assertIsInstance(holder._primary_error, OSError)

    def test_exact_original_actor_and_real_numeric_executor_commit(self):
        self.arm(); self.api.calls.clear()
        before = self.comp._executor.renderer_view().pose
        result = self.step()
        self.assertTrue(result.committed); self.assertEqual(result.pose_revision, 1)
        self.assertNotEqual(before, self.comp._executor.renderer_view().pose)
        self.assertGreaterEqual(len([call for call in self.api.calls if call == ('wait', 300, 0)]), 3)
        self.assertEqual(set(result.__dict__), {'committed', 'pose_revision'})

    def test_static_channel_provider_cannot_mask_original_death(self):
        self.channels.ai_lease = lambda boot, now: rt.runtime.AiLease(boot, boot.ai_instance, 10**20)
        self.arm(); self.api.live = False
        self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_death_during_prepare_and_inside_final_fence_never_commits(self):
        self.arm()
        original = self.comp._executor.prepare_step
        def prepare(*args):
            result = original(*args); self.api.live = False; return result
        with patch.object(self.comp._executor, 'prepare_step', prepare):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_final_fence_detects_death_after_preparation_checks(self):
        self.arm()
        original = self.comp._executor.commit_step
        def commit(prepared, fence):
            self.api.live = False; return original(prepared, fence)
        with patch.object(self.comp._executor, 'commit_step', commit):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_plain_records_and_fixture_ready_text_never_authenticate(self):
        self.create()
        with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(b'DEEPEYE-ACTOR/1 READY\n')
        self.assert_no_pose()
        self.assertFalse(self.channels.used)

    def test_plain_verified_command_record_cannot_bypass_channel(self):
        self.activate(); self.f.observe()
        wrong = rt.runtime.VerifiedEnvelope(self.f.binding, b'{}')
        with self.assertRaises(c.CompositionRejected): self.comp.accept_command(wrong)
        self.assert_no_pose()

    def test_partial_activation_failures_revoke_originals_and_cleanup_once(self):
        self.create()
        primary = OSError('private original activation error')
        original = self.comp._executor.activate_boot
        def fail(boot): original(boot); raise primary
        with patch.object(self.comp._executor, 'activate_boot', fail):
            with self.assertRaises(c.CompositionRejected) as caught: self.comp.accept_boot(self.channels.ready)
        self.assertNotIn('private original', str(caught.exception))
        self.assertIs(self.comp._primary_error, primary)
        self.assert_no_pose()
        self.assertTrue(self.comp._runtime._latched)
        self.comp.close('repeat')
        self.assertEqual(self.api.calls.count(('terminate', 300)), 1)

    def test_runtime_activation_error_after_assignment_is_revoked(self):
        self.create(); original = self.comp._runtime.boot
        def fail(event): original(event); raise OSError('runtime activated then failed')
        with patch.object(self.comp._runtime, 'boot', fail):
            with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assertTrue(self.comp._runtime._latched); self.assert_no_pose()

    def test_binding_error_after_binding_is_revoked(self):
        self.create(); original = self.comp._actor.bind_verified_boot
        def fail(*args, **kwargs): original(*args, **kwargs); raise OSError('bound then failed')
        with patch.object(self.comp._actor, 'bind_verified_boot', fail):
            with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assertTrue(self.comp._runtime._latched); self.assert_no_pose()

    def test_each_revocation_dispatch_rechecks_successor_identity(self):
        self.activate(); old = self.comp._boot
        successor = replace(old, generation=2, context_json=rt.encode(dict(rt.PC, session=8)))
        original_stop = self.comp._runtime.stop
        def stop(reason):
            original_stop(reason)
            self.comp._executor.activate_boot(successor)
        with patch.object(self.comp._runtime, 'stop', stop): self.comp.stop('operator')
        self.assertIs(self.comp._executor._root.boot, successor)
        self.assertFalse(self.comp._executor.controller_view().stopped)
        self.comp.close('late close')
        self.assertFalse(self.comp._executor.controller_view().stopped)

    def test_external_stop_and_broker_stop_never_become_motion(self):
        self.activate(); self.f.command(action=0)
        self.assert_no_pose()
        self.assertIsNone(self.comp._executor._root.command)

    def test_caught_reentry_from_channel_latches_outer_activation(self):
        self.create()
        def reenter():
            try: self.comp.poll()
            except c.CompositionRejected: pass
        self.channels.hook = reenter
        with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assert_no_pose()

    def test_caught_malformed_reentry_from_clock_vetoes_outer_step(self):
        self.arm()
        def reenter():
            try: self.comp.step(self='not the receiver')
            except (c.CompositionRejected, ValueError): pass
        self.clock.hook = reenter
        self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_foreign_thread_veto_has_no_foreign_native_effect_and_owner_drains(self):
        self.arm(); self.api.calls.clear(); errors = []
        def foreign():
            try: self.comp.close('foreign')
            except c.CompositionRejected as error: errors.append(error)
        thread = threading.Thread(target=foreign); thread.start(); thread.join()
        self.assertEqual(len(errors), 1); self.assertEqual(self.api.calls, [])
        self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_missing_progress_cannot_be_replaced_by_nonsignaled_process(self):
        self.arm(); self.channels.healthy = False
        with self.assertRaises(c.CompositionRejected): self.comp.poll()
        self.assert_no_pose()

    def test_noncommitted_idle_is_conservatively_retired(self):
        self.activate(); self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_cleanup_failure_preserves_primary_and_strong_registry(self):
        self.create(); primary = OSError('private readiness error')
        with patch.object(self.channels, 'verify_boot', side_effect=primary), patch.object(a, '_persist', side_effect=OSError('evidence error')):
            with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assertIs(self.comp._primary_error, primary)
        self.assertIn(self.comp, c._RETAINED)
        self.assertIs(self.comp._registry._owners[0], self.comp._actor)
        self.assertEqual(self.comp._actor.state, 'QUARANTINED')
        self.assertNotEqual(self.comp.status().state, 'ACTIVE')

    def test_unknown_call_shape_retires_even_when_already_active(self):
        self.arm()
        with self.assertRaises(c.CompositionRejected): self.comp.accept_command(unknown=True)
        self.assert_no_pose()

    def test_same_value_different_boot_object_cannot_pass_private_verifier(self):
        self.activate()
        event = self.channels.event(rt.runtime.VerifiedEnvelope(replace(self.comp._boot), b'{}'))
        with self.assertRaises(c.CompositionRejected): self.comp.accept_board(event)
        self.assert_no_pose()
