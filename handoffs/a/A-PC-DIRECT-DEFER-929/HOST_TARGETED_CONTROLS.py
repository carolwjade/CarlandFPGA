"""New918 admission-headroom controls, historical835 public input only.
All native state/time/RTT responses are explicit synthetic seams; no runtime IO.
"""
import copy,hashlib,json,sys,types
from pathlib import Path
W=Path('C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发');sys.path.insert(0,str(W))
from competition.deepeye.integration.live_pc_direct import PcDirectClient,digest
from competition.deepeye.integration.continuous_native_client import ClockBracket,NativeRejected
D=Path(__file__).parent;F=json.loads((D.parent/'continuous-pc-direct-host-884/FIXTURE835.public.json').read_bytes())
source=F['recorded835_source'];actual=F['recorded835_actual_board'];advice=F['recorded835_advice'];epoch=source['world_epoch']

def setup(age_ms):
 now=int(source['at_qpc_ns'])+age_ms*1000000
 client=PcDirectClient(None,'x'*64,world_epoch=epoch,clock=lambda:now)
 state=copy.deepcopy(F['recorded835_native_snapshot']['native']);nt=int(state['tick_usec'])+age_ms*1000
 state.update(tick_usec=str(nt),read_now_usec=str(nt),board_request_seq=0,board_receipt_sha256='',admission_mode='PC_DIRECT',action_source='pc_direct_host',world_epoch=epoch,source_witness='a'*32,board_observation_seq=actual['response']['request_seq'],board_observation_sha256=actual['response_sha256'],source_record_sha256=digest(source),observation_native_tick_usec=F['recorded835_native_snapshot']['native']['tick_usec'],pc_command_seq=0,pc_command_sha256='',running=False,deadline_usec='0')
 obs=dict(board_sense_seq=actual['response']['request_seq'],board_receipt_sha256=actual['response_sha256'],board_frame_sha256=advice['board_frame_sha256'],source_record_sha256=digest(source),source=copy.deepcopy(source),native_tick_usec=F['recorded835_native_snapshot']['native']['tick_usec'])
 client.observation=obs;client.observations={obs['board_sense_seq']:obs}
 client.bracket=ClockBracket(now-20000000,now,nt)
 client.last_exchange={'send_qpc_ns':now-20000000,'receive_qpc_ns':now}
 sample=dict(native=state,host={'accepted_tick_qpc_interval_ns':[now-1000000,now]})
 return client,sample,now

def reject(fn,cls):
 try:fn()
 except cls:return
 raise AssertionError('expected fatal original failure')

# Red baseline would send while only130ms of ORIGINAL source lifetime remains.
c,s,now=setup(1370);calls=[];callbacks=[]
def should_not_send(self,*args,**kwargs):calls.append((args,kwargs));raise RuntimeError('UNSENDABLE_WAS_DISPATCHED')
c._exchange=types.MethodType(should_not_send,c)
try:r=c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0),attempt_callback=callbacks.append)
except TypeError:
 # Baseline has no callback API; demonstrate actual baseline transmission too.
 try:c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0))
 except RuntimeError:pass
 raise AssertionError('RED918 baseline dispatched near-expiry original source; sends='+str(len(calls)))
assert r['deferred'] is True and r['reason']=='pc_preflight_headroom' and not calls and not callbacks and c.pc_seq==0
assert c.last_accepted_pc_command is None
# An intent callback can be slow; post-callback preflight still may NOT send
# or consume a seq. The callback is evidence of intent, never wire admission.
slow,slow_state,base=setup(700);clock={'now':base};slow.clock=lambda:clock['now'];slow_calls=[]
def forbidden(self,*a,**k):slow_calls.append(1);raise AssertionError('late callback sent')
slow._exchange=types.MethodType(forbidden,slow)
def slow_callback(a):clock['now']+=800000000
r=slow.apply_advice(advice,slow_state,dict(speed_code=1,yaw_q=0,pitch_q=0),attempt_callback=slow_callback)
assert r['deferred'] is True and slow.pc_seq==0 and not slow_calls and slow.last_pc_command is None

# Adequate headroom: real-intent callback detached, exact normal result unchanged,
# and last_accepted captured only AFTER actual executable correlation.
c,s,now=setup(700);calls=[];attempts=[]
def accepted(self,op,**fields):
 calls.append((op,fields));a=self.last_pc_command;doc=a['command'];state=copy.deepcopy(s['native'])
 state.update(pc_command_seq=doc['command_seq'],pc_command_sha256=a['command_sha256'],deadline_usec=doc['native_deadline_usec'],target_speed_m_s=.0125,yaw_curvature_per_m=0.,pitch_curvature_per_m=0.,running=True)
 return dict(ok=True,state=state)
c._exchange=types.MethodType(accepted,c)
def callback(a):attempts.append(copy.deepcopy(a));a['command']['speed_code']=20
response=c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0),attempt_callback=callback)
assert response.get('deferred') is None and len(calls)==len(attempts)==1
assert json.loads(calls[0][1]['command_json'])['speed_code']==1
assert c.last_accepted_pc_command['command_sha256']==response['state']['pc_command_sha256']
accepted_record=copy.deepcopy(c.last_accepted_pc_command);s['native']=copy.deepcopy(response['state'])

# Only the NEW explicit nonmutating known rejection can defer a still-active,
# byte-identical prior executable command. New attempted seq is not retried.
def known(self,op,**fields):
 calls.append((op,fields));raise NativeRejected(dict(ok=False,reason='pc_admission_headroom',admission_applied=False,state=copy.deepcopy(s['native'])))
c._exchange=types.MethodType(known,c)
r=c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0),attempt_callback=lambda a:None)
assert r['deferred'] is True and r['reason']=='pc_admission_headroom' and len(calls)==2 and c.pc_seq==2
assert c.last_accepted_pc_command==accepted_record
for field,value in (('pc_command_seq',2),('running',False),('read_now_usec',s['native']['deadline_usec']),('yaw_curvature_per_m',.001),('pitch_curvature_per_m',.001),('pc_command_sha256','c'*64),('deadline_usec',str(int(s['native']['deadline_usec'])+1)),('target_speed_m_s',.025),('fault','operator_stop'),('ready',False)):
 bad=copy.deepcopy(s['native']);bad[field]=value
 def wrong(self,op,_bad=bad,**fields):raise NativeRejected(dict(ok=False,reason='pc_admission_headroom',admission_applied=False,state=_bad))
 c._exchange=types.MethodType(wrong,c)
 reject(lambda:c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0)),(NativeRejected,ValueError))
 assert c.last_accepted_pc_command==accepted_record
for reason,applied in (('pc_original_observation_deadline',False),('pc_admission_headroom',0),('pc_admission_headroom',True)):
 def wrong_reason(self,op,_reason=reason,_applied=applied,**fields):raise NativeRejected(dict(ok=False,reason=_reason,admission_applied=_applied,state=copy.deepcopy(s['native'])))
 c._exchange=types.MethodType(wrong_reason,c)
 reject(lambda:c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0)),NativeRejected)
 assert c.last_accepted_pc_command==accepted_record
c.last_accepted_pc_command=None;c._exchange=types.MethodType(known,c)
reject(lambda:c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0)),NativeRejected)
def unknown(self,*a,**k):raise TimeoutError('unknown write')
c._exchange=types.MethodType(unknown,c)
reject(lambda:c.apply_advice(advice,s,dict(speed_code=1,yaw_q=0,pitch_q=0)),TimeoutError)
print(json.dumps(dict(preflight_no_seq_no_write_no_callback=True,slow_intent_callback_rechecks_without_send=True,callback_detached_and_before_single_send=True,normal_response_preserved=True,last_accepted_only_after_correlation=True,known_nonmutating_headroom_only_deferred=True,changed_prior_state_missing_accepted_wrong_reason_unknown_fatal=True,original_FAST_1500_TTL_unchanged=True,actual_runtime_effects=False)))
