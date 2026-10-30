"""Root-side original-object receipts; observations, never authority grants."""
import copy
import threading
from . import functional50_ssh_a as ssh
from . import functional50_b131_loader as loader
from . import functional50_chain_v2_client_a as client
from . import original_source_trace_scan_a as scanner_module
from ..run_causal_functional_chain import FunctionalWorld, FunctionalSource
from ...integration.host_clock import QpcHostClock

def need(ok,msg):
 if not ok:raise ValueError(msg)

_KEY=object()
_OWNERS={}
_SOURCES={}
_SCANNERS={}
_EVENTS={}

class _ReceiptEvent:
 __slots__=()
 def __new__(cls,key):
  need(key is _KEY,'private receipt factory required');return super().__new__(cls)
 def __reduce__(self):raise TypeError('original receipt cannot be serialized')

def consume_original_receipt(event):
 """Consume the exact original event once, in its producer's sequence."""
 need(type(event) is _ReceiptEvent and event in _EVENTS,'original receipt event required')
 owner,seq,facts,refs=_EVENTS[event]
 need(threading.get_ident()==owner._thread and _OWNERS.get(owner._session) is owner and seq==owner._next_consume,'original owner and event order required')
 owner._binding_check()
 del _EVENTS[event];owner._next_consume+=1
 return copy.deepcopy(facts),dict(refs)

class OriginalChainReceiptProducer:
 """Strongly retain one real source/clock/session; explicit methods only."""
 def __init__(self,world,chain,scanner=None):
  need(type(world) is FunctionalWorld and type(world.source) is FunctionalSource and type(chain) is client.ChainSessionV2 and (scanner is None or type(scanner) is scanner_module.OriginalSourceTraceScan),'exact original world, chain and optional scanner required')
  source=world.source;clock=world.clock;session=chain.s;bundle=chain.bundle
  need(type(clock) is QpcHostClock and type(bundle) is loader._Bundle and chain.clock is clock and source.clock is clock,'same original source, clock and B131 required')
  need(world._thread==source._thread==chain.thread==threading.get_ident() and world.owner is source.owner and world.binding is source.binding,'same original owner/thread required')
  origin=ssh._original_session_origin(session);spec,process,origin_clock,ready,parsed,lower,upper,stdin,stdout,stderr=origin
  need(origin_clock is clock and world.operation_id==spec.operation_id==session._dir.name and not session._unknown and not session._closed and session not in _OWNERS and source not in _SOURCES,'original operation, ready and unclaimed source/session required')
  need(not chain.sequence.initialized and not chain.sequence.ids and not chain.sequence.closed,'fresh original chain required')
  self._thread=threading.get_ident();self._world=world;self._source=source;self._chain=chain;self._sequence=chain.sequence;self._scanner=None;self._session=session;self._bundle=bundle;self._clock=clock;self._origin=origin;self._process=process;self._ready=ready;self._stdin=stdin;self._stdout=stdout;self._stderr=stderr;self._book=source.book;self._pump=source.source;self._world_owner=world.owner;self._binding=world.binding;self._operation=spec.operation_id
  self._events=[];self._history=[];self._failed=False;self._closed=False;self._next_consume=1;self._operation_count=0;self._admission_count=0;self._source_pump=None;self._pump_index=0;self._pending_events=[];self._pending_reported=False
  _OWNERS[session]=self;_SOURCES[source]=self
  if scanner is not None:self.bind_scanner(scanner)
 def bind_scanner(self,scanner):
  self._check();need(self._scanner is None and type(scanner) is scanner_module.OriginalSourceTraceScan and scanner not in _SCANNERS,'one original scanner binding required')
  need(scanner._clock is self._clock and scanner._bundle is self._bundle and scanner._functional is self._source and scanner._source is self._pump and scanner._book is self._book and scanner._thread==self._thread and scanner._source_scan_cycle_v2 is True,'same original v2 source scanner required')
  need(not scanner._admitted and not scanner._prepared and not scanner._failed and scanner._prepare_count==0,'fresh source history required')
  need(self._pump.state=='RUNNING' and self._pump._count==0 and not self._source._retained_samples,'original started source before first sample required')
  self._scanner=scanner;_SCANNERS[scanner]=self
 def bind_pump(self,pump):
  from .original_chain_source_pump_a import OriginalChainSourcePump
  self._check();need(self._scanner is not None and self._source_pump is None and type(pump) is OriginalChainSourcePump and pump.session is self._session and pump.source is self._source and pump.scanner is self._scanner and pump.clock is self._clock and not pump.enabled and not pump.failed,'one original disabled source pump required')
  self._session.bind_source_pump(pump);self._source_pump=pump
 def enable_pump(self):
  self._check();need(self._source_pump is not None,'original pump required')
  from .original_chain_source_pump_a import OriginalChainSourcePump
  try:OriginalChainSourcePump.enable(self._source_pump)
  except BaseException:self._session._unknown=True;self._failed=True;raise
 def _flush_pump(self):
  pump=self._source_pump
  if pump is None:return
  from .original_chain_source_pump_a import PumpRecord
  records=pump.history
  need(self._pump_index<=len(records),'source history regressed')
  while self._pump_index<len(records):
   record=records[self._pump_index];need(type(record) is PumpRecord,'original pump record required')
   matches=[item for item in self._scanner._admitted if item['entry'] is record.entry]
   need(len(matches)==1 and matches[0]['token'] is record.token and matches[0]['draft'] is record.draft and matches[0]['admission'] is record.admission,'original pumped admission required')
   item=matches[0]
   need(self._admission_count<len(self._scanner._admitted) and self._scanner._admitted[self._admission_count] is item,'complete ordered source history required')
   event=self._event('source_admission',dict(payload_bytes=item['payload_bytes'],draft=copy.deepcopy(record.draft),received_qpc_ns=record.received_qpc_ns,released=record.released),dict(payload=record.payload,admitted=item,token=record.token,draft=record.draft,adc_handle=record.token._handle,em_handle=record.token._em_handle,admission=record.admission,pump=pump,pump_record=record))
   self._pending_events.append(event);self._pump_index+=1;self._admission_count+=1
  if pump.failed and pump.pending is not None and not self._pending_reported:
   event=self._event('source_pending',dict(status='INCOMPLETE'),dict(pump=pump,pending=pump.pending));self._pending_events.append(event);self._pending_reported=True
 def take_pending_events(self):
  self._binding_check();result=tuple(self._pending_events);self._pending_events.clear();return result
 def pump_once(self):
  self._check();need(self._source_pump is not None and self._source_pump.enabled,'enabled original source pump required')
  from .original_chain_source_pump_a import OriginalChainSourcePump
  try:
   OriginalChainSourcePump.poll_once(self._source_pump,self._session);self._flush_pump()
   return self.take_pending_events()
  except BaseException:
   self._session._unknown=True;self._failed=True
   try:self._flush_pump()
   except BaseException:pass
   raise
 def _check(self):
  need(threading.get_ident()==self._thread and _OWNERS.get(self._session) is self and not self._failed and not self._closed and not self._session._unknown and not self._session._closed,'original active producer required')
  self._binding_check()
  if self._source_pump is not None and self._source_pump.failed:
   self._session._unknown=True;self._failed=True;raise ValueError('original source pump failed')
  need(self._scanner is None or not self._scanner._failed,'original scanner failed')
  need(self._scanner is None or len(self._scanner._admitted)==self._admission_count,'unowned source admission detected')
 def _binding_check(self):
  need(threading.get_ident()==self._thread and _OWNERS.get(self._session) is self and _SOURCES.get(self._source) is self and (self._scanner is None or _SCANNERS.get(self._scanner) is self),'original producer owner required')
  need(ssh._original_session_origin(self._session) is self._origin and self._session._proc is self._process and self._chain.s is self._session and self._chain.sequence is self._sequence and self._chain.clock is self._clock and self._chain.bundle is self._bundle and self._chain.thread==self._thread,'original process/session/clock/bundle changed')
  need(len(self._chain.sequence.ids)==self._operation_count,'unowned chain operation detected')
  need(self._world._thread==self._source._thread==self._thread and self._world.source is self._source and self._world.owner is self._world_owner and self._world.binding is self._binding and self._world.clock is self._clock and self._world.operation_id==self._operation and self._source.owner is self._world_owner and self._source.binding is self._binding and self._source.clock is self._clock and self._source.book is self._book and self._source.source is self._pump,'original world/source association changed')
  if self._scanner is not None:
   need(self._scanner._thread==self._thread and self._scanner._functional is self._source and self._scanner._clock is self._clock and self._scanner._bundle is self._bundle and self._scanner._book is self._book and self._scanner._source is self._pump,'original scanner association changed')
  if self._source_pump is not None:
   need(getattr(self._session,'_source_pump',None) is self._source_pump and self._source_pump.session is self._session and self._source_pump.source is self._source and self._source_pump.scanner is self._scanner and self._source_pump.clock is self._clock,'original fixed source pump changed')
 def _event(self,kind,facts,extra):
  event=_ReceiptEvent(_KEY);seq=len(self._events)+1
  refs=dict(world=self._world,functional_source=self._source,source=self._pump,book=self._book,scanner=self._scanner,source_pump=self._source_pump,bundle=self._bundle,chain=self._chain,session=self._session,session_origin=self._origin,process=self._process,stdin=self._stdin,stdout=self._stdout,stderr=self._stderr,clock=self._clock,**extra)
  detached=dict(kind=kind,sequence=seq,operation_id=self._operation,**facts)
  saved=copy.deepcopy(detached);_EVENTS[event]=(self,seq,saved,refs);self._events.append(event);self._history.append((event,saved,refs))
  return event
 def _call(self,kind,method,ident,*args,**kwargs):
  self._check()
  try:
   out=method(self._chain,ident,*args,**kwargs)
   need(len(self._chain.sequence.ids)==self._operation_count+1 and ident in self._chain.sequence.ids,'original one-use client operation required');self._operation_count+=1
   self._flush_pump()
   need(type(out) is dict and type(out.get('raw_response')) is bytes and type(out.get('lower_qpc_ns')) is int and type(out.get('upper_qpc_ns')) is int and 0<=out['lower_qpc_ns']<=out['upper_qpc_ns'],'original client response brackets')
   doc=client._response(out['raw_response'],ident,self._operation,kind)
   need(doc==out['response'],'raw original reply mismatch')
   if doc['status']!='COMPLETE':self._failed=True
   return self._event(kind,dict(raw_response=out['raw_response'],response=doc,lower_qpc_ns=out['lower_qpc_ns'],upper_qpc_ns=out['upper_qpc_ns'],correlation=copy.deepcopy(out.get('correlation'))),dict(client_result=out))
  except BaseException:
   if len(self._chain.sequence.ids)==self._operation_count+1 and ident in self._chain.sequence.ids:self._operation_count+=1
   try:self._flush_pump()
   except BaseException:pass
   self._failed=True;raise
 def init(self,ident,identity_words,*,max_commands,max_polls,duration_ns,max_io,timeout_ns):
  return self._call('init',client.ChainSessionV2.init,ident,identity_words,max_commands=max_commands,max_polls=max_polls,duration_ns=duration_ns,max_io=max_io,timeout_ns=timeout_ns)
 def admit_source(self,payload):
  self._check()
  try:
   need(self._scanner is not None,'original scanner required')
   admission=scanner_module.OriginalSourceTraceScan.admit(self._scanner,payload);item=self._scanner._admitted[-1]
   need(len(self._scanner._admitted)==self._admission_count+1,'original one-use source admission required');self._admission_count+=1
   need(item['entry']['payload'] is payload and item['token']._draft is item['draft'],'original admitted sample required')
   return self._event('source_admission',dict(payload_bytes=item['payload_bytes'],draft=copy.deepcopy(item['draft']),received_qpc_ns=item['received']),dict(payload=payload,admitted=item,token=item['token'],draft=item['draft'],adc_handle=item['token']._handle,em_handle=item['token']._em_handle,admission=admission))
  except BaseException:self._failed=True;raise
 def scan_actual(self,ident,payload,*,facts,build_binding,max_io,timeout_ns):
  self._check()
  try:
   need(self._scanner is not None,'original scanner required')
   need(self._scanner._admitted and self._scanner._admitted[-1]['entry']['payload'] is payload,'latest admitted original payload required')
   item=self._scanner._admitted[-1]
   need(type(facts) is dict and type(build_binding) is dict,'explicit root facts and binding required')
   facts_snapshot=copy.deepcopy(facts);binding_snapshot=copy.deepcopy(build_binding)
   preparation=scanner_module.OriginalSourceTraceScan.prepare(self._scanner,payload,facts=facts,build_binding=build_binding)
   need(type(preparation) is self._bundle.adapter.Preparation and preparation is self._scanner._result,'actual B131 preparation required')
   out=client.ChainSessionV2.trace_scan(self._chain,ident,preparation,build_binding=build_binding,max_io=max_io,timeout_ns=timeout_ns)
   need(len(self._chain.sequence.ids)==self._operation_count+1 and ident in self._chain.sequence.ids,'original one-use trace operation required');self._operation_count+=1
   self._flush_pump()
   need(type(out) is dict and type(out.get('raw_response')) is bytes and type(out.get('lower_qpc_ns')) is int and type(out.get('upper_qpc_ns')) is int and 0<=out['lower_qpc_ns']<=out['upper_qpc_ns'],'original trace response brackets')
   doc=client._response(out['raw_response'],ident,self._operation,'trace_scan');need(doc==out['response'],'original trace reply mismatch')
   need(facts==facts_snapshot and build_binding==binding_snapshot,'root facts or binding changed during original call')
   if doc['status']=='COMPLETE':need(type(out.get('correlation')) is dict and out['correlation'].get('status')=='FOUR_FRAME_CORRELATION_CONSISTENT','actual original correlation required')
   else:self._failed=True
   original=preparation.original
   return self._event('trace_scan',dict(raw_response=out['raw_response'],response=doc,lower_qpc_ns=out['lower_qpc_ns'],upper_qpc_ns=out['upper_qpc_ns'],correlation=copy.deepcopy(out.get('correlation')),root_facts=facts_snapshot,build_binding=binding_snapshot),dict(client_result=out,payload=payload,admitted=item,admission=item['admission'],token=item['token'],draft=item['draft'],adc_handle=item['token']._handle,em_handle=item['token']._em_handle,preparation=preparation,request=original.request,source_bytes=original.source,companions=original.companions,build_binding=build_binding,root_facts=facts))
  except BaseException:
   if len(self._chain.sequence.ids)==self._operation_count+1 and ident in self._chain.sequence.ids:self._operation_count+=1
   try:self._flush_pump()
   except BaseException:pass
   self._failed=True;raise
 def apply(self,ident,command_words,*,timeout_ns):return self._call('apply',client.ChainSessionV2.apply,ident,command_words,timeout_ns=timeout_ns)
 def status(self,ident,*,timeout_ns):return self._call('status',client.ChainSessionV2.status,ident,timeout_ns=timeout_ns)
 def close(self,ident,*,stop=False,timeout_ns):
  event=self._call('close',client.ChainSessionV2.close,ident,stop=stop,timeout_ns=timeout_ns);self._closed=True;return event
