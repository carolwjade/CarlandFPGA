"""Bounded one-process chain host. Observations are not authority or acceptance."""
import hashlib
import json
import re
import threading
from . import functional50_b131_loader as loader
from . import functional50_board_trace_batch_a as batch
from . import functional50_trace_batch_client_a as trace
from . import functional50_g05_a as g05
from .functional50_ssh_a import Session, _record, _ID
from ...integration.host_clock import QpcHostClock

SCHEMA='functional50_chain_v1'
MAX_REPLY=1048576
def need(ok,msg):
 if not ok:raise ValueError(msg)
def raw(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(data):return hashlib.sha256(data).hexdigest()

def _decode(data,request_id,operation,kind):
 need(type(data) is bytes and 0<len(data)<=MAX_REPLY and data.endswith(b'\n') and data.count(b'\n')==1,'bounded chain response required')
 doc=batch._json(data)
 need(type(doc) is dict and set(doc)=={'schema','id','operation_id','kind','status','result','error','unknown'} and doc['schema']==SCHEMA and doc['id']==request_id and doc['operation_id']==operation and doc['kind']==kind,'chain response identity')
 need(doc['status'] in ('COMPLETE','REJECTED','FAILED','UNKNOWN') and type(doc['unknown']) is bool and doc['unknown']==(doc['status']=='UNKNOWN'),'chain status')
 if doc['status']=='COMPLETE':need(doc['error'] is None and type(doc['result']) is dict,'complete result required')
 elif kind=='trace_scan' and type(doc['result']) is dict:
  need(doc['error'] is None or (type(doc['error']) is str and 0<len(doc['error'])<=96),'bounded trace failure')
 else:need(doc['result'] is None and type(doc['error']) is str and 0<len(doc['error'])<=96,'bounded failure required')
 return doc

def _facts(x,operation,identity,commands,stop):
 keys={'schema','operation_id','policy_sha256','identity_words','captures','deadline_selected_lower_board_monotonic_ns','deadline_board_monotonic_ns','stop_status','stop_fault','receipts','authority'}
 need(type(x) is dict and set(x)==keys and x['schema']=='g05_csr_transaction_v1' and x['operation_id']==operation and x['authority']=='not_evaluated','transaction facts identity')
 need(type(x['policy_sha256']) is str and re.fullmatch('[0-9a-f]{64}',x['policy_sha256']) is not None and x['identity_words']==list(identity),'actual identity/policy')
 need(type(x['captures']) is list and len(x['captures'])==len(commands),'capture count')
 for cap,cmd in zip(x['captures'],commands):
  need(type(cap) is dict and set(cap)=={'status_before_latch','fault_before_latch','words32','status_before_snapshot','status_after_snapshot','result_seq','tick_unit'} and cap['tick_unit']=='50MHz_cycles','capture shape')
  words=cap['words32'];need(type(words) is list and len(words)==32 and all(type(v) is int and 0<=v<=0xffffffff for v in words) and words[1]==cmd[5] and words[2]==cmd[6],'actual capture words')
  need(all(type(cap[k]) is int and 0<=cap[k]<=0xffffffff for k in ('status_before_latch','fault_before_latch','status_before_snapshot','status_after_snapshot','result_seq')),'capture fields')
 a=x['deadline_selected_lower_board_monotonic_ns'];b=x['deadline_board_monotonic_ns'];need(type(a) is int and type(b) is int and 0<=a<b and b-a<=10_000_000_000,'board deadline')
 for k in ('stop_status','stop_fault'):need((type(x[k]) is int and 0<=x[k]<=0xffffffff) if stop else x[k] is None,'stop observation')
 need(type(x['receipts']) is list and len(x['receipts'])>0,'raw receipts required')
 for i,r in enumerate(x['receipts'],1):
  need(type(r) is dict and set(r)=={'index','started_raw_hex','returned_raw_hex'} and r['index']==i,'receipt identity')
  for k in ('started_raw_hex','returned_raw_hex'):
   v=r[k];need(type(v) is str and 0<len(v)<=8192 and len(v)%2==0 and re.fullmatch('[0-9a-f]+',v) is not None,'original receipt bytes')
 return x

class ChainSession:
 def __init__(self,session,bundle,clock):
  need(type(session) is Session and session._protocol==SCHEMA and type(bundle) is loader._Bundle and type(clock) is QpcHostClock and session._clock is clock,'original session/bundle/QPC required')
  session._check();need(not getattr(session,'_chain_claimed',False),'original chain already claimed')
  session._chain_claimed=True;self._session=session;self._bundle=bundle;self._clock=clock;self._thread=threading.get_ident();self._ids=set();self._trace=False;self._g05=False
  self._folder=session._dir/'chain-host';self._folder.mkdir(mode=0o700)
 def _send(self,request_id,kind,payload,timeout_ns):
  s=self._session;need(threading.get_ident()==self._thread and not s._unknown,'owner or unknown');s._check()
  need(type(request_id) is str and _ID.fullmatch(request_id) is not None and request_id not in self._ids,'one-use request id')
  need(type(timeout_ns) is int and 0<timeout_ns<=60_000_000_000,'bounded timeout')
  self._ids.add(request_id);n=len(self._ids);operation=s._dir.name
  wire=raw(dict(schema=SCHEMA,id=request_id,operation_id=operation,kind=kind,payload=payload))+b'\n'
  try:
   lower=self._clock();_record(self._folder,f'{n:02d}-started.json',dict(id=request_id,kind=kind,operation_id=operation,raw_hex=wire.hex(),lower_qpc_ns=lower))
   response=s._call(wire,timeout_ns);upper=self._clock()
   trace.put(self._folder/f'{n:02d}-response.bin',response)
   _record(self._folder,f'{n:02d}-returned.json',dict(upper_qpc_ns=upper,response_sha256=sha(response)))
   doc=_decode(response,request_id,operation,kind)
   if doc['status']!='COMPLETE':s._unknown=True
   return dict(response=doc,raw_response=response,lower_qpc_ns=lower,upper_qpc_ns=upper,authority='not_evaluated')
  except BaseException:s._unknown=True;raise
 def trace_scan(self,request_id,prepared,*,build_binding,timeout_ns):
  need(not self._trace and not self._g05,'trace only once before transaction')
  need(type(prepared) is self._bundle.adapter.Preparation and prepared.status=='TRACE94_PLAN_PREPARED' and prepared.plan is not None,'original preparation required')
  original=prepared.original;fixed=self._bundle.adapter.prepare_bytes(original.request,original.source,original.companions,build_binding=build_binding)
  need(fixed.status=='TRACE94_PLAN_PREPARED' and fixed.plan is not None and fixed.plan.facts()['lineage']['operation_id']==self._session._dir.name,'original input and operation required')
  payload=dict(request_hex=original.request.hex(),source_hex=original.source.hex(),companions_hex=[x.hex() for x in original.companions],build_binding=build_binding)
  packet=dict(schema=batch.SCHEMA,id=request_id,operation_id=self._session._dir.name,**payload);batch.decode_batch_request(batch.raw(packet)+b'\n')
  for name,data in [('request.bin',original.request),('source.bin',original.source),*[(f'companion-{i}.bin',v) for i,v in enumerate(original.companions)]]:trace.put(self._folder/name,data)
  self._trace=True;out=self._send(request_id,'trace_scan',payload,timeout_ns);out['correlation']=None
  try:
   if out['response']['status']=='COMPLETE':
    result,wire=trace._response(raw(out['response']['result'])+b'\n',request_id,self._session._dir.name,sha(original.request),build_binding['request_hash'])
    need(result['status']=='COMPLETE','nested trace incomplete')
    out['correlation']=self._bundle.adapter.correlate_collected(fixed.plan,wire,original.companions,result['results'])
   return out
  except BaseException:self._session._unknown=True;raise
 def g05_transaction(self,request_id,identity_words,commands,*,stop,max_polls,duration_ns,timeout_ns):
  need(not self._g05,'one transaction only');identity=g05._identity(identity_words)
  need(type(commands) is tuple and 1<=len(commands)<=2 and type(stop) is bool and type(max_polls) is int and 1<=max_polls<=64 and type(duration_ns) is int and 0<duration_ns<=10_000_000_000,'bounded transaction')
  last=0;profile=None
  for cmd in commands:g05._command(cmd,last,profile);last,profile=cmd[5],cmd[2]
  payload=dict(identity_words=list(identity),commands=[list(x) for x in commands],stop=stop,max_polls=max_polls,duration_ns=duration_ns)
  self._g05=True;out=self._send(request_id,'g05_transaction',payload,timeout_ns)
  try:
   if out['response']['status']=='COMPLETE':_facts(out['response']['result'],self._session._dir.name,identity,commands,stop)
   return out
  except BaseException:self._session._unknown=True;raise
