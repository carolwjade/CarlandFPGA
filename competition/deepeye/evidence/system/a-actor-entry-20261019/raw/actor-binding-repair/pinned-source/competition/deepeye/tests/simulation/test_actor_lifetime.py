"""Offline original-HANDLE samples and actual numerical runtime/executor veto."""
from dataclasses import replace
import threading
import unittest
from competition.deepeye.tests.simulation.test_actor_owner import OwnerFixture
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt
from competition.deepeye.simulation.authority import motion_executor as m
from competition.deepeye.simulation.authority.motion import passage_phase as p
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion import solid_clearance as s
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState


class ActorLifetimeTests(OwnerFixture):
    def setUp(self):
        super().setUp()
        self.actor = self.launch()
        self.f = rt.PcDirectRuntimeTests(); self.f.setUp()
        self.f.clock = self.clock
        self.f.provider = rt.fixture_provider(self.clock)
        self.f.owner = rt.runtime.PcDirectRuntime(run_id='run-1', dependencies=self.f.provider,
            clock=self.clock, heartbeat_timeout_ns=500_000_000)
        self.f.binding = replace(self.f.boot_binding(), ai_instance=self.actor.instance_id)
        self.f.provider.ai_lease = self.actor.ai_lease
        self.f.activate()
        body = w.Envelope(.4, .12, .52, 'offline numerical containment only', False)
        context = p.RunContext('run-1', 'fixture-scene', 1,
            w.Layout(g.Gate('front', 0, 0), g.Gate('back', 0, 0)), body, 'offline authority only')
        initial = p.initialize(context, RigidState((0, 0, 15.6), (0, 1, 0, 0), .25),
            gc.ErrorBounds(0., 0., 0.), pose_revision=0, monotonic_ns=0,
            error_budget_reference='explicit offline test').state
        self.ex = m.OwnedMotionExecutor(initial_state=initial, scene=s.Scene('fixture-scene', 'v1', (), ()),
            model=s.CapsuleModel('fixture', 'v1', .4, .12, .52),
            budget=m.GeometryBudget(0, 0, 0, 'offline exact fixture'))
        self.ex.activate_boot(self.f.binding)
        self.actor.bind_verified_boot(self.f.binding, runtime=self.f.owner, executor=self.ex)
        self.f.observe(); self.event = self.f.command()
        self.ex.admit_command(self.f.binding, self.event.raw)
        self.f.provider.prepare_step = self.ex.prepare_step
        self.f.provider.commit_step = self.ex.commit_step

    def sample(self): return self.actor.ai_lease(self.f.binding, self.clock.value)
    def assert_veto(self):
        self.assertNotEqual(self.actor.state, 'BOUND_ACTIVE')
        self.assertTrue(self.ex.controller_view().stopped)
        self.assertFalse(self.f.owner.step(expected_pose_revision=0, dt_ns=1_000_000).committed)

    def test_each_positive_lease_probes_original_handle_zero_and_uses_presample_deadline(self):
        self.api.calls.clear()
        first = self.sample(); self.clock.value += 1; second = self.sample()
        self.assertEqual([x for x in self.api.calls if x[0] == 'wait'], [('wait', 300, 0), ('wait', 300, 0)])
        self.assertEqual(first.deadline_ns, 1_020_000_000)
        self.assertEqual(second.deadline_ns, 1_020_000_001)
        self.assertEqual(first.instance_id, self.actor.instance_id)

    def test_signaled_process_even_with_terminal_exit259_revokes_both(self):
        self.api.live = False
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto(); self.api.live = True
        with self.assertRaises(ValueError): self.sample()

    def test_wait_failed_unexpected_boolean_and_exception_never_become_life(self):
        for result in (0xffffffff, 128, 1, True, None):
            with self.subTest(result=result):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                if result is None:
                    self.api.wait_hook = lambda: (_ for _ in ()).throw(OSError('probe failure'))
                else: self.api.wait_result = result
                with self.assertRaises((ValueError, OSError)): self.sample()
                self.assert_veto()

    def test_slow_sample_deadline_not_extended_by_completion_time(self):
        self.api.wait_hook = lambda: setattr(self.clock, 'value', 1_000_500_000)
        self.assertEqual(self.sample().deadline_ns, 1_020_000_000)

    def test_probe_budget_equal_and_excessive_elapsed_are_conservative_veto(self):
        self.api.wait_hook = lambda: setattr(self.clock, 'value', 1_001_000_000)
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto()

    def test_clock_regression_malformed_values_and_future_runtime_time_veto(self):
        for value in (999_999_999, True, -1, 'time'):
            with self.subTest(value=value):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                self.clock.value = value
                with self.assertRaises(ValueError): self.actor.ai_lease(self.f.binding, 1_000_000_000)
                self.assertTrue(self.ex.controller_view().stopped)

    def test_fixed_lifetime_deadline_cannot_be_renewed_by_positive_samples(self):
        self.clock.value = 2_990_000_000
        self.assertEqual(self.sample().deadline_ns, 3_000_000_000)
        self.clock.value = 3_000_000_000
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto()

    def test_attempted_closed_or_ambiguous_original_reference_veto_before_wait(self):
        for change in ('attempted', 'ambiguous', 'terminal_confirmed'):
            with self.subTest(change=change):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                setattr(self.actor._process, change, True); self.api.calls.clear()
                with self.assertRaises(ValueError): self.sample()
                self.assertFalse(any(x[0] == 'wait' for x in self.api.calls)); self.assert_veto()

    def test_replaced_reference_with_same_numeric_value_cannot_adopt(self):
        self.actor._process = replace(self.actor._process)
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto()

    def test_old_binding_generation_and_instance_cannot_sample_current_actor(self):
        for bad in (replace(self.f.binding, generation=2), replace(self.f.binding, ai_instance='caller-claim'),
                    replace(self.f.binding, run_id='wrong-run')):
            with self.subTest(bad=bad):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                with self.assertRaises(ValueError): self.actor.ai_lease(bad, self.clock.value)
                self.assert_veto()

    def test_bound_actor_cannot_rebind_even_to_new_boot_or_resurrect(self):
        with self.assertRaises(ValueError):
            self.actor.bind_verified_boot(replace(self.f.binding, generation=2), runtime=self.f.owner, executor=self.ex)
        self.assert_veto()

    def test_caught_reentrant_probe_or_close_does_not_restore_outer_sample(self):
        for action in ('sample', 'close'):
            with self.subTest(action=action):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                def nested():
                    try: self.sample() if action == 'sample' else self.actor.close('nested')
                    except ValueError: pass
                self.api.wait_hook = nested
                with self.assertRaises(ValueError): self.sample()
                self.assert_veto(); self.assertNotIn(('close', 300), self.api.calls)

    def test_caught_reentry_from_clock_also_vetoes(self):
        def nested():
            try: self.sample()
            except ValueError: pass
        self.clock.hook = nested
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto()

    def test_malformed_arguments_including_receiver_keyword_latch(self):
        with self.assertRaises(ValueError): self.actor.ai_lease(self=self.actor)
        self.assert_veto()

    def test_none_boolean_or_text_runtime_now_cannot_bypass_clock_shape(self):
        for value in (None, True, -1, 'time'):
            with self.subTest(value=value):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                with self.assertRaises(ValueError): self.actor.ai_lease(self.f.binding, value)
                self.assert_veto()

    def test_release_or_replacement_during_probe_cannot_return_positive_lease(self):
        for action in ('release', 'replace', 'native'):
            with self.subTest(action=action):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                def mutate():
                    if action == 'release': self.actor._process.attempted = True
                    elif action == 'native': self.actor._process.native = 999
                    else: self.actor._process = replace(self.actor._process)
                self.api.wait_hook = mutate
                with self.assertRaises(ValueError): self.sample()
                self.assert_veto()

    def test_revocation_callback_reentry_is_bounded_and_still_reaches_executor(self):
        calls = []
        def stop(reason):
            calls.append(reason)
            if len(calls) > 1: raise AssertionError('recursive STOP dispatch')
            try: self.actor.close('caught callback reentry')
            except ValueError: pass
        self.actor._stop = stop; self.api.live = False
        with self.assertRaises(ValueError): self.sample()
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.ex.controller_view().stopped)

    def test_wrong_thread_sets_pending_veto_and_next_owner_entry_revokes(self):
        errors = []
        def foreign():
            try: self.sample()
            except ValueError: errors.append(True)
        t = threading.Thread(target=foreign); t.start(); t.join()
        self.assertEqual(errors, [True])
        with self.assertRaises(ValueError): self.sample()
        self.assert_veto()

    def test_stop_callback_failure_cannot_skip_executor_revoke_or_original_probe_error(self):
        def broken_stop(reason): raise RuntimeError('stop failed')
        self.actor._stop = broken_stop
        self.api.wait_hook = lambda: (_ for _ in ()).throw(OSError('original sample failure'))
        with self.assertRaisesRegex(OSError, 'original sample failure'): self.sample()
        self.assertTrue(self.ex.controller_view().stopped); self.assertTrue(self.actor._callback_errors)

    def test_real_runtime_executor_success_uses_current_samples_and_one_pose_commit(self):
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertTrue(result.committed, result.reason); self.assertEqual(self.ex.renderer_view().pose_revision, 1)

    def test_death_during_geometry_preparation_vetoes_pending_pose(self):
        original = self.ex.prepare_step
        def prepare(*args):
            prepared = original(*args); self.api.live = False; return prepared
        self.f.provider.prepare_step = prepare
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertFalse(result.committed); self.assertEqual(self.ex.renderer_view().pose_revision, 0); self.assert_veto()

    def test_final_sample_death_vetoes_actual_executor_and_clears_pending(self):
        original = self.ex.commit_step
        def commit(prepared, fence):
            self.api.live = False; return original(prepared, fence)
        self.f.provider.commit_step = commit
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertFalse(result.committed); self.assertEqual(self.ex.renderer_view().pose_revision, 0)
        self.assertTrue(self.ex.controller_view().stopped); self.assertEqual(self.ex._pending, {})

    def test_death_after_last_successful_sample_is_an_explicit_observation_gap(self):
        original = self.ex.commit_step
        def commit(prepared, fence):
            def checked_then_death():
                checked = fence(); self.api.live = False; return checked
            return original(prepared, checked_then_death)
        self.f.provider.commit_step = commit
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertTrue(result.committed, 'a past sample cannot prove future survival')
        self.assertEqual(self.ex.renderer_view().pose_revision, 1)
        with self.assertRaises(ValueError): self.sample()
        self.assertTrue(self.ex.controller_view().stopped)

    def test_unbound_actor_readiness_timeout_and_no_lease_before_boot(self):
        other = self.launch()
        with self.assertRaises(ValueError): other.ai_lease(self.f.binding, self.clock.value)
        self.assertNotEqual(other.state, 'BOUND_ACTIVE')
        other = self.launch(); self.clock.value += 50_000_000
        with self.assertRaises(ValueError): other.poll()
        self.assertEqual(other.state, 'REVOKED')

    def test_new_actor_identity_is_distinct_and_old_boot_cannot_bind_replacement(self):
        other = self.launch()
        self.assertNotEqual(other.instance_id, self.actor.instance_id)
        with self.assertRaises(ValueError):
            other.bind_verified_boot(self.f.binding, runtime=self.f.owner, executor=self.ex)
        self.assertNotEqual(other.state, 'BOUND_ACTIVE')

    def test_clock_callback_cannot_rebind_the_actual_wait_target(self):
        self.clock.hook = lambda: setattr(self.actor._process, 'native', 999)
        self.api.calls.clear()
        with self.assertRaises(ValueError): self.sample()
        self.assertFalse(any(x[0] == 'wait' for x in self.api.calls))
        self.assert_veto()

    def test_sealed_or_detached_registry_owner_cannot_continue_or_skip_revoke(self):
        for change in ('sealed', 'detached'):
            with self.subTest(change=change):
                if self.actor.state != 'BOUND_ACTIVE': self.setUp()
                if change == 'sealed': self.actor._resources._sealed = True
                else: self.registry._owners.clear()
                with self.assertRaises(ValueError): self.sample()
                self.assertTrue(self.ex.controller_view().stopped)

    def test_real_probe_typeerror_preserves_original_exception(self):
        primary = TypeError('native boundary failure')
        def fail(): raise primary
        self.api.wait_hook = fail
        with self.assertRaises(TypeError) as caught: self.sample()
        self.assertIs(caught.exception, primary)
        self.assertTrue(self.ex.controller_view().stopped)

    def test_partial_authority_activation_failure_retires_both_owners(self):
        other = self.launch()
        boot = replace(self.f.binding, generation=2, context_json=rt.encode(dict(rt.PC, session=8)), ai_instance=other.instance_id)
        self.f.owner.boot(boot)  # Numerical fixture verifier only, not real BOOT authentication.
        with self.assertRaises(ValueError):
            other.bind_verified_boot(boot, runtime=self.f.owner, executor=self.ex)
        self.assertTrue(self.ex.controller_view().stopped)
        self.assertTrue(self.f.owner._latched)

    def test_replacement_requires_new_instance_boot_and_can_then_commit(self):
        old_id = self.actor.instance_id
        self.actor.close('retire old actor')
        other = self.launch()
        self.f.binding = replace(self.f.boot_binding(generation=2, session=8), ai_instance=other.instance_id)
        self.f.activate(); self.ex.activate_boot(self.f.binding)
        other.bind_verified_boot(self.f.binding, runtime=self.f.owner, executor=self.ex)
        self.f.provider.ai_lease = other.ai_lease
        self.f.observe(); event = self.f.command(); self.ex.admit_command(self.f.binding, event.raw)
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertTrue(result.committed, result.reason)
        self.assertNotEqual(old_id, other.instance_id)
        self.assertEqual(self.actor.state, 'CLOSED')

    def test_actual_executor_rejects_fixed_lifetime_deadline_equality(self):
        for i, now in enumerate((1_400_000_000, 1_800_000_000, 2_200_000_000, 2_600_000_000, 2_990_000_000), 1):
            self.clock.value = now; self.f.beat(seq=10 + i, tick=100 + i)
        self.f.observe(seq=10)
        event = self.f.command(seq=4, obs=10)
        self.ex.admit_command(self.f.binding, event.raw)
        result = self.f.owner.step(expected_pose_revision=0, dt_ns=10_000_000)
        self.assertFalse(result.committed)
        self.assertEqual(self.ex.renderer_view().pose_revision, 0)
        self.assertTrue(self.ex.controller_view().stopped)

    def test_first_probe_failure_is_preserved_in_private_teardown_receipt(self):
        import json
        primary = OSError('first native sample failure')
        def fail(): raise primary
        self.api.wait_hook = fail
        with self.assertRaises(OSError): self.sample()
        self.actor.close('teardown after failure')
        record = json.loads((self.actor._root / 'receipt.json').read_bytes())
        self.assertIn('primary_error', record, 'private evidence discarded original probe failure')
        self.assertEqual(record['primary_error']['message'], 'first native sample failure')
        self.assertIs(self.actor._primary_error, primary)

    def test_closed_and_quarantined_old_entries_cannot_stop_fresh_boot(self):
        for quarantine in (False, True):
            for action in ('close', 'poll', 'lease', 'malformed'):
                with self.subTest(quarantine=quarantine, action=action):
                    self.setUp()
                    old, old_boot = self.actor, self.f.binding
                    self.api.close_ok = not quarantine
                    old.close('retire original activation')
                    self.assertEqual(old.state, 'QUARANTINED' if quarantine else 'CLOSED')
                    self.api.close_ok = True
                    fresh = self.launch()
                    boot = replace(self.f.boot_binding(generation=2, session=8), ai_instance=fresh.instance_id)
                    self.f.binding = boot; self.f.activate(); self.ex.activate_boot(boot)
                    fresh.bind_verified_boot(boot, runtime=self.f.owner, executor=self.ex)
                    self.f.provider.ai_lease = fresh.ai_lease
                    self.f.observe(); event = self.f.command(); self.ex.admit_command(boot, event.raw)
                    native = list(self.api.calls)
                    try:
                        if action == 'close': old.close('late repeat')
                        elif action == 'poll': old.poll()
                        elif action == 'lease': old.ai_lease(old_boot, self.clock.value)
                        else: old.ai_lease()
                    except ValueError: pass
                    self.assertEqual(native, self.api.calls)
                    self.assertFalse(self.f.owner._latched)
                    self.assertFalse(self.ex.controller_view().stopped)
                    self.assertTrue(self.f.owner.step(expected_pose_revision=0, dt_ns=1_000_000).committed)

    def test_old_callbacks_fence_runtime_and_executor_activations_independently(self):
        for advanced in ('runtime', 'executor'):
            with self.subTest(advanced=advanced):
                self.setUp()
                old = self.actor; old.close('retire')
                boot = replace(self.f.boot_binding(generation=2, session=8), ai_instance='future verified fixture')
                if advanced == 'runtime': self.f.owner.boot(boot)
                else: self.ex.activate_boot(boot)
                runtime_veto = self.f.owner._veto_generation
                executor_veto = self.ex._root.revoke_generation
                with self.assertRaises(ValueError): old.poll()
                self.assertEqual(self.f.owner._veto_generation - runtime_veto, 0 if advanced == 'runtime' else 1)
                self.assertEqual(self.ex._root.revoke_generation - executor_veto, 0 if advanced == 'executor' else 1)
                if advanced == 'runtime': self.assertFalse(self.f.owner._latched)
                else: self.assertFalse(self.ex.controller_view().stopped)

    def test_same_original_activation_still_receives_both_revocations(self):
        runtime_veto = self.f.owner._veto_generation
        executor_veto = self.ex._root.revoke_generation
        self.actor.close('original activation STOP')
        self.assertGreater(self.f.owner._veto_generation, runtime_veto)
        self.assertGreater(self.ex._root.revoke_generation, executor_veto)
        self.assertTrue(self.f.owner._latched); self.assertTrue(self.ex.controller_view().stopped)

    def test_stop_callback_advancing_executor_cannot_revoke_new_executor_after_return(self):
        boot = replace(self.f.boot_binding(generation=2, session=8), ai_instance='new fixture activation')
        stop = self.actor._stop
        def advance(reason):
            stop(reason)
            self.ex.activate_boot(boot)
        self.actor._stop = advance
        self.api.live = False
        with self.assertRaises(ValueError): self.sample()
        self.assertTrue(self.f.owner._latched)
        self.assertFalse(self.ex.controller_view().stopped)
        self.assertIs(self.ex.authority_snapshot().boot, boot)


if __name__ == '__main__': unittest.main()
