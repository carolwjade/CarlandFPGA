"""Root's new continuous live demo coordinator. Explicit entry only.

Native owns guarded per-physics-frame motion; source/AI/real board IO are separate
workers. No precomputed route, private scene in AI, total mission cap or replay.
"""
import concurrent.futures,hashlib,json,math,os,pathlib,sys,time,traceback
O=pathlib.Path(__file__).parent;R=pathlib.Path('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发');W=pathlib.Path('C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发')
sys.path[:0]=[str(W),str(O/'continuous-board-session-800/source'),str(O/'continuous-B-review-fix-822'),str(O/'continuous-command-map-810')]
from host_board_session import BoardSession
from native_client import NativeClient
from competition.deepeye.simulation.sensors.live_sensor_worker import LiveSensorWorker,SnapshotPose
from competition.deepeye.ai_pc.continuous_live_advice import LiveAIWorker,LiveProfile

def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def digest(v):return hashlib.sha256(raw(v)).hexdigest()
def atomic(p,v):
 tmp=p.with_name(p.name+'.Root808.tmp');tmp.write_bytes(raw(v)+b'\n');os.replace(tmp,p)
def load(p):return json.loads(p.read_bytes())

def main(run):
 from command_map import command_for_advice
 cfg=load(run/'config.json');status=pathlib.Path(cfg['host_status_file']);epoch=cfg['world_epoch']
 result=dict(operation_id='A-GEN4-CONTINUOUS-DEMO-20261104-808-R01',world_epoch=epoch,requirements_sha256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d',complete=False,arrival=False,board_started=False,formal_all29='not_run')
 journal=(run/'host-events.jsonl').open('xb',buffering=0)
 def log(event,**value):journal.write(raw(dict(event=event,host_qpc_ns=str(time.perf_counter_ns()),**value))+b'\n')
 def display(**fields):
  visible.update(fields);visible['updated_qpc_ns']=str(time.perf_counter_ns())
  visible['status_seq']=visible.get('status_seq',0)+1
  visible.update(abi='DEEPEYE-CONTINUOUS-HOST-801-v1',world_epoch=epoch,updated_unix_ms=int(time.time()*1000),connected=True)
  visible['board']=dict(connected=visible.get('board_connected',False),pwm=str(visible.get('pwm_high','等待')),stop_acknowledged=visible.get('stop_acknowledged',False))
  visible['source']=dict(channel_counts=visible.get('counts'),sample_count=visible.get('sample_count',0),e4_bytes=visible.get('wire_bytes',0),raw_bytes='4通道值',compressed_bytes='RAW回退或无损块')
  visible['ai']=dict(risk=visible.get('risk'),direction=str(visible.get('ai_direction','等待')))
  visible['operator']=dict(ack_seq=visible.get('operator_ack_seq',0),state=visible.get('operator_state','pending'))
  atomic(status,visible)
 visible=dict(stage='等待鼠标设置场景并点击开始',board='未连接',ai='等待实际E4观测',requested_speed_m_s=.1,actual_speed_m_s=0.,paused=False,counts=[None]*4,quality=0,wire_bytes=0,lossless_match=False,phase='EDITING')
 display();print(json.dumps(dict(waiting_for_real_ui_start=True,run=str(run))),flush=True)
 frozen_path=run/'frozen.json'
 while not frozen_path.exists():time.sleep(.05)
 frozen=load(frozen_path);assert frozen['world_epoch']==epoch and frozen['native_install_result']['ok'] is True
 gates=frozen['public_gates'];public_goal=dict(exit_center_m=gates['exit']['center'],exit_outward_normal_world=gates['exit']['normal'],gate_radius_m=.25,entry_center_m=gates['entry']['center'],entry_inward_normal_world=[-v for v in gates['entry']['normal']],exit_clearance_m=.65)
 native=NativeClient.connect(cfg['port'],cfg['token']);source=None;ai=None;board=None
 board_pool=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='actual-board800')
 def start_board():
  nonlocal board
  board=BoardSession(repository_root=R,stage_directory=O/'continuous-board-session-800',evidence_directory=run/'board');return board.start()
 board_future=board_pool.submit(start_board);board_kind='init';board_meta={}
 source_future=ai_future=None;source_pending=observation=advice=None
 desired=None;held=None;grant=0;last_apply=0;last_source=-1;last_native_poll=0.;last_status=0.;source_seq=0;operator_seq=-1;operator_generation=0;ai_generation=0;paused=False;speed_cap=.1;want_stop=False;last_snapshot_at=-1;source_origin=None
 try:
  display(stage='加载一次实板固件，建立持续连接',board='连接与真实初始化中')
  while True:
   now=time.perf_counter_ns();sample=native.state();state=sample['native'];last_native_poll=time.monotonic()
   log('native-observed',sample=sample)
   if state['fault'] and not (want_stop and 'native_stop' in result and state['fault']=='operator_stop'):
    raise RuntimeError('NATIVE_SAFETY_FAULT:'+state['fault'])
   if state['phase']=='ARRIVED':result['arrival']=True;result['arrival_native']=sample;want_stop=True
   op_path=run/'operator_intent.json'
   if op_path.exists():
    op=load(op_path)
    if int(op['seq'])>operator_seq:
     operator_seq=int(op['seq']);operator_generation+=1;advice=None;desired=None
     assert op['world_epoch']==epoch and op['actual_board_action_performed'] is False
     kind=op['action'];log('operator-intent',intent=op)
     speed_cap=float(op['requested_speed_m_s']);assert 0<=speed_cap<=.25
     paused=bool(op['requested_paused'])
     if kind=='stop' or op['stop_latched']:want_stop=True
   if state['operator_request']=='pause' and not paused:paused=True;operator_generation+=1;desired=None
   if state['operator_request']=='stop':want_stop=True
   if board_future is not None and board_future.done():
    actual=board_future.result();kind=board_kind;meta=board_meta;board_future=None
    if kind=='init':
     result['board_started']=True;binding={k:actual[k] for k in ['boot_id','build_id','request_hash']};native.bind_board(binding)
     source=LiveSensorWorker(source_root=W,world_epoch=epoch,private_pieces=frozen['private_pieces'],background_sigma=.005,material_sigma={'water':.1,'hard_rock':.01,'casing':None,'fault':.02,'void':None},boundary_policy='known_box_closed_candidate')
     ai=LiveAIWorker(source_root=W,world_epoch=epoch,profile=LiveProfile(background_c0=2.3,initial_speed_cap_m_s=.1))
     display(stage='等待真实模拟传感器→FPGA E4→PC AI首轮结果',board_connected=True)
     log('actual-board-init',response=actual)
    elif kind=='sense':
     r=actual['response']['result'];original=meta['source'];payload=original.to_payload()
     assert r['source_digest']==digest(payload) and r['source_seq']==meta['source_seq'] and r['correlation']=='FOUR_FRAME_CRC_SOURCE_CONSISTENT'
     decoded=[row['points'][0]['value'] for row in r['decoded']]
     assert decoded==list(original.channel_counts) and r['quality']==original.quality
     observation={k:payload[k] for k in ['world_epoch','segment_id','at_qpc_ns','completed_qpc_ns','position_m','orientation_xyzw','speed_m_s','quality']}
     observation.update(channel_counts=decoded,board_frame_sha256=hashlib.sha256(bytes.fromhex(r['wire_hex'])).hexdigest(),source_record_sha256=digest(payload),board_return_qpc_ns=str(actual['host_returned_ns']))
     display(counts=decoded,quality=r['quality'],wire_bytes=len(bytes.fromhex(r['wire_hex'])),lossless_match=True,sample_count=meta['source_seq'],codec='FPGA E4无损还原，允许RAW回退')
     log('source-e4-correlated',source=payload,actual_board=actual,public_observation=observation)
    elif kind=='apply':
     receipt=actual['response'];grant=actual['host_deadline_qpc_ns'];last_apply=now;held=meta['command']
     acknowledged=native.pause(receipt,grant_deadline_qpc_ns=grant) if held['speed_code']==0 else native.apply_pwm(receipt,grant_deadline_qpc_ns=grant)
     display(board_connected=True,actual_speed_m_s=held['speed_code']*.0125,pwm_period=receipt['result']['pwm_period'],pwm_high=receipt['result']['pwm_high'],paused=held['speed_code']==0,stage='实板控制连续运动闭环运行',operator_ack_seq=operator_seq if meta['operator_generation']==operator_generation else visible.get('operator_ack_seq',0),operator_state='applied' if meta['operator_generation']==operator_generation else 'pending')
     log('actual-pwm-native-accepted',board=actual,native=acknowledged,command=held)
     if desired==held:desired=None
    elif kind=='stop':result['board_stop']=actual;display(stop_acknowledged=True,operator_ack_seq=operator_seq,operator_state='applied');break
   if want_stop:
    if board_future is None:
     try:result['native_stop']=native.stop()
     except Exception as e:result['native_stop_error']=type(e).__name__
     if board is not None and board.client is not None and board.client.ready and not board.client.unknown:
      board_future=board_pool.submit(board.request,'stop');board_kind='stop';board_meta={}
     else:break
    time.sleep(.02);continue
   if source is not None and state['ready']:
    if source_future is not None and source_future.done():source_pending=source_future.result();source_future=None
    at=int(sample['host']['accepted_tick_qpc_interval_ns'][0])
    if source_future is None and source_pending is None and at>last_snapshot_at:
     last_snapshot_at=at
     snap=SnapshotPose('native-'+state['revision'],epoch,at,tuple(state['position_m']),tuple(state['orientation_xyzw']),float(state['speed_m_s']))
     source_future=source.submit(snap)
   if ai_future is not None and ai_future.done():
    produced=ai_future.result();ai_future=None
    if ai_generation==operator_generation:
     advice=produced;desired=command_for_advice(advice,state,speed_cap,paused)
     display(ai=advice['reason'],risk=advice['risk'],uncertainty=advice['uncertainty'],ai_direction=advice['direction_world'],ai_speed_limit_m_s=advice['speed_limit_m_s'])
     log('actual-pc-ai-completed',advice=advice,command=desired)
   if observation is not None and ai is not None and ai_future is None and int(observation['at_qpc_ns'])>last_source:
    current={k:state[k] for k in ['position_m','orientation_xyzw','speed_m_s']};current['at_qpc_ns']=str(sample['host']['accepted_tick_qpc_interval_ns'][0])
    request=dict(world_epoch=epoch,paused=paused,user_speed_cap_m_s=speed_cap,observation=observation,current_pose=current,public_goal=public_goal,executed_actions=[])
    ai_future=ai.submit(request);ai_generation=operator_generation;last_source=int(observation['at_qpc_ns'])
   if board is not None and board.client is not None and board.client.ready and board_future is None:
    if observation is not None and now-int(observation['at_qpc_ns'])>5_000_000_000:
     desired=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='actual_source_stale')
    command=None
    if paused or speed_cap==0:command=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='explicit_operator_pause')
    elif desired is not None:
     if advice is not None and advice.get('status')=='ADVISE':
      age=now-int(advice['source_acquisition_qpc_ns'])
      distance=math.dist(advice['source_pose']['position_m'],state['position_m'])
      aq=advice['source_pose']['orientation_xyzw'];bq=state['orientation_xyzw']
      def forward(q):
       x,y,z,w=q;return [2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]
      angle_dot=sum(a*b for a,b in zip(forward(aq),forward(bq)))
      if advice['world_epoch']!=epoch or not 0<=age<=5_000_000_000 or distance>.25 or angle_dot<math.cos(math.radians(15.)):
       desired=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='original_advice_inapplicable_at_dispatch')
      else:desired=command_for_advice(advice,state,speed_cap,paused)
     command=desired
    elif held is not None and held['speed_code']*.0125>speed_cap:
     from fractions import Fraction
     from competition.deepeye.integration.motion import validate
     code=min(held['speed_code'],int(Fraction(speed_cap)*80))
     y=math.trunc(held['yaw_q']*code/held['speed_code']);p=math.trunc(held['pitch_q']*code/held['speed_code'])
     validate('fast_9600',code,y,p)
     command=dict(yaw_q=y,pitch_q=p,speed_code=code,reason='operator_cap_reduced_actual_held_intent')
    elif held is not None and grant-now<7_000_000_000:command=held
    if command is not None and (held is None or command!=held or grant-now<7_000_000_000):
     fields={k:command[k] for k in ['yaw_q','pitch_q','speed_code']}
     board_future=board_pool.submit(board.apply,**fields);board_kind='apply';board_meta=dict(command=command,operator_generation=operator_generation)
    elif source_pending is not None and ai_future is None:
     candidate=source_pending;source_pending=None;source_seq+=1
     if source_origin is None:source_origin=candidate.snapshot.at_qpc_ns-1_000_000_000
     tick=(candidate.snapshot.at_qpc_ns-source_origin)//1_000_000
     board_future=board_pool.submit(board.sense,source_seq=source_seq,adc_tick_ms=tick,em_tick_ms=tick,counts=list(candidate.channel_counts),quality=candidate.quality,source_digest=digest(candidate.to_payload()));board_kind='sense';board_meta=dict(source=candidate,source_seq=source_seq)
   if time.monotonic()-last_status>.2:
    display(phase=state['phase'],native_speed_m_s=state['speed_m_s'],position_m=state['position_m'],requested_speed_m_s=speed_cap,operator_pause_requested=paused,source_age_s=None if observation is None else (now-int(observation['at_qpc_ns']))/1e9);last_status=time.monotonic()
   time.sleep(.015)
 except BaseException as e:
  result['failure']=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc());log('failed',failure=result['failure']);display(stage='已停止：'+str(e)[:160])
 finally:
  if source is not None:source.close(wait=True)
  if ai is not None:ai.close(wait=True)
  if board_future is not None:
   try:board_future.result(timeout=40)
   except BaseException as e:result['pending_terminal_error']=type(e).__name__
  if board is not None:
   try:result['board_close']=board_pool.submit(board.close).result(timeout=15)
   except BaseException as e:result['board_close_error']=type(e).__name__
  board_pool.shutdown(wait=True,cancel_futures=True)
  try:
   if not native.broken and 'native_stop' not in result:result['native_stop']=native.stop()
  except BaseException as e:result.setdefault('native_stop_error',type(e).__name__)
  native.close();result['complete']=bool(result.get('arrival') and result.get('board_stop') and result.get('board_close',{}).get('wait_confirmed') and not result.get('failure'))
  atomic(run/'RESULT.json',result);display(stage='完整出圈已完成' if result['complete'] else '本次运行已结束，待检查',complete=result['complete']);journal.close()
 print(json.dumps(dict(complete=result['complete'],arrival=result['arrival'],result=str(run/'RESULT.json'))),flush=True)
 return 0 if result['complete'] else 2
if __name__=='__main__':raise SystemExit(main(pathlib.Path(sys.argv[1])))
