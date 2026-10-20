"""Independent literal byte/time fixtures, no transport or physical evidence."""
import binascii
import copy
import dataclasses
import json
from pathlib import Path
import struct
import unittest
try:
    import hil_request_tracker as hil
except ModuleNotFoundError as error:
    if error.name!='hil_request_tracker':raise
    hil=None

NS=1_000_000
PRODUCT=Path(__file__).resolve().parents[1]
BASE=dict(session=7,config_epoch=2,boot_sha256='a'*64,transport_profile_id=1,
          source_id=3,topology_id=1,acquisition_profile_id=1)


def encoded(doc):return json.dumps(doc,separators=(',',':')).encode()


def packet(kind,payload,seq=40,tick=0,epoch=2):
    body=struct.pack('<2sBBBBHI',b'\xa5\x5a',3,kind,len(payload),epoch,seq,tick)+payload
    return body+struct.pack('<H',binascii.crc_hqx(body[2:],0xffff))


def request(ctx,seq=3,tick=0,ttl=3000,obs=9,yaw=0,pitch=0,speed=5,action=1,kind=14):
    if kind==14:payload=struct.pack('<IHBhhBHH',ctx['session'],seq,action,yaw,pitch,speed,ttl,obs)
    elif kind==5:payload=struct.pack('<IBBBHB',ctx['session'],1,0,0,100,0)
    elif kind==10:payload=struct.pack('<IHBBH',ctx['session'],seq,1,0,obs)
    else:payload=struct.pack('<I',ctx['session'])+bytes(23)
    return packet(kind,payload,seq,tick,ctx['config_epoch'])


def observation(ctx,seq=9,sample=0,at=0):
    payload=struct.pack('<4H4HH',1,2,3,4,5,6,7,8,15)
    frame=packet(1,payload,seq,seq,ctx['config_epoch'])
    return encoded(dict(schema_version=1,context=copy.deepcopy(ctx),kind='telem_observation',
        observed_seq=seq,tick_ms_raw=seq,receipt_interval_ns=dict(lower_ns=at*NS,upper_ns=at*NS),
        adc_last_interval_ns=dict(lower_ns=sample*NS,upper_ns=sample*NS),adc_first_interval_ns=None,
        native_em_interval_ns=None,sample_count=50 if ctx['transport_profile_id']==1 else 800,
        mean_counts=[1,2,3,4],range_counts=[5,6,7,8],quality_flags=15,wire_frame_hex=frame.hex()))


def response(ctx,request_seq=3,kind=15,wire_seq=40,tick=500,at=500,lower=None,
             remaining=1000,phase=3,fault=0,yaw=0,pitch=0,speed=5,capture_seq=5,
             control_epoch=None,quality=15,request_type=14,hashes=False):
    epoch=ctx['config_epoch'] if control_epoch is None else control_epoch
    if kind==15:payload=struct.pack('<IHBBhhBHBHBB',ctx['session'],request_seq,request_type,phase,
        yaw,pitch,speed,remaining,fault,capture_seq,epoch,quality)
    elif kind==16:payload=struct.pack('<IHhhBBHHHBB',ctx['session'],request_seq,yaw,pitch,speed,
        phase,remaining,fault,capture_seq,epoch,quality)
    elif kind==8:payload=struct.pack('<IHhBBHHHBB',ctx['session'],request_seq,yaw,speed,phase,
        remaining,fault,capture_seq,epoch,quality)
    elif kind==9:payload=struct.pack('<IHBBBBBHBBBH',ctx['session'],request_seq,5,phase,1,0,0,100,0,0,ctx['config_epoch'],0)
    else:raise AssertionError(kind)
    return encoded(dict(schema_version=1,context=copy.deepcopy(ctx),kind='board_response',
        receipt_interval_ns=dict(lower_ns=(at if lower is None else lower)*NS,upper_ns=at*NS),
        wire_frame_hex=packet(kind,payload,wire_seq,tick,ctx['config_epoch']).hex(),
        timing_record_sha256='b'*64 if hashes else None,physical_capture_record_sha256='c'*64 if hashes else None))


def fixture_dependencies():
    class Fixture(hil.HilDependencies):
        """Synthetic verifier results only, never authentication or measurements."""
        def __init__(self):
            self.owner=None;self.hooks={};self.mods={};self.delays=(40,20,5)
        def hook(self,name,result):
            if name in self.hooks:self.hooks[name]()
            return self.mods[name](result) if name in self.mods else result
        def verify_boot(self,event):return self.hook('boot',event)
        def verify_observation(self,raw,boot):
            j=json.loads(raw);mapped=j['adc_last_interval_ns']
            return self.hook('observation',hil.ObservationEvidence(boot,raw,None if mapped is None else mapped['lower_ns']))
        def verify_timing(self,raw,boot,original):
            return self.hook('timing',hil.TimingEvidence(boot,original,raw,*(x*NS for x in self.delays)))
        def verify_capture(self,raw,boot,original):
            frame=bytes.fromhex(json.loads(raw)['wire_frame_hex']);p=frame[12:-2]
            if frame[3]==15:
                a=struct.unpack('<IHBBhhBHBHBB',p);yaw,pitch,speed,seq,epoch,quality=a[4],a[5],a[6],a[9],a[10],a[11]
            else:
                a=struct.unpack('<IHhhBBHHHBB',p);yaw,pitch,speed,seq,epoch,quality=a[2],a[3],a[4],a[8],a[9],a[10]
            return self.hook('capture',hil.CaptureEvidence(boot,original,raw,yaw,pitch,speed,seq,epoch,quality,object()))
    return Fixture()


class HilTrackerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(hil,'selected HIL tracker implementation absent')
        self.ctx=copy.deepcopy(BASE);self.source=object();self.deps=fixture_dependencies()
        self.owner=hil.HilRequestTracker(run_id='run-1',dependencies=self.deps);self.deps.owner=self.owner
        self.binding=self.binding_for();self.owner.boot(self.binding,now_ns=0)

    def binding_for(self,generation=1,**ctx):
        return hil.BootBinding('run-1',generation,encoded(dict(self.ctx,**ctx)),self.source)

    def observe(self,seq=9,sample=0,at=0):return self.owner.observe(observation(self.ctx,seq,sample,at),now_ns=at*NS)

    def send(self,at=0,first=None,**kw):
        return self.owner.request(request(self.ctx,**kw),first_send_ns=(at if first is None else first)*NS,now_ns=at*NS)

    def arm(self,**kw):self.observe();return self.send(**kw)

    def test_literal_hand_derived_deadlines(self):
        vectors=json.loads((PRODUCT/'tests/vectors/r03_hil_request_lifecycle.json').read_bytes())
        self.assertEqual(len(vectors['traces']),8)
        for v in vectors['traces']:
            with self.subTest(v=v['name']):
                self.setUp();self.ctx['transport_profile_id']=v['profile']
                self.owner.boot(self.binding_for(2,session=8),now_ns=0);self.ctx['session']=8
                self.deps.delays=(v['serial_ms'],v['usb_ms'],v['clock_ms'])
                self.observe(sample=v['sample_ms']);self.send(at=v['first_send_ms'],ttl=v['ttl_ms'])
                for index,r in enumerate(v['responses']):
                    raw=response(self.ctx,wire_seq=40+index,at=r['at_ms'],lower=r['receipt_lower_ms'],remaining=r['remaining_ms'])
                    got=self.owner.response(raw,now_ns=r['at_ms']*NS)
                    self.assertEqual(got.deadline_ns,r['expected_deadline_ms']*NS)
                    self.assertEqual(got.qualified,r['qualified'])

    def test_retry_changes_tick_crc_but_not_original_payload_time(self):
        original=self.arm(ttl=3000);raw=request(self.ctx,tick=123)
        self.assertNotEqual(raw,original.first_raw)
        repeated=self.owner.request(raw,first_send_ns=400*NS,now_ns=400*NS)
        self.assertIs(original,repeated);self.assertEqual(original.first_send_ns,0)
        snap=self.owner.snapshot()['requests'][0]
        self.assertEqual(snap['first_raw_hex'],original.first_raw.hex());self.assertEqual(snap['latest_raw_hex'],raw.hex())

    def test_first_lost_ack_late_retry_cannot_restart_twelve_seconds(self):
        self.owner.boot(self.binding_for(2,session=8,transport_profile_id=2),now_ns=0)
        self.ctx.update(session=8,transport_profile_id=2);self.deps.delays=(1200,100,50)
        original=self.arm(ttl=12000);again=self.send(at=8000,tick=8000,ttl=12000)
        self.assertIs(original,again)
        got=self.owner.response(response(self.ctx,at=8000,remaining=12000),now_ns=8000*NS)
        self.assertEqual(got.deadline_ns,12000*NS);self.assertTrue(got.qualified)
        self.assertFalse(self.owner.check(now_ns=12000*NS).qualified)
        self.assertIs(self.send(at=12001,ttl=12000),original)
        self.assertFalse(self.owner.response(response(self.ctx,wire_seq=41,at=12001,remaining=12000),now_ns=12001*NS).qualified)

    def test_changed_payload_same_key_rejects_and_stops(self):
        self.arm()
        with self.assertRaises(ValueError):self.send(at=10,ttl=2999)
        self.assertTrue(self.owner.snapshot()['stopped'])

    def test_same_sequence_different_type_is_separate_non_motion_key(self):
        motion=self.arm();config=self.send(at=1,kind=5)
        self.assertNotEqual(motion.key,config.key);self.assertEqual(self.owner.snapshot()['request_count'],2)
        got=self.owner.response(response(self.ctx,kind=9,request_type=5),now_ns=500*NS)
        self.assertFalse(got.qualified)
        got=self.owner.response(response(self.ctx,wire_seq=41),now_ns=500*NS)
        self.assertIs(got.request,motion);self.assertTrue(got.qualified)

    def test_unsupported_request_type_refuses(self):
        with self.assertRaises(ValueError):self.send(kind=12)

    def test_superseded_request_cannot_qualify_late_ack(self):
        old=self.arm();new=self.send(at=100,seq=4)
        got=self.owner.response(response(self.ctx,request_seq=3),now_ns=500*NS)
        self.assertIs(got.request,old);self.assertFalse(got.qualified);self.assertEqual(got.status,'superseded')
        got=self.owner.response(response(self.ctx,request_seq=4,wire_seq=41),now_ns=500*NS)
        self.assertTrue(got.qualified);self.assertIs(got.request,new)

    def test_stop_request_needs_no_observation_and_cannot_restart(self):
        self.arm();self.send(at=1,seq=4,action=0,ttl=0,speed=0)
        self.assertTrue(self.owner.snapshot()['stopped'])
        self.assertFalse(self.owner.response(response(self.ctx),now_ns=500*NS).qualified)
        with self.assertRaises(ValueError):self.send(at=500,seq=5)

    def test_stop_zero_field_rule_and_command_id_match(self):
        for raw in [request(self.ctx,action=0,ttl=0,speed=1),packet(14,struct.pack('<IHBhhBHH',7,4,1,0,0,5,1000,9),seq=3)]:
            self.setUp()
            with self.assertRaises(ValueError):self.owner.request(raw,first_send_ns=0,now_ns=0)

    def test_expired_request_not_revived_by_new_observation(self):
        self.arm();self.assertFalse(self.owner.check(now_ns=1500*NS).qualified)
        self.observe(seq=10,sample=1500,at=1500)
        got=self.owner.response(response(self.ctx,at=1501,remaining=3000),now_ns=1501*NS)
        self.assertFalse(got.qualified);self.assertEqual(got.deadline_ns,1500*NS)

    def test_unknown_original_observation_is_never_backfilled(self):
        self.send();self.observe(at=1)
        self.assertFalse(self.owner.response(response(self.ctx),now_ns=500*NS).qualified)

    def test_observation_eviction_invalidates_original_association(self):
        self.arm()
        for seq in range(10,14):self.observe(seq=seq,sample=1,at=1)
        self.assertEqual(self.owner.snapshot()['observation_count'],4)
        got=self.owner.response(response(self.ctx),now_ns=500*NS)
        self.assertFalse(got.qualified);self.assertEqual(got.status,'observation_evicted')

    def test_state8_and_non_motion_responses_never_qualify(self):
        self.arm();self.assertFalse(self.owner.response(response(self.ctx,kind=8),now_ns=500*NS).qualified)

    def test_ack_state3d_current_codes_and_deadlines(self):
        original=self.arm();a=self.owner.response(response(self.ctx,remaining=700),now_ns=500*NS)
        b=self.owner.response(response(self.ctx,kind=16,wire_seq=41,at=600,remaining=2000),now_ns=600*NS)
        self.assertTrue(b.qualified);self.assertIs(b.request,original);self.assertEqual(a.deadline_ns,b.deadline_ns)

    def test_accepted_applied_and_incomplete_quality_are_not_capture(self):
        for kw in ({'phase':1},{'phase':2},{'quality':7}):
            self.setUp();self.arm()
            self.assertFalse(self.owner.response(response(self.ctx,**kw),now_ns=500*NS).qualified)

    def test_fault_rejected_stopped_revoke_current(self):
        for kw in ({'fault':1},{'phase':0},{'phase':4}):
            self.setUp();self.arm();got=self.owner.response(response(self.ctx,**kw),now_ns=500*NS)
            self.assertFalse(got.qualified);self.assertTrue(self.owner.snapshot()['stopped'])

    def test_response_target_and_capture_epoch_mismatch_refuse(self):
        for kw in ({'yaw':1},{'pitch':1},{'speed':6},{'control_epoch':3}):
            self.setUp();self.arm()
            try:got=self.owner.response(response(self.ctx,**kw),now_ns=500*NS)
            except ValueError:continue
            self.assertFalse(got.qualified)

    def test_missing_timing_capture_and_nonnull_hashes_are_not_verification(self):
        for name in ('timing','capture'):
            self.setUp();self.arm();self.deps.mods[name]=lambda result:None
            got=self.owner.response(response(self.ctx,hashes=True),now_ns=500*NS)
            self.assertFalse(got.qualified)

    def test_wrong_boot_request_raw_batch_and_capture_codes_refuse(self):
        cases=[('timing','boot',object()),('timing','request',object()),('timing','response_raw',b'{}'),
            ('timing','serial_upper_ns',True),('capture','boot',object()),('capture','request',object()),
            ('capture','response_raw',b'{}'),('capture','batch',None),('capture','yaw_q',1),
            ('capture','capture_seq',6),('capture','control_epoch',3),('capture','quality',7)]
        for name,field,value in cases:
            self.setUp();self.arm();self.deps.mods[name]=lambda r,field=field,value=value:dataclasses.replace(r,**{field:value})
            with self.assertRaises(ValueError):self.owner.response(response(self.ctx),now_ns=500*NS)

    def test_unknown_source_or_observation_verifier_does_not_qualify(self):
        self.owner.boot(dataclasses.replace(self.binding_for(2,session=8),source=None),now_ns=0);self.ctx['session']=8
        self.assertFalse(self.observe());self.send()
        self.assertFalse(self.owner.response(response(self.ctx),now_ns=500*NS).qualified)
        self.setUp();self.deps.mods['observation']=lambda r:None
        self.assertFalse(self.observe());self.send()
        self.assertFalse(self.owner.response(response(self.ctx),now_ns=500*NS).qualified)

    def test_no_default_verifier_or_pc_direct_capture(self):
        owner=hil.HilRequestTracker(run_id='run-1')
        with self.assertRaises(ValueError):owner.boot(self.binding,now_ns=0)
        with self.assertRaises(ValueError):self.owner.boot(self.binding_for(2,session=8,topology_id=2),now_ns=0)

    def test_invalid_ttl_curvature_and_bad_crc(self):
        for kw in ({'ttl':0},{'ttl':3001},{'speed':0,'yaw':1},{'yaw':15000,'pitch':15000}):
            self.setUp();self.observe()
            with self.assertRaises(ValueError):self.send(**kw)
        self.setUp();raw=bytearray(request(self.ctx));raw[-1]^=1
        with self.assertRaises(ValueError):self.owner.request(bytes(raw),first_send_ns=0,now_ns=0)
        self.setUp();self.arm();doc=json.loads(response(self.ctx));bad=bytearray.fromhex(doc['wire_frame_hex']);bad[-1]^=1;doc['wire_frame_hex']=bad.hex()
        with self.assertRaises(ValueError):self.owner.response(encoded(doc),now_ns=500*NS)

    def test_wrong_request_type_cannot_match_motion_seq(self):
        self.arm();self.send(at=1,kind=5)
        with self.assertRaises(ValueError):self.owner.response(response(self.ctx,request_type=5),now_ns=500*NS)

    def test_duplicate_response_receipt_does_not_renew(self):
        self.arm();a=self.owner.response(response(self.ctx),now_ns=500*NS)
        duplicate=response(self.ctx,at=700,tick=500)
        b=self.owner.response(duplicate,now_ns=700*NS)
        self.assertFalse(b.qualified);self.assertEqual(a.deadline_ns,b.deadline_ns)

    def test_changed_duplicate_and_out_of_order_response_stop(self):
        for raw in [response(self.ctx,wire_seq=39,at=600),response(self.ctx,remaining=900,at=600)]:
            self.setUp();self.arm();self.owner.response(response(self.ctx),now_ns=500*NS)
            with self.assertRaises(ValueError):self.owner.response(raw,now_ns=600*NS)
            self.assertTrue(self.owner.snapshot()['stopped'])

    def test_request_sequence_half_range_wrap_and_epoch_change_stop(self):
        for first,second in ((0,32768),(65535,0)):
            self.setUp();self.observe();self.send(seq=first)
            with self.assertRaises(ValueError):self.send(at=1,seq=second)
        self.setUp();self.arm();wrong=request(dict(self.ctx,config_epoch=3),seq=4)
        with self.assertRaises(ValueError):self.owner.request(wrong,first_send_ns=NS,now_ns=NS)

    def test_capture_sequence_wrap_refuses(self):
        self.arm();self.owner.response(response(self.ctx,capture_seq=65535),now_ns=500*NS)
        with self.assertRaises(ValueError):self.owner.response(response(self.ctx,wire_seq=41,capture_seq=0,at=600),now_ns=600*NS)

    def test_clock_regression_first_send_and_future_receipt_refuse(self):
        for bad in (True,-1,0.5):
            self.setUp()
            with self.assertRaises(ValueError):self.owner.check(now_ns=bad)
        self.setUp();self.arm();self.owner.check(now_ns=100*NS)
        with self.assertRaises(ValueError):self.owner.check(now_ns=99*NS)
        self.setUp()
        with self.assertRaises(ValueError):self.owner.request(request(self.ctx),first_send_ns=NS,now_ns=0)

    def test_callback_stop_failure_and_caught_reentry_cannot_publish(self):
        for name in ('observation','timing','capture'):
            for operation in ('stop','reentry','bad_shape','exception'):
                self.setUp()
                if name!='observation':self.arm()
                def hook(operation=operation):
                    if operation=='stop':self.owner.stop('callback')
                    elif operation=='exception':raise RuntimeError('fixture verifier failed')
                    else:
                        try:
                            if operation=='reentry':self.owner.check(now_ns=500*NS)
                            else:self.owner.response(b'{}',unknown=1)
                        except ValueError:pass
                self.deps.hooks[name]=hook
                with self.assertRaises(ValueError):
                    if name=='observation':self.observe()
                    else:self.owner.response(response(self.ctx),now_ns=500*NS)
                self.assertTrue(self.owner.snapshot()['stopped'])

    def test_boot_veto_retires_verified_proposal_and_fresh_boot_recovers(self):
        proposed=self.binding_for(2,session=8);self.deps.hooks['boot']=lambda:self.owner.stop('during_boot')
        with self.assertRaises(ValueError):self.owner.boot(proposed,now_ns=0)
        self.deps.hooks.clear()
        with self.assertRaises(ValueError):self.owner.boot(proposed,now_ns=0)
        self.owner.boot(self.binding_for(3,session=9),now_ns=0)
        self.assertFalse(self.owner.snapshot()['stopped'])

    def test_public_call_shape_errors_latch_even_when_caught(self):
        for call in [lambda:self.owner.request(),lambda:self.owner.check(unknown=1),lambda:self.owner.stop(unknown=1),lambda:self.owner.snapshot(unknown=1)]:
            self.setUp()
            with self.assertRaises(ValueError):call()
            self.assertTrue(self.owner.snapshot()['stopped'])

    def test_bounded_history_eviction_and_no_replay(self):
        for seq in range(20):self.send(kind=5,seq=seq,at=seq)
        snap=self.owner.snapshot();self.assertEqual(snap['request_count'],16)
        self.assertEqual(len(snap['request_high_waters']),1)
        with self.assertRaises(ValueError):self.send(kind=5,seq=0,at=20)

    def test_new_boot_cannot_reuse_retired_session_and_old_capture(self):
        original=self.arm();raw=response(self.ctx)
        self.owner.boot(self.binding_for(2,session=8),now_ns=100*NS)
        with self.assertRaises(ValueError):self.owner.response(raw,now_ns=500*NS)
        with self.assertRaises(ValueError):self.owner.boot(self.binding_for(3),now_ns=500*NS)

    def test_records_and_snapshots_are_defensive(self):
        original=self.arm()
        with self.assertRaises(dataclasses.FrozenInstanceError):original.first_send_ns=NS
        snap=self.owner.snapshot();snap['requests'].clear();self.ctx['session']=999
        self.assertEqual(self.owner.snapshot()['request_count'],1)


if __name__=='__main__':unittest.main(verbosity=2)
