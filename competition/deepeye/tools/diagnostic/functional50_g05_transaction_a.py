"""One same-process G05P transaction; raw observations, no authority grant."""
from dataclasses import dataclass
from pathlib import Path
import os
import threading
import time
import uuid
from . import functional50_board_a as board
from . import functional50_g05_a as g05

_SCHEMA='g05_csr_transaction_v1'
_ISSUERS={}

def _need(ok,msg):
    if not ok:raise ValueError(msg)

@dataclass(frozen=True)
class Limits:
    max_commands:int
    max_polls:int
    duration_ns:int
    def __post_init__(self):
        _need(type(self.max_commands) is int and 1<=self.max_commands<=16,'1..16 commands required')
        _need(type(self.max_polls) is int and 1<=self.max_polls<=1024,'bounded polls required')
        _need(type(self.duration_ns) is int and 0<self.duration_ns<=10_000_000_000,'bounded duration required')

@dataclass(frozen=True)
class IOReceipt:
    index:int
    started_raw:bytes
    returned_raw:bytes

@dataclass(frozen=True)
class CaptureFacts:
    status_before_latch:int
    fault_before_latch:int
    words32:tuple
    status_before_snapshot:int
    status_after_snapshot:int
    result_seq:int
    tick_unit:str='50MHz_cycles'

@dataclass(frozen=True)
class TransactionFacts:
    schema:str
    operation_id:str
    policy_sha256:str
    identity_words:tuple
    captures:tuple
    deadline_selected_lower_board_monotonic_ns:int
    deadline_board_monotonic_ns:int
    stop_status:int | None
    stop_fault:int | None
    receipts:tuple
    authority:str='not_evaluated'

class TransactionIssuer:
    """Strongly retain exact original ports; never replay or auto-stop a failure."""
    def __init__(self,trace,port,limits):
        _need(type(trace) is board._TracePort and type(port) is g05.G05Port and type(limits) is Limits,'exact original ports and limits required')
        _need(board._G05_PORTS.get(trace) is port and board._G05_LOADS.get(trace) is port._reg and port._trace is trace and trace in board._G05_CLAIMED,'registered same-load G05/TRACE required')
        _need(port._mmio.device is port._reg[0] and port._reg[7] is trace._mmio and port._thread==threading.get_ident() and port._reg[8]==threading.get_ident() and port._pid==os.getpid(),'same device/thread/process required')
        port._check()
        _need(not port._bound and not port._stopped and port._identity is None and port._staged is None and all(x==0 for x in port._used.values()),'fresh unconsumed G05 required')
        _need(port not in _ISSUERS,'one issuer per original G05')
        self.trace,self.port,self.limits=trace,port,limits
        self.thread=threading.get_ident();self.operation_id=dict(port._reg[3])['operation_id'];self.policy_sha256=port._policy['policy_sha256']
        self._issued=False;self._step_number=0;self._receipts=[];self._deadline=None
        _ISSUERS[port]=self
        self.directory=port._dir/'transaction';self.directory.mkdir(mode=0o700)
    def _check(self):
        _need(threading.get_ident()==self.thread and _ISSUERS.get(self.port) is self,'original issuer thread/identity required')
        _need(board._G05_PORTS.get(self.trace) is self.port and board._G05_LOADS.get(self.trace) is self.port._reg,'original registration changed')
        self.port._check()
    def _receipt(self,index,expected_id=None):
        data=[]
        for suffix in ('started','returned'):
            p=self.port._dir/('g05-%05d-%s.json'%(index,suffix));raw=p.read_bytes()
            _need(0<len(raw)<=4096,'bounded original G05 I/O evidence required');data.append(raw)
        started,returned=(board._json(raw) for raw in data)
        _need(type(started) is dict and type(returned) is dict and started.get('io')==returned.get('io')==index and started.get('request_id')==returned.get('request_id') and started.get('kind')==returned.get('kind') and started.get('pid')==self.port._pid,'original I/O record identity mismatch')
        _need(expected_id is None or started['request_id']==expected_id,'original I/O request changed')
        return IOReceipt(index,*data)
    def _step(self,name,*args):
        self._check();now=time.monotonic_ns();_need(now<self._deadline,'transaction deadline expired before intent')
        self._step_number+=1;n=self._step_number;request_id='tx-'+uuid.uuid4().hex
        board._record(self.directory,'step-%05d-started.json'%n,dict(step=n,method=name,request_id=request_id,monotonic_ns=now))
        now=time.monotonic_ns()
        if now>=self._deadline:
            board._record(self.directory,'step-%05d-not-attempted.json'%n,dict(step=n,request_id=request_id,monotonic_ns=now))
            raise TimeoutError('deadline expired after intent; original port not called')
        before=self.port._count
        # Each fixed high-level method may itself perform multiple MMIO calls;
        # no per-MMIO deadline or hard timeout is asserted here.
        method=getattr(self.port,name)
        result=method(*args,request_id)
        after=self.port._count
        _need(type(after) is int and after>before,'original G05 I/O receipt missing')
        for i in range(before+1,after+1):self._receipts.append(self._receipt(i,request_id))
        board._record(self.directory,'step-%05d-returned.json'%n,dict(step=n,request_id=request_id,first_io=before+1,last_io=after,monotonic_ns=time.monotonic_ns()))
        return result
    def run(self,identity_words,commands,*,stop=False):
        self._check();_need(not self._issued,'one transaction per original issuer')
        _need(type(stop) is bool,'explicit STOP choice required')
        identity=g05._identity(identity_words)
        _need(type(commands) is tuple and 1<=len(commands)<=self.limits.max_commands,'bounded immutable commands required')
        last=0;profile=None
        for cmd in commands:
            g05._command(cmd,last,profile);last,profile=cmd[5],cmd[2]
        quotas=self.port._policy['limits'];n=len(commands)
        _need(quotas['begin']>=1 and (not stop or quotas['stop']>=1) and all(quotas[k]>=n for k in ('commit','latch','release')),'original G05 policy insufficient')
        self._issued=True;start=time.monotonic_ns();self._deadline=start+self.limits.duration_ns
        board._record(self.directory,'transaction-started.json',dict(schema=_SCHEMA,operation_id=self.operation_id,policy_sha256=self.policy_sha256,monotonic_ns=start,deadline_board_monotonic_ns=self._deadline,max_commands=n,max_polls=self.limits.max_polls,duration_ns=self.limits.duration_ns,stop_requested=stop,authority='not_evaluated'))
        self.port._bind_deadline(g05._DEADLINE_KEY,self._deadline)
        # Retain original mapping/identity reads from the same G05 factory too.
        for i in range(1,self.port._count+1):self._receipts.append(self._receipt(i))
        self._step('stage_identity',identity);self._step('begin')
        actual=tuple(self._step('read32',0x100+4*i) for i in range(13))
        _need(actual==identity,'actual private identity readback mismatch')
        captures=[];polls=0
        for cmd in commands:
            self._step('stage_command',cmd);self._step('commit')
            while True:
                _need(polls<self.limits.max_polls,'capture polling budget exhausted');polls+=1
                status=self._step('read32',0x08);fault=self._step('read32',0x10)
                g05._status_check(status,fault,'bound')
                if status&0x10:break
            self._step('latch');snap=self._step('read_snapshot');self._step('release')
            words=snap['words'];_need(type(words) is tuple and len(words)==32 and words[1]==cmd[5] and words[2]==cmd[6],'actual captured command/tag mismatch')
            captures.append(CaptureFacts(status,fault,words,snap['status_before'],snap['status_after'],snap['result_seq']))
        stop_status=stop_fault=None
        if stop:
            self._step('stop')
            stop_status=self._step('read32',0x08);stop_fault=self._step('read32',0x10)
        facts=TransactionFacts(_SCHEMA,self.operation_id,self.policy_sha256,actual,tuple(captures),start,self._deadline,stop_status,stop_fault,tuple(self._receipts))
        board._record(self.directory,'transaction-returned.json',dict(schema=_SCHEMA,operation_id=self.operation_id,captures=len(captures),stop_status=stop_status,stop_fault=stop_fault,monotonic_ns=time.monotonic_ns(),authority='not_evaluated',remote_or_physical_stop_proven=False))
        return facts
