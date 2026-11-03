"""Pure host controls with explicitly synthetic CSR captures; no board claim."""
import importlib.util
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from competition.deepeye.integration import candidate_mailbox as mailbox
from competition.deepeye.simulation.authority import actor_composition as actors

MODULE = 'competition.deepeye.simulation.authority.g05_board_output_v1'


def capture(yaw=10, pitch=-20, speed=12, ttl=1000, seq=1, tag=42):
    words = [0] * 32
    words[:6] = [1, seq, tag, (speed << 8) | 1,
                 ((pitch & 0xffff) << 16) | (yaw & 0xffff), ttl]
    words[6], words[8], words[10] = 500, 500 + ttl * 50000, 3000000
    words[12:18] = [1000000] * 3 + [125000 + yaw * 8,
                                                 125000 + pitch * 8, 25000 + speed * 500]
    for lane in range(3):
        words[18 + lane * 2] = 1000000
        words[24 + lane * 2] = 2000000
    words[30:] = [13, 0x47303550]
    return words, (yaw & 0xffff, pitch & 0xffff, 1, speed, ttl, seq, tag)


class BoardOutputControls(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), 'typed board-output module required')
        return __import__(MODULE, fromlist=['G05BoardOutputPolicyV1'])

    def test_measured_pwm_outputs_make_target(self):
        api = self.api(); words, command = capture()
        words[15] += 1; words[16] -= 1
        target = api.decode_board_output(words, command, session=13)
        self.assertEqual(target, dict(action=1, yaw_q=10, pitch_q=-20,
                                     speed_code=12, duration_ms=1000))

    def test_submitted_echo_cannot_override_measured_output(self):
        api = self.api(); words, command = capture()
        words[15] += 80  # Echo still says yaw=10; actual output says yaw=20.
        with self.assertRaises(ValueError): api.decode_board_output(words, command, session=13)

    def test_capture_identity_timing_and_encoding_fail_closed(self):
        api = self.api()
        for index, value in ((1,2),(2,43),(3,1),(4,0),(5,999),(8,500),
                             (12,900000),(15,125000+10*8+3),(30,14),(31,0)):
            with self.subTest(index=index):
                words, command = capture(); words[index] = value
                with self.assertRaises(ValueError): api.decode_board_output(words, command, session=13)

    def test_stop_capture_is_never_arrival_or_movement(self):
        api = self.api(); words, command = capture(yaw=0,pitch=0,speed=0)
        with self.assertRaises(ValueError): api.decode_board_output(words, command, session=13)

    def test_policy_is_distinct_and_mutually_exclusive(self):
        api = self.api(); policy = api.G05BoardOutputPolicyV1(10_000_000)
        self.assertNotIsInstance(policy, mailbox.PcDirectWindowV2)
        self.assertIn('g05_board_output_v1', actors.AuthorityConfig.__dataclass_fields__)
        api.check_mode_selection(policy, None, object())
        with self.assertRaises(ValueError):
            api.check_mode_selection(policy, mailbox.PcDirectWindowV2(10), object())
        with self.assertRaises(ValueError): api.check_mode_selection(policy, None, None)
        for width in (True,0,-1,5_000_000_001):
            with self.assertRaises(ValueError): api.G05BoardOutputPolicyV1(width).check()

    def pending_mailbox(self,target=None):
        api = self.api()
        self.assertTrue(hasattr(mailbox.LatestCompletedMailbox,'consume_g05_board_output_v1'),
                        'separate typed board-output mailbox required')
        from competition.deepeye.tests.simulation import test_pc_direct_runtime as fixture
        document = mailbox.boot.load_document(Path(mailbox.__file__).resolve().parents[1] / 'docs/boot_profiles.json')
        ctx = dict(fixture.PC, boot_sha256=mailbox.boot.canonical_sha256(document).hex())
        owner = mailbox.LatestCompletedMailbox(document)
        source, clock = object(), object()
        owner.activate(fixture.encode(ctx), generation=1, slot_origin_ns=0, source=source,
            clock_domain=clock,bounds=mailbox.TransferBounds(0,0),now_ns=100_000_000,
            g05_board_output_v1=api.G05BoardOutputPolicyV1(10_000_000))
        raw = fixture.encode(fixture.telem_document(context=ctx,seq=9,tick=1,count=50,
            receipt=dict(lower_ns=200_000_000,upper_ns=200_000_000),
            adc_last=dict(lower_ns=200_000_000,upper_ns=200_000_000)))
        owner.observe(raw,sample_lower_ns=200_000_000,now_ns=200_000_000)
        candidate = fixture.encode(dict(schema_version=1,kind='model_candidate',context=ctx,
            candidate_id=1,model_sha256='a'*64,observation=dict(context=ctx,observed_seq=9),
            target=target or dict(action=1,yaw_q=0,pitch_q=0,speed_code=5,duration_ms=1000),
            completed_monotonic_ns=205_000_000))
        owner.complete(mailbox.Completion(1,source,clock,candidate,1,201_000_000,
            205_000_000,205_000_000,300_000_000),now_ns=205_000_000)
        return owner

    def test_board_window_is_one_use_and_truthfully_labelled(self):
        owner = self.pending_mailbox()
        selected = owner.consume_g05_board_output_v1(210_000_001,grant=mailbox.SlotGrant(1,0))
        self.assertEqual(selected.mode,'G05_CSR_BOARD_OUTPUT')
        self.assertIsNone(owner.consume_g05_board_output_v1(210_000_002,grant=mailbox.SlotGrant(1,0)))

    def test_board_window_cannot_use_pc_direct_consume_or_close_boundary(self):
        owner = self.pending_mailbox()
        with self.assertRaises(ValueError): owner.consume_pc_direct_v2(210_000_001,grant=mailbox.SlotGrant(1,0))
        owner = self.pending_mailbox()
        self.assertIsNone(owner.consume_g05_board_output_v1(220_000_000,grant=mailbox.SlotGrant(1,0)))

    def channel(self):
        api = self.api()
        from competition.deepeye.simulation.authority.g05_csr_channels_v1 import G05CsrChannels, _raw
        self.assertTrue(hasattr(G05CsrChannels,'prepare_board_output'),
                        'original APPLY output admission required')
        from competition.deepeye.simulation.authority.candidate_owner import _CompletedInference
        from competition.deepeye.simulation.authority.pc_direct_runtime import BootBinding
        obj = object.__new__(G05CsrChannels)
        obj.config = SimpleNamespace(g05_board_output_v1=api.G05BoardOutputPolicyV1(10_000_000))
        obj.boot = BootBinding('synthetic',1,b'{}','synthetic')
        words,command = capture()
        proof = _CompletedInference(obj.boot,obj,None,_raw(dict(target=dict(action=1,yaw_q=10,
            pitch_q=-20,speed_code=12,duration_ms=1000))),1,1,1,2)
        obj.owner = SimpleNamespace(_busy=False,_state='ACTIVE',_candidates=SimpleNamespace(_pending=proof))
        obj.refs = SimpleNamespace(legacy_context=dict(transport_profile_id=1),chain=SimpleNamespace(identity=tuple(range(1,14))))
        obj._board_pending = None; obj._board_outputs=[]; obj._board_last_sequence=0; obj._board_last_result=0
        obj._global_deadline=9_000_000_000; obj._health_deadline=8_000_000_000
        phase = SimpleNamespace(kind='apply',lower_qpc_ns=10,upper_qpc_ns=20,
            request_raw=_raw(dict(kind='apply',payload=dict(command_words=list(command)))),
            response_raw=_raw(dict(result=dict(capture=dict(words32=words)))))
        facts=dict(kind='apply'); refs=dict(phase_receipt=phase)
        return obj,proof,phase,facts,refs

    def test_original_apply_preissue_deadline_is_fixed_and_one_use(self):
        obj,proof,phase,facts,refs = self.channel()
        with patch.object(obj,'checkpoint',return_value=30), patch.object(obj,'_consume',return_value=(facts,refs)), patch.object(obj,'_health'):
            result = obj.prepare_board_output(object())
            self.assertEqual(result['mode'],'G05_CSR_BOARD_OUTPUT')
            self.assertFalse(result['genuine_PC_DIRECT'])
            self.assertEqual(result['deadline_qpc_ns'],10 + 1_000_000_000)
            self.assertEqual(result['pwm_period_words'],[1000000]*3)
            self.assertEqual(result['pwm_high_words'],[125080,124840,31000])
            with self.assertRaises(ValueError): obj.prepare_board_output(object())

    def test_apply_from_before_ai_or_mismatched_actual_target_is_rejected(self):
        from competition.deepeye.simulation.authority.g05_csr_channels_v1 import _raw
        for mismatch in (True,False):
            obj,proof,phase,facts,refs = self.channel()
            if mismatch:
                obj.owner._candidates._pending=replace(proof,candidate_raw=_raw(dict(target=dict(
                    action=1,yaw_q=11,pitch_q=-20,speed_code=12,duration_ms=1000))))
            else:
                phase.lower_qpc_ns=1
            with patch.object(obj,'checkpoint',return_value=30), patch.object(obj,'_consume',return_value=(facts,refs)), patch.object(obj,'_health'):
                with self.assertRaises(ValueError): obj.prepare_board_output(object())

    def test_apply_ttl_expired_during_readback_is_not_renewed(self):
        obj,proof,phase,facts,refs = self.channel()
        with patch.object(obj,'checkpoint',return_value=1_000_000_010), patch.object(obj,'_consume',return_value=(facts,refs)), patch.object(obj,'_health'):
            with self.assertRaises(ValueError): obj.prepare_board_output(object())

    def test_board_broker_needs_apply_then_emits_measured_target_and_fixed_deadline(self):
        obj,proof,phase,facts,refs = self.channel()
        target=dict(action=1,yaw_q=10,pitch_q=-20,speed_code=12,duration_ms=1000)
        box=self.pending_mailbox(target)
        proof=replace(proof,candidate_raw=box._pending.record.candidate_raw,
                      completion_lower_ns=205_000_000,completion_upper_ns=205_000_000)
        obj.owner._candidates._pending=proof;obj.owner._candidates._mailbox=box
        obj.config.g05_board_output_v1=box._g05_board_output_v1
        obj.refs.legacy_context=box._context
        obj.policy=SimpleNamespace(usb_upper_ns=0,packing_upper_ns=0)
        obj._command_seq=0;obj.command_quality_reports=[]
        phase.lower_qpc_ns=206_000_000;phase.upper_qpc_ns=207_000_000
        with patch.object(obj,'checkpoint',return_value=210_000_001), patch.object(obj,'_consume',return_value=(facts,refs)), patch.object(obj,'_health'):
            self.assertIsNone(obj.broker_next())
            receipt=obj.prepare_board_output(object())
            event=obj.broker_next()
            self.assertIsNotNone(event)
            admitted=obj.verify_command(event,obj.boot)
            self.assertEqual(mailbox.envelope._parse_message(admitted.raw)['target'],target)
            self.assertEqual(obj.verify_board_output(event,obj.boot,admitted.raw,proof,
                             now_ns=210_000_001),receipt['deadline_qpc_ns'])
            self.assertIsNone(obj.broker_next())
            with self.assertRaises(ValueError):
                obj.verify_board_output(object(),obj.boot,admitted.raw,proof,now_ns=210_000_001)
            with self.assertRaises(ValueError):
                obj.board_deadline_for(admitted.raw,now_ns=receipt['deadline_qpc_ns'])

    def test_board_owner_consumes_original_ai_proof_in_its_separate_mode(self):
        from competition.deepeye.simulation.authority import candidate_owner as co
        from competition.deepeye.simulation.authority.g05_csr_channels_v1 import _raw
        box=self.pending_mailbox();obj,_,_,_,_=self.channel();clock=object()
        boot=replace(obj.boot,context_json=box._context_raw)
        obj.policy=SimpleNamespace(max_source_age_ns=1_500_000_000)
        policy=box._g05_board_output_v1
        owner=co._CandidateOwner(boot,obj,clock,'a'*64,100_000_000,100_000_000,
            co._MailboxActivation(boot,obj,clock,0,0,0),100_000_000,g05_board_output_v1=policy)
        interval=dict(lower_ns=200_000_000,upper_ns=200_000_000)
        raw=_raw(dict(schema_version=1,kind='g05_raw4_observation_v1',context=box._context,
            observed_seq=9,adc_interval_ns=interval,native_em_interval_ns=None,receipt_interval_ns=interval,
            capture_sha256='a'*64,quality=0,channel_counts=[None]*4,wire_format='ABI3_E4_PAYLOAD_REV2',
            wire_hex='00',target100ms_met=False))
        from competition.deepeye.simulation.authority.pc_direct_runtime import VerifiedObservation
        owner.observe(VerifiedObservation(boot,raw,200_000_000),200_000_000)
        record=box._pending.record
        proof=co._CompletedInference(boot,obj,clock,record.candidate_raw,1,201_000_000,
                                    205_000_000,205_000_000)
        self.assertTrue(owner.offer(proof,205_000_000))
        selected=owner.select(b'synthetic command',co._VerifiedSlot(boot,obj,clock,0),210_000_001)
        self.assertIs(selected,proof)
        self.assertIsNone(owner._pending)
        self.assertEqual(owner._mailbox._mode,'G05_CSR_BOARD_OUTPUT')

    def test_final_ai_lease_also_caps_every_physics_fence_by_board_ttl(self):
        from competition.deepeye.simulation.authority.pc_direct_runtime import AiLease, BootBinding, VerifiedEnvelope
        boot=BootBinding('synthetic',1,b'{}','synthetic')
        gate=SimpleNamespace(generation=1,deadline_for=lambda raw,now:200)
        owner=SimpleNamespace(_veto=0,_active=lambda:None,_checkpoint=lambda *args:None,
            _progress=gate,_actor=SimpleNamespace(ai_lease=lambda boot,now:AiLease(boot,boot.ai_instance,300)),
            _command_record=VerifiedEnvelope(boot,b'original command'),_runtime=SimpleNamespace(_stepping=False),
            _config=SimpleNamespace(g05_board_output_v1=self.api().G05BoardOutputPolicyV1(10)),
            _channels=SimpleNamespace(board_deadline_for=lambda raw,**kwargs:100))
        lease=actors._Dependencies(owner).ai_lease(boot,50)
        self.assertEqual(lease.deadline_ns,100)


if __name__ == '__main__': unittest.main()
