"""Default two-command G05P session; explicit typed demo allows four; no authority."""
from dataclasses import dataclass
import threading
import time
from . import functional50_board_a as board
from . import functional50_g05_a as g05
from . import functional50_g05_transaction_a as transaction
from . import functional50_demo_four_cycle_profile_a as demo

_SESSIONS={}
_SCHEMA='g05_csr_session_v2'

def _need(ok,msg):
    if not ok:raise ValueError(msg)

@dataclass(frozen=True)
class UnresolvedIO:
    index:int
    started_raw:bytes | None
    returned_raw:bytes | None
    not_attempted_raw:bytes | None
@dataclass(frozen=True)
class HeldCaptureFactsV2:
    status_before_latch:int
    fault_before_latch:int
    words32:tuple
    status_before_snapshot:int
    status_after_snapshot:int
    result_seq:int
    held_before_seq:int
    held_after_seq:int
    latest_before_seq:int
    latest_after_seq:int
    tick_unit:str='50MHz_cycles'
    capture_kind:str='g05_held_bank_v2'
@dataclass(frozen=True)
class SessionFacts:
    schema:str
    kind:str
    operation_id:str
    policy_sha256:str
    deadline_selected_lower_board_monotonic_ns:int
    deadline_board_monotonic_ns:int
    phase_io_first:int | None
    phase_io_last:int | None
    identity_words:tuple | None
    status:int | None
    fault:int | None
    capture:transaction.CaptureFacts | None
    receipts:tuple
    unresolved_receipts:tuple
    state:str
    authority:str='not_evaluated'

class G05SessionV2:
    """One init and selected finite commands; no callbacks or time renewal."""
    def __init__(self,issuer,*,demo_cycle_profile=None):
        _need(type(issuer) is transaction.TransactionIssuer and transaction._ISSUERS.get(issuer.port) is issuer,'exact original issuer required')
        issuer._check()
        _need(not issuer._issued and issuer not in _SESSIONS,'fresh one-use issuer required')
        demo.validate_profile(demo_cycle_profile)
        _need(1<=issuer.limits.max_commands<=demo.command_cap(demo_cycle_profile) and 1<=issuer.limits.max_polls<=demo.poll_cap(demo_cycle_profile) and issuer.limits.duration_ns<=demo.duration_cap(demo_cycle_profile),'session v2 finite limits')
        if demo.is_navigation(demo_cycle_profile):
            _need(issuer.limits.demo_cycle_profile==demo_cycle_profile,'same typed navigation issuer/session required')
        quotas=issuer.port._policy['limits'];n=issuer.limits.max_commands
        if demo_cycle_profile is not None:
            prospective=demo.validate_caps(demo_cycle_profile,max_commands=n,max_polls=issuer.limits.max_polls,
                duration_ns=issuer.limits.duration_ns,max_io=quotas['total_io'])
            _need(prospective<=quotas['total_io']<=demo.io_cap(demo_cycle_profile),'selected original I/O ledger must cover prospective budget')
        _need(quotas['begin']>=1 and all(quotas[k]>=n for k in ('commit','latch','release')),'G05 policy insufficient for selected session')
        self.issuer=issuer;self.thread=threading.get_ident();self._state='NEW';self._identity=None;self._polls=0;self._commands=0;self._start=None;self._phase=0
        self._demo_cycle_profile=demo_cycle_profile;self._capture_polls=0;self._total_status_reads=0
        self._status_phases=0
        self._status_limit=issuer.limits.max_polls if demo_cycle_profile is None else demo_cycle_profile.total_status_reads
        _SESSIONS[issuer]=self
    def _owner(self):
        _need(threading.get_ident()==self.thread and _SESSIONS.get(self.issuer) is self,'original session owner required')
        _need(transaction._ISSUERS.get(self.issuer.port) is self.issuer and board._G05_PORTS.get(self.issuer.trace) is self.issuer.port and board._G05_LOADS.get(self.issuer.trace) is self.issuer.port._reg,'same original port association required')
    def _active(self):
        self._owner();_need(self._state=='ACTIVE','active original session required');self.issuer._check()
    def _open_phase(self,kind):
        self._phase+=1;n=self._phase;before=self.issuer.port._count
        board._record(self.issuer.directory,'session-%03d-started.json'%n,dict(schema=_SCHEMA,kind=kind,phase=n,first_possible_io=before+1,monotonic_ns=time.monotonic_ns()))
        return n,before
    def _unresolved(self):
        completed={r.index for r in self.issuer._receipts}
        out=[]
        for i in range(1,self.issuer.port._count+1):
            if i in completed:continue
            raws=[]
            for suffix in ('started','returned','not-attempted'):
                path=self.issuer.port._dir/('g05-%05d-%s.json'%(i,suffix))
                if not path.exists():raws.append(None);continue
                raw=path.read_bytes();_need(0<len(raw)<=4096,'bounded original unresolved evidence required');raws.append(raw)
            out.append(UnresolvedIO(i,*raws))
        return tuple(out)
    def _facts(self,n,before,kind,*,identity=None,status=None,fault=None,capture=None,state='ACTIVE'):
        end=self.issuer.port._count
        board._record(self.issuer.directory,'session-%03d-returned.json'%n,dict(schema=_SCHEMA,kind=kind,phase=n,first_io=before+1 if end>before else None,last_io=end if end>before else None,monotonic_ns=time.monotonic_ns(),authority='not_evaluated'))
        return SessionFacts(_SCHEMA,kind,self.issuer.operation_id,self.issuer.policy_sha256,self._start,self.issuer._deadline,before+1 if end>before else None,end if end>before else None,identity,status,fault,capture,tuple(self.issuer._receipts),self._unresolved(),state)
    def _step(self,name,*args):
        # Count even the status reads hidden inside original 197 high-level methods.
        costs={'stage_identity':1,'begin':2,'stage_command':1,'commit':2,
               'latch':2,'read_snapshot':2,'read_snapshot_v2':2,'release':2,'stop':0}
        cost=(1 if name=='read32' and args[0]==0x08 else 0) if name=='read32' else costs[name]
        if self._demo_cycle_profile is not None and name=='read32' and 0x300<=args[0]<=0x37c:cost=1
        _need(self._polls+cost<=self._status_limit,'session status-read budget exhausted')
        self._polls+=cost
        if self._demo_cycle_profile is None:return self.issuer._step(name,*args)
        before=self.issuer.port._count
        result=self.issuer._step(name,*args)
        # Real successful MMIO ledger, including status reads hidden in fixed
        # high-level methods. Unknown attempts retain their original raw files.
        actual=0
        for receipt in self.issuer._receipts[before:]:
            if receipt.index>before:
                request=board._json(receipt.started_raw)
                if request['kind']=='read' and request['offset']==8:actual+=1
        _need(actual==cost,'hidden status-read accounting mismatch')
        self._total_status_reads+=actual
        _need(self._total_status_reads==self._polls<=self._status_limit,'total actual status-read cap')
        return result
    def _actual_identity(self):
        return tuple(self._step('read32',0x100+4*i) for i in range(13))
    def _live_status(self):
        status=self._step('read32',0x08);fault=self._step('read32',0x10)
        g05._status_check(status,fault,'bound');return status,fault
    def init(self,identity_words):
        self._owner();_need(self._state=='NEW' and not self.issuer._issued,'one original init only')
        identity=g05._identity(identity_words);self.issuer._check()
        _need(self._polls+4<=self._status_limit,'insufficient status-read budget for init')
        self._state='BUSY';self.issuer._issued=True
        try:
            self._start=time.monotonic_ns();self.issuer._deadline=self._start+self.issuer.limits.duration_ns
            journal=dict(schema=_SCHEMA,operation_id=self.issuer.operation_id,policy_sha256=self.issuer.policy_sha256,monotonic_ns=self._start,deadline_board_monotonic_ns=self.issuer._deadline,max_commands=self.issuer.limits.max_commands,max_polls=self.issuer.limits.max_polls,authority='not_evaluated')
            if self._demo_cycle_profile is not None:journal['demo_cycle_profile']=demo.to_wire(self._demo_cycle_profile)
            board._record(self.issuer.directory,'transaction-started.json',journal)
            self.issuer.port._bind_deadline(g05._DEADLINE_KEY,self.issuer._deadline,demo_cycle_profile=self._demo_cycle_profile)
            for i in range(1,self.issuer.port._count+1):self.issuer._receipts.append(self.issuer._receipt(i))
            n,before=self._open_phase('init')
            self._step('stage_identity',identity);self._step('begin')
            actual=self._actual_identity();_need(actual==identity,'actual identity mismatch')
            status,fault=self._live_status();self._identity=actual
            result=self._facts(n,before,'init',identity=actual,status=status,fault=fault)
            self._state='ACTIVE';return result
        except BaseException:self._state='FAILED';raise
    def apply_one(self,command_words):
        self._active();_need(self._commands<self.issuer.limits.max_commands,'session command quota exhausted')
        g05._command(command_words,self.issuer.port._seq,self.issuer.port._profile,build_id=self.issuer.port._policy['binding']['build_id'])
        if demo.is_navigation(self._demo_cycle_profile):
            _need(command_words[2]==1,'navigation uses unchanged FAST TTL/ROM')
        _need(self._polls+10<=self._status_limit,'insufficient status-read budget for one capture')
        self._state='BUSY';self._commands+=1
        try:
            n,before=self._open_phase('apply')
            actual=self._actual_identity();_need(actual==self._identity,'original identity changed')
            self._step('stage_command',command_words);self._step('commit')
            while True:
                _need(self._polls+7<=self._status_limit,'insufficient status-read budget for poll and latch')
                if self._demo_cycle_profile is not None:
                    _need(self._capture_polls<self.issuer.limits.max_polls,'capture-poll quota exhausted')
                    self._capture_polls+=1
                status,fault=self._live_status()
                if status&0x10:break
            self._step('latch')
            snap=self._step('read_snapshot_v2' if demo.is_navigation(self._demo_cycle_profile) else 'read_snapshot')
            self._step('release')
            words=snap['words'];_need(type(words) is tuple and len(words)==32 and words[1]==command_words[5] and words[2]==command_words[6],'actual captured command/tag mismatch')
            if demo.is_navigation(self._demo_cycle_profile):
                capture=HeldCaptureFactsV2(status,fault,words,snap['status_before'],snap['status_after'],snap['result_seq'],
                    snap['held_before_seq'],snap['held_after_seq'],snap['latest_before_seq'],snap['latest_after_seq'])
            else:
                capture=transaction.CaptureFacts(status,fault,words,snap['status_before'],snap['status_after'],snap['result_seq'])
            result=self._facts(n,before,'apply',identity=actual,status=status,fault=fault,capture=capture)
            self._state='ACTIVE';return result
        except BaseException:self._state='FAILED';raise
    def observe_status(self):
        self._active();_need(self._polls+1<=self._status_limit,'status-read budget exhausted')
        if demo.is_navigation(self._demo_cycle_profile):
            _need(self._status_phases<self._demo_cycle_profile.status_phases,'selected status-phase quota exhausted')
        self._state='BUSY'
        try:
            if demo.is_navigation(self._demo_cycle_profile):
                self._status_phases+=1
            n,before=self._open_phase('status');identity=self._actual_identity();_need(identity==self._identity,'original identity changed')
            status,fault=self._live_status();result=self._facts(n,before,'status',identity=identity,status=status,fault=fault)
            self._state='ACTIVE';return result
        except BaseException:self._state='FAILED';raise
    def close(self,*,stop=False):
        self._owner();_need(type(stop) is bool and self._state in ('ACTIVE','FAILED'),'active or failed original session required')
        if stop:
            _need(self._state=='ACTIVE','cannot STOP after unknown/failure')
            _need(self._polls+1<=self._status_limit,'insufficient status-read budget for STOP observation')
        previous=self._state;self._state='BUSY'
        try:
            n,before=self._open_phase('close');status=fault=None
            if stop:
                self._step('stop');status=self._step('read32',0x08);fault=self._step('read32',0x10)
            result=self._facts(n,before,'close',identity=self._identity,status=status,fault=fault,state='CLOSED' if previous=='ACTIVE' else 'CLOSED_AFTER_FAILURE')
            self._state='CLOSED';return result
        except BaseException:self._state='FAILED';raise
