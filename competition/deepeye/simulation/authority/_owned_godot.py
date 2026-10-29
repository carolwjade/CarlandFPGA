"""Same-process original Godot native owner. No DLL/socket/file effects at import.

Only the actual factory creates a production original. Values/PID/HANDLE exports
cannot construct or adopt it. Private tests exercise external seams separately.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading

from ...integration import host_clock as clocks
from ._world_wire import _WireChannel,WireFault,MAX_IO,MAX_FRAMES

_FACTORY=object();_TEST=object();_ACQUISITIONS=[]
_SLOT_NAMES=('listener','connection','bootstrap_read','bootstrap_write','stdout','stderr','job','attributes','process','thread')
_ALLOWED_ENV={'SystemRoot','WINDIR','TEMP','TMP','LOCALAPPDATA','PATH'}


@dataclass(frozen=True)
class ApprovedLaunchSpec:
    engine_path:Path
    engine_sha256:str
    project_path:Path
    project_files:tuple
    source_bundle_sha256:str
    raw_layout_sha256:str
    stdout_path:Path
    stderr_path:Path
    environment:tuple
    run_id:str
    startup_timeout_ns:int=120_000_000_000
    containment_timeout_ns:int=600_000_000_000


class AcquisitionFailure(RuntimeError):
    def __init__(self,owner,cause):
        super().__init__('original Godot acquisition failed; retained owner required')
        self.owner,self.cause=owner,cause


class _PI(C.Structure):
    _fields_=[('hProcess',W.HANDLE),('hThread',W.HANDLE),('dwProcessId',W.DWORD),('dwThreadId',W.DWORD)]


class _Slot:
    def __init__(self,label):
        self.label=label;self.native=None;self.original_native=None;self.output=W.HANDLE();self.state='NOT_ACQUIRED'
        self.attempted=False;self.close_result=None;self.close_error=None;self.keepalive=None
        self.close_native_error=None
    def begin(self):
        if self.state!='NOT_ACQUIRED':raise ValueError('original acquisition slot already consumed')
        self.state='UNKNOWN'
    def capture(self,native):
        self.native=native;self.original_native=native
        self.state='ACQUIRED' if native not in (None,0,C.c_void_p(-1).value) else 'NOT_ACQUIRED'


@dataclass(frozen=True)
class NativeObservation:
    alive:bool
    terminal:bool
    wait_result:int|None
    exit_code:int|None
    job_active_processes:int|None
    original_pid:int|None


def _ordinary(path,*,directory=False):
    if not isinstance(path,Path) or not path.is_absolute():raise ValueError('approved absolute Path required')
    for part in (path,*path.parents):
        if part.exists():
            st=part.lstat()
            if part.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:raise ValueError('alias/reparse path refused')
    if directory and not path.is_dir():raise ValueError('existing private project directory required')
    if not directory and (not path.is_file() or path.stat().st_nlink!=1):raise ValueError('ordinary single-link file required')


def _digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_spec(spec):
    if type(spec) is not ApprovedLaunchSpec:raise ValueError('exact Root-approved launch values required')
    from ._world_wire import _sha,_label
    _label(spec.run_id)
    for digest in (spec.engine_sha256,spec.source_bundle_sha256,spec.raw_layout_sha256):_sha(digest)
    _ordinary(spec.engine_path);_ordinary(spec.project_path,directory=True)
    if _digest(spec.engine_path)!=spec.engine_sha256:raise ValueError('approved engine bytes changed')
    if type(spec.project_files) is not tuple or not spec.project_files:raise ValueError('complete approved source inventory required')
    normalized=[];seen=set()
    for record in spec.project_files:
        if type(record) is not tuple or len(record)!=2:raise ValueError('exact source pin pair required')
        name,digest=record;_sha(digest)
        if type(name) is not str or not name or '\\' in name or ':' in name or Path(name).anchor or any(part in ('..','.','') for part in name.split('/')):
            raise ValueError('strict relative source path required')
        folded=name.casefold()
        if folded in seen:raise ValueError('duplicate/case alias source path')
        seen.add(folded);path=spec.project_path/name;_ordinary(path)
        if _digest(path)!=digest:raise ValueError('approved project source changed')
        normalized.append((name,digest))
    if tuple(sorted(normalized))!=spec.project_files:raise ValueError('source inventory must be sorted')
    actual={str(path.relative_to(spec.project_path)).replace('\\','/') for path in spec.project_path.rglob('*') if path.is_file()}
    if actual!={name for name,digest in normalized}:raise ValueError('unmanifested or missing project bytes')
    canonical=json.dumps(normalized,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    if hashlib.sha256(canonical).hexdigest()!=spec.source_bundle_sha256:raise ValueError('source bundle digest mismatch')
    if dict(normalized).get('owned-input/layout.json')!=spec.raw_layout_sha256:raise ValueError('fixed raw layout source missing')
    if 'runtime/owned_world_start.gd' not in dict(normalized):raise ValueError('fixed startup source missing')
    for target in (spec.stdout_path,spec.stderr_path):
        if not isinstance(target,Path) or not target.is_absolute() or target.exists():raise ValueError('fresh absolute log path required')
        _ordinary(target.parent,directory=True)
    if spec.stdout_path==spec.stderr_path:raise ValueError('distinct fresh stdout/stderr required')
    if type(spec.environment) is not tuple or any(type(pair) is not tuple or len(pair)!=2 for pair in spec.environment):raise ValueError('fixed environment pairs required')
    env=dict(spec.environment)
    if len(env)!=len(spec.environment) or not {'SystemRoot','WINDIR'}<=set(env) or not set(env)<=_ALLOWED_ENV:
        raise ValueError('explicit approved environment boundary required')
    if any(type(k) is not str or type(v) is not str or '\0' in k+v or '=' in k for k,v in env.items()):raise ValueError('environment bytes rejected')
    for timeout in (spec.startup_timeout_ns,spec.containment_timeout_ns):
        if type(timeout) is not int or not 0<timeout<=600_000_000_000:raise ValueError('bounded original duration required')
    if spec.startup_timeout_ns>spec.containment_timeout_ns:raise ValueError('startup exceeds containment')


class _OwnedGodot:
    def __init__(self,key,spec,clock_binding):
        if key not in (_FACTORY,_TEST):raise ValueError('original native factory required')
        self._key,self.spec,self.clock_binding=key,spec,clock_binding
        self._thread=threading.get_ident();self._busy=False;self._foreign=False
        self._slots={name:_Slot(name) for name in _SLOT_NAMES}
        self._pi=_PI();self._original_pi=self._pi;self._process_native=None;self._thread_native=None;self._process_id=None
        self._bootstrap_count=W.DWORD();self._bootstrap_raw=None;self._bootstrap_write_attempted=False
        self._bootstrap_return=None;self._bootstrap_error=None;self._assignment_return=None;self._assignment_error=None
        self._resume_return=None;self._resume_error=None
        self._secret=None;self._challenge=None;self._api=None;self._channel=None;self.hello=None
        self._errors=[];self._stop_attempted=False;self._stop_return=None;self._stop_error=None
        self._wait=None;self._exit=None;self._job_active=None;self._last_time=None
        self._startup_deadline=self._containment_deadline=None
        self._accept_consumed=False;self._hello_consumed=False;self.state='ACQUIRING';self._retired=False
        self._acquisition_started=False

    @property
    def run_id(self):return None if self.spec is None else self.spec.run_id

    def _enter(self,allow_retired=False):
        if threading.get_ident()!=self._thread:self._foreign=True;self._retired=True;raise ValueError('original owner thread required')
        if self._busy:self._retired=True;raise ValueError('original owner reentry refused')
        if self._foreign and not allow_retired:raise ValueError('foreign entry retired original owner')
        self._busy=True

    def _now(self):
        if self._retired:raise ValueError('original owner revoked')
        if self._pi is not self._original_pi:raise ValueError('original retained PI replaced')
        now=self.clock_binding()
        if type(now) is not int or not 0<=now<(1<<63) or (self._last_time is not None and now<self._last_time):
            self._retired=True;raise ValueError('original clock failed')
        self._last_time=now
        return now

    def _capture_socket(self,name,value):
        slot=self._slots[name];slot.native=value;slot.original_native=value;slot.state='ACQUIRED'

    def _release(self,slot):
        if slot.attempted:return slot.state=='CLOSED'
        if slot.state=='NOT_ACQUIRED':return True
        if slot.state!='ACQUIRED':return False
        same=(slot.native is slot.original_native if slot.label in ('listener','connection') else slot.native==slot.original_native)
        if slot.original_native is None or not same:
            slot.state='UNKNOWN';self._retired=True;self._errors.append(ValueError('original resource reference replaced'));return False
        slot.attempted=True;slot.state='RELEASE_UNKNOWN'
        try:
            if slot.label in ('listener','connection'):
                slot.native.close();result=True
            else:result=self._api.close(slot)
            slot.close_result=result
            if result is not True:raise OSError('checked original close unconfirmed')
            slot.state='CLOSED';return True
        except BaseException as error:
            slot.close_error=type(error).__name__;self._errors.append(error);return False

    def _acquire(self):
        self._enter()
        try:
            if self._acquisition_started:raise ValueError('original acquisition slot already consumed')
            self._acquisition_started=True
            return self._start_acquisition()
        finally:self._busy=False

    def _start_acquisition(self):
        if type(self.spec) is not ApprovedLaunchSpec:raise ValueError('exact Root-approved launch values required')
        for duration in (self.spec.startup_timeout_ns,self.spec.containment_timeout_ns):
            if type(duration) is not int or not 0<duration<=600_000_000_000:raise ValueError('bounded fixed duration required')
        start=self._now();self._startup_deadline=start+self.spec.startup_timeout_ns
        self._containment_deadline=start+self.spec.containment_timeout_ns
        if self._containment_deadline>=(1<<63):raise ValueError('fixed original deadline overflow')
        _validate_spec(self.spec)
        if self._now()>=self._startup_deadline:raise ValueError('startup source validation exceeded original deadline')
        self._secret=secrets.token_bytes(32);self._challenge=secrets.token_hex(32)
        slot=self._slots['listener'];slot.begin()
        slot.native=socket.socket(socket.AF_INET,socket.SOCK_STREAM);slot.original_native=slot.native;slot.state='ACQUIRED'
        listener=slot.native
        listener.set_inheritable(False)
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        listener.bind(('127.0.0.1',0));listener.setblocking(False);listener.listen(1)
        port=listener.getsockname()[1]
        self._api.pipe(self)
        self._api.log(self,self._slots['stdout'],self.spec.stdout_path)
        self._api.log(self,self._slots['stderr'],self.spec.stderr_path)
        self._api.job(self)
        self._bootstrap_raw=json.dumps(dict(protocol='DEYWRL01',address='127.0.0.1',port=port,
            key_hex=self._secret.hex(),launch_challenge=self._challenge,run_id=self.run_id,
            source_bundle_sha256=self.spec.source_bundle_sha256,engine_sha256=self.spec.engine_sha256,
            raw_layout_sha256=self.spec.raw_layout_sha256),sort_keys=True,separators=(',',':')).encode('utf-8')
        if len(self._bootstrap_raw)>2048:raise ValueError('bounded single bootstrap required')
        self._api.process(self)
        if self._process_native is None or self._thread_native is None:raise ValueError('actual original process return was not retained')
        self._api.assign(self)
        if not self._release(self._slots['bootstrap_read']):raise OSError('parent read copy close unknown')
        self._bootstrap_write_attempted=True
        self._api.bootstrap(self,self._bootstrap_raw)
        if not self._release(self._slots['bootstrap_write']):raise OSError('bootstrap writer close unknown')
        if self._now()>=self._startup_deadline:raise ValueError('fixed startup deadline expired before Resume')
        self._api.resume(self)
        if not self._release(self._slots['thread']):raise OSError('original primary thread close unknown')
        self.state='AWAITING_HELLO'

    def _observe(self):
        process=self._slots['process'];job=self._slots['job']
        if process.state=='ACQUIRED':
            if self._pi.hProcess!=self._process_native or process.native!=self._process_native:raise ValueError('original process continuity lost')
            state=self._api.wait(self)
            if type(state) is not int or state not in (0,258):raise OSError('original Wait unclassified')
            self._wait=state
            if state==0:
                code=self._api.exit(self)
                if type(code) is not int or not 0<=code<=0xffffffff:raise ValueError('actual DWORD exit required')
                self._exit=code
        if job.state=='ACQUIRED':
            if job.native!=job.original_native:raise ValueError('original Job reference replaced')
            count=self._api.job_active(self)
            if type(count) is not int or not 0<=count<=0xffffffff:raise ValueError('actual Job accounting required')
            self._job_active=count
        return NativeObservation(self._wait==258,self._wait==0,self._wait,self._exit,self._job_active,
            self._process_id)

    def native_liveness(self):
        self._enter(allow_retired=True)
        try:return self._observe()
        except BaseException as error:
            self._retired=True;self._errors.append(error);raise
        finally:self._busy=False

    def _hello(self,frame):
        if self._hello_consumed or frame.message['type']!='HELLO':raise WireFault('single original HELLO required first')
        self._hello_consumed=True;body=frame.message['body']
        expected=(body['launch_challenge']==self._challenge and body['engine_pid']==str(self._process_id)
            and body['engine_sha256']==self.spec.engine_sha256 and body['source_bundle_sha256']==self.spec.source_bundle_sha256
            and body['raw_layout_sha256']==self.spec.raw_layout_sha256)
        if not expected or not self._observe().alive:raise WireFault('HELLO original challenge/source/process mismatch')
        self.hello=frame;self.state='AUTHENTICATED'

    def poll(self):
        self._enter()
        try:
            if self._retired:raise ValueError('original owner retired')
            now=self._now()
            if now>=self._containment_deadline or (self.hello is None and now>=self._startup_deadline):raise ValueError('fixed original owner deadline expired')
            if not self._observe().alive:raise ValueError('original engine not live')
            if self._channel is None:
                listener=self._slots['listener'].native
                slot=self._slots['connection'];slot.begin()
                try:slot.keepalive=listener.accept()
                except BlockingIOError:slot.state='NOT_ACQUIRED';return ()
                connection,address=slot.keepalive
                self._capture_socket('connection',connection);self._accept_consumed=True
                if address[0]!='127.0.0.1':raise WireFault('nonloopback original connection refused')
                connection.set_inheritable(False);connection.setblocking(False)
                self._channel=_WireChannel(connection,self._secret,self.run_id)
                if not self._release(self._slots['listener']):raise OSError('original listener close unknown')
            if self._channel._socket is not self._slots['connection'].native:raise WireFault('original accepted socket replaced')
            frames=self._channel.pump(now)
            for frame in frames:
                if self.hello is None:self._hello(frame)
                elif frame.message['type']=='HELLO':raise WireFault('duplicate logical HELLO')
                if frame.message['type']=='VIEW_READBACK':
                    width=self.hello.message['body']['scalar_width']//4
                    for field in ('local_transform','global_transform'):
                        transform=frame.message['body'][field]
                        if any(len(v)!=width for col in transform['basis_columns'] for v in col) or any(len(v)!=width for v in transform['origin']):raise WireFault('frozen real_t width mismatch')
            if self._now()>=self._containment_deadline:raise ValueError('original containment expired during pump')
            return frames
        except BaseException as error:
            self._retired=True;self.state='QUARANTINED';self._errors.append(error);raise
        finally:self._busy=False

    def send(self,message,*,deadline_ns):
        self._enter()
        try:
            now=self._now()
            if self._retired or self.hello is None or self._channel is None:raise ValueError('original authenticated owner required')
            if not now<deadline_ns<=self._containment_deadline:raise ValueError('fixed unexpired original deadline required')
            return self._channel.queue(message,deadline_ns)
        except BaseException as error:
            self._retired=True;self._errors.append(error);raise
        finally:self._busy=False

    def complete_tx(self,tx):
        if threading.get_ident()!=self._thread:self._foreign=True;self._retired=True;raise ValueError('original thread required')
        return self._channel is not None and self._channel.complete_tx(tx)

    def healthy_frame_aligned(self):
        if threading.get_ident()!=self._thread:return False
        return not self._retired and self._channel is not None and self._channel.healthy_frame_aligned()

    def close(self,reason):
        self._enter(allow_retired=True)
        try:
            if type(reason) is not str or not reason:raise ValueError('explicit close reason required')
            self._retired=True
            unknown=any(slot.state=='UNKNOWN' for slot in self._slots.values())
            process=self._slots['process']
            if process.state=='ACQUIRED':
                try:self._observe()
                except BaseException as error:self._errors.append(error)
                if self._wait!=0 and not self._stop_attempted:
                    self._stop_attempted=True
                    try:
                        value=self._api.terminate(self)
                        if type(value) is not tuple or len(value)!=2 or type(value[0]) is not bool or type(value[1]) is not int:raise ValueError('classified original stop return required')
                        self._stop_return,self._stop_error=value
                    except BaseException as error:self._errors.append(error)
                try:self._observe()
                except BaseException as error:self._errors.append(error)
            elif self._slots['job'].state=='ACQUIRED':
                try:self._observe()
                except BaseException as error:self._errors.append(error)
            terminal=process.state=='NOT_ACQUIRED' or self._wait==0
            job_empty=self._slots['job'].state=='NOT_ACQUIRED' or self._job_active==0
            if not unknown and terminal and job_empty:
                for name in ('connection','listener','bootstrap_write','bootstrap_read','thread','process','attributes','stdout','stderr','job'):
                    self._release(self._slots[name])
            complete=all(slot.state in ('NOT_ACQUIRED','CLOSED') for slot in self._slots.values())
            self.state='CLOSED' if complete and not self._errors else 'QUARANTINED'
            return self.diagnostics()
        finally:self._busy=False

    def diagnostics(self):
        return dict(state=self.state,original_factory=self._key is _FACTORY,
            process_correlation_pid=self._process_id,
            wait_result=self._wait,exit_code=self._exit,job_active_processes=self._job_active,
            stop_attempted=self._stop_attempted,stop_return=self._stop_return,stop_error=self._stop_error,
            bootstrap_write_attempted=self._bootstrap_write_attempted,
            bootstrap_write_return=self._bootstrap_return,bootstrap_write_error=self._bootstrap_error,
            bootstrap_written_count=self._bootstrap_count.value if self._bootstrap_return else None,
            assignment_return=self._assignment_return,assignment_error=self._assignment_error,
            resume_return=self._resume_return,resume_error=self._resume_error,
            slots={name:dict(state=slot.state,close_attempted=slot.attempted,close_result=slot.close_result,close_error=slot.close_error,close_native_error=slot.close_native_error)
                for name,slot in self._slots.items()},errors=[type(error).__name__ for error in self._errors],
            healthy_frame_aligned=self.healthy_frame_aligned())


def is_original_owner(value):
    return type(value) is _OwnedGodot and value._key is _FACTORY and any(value is owner for owner in _ACQUISITIONS)


def _private_test_owner(clock):return _OwnedGodot(_TEST,None,clock)


def _acquire_owned_godot(spec,original_host_clock_binding):
    binding=clocks._require_binding(original_host_clock_binding)
    if binding is None:raise ValueError('original explicit QPC binding required')
    owner=_OwnedGodot(_FACTORY,spec,binding)
    _ACQUISITIONS.append(owner)
    try:
        owner._api=_Windows();owner._acquire();return owner
    except BaseException as error:
        owner._errors.append(error)
        try:owner.close('original acquisition failed')
        except BaseException as cleanup_error:owner._errors.append(cleanup_error);owner.state='QUARANTINED'
        raise AcquisitionFailure(owner,error) from error


class _SA(C.Structure):
    _fields_=[('nLength',W.DWORD),('lpSecurityDescriptor',C.c_void_p),('bInheritHandle',W.BOOL)]
class _SI(C.Structure):
    _fields_=[('cb',W.DWORD),('lpReserved',W.LPWSTR),('lpDesktop',W.LPWSTR),('lpTitle',W.LPWSTR),
        ('dwX',W.DWORD),('dwY',W.DWORD),('dwXSize',W.DWORD),('dwYSize',W.DWORD),('dwXCountChars',W.DWORD),
        ('dwYCountChars',W.DWORD),('dwFillAttribute',W.DWORD),('dwFlags',W.DWORD),('wShowWindow',W.WORD),
        ('cbReserved2',W.WORD),('lpReserved2',C.c_void_p),('hStdInput',W.HANDLE),('hStdOutput',W.HANDLE),('hStdError',W.HANDLE)]
class _SIEX(C.Structure):_fields_=[('StartupInfo',_SI),('lpAttributeList',C.c_void_p)]
class _LIMIT(C.Structure):
    _fields_=[('PerProcessUserTimeLimit',C.c_longlong),('PerJobUserTimeLimit',C.c_longlong),('LimitFlags',W.DWORD),
        ('MinimumWorkingSetSize',C.c_size_t),('MaximumWorkingSetSize',C.c_size_t),('ActiveProcessLimit',W.DWORD),
        ('Affinity',C.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
class _IO(C.Structure):_fields_=[(name,C.c_ulonglong) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class _EXTLIMIT(C.Structure):
    _fields_=[('BasicLimitInformation',_LIMIT),('IoInfo',_IO),('ProcessMemoryLimit',C.c_size_t),('JobMemoryLimit',C.c_size_t),('PeakProcessMemoryUsed',C.c_size_t),('PeakJobMemoryUsed',C.c_size_t)]
class _ACCOUNTING(C.Structure):
    _fields_=[('TotalUserTime',C.c_longlong),('TotalKernelTime',C.c_longlong),('ThisPeriodTotalUserTime',C.c_longlong),
        ('ThisPeriodTotalKernelTime',C.c_longlong),('TotalPageFaultCount',W.DWORD),('TotalProcesses',W.DWORD),
        ('ActiveProcesses',W.DWORD),('TotalTerminatedProcesses',W.DWORD)]


class _Windows:
    """Built-in actual API, constructed only after original owner retention."""
    def __init__(self):
        if os.name!='nt':raise OSError('original Windows native owner required')
        dll=C.WinDLL('kernel32',use_last_error=True)
        def bind(name,args,result=W.BOOL):
            fn=getattr(dll,name);fn.argtypes=args;fn.restype=result;return fn
        P=C.c_void_p;D=W.DWORD;H=W.HANDLE
        self.CreatePipe=bind('CreatePipe',[C.POINTER(H),C.POINTER(H),C.POINTER(_SA),D])
        self.SetHandle=bind('SetHandleInformation',[H,D,D]);self.GetHandle=bind('GetHandleInformation',[H,C.POINTER(D)])
        self.CreateFile=bind('CreateFileW',[W.LPCWSTR,D,D,C.POINTER(_SA),D,D,H],H)
        self.CreateJob=bind('CreateJobObjectW',[P,W.LPCWSTR],H)
        self.SetJob=bind('SetInformationJobObject',[H,C.c_int,P,D]);self.QueryJob=bind('QueryInformationJobObject',[H,C.c_int,P,D,P])
        self.InitAttrs=bind('InitializeProcThreadAttributeList',[P,D,D,C.POINTER(C.c_size_t)])
        self.UpdateAttr=bind('UpdateProcThreadAttribute',[P,D,C.c_size_t,P,C.c_size_t,P,P])
        self.DeleteAttrs=bind('DeleteProcThreadAttributeList',[P],None)
        self.CreateProcess=bind('CreateProcessW',[W.LPCWSTR,W.LPWSTR,P,P,W.BOOL,D,P,W.LPCWSTR,C.POINTER(_SIEX),C.POINTER(_PI)])
        self.AssignJob=bind('AssignProcessToJobObject',[H,H]);self.WriteFile=bind('WriteFile',[H,P,D,C.POINTER(D),P])
        self.Resume=bind('ResumeThread',[H],D);self.Wait=bind('WaitForSingleObject',[H,D],D)
        self.Exit=bind('GetExitCodeProcess',[H,C.POINTER(D)]);self.Terminate=bind('TerminateProcess',[H,W.UINT])
        self.Close=bind('CloseHandle',[H])

    @staticmethod
    def check(value,operation):
        if not value:raise C.WinError(C.get_last_error(),operation)

    def pipe(self,owner):
        read,write=owner._slots['bootstrap_read'],owner._slots['bootstrap_write']
        read.begin();write.begin();sa=_SA(C.sizeof(_SA),None,True)
        ok=self.CreatePipe(C.byref(read.output),C.byref(write.output),C.byref(sa),4096)
        read.native,write.native=read.output.value,write.output.value
        read.original_native,write.original_native=read.native,write.native
        if not ok:
            if not read.native and not write.native:read.state=write.state='NOT_ACQUIRED'
            self.check(ok,'CreatePipe original bootstrap')
        read.state=write.state='ACQUIRED'
        self.check(self.SetHandle(write.native,1,0),'noninheritable original parent writer')
        for slot,expected in ((read,1),(write,0)):
            flags=W.DWORD();self.check(self.GetHandle(slot.native,C.byref(flags)),'original pipe inheritance readback')
            if flags.value!=expected:raise ValueError('exact original inheritance flags required')

    def log(self,owner,slot,path):
        slot.begin();sa=_SA(C.sizeof(_SA),None,True)
        slot.native=self.CreateFile(str(path),0x40000000,1,C.byref(sa),1,0x80,None)
        slot.original_native=slot.native
        if slot.native in (None,0,C.c_void_p(-1).value):slot.state='NOT_ACQUIRED';self.check(False,'CreateFileW fresh original log')
        slot.state='ACQUIRED'

    def job(self,owner):
        slot=owner._slots['job'];slot.begin();slot.native=self.CreateJob(None,None)
        slot.original_native=slot.native
        if not slot.native:slot.state='NOT_ACQUIRED';self.check(False,'CreateJobObject original containment')
        slot.state='ACQUIRED';limits=_EXTLIMIT();limits.BasicLimitInformation.LimitFlags=0x2000
        self.check(self.SetJob(slot.native,9,C.byref(limits),C.sizeof(limits)),'original Job kill-on-close')

    def process(self,owner):
        attr=owner._slots['attributes'];size=C.c_size_t()
        self.InitAttrs(None,1,0,C.byref(size))
        if not 0<size.value<=65536:raise ValueError('bounded actual attribute-list allocation required')
        buffer=C.create_string_buffer(size.value)
        handles=(W.HANDLE*3)(owner._slots['bootstrap_read'].native,owner._slots['stdout'].native,owner._slots['stderr'].native)
        attr.keepalive=(buffer,handles);attr.begin();attr.native=C.cast(buffer,C.c_void_p).value
        attr.original_native=attr.native
        self.check(self.InitAttrs(buffer,1,0,C.byref(size)),'original attribute list init');attr.state='ACQUIRED'
        self.check(self.UpdateAttr(buffer,0,0x20002,C.byref(handles),C.sizeof(handles),None,None),'exact inherited HANDLE_LIST')
        si=_SIEX();si.StartupInfo.cb=C.sizeof(si);si.StartupInfo.dwFlags=0x100|1
        si.StartupInfo.hStdInput=handles[0];si.StartupInfo.hStdOutput=handles[1];si.StartupInfo.hStdError=handles[2]
        si.lpAttributeList=C.cast(buffer,C.c_void_p)
        argv=[str(owner.spec.engine_path),'--headless','--path',str(owner.spec.project_path),'--script','res://runtime/owned_world_start.gd']
        command=C.create_unicode_buffer(subprocess.list2cmdline(argv))
        environment=C.create_unicode_buffer('\0'.join(key+'='+value for key,value in sorted(owner.spec.environment))+'\0\0')
        process,thread=owner._slots['process'],owner._slots['thread'];process.begin();thread.begin()
        owner._process_call_storage=(si,command,environment)
        ok=self.CreateProcess(str(owner.spec.engine_path),command,None,None,True,0x08000000|0x80000|0x400|4,
            environment,str(owner.spec.project_path),C.byref(si),C.byref(owner._pi))
        process.native,thread.native=owner._pi.hProcess,owner._pi.hThread
        process.original_native,thread.original_native=process.native,thread.native
        error=C.get_last_error() if not ok else 0
        if ok and process.native and thread.native:process.state=thread.state='ACQUIRED'
        elif not ok and not process.native and not thread.native:process.state=thread.state='NOT_ACQUIRED'
        if not ok:raise C.WinError(error,'original suspended Godot CreateProcessW')
        if process.state!='ACQUIRED':raise ValueError('original successful PI incomplete')
        owner._process_native,owner._thread_native=owner._pi.hProcess,owner._pi.hThread
        owner._process_id=int(owner._pi.dwProcessId)
        if not owner._process_id or not owner._pi.dwThreadId:raise ValueError('actual original process correlation incomplete')
        if not owner._release(attr):raise OSError('original attributes cleanup unknown')

    def assign(self,owner):
        result=self.AssignJob(owner._slots['job'].original_native,owner._process_native)
        owner._assignment_return=result;owner._assignment_error=C.get_last_error() if not result else 0
        self.check(result,'Assign original Godot to original Job')

    def bootstrap(self,owner,raw):
        if len(raw)>2048:raise ValueError('bounded original bootstrap required')
        owner._bootstrap_buffer=C.create_string_buffer(raw,len(raw))
        ok=self.WriteFile(owner._slots['bootstrap_write'].native,owner._bootstrap_buffer,len(raw),C.byref(owner._bootstrap_count),None)
        owner._bootstrap_return=ok;owner._bootstrap_error=C.get_last_error() if not ok else 0
        self.check(ok,'single original bootstrap WriteFile')
        if owner._bootstrap_count.value!=len(raw):raise OSError('short original bootstrap; no remainder')

    def resume(self,owner):
        result=self.Resume(owner._thread_native)
        owner._resume_return=result;owner._resume_error=C.get_last_error() if result==0xffffffff else 0
        if result!=1:raise OSError('original suspended thread ResumeThread count rejected')

    def wait(self,owner):return self.Wait(owner._process_native,0)
    def exit(self,owner):
        value=W.DWORD();self.check(self.Exit(owner._process_native,C.byref(value)),'actual original process exit readback');return value.value
    def job_active(self,owner):
        value=_ACCOUNTING();self.check(self.QueryJob(owner._slots['job'].native,1,C.byref(value),C.sizeof(value),None),'actual original Job accounting');return value.ActiveProcesses
    def terminate(self,owner):
        result=self.Terminate(owner._process_native,0xdead);error=C.get_last_error() if not result else 0
        return bool(result),error
    def close(self,slot):
        if slot.label=='attributes':self.DeleteAttrs(slot.native);return True
        result=self.Close(slot.native)
        slot.close_native_error=C.get_last_error() if not result else 0
        return bool(result)


__all__=[]
