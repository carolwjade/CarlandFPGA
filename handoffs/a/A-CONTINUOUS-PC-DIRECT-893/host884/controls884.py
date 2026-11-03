"""New884 host-only controls. Actual835 public data + synthetic PC server.
No native/model/source numerical execution, board, network listener or UI.
"""
import ast,copy,hashlib,json,socket,sys,threading
from pathlib import Path
W=Path('C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发')
sys.path.insert(0,str(W))
from competition.deepeye.integration.continuous_native_client import NativeClient,canonical
from competition.deepeye.integration.live_pc_direct import PcDirectClient,verify_e4,EXTRA_STATE,digest
from competition.deepeye.integration.motion import validate
D=Path(__file__).parent;F=json.loads((D/'FIXTURE835.public.json').read_bytes())
source=F['recorded835_source'];actual=F['recorded835_actual_board'];advice=F['recorded835_advice']
binding={k:actual['response'][k] for k in ('boot_id','build_id','request_hash')}
epoch=source['world_epoch'];now=max(int(advice['inference_completed_qpc_ns']),actual['host_returned_ns'])+1000000
original=copy.deepcopy(F['recorded835_native_snapshot']);native_tick=int(original['native']['tick_usec']);read_tick=native_tick+(now-int(source['at_qpc_ns']))//1000

def pc_state():
 s=copy.deepcopy(original['native']);s.update(tick_usec=str(read_tick),read_now_usec=str(read_tick),board_request_seq=0,board_receipt_sha256='',admission_mode='PC_DIRECT',action_source='pc_direct_host',world_epoch=epoch,source_witness='a'*32,board_observation_seq=0,board_observation_sha256='',source_record_sha256='',observation_native_tick_usec='0',pc_command_seq=0,pc_command_sha256='')
 return s

def refused(f):
 try:f()
 except (ValueError,RuntimeError):return True
 raise AssertionError('expected refusal')

# Red: exact822 rejects the real-schema extension; green: explicit PC subclass.
s=pc_state();assert refused(lambda:NativeClient._validate_state(s))
left,right=socket.socketpair();c=PcDirectClient(left,'x'*64,world_epoch=epoch,board_binding=binding,clock=lambda:now)
c._validate_state(s)
bad=copy.deepcopy(s);bad['world_epoch']='foreign';assert refused(lambda:c._validate_state(bad))
bad=copy.deepcopy(s);bad['obstacle_truth']={};assert refused(lambda:c._validate_state(bad))
assert verify_e4(source,actual,binding=binding,source_seq=actual['response']['result']['source_seq'])['source_record_sha256']==digest(source)
corrupt=copy.deepcopy(actual);corrupt['response']['result']['wire_hex']='00'+corrupt['response']['result']['wire_hex'][2:];corrupt['response_sha256']=digest(corrupt['response'])
assert refused(lambda:verify_e4(source,corrupt,binding=binding,source_seq=actual['response']['result']['source_seq']))
wrong=dict(binding,request_hash='0'*64);assert refused(lambda:verify_e4(source,actual,binding=wrong,source_seq=actual['response']['result']['source_seq']))

requests=[];server_errors=[]
def server():
 state=pc_state();stream=right.makefile('rb')
 try:
  while True:
   line=stream.readline()
   if not line:break
   req=json.loads(line);requests.append(req);op=req['op']
   if op=='hello':pass
   elif op=='observe_pc':
    assert req['source_witness']=='a'*32 and req['source_segment_id']==source['segment_id']
    state.update(board_observation_seq=req['board_sense_seq'],board_observation_sha256=req['board_receipt_sha256'],source_record_sha256=req['source_record_sha256'],observation_native_tick_usec=str(native_tick))
   elif op in ('apply_pc_direct','pause_pc_direct'):
    body=req['command_json'].encode('ascii');assert hashlib.sha256(body).hexdigest()==req['command_sha256']
    cmd=json.loads(body);assert canonical(cmd)==body and all(type(cmd[k]) is str for k in ('first_send_qpc_ns','source_acquisition_qpc_ns','native_deadline_usec'))
    assert all(type(v) in (str,int) for v in cmd.values())
    assert cmd['source_acquisition_qpc_ns']==source['at_qpc_ns'] and cmd['first_send_qpc_ns']==str(now)
    mapped=validate('fast_9600',cmd['speed_code'],cmd['yaw_q'],cmd['pitch_q'])
    state.update(pc_command_seq=cmd['command_seq'],pc_command_sha256=req['command_sha256'],deadline_usec=cmd['native_deadline_usec'],target_speed_m_s=mapped.target_speed_m_s,yaw_curvature_per_m=mapped.curvature_yaw_per_m,pitch_curvature_per_m=mapped.curvature_pitch_per_m)
   elif op=='state':
    state.update(board_observation_seq=state['board_observation_seq']+1,board_observation_sha256='b'*64,source_record_sha256='c'*64)
   else:raise AssertionError(op)
   right.sendall(canonical(dict(abi=state['abi'],seq=req['seq'],ok=True,state=state))+b'\n')
 except BaseException as e:server_errors.append(repr(e))
 finally:stream.close();right.close()
t=threading.Thread(target=server);t.start()
try:
 c.hello();original['native'].update({k:pc_state()[k] for k in EXTRA_STATE});original['native']['tick_usec']=str(native_tick)
 c.observe_pc(original,source,actual,source_seq=actual['response']['result']['source_seq'])
 current=c.state();command=dict(speed_code=1,yaw_q=0,pitch_q=0)
 reply=c.apply_advice(advice,current,command,operator_cap_m_s=.1)
 assert reply['state']['pc_command_seq']==1 and c.last_pc_command['host_deadline_qpc_ns']==int(source['at_qpc_ns'])+1500000000
 assert refused(lambda:c.apply_advice(advice,current,dict(speed_code=20,yaw_q=0,pitch_q=0),operator_cap_m_s=.1))
 assert refused(lambda:c.apply_advice(advice,current,command,ttl_ms=3001))
 assert refused(lambda:c.apply_pwm({}))
 stale=copy.deepcopy(advice);stale['source_acquisition_qpc_ns']=str(now-1500000000)
 assert refused(lambda:c.apply_advice(stale,current,command))
 # A newer registered observation may be latest native state, while the held
 # PC command still references its genuinely registered older fresh source.
 state=copy.deepcopy(current['native']);state['board_observation_seq']+=1;state['board_observation_sha256']='b'*64
 c._validate_state(state)
finally:c.close();t.join(2)
assert not t.is_alive() and not server_errors,server_errors
assert [r['op'] for r in requests]==['hello','observe_pc','state','apply_pc_direct']

# Unknown write/EOF poisons once; no retry may touch the socket.
l,r=socket.socketpair();u=PcDirectClient(l,'x'*64,world_epoch=epoch,clock=lambda:now)
seen=[]
def unknown():
 b=r.recv(8192);seen.append(b);r.close()
t=threading.Thread(target=unknown);t.start()
assert refused(u.hello);assert u.broken;assert refused(u.hello);u.close();t.join(2)
assert len(seen)==1 and not t.is_alive()

# Preserve baseline and protected controller functions; no model execution.
assert hashlib.sha256((W/'competition/deepeye/integration/continuous_native_client.py').read_bytes()).hexdigest()=='1ae13d841e7c9ad11dd83d8eb94ec35152fd2e3b516d71fa5ccdc2562b20a0fb'
O=D.parent;a=ast.parse((O/'continuous-final-control-fix-847/controller847.py').read_text(encoding='utf8'));b=ast.parse((D/'controller884.py').read_text(encoding='utf8'))
for name in ('RunControl','publish_display','advice_applicable','stop_native_once'):
 assert ast.dump(next(x for x in a.body if getattr(x,'name',None)==name))==ast.dump(next(x for x in b.body if getattr(x,'name',None)==name))
print(json.dumps(dict(actual835_public_fixture_only=True,old822_extension_red=True,explicit_pc_extension_green=True,e4_crc_source_identity=True,canonical_host_command_and_fast_deadline=True,stale_cap_and_ttl_rejections=True,unknown_write_once_no_retry=True,protected_functions_unchanged=True,board_native_source_ai_execution=False)))
