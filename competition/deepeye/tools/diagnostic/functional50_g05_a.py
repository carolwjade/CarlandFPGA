"""Opt-in same-load private G05P CSR endpoint; not BOOT/STATE8 authority."""
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from types import MappingProxyType
from . import functional50_board_a as board

# Exact G05P mapper ROM d462859e6893cd90fb33ad9ddd481aaa7ee46937ba3d197431f81b602357a83c.
_ROM=((0,128234,512938,1154111,2051753,3205865,4616446,6283496,8207015,10387004,12823462,15516389,18465785,21671651,25133986,28852790,32828063,37059806,41548017,46292698,51293849),
      (0,8,32,73,131,205,295,402,525,664,820,993,1181,1386,1608,1846,2100,2371,2659,2962,3282))
_MAX={'begin':1,'commit':16,'stop':1,'latch':16,'release':16,'total_io':2048}
_READ=frozenset((0,4,8,0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x40,0x44,0x48,0x4c,*range(0x100,0x134,4),*range(0x200,0x21c,4),*range(0x300,0x380,4)))
_KEY=object()
_DEADLINE_KEY=object()

def _need(ok,msg):
    if not ok:raise ValueError(msg)

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')

def _policy(raw,binding):
    doc=board._json(raw)
    _need(type(doc) is dict and set(doc)=={'binding','limits','policy_sha256'},'exact G05 policy')
    _need(type(doc['binding']) is dict and doc['binding']==binding,'same load policy binding')
    limits=doc['limits'];_need(type(limits) is dict and set(limits)==set(_MAX),'exact finite quotas')
    _need(all(type(limits[k]) is int and 0<=limits[k]<=v for k,v in _MAX.items()) and limits['total_io']>0,'bounded G05 quotas')
    digest=doc['policy_sha256'];_need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,'policy hash')
    _need(hashlib.sha256(_canonical(dict(binding=doc['binding'],limits=limits))).hexdigest()==digest,'policy hash mismatch')
    return doc

def _status_check(status,fault,mode):
    _need(type(status) is int and 0<=status<=0x7f and type(fault) is int and fault==0,'G05 status/fault')
    if mode=='new':_need(status==0,'G05 must start unbound')
    elif mode=='bound':_need(status&1 and not status&2,'G05 bound and live required')
    elif mode=='latched':_need(status&0x21==0x21 and not status&2,'G05 live latch required')
    else:raise ValueError('status mode')

def _command(words,last_cmd,locked_profile):
    _need(type(words) is tuple and len(words)==7 and all(type(v) is int and 0<=v<=0xffffffff for v in words),'seven exact unsigned command words')
    y,p,profile,speed,ttl,seq,tag=words
    _need(y<=0xffff and p<=0xffff and profile in (1,2) and speed<=20 and 1<=ttl<=(3000 if profile==1 else 12000),'G05 encoding and profile')
    y=y if y<0x8000 else y-65536;p=p if p<0x8000 else p-65536
    _need(-15000<=y<=15000 and -15000<=p<=15000 and (speed!=0 or (y==0 and p==0)),'G05 target bounds')
    _need(y*y+p*p<=_ROM[profile-1][speed] and seq>last_cmd and (locked_profile is None or locked_profile==profile),'G05 curvature, sequence or locked profile')
    return words

def _identity(words):
    _need(type(words) is tuple and len(words)==13 and all(type(v) is int and 0<=v<=0xffffffff for v in words),'13 unsigned identity words required')
    _need(any(words[:8]) and any(words[8:12]) and words[12]!=0,'nonzero original run/nonce/session')
    return words

class G05Port:
    def __init__(self,key,trace,reg,mmio,directory,policy):
        _need(key is _KEY,'original G05 factory required')
        self._trace,self._reg,self._mmio,self._dir=trace,reg,mmio,directory
        self._policy=MappingProxyType({'binding':MappingProxyType(dict(policy['binding'])),'limits':MappingProxyType(dict(policy['limits'])),'policy_sha256':policy['policy_sha256']})
        self._thread=threading.get_ident();self._pid=os.getpid();self._failed=False;self._count=0;self._ids=set();self._seq=0;self._profile=None;self._identity=None;self._staged=None;self._bound=False;self._stopped=False
        self._used={k:0 for k in _MAX if k!='total_io'};self._deadline_ns=None
    def _check(self):
        _need(threading.get_ident()==self._thread and os.getpid()==self._pid and not self._failed,'original owner or failed G05')
        _need(board._G05_LOADS.get(self._trace) is self._reg and self._trace in board._G05_CLAIMED and not self._trace._failed and self._trace._mmio is self._reg[7] and self._trace._mmio.device is self._reg[0],'original same-load association changed')
        _need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==self._trace._boot,'boot changed')
    def _bind_deadline(self,key,deadline_ns):
        """Issuer-only, fixed one-use board monotonic deadline; no renewal."""
        self._check()
        _need(key is _DEADLINE_KEY and self._deadline_ns is None,'one original deadline binding required')
        now=time.monotonic_ns()
        _need(type(deadline_ns) is int and now<deadline_ns<=now+10_000_000_000,'future deadline within 10 seconds required')
        self._deadline_ns=deadline_ns
        try:
            board._record(self._dir,'g05-deadline-bound.json',dict(lower_monotonic_ns=now,deadline_monotonic_ns=deadline_ns))
            if time.monotonic_ns()>=deadline_ns:raise TimeoutError('deadline expired during binding')
        except BaseException:
            self._failed=True;raise
    def _claim(self,request_id):
        self._check();_need(type(request_id) is str and re.fullmatch('[A-Za-z0-9_-]{1,64}',request_id) is not None and request_id not in self._ids,'fresh request ID required')
        self._ids.add(request_id)
    def _io(self,kind,offset,value,request_id):
        self._check();_need(type(offset) is int and offset%4==0,'aligned G05 word')
        if kind=='read':_need(offset in _READ and value is None,'G05 read refused')
        else:
            _need(kind=='write' and (offset==0x00c or offset in range(0x100,0x134,4) or offset in range(0x200,0x21c,4)) and type(value) is int and 0<=value<=0xffffffff,'G05 write refused')
            if offset==0x00c:_need(value in (1,2,3,4,5),'G05 control refused')
        _need(self._count<self._policy['limits']['total_io'],'G05 total I/O cap');self._count+=1;n=self._count
        try:
            board._record(self._dir,'g05-%05d-started.json'%n,dict(request_id=request_id,io=n,kind=kind,offset=offset,value=value,pid=self._pid,monotonic_ns=time.monotonic_ns()))
            if self._deadline_ns is not None:
                checked=time.monotonic_ns()
                if checked>=self._deadline_ns:
                    board._record(self._dir,'g05-%05d-not-attempted.json'%n,dict(request_id=request_id,io=n,monotonic_ns=checked))
                    raise TimeoutError('G05 deadline passed before MMIO; not attempted')
            result=self._mmio.read(offset) if kind=='read' else self._mmio.write(offset,value)
            if kind=='read':_need(type(result) is int and 0<=result<=0xffffffff,'actual read word required')
            else:_need(result is None,'actual write result invalid')
            board._record(self._dir,'g05-%05d-returned.json'%n,dict(request_id=request_id,io=n,kind=kind,value=result,monotonic_ns=time.monotonic_ns()))
            return result
        except BaseException:
            self._failed=True;raise
    def _status(self,request_id,mode):
        status=self._io('read',8,None,request_id);fault=self._io('read',0x10,None,request_id)
        try:_status_check(status,fault,mode)
        except BaseException:self._failed=True;raise
        return status
    def _quota(self,name):
        _need(self._used[name]<self._policy['limits'][name],'G05 command quota');self._used[name]+=1
    def read32(self,offset,request_id):
        self._claim(request_id)
        if type(offset) is int and 0x300<=offset<=0x37c:self._status(request_id,'latched')
        return self._io('read',offset,None,request_id)
    def stage_identity(self,words,request_id):
        words=_identity(words);self._claim(request_id);_need(not self._bound and not self._stopped and self._identity is None,'identity stage one use')
        self._status(request_id,'new')
        for i,w in enumerate(words):self._io('write',0x100+4*i,w,request_id)
        self._identity=words
    def begin(self,request_id):
        self._claim(request_id);_need(self._identity is not None and not self._bound and not self._stopped,'staged initial identity required')
        self._status(request_id,'new');self._quota('begin');self._io('write',0x00c,1,request_id)
        self._status(request_id,'bound');self._bound=True
    def stage_command(self,words,request_id):
        words=_command(words,self._seq,self._profile);self._claim(request_id)
        _need(self._bound and not self._stopped and self._staged is None,'live unstaged command required')
        status=self._status(request_id,'bound');_need(not status&0x68,'G05 pending/inflight/latch')
        for i,w in enumerate(words):self._io('write',0x200+4*i,w,request_id)
        self._staged=words
    def commit(self,request_id):
        self._claim(request_id);_need(self._bound and not self._stopped and self._staged is not None,'staged command required')
        status=self._status(request_id,'bound');_need(not status&0x68,'G05 pending/inflight/latch')
        self._quota('commit');command=self._staged;self._staged=None
        self._io('write',0x00c,2,request_id)
        actual=self._io('read',0x14,None,request_id);self._status(request_id,'bound')
        if actual!=command[5]:self._failed=True;raise ValueError('original command acceptance not observed')
        self._seq,self._profile=command[5],command[2]
    def latch(self,request_id):
        self._claim(request_id);_need(self._bound and not self._stopped,'live G05 required')
        status=self._status(request_id,'bound');_need(status&0x10 and not status&0x20,'eligible unlatch result required')
        self._quota('latch');self._io('write',0x00c,4,request_id);self._status(request_id,'latched')
    def read_snapshot(self,request_id):
        self._claim(request_id);_need(self._bound and not self._stopped,'live G05 required')
        before=self._status(request_id,'latched');seq_before=self._io('read',0x1c,None,request_id)
        words=tuple(self._io('read',0x300+4*i,None,request_id) for i in range(32))
        seq_after=self._io('read',0x1c,None,request_id);after=self._status(request_id,'latched')
        if words[31]!=0x47303550 or words[30]!=self._identity[12] or words[0]!=seq_before or seq_before!=seq_after:
            self._failed=True;raise ValueError('original latched record association changed')
        return dict(words=words,status_before=before,status_after=after,result_seq=seq_after,
                    tick_unit='50MHz_cycles',native_atomic_interval=False,authority='not_evaluated')
    def release(self,request_id):
        self._claim(request_id);self._status(request_id,'latched');self._quota('release');self._io('write',0x00c,5,request_id)
        status=self._status(request_id,'bound')
        if status&0x20:self._failed=True;raise ValueError('latch release not observed')
    def stop(self,request_id):
        self._claim(request_id);_need(not self._stopped,'STOP already consumed');self._quota('stop');self._stopped=True
        self._io('write',0x00c,3,request_id)
        # No success, retirement, or physical stopped assertion from a write alone.

def open_g05(trace,policy_path):
    """Explicit one-use same-load mapping; no legacy authority or auto-retry."""
    _need(type(trace) is board._TracePort and trace in board._G05_LOADS and trace not in board._G05_CLAIMED,'original registered loader trace required')
    reg=board._G05_LOADS[trace];device,mmio_type,spans,binding,parser,hwh,pid,trace_mmio,loader_thread=reg
    _need(pid==os.getpid()==trace._pid and loader_thread==threading.get_ident() and trace._mmio is trace_mmio and trace_mmio.device is device and not trace._failed,'original same-device/pid/thread required')
    _need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==trace._boot,'original boot required')
    raw,_=board._bytes(policy_path,131072);policy=_policy(raw,dict(binding))
    _need(spans[0][1]-spans[0][0]==4095 and spans[1][1]-spans[1][0]==4095 and (spans[0][1]<spans[1][0] or spans[1][1]<spans[0][0]),'original HWH aperture')
    board._G05_CLAIMED.add(trace)  # Reserve before any creation/mapping effect.
    directory=trace._dir/('g05-'+policy['policy_sha256'][:24]);directory.mkdir(mode=0o700)
    with (directory/'policy.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    board._record(directory,'g05-map-started.json',dict(policy_sha256=policy['policy_sha256'],g05_base=spans[0][0],pid=pid))
    mmio=mmio_type(spans[0][0],4096,device=device)
    _need(mmio.device is device and mmio.base_addr==spans[0][0] and mmio.length==4096,'mapped original G05 window')
    board._record(directory,'g05-map-returned.json',dict(pid=pid))
    port=G05Port(_KEY,trace,reg,mmio,directory,policy)
    board._G05_PORTS[trace]=port  # Strong retention even when a later identity call fails.
    try:
        magic=port.read32(0,'factory-magic');layout=port.read32(4,'factory-layout')
        _need(magic==0x47303550 and layout==2,'actual G05P identity mismatch')
        port._status('factory-status','new')
        return port
    except BaseException:
        port._failed=True
        raise
