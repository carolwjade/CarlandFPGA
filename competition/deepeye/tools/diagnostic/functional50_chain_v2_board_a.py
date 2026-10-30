"""Explicit same-load TRACE/G05 chain entry; import never accesses a board."""
import hashlib
import importlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import types

BASE='competition/deepeye/tools/diagnostic/'
FILES=frozenset((BASE+'functional50_chain_v2_board_a.py',BASE+'functional50_board_a.py',
 BASE+'functional50_g05_session_a.py',BASE+'functional50_trace_cycles_a.py',
 BASE+'functional50_board_trace_batch_a.py',BASE+'functional50_b131_loader.py',
 BASE+'functional50_g05_a.py',BASE+'functional50_g05_transaction_a.py',
 BASE+'functional50_adapter128/dependencies128.py',BASE+'functional50_adapter128/adapter128.py',
 BASE+'functional50_adapter128/reducer128.py',BASE+'functional50_input113/input113.py',
 'competition/deepeye/golden/codec/trace_candidate.py'))
MAX_REPLY=1048576
MAX_REQUEST=4210688
MAX_POLLS=64
MAX_COMMANDS=2
MAX_TIME=10000000000
MAX_U63=(1<<63)-1
ID=re.compile(r'[A-Za-z0-9_-]{1,64}\Z')

def need(value,message):
 if not value:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(value):return hashlib.sha256(value).hexdigest()
def parse(value):
 def pairs(items):
  out={}
  for k,v in items:need(k not in out,'duplicate key');out[k]=v
  return out
 return json.loads(value,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))
def read_fixed(path,cap):
 p=Path(path);need(p.is_absolute() and not p.is_symlink() and p.is_file(),'ordinary absolute file required')
 for parent in p.parents:need(not parent.is_symlink(),'symlink parent refused')
 with p.open('rb') as f:
  a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and 0<a.st_size<=cap,'file bounds')
  b=f.read(cap+1);z=os.fstat(f.fileno())
 need(len(b)==a.st_size and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),'file changed')
 return b,(a.st_dev,a.st_ino)
def verify_manifest(path,expected):
 need(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected) is not None,'manifest SHA required')
 root=Path(__file__).resolve().parents[4];p=Path(path);need(p.name=='chain-v2-board-manifest.json','manifest filename')
 data,_=read_fixed(p,65536);need(digest(data)==expected,'manifest SHA mismatch');doc=parse(data)
 need(type(doc) is dict and set(doc)=={'schema','files'} and doc['schema']=='chain_board_manifest_v2' and type(doc['files']) is dict and set(doc['files'])==FILES,'exact manifest')
 for name,entry in doc['files'].items():
  need(type(entry) is dict and set(entry)=={'bytes','sha256'} and type(entry['bytes']) is int and 0<entry['bytes']<=2097152 and type(entry['sha256']) is str and re.fullmatch('[0-9a-f]{64}',entry['sha256']),'manifest pin')
  value,_=read_fixed(root/name,2097152);need(len(value)==entry['bytes'] and digest(value)==entry['sha256'],'source pin mismatch')
 need(Path(__file__).resolve()==(root/(BASE+'functional50_chain_v2_board_a.py')).resolve(),'original entry required')
 for part in ('competition','competition/deepeye','competition/deepeye/tools','competition/deepeye/tools/diagnostic'):
  try:(root/part/'__init__.py').lstat()
  except FileNotFoundError:pass
  else:raise ValueError('unexpected executable namespace initializer')
 return root

def make_manifest_bytes(snapshot_root):
 root=Path(snapshot_root);need(root.is_absolute() and root.is_dir() and not root.is_symlink(),'absolute snapshot required')
 files={}
 for name in sorted(FILES):
  data,_=read_fixed(root/name,2097152);files[name]=dict(bytes=len(data),sha256=digest(data))
 return raw(dict(schema='chain_board_manifest_v2',files=files))

def load_modules(root):
 need(not any(x=='competition' or x.startswith('competition.') for x in sys.modules),'fresh canonical package required')
 for name,part in (('competition','competition'),('competition.deepeye','competition/deepeye'),
                   ('competition.deepeye.tools','competition/deepeye/tools'),
                   ('competition.deepeye.tools.diagnostic','competition/deepeye/tools/diagnostic')):
  package=types.ModuleType(name);package.__package__=name;package.__path__=[str(root/part)]
  package.__spec__=importlib.machinery.ModuleSpec(name,None,is_package=True)
  package.__spec__.submodule_search_locations=package.__path__;sys.modules[name]=package
 prefix='competition.deepeye.tools.diagnostic.'
 board=importlib.import_module(prefix+'functional50_board_a')
 batch=importlib.import_module(prefix+'functional50_board_trace_batch_a')
 loader=importlib.import_module(prefix+'functional50_b131_loader')
 g05=importlib.import_module(prefix+'functional50_g05_a')
 tx=importlib.import_module(prefix+'functional50_g05_transaction_a')
 session=importlib.import_module(prefix+'functional50_g05_session_a')
 cycles=importlib.import_module(prefix+'functional50_trace_cycles_a')
 need(g05.board is board and tx.board is board and tx.g05 is g05,'canonical same-board module required')
 need(session.board is board and session.transaction is tx and cycles.board is board and cycles.loader is loader,'canonical v2 module required')
 for module in (board,batch,loader,g05,tx,session,cycles):
  need(Path(module.__file__).resolve().is_relative_to(root),'module escaped pinned root')
 return board,batch,loader,g05,tx,session,cycles

SCHEMA='functional50_chain_v2'
class Sequence:
 def __init__(self):self.initialized=False;self.closed=False;self.counts={'trace_scan':0,'apply':0,'status':0};self.ids=set();self.max_commands=0;self.last=0;self.profile=None
 def consume(self,x):
  kind=x['kind'];self.ids.add(x['id'])
  if kind=='init':self.initialized=True;self.max_commands=x['payload']['max_commands']
  elif kind=='close':self.closed=True
  else:
   self.counts[kind]+=1
   if kind=='apply':self.last=x['payload']['command_words'][5];self.profile=x['payload']['command_words'][2]

def decode_request(line,operation,g05,state):
 need(type(line) is bytes and 0<len(line)<=MAX_REQUEST and line.endswith(b'\n') and line.count(b'\n')==1,'bounded request')
 x=parse(line);need(type(x) is dict and set(x)=={'schema','id','operation_id','kind','payload'} and x['schema']==SCHEMA and line==raw(x)+b'\n','canonical envelope')
 need(type(x['id']) is str and ID.fullmatch(x['id']) and x['id'] not in state.ids and x['operation_id']==operation and not state.closed,'one use request identity')
 k=x['kind'];p=x['payload'];need(type(p) is dict,'payload object')
 if k=='init':
  need(not state.initialized and set(p)=={'identity_words','max_commands','max_polls','duration_ns','max_io'},'one init payload')
  need(type(p['identity_words']) is list,'identity words');g05._identity(tuple(p['identity_words']))
  need(type(p['max_commands']) is int and 1<=p['max_commands']<=2 and type(p['max_polls']) is int and 4<=p['max_polls']<=64 and type(p['duration_ns']) is int and 0<p['duration_ns']<=MAX_TIME and type(p['max_io']) is int and 1<=p['max_io']<=450,'explicit session caps')
 else:
  need(state.initialized,'init required')
  if k=='trace_scan':
   need(state.counts[k]<2 and set(p)=={'request_hex','source_hex','companions_hex','build_binding','max_io'} and type(p['max_io']) is int and 1<=p['max_io']<=2000,'trace cap/payload')
  elif k=='apply':
   need(state.counts[k]<state.max_commands and set(p)=={'command_words'} and type(p['command_words']) is list,'apply cap/payload');g05._command(tuple(p['command_words']),state.last,state.profile)
  elif k=='status':need(state.counts[k]<4 and not p,'status cap/payload')
  elif k=='close':need(set(p)=={'stop'} and type(p['stop']) is bool,'explicit close')
  else:raise ValueError('unknown kind')
 return x

def put(path,value):
 with path.open('xb') as f:f.write(value);f.flush();os.fsync(f.fileno())
def write_line(value):
 need(type(value) is bytes and len(value)<=MAX_REPLY and value.endswith(b'\n'),'reply bound');sys.stdout.buffer.write(value);sys.stdout.buffer.flush()
def facts_json(facts,session,tx):
 need(type(facts) is session.SessionFacts and facts.schema=='g05_csr_session_v2' and facts.authority=='not_evaluated','original facts required')
 cap=facts.capture
 capture=None if cap is None else dict(status_before_latch=cap.status_before_latch,fault_before_latch=cap.fault_before_latch,words32=list(cap.words32),status_before_snapshot=cap.status_before_snapshot,status_after_snapshot=cap.status_after_snapshot,result_seq=cap.result_seq,tick_unit=cap.tick_unit)
 receipts=[]
 for r in facts.receipts:
  need(type(r) is tx.IOReceipt and len(r.started_raw)<=512 and len(r.returned_raw)<=512,'bounded original receipts')
  receipts.append(dict(index=r.index,started_raw_hex=r.started_raw.hex(),returned_raw_hex=r.returned_raw.hex()))
 unresolved=[];indices=[r['index'] for r in receipts]
 for r in facts.unresolved_receipts:
  need(type(r) is session.UnresolvedIO,'original unresolved record')
  values=(r.started_raw,r.returned_raw,r.not_attempted_raw)
  need(sum(v is not None for v in values)<=2 and all(v is None or (type(v) is bytes and 0<len(v)<=512) for v in values),'bounded partial originals')
  indices.append(r.index);unresolved.append(dict(index=r.index,started_raw_hex=None if values[0] is None else values[0].hex(),returned_raw_hex=None if values[1] is None else values[1].hex(),not_attempted_raw_hex=None if values[2] is None else values[2].hex()))
 need(len(indices)<=450 and len(set(indices))==len(indices) and all(type(i) is int and 1<=i<=450 for i in indices),'distinct bounded receipt indices')
 need(facts.state=='CLOSED_AFTER_FAILURE' or not unresolved,'complete facts have no unresolved I/O')
 return dict(schema=facts.schema,kind=facts.kind,operation_id=facts.operation_id,policy_sha256=facts.policy_sha256,deadline_selected_lower_board_monotonic_ns=facts.deadline_selected_lower_board_monotonic_ns,deadline_board_monotonic_ns=facts.deadline_board_monotonic_ns,phase_io_first=facts.phase_io_first,phase_io_last=facts.phase_io_last,identity_words=None if facts.identity_words is None else list(facts.identity_words),status=facts.status,fault=facts.fault,capture=capture,receipts=receipts,unresolved_receipts=unresolved,state=facts.state,authority=facts.authority)

def main(argv=None):
 argv=sys.argv[1:] if argv is None else argv
 need(len(argv)==5 and argv[0]=='chain_v2','explicit chain_v2 PLAN MANIFEST SHA G05_POLICY required')
 root=verify_manifest(argv[2],argv[3]);board,batch,loader,g05,tx,session,cycles=load_modules(root);bundle=loader.load_selected(root)
 plan_raw,plan_id=board._bytes(argv[1],131072);plan=board._json(plan_raw);policy_raw,policy_id=board._bytes(argv[4],131072)
 binding={k:plan[k] for k in ('operation_id','request_sha256','boot_id','source_commit','build_id')};policy=g05._policy(policy_raw,binding)
 verify_manifest(argv[2],argv[3]);port=board.open_from_plan(argv[1],trace_cycle_v2=board.select_trace_cycle_v2())
 plan_after,plan_after_id=board._bytes(argv[1],131072);policy_after,policy_after_id=board._bytes(argv[4],131072)
 need(plan_raw==plan_after and plan_id==plan_after_id and policy_raw==policy_after and policy_id==policy_after_id,'input changed during load')
 custody=board._G05_LOADS.get(port);need(type(port) is board._TracePort and type(custody) is tuple and len(custody)==9 and dict(custody[3])==binding and port._dir.name==plan['operation_id'] and port._boot==plan['boot_id'] and len(str(port._dir))<=900,'original same-load custody and bounded evidence path')
 put(port._dir/'chain-v2-load-plan.json',plan_raw);put(port._dir/'chain-v2-g05-policy.json',policy_raw)
 ready=dict(schema='chain_board_v2',state='ready',operation_id=plan['operation_id'],plan_sha256=digest(plan_raw),load_request_hash=plan['request_sha256'],build_id=plan['build_id'],source_commit=plan['source_commit'],policy_file_sha256=digest(policy_raw),manifest_sha256=argv[3]);put(port._dir/'chain-v2-ready.json',raw(ready)+b'\n');write_line(raw(ready)+b'\n')
 sequence=Sequence();owner=cycles.TraceCycles(port,bundle);gs=None
 for step in range(10):
  line=sys.stdin.buffer.readline(MAX_REQUEST+1)
  if not line:return
  started=False;request_id=kind=None
  try:
   x=decode_request(line,plan['operation_id'],g05,sequence);request_id=x['id'];kind=x['kind'];p=x['payload']
   if kind=='init':
    # Factory 4 + init 35, each command <=76 plus two I/Os per
    # selected status poll, four fresh statuses <=60, optional STOP <=3.
    prospective_io=102+76*p['max_commands']+2*p['max_polls']
    need(prospective_io<=policy['limits']['total_io']<=p['max_io'],'G05 policy cannot cover selected session or exceeds budget')
    need(policy['limits']['begin']>=1 and all(policy['limits'][k]>=p['max_commands'] for k in ('commit','latch','release')),'G05 selected command quotas')
    need(os.getpid()<=0xffffffff and 0<=time.monotonic_ns()<=MAX_U63-MAX_TIME and 40960+p['max_io']*2176<=MAX_REPLY,'prospective complete receipt budget')
    again,again_id=board._bytes(argv[4],131072);need(again==policy_raw and again_id==policy_id,'policy changed')
    sequence.consume(x);started=True
    gp=g05.open_g05(port,argv[4]);issuer=tx.TransactionIssuer(port,gp,tx.Limits(p['max_commands'],p['max_polls'],p['duration_ns']));gs=session.G05SessionV2(issuer)
    facts=gs.init(tuple(p['identity_words']));owner.bind_deadline(issuer._deadline);result=facts_json(facts,session,tx)
   elif kind=='trace_scan':
    data={k:p[k] for k in ('request_hex','source_hex','companions_hex','build_binding')}
    trace_line=raw(dict(schema=batch.SCHEMA,id=request_id,operation_id=plan['operation_id'],**data))+b'\n';batch.decode_batch_request(trace_line)
    sequence.consume(x);started=True;before=port._count;record=owner.scan(trace_line,max_io=p['max_io']);after=port._count
    need(type(before) is int and type(after) is int and 0<=before<after<=5000 and after-before<=p['max_io'],'original TRACE phase boundaries')
    result=dict(schema='trace_cycle_v2',index=record['index'],request_sha256=record['request_sha256'],source_sha256=record['source_sha256'],response=batch._json(record['response']),phase_io_first=before+1,phase_io_last=after,correlation_status=record['correlation']['status'],directory=str(record['directory']),evidence_manifest_sha256=record['evidence_manifest_sha256'],authority='not_evaluated')
   else:
    need(gs is not None and time.monotonic_ns()<gs.issuer._deadline,'session deadline')
    sequence.consume(x);started=True
    if kind=='apply':facts=gs.apply_one(tuple(p['command_words']))
    elif kind=='status':facts=gs.observe_status()
    else:facts=gs.close(stop=p['stop'])
    result=facts_json(facts,session,tx)
   response=raw(dict(schema=SCHEMA,id=request_id,operation_id=plan['operation_id'],kind=kind,status='COMPLETE',result=result,error=None,unknown=False))+b'\n';need(len(response)<=MAX_REPLY,'bounded response violated');put(port._dir/('chain-v2-%02d-response.json'%(step+1)),response);write_line(response)
   if kind=='close':return
  except BaseException as e:
   partial=None
   if started and kind in ('init','apply','status','close') and gs is not None and gs._state=='FAILED':
    try:
     captured=gs.close(stop=False);need(captured.state=='CLOSED_AFTER_FAILURE','failed evidence state');partial=facts_json(captured,session,tx)
    except BaseException:partial=None
   failure=raw(dict(schema=SCHEMA,id=request_id,operation_id=plan['operation_id'],kind=kind,status='UNKNOWN' if started else 'REJECTED',result=partial,error=type(e).__name__,unknown=started))+b'\n'
   if len(failure)>MAX_REPLY:failure=raw(dict(schema=SCHEMA,id=request_id,operation_id=plan['operation_id'],kind=kind,status='UNKNOWN' if started else 'REJECTED',result=None,error=type(e).__name__,unknown=started))+b'\n'
   write_line(failure);return

if __name__=='__main__':main()
