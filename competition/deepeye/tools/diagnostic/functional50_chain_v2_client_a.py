"""Original-host v2 chain: bounded explicit choices and raw reply retention."""
import re
import threading
from . import functional50_b131_loader as loader
from . import functional50_board_trace_batch_a as batch
from . import functional50_trace_batch_client_a as trace
from . import functional50_g05_a as g05
from . import functional50_ssh_a as ssh
from . import functional50_chain_v2_board_a as protocol
from .functional50_ssh_a import Session, _record, _original_session_origin
from ...integration.host_clock import QpcHostClock

def need(ok,msg):
 if not ok:raise ValueError(msg)
def _hex(v):return type(v) is str and len(v)%2==0 and re.fullmatch('[0-9a-f]*',v) is not None

_PHASE_KEY=object()
_PHASE_LEDGERS={}
_CHAIN_BINDINGS={}
_OWNER_WORK_SELECTION={}
class OriginalPhaseReceipt:
 """One exact host request/reply observation; never an authority decision."""
 __slots__=('owner','phase_index','request_id','kind','operation_id','request_raw','response_raw',
            'lower_qpc_ns','upper_qpc_ns','session','process','stdin','stdout','stderr','clock',
            'session_origin','spec','ready_raw','ready_lower_qpc_ns','ready_upper_qpc_ns','source_pump','status','unknown')
 def __new__(cls,key,*args):
  need(key is _PHASE_KEY,'private original phase factory required');return super().__new__(cls)
 def __init__(self,key,owner,phase_index,request_id,kind,operation,request_raw,response_raw,lower,upper,origin,status,unknown):
  spec,process,clock,ready,parsed,ready_lower,ready_upper,stdin,stdout,stderr=origin
  values=(owner,phase_index,request_id,kind,operation,request_raw,response_raw,lower,upper,owner.s,process,stdin,stdout,stderr,clock,origin,spec,ready,ready_lower,ready_upper,getattr(owner.s,'_source_pump',None),status,unknown)
  for name,value in zip(self.__slots__,values):object.__setattr__(self,name,value)
 def __setattr__(self,name,value):raise AttributeError('original phase is immutable')
 def __reduce__(self):raise TypeError('original phase cannot be serialized')
def _response(data,ident,operation,kind):
 need(type(data) is bytes and 0<len(data)<=1048576 and data.endswith(b'\n') and data.count(b'\n')==1,'bounded reply')
 x=batch._json(data);need(type(x) is dict and set(x)=={'schema','id','operation_id','kind','status','result','error','unknown'} and x['schema']==protocol.SCHEMA and x['id']==ident and x['operation_id']==operation and x['kind']==kind,'reply identity')
 need(x['status'] in ('COMPLETE','REJECTED','UNKNOWN') and type(x['unknown']) is bool and x['unknown']==(x['status']=='UNKNOWN'),'reply status')
 if x['status']=='COMPLETE':need(type(x['result']) is dict and x['error'] is None,'result required')
 else:need((x['result'] is None or (x['status']=='UNKNOWN' and type(x['result']) is dict)) and type(x['error']) is str and 0<len(x['error'])<=96,'bounded failure')
 return x
def _failure_facts(x,operation):
 keys={'schema','kind','operation_id','policy_sha256','deadline_selected_lower_board_monotonic_ns','deadline_board_monotonic_ns','phase_io_first','phase_io_last','identity_words','status','fault','capture','receipts','unresolved_receipts','state','authority'}
 need(type(x) is dict and set(x)==keys and x['schema']=='g05_csr_session_v2' and x['kind']=='close' and x['operation_id']==operation and x['state']=='CLOSED_AFTER_FAILURE' and x['authority']=='not_evaluated','partial failure facts')
 need(type(x['receipts']) is list and type(x['unresolved_receipts']) is list,'original partial records');indices=[]
 for r in x['receipts']:
  need(type(r) is dict and set(r)=={'index','started_raw_hex','returned_raw_hex'} and all(_hex(r[k]) and 0<len(r[k])<=1024 for k in ('started_raw_hex','returned_raw_hex')),'complete raw records');indices.append(r['index'])
 for r in x['unresolved_receipts']:
  keys={'index','started_raw_hex','returned_raw_hex','not_attempted_raw_hex'};need(type(r) is dict and set(r)==keys,'partial raw records')
  values=[r[k] for k in keys if k!='index'];need(sum(v is not None for v in values)<=2 and all(v is None or (_hex(v) and 0<len(v)<=1024) for v in values),'partial original bytes');indices.append(r['index'])
 need(len(indices)<=450 and len(indices)==len(set(indices)) and all(type(i) is int and 1<=i<=450 for i in indices),'distinct original indices')
def _facts(x,kind,operation,identity,deadline):
 keys={'schema','kind','operation_id','policy_sha256','deadline_selected_lower_board_monotonic_ns','deadline_board_monotonic_ns','phase_io_first','phase_io_last','identity_words','status','fault','capture','receipts','unresolved_receipts','state','authority'}
 need(type(x) is dict and set(x)==keys and x['schema']=='g05_csr_session_v2' and x['kind']==kind and x['operation_id']==operation and x['authority']=='not_evaluated' and x['identity_words']==list(identity) and x['unresolved_receipts']==[],'original session facts')
 need(type(x['policy_sha256']) is str and re.fullmatch('[0-9a-f]{64}',x['policy_sha256']) is not None,'policy hash')
 a=x['deadline_selected_lower_board_monotonic_ns'];b=x['deadline_board_monotonic_ns'];need(type(a) is int and type(b) is int and 0<=a<b and b-a<=10_000_000_000 and (deadline is None or deadline==(a,b)),'original board deadline')
 need(x['state']==('CLOSED' if kind=='close' else 'ACTIVE'),'session state')
 need(type(x['receipts']) is list and 0<len(x['receipts'])<=450,'original receipts')
 for i,r in enumerate(x['receipts'],1):
  need(type(r) is dict and set(r)=={'index','started_raw_hex','returned_raw_hex'} and r['index']==i,'receipt index')
  need(all(_hex(r[k]) and 0<len(r[k])<=1024 for k in ('started_raw_hex','returned_raw_hex')),'original receipt bytes')
 first=x['phase_io_first'];last=x['phase_io_last'];need((first is None and last is None) or (type(first) is int and type(last) is int and 1<=first<=last<=len(x['receipts'])),'phase boundaries')
 for k in ('status','fault'):need(x[k] is None or (type(x[k]) is int and 0<=x[k]<=0xffffffff),'observed status')
 c=x['capture']
 if kind=='apply':
  need(type(c) is dict and set(c)=={'status_before_latch','fault_before_latch','words32','status_before_snapshot','status_after_snapshot','result_seq','tick_unit'} and c['tick_unit']=='50MHz_cycles' and type(c['words32']) is list and len(c['words32'])==32 and all(type(w) is int and 0<=w<=0xffffffff for w in c['words32']),'capture facts')
  need(all(type(c[k]) is int and 0<=c[k]<=0xffffffff for k in ('status_before_latch','fault_before_latch','status_before_snapshot','status_after_snapshot','result_seq')),'capture fields')
 else:need(c is None,'unexpected capture')
 return (a,b)

class ChainSessionV2:
 def __init__(self,session,bundle,clock):
  need(type(session) is Session and session._protocol==protocol.SCHEMA and type(bundle) is loader._Bundle and type(clock) is QpcHostClock and session._clock is clock,'original session/bundle/QPC')
  origin=_original_session_origin(session);need(origin[2] is clock,'original factory origin required')
  session._check();need(not getattr(session,'_chain_claimed',False),'original session claimed');session._chain_claimed=True
  self.s=session;self.bundle=bundle;self.clock=clock;self.thread=threading.get_ident();self.sequence=protocol.Sequence();self.identity=None;self.deadline=None;self.duration=None;self.policy_sha=None;self.receipts=[];self.folder=session._dir/'chain-v2-host';self.folder.mkdir(mode=0o700)
  _PHASE_LEDGERS[self]=[];_CHAIN_BINDINGS[self]=(session,clock,bundle,session._proc,self.sequence,origin)
 def _phase_binding(self):
  need(self in _CHAIN_BINDINGS and self in _PHASE_LEDGERS,'original chain custody required')
  session,clock,bundle,process,sequence,origin=_CHAIN_BINDINGS[self]
  need(self.s is session and self.clock is clock and self.bundle is bundle and session._proc is process and self.sequence is sequence and _original_session_origin(session) is origin,'original chain custody changed')
  return origin
 @property
 def owner_work_v1(self):
  self._phase_binding()
  return _OWNER_WORK_SELECTION.get(self) is _CHAIN_BINDINGS[self]
 def select_owner_work_v1(self):
  origin=self._phase_binding();need(threading.get_ident()==self.thread and not self.sequence.initialized and not self.sequence.ids and self not in _OWNER_WORK_SELECTION,'one pre-init owner work selection required')
  self.s._check();_OWNER_WORK_SELECTION[self]=_CHAIN_BINDINGS[self]
 def _work_pump(self,*,_closing=None):
  from .original_chain_source_pump_a import OriginalChainSourcePump
  from .original_source_trace_scan_a import OriginalSourceTraceScan
  pump=getattr(self.s,'_source_pump',None)
  need(type(pump) is OriginalChainSourcePump and ssh._SESSION_PUMPS.get(self.s) is pump and pump.session is self.s and pump.clock is self.clock and type(pump.scanner) is OriginalSourceTraceScan and pump.enabled and not pump.failed,'exact enabled original source pump required')
  if _closing is None:OriginalChainSourcePump._check(pump,True)
  else:OriginalChainSourcePump._check(pump,True,_closing=_closing)
  return pump
 def _selected_active(self,kind):
  if self not in _OWNER_WORK_SELECTION:return False
  need(self.owner_work_v1,'original owner work selection changed')
  pump=getattr(self.s,'_source_pump',None)
  if pump is not None and pump.failed:
   self.s._unknown=True;raise ValueError('original source pump failed')
  if kind=='init' and (pump is None or not pump.enabled):return False
  try:self._work_pump();return True
  except BaseException:self.s._unknown=True;raise
 def _sequence_snapshot(self):
  q=self.sequence
  return (q.initialized,q.closed,tuple(sorted(q.counts.items())),frozenset(q.ids),q.max_commands,q.last,q.profile)
 def _run_work(self,kind,args,end):
  from . import original_chain_client_work_a as work
  return work._wait(self,work._start(self,kind,args,end),end)
 def _send_selected(self,ident,kind,payload,end,*,prepared=None,trace_args=None):
  from . import original_chain_client_work_a as work
  s=self.s;need(threading.get_ident()==self.thread and not s._unknown,'owner or unknown');s._check();origin=self._phase_binding();pump=self._work_pump()
  try:
   snapshot=self._sequence_snapshot();wire,x=self._run_work('encode',(ident,kind,payload,s._dir.name,snapshot),end)
   need(self._sequence_snapshot()==snapshot,'original sequence changed during fixed work')
   self.sequence.consume(x);n=len(self.sequence.ids)
   lower=self.clock();job=work._start(self,'intent',(self.folder,n,ident,kind,wire,lower),end);work._wait(self,job,end)
   permit=work._permit(self,end,wire,job,prepared)
   response=s._call_until(wire,permit);upper=self.clock()
   doc=self._run_work('reply',(self.folder,n,response,upper,ident,s._dir.name,kind),end)
   need(_original_session_origin(s) is origin and getattr(s,'_source_pump',None) is pump and ssh._SESSION_PUMPS.get(s) is pump and len(_PHASE_LEDGERS[self])==n-1,'original phase ordering changed')
   receipt=OriginalPhaseReceipt(_PHASE_KEY,self,n,ident,kind,s._dir.name,wire,response,lower,upper,origin,doc['status'],doc['unknown']);_PHASE_LEDGERS[self].append(receipt)
   correlation=None
   if doc['status']=='UNKNOWN' and doc['result'] is not None:
    self._run_work('failure_post',(doc['result'],s._dir.name),end)
    need(_original_session_origin(s) is origin and getattr(s,'_source_pump',None) is pump and ssh._SESSION_PUMPS.get(s) is pump and len(_PHASE_LEDGERS[self])==n and _PHASE_LEDGERS[self][-1] is receipt,'original phase changed after failure validation')
   if trace_args is not None and doc['status']=='COMPLETE':
    observed,correlation=self._run_work('trace_post',(*trace_args,response),end);need(observed==doc,'trace reply changed')
    need(_original_session_origin(s) is origin and getattr(s,'_source_pump',None) is pump and ssh._SESSION_PUMPS.get(s) is pump and len(_PHASE_LEDGERS[self])==n and _PHASE_LEDGERS[self][-1] is receipt,'original phase changed after correlation')
   if doc['status']!='COMPLETE':s._unknown=True
   out=dict(response=doc,raw_response=response,lower_qpc_ns=lower,upper_qpc_ns=upper,authority='not_evaluated',phase_receipt=receipt,_owner_work_end=end)
   if trace_args is not None:out['correlation']=correlation
   return out
  except BaseException:s._unknown=True;raise
 @property
 def phase_receipts(self):
  self._phase_binding();return tuple(_PHASE_LEDGERS[self])
 def _send(self,ident,kind,payload,timeout_ns):
  s=self.s;need(threading.get_ident()==self.thread and not s._unknown,'owner or unknown');s._check();need(type(timeout_ns) is int and 0<timeout_ns<=60_000_000_000,'bounded timeout')
  if self in _OWNER_WORK_SELECTION:
   phase_started=self.clock()
   if self._selected_active(kind):return self._send_selected(ident,kind,payload,phase_started+timeout_ns)
  origin=self._phase_binding();pump=getattr(s,'_source_pump',None)
  need(origin[2] is self.clock and self in _PHASE_LEDGERS and (pump is None and s not in ssh._SESSION_PUMPS or pump is not None and ssh._SESSION_PUMPS.get(s) is pump),'original session, pump and phase ledger required')
  wire=protocol.raw(dict(schema=protocol.SCHEMA,id=ident,operation_id=s._dir.name,kind=kind,payload=payload))+b'\n';x=protocol.decode_request(wire,s._dir.name,g05,self.sequence)
  self.sequence.consume(x);n=len(self.sequence.ids)
  try:
   lower=self.clock();_record(self.folder,f'{n:02d}-started.json',dict(id=ident,kind=kind,raw_hex=wire.hex(),lower_qpc_ns=lower))
   response=s._call(wire,timeout_ns);upper=self.clock();trace.put(self.folder/f'{n:02d}-response.bin',response);_record(self.folder,f'{n:02d}-returned.json',dict(upper_qpc_ns=upper,response_sha256=protocol.digest(response)))
   doc=_response(response,ident,s._dir.name,kind)
   need(_original_session_origin(s) is origin and getattr(s,'_source_pump',None) is pump and (pump is None and s not in ssh._SESSION_PUMPS or pump is not None and ssh._SESSION_PUMPS.get(s) is pump) and len(_PHASE_LEDGERS[self])==n-1,'original phase ordering changed')
   receipt=OriginalPhaseReceipt(_PHASE_KEY,self,n,ident,kind,s._dir.name,wire,response,lower,upper,origin,doc['status'],doc['unknown'])
   _PHASE_LEDGERS[self].append(receipt)
   if doc['status']!='COMPLETE':s._unknown=True
   if doc['status']=='UNKNOWN' and doc['result'] is not None:_failure_facts(doc['result'],s._dir.name)
   return dict(response=doc,raw_response=response,lower_qpc_ns=lower,upper_qpc_ns=upper,authority='not_evaluated',phase_receipt=receipt)
  except BaseException:s._unknown=True;raise
 def _g05(self,ident,kind,payload,timeout_ns):
  try:
   out=self._send(ident,kind,payload,timeout_ns)
   if out['response']['status']=='COMPLETE':
    result=out['response']['result']
    if '_owner_work_end' in out:
     self.deadline=self._run_work('g05_post',(result,kind,self.s._dir.name,self.identity,self.deadline,self.duration,self.policy_sha,self.receipts,payload),out['_owner_work_end'])
     self.policy_sha=result['policy_sha256'];self.receipts=result['receipts']
     if kind=='close':
      from . import original_chain_client_work_a as work
      work._await_close_exit(self.s)
     return out
    self.deadline=_facts(result,kind,self.s._dir.name,self.identity,self.deadline)
    need(self.deadline[1]-self.deadline[0]==self.duration and (self.policy_sha is None or self.policy_sha==result['policy_sha256']),'fixed duration and policy')
    need(result['receipts'][:len(self.receipts)]==self.receipts,'original cumulative receipts changed')
    self.policy_sha=result['policy_sha256'];self.receipts=result['receipts']
    if kind=='apply':need(result['capture']['words32'][1:3]==payload['command_words'][5:7],'capture command association')
   return out
  except BaseException:self.s._unknown=True;raise
  finally:
   if kind=='close':
    from . import original_chain_client_work_a as work
    work._finish_closing(self.s)
 def init(self,ident,identity_words,*,max_commands,max_polls,duration_ns,max_io,timeout_ns):
  need(not self.sequence.initialized and type(identity_words) is tuple,'one immutable identity required');g05._identity(identity_words);self.identity=identity_words;self.duration=duration_ns
  return self._g05(ident,'init',dict(identity_words=list(identity_words),max_commands=max_commands,max_polls=max_polls,duration_ns=duration_ns,max_io=max_io),timeout_ns)
 def apply(self,ident,command_words,*,timeout_ns):
  need(type(command_words) is tuple,'immutable command required');return self._g05(ident,'apply',dict(command_words=list(command_words)),timeout_ns)
 def status(self,ident,*,timeout_ns):return self._g05(ident,'status',{},timeout_ns)
 def close(self,ident,*,stop=False,timeout_ns):return self._g05(ident,'close',dict(stop=stop),timeout_ns)
 def _trace_selected(self,ident,prepared,build_binding,max_io,timeout_ns,start):
  need(type(timeout_ns) is int and 0<timeout_ns<=60_000_000_000,'bounded timeout')
  try:
   pump=self._work_pump();scanner=pump.scanner
   from .original_source_trace_scan_a import OriginalSourceTraceScan
   original_end=OriginalSourceTraceScan._prepared_work_deadline(scanner,prepared);end=min(original_end,start+timeout_ns)
   need(type(prepared) is self.bundle.adapter.Preparation and prepared.status=='TRACE94_PLAN_PREPARED' and prepared.plan is not None,'original preparation required')
   original=prepared.original;request=original.request;source=original.source;companions=original.companions
   need(type(request) is bytes and type(source) is bytes and type(companions) is tuple and len(companions)==4 and all(type(x) is bytes for x in companions),'immutable original trace bytes required')
   need(type(build_binding) is dict and all(type(k) is str and type(v) is str for k,v in build_binding.items()),'fixed trace binding required');binding=dict(build_binding)
   index=self.sequence.counts['trace_scan']+1
   fixed,payload=self._run_work('trace_prepare',(self.bundle,request,source,companions,binding,ident,self.s._dir.name,max_io,self.folder,index),end)
   trace_args=(self.bundle,fixed,request,source,companions,binding,ident,self.s._dir.name,index,max_io)
   return self._send_selected(ident,'trace_scan',payload,end,prepared=prepared,trace_args=trace_args)
  except BaseException:self.s._unknown=True;raise
 def trace_scan(self,ident,prepared,*,build_binding,max_io,timeout_ns):
  if self in _OWNER_WORK_SELECTION:
   phase_started=self.clock()
   if self._selected_active('trace_scan'):return self._trace_selected(ident,prepared,build_binding,max_io,timeout_ns,phase_started)
  need(type(prepared) is self.bundle.adapter.Preparation and prepared.status=='TRACE94_PLAN_PREPARED' and prepared.plan is not None,'original preparation required')
  original=prepared.original;fixed=self.bundle.adapter.prepare_bytes(original.request,original.source,original.companions,build_binding=build_binding)
  need(fixed.status=='TRACE94_PLAN_PREPARED' and fixed.plan is not None and fixed.plan.facts()['lineage']['operation_id']==self.s._dir.name,'original inputs and operation')
  payload=dict(request_hex=original.request.hex(),source_hex=original.source.hex(),companions_hex=[v.hex() for v in original.companions],build_binding=build_binding,max_io=max_io)
  p={k:payload[k] for k in ('request_hex','source_hex','companions_hex','build_binding')};batch.decode_batch_request(batch.raw(dict(schema=batch.SCHEMA,id=ident,operation_id=self.s._dir.name,**p))+b'\n')
  folder=self.folder/('scan-%02d'%(self.sequence.counts['trace_scan']+1));folder.mkdir(mode=0o700)
  for name,data in [('request.bin',original.request),('source.bin',original.source),*[(f'companion-{i}.bin',v) for i,v in enumerate(original.companions)]]:trace.put(folder/name,data)
  out=self._send(ident,'trace_scan',payload,timeout_ns);out['correlation']=None
  try:
   if out['response']['status']=='COMPLETE':
    result=out['response']['result'];keys={'schema','index','request_sha256','source_sha256','response','phase_io_first','phase_io_last','correlation_status','directory','evidence_manifest_sha256','authority'}
    need(type(result) is dict and set(result)==keys and result['schema']=='trace_cycle_v2' and result['index']==self.sequence.counts['trace_scan'] and result['authority']=='not_evaluated' and result['request_sha256']==protocol.digest(original.request) and result['source_sha256']==protocol.digest(original.source),'original trace result')
    need(result['correlation_status']=='FOUR_FRAME_CORRELATION_CONSISTENT' and type(result['directory']) is str and result['directory'].startswith('/') and len(result['directory'])<=1024 and type(result['evidence_manifest_sha256']) is str and re.fullmatch('[0-9a-f]{64}',result['evidence_manifest_sha256']) is not None,'board evidence manifest reference')
    first=result['phase_io_first'];last=result['phase_io_last'];need(type(first) is int and type(last) is int and 1<=first<=last<=5000 and last-first+1<=max_io,'actual TRACE phase')
    doc,wire=trace._response(protocol.raw(result['response'])+b'\n',ident,self.s._dir.name,protocol.digest(original.request),build_binding['request_hash']);need(doc['status']=='COMPLETE','complete trace required')
    out['correlation']=self.bundle.adapter.correlate_collected(fixed.plan,wire,original.companions,doc['results']);need(out['correlation']['status']=='FOUR_FRAME_CORRELATION_CONSISTENT','host correlation required')
   return out
  except BaseException:self.s._unknown=True;raise
