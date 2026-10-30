"""One strict batch over an already-owned original SSH session; no authorization."""
import hashlib
import json
from pathlib import Path
import threading

from . import functional50_b131_loader as loader
from . import functional50_board_trace_batch_a as protocol
from .functional50_ssh_a import Session, _record
from ...integration.host_clock import QpcHostClock


def need(value,message):
 if not value:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(data):return hashlib.sha256(data).hexdigest()
def put(path,data):
 with path.open('xb') as f:
  import os
  f.write(data);f.flush();os.fsync(f.fileno())

def _response(data,request_id,operation,request_hash,lineage_hash):
 need(type(data) is bytes and 0<len(data)<=4096 and data.endswith(b'\n') and data.count(b'\n')==1,'bounded batch response required')
 doc=protocol._json(data);keys={'schema','id','operation_id','request_sha256','lineage_request_hash','status','raw_wire_hex','wire_complete','results','io_count','batch_io_count','cleanup_observed','terminal','unknown'}
 need(type(doc) is dict and set(doc) in (keys,keys|{'error_type'}) and doc['schema']==protocol.SCHEMA and doc['id']==request_id and doc['operation_id']==operation and doc['request_sha256']==request_hash and doc['lineage_request_hash']==lineage_hash,'batch response identity')
 if 'error_type' in doc:need(type(doc['error_type']) is str and 0<len(doc['error_type'])<=96,'bounded error type required')
 need(doc['status'] in ('COMPLETE','REFUSED','FAILED','UNKNOWN') and type(doc['unknown']) is bool and type(doc['wire_complete']) is bool and type(doc['cleanup_observed']) is bool and type(doc['io_count']) is int and 0<=doc['io_count']<=5000 and type(doc['batch_io_count']) is int and 0<=doc['batch_io_count']<=doc['io_count'] and type(doc['results']) is list and len(doc['results'])<=4 and doc['terminal'] in ('QUIESCENT','NOT_PROVEN','UNKNOWN','NOT_STARTED'),'batch response shape')
 if doc['terminal']=='QUIESCENT':need(doc['cleanup_observed'],'cleanup observation missing')
 need((doc['status']=='UNKNOWN')==doc['unknown'] and (doc['terminal']=='UNKNOWN')==doc['unknown'],'batch unknown state mismatch')
 value=doc['raw_wire_hex']
 if value is None:need(not doc['wire_complete'],'missing wire cannot be complete');wire=None
 else:
  need(type(value) is str and len(value)<=504 and len(value)%2==0 and all(c in '0123456789abcdef' for c in value),'invalid wire representation');wire=bytes.fromhex(value)
 if doc['status']=='COMPLETE':need(not doc['unknown'] and doc['terminal']=='QUIESCENT' and doc['wire_complete'] and wire is not None and len(doc['results'])==4,'complete result lacks original evidence')
 else:need(not doc['wire_complete'],'incomplete operation cannot assert complete wire')
 return doc,wire


class BatchSession:
 """Own one request on one original SSH process; no retries or replacements."""
 def __init__(self,session,bundle,clock):
  need(type(session) is Session and session._protocol=='trace_batch_v1' and type(bundle) is loader._Bundle and type(clock) is QpcHostClock and session._clock is clock,'original batch session/bundle/QPC required')
  session._check();self._session=session;self._bundle=bundle;self._clock=clock;self._thread=threading.get_ident()
 def exchange(self,request_id,prepared,*,build_binding,timeout_ns):
  session=self._session
  need(threading.get_ident()==self._thread and not session._batch_consumed,'single original batch required')
  need(type(timeout_ns) is int and 0<timeout_ns<=60_000_000_000,'fixed batch timeout required')
  session._check()
  need(type(prepared) is self._bundle.adapter.Preparation and prepared.status=='TRACE94_PLAN_PREPARED' and prepared.plan is not None,'original prepared plan required')
  original=prepared.original
  fixed=self._bundle.adapter.prepare_bytes(original.request,original.source,original.companions,build_binding=build_binding)
  need(fixed.status=='TRACE94_PLAN_PREPARED' and fixed.plan is not None,'original input revalidation failed')
  facts=fixed.plan.facts();operation=facts['lineage']['operation_id'];need(operation==session._dir.name,'same original SSH operation required')
  packet=dict(schema=protocol.SCHEMA,id=request_id,operation_id=operation,request_hex=original.request.hex(),source_hex=original.source.hex(),companions_hex=[v.hex() for v in original.companions],build_binding=build_binding)
  wire=raw(packet)+b'\n';protocol.decode_batch_request(wire)
  session._batch_consumed=True
  folder=session._dir/'trace-batch-host';folder.mkdir(mode=0o700)
  for name,data in [('request.bin',original.request),('source.bin',original.source),*[(f'companion-{i}.bin',v) for i,v in enumerate(original.companions)]]:put(folder/name,data)
  try:
   lower=self._clock();_record(folder,'batch-started.json',dict(id=request_id,operation_id=operation,request_sha256=sha(original.request),envelope_sha256=sha(wire),build_binding=build_binding,lower_qpc_ns=lower))
   response=session._call(wire,timeout_ns);upper=self._clock()
   put(folder/'response.bin',response);_record(folder,'batch-returned.json',dict(upper_qpc_ns=upper,response_sha256=sha(response)))
   result,wire_bytes=_response(response,request_id,operation,sha(original.request),build_binding['request_hash'])
   if result['unknown']:session._unknown=True
   correlation=None
   if result['status']=='COMPLETE':
    correlation=self._bundle.adapter.correlate_collected(fixed.plan,wire_bytes,original.companions,result['results'])
   return dict(response=result,raw_response=response,lower_qpc_ns=lower,upper_qpc_ns=upper,correlation=correlation,authority='not_evaluated')
  except BaseException:
   session._unknown=True
   raise
