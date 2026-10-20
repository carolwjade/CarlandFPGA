"""Offline composition counterexamples. No genuine AI/readiness/native effects."""
from dataclasses import replace
import importlib
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from competition.deepeye.tests.simulation.test_actor_owner import OwnerFixture, a
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt
from competition.deepeye.tests.simulation import test_motion_executor as mt
from competition.deepeye.simulation.authority import candidate_owner as co

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
        self.last_completion = None
        self.slot_origin_ns, self.slot_window = 0, 0
    def checkpoint(self):
        hook, self.hook = self.hook, None
        if hook: hook()
        if not self.healthy: raise ValueError('synthetic inference progress expired')
    def verify_boot(self, event, *, run_id, instance_id):
        self.checkpoint()
        if event is not self.ready or self.used: raise ValueError('original synthetic readiness missing')
        self.used = True
        binding = replace(self.fixture.boot_binding(), run_id=run_id, ai_instance=instance_id)
        context = rt.runtime.envelope._parse_message(binding.context_json)
        document = co.boot_profile.load_document(Path(co.__file__).resolve().parents[2] / 'docs/boot_profiles.json')
        context['boot_sha256'] = co.boot_profile.canonical_sha256(document).hex()
        return replace(binding, context_json=rt.encode(context))
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

    def verify_completion(self, event, boot): return self._verify(event)
    def verify_slot(self, event, boot): return self._verify(event)

    def mailbox_activation_for_boot(self, boot):
        self.checkpoint()
        return co._MailboxActivation(boot,self,c.monotonic_ns,self.slot_origin_ns,0,0)

    def slot_event(self, boot):
        return self.event(co._VerifiedSlot(boot,self,c.monotonic_ns,self.slot_window))

    def completion_event(self, boot, *, seq=3, obs=9, issue=None, duration=1000, **unused):
        # Explicit upstream synthetic event, created before any broker command.
        # No command parsing/lookup and no completion history or receipt renewal.
        completed = self.fixture.clock.value if issue is None else issue
        context = rt.runtime.envelope._parse_message(boot.context_json)
        candidate = dict(schema_version=1,kind='model_candidate',context=context,
            candidate_id=seq,model_sha256='a'*64,
            observation=dict(context=context,observed_seq=obs),
            target=dict(action=1,yaw_q=0,pitch_q=0,speed_code=5,duration_ms=duration),
            completed_monotonic_ns=completed)
        self.last_completion = c._CompletedInference(boot,self,c.monotonic_ns,
            rt.encode(candidate),seq+1,completed,completed,completed)
        return self.event(self.last_completion)


class ActorCompositionTests(OwnerFixture):
    def setUp(self):
        super().setUp()
        # Established synthetic origin=0, first legal slot=210 ms. The clock
        # starts at that instant; no production clock is replaced by slot time.
        self.clock.value = 210_000_000
        self.assertIsNotNone(c, 'trusted actor composition is not implemented')
        self.f = rt.PcDirectRuntimeTests(); self.f.setUp(); self.f.clock = self.clock
        self.channels = FakeChannels(self.f)
        geom = mt.MotionExecutorTests(); geom.setUp()
        initial = mt.p.initialize(geom.ctx, mt.RigidState((0, 0, 15.6), (0, 1, 0, 0), .25),
            mt.gc.ErrorBounds(0., 0., 0.), pose_revision=0, monotonic_ns=0,
            error_budget_reference='explicit offline composition fixture').state
        self.config = c.AuthorityConfig(actor_policy=self.policy, initial_state=initial,
            scene=geom.scene, model=geom.model, budget=geom.budget,
            heartbeat_timeout_ns=500_000_000, max_slices=16,
            progress_max_age_ns=100_000_000, ai_model_sha256='a' * 64)
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
            command=lambda record: self.comp.accept_command(self.channels.event(record),
                slot_event=self.channels.slot_event(self.comp._boot)))
        original_command = self.f.command
        def completed_then_command(**values):
            if values.get('action',1) != 0:
                self.comp.accept_completion(self.channels.completion_event(self.comp._boot,**values))
            return original_command(**values)
        self.f.command = completed_then_command
        self.f.beat()

    def arm(self):
        self.activate(); self.f.observe(); self.f.command()

    def next_slot(self):
        # Explicit synthetic schedule traversal: keep the real 500 ms heartbeat
        # policy alive mid-window, then reach the next exact 500 ms decision slot.
        self.clock.value += 250_000_000
        self.f.beat(seq=11,tick=350)
        self.clock.value += 250_000_000
        self.f.beat(seq=12,tick=600)
        self.channels.slot_window = 1

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

    def test_foreign_veto_during_original_wait_is_seen_before_pose_commit(self):
        self.arm(); errors = []
        def foreign():
            try: self.comp.stop('foreign')
            except c.CompositionRejected as error: errors.append(error)
        def during_wait():
            thread = threading.Thread(target=foreign); thread.start(); thread.join()
        self.api.wait_hook = during_wait
        self.assertFalse(self.step().committed)
        self.assertEqual(len(errors), 1); self.assert_no_pose()

    def test_progress_expiry_after_real_geometry_never_commits(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.arm(); original = self.comp._executor.prepare_step
        def prepare(*args):
            result = original(*args)
            self.clock.value = self.comp._progress.bound.deadline_ns
            return result
        with patch.object(self.comp._executor, 'prepare_step', prepare):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_progress_expiry_only_inside_commit_hits_actual_final_fence(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.arm(); original = self.comp._executor.commit_step
        def commit(prepared, before_commit):
            self.clock.value = self.comp._progress.bound.deadline_ns
            return original(prepared, before_commit)
        with patch.object(self.comp._executor, 'commit_step', commit):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_entire_step_ending_on_progress_deadline_is_rejected(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.arm()
        self.assertFalse(self.comp.step(expected_pose_revision=0, dt_ns=5_000_000).committed)
        self.assert_no_pose()

    def test_end_one_ns_before_progress_deadline_commits_with_exact_minimum(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.arm(); seen = []; original = self.comp._executor.commit_step
        def commit(prepared, before_commit):
            def observe_fence():
                value = before_commit(); seen.append(value); return value
            return original(prepared, observe_fence)
        with patch.object(self.comp._executor, 'commit_step', commit):
            result = self.comp.step(expected_pose_revision=0, dt_ns=4_999_999)
        self.assertTrue(result.committed)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].deadline_ns, self.comp._progress.bound.deadline_ns)
        self.assertEqual(seen[0].step_end_ns, seen[0].deadline_ns - 1)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision, 1)

    def test_exact_duplicate_later_receipt_does_not_renew_original_completion(self):
        self.arm(); gate = self.comp._progress; original = gate.bound
        record = self.comp._command_record
        self.clock.value += 10_000_000
        self.comp.accept_command(self.channels.event(record))
        self.assertIs(gate.bound, original)
        self.assertEqual(gate.bound.deadline_ns, original.completion_lower_ns + self.config.progress_max_age_ns)

    def test_changed_duplicate_invocation_is_rejected_without_new_freshness(self):
        self.arm(); record = self.comp._command_record
        proof = self.channels.last_completion
        with patch.object(self.channels, 'verify_completion', return_value=replace(proof, invocation_id=proof.invocation_id + 1)):
            with self.assertRaises(c.CompositionRejected): self.comp.accept_completion(self.channels.event(proof))
        self.assertTrue(self.comp._progress.revoked)
        self.assert_no_pose()

    def test_unrelated_new_completion_does_not_extend_old_command(self):
        self.arm(); old = self.comp._progress.bound
        record = self.comp._command_record
        proof = self.channels.last_completion
        self.clock.value += 10_000_000
        candidate = rt.runtime.envelope._parse_message(proof.candidate_raw)
        candidate.update(candidate_id=99, completed_monotonic_ns=self.clock.value)
        unrelated = replace(proof, candidate_raw=rt.encode(candidate), invocation_id=99,
            dispatch_lower_ns=self.clock.value, completion_lower_ns=self.clock.value,
            completion_upper_ns=self.clock.value)
        with patch.object(self.channels, 'verify_completion', return_value=unrelated) as lookup:
            self.comp.accept_completion(self.channels.event(unrelated))
        self.assertEqual(lookup.call_count, 1)
        self.assertIs(self.comp._progress.bound, old)
        self.comp.accept_command(self.channels.event(record))
        self.assertIs(self.comp._progress.bound, old)
        self.clock.value = old.deadline_ns
        self.assertFalse(self.step().committed)
        self.assertTrue(self.comp._progress.revoked)
        self.assert_no_pose()

    def test_expired_progress_cannot_be_restored_by_new_candidate(self):
        self.arm(); old = self.comp._progress.bound
        self.clock.value = old.deadline_ns
        with self.assertRaises(c.CompositionRejected): self.f.command(seq=4)
        self.assertIs(self.comp._progress.bound, old)
        self.assertTrue(self.comp._progress.revoked)
        self.assert_no_pose()

    def test_missing_original_completion_rejects_alive_actor(self):
        self.activate(); self.f.observe()
        with patch.object(self.channels, 'verify_completion', return_value=None):
            with self.assertRaises(c.CompositionRejected): self.f.command()
        self.assert_no_pose()

    def test_broker_stop_needs_no_inference_completion(self):
        self.activate()
        with patch.object(self.channels, 'verify_completion', side_effect=AssertionError('STOP must not ask')) as lookup:
            self.f.command(action=0)
        self.assertEqual(lookup.call_count, 0)
        self.assert_no_pose()

    def test_original_completion_lookup_time_cannot_refresh_initial_deadline(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.activate(); self.f.observe(); original = self.channels.verify_completion
        def slow(event, boot):
            result = original(event, boot)
            self.clock.value = self.comp._progress.initial_deadline
            return result
        with patch.object(self.channels, 'verify_completion', slow):
            with self.assertRaises(c.CompositionRejected): self.f.command()
        self.assertIsNone(self.comp._progress.bound)
        self.assert_no_pose()

    def test_revoke_during_original_wait_cannot_restore_progress(self):
        self.arm(); gate = self.comp._progress
        proof = self.channels.last_completion; raw = self.comp._command_record.raw
        refused = []
        def invalidate():
            gate.revoke()
            try: gate.admit(proof, raw, self.clock.value)
            except ValueError: refused.append(True)
        self.api.wait_hook = invalidate
        self.assertFalse(self.step().committed)
        self.assertEqual(refused, [True]); self.assertTrue(gate.revoked)
        self.assert_no_pose()

    def test_progress_clock_regression_retires_and_preserves_high_water(self):
        self.arm(); water = self.comp._progress.high_water
        self.clock.value = water - 1
        self.assertFalse(self.step().committed)
        self.assertEqual(self.comp._progress.high_water, water)
        self.assert_no_pose()

    def test_private_proof_identity_bounds_and_model_are_not_caller_claims(self):
        from enum import IntEnum
        class Disguised(IntEnum): ONE = 1
        self.arm(); proof = self.channels.last_completion
        raw = self.comp._command_record.raw
        bad_model = rt.runtime.envelope._parse_message(proof.candidate_raw)
        bad_model['model_sha256'] = 'b' * 64
        variants = [replace(proof, boot=replace(proof.boot)), replace(proof, source=object()),
            replace(proof, clock_domain=object()), replace(proof, candidate_raw=rt.encode(bad_model)),
            replace(proof, invocation_id=True), replace(proof, invocation_id=Disguised.ONE),
            replace(proof, invocation_id=0), replace(proof, dispatch_lower_ns=-1),
            replace(proof, completion_lower_ns=True), replace(proof, completion_upper_ns=1 << 63),
            replace(proof, completion_lower_ns=proof.completion_upper_ns + 1),
            replace(proof, completion_upper_ns=self.clock.value + 1),
            replace(proof, dispatch_lower_ns=self.comp._progress.started - 1)]
        for value in variants:
            with self.subTest(value=value):
                gate = c._ProgressGate(proof.boot, self.channels, self.comp._clock,
                    self.config.ai_model_sha256, self.config.progress_max_age_ns, self.clock.value)
                with self.assertRaises(ValueError): gate.admit(value, raw, self.clock.value)
                self.assertTrue(gate.revoked); self.assertIsNone(gate.bound)

    def test_invalid_progress_policy_rejects_before_any_acquisition(self):
        self.api.calls.clear()
        for age in (True, 0, -1, 1.5, 1 << 63):
            with self.subTest(age=age), patch.object(c, 'ActorRegistry') as registry:
                with self.assertRaises(ValueError): c.create_authority(replace(self.config, progress_max_age_ns=age))
                self.assertEqual(registry.call_count, 0)
        for model in ('', 'A' * 64, 'g' * 64, True):
            with self.subTest(model=model), patch.object(c, 'ActorRegistry') as registry:
                with self.assertRaises(ValueError): c.create_authority(replace(self.config, ai_model_sha256=model))
                self.assertEqual(registry.call_count, 0)
        self.assertEqual(self.api.calls, [])

    def test_original_actor_lifetime_can_be_shorter_than_progress(self):
        self.config = replace(self.config, actor_policy=replace(self.policy, sample_age_cap_ns=2_000_000))
        self.arm(); seen = []; original = self.comp._executor.commit_step
        def commit(prepared, before_commit):
            def observe():
                value = before_commit(); seen.append(value); return value
            return original(prepared, observe)
        with patch.object(self.comp._executor, 'commit_step', commit):
            self.assertTrue(self.step().committed)
        self.assertEqual(seen[0].deadline_ns, self.clock.value + 2_000_000)
        self.assertLess(seen[0].deadline_ns, self.comp._progress.bound.deadline_ns)

    def test_progress_expiry_during_original_wait_is_checked_after_sample(self):
        self.config = replace(self.config, progress_max_age_ns=5_000_000)
        self.arm(); self.clock.value = self.comp._progress.bound.deadline_ns - 500_000
        def cross_deadline(): self.clock.value += 500_000
        self.api.wait_hook = cross_deadline
        self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_new_completed_candidate_advances_bound_and_commits(self):
        self.config = replace(self.config, progress_max_age_ns=750_000_000)
        self.arm(); old = self.comp._progress.bound
        self.next_slot()
        self.f.observe(seq=10); self.f.command(seq=4, obs=10)
        current = self.comp._progress.bound
        self.assertGreater(current.command_seq, old.command_seq)
        self.assertGreater(current.invocation_id, old.invocation_id)
        self.assertGreater(current.deadline_ns, old.deadline_ns)
        self.assertTrue(self.step().committed)

    def test_old_command_replay_cannot_replace_new_completion(self):
        self.config = replace(self.config, progress_max_age_ns=750_000_000)
        self.arm(); record = self.comp._command_record
        self.next_slot()
        self.f.command(seq=4); current = self.comp._progress.bound
        with self.assertRaises(c.CompositionRejected): self.comp.accept_command(self.channels.event(record))
        self.assertIs(self.comp._progress.bound, current)
        self.assert_no_pose()

    def test_time_addition_overflow_never_produces_progress(self):
        self.arm(); proof = self.channels.last_completion
        raw = self.comp._command_record.raw
        with self.assertRaises(ValueError):
            c._ProgressGate(proof.boot, self.channels, self.comp._clock,
                self.config.ai_model_sha256, 2, c._MAX_NS - 1)
        gate = c._ProgressGate(proof.boot, self.channels, self.comp._clock,
            self.config.ai_model_sha256, c._MAX_NS - self.clock.value + 1, 0)
        with self.assertRaises(ValueError): gate.admit(proof, raw, self.clock.value)
        self.assertTrue(gate.revoked); self.assertIsNone(gate.bound)

    def test_channel_heartbeat_cannot_renew_inference_progress(self):
        self.arm(); original = self.comp._progress.bound
        self.clock.value += 10_000_000
        self.f.beat(seq=11, tick=110); self.comp.poll()
        self.assertIs(self.comp._progress.bound, original)
        self.clock.value = original.deadline_ns
        with self.assertRaises(c.CompositionRejected): self.comp.poll()
        self.assert_no_pose()

    def test_veto_after_actual_commit_keeps_receipt_fact_and_retires_admission(self):
        self.arm(); original = self.comp._runtime.step
        def after_commit(**kwargs):
            result = original(**kwargs)
            self.assertTrue(result.committed)
            def foreign():
                try: self.comp.stop('late foreign veto')
                except c.CompositionRejected: pass
            thread = threading.Thread(target=foreign); thread.start(); thread.join()
            return result
        with patch.object(self.comp._runtime, 'step', after_commit): result = self.step()
        self.assertTrue(result.committed)
        self.assertEqual(result.pose_revision, 1)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision, 1)
        self.assertNotEqual(self.comp.status().state, 'ACTIVE')
        self.assertFalse(self.step().committed)
