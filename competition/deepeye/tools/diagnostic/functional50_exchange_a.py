"""One A-owned TRACE scan using fixed B131 reducer and original SSH session.

This module provides no authorization, peer authentication or board acceptance.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
from .functional50_board_a import validate_io
from .functional50_ssh_a import Session
from ...integration.host_clock import QpcHostClock

from .functional50_b131_loader import _Bundle, load_selected, _PINS, _DEPS, _sha, _need

def _observation(intent,status,value):
    _need(type(intent) is dict and type(intent.get('operation_id')) is str and type(intent.get('call_id')) is int,'original intent identity')
    _need(status in ('confirmed_read','confirmed_write','unknown','not_attempted'),'observation kind')
    if status=='confirmed_read':_need(intent.get('kind')=='read' and type(value) is int and 0<=value<=0xffffffff,'read response')
    elif status=='confirmed_write':_need(intent.get('kind')=='write' and value is None,'write response')
    else:_need(value is None,'unknown response')
    return dict(operation_id=intent['operation_id'],call_id=intent['call_id'],status=status,value=value,error_code=None)

def _validate_intent(i,operation):
    keys={'operation_id','call_id','kind','offset','value','label','poll','window','phase','reserve_and_persist_before_effect_bytes','phase_deadline_ns'}
    _need(type(i) is dict and set(i)==keys and i['operation_id']==operation and type(i['call_id']) is int and i['call_id']>0,'intent identity')
    _need(i['window']=='TRACE_HWH_RELATIVE' and i['phase'] in ('work','cleanup') and type(i['poll']) is bool and type(i['label']) is str and len(i['label'])<=96,'intent boundary')
    _need(i['reserve_and_persist_before_effect_bytes']==2048 and type(i['phase_deadline_ns']) is int and i['phase_deadline_ns']>0,'intent reservation')
    validate_io(i['kind'],i['offset'],i['value'])

def _preflight_trace_compatibility():
    # The unchanged B131 reducer uses 0x034 for prior RX-total headroom.
    reads=(0,4,8,12,16,20,0x18,0x1c,0x20,0x24,0x28,0x2c,0x30,0x34,0x38,0x40,0x44,0x48,0x4c,0x50,0x60,0x64,0x68,0x6c,0x70,0x7c)
    writes=(0x100,0x104,0x108,0x110,0x114,0x118,0x11c,0x120,*range(0x130,0x158,4),0x160,0x164)
    for offset in reads:validate_io('read',offset,None)
    for offset in writes:validate_io('write',offset,0)
    for command in (1,2,3,4,5,8):validate_io('write',0x80,command)
def _put(path,data):
    _need(type(data) is bytes,'exact evidence bytes')
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())

def _raw(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

class Exchange:
    """Single original session/operation; reducer output never authorizes effects."""
    def __init__(self,bundle,session,clock,request_bytes,source_bytes,companions,*,build_binding,timeout_ns):
        _need(type(bundle) is _Bundle and type(session) is Session and type(clock) is QpcHostClock and session._clock is clock,'fixed B131/session/QPC required')
        _need(type(timeout_ns) is int and 0<timeout_ns<=10_000_000_000,'bounded request timeout')
        session._check()
        _preflight_trace_compatibility()
        _need(type(build_binding) is dict and build_binding.get('operation_id')==session._dir.name,'original operation directory mismatch')
        prepared=bundle.adapter.prepare_bytes(request_bytes,source_bytes,companions,build_binding=build_binding)
        self.bundle,self.session,self.clock=bundle,session,clock
        self.thread=threading.get_ident();self.timeout_ns=timeout_ns;self.failed=False;self.started=False;self.collected=False;self.cleaned=False
        self.directory=session._dir/'b131-exchange';self.directory.mkdir(mode=0o700)
        original=prepared.original
        for name,data in [('request.bin',original.request),('source.bin',original.source),*[(f'companion-{i}.bin',v) for i,v in enumerate(original.companions)]]:_put(self.directory/name,data)
        _put(self.directory/'preparation.json',_raw(dict(status=prepared.status,reason=prepared.reason,build_binding=build_binding,inventory=original.inventory(),authority='not_evaluated')))
        self.prepared=prepared
        self.reducer=None if prepared.plan is None else bundle.reducer.Reducer(prepared.plan)
        self.work_origin=None;self.cleanup_origin=None
        self._used={'work':sum(x.stat().st_size for x in self.directory.iterdir()),'cleanup':0}
    def _check(self):
        _need(threading.get_ident()==self.thread and not self.failed and self.reducer is not None,'original active exchange required')
        self.session._check()
    def _elapsed(self,phase):
        now=self.clock();origin=self.work_origin if phase=='work' else self.cleanup_origin
        _need(type(origin) is int and now>=origin,'original phase clock')
        return now-origin
    def _drive(self,phase):
        r=self.reducer;intent=r.advance(phase_elapsed_ns=self._elapsed(phase))
        while intent is not None:
            try:
                _validate_intent(intent,r.operation_id)
                index=intent['call_id'];reservation=self.directory/('intent-%05d.bin'%index)
                raw=_raw(intent);_need(len(raw)<=1023,'intent evidence exceeds reserved bound')
                _need(self._used[phase]+2048+12288<=r.limits[phase+'_evidence'],'actual evidence headroom exhausted')
                _put(reservation,raw+b'\n'+b'\0'*(2047-len(raw)))
                self._used[phase]+=2048
            except BaseException:
                self.failed=True
                try:r.advance(_observation(intent,'not_attempted',None),phase_elapsed_ns=self._elapsed(phase))
                except BaseException:pass
                raise
            try:
                receipt=self.session.request('b131-%05d'%index,intent['kind'],intent['offset'],intent['value'],timeout_ns=self.timeout_ns)
            except BaseException as error:
                self.failed=True
                obs=_observation(intent,'unknown',None)
                self._record_outcome(reservation,dict(observation=obs,error=type(error).__name__,remote_effect='unknown'))
                try:r.advance(obs,phase_elapsed_ns=self._elapsed(phase))
                except BaseException:pass
                try:self._save_snapshot('unknown-%05d.json'%index)
                except BaseException:pass
                raise
            obs=_observation(intent,'confirmed_read' if intent['kind']=='read' else 'confirmed_write',receipt['returned'])
            try:
                self._record_outcome(reservation,dict(observation=obs,lower_qpc_ns=receipt['lower_qpc_ns'],upper_qpc_ns=receipt['upper_qpc_ns'],raw_response_hex=receipt['raw_response'].hex()))
                n=self.session._quota.count
                self._used[phase]+=sum((self.session._dir/('request-%04d-%s.json'%(n,k))).stat().st_size for k in ('started','returned'))
                _need(self._used[phase]<=r.limits[phase+'_evidence'],'actual evidence budget exhausted')
                intent=r.advance(obs,phase_elapsed_ns=self._elapsed(phase))
            except BaseException:
                self.failed=True;raise
    def _record_outcome(self,reservation,record):
        raw=_raw(record)
        _need(len(raw)<=1023,'outcome exceeds reserved bound; preserve session raw')
        with reservation.open('r+b') as f:
            f.seek(1024);f.write(raw+b'\n');f.flush();os.fsync(f.fileno())
    def scan(self):
        self._check();_need(not self.started,'one ARM scan only')
        self.started=True;self.work_origin=self.clock();self.reducer.begin();self._drive('work')
        self._save_snapshot('scan.json')
        return self.snapshot()
    def collect(self):
        self._check();_need(self.started and not self.collected,'one collection only')
        self.collected=True;self.reducer.begin_collect()
        phase=self.reducer.phase
        if phase=='cleanup' and self.cleanup_origin is None:self.cleanup_origin=self.clock()
        self._drive(phase);self._save_snapshot('collection.json');snap=self.snapshot()
        if snap['completed'] and not snap['failed'] and snap['outstanding_intent'] is None:
            original=self.prepared.original
            correlation=self.bundle.adapter.correlate_collected(self.prepared.plan,snap['confirmed_wire_prefix'],original.companions,snap['results'])
            _put(self.directory/'collected-wire.bin',snap['confirmed_wire_prefix'])
            facts={k:v for k,v in correlation.items() if k!='retained'}
            _put(self.directory/'correlation.json',_raw(facts))
            return correlation
        return snap
    def cleanup(self):
        self._check();_need(self.started and not self.cleaned,'one cleanup only')
        self.cleaned=True
        if self.cleanup_origin is None:self.cleanup_origin=self.clock()
        self.reducer.begin_cleanup();self._drive('cleanup')
        self._save_snapshot('cleanup.json')
        return self.snapshot()
    def _save_snapshot(self,name):
        snap=self.reducer.snapshot()
        safe={k:v for k,v in snap.items() if k not in ('original','events','confirmed_wire_prefix')}
        safe['confirmed_wire_prefix_hex']=snap['confirmed_wire_prefix'].hex()
        _put(self.directory/name,_raw(safe))
    def snapshot(self):
        _need(threading.get_ident()==self.thread,'original owner thread required')
        return None if self.reducer is None else self.reducer.snapshot()
