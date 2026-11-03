"""Default two-scan TRACE coordinator; typed demo allows four on the same port.

No callbacks, caller-selected CSR values, replacement device or authority grant.
"""
import hashlib
from pathlib import Path
import threading
import time
from . import functional50_board_a as board
from . import functional50_board_trace_batch_a as batch
from . import functional50_b131_loader as loader
from . import functional50_demo_four_cycle_profile_a as demo

_OWNERS={}
_KEY=object()

def need(ok,msg):
 if not ok:raise ValueError(msg)

class _CyclePort:
 """Fixed 198 adapter retaining copies of each original port I/O record."""
 def __init__(self,key,owner,directory,index):
  need(key is _KEY,'fixed cycle adapter required');self._owner=owner;self._dir=directory;self._index=index;self._copies=0;self._audit=None
 @property
 def _count(self):return self._owner._port._count
 @property
 def _failed(self):return self._owner._port._failed
 def _call(self,kind,offset,value,request_id):
  owner=self._owner;port=owner._port;owner._check();owner._check_deadline();before=port._count
  need(before-owner._scan_io_start<owner._scan_max_io,'explicit per-scan I/O limit')
  try:
   result=port._call(kind,offset,value,'cy%d-%s'%(self._index,request_id),_cycle_owner=owner)
   owner._check_deadline()
   return result
  finally:
   if port._count>before:
    try:
     need(port._count==before+1,'original I/O count changed')
     if self._audit is not None:
      need(port._trace_audit is self._audit,'same original finite trace journal')
      if self._audit.pair(port._count) is not None:self._copies+=1
     else:
      saved=set()
      for suffix in ('started','returned'):
       name='io-%05d-%s.json'%(port._count,suffix);source=port._dir/name
       if source.exists():
        data,_=board._bytes(source,8192);batch._put(self._dir/name,data);saved.add(suffix)
      if saved=={'started','returned'}:self._copies+=1
    except BaseException:
     port._failed=True;raise

class _Facade:
 _TracePort=_CyclePort

class TraceCycles:
 """Retain one fixed bundle/port and finite nonrenewable scan attempts."""
 def __init__(self,port,bundle):
  need(type(port) is board._TracePort and type(bundle) is loader._Bundle,'original TRACE port and fixed B131 bundle required')
  need(type(port._cycle_policy) is board._TraceCyclePolicy and port._cycle_ready and port._cycle_owner is None and not port._failed,'prospectively bound fresh cycle required')
  reg=board._G05_LOADS.get(port);need(type(reg) is tuple and len(reg)==9 and reg[7] is port._mmio and reg[8]==threading.get_ident()==port._cycle_thread,'original loaded port association required')
  self._port=port;self._bundle=bundle;self._reg=reg;self._thread=threading.get_ident();self._records=[];self._failed=False;self._used_requests=set();self._used_sources=set();self._deadline=None;self._scan_io_start=None;self._scan_max_io=None
  self._directory=port._dir/'trace-cycles-v2';self._directory.mkdir(mode=0o700)
  port._cycle_owner=self;_OWNERS[port]=self
  self._demo_cycle_profile=None
 def select_demo_cycle_profile(self,profile):
  self._check();demo.validate_profile(profile)
  need(profile is not None and self._demo_cycle_profile is None and self._deadline is None
       and not self._records and not self._used_requests and not self._used_sources,'one pre-deadline four-cycle selection required')
  self._demo_cycle_profile=profile
  if demo.is_navigation(profile):self._port._bind_navigation_trace_profile(self,profile)
 def _check(self):
  p=self._port
  need(threading.get_ident()==self._thread and _OWNERS.get(p) is self and p._cycle_owner is self and board._G05_LOADS.get(p) is self._reg and p._mmio is self._reg[7] and not self._failed and not p._failed,'original active cycle owner required')
  if demo.is_navigation(self._demo_cycle_profile):
   need(p._navigation_trace_profile is self._demo_cycle_profile,'original navigation TRACE selection changed')
 def bind_deadline(self,deadline_ns):
  self._check();need(self._deadline is None,'cycle deadline cannot be renewed')
  now=time.monotonic_ns();need(type(deadline_ns) is int and 0<=now<deadline_ns<=min(now+demo.duration_cap(self._demo_cycle_profile),(1<<63)-1),'original bounded board deadline required')
  need(0<=self._port._pid<=0xffffffff,'bounded journal process id required')
  self._deadline=deadline_ns;self._port._cycle_deadline=deadline_ns
 def _check_deadline(self):
  need(self._deadline is not None and 0<=time.monotonic_ns()<self._deadline,'cycle deadline expired')
 def scan(self,line,*,max_io):
  self._check();need(len(self._records)<demo.scan_cap(self._demo_cycle_profile),'selected scan quota consumed')
  p=self._port
  try:
   self._check_deadline();need(type(max_io) is int and 1<=max_io<=2000,'explicit bounded scan I/O required')
   request,source,companions,envelope=batch.decode_batch_request(line)
   request_hash=hashlib.sha256(request).hexdigest();source_hash=hashlib.sha256(source).hexdigest()
   need(request_hash not in self._used_requests and source_hash not in self._used_sources,'new original request and source required')
   plan= self._bundle.adapter.prepare_bytes(request,source,companions,build_binding=envelope['build_binding'])
   need(plan.status=='TRACE94_PLAN_PREPARED' and plan.plan is not None,'original scan preparation required')
   binding=dict(self._reg[3]);need(envelope['operation_id']==binding['operation_id'] and plan.plan.facts()['lineage']['build_id_hex128']==binding['build_id'],'same original load required')
   self._used_requests.add(request_hash);self._used_sources.add(source_hash)
   index=len(self._records)+1;directory=self._directory/('scan-%02d'%index);directory.mkdir(mode=0o700)
   proxy=_CyclePort(_KEY,self,directory,index);self._scan_io_start=p._count;self._scan_max_io=max_io;p._cycle_commands={1:0,2:0,3:0,4:0,5:0,8:0};p._cycle_active=True
   if demo.is_navigation(self._demo_cycle_profile):
    need(p._trace_audit is None,'no prior active trace slab')
    proxy._audit=batch._AuditSlabV1(directory/'trace-audit-v1.bin',base_io=p._count,capacity=max_io,binding=binding,boot=p._boot)
    p._trace_audit=proxy._audit
   try:response=batch.run_batch(proxy,self._bundle,line,_Facade,binding)
   finally:
    p._cycle_active=False
    try:
     if proxy._audit is not None:proxy._audit.finish()
    finally:p._trace_audit=None
   result=batch._json(response);need(result['status']=='COMPLETE' and result['terminal']=='QUIESCENT' and result['cleanup_observed'] and result['wire_complete'] and not result['unknown'],'original scan not complete and quiescent')
   need(all(p._cycle_commands[k]==v for k,v in ((1,1),(2,4),(3,4),(4,4),(5,1))),'exact original per-scan command use required')
   need(proxy._copies==result['batch_io_count']<=max_io,'every original I/O receipt required')
   wire=bytes.fromhex(result['raw_wire_hex']);verified=self._bundle.adapter.correlate_collected(plan.plan,wire,companions,result['results'])
   need(verified['status']=='FOUR_FRAME_CORRELATION_CONSISTENT','four original frame association required')
   files={}
   for path in sorted(directory.rglob('*')):
    if path.is_dir():continue
    limit=8_196_096 if path.name=='trace-audit-v1.bin' and proxy._audit is not None else 2*1024*1024
    data,_=board._bytes(path,limit);files[path.relative_to(directory).as_posix()]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   schema='trace_cycle_evidence_slab_v1' if proxy._audit is not None else 'trace_cycle_evidence_v1'
   manifest=batch.raw(dict(schema=schema,index=index,files=files))+b'\n'
   batch._put(directory/'evidence-manifest.json',manifest)
   record=dict(index=index,request_sha256=request_hash,source_sha256=source_hash,response=response,correlation=verified,directory=directory,evidence_manifest_sha256=hashlib.sha256(manifest).hexdigest())
   self._records.append(record)
   return record
  except BaseException:
   p._cycle_active=False;self._failed=True
   raise
