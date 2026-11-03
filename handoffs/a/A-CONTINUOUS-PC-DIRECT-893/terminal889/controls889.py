"""889 terminal-only pure controls; no native/socket/board/model/source execution."""
import ast,copy,hashlib,json,sys,textwrap
from pathlib import Path
W=Path('C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发');sys.path.insert(0,str(W))
from competition.deepeye.integration.continuous_native_client import NativeRejected
from competition.deepeye.integration.live_pc_direct import PcDirectClient
D=Path(__file__).parent;O=D.parent
parent=O/'continuous-pc-direct-mode-887/controller887.py';candidate=D/'controller889.py'
a=ast.parse(parent.read_text(encoding='utf8'));b=ast.parse(candidate.read_text(encoding='utf8'))
ns={'NativeRejected':NativeRejected}
names=('stop_native_once','pc_rpc_or_arrived')
exec(compile(ast.Module(body=[x for x in b.body if getattr(x,'name',None) in names],type_ignores=[]),'pure889','exec'),ns)
wrap=ns['pc_rpc_or_arrived']
fixture=json.loads((O/'continuous-pc-direct-host-884/FIXTURE835.public.json').read_bytes())
epoch=fixture['recorded835_source']['world_epoch']
validator=PcDirectClient(None,'x'*64,world_epoch=epoch)
def pc_state(fault=''):
 s=copy.deepcopy(fixture['recorded835_native_snapshot']['native'])
 s.update(ready=not fault,phase='ARRIVED',fault=fault,board_request_seq=0,board_receipt_sha256='',admission_mode='PC_DIRECT',action_source='pc_direct_host',world_epoch=epoch,source_witness='a'*32,board_observation_seq=0,board_observation_sha256='',source_record_sha256='',observation_native_tick_usec='0',pc_command_seq=0,pc_command_sha256='')
 return s
class Native:
 def __init__(self,reason='already_arrived',state=None,confirm=None,error=None):
  self.trace=[];self.calls=0;self.reason=reason;self.payload=pc_state() if state is None else state
  self.confirm=pc_state('operator_stop') if confirm is None else confirm;self.error=error
 def _validate_state(self,state):self.trace.append('validate');validator._validate_state(state)
 def _operation(self):
  self.calls+=1;self.trace.append('operation')
  if self.error:raise self.error
  raise NativeRejected(dict(ok=False,reason=self.reason,state=self.payload))
 def observe_pc(self,*args,**kwargs):return self._operation()
 def apply_advice(self,*args,**kwargs):return self._operation()
 def stop(self):self.trace.append('stop');return dict(ok=True,state=self.confirm,board_stop_acknowledged=False)
 def state(self):self.trace.append('state');return dict(native=self.confirm,host={'fixture_only':True})

def rejects(call,error_type=ValueError):
 try:call()
 except error_type:return
 raise AssertionError('expected original refusal')

# Exact first call, then immediate stop before one real-read seam, then log.
for method in ('observe_pc','apply_advice'):
 native=Native();result={};events=[]
 def log(event,**fields):native.trace.append('log');events.append((event,fields))
 assert wrap(native,result,log,getattr(native,method)) is None
 assert native.trace==['operation','validate','stop','state','validate','log'],native.trace
 assert native.calls==1 and result['arrival'] is True and result['native_stop_attempted'] is True
 assert events[0][0]=='pc-known-terminal-not-admitted' and events[0][1]['no_retry'] is True
 assert result['arrival_native']['native']['phase']=='ARRIVED'

native=Native(reason='not_ready_or_fault');rejects(lambda:wrap(native,{},lambda *a,**k:None,native.observe_pc),NativeRejected)
assert native.trace==['operation']
invalid=pc_state();invalid['obstacle_truth']={};native=Native(state=invalid)
rejects(lambda:wrap(native,{},lambda *a,**k:None,native.apply_advice));assert native.trace==['operation','validate']
native=Native(state=pc_state('operator_stop'))
rejects(lambda:wrap(native,{},lambda *a,**k:None,native.apply_advice));assert 'stop' not in native.trace
native=Native(error=TimeoutError('unknown write'))
rejects(lambda:wrap(native,{},lambda *a,**k:None,native.apply_advice),TimeoutError);assert native.calls==1 and native.trace==['operation']
wrong=pc_state('operator_stop');wrong['phase']='INSIDE';native=Native(confirm=wrong);result={}
rejects(lambda:wrap(native,result,lambda *a,**k:None,native.observe_pc));assert not result.get('arrival') and native.trace==['operation','validate','stop','state','validate']

# Run the actual new sense branch on the actual835 expired recorded source,
# without evaluating a numerical source, board or RPC. Prior full observation
# must survive the discard, rather than become a partial dictionary.
main=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name=='main')
sense=next(x for x in ast.walk(main) if isinstance(x,ast.If) and ast.unparse(x.test)=="kind == 'sense'")
body='\n'.join(ast.unparse(x) for x in sense.body)
code='def discard(observation,actual,meta,now):\n    direct=True;want_stop=False\n    for unused in range(1):\n'+textwrap.indent(body,'        ')+'\n    return observation\n'
source=fixture['recorded835_source'];actual=fixture['recorded835_actual_board']
class Source:
 channel_counts=source['channel_counts'];quality=source['quality']
 def to_payload(self):return copy.deepcopy(source)
ns={'SOURCE_AGE_NS':1500000000,'digest':lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'log':lambda *a,**k:None}
exec(compile(code,'sense-discard889','exec'),ns)
prior={'complete_observation':'preserved'}
assert ns['discard'](prior,actual,{'source':Source(),'source_seq':actual['response']['result']['source_seq']},int(source['at_qpc_ns'])+1500000000) is prior
# Red: execute the exact frozen887 branch with that same expired fixture.
old_main=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=='main')
old_sense=next(x for x in ast.walk(old_main) if isinstance(x,ast.If) and ast.unparse(x.test)=="kind == 'sense'")
old_body='\n'.join(ast.unparse(x) for x in old_sense.body)
old_code='def discard_old(observation,actual,meta,now):\n    direct=True;want_stop=False\n    for unused in range(1):\n'+textwrap.indent(old_body,'        ')+'\n    return observation\n'
exec(compile(old_code,'sense-discard887-red','exec'),ns)
old_result=ns['discard_old'](prior,actual,{'source':Source(),'source_seq':actual['response']['result']['source_seq']},int(source['at_qpc_ns'])+1500000000)
assert old_result is not prior and 'channel_counts' not in old_result
for name in ('RunControl','publish_display','advice_applicable','stop_native_once'):
 assert ast.dump(next(x for x in a.body if getattr(x,'name',None)==name))==ast.dump(next(x for x in b.body if getattr(x,'name',None)==name))
assert candidate.read_text(encoding='utf8').count('pc_rpc_or_arrived(native,result,log,native.observe_pc')==1
assert candidate.read_text(encoding='utf8').count('pc_rpc_or_arrived(native,result,log,native.apply_advice')==1
print(json.dumps(dict(terminal_operations_checked=2,call_stop_confirm_log_order=True,known_rejection_no_resend=True,wrong_reason_invalid_state_unknown_preserved=True,wrong_confirmation_refused=True,actual835_expired_source_old_red_new_green=True,protected_asts_unchanged=True,actual_runtime_effects=False)))
