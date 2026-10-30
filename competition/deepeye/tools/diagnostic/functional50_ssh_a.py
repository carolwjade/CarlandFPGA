"""A-owned one-process transport to the reviewed functional50 board entry.

Loading/effects require a separate Root decision; transport records no authority.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import threading
import time
from ...integration.host_clock import QpcHostClock
from .functional50_board_a import validate_io

_SSH = r'C:\Windows\System32\OpenSSH\ssh.exe'
_SSH_HASH = '98d447730047f5df91373e852d057928a921c3d1e89938700ab656ba84b19dc8'
_KNOWN = r'C:\Users\CarlJade\.ssh\pynq_z2_known_hosts'
_KNOWN_HASH = '31a10124495b85e9b62bbf46418393124888b2f381f9a4d1334521760ada4418'
_HOST = 'xilinx@fe80::200:5ff:fe6b:1f5%8'
_MAX_NS = 60_000_000_000
_ID = re.compile(r'[A-Za-z0-9_-]{1,64}\Z')

@dataclass(frozen=True)
class SessionSpec:
    route: tuple
    remote_python: str
    remote_script: str
    remote_plan: str
    local_script: str
    local_script_sha256: str
    evidence_parent: str
    operation_id: str
    protocol: str = 'scalar_v1'
    remote_manifest: str | None = None
    remote_manifest_sha256: str | None = None
    remote_g05_policy: str | None = None

def _need(ok, message):
    if not ok: raise ValueError(message)

def _remote_path(path):
    _need(type(path) is str and re.fullmatch(r'/[A-Za-z0-9_./-]{1,240}',path) is not None,'remote absolute path required')
    _need(not path.startswith('//') and str(PurePosixPath(path)) == path and '..' not in PurePosixPath(path).parts,'remote path normalization')
    return path

def _sha_file(path):
    p=Path(path); _need(p.is_absolute() and p.is_file() and not p.is_symlink(),'pinned regular file required')
    with p.open('rb') as f:
        before=os.fstat(f.fileno()); h=hashlib.sha256()
        while True:
            b=f.read(65536)
            if not b: break
            h.update(b)
        after=os.fstat(f.fileno())
    _need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'pin changed while read')
    return h.hexdigest()

def _route(route):
    _need(type(route) is tuple and len(route)==18 and all(type(x) is str for x in route),'exact original SSH route required')
    _need(os.path.normcase(route[0])==os.path.normcase(_SSH) and route[1:3]==('-6','-T') and route[3]=='-i','SSH executable/identity route')
    _need(Path(route[4]).is_absolute() and Path(route[4]).is_file(),'existing identity path')
    _need(route[5:14]==('-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=pynq-z2-local','-o'),'fixed SSH options')
    _need(route[14].startswith('UserKnownHostsFile=') and os.path.normcase(route[14].split('=',1)[1])==os.path.normcase(_KNOWN) and route[15:]==('-o','ConnectTimeout=8',_HOST),'fixed known hosts/route')
    _need(_sha_file(route[0])==_SSH_HASH and _sha_file(_KNOWN)==_KNOWN_HASH,'SSH or host key pin mismatch')

def _json(raw):
    def pairs(items):
        result={}
        for k,v in items:
            _need(k not in result,'duplicate JSON key');result[k]=v
        return result
    return json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))

def _parse_response(raw, request_id, kind):
    _need(type(raw) is bytes and 1<=len(raw)<=4096 and raw.endswith(b'\n') and raw.count(b'\n')==1,'single bounded response line required')
    x=_json(raw)
    if kind=='ready':
        _need(type(x) is dict and set(x)=={'state','pid'} and x['state']=='ready' and type(x['pid']) is int and x['pid']>0,'invalid ready')
        return x
    _need(type(x) is dict and set(x)=={'id','returned'} and x['id']==request_id,'response identity')
    value=x['returned']
    if kind=='read':_need(type(value) is int and 0<=value<=0xffffffff,'invalid read result')
    else:_need(value is None,'invalid write result')
    return value

def _remote_command(spec):
    for path in (spec.remote_python, spec.remote_script, spec.remote_plan):
        _remote_path(path)
    need_batch = spec.protocol == 'trace_batch_v1'
    need_chain = spec.protocol == 'functional50_chain_v1'
    _need(spec.protocol in ('scalar_v1','trace_batch_v1','functional50_chain_v1'),'explicit fixed protocol required')
    if need_batch or need_chain:
        _remote_path(spec.remote_manifest)
        _need(PurePosixPath(spec.remote_script).name==('functional50_chain_board_a.py' if need_chain else 'functional50_board_trace_batch_a.py')
              and PurePosixPath(spec.remote_manifest).name==('chain-board-manifest.json' if need_chain else 'trace-batch-manifest.json')
              and type(spec.remote_manifest_sha256) is str
              and re.fullmatch('[0-9a-f]{64}',spec.remote_manifest_sha256) is not None,
              'fixed batch entry and manifest required')
    else:
        _need(spec.remote_manifest is None and spec.remote_manifest_sha256 is None,
              'scalar protocol has no batch manifest')
    if need_chain:_remote_path(spec.remote_g05_policy)
    else:_need(spec.remote_g05_policy is None,'G05 policy only for chain')
    command = ('/usr/bin/sudo -S -p ' + shlex.quote('') +
            ' /usr/bin/env BOARD=Pynq-Z2 XILINX_XRT=/usr ' +
            shlex.quote(spec.remote_python) + ' -I -B ' +
            shlex.quote(spec.remote_script) + (' chain_v1 ' if need_chain else ' ') + shlex.quote(spec.remote_plan))
    if need_batch or need_chain:
        command += ' ' + shlex.quote(spec.remote_manifest) + ' ' + shlex.quote(spec.remote_manifest_sha256)
    if need_chain:command += ' ' + shlex.quote(spec.remote_g05_policy)
    return command

def _write_once(pipe, raw):
    count = pipe.write(raw)
    if type(count) is not int or count != len(raw):
        raise OSError('original pipe short/unknown write; no replay')
    pipe.flush()
class _Quota:
    def __init__(self): self.ids=set();self.count=0;self.commands={x:0 for x in (1,2,3,4,5,8)}
    def check(self, request_id, kind, offset, value):
        validate_io(kind,offset,value)
        _need(type(request_id) is str and _ID.fullmatch(request_id) is not None and request_id not in self.ids and self.count<5000,'one-use request or count')
        if kind=='write' and offset==128:
            _need(self.commands[value] < {1:1,2:4,3:4,4:4,5:1,8:4096}[value] and (value==1 or self.commands[1]==1),'command quota/ARM')
        self.ids.add(request_id);self.count+=1
        if kind=='write' and offset==128:self.commands[value]+=1

def _record(directory,name,obj):
    data=(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')
    with (directory/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())

class Session:
    def __init__(self,key,proc,clock,directory,protocol='scalar_v1'):
        _need(key is _SESSION_KEY,'original session factory required')
        self._proc=proc;self._clock=clock;self._dir=directory;self._thread=threading.get_ident();self._quota=_Quota();self._unknown=False;self._closed=False;self._stderr=bytearray();self._stderr_overflow=False;self._threads=[];self._cleanup_attempted=False;self._protocol=protocol;self._batch_consumed=False
        def drain():
            while True:
                chunk=proc.stderr.read(1024)
                if not chunk:return
                room=max(0,8192-len(self._stderr));self._stderr.extend(chunk[:room])
                if len(chunk)>room:self._stderr_overflow=True
        thread=threading.Thread(target=drain,daemon=True);self._threads.append(thread);thread.start()
    def _check(self):
        _need(threading.get_ident()==self._thread and not self._unknown and not self._closed,'owner/unknown/closed')
        _need(self._proc.poll() is None,'original SSH already exited')
        _need(not self._stderr_overflow,'stderr budget exceeded')
    def _call(self,wire,timeout_ns):
        _need(type(timeout_ns) is int and 0<timeout_ns<=_MAX_NS,'timeout bound')
        done=threading.Event();result={}
        def io():
            try:
                if wire is not None:_write_once(self._proc.stdin,wire)
                raw=self._proc.stdout.readline(1048577 if self._protocol=='functional50_chain_v1' else 4097)
                result['raw']=raw
            except BaseException as e:result['error']=type(e).__name__
            finally:done.set()
        thread=threading.Thread(target=io,daemon=True);self._threads.append(thread);thread.start()
        if not done.wait(timeout_ns/1_000_000_000):
            self._unknown=True;raise TimeoutError('original SSH effect unknown; no replay')
        if 'error' in result:
            self._unknown=True;raise OSError('original SSH I/O unknown: '+result['error'])
        return result['raw']
    def request(self,request_id,kind,offset,value,*,timeout_ns):
        _need(self._protocol=='scalar_v1','scalar requests refused by batch session')
        self._check();self._quota.check(request_id,kind,offset,value)
        raw=(json.dumps(dict(id=request_id,kind=kind,offset=offset,value=value),separators=(',',':'))+'\n').encode('ascii')
        n=self._quota.count
        try:
            lower=self._clock();_record(self._dir,'request-%04d-started.json'%n,dict(id=request_id,raw_hex=raw.hex(),lower_qpc_ns=lower))
            response=self._call(raw,timeout_ns);upper=self._clock()
            _record(self._dir,'request-%04d-returned.json'%n,dict(id=request_id,raw_hex=response.hex(),upper_qpc_ns=upper))
            value=_parse_response(response,request_id,kind)
            return dict(id=request_id,returned=value,lower_qpc_ns=lower,upper_qpc_ns=upper,raw_response=response)
        except BaseException:
            self._unknown=True;raise
    def close_input(self):
        self._check();self._closed=True;self._proc.stdin.close()
        _record(self._dir,'stdin-closed.json',dict(closed=True,remote_stopped=False))
    def cleanup_local(self, *, kill, timeout_seconds):
        """Retire and inspect only this SSH process; no remote stop assertion."""
        _need(threading.get_ident()==self._thread and not self._cleanup_attempted,
              'original owner and one local cleanup required')
        _need(type(kill) is bool and type(timeout_seconds) is int and 1<=timeout_seconds<=10,
              'bounded cleanup arguments')
        self._cleanup_attempted=True
        self._unknown=True
        result=dict(pid=self._proc.pid,kill_requested=kill,kill_attempted=False,kill_returned=None,
                    wait_confirmed=False,exit_code=None,threads_stopped=False,
                    streams_closed=False,handle_closed=False,remote_stopped=False,errors=[])
        _record(self._dir,'local-cleanup-started.json',dict(pid=self._proc.pid,kill_requested=kill,remote_stopped=False))
        end=time.monotonic()+timeout_seconds
        if kill and self._proc.poll() is None:
            result['kill_attempted']=True
            try:self._proc.kill();result['kill_returned']=True
            except BaseException as e:result['kill_returned']=False;result['errors'].append(type(e).__name__)
        try:
            code=self._proc.wait(timeout=max(0,end-time.monotonic()))
            if type(code) is int:
                result['wait_confirmed']=True;result['exit_code']=code
        except BaseException as e:result['errors'].append(type(e).__name__)
        if result['wait_confirmed']:
            for thread in self._threads:thread.join(max(0,end-time.monotonic()))
            result['threads_stopped']=all(not thread.is_alive() for thread in self._threads)
        if result['wait_confirmed'] and result['threads_stopped']:
            closed=True
            for stream in (self._proc.stdin,self._proc.stdout,self._proc.stderr):
                try:stream.close()
                except BaseException as e:closed=False;result['errors'].append(type(e).__name__)
            result['streams_closed']=closed
            try:self._proc._handle.Close();result['handle_closed']=True
            except BaseException as e:result['errors'].append(type(e).__name__)
        _record(self._dir,'local-cleanup-returned.json',result)
        return result
    @property
    def original_process(self):return self._proc
    def stderr_snapshot(self):
        return dict(raw=bytes(self._stderr),overflow=self._stderr_overflow)

class StartupUnknown(RuntimeError):
    def __init__(self,session):
        super().__init__('SSH start/ready unknown; original session retained, no replay')
        self.session=session

_SESSION_KEY=object()
def open_session(spec,clock,*,sudo_input,timeout_ns):
    _need(type(spec) is SessionSpec and type(clock) is QpcHostClock,'exact spec and QPC required')
    _need(type(timeout_ns) is int and 0<timeout_ns<=_MAX_NS,'timeout bound')
    _need(type(sudo_input) is bytes and 1<=len(sudo_input)<=1024 and sudo_input.endswith(b'\n') and sudo_input.count(b'\n')==1,'one-time sudo input required')
    _route(spec.route)
    for x in (spec.remote_python,spec.remote_script,spec.remote_plan):_remote_path(x)
    _need(spec.remote_python=='/usr/local/share/pynq-venv/bin/python3','fixed board Python')
    _need(type(spec.local_script_sha256) is str and re.fullmatch('[0-9a-f]{64}',spec.local_script_sha256) is not None and _sha_file(spec.local_script)==spec.local_script_sha256,'local selected script pin')
    _need(type(spec.operation_id) is str and _ID.fullmatch(spec.operation_id) is not None,'operation ID')
    parent=Path(spec.evidence_parent);_need(parent.is_absolute() and parent.is_dir() and not parent.is_symlink(),'existing evidence parent')
    directory=parent/spec.operation_id;directory.mkdir(mode=0o700)
    command=_remote_command(spec)
    start=dict(operation_id=spec.operation_id,local_script_sha256=spec.local_script_sha256,remote_script=spec.remote_script,remote_plan=spec.remote_plan,remote_hash_verified=False,lower_qpc_ns=clock())
    if spec.protocol in ('trace_batch_v1','functional50_chain_v1'):
        start.update(protocol=spec.protocol,remote_manifest=spec.remote_manifest,remote_manifest_sha256=spec.remote_manifest_sha256)
    if spec.protocol=='functional50_chain_v1':start['remote_g05_policy']=spec.remote_g05_policy
    _record(directory,'ssh-started.json',start)
    proc=subprocess.Popen([*spec.route,command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    s=Session(_SESSION_KEY,proc,clock,directory,spec.protocol)
    try:
        _record(directory,'ssh-created.json',dict(pid=proc.pid))
        raw=s._call(sudo_input,timeout_ns);upper=clock()
        _record(directory,'ready-returned.json',dict(raw_hex=raw.hex(),upper_qpc_ns=upper))
        if spec.protocol=='functional50_chain_v1':
            _need(type(raw) is bytes and 0<len(raw)<=4096 and raw.endswith(b'\n') and raw.count(b'\n')==1,'bounded chain ready required')
            x=_json(raw)
            _need(type(x) is dict and set(x)=={'schema','state','operation_id','plan_sha256','load_request_hash','build_id','source_commit','policy_file_sha256','manifest_sha256'} and x['schema']=='chain_board_v1' and x['state']=='ready' and x['operation_id']==spec.operation_id and x['manifest_sha256']==spec.remote_manifest_sha256,'chain ready identity')
            _need(all(type(x[k]) is str and 0<len(x[k])<=192 for k in ('plan_sha256','load_request_hash','build_id','source_commit','policy_file_sha256')),'chain ready fields')
        else:_parse_response(raw,None,'ready')
        return s
    except BaseException as error:
        s._unknown=True
        # The exception retains the exact original owner and process handle.
        raise StartupUnknown(s) from error
