"""Standalone, explicit TRACE batch board entry. No imports cause board effects."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

SCHEMA='trace_batch_v1'
MANIFEST='trace_batch_manifest_v1'
MAX_RAW=2*1024*1024
MAX_LINE=2*MAX_RAW+16384
MAX_REPLY=4096
BASE='competition/deepeye/tools/diagnostic/'
FILES=frozenset((BASE+'functional50_board_trace_batch_a.py',BASE+'functional50_board_a.py',
 BASE+'functional50_b131_loader.py',BASE+'functional50_adapter128/dependencies128.py',
 BASE+'functional50_adapter128/adapter128.py',BASE+'functional50_adapter128/reducer128.py',
 BASE+'functional50_input113/input113.py','competition/deepeye/golden/codec/trace_candidate.py'))
ID=re.compile(r'[A-Za-z0-9_-]{1,64}\Z')

def need(value,message):
 if not value:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(data):return hashlib.sha256(data).hexdigest()
def _json(data):
 def pairs(items):
  out={}
  for k,v in items:need(k not in out,'duplicate key');out[k]=v
  return out
 return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))
def _hex(value,cap):
 need(type(value) is str and len(value)%2==0 and len(value)<=cap*2 and re.fullmatch('[0-9a-f]*',value) is not None,'bounded lowercase hex required')
 data=bytes.fromhex(value);need(data,'nonempty original bytes required');return data

def decode_batch_request(line):
 need(type(line) is bytes and 0<len(line)<=MAX_LINE and line.endswith(b'\n') and line.count(b'\n')==1,'bounded single batch line required')
 x=_json(line);need(type(x) is dict and set(x)=={'schema','id','operation_id','request_hex','source_hex','companions_hex','build_binding'} and x['schema']==SCHEMA,'exact batch request required')
 need(line==raw(x)+b'\n','canonical batch envelope required')
 need(type(x['id']) is str and ID.fullmatch(x['id']) is not None and type(x['operation_id']) is str and ID.fullmatch(x['operation_id']) is not None,'strict batch identity required')
 need(type(x['companions_hex']) is list and len(x['companions_hex'])==4,'four original companions required')
 request=_hex(x['request_hex'],262144);source=_hex(x['source_hex'],1048576);companions=tuple(_hex(v,262144) for v in x['companions_hex'])
 need(len(request)+len(source)+sum(map(len,companions))<=MAX_RAW,'total original bytes exceed bound')
 b=x['build_binding'];need(type(b) is dict and set(b)=={'canonical_build_id_full_sha256','source_closure_file_sha256','operation_id','request_hash'} and all(type(v) is str and len(v)<=192 for v in b.values()),'exact build binding required')
 return request,source,companions,x

def verify_manifest_structure(doc):
 need(type(doc) is dict and set(doc)=={'schema','files'} and doc['schema']==MANIFEST and type(doc['files']) is dict and set(doc['files'])==FILES,'exact manifest file set required')
 for item in doc['files'].values():
  need(type(item) is dict and set(item)=={'sha256','bytes'} and type(item['bytes']) is int and 0<item['bytes']<=2*1024*1024 and type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['sha256']) is not None,'manifest file pin invalid')
 return doc

def _read_fixed(path,cap):
 need(path.is_absolute() and not path.is_symlink() and path.is_file(),'ordinary fixed input required')
 for parent in path.parents:need(not parent.is_symlink(),'symlink path refused')
 with path.open('rb') as f:
  before=os.fstat(f.fileno());need(before.st_nlink==1 and 0<before.st_size<=cap,'file size/link refused');data=f.read(cap+1);after=os.fstat(f.fileno())
 need(len(data)==before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'file changed while reading')
 return data

def make_manifest_bytes(snapshot_root):
 """Create the exact upload candidate; Root verifies the remote bytes separately."""
 root=Path(snapshot_root)
 need(root.is_absolute() and root.is_dir() and not root.is_symlink(),'absolute source snapshot required')
 files={}
 for name in sorted(FILES):
  data=_read_fixed(root/name,2*1024*1024)
  files[name]=dict(sha256=digest(data),bytes=len(data))
 return raw(dict(schema=MANIFEST,files=files))

def _load(root,relative,name):
 path=root/relative;spec=importlib.util.spec_from_file_location(name,path);need(spec is not None and spec.loader is not None,'fixed loader unavailable')
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def _verify_manifest(path,expected):
 need(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected) is not None,'manifest pin required')
 root=Path(__file__).resolve().parents[4];path=Path(path);need(path.name=='trace-batch-manifest.json','fixed manifest filename required')
 data=_read_fixed(path,65536);need(digest(data)==expected,'manifest hash mismatch');doc=verify_manifest_structure(_json(data))
 for name,pin in doc['files'].items():
  b=_read_fixed(root/name,2*1024*1024);need(len(b)==pin['bytes'] and digest(b)==pin['sha256'],'manifest source mismatch')
 need(Path(__file__).resolve()==(root/(BASE+'functional50_board_trace_batch_a.py')).resolve(),'fixed entry path required')
 return root

def _put(path,data):
 with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def _record(path,obj):_put(path,raw(obj)+b'\n')
def _outcome(intent,status,value):
 return dict(operation_id=intent['operation_id'],call_id=intent['call_id'],status=status,value=value,error_code=None)

def _drive(port,reducer,phase,origin,directory,used):
 intent=reducer.advance(phase_elapsed_ns=time.monotonic_ns()-origin)
 while intent is not None:
  try:
   keys={'operation_id','call_id','kind','offset','value','label','poll','window','phase','reserve_and_persist_before_effect_bytes','phase_deadline_ns'}
   need(type(intent) is dict and set(intent)==keys and intent['operation_id']==reducer.operation_id and intent['phase']==phase and intent['window']=='TRACE_HWH_RELATIVE' and intent['reserve_and_persist_before_effect_bytes']==2048,'fixed reducer intent required')
   n=intent['call_id'];need(type(n) is int and n>0,'fixed call ID required')
   reservation=directory/('intent-%05d.bin'%n);b=raw(intent);need(len(b)<=1023 and used[phase]+2048+12288<=reducer.limits[phase+'_evidence'],'intent reservation bound')
   _put(reservation,b+b'\n'+b'\0'*(2047-len(b)));used[phase]+=2048
  except BaseException:
   try:reducer.advance(_outcome(intent,'not_attempted',None),phase_elapsed_ns=time.monotonic_ns()-origin)
   except BaseException:pass
   raise
  # A durable intent is not permission to execute after its phase deadline.
  elapsed=time.monotonic_ns()-origin
  if elapsed>=intent['phase_deadline_ns']:
   observation=_outcome(intent,'not_attempted',None)
   with reservation.open('r+b') as f:f.seek(1024);f.write(raw(dict(observation=observation))+b'\n');f.flush();os.fsync(f.fileno())
   reducer.advance(observation,phase_elapsed_ns=elapsed)
   return
  before=port._count
  try:
   value=port._call(intent['kind'],intent['offset'],intent['value'],'batch-%05d'%n)
   observation=_outcome(intent,'confirmed_read' if intent['kind']=='read' else 'confirmed_write',value)
  except BaseException as error:
   observation=_outcome(intent,'unknown',None)
   with reservation.open('r+b') as f:f.seek(1024);f.write(raw(dict(observation=observation,error=type(error).__name__))+b'\n');f.flush();os.fsync(f.fileno())
   try:reducer.advance(observation,phase_elapsed_ns=time.monotonic_ns()-origin)
   except BaseException:pass
   raise
  with reservation.open('r+b') as f:f.seek(1024);f.write(raw(dict(observation=observation))+b'\n');f.flush();os.fsync(f.fileno())
  need(port._count==before+1,'original port count changed')
  for suffix in ('started','returned'):
   used[phase]+=(port._dir/('io-%05d-%s.json'%(port._count,suffix))).stat().st_size
  need(used[phase]<=reducer.limits[phase+'_evidence'],'actual evidence budget exhausted')
  intent=reducer.advance(observation,phase_elapsed_ns=time.monotonic_ns()-origin)

def run_batch(port,bundle,line,board,plan):
 need(type(port) is board._TracePort,'exact original board port required')
 start_count=port._count
 request,source,companions,outer=decode_batch_request(line)
 directory=port._dir/'trace-batch';directory.mkdir(mode=0o700)
 _record(directory/'batch-started.json',dict(id=outer['id'],operation_id=outer['operation_id'],request_sha256=digest(request),envelope_sha256=digest(line),build_binding=outer['build_binding'],monotonic_ns=time.monotonic_ns()))
 for name,data in [('request.bin',request),('source.bin',source),*[(f'companion-{i}.bin',b) for i,b in enumerate(companions)]]:_put(directory/name,data)
 prepared=bundle.adapter.prepare_bytes(request,source,companions,build_binding=outer['build_binding'])
 result=dict(schema=SCHEMA,id=outer['id'],operation_id=outer['operation_id'],request_sha256=digest(request),lineage_request_hash=outer['build_binding']['request_hash'],status='REFUSED',raw_wire_hex=None,wire_complete=False,results=[],io_count=port._count,batch_io_count=0,cleanup_observed=False,terminal='NOT_STARTED',unknown=False)
 reducer=None
 try:
  need(prepared.status=='TRACE94_PLAN_PREPARED' and prepared.plan is not None,'original normalizer refused')
  facts=prepared.plan.facts();need(facts['lineage']['operation_id']==outer['operation_id']==plan['operation_id'],'operation mismatch')
  need(facts['lineage']['build_id_hex128']==plan['build_id'],'original build mismatch')
  reducer=bundle.reducer.Reducer(prepared.plan);used={'work':len(request)+len(source)+sum(map(len,companions))+4096,'cleanup':0}
  work=time.monotonic_ns();reducer.begin();_drive(port,reducer,'work',work,directory,used)
  snap=reducer.snapshot()
  if snap['completed'] and not snap['failed'] and snap['outstanding_intent'] is None:
   reducer.begin_collect();_drive(port,reducer,'work',work,directory,used)
  snap=reducer.snapshot()
  if snap['arm_attempt_owned'] and not snap['unknown_effects'] and not port._failed and snap['outstanding_intent'] is None:
   cleanup=time.monotonic_ns();prior_errors=len(snap['errors']);reducer.begin_cleanup();_drive(port,reducer,'cleanup',cleanup,directory,used)
   cleaned=reducer.snapshot()
   result['cleanup_observed']=bool(cleaned['cancel_consumed'] and cleaned['quiescent'] and not cleaned['unknown_effects'] and cleaned['outstanding_intent'] is None and len(cleaned['errors'])==prior_errors and reducer.generator is None)
  snap=reducer.snapshot()
  if (not snap['collect_consumed'] and result['cleanup_observed'] and not snap['unknown_effects'] and not port._failed and snap['outstanding_intent'] is None):
   reducer.begin_collect();_drive(port,reducer,'cleanup',cleanup,directory,used)
  snap=reducer.snapshot();wire=snap['confirmed_wire_prefix'];_put(directory/'wire.bin',wire)
  complete=bool(snap['completed'] and snap['collect_consumed'] and result['cleanup_observed'] and not snap['failed'] and not snap['unknown_effects'])
  result.update(status=('UNKNOWN' if snap['unknown_effects'] else 'COMPLETE' if complete else 'FAILED'),
   raw_wire_hex=wire.hex() if len(wire)<=252 else None,wire_complete=complete and len(wire)<=252,
   results=snap['results'],io_count=port._count,terminal=('UNKNOWN' if snap['unknown_effects'] else 'QUIESCENT' if result['cleanup_observed'] else 'NOT_PROVEN'),unknown=snap['unknown_effects'])
  _record(directory/'reducer-terminal.json',{k:(v.hex() if k=='confirmed_wire_prefix' else v) for k,v in snap.items() if k not in ('original','events')})
 except BaseException as error:
  if reducer is not None:
   snap=reducer.snapshot();wire=snap['confirmed_wire_prefix'];_put(directory/'failure-wire.bin',wire)
   unknown=bool(snap['unknown_effects'] or port._failed or snap['outstanding_intent'] is not None)
   result.update(status='UNKNOWN' if unknown else 'FAILED',unknown=unknown,io_count=port._count,results=snap['results'],raw_wire_hex=wire.hex() if len(wire)<=252 else None,wire_complete=False)
  result['terminal']='UNKNOWN' if result['unknown'] else 'NOT_PROVEN'
  result['error_type']=type(error).__name__
 result['batch_io_count']=port._count-start_count
 encoded=raw(result)+b'\n';need(len(encoded)<=MAX_REPLY,'response exceeds bound; original evidence retained')
 _record(directory/'batch-returned.json',dict(result=result,monotonic_ns=time.monotonic_ns()))
 return encoded

def main():
 need(len(sys.argv)==4,'usage: batch_entry PLAN MANIFEST MANIFEST_SHA256')
 root=_verify_manifest(sys.argv[2],sys.argv[3])
 loader=_load(root,BASE+'functional50_b131_loader.py','_trace_batch_loader')
 bundle=loader.load_selected(root)
 board=_load(root,BASE+'functional50_board_a.py','_trace_batch_board')
 plan_bytes,plan_file_id=board._bytes(sys.argv[1],131072);plan=board._json(plan_bytes)
 port=board.open_from_plan(sys.argv[1])
 after_bytes,after_file_id=board._bytes(sys.argv[1],131072)
 need(after_bytes==plan_bytes and after_file_id==plan_file_id,'original plan changed during load')
 custody=board._G05_LOADS.get(port)
 binding=tuple((key,plan[key]) for key in ('operation_id','request_sha256','boot_id','source_commit','build_id'))
 need(type(custody) is tuple and len(custody)==9 and custody[3]==binding
      and port._boot==plan['boot_id'] and port._dir.name==plan['operation_id'],
      'loaded port does not retain original plan binding')
 print(json.dumps({'state':'ready','pid':os.getpid()}),flush=True)
 line=sys.stdin.buffer.readline(MAX_LINE+1);response=run_batch(port,bundle,line,board,plan)
 sys.stdout.buffer.write(response);sys.stdout.buffer.flush()
if __name__=='__main__':main()
