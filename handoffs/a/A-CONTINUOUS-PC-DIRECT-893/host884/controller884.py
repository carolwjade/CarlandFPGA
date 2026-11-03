"""Root's candidate884 BOARD_PWM/PC_DIRECT continuous live demo coordinator. Explicit entry only.

Native owns guarded per-physics-frame motion; source/AI/real board IO are separate
workers. No precomputed route, private scene in AI, total mission cap or replay.
"""
import concurrent.futures,hashlib,json,math,os,pathlib,sys,time,traceback
O=pathlib.Path(__file__).parent;R=pathlib.Path('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发');W=pathlib.Path('C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发')
sys.path[:0]=[str(W),str(O/'continuous-board-session-800/source'),str(O/'continuous-B-review-fix-822'),str(O/'continuous-command-map-810')]
from host_board_session import BoardSession
from competition.deepeye.integration.continuous_native_client import NativeClient
from competition.deepeye.integration.live_pc_direct import PcDirectClient,advice_applicable as pc_advice_applicable,SOURCE_AGE_NS
from competition.deepeye.simulation.sensors.live_sensor_worker import LiveSensorWorker,SnapshotPose
from competition.deepeye.ai_pc.continuous_live_advice import LiveAIWorker,LiveProfile

def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def digest(v):return hashlib.sha256(raw(v)).hexdigest()
def atomic(p,v):
 tmp=p.with_name(p.name+'.Root833.tmp');tmp.write_bytes(raw(v)+b'\n');os.replace(tmp,p)
def load(p):return json.loads(p.read_bytes())

def advice_applicable(advice,state,epoch,now):
 """Original selected epoch/5s/.25m/15degree guard, including held renewals."""
 try:
  if advice is None or advice.get('status')!='ADVISE' or advice['world_epoch']!=epoch:return False
  age=now-int(advice['source_acquisition_qpc_ns'])
  if not 0<=age<=5_000_000_000 or math.dist(advice['source_pose']['position_m'],state['position_m'])>.25:return False
  def forward(q):
   x,y,z,w=q;return [2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]
  dot=sum(a*b for a,b in zip(forward(advice['source_pose']['orientation_xyzw']),forward(state['orientation_xyzw'])))
  return dot>=math.cos(math.radians(15.))
 except (KeyError,TypeError,ValueError,OverflowError):return False

def stop_native_once(native,result,reason):
 """Attempt one independent terminal native STOP, even on unknown response.
 No board acknowledgement is fabricated; physical STOP keeps single-IO order.
 """
 if result.get('native_stop_attempted'):return
 result['native_stop_attempted']=True;result['native_stop_reason']=reason
 try:result['native_stop']=native.stop()
 except BaseException as error:
  result['native_stop_error']=dict(type=type(error).__name__,message=str(error)[:256])

class RunControl:
 """Initial preference storage is separate from actual ongoing control.

 Reservation precedes the first submitted APPLY. Consumption of its real receipt
 latches that reservation, including zero; pause/resume never resets the latch.
 No future-run preference is read by the current-run speed policy after reserve.
 """
 def __init__(self,initial_request=.1):
  self.initial_request=float(initial_request);self.next_initial_preference=float(initial_request)
  self.initial_speed_latched=False;self.latched_initial_speed=None;self.reserved_initial_speed=None
  self.operator_seq=-1;self.operator_generation=0;self.control_seq=0;self.control_ack_seq=0
  self.preference_ack_seq=0;self.control_state='pending';self.last_intent_scope='control'
  self.paused=False;self.advice=None;self.desired=None;self.awaiting_resume_ai=False
  self.current_speed_source='awaiting_actual_board_apply'
 def speed_limit(self):
  if self.initial_speed_latched:return .25
  if self.reserved_initial_speed is not None:return self.reserved_initial_speed
  return self.initial_request
 def reserve_initial(self):
  if self.initial_speed_latched:return None
  if self.reserved_initial_speed is None:self.reserved_initial_speed=self.initial_request
  return self.reserved_initial_speed
 def consume_initial(self,reserved):
  if not self.initial_speed_latched:
   if reserved is None or reserved!=self.reserved_initial_speed:raise ValueError('INITIAL_APPLY_RESERVATION_REQUIRED')
   self.latched_initial_speed=reserved;self.initial_speed_latched=True
 def invalidate(self,*,awaiting_resume_ai=False):
  self.operator_generation+=1;self.advice=None;self.desired=None
  self.awaiting_resume_ai=awaiting_resume_ai;self.control_state='pending'
 def accept(self,op,epoch):
  seq=int(op['seq'])
  if seq<=self.operator_seq:return False
  if op.get('epoch',op.get('world_epoch'))!=epoch or op.get('world_epoch',epoch)!=epoch:
   raise ValueError('OPERATOR_WORLD_EPOCH')
  if op.get('actual_board_action_performed',False) is not False:raise ValueError('OPERATOR_IS_INTENT_ONLY')
  kind=op['action']
  if kind not in ('start','set_initial_speed','next_initial_speed','set_speed','pause','resume','stop'):
   raise ValueError('OPERATOR_ACTION')
  speed=op['requested_speed_m_s']
  if type(speed) not in (int,float) or not math.isfinite(speed) or not 0<=speed<=.25:
   raise ValueError('OPERATOR_INITIAL_SPEED_BOUND')
  if type(op['requested_paused']) is not bool:raise ValueError('OPERATOR_PAUSE_BOOL')
  self.operator_seq=seq
  # Pause/resume carry a UI snapshot of the slider, but do not consume it.
  if kind in ('start','set_initial_speed','next_initial_speed','set_speed'):
   self.next_initial_preference=float(speed);self.preference_ack_seq=seq
   if kind=='next_initial_speed' or self.initial_speed_latched or self.reserved_initial_speed is not None:
    self.last_intent_scope='next_initial_preference'
    return True
   self.initial_request=float(speed)
   if kind=='start':self.paused=op['requested_paused']
  elif kind=='pause':self.paused=True
  elif kind=='resume':self.paused=False
  self.control_seq=seq;self.last_intent_scope='control'
  self.invalidate(awaiting_resume_ai=kind=='resume')
  return True
 def acknowledge_apply(self,generation,control_seq,command,*,control_ack_allowed=True):
  if control_ack_allowed and generation==self.operator_generation:
   self.control_ack_seq=control_seq;self.control_state='applied'
  reason=command['reason']
  self.current_speed_source=('explicit_pause_via_actual_board' if reason=='explicit_operator_pause'
                            else 'host_safety_guard_via_actual_board' if reason in
                            ('actual_source_stale','original_advice_inapplicable_at_dispatch','resume_waiting_for_fresh_actual_ai','held_original_advice_inapplicable_at_renewal')
                            else 'actual_pc_ai_and_board')
 def status_fields(self):
  stored=self.last_intent_scope=='next_initial_preference'
  return dict(initial_request_m_s=self.initial_request,initial_speed_latched=self.initial_speed_latched,
              latched_initial_speed_m_s=self.latched_initial_speed,
              reserved_initial_speed_m_s=self.reserved_initial_speed,
              next_initial_speed_m_s=self.next_initial_preference,
              requested_speed_m_s=self.initial_request,current_speed_source=self.current_speed_source,
              operator_ack_seq=self.preference_ack_seq if stored else self.control_ack_seq,
              operator_state='next_initial_stored' if stored else self.control_state,
              operator_preference_ack_seq=self.preference_ack_seq,
              operator_control_ack_seq=self.control_ack_seq,
              operator_control_pending_seq=self.control_seq,
              operator_ack_kind='preference_storage' if stored else 'actual_control',
              operator_pause_requested=self.paused)

def publish_display(path,value,log):
 """Display races do not retry/block physical requests or swallow journal errors."""
 try:atomic(path,value)
 except PermissionError as e:
  log('display-publication-delayed',path=str(path),error=type(e).__name__,
      winerror=getattr(e,'winerror',None),message=str(e))
  return False
 return True

def main(run):
 from command_map import command_for_advice
 cfg=load(run/'config.json');status=pathlib.Path(cfg['host_status_file']);epoch=cfg['world_epoch']
 mode=cfg.get('admission_mode','BOARD_PWM')
 if mode not in ('BOARD_PWM','PC_DIRECT'):raise ValueError('EXPLICIT_ADMISSION_MODE')
 direct=mode=='PC_DIRECT'
 operation_id=cfg['operation_id'];board_stage=pathlib.Path(cfg['board_stage_directory'])
 if not board_stage.is_absolute():board_stage=O/board_stage
 control=RunControl()
 result=dict(operation_id=operation_id,world_epoch=epoch,board_stage_directory=str(board_stage),requirements_sha256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d',complete=False,arrival=False,board_started=False,formal_all29='not_run')
 journal=(run/'host-events.jsonl').open('xb',buffering=0)
 def log(event,**value):journal.write(raw(dict(event=event,host_qpc_ns=str(time.perf_counter_ns()),**value))+b'\n')
 def display(**fields):
  visible.update(fields);visible.update(control.status_fields());visible['updated_qpc_ns']=str(time.perf_counter_ns())
  visible['status_seq']=visible.get('status_seq',0)+1
  visible.update(abi='DEEPEYE-CONTINUOUS-HOST-801-v1',operation_id=operation_id,world_epoch=epoch,updated_unix_ms=int(time.time()*1000),connected=True)
  visible['board']=dict(connected=visible.get('board_connected',False),pwm=str(visible.get('pwm_high','等待')),stop_acknowledged=visible.get('stop_acknowledged',False))
  visible['source']=dict(channel_counts=visible.get('counts'),sample_count=visible.get('sample_count',0),e4_bytes=visible.get('wire_bytes',0),raw_bytes='4通道值',compressed_bytes='RAW回退或无损块')
  visible['ai']=dict(risk=visible.get('risk'),direction=str(visible.get('ai_direction','等待')))
  visible['operator']=dict(ack_seq=visible.get('operator_ack_seq',0),state=visible.get('operator_state','pending'))
  publish_display(status,visible,log)
 visible=dict(stage='等待鼠标设置场景并点击开始',board='未连接',ai='等待实际E4观测',requested_speed_m_s=.1,actual_speed_m_s=0.,paused=False,counts=[None]*4,quality=0,wire_bytes=0,lossless_match=False,phase='EDITING')
 display();print(json.dumps(dict(waiting_for_real_ui_start=True,run=str(run))),flush=True)
 frozen_path=run/'frozen.json'
 while not frozen_path.exists():time.sleep(.05)
 frozen=load(frozen_path);assert frozen['world_epoch']==epoch and frozen['native_install_result']['ok'] is True
 if frozen.get('admission_mode','BOARD_PWM')!=mode:raise ValueError('FROZEN_ADMISSION_MODE')
 gates=frozen['public_gates'];public_goal=dict(exit_center_m=gates['exit']['center'],exit_outward_normal_world=gates['exit']['normal'],gate_radius_m=.25,entry_center_m=gates['entry']['center'],entry_inward_normal_world=[-v for v in gates['entry']['normal']],exit_clearance_m=.65)
 native=(PcDirectClient.connect(cfg['port'],cfg['token'],world_epoch=epoch) if direct else NativeClient.connect(cfg['port'],cfg['token']));source=None;ai=None;board=None
 result['admission_mode']=mode;visible['admission_mode']=mode;visible['action_source']='pc_direct_host' if direct else 'board_capture'
 board_pool=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix=operation_id)
 def start_board():
  nonlocal board
  board=BoardSession(repository_root=R,stage_directory=board_stage,evidence_directory=run/'board')
  if board.plan['operation_id']!=operation_id:raise ValueError('CONFIG_BOARD_OPERATION_ID')
  if board.plan.get('world_epoch',epoch)!=epoch:raise ValueError('CONFIG_BOARD_WORLD_EPOCH')
  return board.start()
 board_future=board_pool.submit(start_board);board_kind='init';board_meta={}
 source_future=ai_future=None;source_pending=observation=advice=None
 source_future_snapshot=source_pending_snapshot=None;last_pc_advice_hash=None
 held=None;held_advice=None;grant=0;last_apply=0;last_source=-1;last_native_poll=0.;last_status=0.;source_seq=0;ai_generation=0;want_stop=False;last_snapshot_at=-1;source_origin=None;native_pause_seen=False
 try:
  display(stage='加载一次实板固件，建立持续连接',board='连接与真实初始化中')
  while True:
   now=time.perf_counter_ns();sample=native.state();state=sample['native'];last_native_poll=time.monotonic()
   log('native-observed',sample=sample)
   if state['fault'] and not (want_stop and 'native_stop' in result and state['fault']=='operator_stop'):
    raise RuntimeError('NATIVE_SAFETY_FAULT:'+state['fault'])
   if state['phase']=='ARRIVED':result['arrival']=True;result['arrival_native']=sample;want_stop=True
   if want_stop:stop_native_once(native,result,'arrival_or_terminal_control')
   op_path=run/'operator_intent.json';operator_resumed=False
   if op_path.exists():
    op=load(op_path)
    if control.accept(op,epoch):
     operator_resumed=op['action']=='resume'
     if control.last_intent_scope=='control' and (op['action']=='stop' or op.get('stop_latched',False)):
      want_stop=True;stop_native_once(native,result,'operator_intent')
     log('operator-intent',intent=op,scope=control.last_intent_scope)
     display()
   if state['operator_request']=='pause':
    if not native_pause_seen and not control.paused and not operator_resumed:control.paused=True;control.invalidate()
    native_pause_seen=True
   else:native_pause_seen=False
   if state['operator_request']=='stop':
    want_stop=True;stop_native_once(native,result,'native_operator_request')
   if board_future is not None and board_future.done():
    actual=board_future.result();kind=board_kind;meta=board_meta;board_future=None
    if kind=='init':
     result['board_started']=True;binding={k:actual[k] for k in ['boot_id','build_id','request_hash']};native.bind_board(binding)
     source=LiveSensorWorker(source_root=W,world_epoch=epoch,private_pieces=frozen['private_pieces'],background_sigma=.005,material_sigma={'water':.1,'hard_rock':.01,'casing':None,'fault':.02,'void':None},boundary_policy='known_box_closed_candidate')
     ai=LiveAIWorker(source_root=W,world_epoch=epoch,profile=LiveProfile(background_c0=2.3,initial_speed_cap_m_s=.1,max_source_age_s=1.5 if direct else 5.0))
     display(stage='等待真实模拟传感器→FPGA E4→PC AI首轮结果',board_connected=True)
     log('actual-board-init',response=actual)
    elif kind=='sense':
     r=actual['response']['result'];original=meta['source'];payload=original.to_payload()
     assert r['source_digest']==digest(payload) and r['source_seq']==meta['source_seq'] and r['correlation']=='FOUR_FRAME_CRC_SOURCE_CONSISTENT'
     decoded=[row['points'][0]['value'] for row in r['decoded']]
     assert decoded==list(original.channel_counts) and r['quality']==original.quality
     observation={k:payload[k] for k in ['world_epoch','segment_id','at_qpc_ns','completed_qpc_ns','position_m','orientation_xyzw','speed_m_s','quality']}
     if direct and not want_stop:
      if now-int(payload['at_qpc_ns'])>=SOURCE_AGE_NS:
       log('pc-source-expired-before-observe',source=payload,actual_board=actual);continue
      registered=native.observe_pc(meta['native_snapshot'],payload,actual,source_seq=meta['source_seq'])
      log('pc-real-observation-native-registered',source=payload,actual_board=actual,native=registered)
     observation.update(channel_counts=decoded,board_frame_sha256=hashlib.sha256(bytes.fromhex(r['wire_hex'])).hexdigest(),source_record_sha256=digest(payload),board_return_qpc_ns=str(actual['host_returned_ns']))
     display(counts=decoded,quality=r['quality'],wire_bytes=len(bytes.fromhex(r['wire_hex'])),lossless_match=True,sample_count=meta['source_seq'],codec='FPGA E4无损还原，允许RAW回退')
     log('source-e4-correlated',source=payload,actual_board=actual,public_observation=observation)
    elif kind=='apply':
     receipt=actual['response'];grant=actual['host_deadline_qpc_ns'];last_apply=now;held=meta['command']
     held_advice=meta.get('actual_advice') if held['speed_code']>0 else None
     control.consume_initial(meta['reserved_initial_speed'])
     if want_stop or result.get('native_stop_attempted'):
      log('actual-pwm-terminal-not-admitted',board=actual,command=held,reason='native_terminal_before_inflight_apply_returned')
     else:
      acknowledged=native.pause(receipt,grant_deadline_qpc_ns=grant) if held['speed_code']==0 else native.apply_pwm(receipt,grant_deadline_qpc_ns=grant)
      control.acknowledge_apply(meta['operator_generation'],meta['control_seq'],held,control_ack_allowed=meta['control_ack_allowed'])
      display(board_connected=True,actual_speed_m_s=held['speed_code']*.0125,pwm_period=receipt['result']['pwm_period'],pwm_high=receipt['result']['pwm_high'],paused=held['speed_code']==0,stage='实板控制连续运动闭环运行')
      log('actual-pwm-native-accepted',board=actual,native=acknowledged,command=held,initial_speed_latched=control.initial_speed_latched,latched_initial_speed_m_s=control.latched_initial_speed,advice_source_acquisition_qpc_ns=None if held_advice is None else held_advice['source_acquisition_qpc_ns'])
      if control.desired==held:control.desired=None
    elif kind=='stop':
     result['board_stop']=actual;control.control_ack_seq=control.control_seq;control.control_state='applied'
     display(stop_acknowledged=True);break
   if want_stop:
    stop_native_once(native,result,'terminal_control')
    if board_future is None:
     if board is not None and board.client is not None and board.client.ready and not board.client.unknown:
      board_future=board_pool.submit(board.request,'stop');board_kind='stop';board_meta={}
     else:break
    time.sleep(.02);continue
   if source is not None and state['ready']:
    if source_future is not None and source_future.done():
     source_pending=source_future.result();source_future=None
     source_pending_snapshot=source_future_snapshot;source_future_snapshot=None
    at=int(sample['host']['accepted_tick_qpc_interval_ns'][0])
    if source_future is None and source_pending is None and at>last_snapshot_at:
     last_snapshot_at=at
     snap=SnapshotPose('native-'+state['revision'],epoch,at,tuple(state['position_m']),tuple(state['orientation_xyzw']),float(state['speed_m_s']))
     source_future=source.submit(snap)
     if source_future is not None:source_future_snapshot=json.loads(raw(sample))
   if ai_future is not None and ai_future.done():
    produced=ai_future.result();ai_future=None
    if ai_generation==control.operator_generation:
     control.advice=produced;control.desired=command_for_advice(produced,state,control.speed_limit(),control.paused);control.awaiting_resume_ai=False
     display(ai=produced['reason'],risk=produced['risk'],uncertainty=produced['uncertainty'],ai_direction=produced['direction_world'],ai_speed_limit_m_s=produced['speed_limit_m_s'])
     log('actual-pc-ai-completed',advice=produced,command=control.desired)
   if observation is not None and ai is not None and ai_future is None and int(observation['at_qpc_ns'])>last_source:
    current={k:state[k] for k in ['position_m','orientation_xyzw','speed_m_s']};current['at_qpc_ns']=str(sample['host']['accepted_tick_qpc_interval_ns'][0])
    request=dict(world_epoch=epoch,paused=control.paused,user_speed_cap_m_s=control.speed_limit(),observation=observation,current_pose=current,public_goal=public_goal,executed_actions=[])
    ai_future=ai.submit(request);ai_generation=control.operator_generation;last_source=int(observation['at_qpc_ns'])
   if direct and board is not None and board.client is not None and board.client.ready:
    # Only native admission here: all physical board requests remain one IO worker.
    chosen=control.advice
    if control.paused and chosen is None:chosen=held_advice
    if chosen is not None and pc_advice_applicable(chosen,sample,epoch,now):
     command=command_for_advice(chosen,state,control.speed_limit(),control.paused)
     chosen_hash=digest(chosen)
     if held is None or command!=held or chosen_hash!=last_pc_advice_hash:
      reserved=control.reserve_initial()
      accepted=native.apply_advice(chosen,sample,command,paused=control.paused,
                                   operator_cap_m_s=control.speed_limit())
      control.consume_initial(reserved)
      control.acknowledge_apply(control.operator_generation,control.control_seq,command,
                               control_ack_allowed=not control.awaiting_resume_ai)
      control.current_speed_source='actual_pc_ai_direct_host_command'
      held=command;held_advice=chosen;last_pc_advice_hash=chosen_hash
      grant=native.last_pc_command['host_deadline_qpc_ns'];control.desired=None
      display(stage='PC直控：真实板观测→AI→连续运动',actual_speed_m_s=command['speed_code']*.0125,
              paused=command['speed_code']==0,pc_command_seq=native.pc_seq,
              pc_command_sha256=native.last_pc_command['command_sha256'])
      log('actual-pc-direct-native-accepted',advice=chosen,host_command=native.last_pc_command,
          native=accepted,command=command,initial_speed_latched=control.initial_speed_latched,
          latched_initial_speed_m_s=control.latched_initial_speed)
    # Stale sources/AI cannot renew a host lease. Native enforces its own1500ms.
   if direct and board is not None and board.client is not None and board.client.ready and board_future is None:
    if source_pending is not None and ai_future is None:
     candidate=source_pending;original_snapshot=source_pending_snapshot
     source_pending=source_pending_snapshot=None;source_seq+=1
     if source_origin is None:source_origin=candidate.snapshot.at_qpc_ns-1_000_000_000
     tick=(candidate.snapshot.at_qpc_ns-source_origin)//1_000_000
     board_future=board_pool.submit(board.sense,source_seq=source_seq,adc_tick_ms=tick,em_tick_ms=tick,
        counts=list(candidate.channel_counts),quality=candidate.quality,source_digest=digest(candidate.to_payload()))
     board_kind='sense';board_meta=dict(source=candidate,source_seq=source_seq,native_snapshot=original_snapshot)
   if not direct and board is not None and board.client is not None and board.client.ready and board_future is None:
    if observation is not None and now-int(observation['at_qpc_ns'])>5_000_000_000:
     control.desired=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='actual_source_stale')
    command=None;command_advice=None
    if control.paused:command=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='explicit_operator_pause')
    elif control.desired is not None:
     advice=control.advice
     if advice is not None and advice.get('status')=='ADVISE':
      if not advice_applicable(advice,state,epoch,now):
       control.desired=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='original_advice_inapplicable_at_dispatch')
      else:
       control.desired=command_for_advice(advice,state,control.speed_limit(),control.paused)
       command_advice=advice
     command=control.desired
    elif control.awaiting_resume_ai and held is not None and held['speed_code']!=0:
     command=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='resume_waiting_for_fresh_actual_ai')
    elif held is not None and grant-now<7_000_000_000:
     if held['speed_code']==0:command=held
     elif advice_applicable(held_advice,state,epoch,now):
      command=held;command_advice=held_advice
     elif advice_applicable(control.advice,state,epoch,now):
      command=command_for_advice(control.advice,state,control.speed_limit(),control.paused)
      command_advice=control.advice
     else:command=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='held_original_advice_inapplicable_at_renewal')
    # Every positive submission retains the actual original applicable ADVISE.
    if command is not None and command['speed_code']>0:
     if not advice_applicable(command_advice,state,epoch,now):
      command=dict(yaw_q=0,pitch_q=0,speed_code=0,reason='held_original_advice_inapplicable_at_renewal');command_advice=None
    if command is not None and (held is None or command!=held or grant-now<7_000_000_000):
     fields={k:command[k] for k in ['yaw_q','pitch_q','speed_code']}
     reserved=control.reserve_initial()
     board_meta=dict(command=command,actual_advice=command_advice,operator_generation=control.operator_generation,control_seq=control.control_seq,reserved_initial_speed=reserved,control_ack_allowed=not control.awaiting_resume_ai)
     board_future=board_pool.submit(board.apply,**fields);board_kind='apply'
    elif source_pending is not None and ai_future is None:
     candidate=source_pending;source_pending=None;source_seq+=1
     if source_origin is None:source_origin=candidate.snapshot.at_qpc_ns-1_000_000_000
     tick=(candidate.snapshot.at_qpc_ns-source_origin)//1_000_000
     board_future=board_pool.submit(board.sense,source_seq=source_seq,adc_tick_ms=tick,em_tick_ms=tick,counts=list(candidate.channel_counts),quality=candidate.quality,source_digest=digest(candidate.to_payload()));board_kind='sense';board_meta=dict(source=candidate,source_seq=source_seq)
   if time.monotonic()-last_status>.2:
    display(phase=state['phase'],native_speed_m_s=state['speed_m_s'],position_m=state['position_m'],source_age_s=None if observation is None else (now-int(observation['at_qpc_ns']))/1e9);last_status=time.monotonic()
   time.sleep(.015)
 except BaseException as e:
  stop_native_once(native,result,'controller_failure')
  if direct and native.broken:
   native.close();result['native_disconnect_after_unknown']=True
  result['failure']=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc());log('failed',failure=result['failure']);display(stage='已停止：'+str(e)[:160])
 finally:
  stop_native_once(native,result,'controller_finally')
  if source is not None:source.close(wait=True)
  if ai is not None:ai.close(wait=True)
  if board_future is not None:
   try:board_future.result(timeout=40)
   except BaseException as e:result['pending_terminal_error']=type(e).__name__
  if board is not None:
   try:result['board_close']=board_pool.submit(board.close).result(timeout=15)
   except BaseException as e:result['board_close_error']=type(e).__name__
  board_pool.shutdown(wait=True,cancel_futures=True)
  native.close();result['complete']=bool(result.get('arrival') and result.get('board_stop') and result.get('board_close',{}).get('wait_confirmed') and not result.get('failure'))
  result.update(initial_speed_latched=control.initial_speed_latched,latched_initial_speed_m_s=control.latched_initial_speed,next_initial_speed_m_s=control.next_initial_preference)
  atomic(run/'RESULT.json',result);display(stage='完整出圈已完成' if result['complete'] else '本次运行已结束，待检查',complete=result['complete']);journal.close()
 print(json.dumps(dict(complete=result['complete'],arrival=result['arrival'],result=str(run/'RESULT.json'))),flush=True)
 return 0 if result['complete'] else 2
if __name__=='__main__':raise SystemExit(main(pathlib.Path(sys.argv[1])))
