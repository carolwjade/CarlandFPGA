"""Stateful owner integration; upstream, native and clock evidence is synthetic."""
from dataclasses import replace
import importlib
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from . import test_actor_composition as ac
from .test_actor_owner import OwnerFixture

c, rt = ac.c, ac.rt
try:
    co = importlib.import_module('competition.deepeye.simulation.authority.candidate_owner')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.authority.candidate_owner': raise
    co = None


def fixture_record(name, **fields):
    # Prior-to-implementation RED can still exercise the old owner ignoring
    # these new mandatory callbacks; this fallback is confined to test records.
    return (getattr(co, name) if co is not None else SimpleNamespace)(**fields)


class StatefulChannels(ac.FakeChannels):
    """Synthetic original opaque events, never a production verifier."""
    origin = 0
    window = 0
    def verify_boot(self, event, **kwargs):
        binding=super().verify_boot(event,**kwargs)
        if co is not None:
            context=rt.runtime.envelope._parse_message(binding.context_json)
            document=co.boot_profile.load_document(Path(co.__file__).resolve().parents[2]/'docs/boot_profiles.json')
            context['boot_sha256']=co.boot_profile.canonical_sha256(document).hex()
            binding=replace(binding,context_json=rt.encode(context))
        return binding
    def mailbox_activation_for_boot(self, boot):
        self.checkpoint()
        return fixture_record('_MailboxActivation',boot=boot,source=self,
            clock_domain=c.monotonic_ns,slot_origin_ns=self.origin,
            usb_upper_ns=0,packing_upper_ns=0)
    def verify_completion(self, event, boot): return self._verify(event)
    def verify_slot(self, event, boot): return self._verify(event)
    def completion_for_command(self, *args):
        raise AssertionError('legacy command lookup must never be used')


class CandidateOwnerTests(OwnerFixture):
    def setUp(self):
        super().setUp()
        self.f=rt.PcDirectRuntimeTests(); self.f.setUp(); self.f.clock=self.clock
        self.channels=StatefulChannels(self.f)
        geom=ac.mt.MotionExecutorTests(); geom.setUp()
        initial=ac.mt.p.initialize(geom.ctx,ac.mt.RigidState((0,0,15.6),(0,1,0,0),.25),
            ac.mt.gc.ErrorBounds(0.,0.,0.),pose_revision=0,monotonic_ns=0,
            error_budget_reference='explicit offline stateful composition fixture').state
        self.config=c.AuthorityConfig(actor_policy=self.policy,initial_state=initial,
            scene=geom.scene,model=geom.model,budget=geom.budget,
            heartbeat_timeout_ns=500_000_000,max_slices=16,
            progress_max_age_ns=100_000_000,ai_model_sha256='a'*64)
        self.clock_patch=patch.object(c,'monotonic_ns',self.clock)
        self.clock_patch.start(); self.addCleanup(self.clock_patch.stop)
        self.comp=None; self.addCleanup(self.close_fixture)
    create = ac.ActorCompositionTests.create
    close_fixture = ac.ActorCompositionTests.close_fixture
    step = ac.ActorCompositionTests.step
    assert_no_pose = ac.ActorCompositionTests.assert_no_pose

    def activate(self, *, now=210_000_000, age=None):
        self.clock.value = now
        if age is not None: self.config = replace(self.config,progress_max_age_ns=age)
        self.channels = StatefulChannels(self.f)
        self.create()
        self.comp.accept_boot(self.channels.ready)
        self.f.binding = self.comp._boot
        self.f.owner = SimpleNamespace(
            board=lambda r:self.comp.accept_board(self.channels.event(r)),
            observe=lambda r:self.comp.accept_observation(self.channels.event(r)))
        self.f.beat()

    def proof(self, candidate=3, obs=9, **changes):
        now = self.clock.value
        context = rt.runtime.envelope._parse_message(self.comp._boot.context_json)
        target = dict(action=1,yaw_q=0,pitch_q=0,speed_code=5,duration_ms=1000)
        raw = rt.encode(dict(schema_version=1,kind='model_candidate',context=context,
            candidate_id=candidate,model_sha256='a'*64,
            observation=dict(context=context,observed_seq=obs),target=target,
            completed_monotonic_ns=now))
        proof = c._CompletedInference(self.comp._boot,self.channels,self.comp._clock,
            raw,candidate+1,now,now,now)
        return replace(proof,**changes)

    def offer(self, proof):
        return self.comp.accept_completion(self.channels.event(proof))

    def record(self, proof, sequence=None):
        candidate = rt.runtime.envelope._parse_message(proof.candidate_raw)
        return rt.runtime.VerifiedEnvelope(self.comp._boot,rt.encode(rt.request_document(
            context=candidate['context'],command_seq=candidate['candidate_id'] if sequence is None else sequence,
            candidate_id=candidate['candidate_id'],issue=self.clock.value,
            target_value=candidate['target'],observation=candidate['observation'])))

    def slot(self, window=0):
        return self.channels.event(fixture_record('_VerifiedSlot',boot=self.comp._boot,
            source=self.channels,clock_domain=self.comp._clock,window_index=window))

    def command(self, proof, sequence=None):
        record = self.record(proof,sequence)
        self.comp.accept_command(self.channels.event(record),slot_event=self.slot())
        return record

    def arm(self, **kwargs):
        self.activate(**kwargs); self.f.observe()
        proof = self.proof()
        self.offer(proof)
        return proof,self.command(proof)

    def test_opposite_completion_order_preserves_original_newer_proof_and_real_cas(self):
        self.activate(); self.f.observe(seq=9); self.f.observe(seq=10)
        older,newer = self.proof(9,9),self.proof(10,10)
        self.assertTrue(self.offer(newer)); self.assertFalse(self.offer(older))
        self.command(newer)
        self.assertIs(self.comp._candidates._current[1],newer)
        self.assertTrue(self.step().committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)

    def test_completion_callback_cannot_renew_initial_progress_deadline(self):
        self.activate(age=5_000_000); self.f.observe(); proof=self.proof()
        original=self.channels.verify_completion
        def slow(event,boot):
            value=original(event,boot); self.clock.value=self.comp._progress.initial_deadline; return value
        with patch.object(self.channels,'verify_completion',slow):
            with self.assertRaises(c.CompositionRejected): self.offer(proof)
        self.assertIsNone(self.comp._progress.bound); self.assert_no_pose()

    def test_late_slot_verifier_uses_actual_time_and_refuses_one_ns_late(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        original=self.channels.verify_slot
        def slow(event,boot):
            value=original(event,boot); self.clock.value+=1; return value
        with patch.object(self.channels,'verify_slot',slow):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assertIsNone(self.comp._runtime._command); self.assert_no_pose()

    def test_late_command_verifier_cannot_substitute_nominal_slot_time(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        original=self.channels.verify_command
        def slow(event,boot):
            value=original(event,boot); self.clock.value+=1; return value
        with patch.object(self.channels,'verify_command',slow):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()

    def test_reentrant_stop_in_completion_callback_retires_before_cleanup(self):
        self.activate(); self.f.observe(); proof=self.proof(); seen=[]
        original=self.channels.verify_completion
        def stop(event,boot):
            value=original(event,boot)
            try: self.comp.stop('during completion')
            except c.CompositionRejected: pass
            seen.append(self.comp._candidates._mailbox.snapshot()['stopped'])
            return value
        with patch.object(self.channels,'verify_completion',stop):
            with self.assertRaises(c.CompositionRejected): self.offer(proof)
        self.assertEqual(seen,[True]); self.assert_no_pose()
        self.assertIsNone(self.comp._candidates._pending)
        self.assertIsNone(self.comp._candidates._current)

    def test_foreign_stop_in_slot_callback_vetoes_no_foreign_native_effect(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        original=self.channels.verify_slot; effects=[]
        def stop(event,boot):
            value=original(event,boot)
            def foreign():
                before=list(self.api.calls)
                try: self.comp.stop('foreign')
                except c.CompositionRejected: pass
                effects.append(self.api.calls==before)
            t=threading.Thread(target=foreign); t.start(); t.join()
            return value
        with patch.object(self.channels,'verify_slot',stop):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assertEqual(effects,[True]); self.assert_no_pose()

    def test_retired_owner_cannot_reboot_and_fresh_owner_rejects_old_proof(self):
        proof,_=self.arm(); self.comp.stop('new session')
        with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        old=self.comp
        self.channels=StatefulChannels(self.f)
        binding=self.f.boot_binding(generation=2,session=8)
        self.channels.fixture=SimpleNamespace(boot_binding=lambda:binding)
        self.create(); self.comp.accept_boot(self.channels.ready)
        with self.assertRaises(c.CompositionRejected): self.offer(proof)
        self.assertTrue(old._candidates._mailbox.snapshot()['stopped'])
        self.assert_no_pose()

    def test_duplicate_completion_never_requeues_and_command_needs_no_second_slot(self):
        proof,record=self.arm(); bound=self.comp._progress.bound
        self.assertFalse(self.offer(replace(proof)))
        self.assertIsNone(self.comp._candidates._pending)
        self.clock.value+=1
        with patch.object(self.channels,'verify_slot',side_effect=AssertionError('duplicate slot')), \
             patch.object(self.channels,'verify_completion',side_effect=AssertionError('duplicate completion')):
            self.comp.accept_command(self.channels.event(record))
        self.assertIs(self.comp._progress.bound,bound)
        self.assertIs(self.comp._candidates._current[1],proof)

    def test_changed_completion_bounds_refuse_original_identity(self):
        proof,_=self.arm()
        with self.assertRaises(c.CompositionRejected):
            self.offer(replace(proof,dispatch_lower_ns=proof.dispatch_lower_ns+1))
        self.assert_no_pose()

    def test_new_numbered_command_cannot_reuse_consumed_proof(self):
        proof,_=self.arm()
        with self.assertRaises(c.CompositionRejected): self.command(proof,sequence=4)
        self.assert_no_pose()

    def test_pending_history_bounded_and_new_completion_does_not_renew_current(self):
        original,_=self.arm(); bound=self.comp._progress.bound
        for seq in range(10,80):
            self.f.observe(seq=seq)
            self.offer(self.proof(seq,seq))
        self.assertIs(self.comp._progress.bound,bound)
        self.assertIs(self.comp._candidates._current[1],original)
        self.assertEqual(self.comp._candidates._mailbox.snapshot()['observation_count'],4)
        self.assertEqual(self.comp._candidates._pending.invocation_id,80)
        self.assertIsNone(self.comp._input_transaction)

    def test_slot_equal_completion_deadline_refuses(self):
        self.activate(now=209_999_999,age=1); self.f.observe(); proof=self.proof(); self.offer(proof)
        self.clock.value=210_000_000
        self.assertIsNone(self.comp._candidates._mailbox.plan(self.clock.value,
            grant=co.mailbox.SlotGrant(self.comp._boot.generation,0)))
        with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()

    def test_one_ns_full_step_ending_at_deadline_cannot_cas(self):
        self.arm(age=1)
        self.assertFalse(self.comp.step(expected_pose_revision=0,dt_ns=1).committed)
        self.assert_no_pose()

    def test_one_ns_inside_full_step_deadline_uses_real_executor(self):
        self.arm(age=2)
        self.assertTrue(self.comp.step(expected_pose_revision=0,dt_ns=1).committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)

    def test_five_ms_policy_cannot_wait_for_next_500ms_slot(self):
        proof,_=self.arm(age=5_000_000)
        self.clock.value+=500_000_000
        with self.assertRaises(c.CompositionRejected): self.offer(self.proof(4,9))
        self.assert_no_pose()

    def test_missing_activation_provider_refuses_and_factory_still_closed(self):
        self.channels=StatefulChannels(self.f); self.clock.value=210_000_000
        self.channels.mailbox_activation_for_boot=None; self.create()
        with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assert_no_pose()
        self.api.calls.clear()
        with patch.object(c,'ActorRegistry') as registry:
            with self.assertRaises(c.ActivationUnavailable): c.create_authority(self.config)
        self.assertEqual(registry.call_count,0); self.assertEqual(self.api.calls,[])

    def test_plain_proof_and_boolean_cannot_bypass_original_verifier(self):
        self.activate(); self.f.observe(); proof=self.proof()
        with self.assertRaises(c.CompositionRejected): self.comp.accept_completion(proof)
        self.assert_no_pose()

    def test_completion_verifier_wrong_records_source_clock_model_and_overflow_refuse(self):
        for variant in ('boolean','selection','association','c_ordinal','boot',
                        'source','clock','model','overflow','future'):
            with self.subTest(variant=variant):
                self.activate(); self.f.observe(); proof=self.proof()
                candidate=rt.runtime.envelope._parse_message(proof.candidate_raw)
                candidate['model_sha256']='b'*64
                values={
                    'boolean':True,
                    'selection':co.mailbox.Selection(1,self.comp._boot.context_json,'PC_DIRECT',
                        0,self.clock.value,self.clock.value+1,self.clock.value,self.clock.value,
                        3,4,proof.candidate_raw),
                    'association':SimpleNamespace(qualified=True),
                    'c_ordinal':dict(generation_ordinal=1,sent_ordinal=9,payload=proof.candidate_raw),
                    'boot':replace(proof,boot=replace(proof.boot)),
                    'source':replace(proof,source=object()),
                    'clock':replace(proof,clock_domain=object()),
                    'model':replace(proof,candidate_raw=rt.encode(candidate)),
                    'overflow':replace(proof,completion_upper_ns=1<<63),
                    'future':replace(proof,completion_upper_ns=self.clock.value+1)}
                with patch.object(self.channels,'verify_completion',return_value=values[variant]):
                    with self.assertRaises(c.CompositionRejected): self.offer(proof)
                self.assert_no_pose()
                self.assertIsNone(self.comp._candidates._pending)
                self.comp.close('subtest ended')

    def test_missing_slot_provider_refuses_after_completion_without_consuming_fallback(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        with patch.object(self.channels,'verify_slot',None):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()
        self.assertIsNone(self.comp._candidates._pending)

    def test_wrong_activation_identity_and_unknown_transfer_bounds_refuse(self):
        for name in ('boot','source','clock_domain','usb_upper_ns','packing_upper_ns','slot_origin_ns'):
            with self.subTest(field=name):
                self.channels=StatefulChannels(self.f); self.clock.value=210_000_000; self.create()
                original=self.channels.mailbox_activation_for_boot
                def wrong(boot):
                    record=original(boot)
                    value=replace(boot) if name=='boot' else object() if name in ('source','clock_domain') else None
                    return replace(record,**{name:value})
                with patch.object(self.channels,'mailbox_activation_for_boot',wrong):
                    with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
                self.assert_no_pose()
                self.comp.close('subtest ended')

    def test_wrong_slot_source_is_not_a_verified_grant(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        wrong=fixture_record('_VerifiedSlot',boot=self.comp._boot,source=object(),
            clock_domain=self.comp._clock,window_index=0)
        with patch.object(self.channels,'verify_slot',return_value=wrong):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()

    def test_missing_completion_or_slot_provider_has_no_legacy_fallback(self):
        self.activate(); self.f.observe(); proof=self.proof()
        with patch.object(self.channels,'verify_completion',None):
            with self.assertRaises(c.CompositionRejected): self.offer(proof)
        self.assert_no_pose()

    def test_partial_executor_admission_never_commits_tentative_proof(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        original=self.comp._executor.admit_command
        def fail(*args): original(*args); raise ValueError('after executor admission')
        with patch.object(self.comp._executor,'admit_command',fail):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assertIsNone(self.comp._candidates._current)
        self.assertIsNone(self.comp._candidates._pending)
        self.assert_no_pose()

    def test_observation_is_verified_once_and_runtime_failure_never_taps_mailbox(self):
        self.activate()
        with patch.object(self.channels,'verify_observation',wraps=self.channels.verify_observation) as verify:
            self.f.observe()
        self.assertEqual(verify.call_count,1)
        original=self.comp._runtime.observe
        def fail(event): original(event); raise ValueError('after actual runtime admission')
        with patch.object(self.comp._candidates._mailbox,'observe',wraps=self.comp._candidates._mailbox.observe) as tap, \
             patch.object(self.comp._runtime,'observe',fail):
            with self.assertRaises(c.CompositionRejected): self.f.observe(seq=10)
        self.assertEqual(tap.call_count,0); self.assert_no_pose()

    def test_topology_one_is_not_a_pc_direct_activation_or_hil_capture(self):
        self.channels=StatefulChannels(self.f); self.clock.value=210_000_000
        binding=self.f.boot_binding(topology_id=1)
        self.channels.fixture=SimpleNamespace(boot_binding=lambda:binding)
        self.create()
        with self.assertRaises(c.CompositionRejected): self.comp.accept_boot(self.channels.ready)
        self.assert_no_pose()
