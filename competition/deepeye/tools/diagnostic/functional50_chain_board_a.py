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
FILES=frozenset((BASE+'functional50_chain_board_a.py',BASE+'functional50_board_a.py',
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
 root=Path(__file__).resolve().parents[4];p=Path(path);need(p.name=='chain-board-manifest.json','manifest filename')
 data,_=read_fixed(p,65536);need(digest(data)==expected,'manifest SHA mismatch');doc=parse(data)
 need(type(doc) is dict and set(doc)=={'schema','files'} and doc['schema']=='chain_board_manifest_v1' and type(doc['files']) is dict and set(doc['files'])==FILES,'exact manifest')
 for name,entry in doc['files'].items():
  need(type(entry) is dict and set(entry)=={'bytes','sha256'} and type(entry['bytes']) is int and 0<entry['bytes']<=2097152 and type(entry['sha256']) is str and re.fullmatch('[0-9a-f]{64}',entry['sha256']),'manifest pin')
  value,_=read_fixed(root/name,2097152);need(len(value)==entry['bytes'] and digest(value)==entry['sha256'],'source pin mismatch')
 need(Path(__file__).resolve()==(root/(BASE+'functional50_chain_board_a.py')).resolve(),'original entry required')
 for part in ('competition','competition/deepeye','competition/deepeye/tools','competition/deepeye/tools/diagnostic'):
  try:(root/part/'__init__.py').lstat()
  except FileNotFoundError:pass
  else:raise ValueError('unexpected executable namespace initializer')
 return root

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
 need(g05.board is board and tx.board is board and tx.g05 is g05,'canonical same-board module required')
 for module in (board,batch,loader,g05,tx):
  need(Path(module.__file__).resolve().is_relative_to(root),'module escaped pinned root')
 return board,batch,loader,g05,tx

def decode_g05(line,g05,operation):
 need(type(line) is bytes and line.endswith(b'\n') and len(line)<=65536 and line.count(b'\n')==1,'bounded G05 line')
 envelope=parse(line);need(type(envelope) is dict and set(envelope)=={'schema','id','operation_id','kind','payload'} and envelope['schema']=='functional50_chain_v1' and envelope['kind']=='g05_transaction' and line==raw(envelope)+b'\n','exact canonical G05 request')
 need(type(envelope['id']) is str and ID.fullmatch(envelope['id']) and envelope['operation_id']==operation,'request identity')
 x=envelope['payload'];need(type(x) is dict and set(x)=={'identity_words','commands','stop','max_polls','duration_ns'},'exact G05 payload')
 need(type(x['identity_words']) is list and type(x['commands']) is list and 1<=len(x['commands'])<=MAX_COMMANDS,'bounded commands')
 identity=g05._identity(tuple(x['identity_words']));last=0;profile=None;commands=[]
 for command in x['commands']:
  need(type(command) is list,'command words');value=g05._command(tuple(command),last,profile);last,profile=value[5],value[2];commands.append(value)
 need(type(x['stop']) is bool and type(x['max_polls']) is int and 1<=x['max_polls']<=MAX_POLLS and type(x['duration_ns']) is int and 0<x['duration_ns']<=MAX_TIME,'explicit bounded choices')
 # Conservative count: factory/identity/setup plus 100 per command, 2 per poll, STOP.
 count=50+100*len(commands)+2*x['max_polls']+3
 # Fixed G05 journal schema and bounded IDs/uint32/64-bit monotonic/pid imply each
 # started/returned ASCII record <=512 bytes; hex preserves original bytes.
 worst=40960+count*(2*1024+128)
 need(worst<=MAX_REPLY,'response evidence budget')
 return envelope,identity,tuple(commands),count,worst

def encode_facts(facts,tx,request_id,worst):
 need(type(facts) is tx.TransactionFacts and facts.schema=='g05_csr_transaction_v1','original transaction facts')
 captures=[dict(status_before_latch=c.status_before_latch,fault_before_latch=c.fault_before_latch,words32=list(c.words32),status_before_snapshot=c.status_before_snapshot,status_after_snapshot=c.status_after_snapshot,result_seq=c.result_seq,tick_unit=c.tick_unit) for c in facts.captures]
 records=[]
 for r in facts.receipts:
  need(type(r) is tx.IOReceipt and len(r.started_raw)<=512 and len(r.returned_raw)<=512,'journal record bound changed')
  records.append(dict(index=r.index,started_raw_hex=r.started_raw.hex(),returned_raw_hex=r.returned_raw.hex()))
 result=dict(schema=facts.schema,operation_id=facts.operation_id,policy_sha256=facts.policy_sha256,identity_words=list(facts.identity_words),captures=captures,deadline_selected_lower_board_monotonic_ns=facts.deadline_selected_lower_board_monotonic_ns,deadline_board_monotonic_ns=facts.deadline_board_monotonic_ns,stop_status=facts.stop_status,stop_fault=facts.stop_fault,receipts=records,authority=facts.authority)
 out=dict(schema='functional50_chain_v1',id=request_id,operation_id=facts.operation_id,kind='g05_transaction',status='COMPLETE',result=result,error=None,unknown=False)
 b=raw(out)+b'\n';need(len(b)<=worst<=MAX_REPLY,'evidence bound violated');return b

def put(path,value):
 with path.open('xb') as f:f.write(value);f.flush();os.fsync(f.fileno())
def trace_status(result):
 need(type(result) is dict and result.get('status') in ('COMPLETE','REFUSED','FAILED','UNKNOWN') and type(result.get('unknown')) is bool,'original batch result')
 return 'REJECTED' if result['status']=='REFUSED' else result['status']
def write_line(value):
 need(type(value) is bytes and len(value)<=MAX_REPLY and value.endswith(b'\n'),'reply bound');sys.stdout.buffer.write(value);sys.stdout.buffer.flush()

def main(argv=None):
 argv=sys.argv[1:] if argv is None else argv
 need(len(argv)==5 and argv[0]=='chain_v1','explicit chain_v1 PLAN MANIFEST MANIFEST_SHA256 G05_POLICY required')
 root=verify_manifest(argv[2],argv[3]); board,batch,loader,g05,tx=load_modules(root)
 # Load pure fixed reducer before any board access. The exact same manifest remains pinned.
 bundle=loader.load_selected(root)
 plan_raw,plan_id=board._bytes(argv[1],131072);plan=board._json(plan_raw)
 policy_raw,policy_id=board._bytes(argv[4],131072)
 keys=('operation_id','request_sha256','boot_id','source_commit','build_id')
 binding={k:plan[k] for k in keys};g05._policy(policy_raw,binding)
 verify_manifest(argv[2],argv[3]);port=board.open_from_plan(argv[1])
 plan_after,plan_after_id=board._bytes(argv[1],131072);policy_after,policy_after_id=board._bytes(argv[4],131072)
 need(plan_raw==plan_after and plan_id==plan_after_id and policy_raw==policy_after and policy_id==policy_after_id,'input changed during load')
 custody=board._G05_LOADS.get(port);need(type(port) is board._TracePort and type(custody) is tuple and len(custody)==9 and dict(custody[3])==binding and port._dir.name==plan['operation_id'] and port._boot==plan['boot_id'],'original same-load custody')
 put(port._dir/'chain-load-plan.json',plan_raw);put(port._dir/'chain-g05-policy.json',policy_raw)
 ready=dict(schema='chain_board_v1',state='ready',operation_id=plan['operation_id'],plan_sha256=digest(plan_raw),load_request_hash=plan['request_sha256'],build_id=plan['build_id'],source_commit=plan['source_commit'],policy_file_sha256=digest(policy_raw),manifest_sha256=argv[3])
 put(port._dir/'chain-ready.json',raw(ready)+b'\n');write_line(raw(ready)+b'\n')
 scanned=False
 for step in range(2):
  line=sys.stdin.buffer.readline(MAX_REQUEST+1)
  if not line:return
  effect_started=False;request_id=None;kind=None
  try:
   obj=parse(line);need(type(obj) is dict and set(obj)=={'schema','id','operation_id','kind','payload'} and obj['schema']=='functional50_chain_v1' and line==raw(obj)+b'\n','exact chain request')
   need(type(obj['id']) is str and ID.fullmatch(obj['id']) and obj['operation_id']==plan['operation_id'],'original request identity');request_id=obj['id'];kind=obj['kind']
   if kind=='trace_scan':
    need(step==0 and not scanned,'one first trace scan only');scanned=True
    data=obj['payload'];need(type(data) is dict and set(data)=={'request_hex','source_hex','companions_hex','build_binding'},'exact trace payload')
    trace_line=raw(dict(schema=batch.SCHEMA,id=request_id,operation_id=plan['operation_id'],**data))+b'\n';batch.decode_batch_request(trace_line)
    effect_started=True
    response=batch.run_batch(port,bundle,trace_line,board,plan);result=parse(response)
    status=trace_status(result)
    write_line(raw(dict(schema='functional50_chain_v1',id=request_id,operation_id=plan['operation_id'],kind=kind,status=status,result=result,error=result.get('error_type'),unknown=result['unknown']))+b'\n')
    if result.get('status')!='COMPLETE' or result.get('unknown'):return
   elif kind=='g05_transaction':
    envelope,identity,commands,count,worst=decode_g05(line,g05,plan['operation_id']);x=envelope['payload']
    need(os.getpid()<=0xffffffff and 0<=time.monotonic_ns()<=MAX_U63-MAX_TIME,'bounded journal scalar values')
    again,again_id=board._bytes(argv[4],131072);need(again==policy_raw and again_id==policy_id,'policy changed before G05')
    # Exact prospective bound for all factory + issuer records precedes mapping/effect.
    policy=g05._policy(policy_raw,binding);limits=policy['limits'];n=len(commands)
    need(limits['total_io']>=count and limits['begin']>=1 and all(limits[k]>=n for k in ('commit','latch','release')) and (not x['stop'] or limits['stop']>=1),'policy cannot cover selected worst-case')
    put(port._dir/'chain-g05-request.json',line)
    effect_started=True
    gport=g05.open_g05(port,argv[4]);issuer=tx.TransactionIssuer(port,gport,tx.Limits(n,x['max_polls'],x['duration_ns']))
    facts=issuer.run(identity,commands,stop=x['stop']);need(len(facts.receipts)<=count,'receipt count bound violated')
    response=encode_facts(facts,tx,request_id,worst);put(port._dir/'chain-g05-response.json',response);write_line(response);return
   else:raise ValueError('unsupported request')
  except BaseException as e:
   # Once any selected operation fails, retain original local files and never retry or stop.
   write_line(raw(dict(schema='functional50_chain_v1',id=request_id,operation_id=plan['operation_id'],kind=kind,status='UNKNOWN' if effect_started else 'REJECTED',result=None,error=type(e).__name__,unknown=effect_started))+b'\n');return

if __name__=='__main__':main()
