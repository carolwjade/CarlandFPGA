"""New v2 composition controls, with synthetic upstream/native/clock evidence.

Only construction helpers are borrowed. No old TestCase is inherited/discovered.
Mailbox, composition, runtime, full geometry, executor and CAS remain real code.
"""
from dataclasses import replace
import threading
from unittest.mock import patch

from . import test_candidate_owner as fixture
from . import test_actor_owner as owners
from ...integration import candidate_mailbox as mailbox

c, rt = fixture.c, fixture.rt
S, E, W = 210_000_000, 220_000_000, 10_000_000


class PcDirectWindowCompositionTests(owners.OwnerFixture):
    def setUp(self):
        super().setUp()
        self.f = rt.PcDirectRuntimeTests(); self.f.setUp(); self.f.clock = self.clock
        self.channels = fixture.StatefulChannels(self.f)
        geom = fixture.ac.mt.MotionExecutorTests(); geom.setUp()
        initial = fixture.ac.mt.p.initialize(geom.ctx,
            fixture.ac.mt.RigidState((0,0,15.6),(0,1,0,0),.25),
            fixture.ac.mt.gc.ErrorBounds(0.,0.,0.),pose_revision=0,monotonic_ns=0,
            error_budget_reference='new offline v2 fixture, upstream/native/time synthetic').state
        self.config = c.AuthorityConfig(actor_policy=self.policy,initial_state=initial,
            scene=geom.scene,model=geom.model,budget=geom.budget,
            heartbeat_timeout_ns=500_000_000,max_slices=16,
            progress_max_age_ns=100_000_000,ai_model_sha256='a'*64)
        clock_patch = patch.object(c,'monotonic_ns',self.clock)
        clock_patch.start(); self.addCleanup(clock_patch.stop)
        self.comp = None; self.addCleanup(self.close_fixture)
        self.assertIn('pc_direct_window_v2', c.AuthorityConfig.__dataclass_fields__,
                      'composition must explicitly bind the v2 policy')
        self.config = replace(self.config, pc_direct_window_v2=mailbox.PcDirectWindowV2(W))

    create = fixture.CandidateOwnerTests.create
    close_fixture = fixture.CandidateOwnerTests.close_fixture
    activate = fixture.CandidateOwnerTests.activate
    proof = fixture.CandidateOwnerTests.proof
    offer = fixture.CandidateOwnerTests.offer
    record = fixture.CandidateOwnerTests.record
    slot = fixture.CandidateOwnerTests.slot
    command = fixture.CandidateOwnerTests.command
    step = fixture.CandidateOwnerTests.step
    assert_no_pose = fixture.CandidateOwnerTests.assert_no_pose

    def pending(self, age=None):
        self.activate(age=age); self.f.observe()
        proof = self.proof(); self.assertTrue(self.offer(proof))
        return proof

    def armed(self, age=None):
        proof = self.pending(age)
        self.clock.value = S+1
        return proof, self.command(proof)

    def test_v2_one_ns_late_keeps_original_proof_and_commits_real_pose(self):
        proof,_ = self.armed()
        self.assertIs(self.comp._candidates._current[1],proof)
        self.assertEqual(self.comp._candidates._mailbox.snapshot()['last_consumed_window'],0)
        self.assertTrue(self.step().committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)

    def test_slot_verifier_returning_at_close_uses_refreshed_actual_now(self):
        proof = self.pending(); self.clock.value = S+1
        original = self.channels.verify_slot
        def at_close(event,boot):
            result = original(event,boot); self.clock.value = E; return result
        with patch.object(self.channels,'verify_slot',at_close):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assertIsNone(self.comp._runtime._command)
        self.assert_no_pose()

    def test_exact_committed_duplicate_after_close_never_reconsumes_or_renews(self):
        proof,record = self.armed(); bound = self.comp._progress.bound
        self.clock.value = E+1
        with patch.object(self.channels,'verify_slot',side_effect=AssertionError('no new grant')):
            self.comp.accept_command(self.channels.event(record))
        self.assertIs(self.comp._progress.bound,bound)
        self.assertIs(self.comp._candidates._current[1],proof)
        self.assertIsNone(self.comp._candidates._pending)
        self.assertFalse(self.offer(replace(proof)))
        self.assertIsNone(self.comp._candidates._pending)

    def test_new_request_sequence_cannot_revive_consumed_candidate(self):
        proof,_ = self.armed()
        with self.assertRaises(c.CompositionRejected): self.command(proof,sequence=4)
        self.assertIsNone(self.comp._candidates._pending); self.assert_no_pose()

    def test_changed_target_consumes_once_then_retires_without_rollback(self):
        proof = self.pending(); self.clock.value = S+1
        record = self.record(proof)
        document = rt.runtime.envelope._parse_message(record.raw)
        document['target']['yaw_q'] = 1
        record = replace(record,raw=rt.encode(document))
        with self.assertRaises(c.CompositionRejected):
            self.comp.accept_command(self.channels.event(record),slot_event=self.slot())
        self.assertEqual(self.comp._candidates._mailbox.snapshot()['last_consumed_window'],0)
        self.assertIsNone(self.comp._candidates._pending)
        with self.assertRaises(c.CompositionRejected): self.offer(proof)
        self.assert_no_pose()

    def test_wrong_original_completion_source_retires(self):
        self.activate(); self.f.observe()
        with self.assertRaises(c.CompositionRejected):
            self.offer(self.proof(source=object()))
        self.assert_no_pose()

    def test_original_progress_deadline_at_final_callback_refuses_cas(self):
        self.armed(age=5_000_000)
        original = self.comp._executor.commit_step
        def commit(prepared,before_commit):
            self.clock.value = 215_000_000
            return original(prepared,before_commit)
        with patch.object(self.comp._executor,'commit_step',commit):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_final_handle_sample_crossing_original_deadline_refuses_cas(self):
        self.armed(age=5_000_000)
        self.clock.value = 214_500_000
        self.api.wait_hook = lambda: setattr(self.clock,'value',215_000_000)
        self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_entire_dt_end_equal_original_deadline_refuses(self):
        self.armed(age=5_000_000)
        self.assertFalse(self.comp.step(expected_pose_revision=0,dt_ns=4_999_999).committed)
        self.assert_no_pose()

    def test_broker_stop_needs_no_slot_and_clears_pending(self):
        self.pending()
        raw = rt.encode(rt.request_document(
            context=rt.runtime.envelope._parse_message(self.comp._boot.context_json),
            command_seq=3,candidate_id=3,issue=self.clock.value,
            target_value=dict(action=0,yaw_q=0,pitch_q=0,speed_code=0,duration_ms=0),
            observation=None))
        with patch.object(self.channels,'verify_slot',side_effect=AssertionError('STOP has no grant')):
            self.comp.accept_command(self.channels.event(rt.runtime.VerifiedEnvelope(self.comp._boot,raw)))
        self.assertIsNone(self.comp._candidates._pending); self.assert_no_pose()

    def test_entire_dt_end_one_ns_before_original_deadline_commits(self):
        self.armed(age=5_000_000)
        self.assertTrue(self.comp.step(expected_pose_revision=0,dt_ns=4_999_998).committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)

    def test_reentry_during_slot_callback_retires_pending(self):
        proof = self.pending(); original = self.channels.verify_slot
        self.clock.value = S+1
        def grant(event,boot):
            record = original(event,boot)
            try: self.comp.stop('reentrant fixture STOP')
            except c.CompositionRejected: pass
            return record
        with patch.object(self.channels,'verify_slot',grant):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assertIsNone(self.comp._candidates._pending); self.assert_no_pose()

    def test_post_cas_veto_preserves_positive_commit_fact(self):
        self.armed(); original = self.comp._runtime.step
        def after_commit(**kwargs):
            result = original(**kwargs)
            self.comp._foreign.set()
            return result
        with patch.object(self.comp._runtime,'step',after_commit):
            result = self.step()
        self.assertTrue(result.committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)
        self.assertNotEqual(self.comp.status().state,'ACTIVE')

    def test_foreign_thread_veto_during_slot_callback_retires(self):
        proof = self.pending(); original = self.channels.verify_slot
        self.clock.value = S+1
        def grant(event,boot):
            record = original(event,boot)
            def veto():
                try: self.comp.stop('foreign fixture STOP')
                except c.CompositionRejected: pass
            worker = threading.Thread(target=veto); worker.start(); worker.join()
            return record
        with patch.object(self.channels,'verify_slot',grant):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()

    def test_invalid_config_refuses_before_production_gate_or_acquisition(self):
        class IntegerSubclass(int): pass
        for policy in (True,object(),mailbox.PcDirectWindowV2(True),mailbox.PcDirectWindowV2(0),
                       mailbox.PcDirectWindowV2(IntegerSubclass(W)),
                       mailbox.PcDirectWindowV2((1<<63))):
            with self.subTest(policy=policy),patch.object(c,'ActorRegistry') as registry,\
                 patch.object(c,'_production_channels',side_effect=AssertionError('invalid policy')):
                with self.assertRaises(ValueError): c.create_authority(replace(self.config,pc_direct_window_v2=policy))
                registry.assert_not_called()
        with patch.object(c,'ActorRegistry') as registry:
            with self.assertRaises(c.ActivationUnavailable): c.create_authority(self.config)
            registry.assert_not_called()

    def test_width_equal_period_retires_activation_instead_of_legacy_fallback(self):
        self.config = replace(self.config,pc_direct_window_v2=mailbox.PcDirectWindowV2(500_000_000))
        with self.assertRaises(c.CompositionRejected): self.activate()
        self.assertNotEqual(self.comp.status().state,'ACTIVE')
        self.assertIsNone(self.comp._candidates)
