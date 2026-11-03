"""New typed long-TTL pure controls; synthetic records are not board proof."""
import dataclasses,json,unittest
from competition.deepeye.simulation.authority import demo30h_ai_em3_profile_v2 as em
from competition.deepeye.simulation.authority import navigation_session_profile as nav
from competition.deepeye.integration import host_envelope as envelope
from competition.deepeye.tools.diagnostic import functional50_g05_a as g05
from competition.deepeye.tools.diagnostic import functional50_demo_four_cycle_profile_a as cycle
from competition.deepeye.simulation.authority.g05_csr_channels_v1 import G05CsrPolicy

NEW_BUILD = 'dc4e89ccf3db18c4f9871575efc399ba'

class LongTTLBorders(unittest.TestCase):
    def selected(self):
        return em.selected_profile(30_000_000_000, navigation_profile=em.NAV_ENTRY_LONG_TTL_V4)

    def test_new_descriptor_and_old_caps(self):
        p = self.selected()
        self.assertEqual(p.prospective_command_max_ns, 12_000_000_000)
        self.assertEqual(p.max_source_age_ns, 30_000_000_000)
        self.assertEqual(p.age_normalization_ms, 5000)
        self.assertEqual(p.original_quality_age_ns, 100_000_000)
        for selector, cap, prospective in ((None, 5_000_000_000, 1_000_000_000),
                (em.NAV_FAST_V1,5_000_000_000,3_000_000_000),
                (em.NAV_ENTRY_C0_V1,8_000_000_000,3_000_000_000),
                (em.NAV_ENTRY_C0_12S_V3,12_000_000_000,3_000_000_000)):
            self.assertEqual(em.selected_profile(cap,navigation_profile=selector).prospective_command_max_ns, prospective)
            with self.assertRaises(ValueError):
                em.selected_profile(cap+1,navigation_profile=selector)
        with self.assertRaises(ValueError):
            em.selected_profile(30_000_000_001,navigation_profile=em.NAV_ENTRY_LONG_TTL_V4)

    def test_typed_navigation_wire_and_old_hash(self):
        old = nav.NAV_ADJACENT_180S
        new = nav.NAV_FAST_LONGTTL_180S
        self.assertEqual(old.max_command_ttl_ms,3000)
        self.assertEqual(new.max_command_ttl_ms,12000)
        self.assertNotEqual(new.sha256, old.sha256)
        self.assertEqual(new.max_step_ns,100_000_000)
        self.assertEqual(new.source_pins,old.source_pins)
        self.assertEqual(new.max_public_items,24)
        self.assertIs(nav.from_wire(nav.to_wire(new)),new)
        self.assertIs(cycle.from_wire(cycle.to_wire(new)),new)
        self.assertIs(nav.from_wire(nav.to_wire(old)),old)
        with self.assertRaises(ValueError):
            dataclasses.replace(new,max_command_ttl_ms=12001)

    def test_hardware_default_three_seconds_and_exact_build_twelve(self):
        def words(ttl,profile=1): return (10,0,profile,10,ttl,1,9)
        self.assertEqual(g05._command(words(3000),0,None),words(3000))
        for ttl in (3001,12000):
            with self.assertRaises(ValueError):g05._command(words(ttl),0,None)
            with self.assertRaises(ValueError):g05._command(words(ttl),0,None,build_id='5764b1c0ecc25fe261812613fc925923')
            self.assertEqual(g05._command(words(ttl),0,None,build_id=NEW_BUILD),words(ttl))
        with self.assertRaises(ValueError):g05._command(words(12001),0,None,build_id=NEW_BUILD)
        self.assertEqual(g05._command(words(12000,2),0,None),words(12000,2))
        with self.assertRaises(ValueError):g05._command((15000,15000,1,1,12000,1,9),0,None,build_id=NEW_BUILD)

    def test_target_default_and_explicit_typed_extension(self):
        target=dict(action=1,yaw_q=10,pitch_q=0,speed_code=10,duration_ms=12000)
        with self.assertRaises(ValueError):envelope._check_target(target,'fast_9600')
        envelope._check_target(target,'fast_9600',navigation_profile=nav.NAV_FAST_LONGTTL_180S)
        with self.assertRaises(ValueError):envelope._check_target(dict(target,duration_ms=12001),'fast_9600',navigation_profile=nav.NAV_FAST_LONGTTL_180S)
        with self.assertRaises(ValueError):envelope._check_target(target,'fast_9600',navigation_profile=nav.NAV_ADJACENT_180S)
        with self.assertRaises(ValueError):envelope._check_target(target,'stress_300',navigation_profile=nav.NAV_FAST_LONGTTL_180S)
        self.assertEqual(envelope.DURATION_LIMIT_MS,{'fast_9600':3000,'stress_300':12000})

    def test_policy_pair_and_original_health_limits(self):
        p = self.selected()
        long = G05CsrPolicy(30_000_000_000,30_000_000_000,0,0,p)
        long.check()
        self.assertIs(nav.longttl_for_g05(long),nav.NAV_FAST_LONGTTL_180S)
        for selector,cap in ((None,5_000_000_000),(em.NAV_ENTRY_C0_V1,8_000_000_000),(em.NAV_ENTRY_C0_12S_V3,12_000_000_000)):
            old=em.selected_profile(cap,navigation_profile=selector)
            with self.assertRaises(ValueError):G05CsrPolicy(cap+1,cap,0,0,old).check()
        with self.assertRaises(ValueError):dataclasses.replace(long,health_timeout_ns=30_000_000_001).check()
        self.assertIsNone(nav.longttl_for_g05(None))

    def test_owned_prospective_policy(self):
        from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import OwnedInvocationPolicy
        p=OwnedInvocationPolicy('new558','a'*64,'b'*40,16,256,65536,12000,navigation_profile=nav.NAV_FAST_LONGTTL_180S)
        p.check()
        with self.assertRaises(ValueError):dataclasses.replace(p,duration_ms=12001).check()
        with self.assertRaises(ValueError):dataclasses.replace(p,navigation_profile=nav.NAV_ADJACENT_180S).check()

    def test_full_interval_and_request_keep_original_bounds(self):
        from competition.deepeye.integration import completion_interval as interval
        now=50_000_000_000
        ctx=dict(session=7,config_epoch=2,boot_sha256='a'*64,transport_profile_id=1,source_id=3,topology_id=2,acquisition_profile_id=1)
        target=dict(action=1,yaw_q=10,pitch_q=0,speed_code=10,duration_ms=12000)
        observation=dict(context=ctx,observed_seq=9)
        document=dict(schema_version=2,kind='model_candidate',context=ctx,candidate_id=1,model_sha256=self.selected().model_sha256,
            observation=observation,target=target,completion_observed_interval_ns=dict(lower_ns=now-1000,upper_ns=now-100),basis=interval.BASIS)
        encode=lambda v:json.dumps(v,separators=(',',':')).encode()
        bounds=dict(max_age_ns=30_000_000_000,source_deadline_ns=now+30_000_000_000,dispatch_deadline_ns=now+29_000_000_000,previous_deadline_ns=None)
        policy=G05CsrPolicy(30_000_000_000,30_000_000_000,0,0,self.selected())
        parsed=interval.validate_message(encode(document),legacy=envelope,producer='ai_controller',context=ctx,now_ns=now,
            consumer='control_broker',enable_interval=True,bounds=bounds,g05_policy=policy)
        adapted=interval.adapt_action_candidate(parsed,host_issue_ns=now,now_ns=now,previous_deadline_ns=None)
        self.assertEqual(adapted.deadline_ns,now+12_000_000_000)
        with self.assertRaises(ValueError):interval.adapt_action_candidate(parsed,host_issue_ns=now,now_ns=now,previous_deadline_ns=now+11_000_000_000)
        request=dict(schema_version=1,kind='motion_request',context=ctx,command_seq=1,candidate_id=1,observation=observation,target=target,host_issue_monotonic_ns=now)
        with self.assertRaises(ValueError):envelope.validate_message(encode(request),producer='control_broker',context=ctx,now_ns=now,consumer='world_authority')
        self.assertEqual(envelope.validate_message(encode(request),producer='control_broker',context=ctx,now_ns=now,consumer='world_authority',navigation_profile=nav.NAV_FAST_LONGTTL_180S).kind,'motion_request')
        request['observation']=None
        with self.assertRaises(ValueError):envelope.validate_message(encode(request),producer='control_broker',context=ctx,now_ns=now,consumer='world_authority',navigation_profile=nav.NAV_FAST_LONGTTL_180S)

    def test_protocol_only_selected_navigation_accepts_twelve(self):
        from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as protocol
        value=dict(schema=protocol.SCHEMA,id='apply1',operation_id='synthetic558',kind='apply',payload=dict(command_words=[10,0,1,10,12000,1,9]))
        wire=protocol.raw(value)+b'\n'
        for selected,allowed in ((nav.NAV_FAST_LONGTTL_180S,True),(nav.NAV_ADJACENT_180S,False)):
            state=protocol.Sequence();state.initialized=True;state.max_commands=16;state.demo_cycle_profile=selected
            if allowed:self.assertEqual(protocol.decode_request(wire,'synthetic558',g05,state),value)
            else:
                with self.assertRaises(ValueError):protocol.decode_request(wire,'synthetic558',g05,state)

    def test_long_capture_requires_full_measured_output_and_build(self):
        from competition.deepeye.simulation.authority.g05_board_output_v1 import decode_board_output
        command=(10,0,1,10,12000,1,9)
        w=[0]*32
        w[:6]=[1,1,9,(10<<8)|1,10,12000]
        for at,n in ((6,100),(8,100+12000*50000),(10,200)):
            w[at:at+2]=[n & 0xffffffff,n>>32]
        w[12:18]=[1000000]*3+[125080,125000,30000]
        for i in range(3):
            w[18+2*i:20+2*i]=[1000,0]
            w[24+2*i:26+2*i]=[1001000,0]
        w[30:]=[7,0x47303550]
        with self.assertRaises(ValueError):decode_board_output(w,command,session=7)
        self.assertEqual(decode_board_output(w,command,session=7,build_id=NEW_BUILD)['duration_ms'],12000)
        torn=w.copy();torn[15]=0
        with self.assertRaises(ValueError):decode_board_output(torn,command,session=7,build_id=NEW_BUILD)
        with self.assertRaises(ValueError):decode_board_output(w,command,session=8,build_id=NEW_BUILD)

if __name__=='__main__':unittest.main()
