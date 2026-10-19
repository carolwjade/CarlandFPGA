"""CPU-only runtime fixtures; never real observations, ACL or physical motion."""
import copy
import importlib
import json
import struct
from pathlib import Path
import sys
import unittest

INTEGRATION = Path(__file__).resolve().parents[2] / 'integration'
sys.path.insert(0, str(INTEGRATION))
from test_host_envelope import encode, request_document, telem_document, response_document, config_ack_frame, wire
from test_pc_direct_watchdog import heartbeat, PC

try:
    runtime = importlib.import_module('competition.deepeye.simulation.authority.pc_direct_runtime')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.authority.pc_direct_runtime':
        raise
    runtime = None


class Clock:
    value = 1_000_000_000
    increment = 0
    on_read = None
    next_value = None
    def __call__(self):
        value=self.value;self.value+=self.increment
        hook=self.on_read;self.on_read=None
        if hook:hook()
        if self.next_value is not None:
            result=self.next_value;self.next_value=None;return result
        return value


def fixture_provider(clock):
    class Fixture(runtime.AuthorityDependencies):
        """Trusted deterministic records only; no authentication provider exists here."""
        live = True
        prepare_hook = None
        fence_hook = None
        committed = 0
        omit_fence = False
        twice_fence = False
        retry_failed_fence = False
        def verify_boot(self, event):
            if type(event) is not runtime.BootBinding: raise ValueError('unverified BOOT fixture')
            return event
        def verify_board(self, event, boot):
            if type(event) is not runtime.VerifiedEnvelope: raise ValueError('unverified channel fixture')
            return event
        def verify_observation(self, event, boot):
            if type(event) is not runtime.VerifiedObservation: raise ValueError('unverified source fixture')
            return event
        def verify_command(self, event, boot):
            if type(event) is not runtime.VerifiedEnvelope: raise ValueError('unverified broker fixture')
            return event
        def ai_lease(self, boot, now_ns):
            if not self.live: raise ValueError('AI fixture process died')
            return runtime.AiLease(boot, boot.ai_instance, clock.value + 1_000_000_000)
        def prepare_step(self, boot, command_raw, expected_pose_revision, dt_ns):
            if self.prepare_hook: self.prepare_hook()
            return (expected_pose_revision, dt_ns)
        def commit_step(self, prepared, before_commit):
            if self.fence_hook: self.fence_hook()
            if self.omit_fence: return True
            if self.retry_failed_fence:
                self.live=False
                try:before_commit()
                except ValueError:self.live=True
            fence = before_commit()
            if self.twice_fence: before_commit()
            self.committed += 1
            return runtime.CommitReceipt(fence.boot, fence.command_seq, prepared[0]+1,
                                         fence.checked_ns, fence.step_end_ns)
    return Fixture()


class PcDirectRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(runtime, 'authority runtime adapter absent')
        self.clock = Clock()
        self.provider = fixture_provider(self.clock)
        self.owner = runtime.PcDirectRuntime(run_id='run-1', dependencies=self.provider,
            clock=self.clock, heartbeat_timeout_ns=500_000_000)
        self.binding = self.boot_binding()

    def boot_binding(self, generation=1, session=7, run='run-1', **context):
        ctx=dict(PC, session=session, **context)
        return runtime.BootBinding(run, generation, encode(ctx), 'ai-1')

    def activate(self):
        self.owner.boot(self.binding)
        self.beat()

    def beat(self, seq=10, tick=100, fault=0):
        raw=encode(heartbeat(context=json.loads(self.binding.context_json),seq=seq,tick=tick,
                             lo=self.clock.value,hi=self.clock.value,fault=fault))
        return self.owner.board(runtime.VerifiedEnvelope(self.binding,raw))

    def observe(self, seq=9, sample=None, binding=None):
        binding=binding or self.binding
        sample=self.clock.value if sample is None else sample
        ctx=json.loads(binding.context_json)
        doc=telem_document(context=ctx,seq=seq,tick=1234+seq,
            count=50 if ctx['transport_profile_id']==1 else 800,
            receipt=dict(lower_ns=self.clock.value,upper_ns=self.clock.value),
            adc_last=dict(lower_ns=sample,upper_ns=sample))
        event=runtime.VerifiedObservation(binding,encode(doc),sample)
        self.owner.observe(event)
        return event

    def command(self, seq=3, obs=9, issue=None, duration=1000, binding=None, action=1):
        binding=binding or self.binding
        ctx=json.loads(binding.context_json)
        target=dict(action=action,yaw_q=0,pitch_q=0,speed_code=5 if action else 0,
                    duration_ms=duration if action else 0)
        doc=request_document(context=ctx,command_seq=seq,candidate_id=seq,
            issue=self.clock.value if issue is None else issue,target_value=target,
            observation=dict(context=ctx,observed_seq=obs) if action else None)
        event=runtime.VerifiedEnvelope(binding,encode(doc))
        self.owner.command(event)
        return event

    def arm(self, **command):
        self.activate(); self.observe(); return self.command(**command)

    def step(self, dt=1_000_000):
        return self.owner.step(expected_pose_revision=0,dt_ns=dt)

    def assert_stopped(self):
        self.assertFalse(self.step().committed)
        self.assertEqual(self.provider.committed,0)

    def test_no_boot_or_heartbeat_alone_cannot_commit(self):
        self.assert_stopped(); self.activate(); self.assert_stopped()

    def test_all_separate_inputs_and_final_fence_commit_one_fixture_step(self):
        self.arm(); result=self.step()
        self.assertTrue(result.committed)
        self.assertEqual(result.receipt.command_seq,3)
        self.assertEqual(result.receipt.pose_revision,1)
        self.assertEqual(self.provider.committed,1)

    def test_valid_non_state_ack_does_not_poison_or_refresh_heartbeat(self):
        self.arm(); self.clock.value+=100_000_000
        raw=encode(dict(response_document(config_ack_frame()),context=PC,
            receipt_interval_ns=dict(lower_ns=self.clock.value,upper_ns=self.clock.value)))
        self.owner.board(runtime.VerifiedEnvelope(self.binding,raw))
        self.assertTrue(self.step().committed)
        self.clock.value=1_500_000_000
        self.assertFalse(self.step().committed)
        self.assertEqual(self.provider.committed,1)

    def test_wrong_channel_boolean_cannot_authenticate(self):
        self.arm()
        with self.assertRaises(ValueError): self.owner.board(True)
        self.assert_stopped()

    def test_crc_error_latches_and_normal_heartbeat_cannot_restore(self):
        self.arm()
        raw=encode(heartbeat(context=PC,lo=self.clock.value,hi=self.clock.value))
        doc=json.loads(raw); frame=bytearray.fromhex(doc['wire_frame_hex']);frame[-1]^=1
        doc['wire_frame_hex']=frame.hex()
        with self.assertRaises(ValueError): self.owner.board(runtime.VerifiedEnvelope(self.binding,encode(doc)))
        with self.assertRaises(ValueError): self.beat(seq=11,tick=101)
        self.assert_stopped()

    def test_board_fault_vetoes_immediately(self):
        self.arm(); self.clock.value+=1
        self.beat(seq=11,tick=101,fault=1); self.assert_stopped()

    def test_wrong_boot_generation_cannot_supply_observation(self):
        self.activate()
        with self.assertRaises(ValueError): self.observe(binding=self.boot_binding(generation=2))
        self.assert_stopped()

    def test_wrong_epoch_cannot_supply_command(self):
        self.arm()
        with self.assertRaises(ValueError): self.command(seq=4,binding=self.boot_binding(config_epoch=3))
        self.assert_stopped()

    def test_wrong_run_boot_cannot_activate(self):
        with self.assertRaises(ValueError): self.owner.boot(self.boot_binding(run='other'))
        self.assert_stopped()

    def test_other_topology_cannot_activate(self):
        with self.assertRaises(ValueError): self.owner.boot(self.boot_binding(topology_id=1))
        self.assert_stopped()

    def test_same_session_or_old_generation_boot_does_not_clear_stop(self):
        self.arm();self.owner.stop('mode changed')
        with self.assertRaises(ValueError):self.owner.boot(self.boot_binding(generation=2))
        with self.assertRaises(ValueError):self.owner.boot(self.boot_binding(generation=1,session=8))
        self.assert_stopped()

    def test_new_boot_retires_old_command_observation_and_heartbeat(self):
        old=self.arm();self.owner.stop('restart')
        self.binding=self.boot_binding(generation=2,session=8)
        self.owner.boot(self.binding);self.beat();self.assert_stopped()
        with self.assertRaises(ValueError):self.owner.command(old)
        self.assert_stopped()

    def test_duplicate_command_never_renews_original_issue_deadline(self):
        event=self.arm(duration=100)
        self.clock.value+=50_000_000;self.owner.command(event)
        self.assertTrue(self.step().committed)
        self.clock.value=1_100_000_000;self.assertFalse(self.step().committed)
        with self.assertRaises(ValueError):self.owner.command(event)
        self.assertFalse(self.step().committed)
        self.assertEqual(self.provider.committed,1)

    def test_changed_same_command_key_is_rejected(self):
        self.arm()
        with self.assertRaises(ValueError):self.command(issue=self.clock.value+0,duration=2000)
        self.assert_stopped()

    def test_sample_age_caps_long_command_even_with_new_heartbeat(self):
        self.activate();self.observe(sample=0);self.command(duration=3000)
        for i in range(1,4):
            self.clock.value=1_000_000_000+i*200_000_000;self.beat(seq=10+i,tick=100+i)
        self.assert_stopped()

    def test_duplicate_observation_cannot_relabel_receipt_or_sample_age(self):
        self.arm();self.clock.value+=1
        with self.assertRaises(ValueError):self.observe(seq=9)
        self.assert_stopped()

    def test_old_observation_sequence_cannot_restore_motion(self):
        self.arm();self.clock.value+=1
        with self.assertRaises(ValueError):self.observe(seq=8)
        self.assert_stopped()

    def test_fifth_observation_evicts_oldest_but_does_not_relabel_active_command(self):
        self.arm()
        for seq in range(10,14):self.clock.value+=1;self.observe(seq=seq)
        self.assert_stopped()

    def test_missing_sample_mapping_is_not_an_observation(self):
        self.activate();ctx=json.loads(self.binding.context_json)
        doc=telem_document(context=ctx,adc_last=None)
        with self.assertRaises(ValueError):self.owner.observe(runtime.VerifiedObservation(self.binding,encode(doc),None))
        self.assert_stopped()

    def test_stale_observation_is_rejected(self):
        self.activate();self.clock.value=2_500_000_000
        with self.assertRaises(ValueError):self.observe(sample=0)
        self.assert_stopped()

    def test_ai_death_vetoes_before_commit(self):
        self.arm();self.provider.live=False;self.assert_stopped()

    def test_ai_death_during_geometry_prepare_vetoes(self):
        self.arm();self.provider.prepare_hook=lambda:setattr(self.provider,'live',False)
        self.assert_stopped()

    def test_expiration_during_prepare_vetoes_before_commit(self):
        self.arm(duration=100)
        self.provider.prepare_hook=lambda:setattr(self.clock,'value',1_100_000_000)
        self.assert_stopped()

    def test_final_executor_fence_rechecks_time(self):
        self.arm(duration=100)
        self.provider.fence_hook=lambda:setattr(self.clock,'value',1_100_000_000)
        self.assert_stopped()

    def test_final_executor_fence_rechecks_ai(self):
        self.arm();self.provider.fence_hook=lambda:setattr(self.provider,'live',False)
        self.assert_stopped()

    def test_step_cannot_cross_command_or_heartbeat_deadline(self):
        self.arm(duration=100);self.assertFalse(self.step(dt=100_000_001).committed)
        self.assertEqual(self.provider.committed,0)

    def test_executor_cannot_return_success_without_fence(self):
        self.arm();self.provider.omit_fence=True;self.assert_stopped()

    def test_fence_is_single_use(self):
        self.arm();self.provider.twice_fence=True;self.assert_stopped()

    def test_explicit_stop_invalidates_commands_without_fresh_observation(self):
        self.arm();self.owner.stop('configuration changed');self.assert_stopped()
        with self.assertRaises(ValueError):self.command(seq=4)

    def test_broker_stop_requires_no_observation_and_latches(self):
        self.activate();self.command(action=0);self.assert_stopped()
        with self.assertRaises(ValueError):self.beat(seq=11,tick=101)

    def test_clock_regression_latches(self):
        self.arm();self.clock.value-=1;self.assert_stopped()

    def test_reentrant_stop_during_prepare_vetoes(self):
        self.arm();self.provider.prepare_hook=lambda:self.owner.stop('operator STOP')
        self.assert_stopped()

    def test_same_pose_revision_cannot_commit_twice(self):
        self.arm();self.assertTrue(self.step().committed)
        self.clock.value+=1_000_000
        self.assertFalse(self.step().committed)
        self.assertEqual(self.provider.committed,1)

    def test_future_physics_intervals_cannot_overlap(self):
        self.arm();self.assertTrue(self.step().committed)
        result=self.owner.step(expected_pose_revision=1,dt_ns=1_000_000)
        self.assertFalse(result.committed)
        self.assertEqual(self.provider.committed,1)

    def test_correct_revision_after_elapsed_interval_can_commit(self):
        self.arm();self.assertTrue(self.step().committed)
        self.clock.value+=1_000_000
        self.assertTrue(self.owner.step(expected_pose_revision=1,dt_ns=1_000_000).committed)
        self.assertEqual(self.provider.committed,2)

    def test_boolean_generation_cannot_alias_real_binding(self):
        self.activate()
        with self.assertRaises(ValueError):self.observe(binding=self.boot_binding(generation=True))
        self.assert_stopped()

    def test_bytearray_context_cannot_alias_immutable_binding(self):
        self.activate()
        alias=runtime.BootBinding('run-1',1,bytearray(self.binding.context_json),'ai-1')
        with self.assertRaises(ValueError):self.observe(binding=alias)
        self.assert_stopped()

    def test_advancing_monotonic_clock_does_not_force_stop(self):
        self.clock.increment=1;self.arm()
        self.assertTrue(self.step().committed)

    def test_other_response_faults_and_rejection_cannot_be_ignored(self):
        payloads=[(11,struct.pack('<IHBBBHHHHB',7,3,10,2,2,512,900,1,1,0)),
                  (15,struct.pack('<IHBBhhBHBHBB',7,3,14,3,57,0,20,900,1,5,2,15)),
                  (16,struct.pack('<IHhhBBHHHBB',7,3,57,0,20,2,900,1,5,2,15)),
                  (9,wire.decode(config_ack_frame(phase=4)).payload)]
        for frame_type,payload in payloads:
            with self.subTest(frame_type=frame_type):
                self.setUp();self.arm()
                frame=wire.encode(wire.Frame(frame_type,2,4,111,payload))
                doc=dict(response_document(frame),context=PC,
                    receipt_interval_ns=dict(lower_ns=self.clock.value,upper_ns=self.clock.value))
                self.owner.board(runtime.VerifiedEnvelope(self.binding,encode(doc)))
                self.assert_stopped()

    def test_replayed_state_cannot_refresh_health(self):
        self.arm();self.clock.value+=1
        with self.assertRaises(ValueError):self.beat(seq=10,tick=100)
        self.assert_stopped()

    def test_ai_instance_change_cannot_reuse_old_process_identity(self):
        self.arm()
        self.provider.ai_lease=lambda boot,now:runtime.AiLease(boot,'replacement-ai',now+1_000_000_000)
        self.assert_stopped()

    def test_expired_ai_lease_cannot_commit(self):
        self.arm()
        self.provider.ai_lease=lambda boot,now:runtime.AiLease(boot,boot.ai_instance,now)
        self.assert_stopped()

    def test_caught_fence_failure_cannot_retry_and_restore_motion(self):
        self.arm();self.provider.retry_failed_fence=True
        self.assert_stopped()

    def test_stress_observation_age_uses_original_twelve_second_cap(self):
        self.owner=runtime.PcDirectRuntime(run_id='run-1',dependencies=self.provider,
            clock=self.clock,heartbeat_timeout_ns=20_000_000_000)
        self.binding=self.boot_binding(transport_profile_id=2)
        self.activate();self.observe(sample=0);self.command(duration=12000)
        self.clock.value=11_999_999_999
        self.assertTrue(self.step(dt=1).committed)
        self.clock.value=12_000_000_000
        self.assertFalse(self.owner.step(expected_pose_revision=1,dt_ns=1).committed)
        self.assertEqual(self.provider.committed,1)

    def test_stop_inside_boot_verifier_cannot_be_cleared_by_that_boot(self):
        def verify(event):
            self.owner.stop('STOP during BOOT verification')
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.assert_stopped()

    def test_caught_board_reentrancy_inside_boot_cannot_clear_veto(self):
        def verify(event):
            try:self.owner.board(None)
            except ValueError:pass
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.assert_stopped()

    def test_caught_nested_boot_cannot_activate_the_outer_boot(self):
        def verify(event):
            try:self.owner.boot(event)
            except ValueError:pass
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.assert_stopped()

    def test_step_reentrancy_in_boot_without_active_command_vetoes(self):
        self.activate()
        next_binding=self.boot_binding(generation=2,session=8)
        def verify(event):
            self.assertFalse(self.step().committed)
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(next_binding)
        self.assert_stopped()

    def test_stop_from_activation_clock_callback_vetoes_boot_commit(self):
        def verify(event):
            self.clock.on_read=lambda:self.owner.stop('STOP at activation clock read')
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.assert_stopped()

    def test_vetoed_proposal_cannot_replay_but_separate_fresh_boot_recovers(self):
        def verify(event):
            self.owner.stop('STOP during old proposal')
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.provider.verify_boot=lambda event:event
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.binding=self.boot_binding(generation=2,session=8)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)
        self.assertEqual(self.provider.committed,1)

    def test_preexisting_watchdog_timeout_allows_separate_fresh_boot(self):
        self.arm();self.clock.value=1_500_000_000
        self.assert_stopped()
        self.binding=self.boot_binding(generation=2,session=8)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)
        self.assertEqual(self.provider.committed,1)

    def test_new_stop_during_recovery_boot_does_not_restore_prior_command(self):
        self.arm();self.owner.stop('prior STOP')
        next_binding=self.boot_binding(generation=2,session=8)
        def verify(event):
            self.owner.stop('new STOP during recovery')
            return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(next_binding)
        self.assert_stopped()

    def test_stop_from_boot_entry_clock_callback_also_vetoes_activation(self):
        self.clock.on_read=lambda:self.owner.stop('STOP at BOOT entry clock read')
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.assert_stopped()

    def test_malformed_reentrant_step_arguments_always_veto_idle_boot(self):
        arguments=[dict(expected_pose_revision=0,dt_ns=0),dict(expected_pose_revision=False,dt_ns=1),
                   dict(expected_pose_revision=-1,dt_ns=1),dict(expected_pose_revision=0,dt_ns=False),
                   dict(expected_pose_revision='0',dt_ns=1),dict(expected_pose_revision=0,dt_ns=1.0)]
        for values in arguments:
            with self.subTest(arguments=values):
                self.setUp();self.activate()
                def verify(event):
                    self.assertFalse(self.owner.step(**values).committed)
                    return event
                self.provider.verify_boot=verify
                with self.assertRaises(ValueError):self.owner.boot(self.boot_binding(generation=2,session=8))
                self.assert_stopped()

    def test_runtime_argument_binding_errors_cannot_escape_boot_veto(self):
        callbacks=[lambda:self.owner.step(),lambda:self.owner.step(expected_pose_revision=0,dt_ns=1,extra=True),
                   lambda:self.owner.boot(),lambda:self.owner.board(),lambda:self.owner.observe(),
                   lambda:self.owner.command(),lambda:self.owner.stop(),
                   lambda:self.owner.board(None,extra=True)]
        for index,callback in enumerate(callbacks):
            with self.subTest(index=index):
                self.setUp();self.activate()
                def verify(event):
                    try:callback()
                    except (TypeError,ValueError):pass
                    return event
                self.provider.verify_boot=verify
                with self.assertRaises(ValueError):self.owner.boot(self.boot_binding(generation=2,session=8))
                self.assert_stopped()

    def test_verified_proposal_retires_before_activation_clock_exception(self):
        def fail_clock():raise ValueError('activation clock fixture failure')
        def verify(event):self.clock.on_read=fail_clock;return event
        self.provider.verify_boot=verify
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.provider.verify_boot=lambda event:event
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.binding=self.boot_binding(generation=2,session=8)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_reserved_receiver_keyword_cannot_bypass_boot_veto(self):
        for name in ('boot','board','observe','command','stop','step'):
            with self.subTest(method=name):
                self.setUp();self.activate()
                def verify(event):
                    values={'self':None}
                    if name=='step':values.update(expected_pose_revision=0,dt_ns=1)
                    elif name=='stop':values['reason']='STOP'
                    else:values['event']=None
                    try:getattr(self.owner,name)(**values)
                    except (TypeError,ValueError):pass
                    return event
                self.provider.verify_boot=verify
                with self.assertRaises(ValueError):self.owner.boot(self.boot_binding(generation=2,session=8))
                self.assert_stopped();self.assertEqual(self.provider.committed,0)

    def test_verified_proposal_retires_before_invalid_or_regressed_activation_clock(self):
        for value in (False,-1,1.5,'bad clock',999_999_999):
            with self.subTest(clock_value=value):
                self.setUp()
                def verify(event):self.clock.next_value=value;return event
                self.provider.verify_boot=verify
                with self.assertRaises(ValueError):self.owner.boot(self.binding)
                self.provider.verify_boot=lambda event:event
                with self.assertRaises(ValueError):self.owner.boot(self.binding)
                self.binding=self.boot_binding(generation=2,session=8)
                self.activate();self.observe();self.command()
                self.assertTrue(self.step().committed)

    def test_never_returned_boot_verification_does_not_retire_unverified_identity(self):
        def unavailable(event):raise ValueError('no completed BOOT verification')
        self.provider.verify_boot=unavailable
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.provider.verify_boot=lambda event:event
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_boot_entry_clock_exception_before_verifier_does_not_retire_identity(self):
        def unavailable_clock():raise ValueError('entry clock unavailable')
        self.clock.on_read=unavailable_clock
        with self.assertRaises(ValueError):self.owner.boot(self.binding)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_malformed_unverified_context_does_not_retire_corrected_identity(self):
        doc=json.loads(self.binding.context_json);del doc['topology_id']
        malformed=runtime.BootBinding('run-1',1,encode(doc),'ai-1')
        with self.assertRaises(ValueError):self.owner.boot(malformed)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_healthy_idle_step_poll_does_not_block_later_valid_command(self):
        self.activate();self.assert_stopped()
        self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_malformed_idle_step_latches_until_fresh_boot(self):
        self.activate()
        self.assertFalse(self.step(dt=0).committed)
        with self.assertRaises(ValueError):self.observe()
        self.binding=self.boot_binding(generation=2,session=8)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)

    def test_idle_step_clock_error_latches_until_fresh_boot(self):
        self.activate()
        def unavailable_clock():raise ValueError('idle step clock unavailable')
        self.clock.on_read=unavailable_clock
        self.assert_stopped()
        with self.assertRaises(ValueError):self.observe()
        self.binding=self.boot_binding(generation=2,session=8)
        self.activate();self.observe();self.command()
        self.assertTrue(self.step().committed)


if __name__=='__main__':unittest.main()
