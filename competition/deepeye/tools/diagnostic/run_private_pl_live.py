"""Two-phase original Windows QPC owner and one original SSH/Job diagnostic supervisor.

Prepare alone performs no SSH. Root independently stages/pins the concrete request,
then one exclusive activation releases this same owner thread. No motion provider.
"""
import argparse
import ast
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import threading
import time


def require(value,message):
    if not value:raise ValueError(message)


def canonical(value):return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def pin(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'regular unaliased source required')
    raw=path.read_bytes();return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def pin_system_ssh(path):
    path=Path(path)
    require(path.is_absolute() and path==Path('C:/WINDOWS/System32/OpenSSH/ssh.exe'),
            'exact original system SSH path required')
    def identity(info):
        return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,
                stat.S_IFMT(info.st_mode),info.st_file_attributes)
    before=path.lstat()
    require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,
            'regular non-reparse system SSH required')
    with path.open('rb') as stream:
        a=os.fstat(stream.fileno())
        require(stat.S_ISREG(a.st_mode) and not a.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT and
                a.st_nlink==2 and a.st_size==1256448 and identity(before)==identity(a),
                'exact original two-link system SSH required')
        raw=stream.read(a.st_size+1);z=os.fstat(stream.fileno())
    require(len(raw)==a.st_size and a.st_mode==z.st_mode and identity(a)==identity(z)==identity(path.lstat()),
            'system SSH changed during bounded read')
    digest=hashlib.sha256(raw).hexdigest()
    require(digest=='98d447730047f5df91373e852d057928a921c3d1e89938700ab656ba84b19dc8',
            'original system SSH bytes differ')
    return {'bytes':len(raw),'sha256':digest}


def read_json(path,limit=16384):
    require(path.stat().st_size<=limit,'bounded Root file required')
    def pairs(items):
        result={}
        for key,value in items:require(key not in result,'duplicate Root JSON field');result[key]=value
        return result
    return json.loads(path.read_bytes(),object_pairs_hook=pairs,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite Root JSON')))


def save(path,value):
    with path.open('xb') as stream:
        raw=canonical(value);require(stream.write(raw)==len(raw),'short original host record')
        stream.flush();os.fsync(stream.fileno())


def _original_process_identity():
    require(os.name=='nt','actual Windows original process required')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;k.GetProcessTimes.restype=wintypes.BOOL
    creation,exit_time,kernel,user=(wintypes.FILETIME() for _ in range(4))
    require(k.GetProcessTimes(k.GetCurrentProcess(),ctypes.byref(creation),ctypes.byref(exit_time),ctypes.byref(kernel),ctypes.byref(user)),
            'original host process creation identity unavailable')
    return {'pid':os.getpid(),'native_thread_id':threading.get_native_id(),
            'creation_filetime_100ns':(creation.dwHighDateTime<<32)|creation.dwLowDateTime}


def _prepare(out,template,clock,source_pins,process_identity):
    seed=dict(template['context'])
    require('request_hash' not in seed and 'clock_domain_id' not in seed,'Root template excludes runtime clock/hash')
    seed['clock_domain_id']=clock.metadata['domain_id']
    result={'schema':1,'phase':'HOST_PREPARED','context_seed':seed,'clock':dict(clock.metadata),
            'source_pins':source_pins,'original_process':process_identity,'owner_thread_id':threading.get_ident(),
            'prepared_qpc_ns':clock(),'template_sha256':hashlib.sha256(canonical(template)).hexdigest(),
            'agent_source_commit':template['agent_source_commit'],'SSH_started':False,'physical_started':False}
    save(out/'HOST_PREPARED.json',result);return result


def _wait_activation(out,timeout):
    require(type(timeout) is int and 1<=timeout<=120,'bounded prepare wait1..120s required')
    end=time.monotonic()+timeout
    while not (out/'ROOT_ACTIVATION.json').exists():
        if time.monotonic()>=end:raise TimeoutError('prepare expired; no SSH/hardware started')
        time.sleep(0.02)


def _claim(out,prepared):
    activation=read_json(out/'ROOT_ACTIVATION.json');request=read_json(out/'LIVE_REQUEST.json')
    require(activation['allowed'] is True and type(activation['attempts']) is int and activation['attempts']==1,
            'one explicit Root activation required')
    require(activation['prepared_sha256']==pin(out/'HOST_PREPARED.json')['sha256'] and
            read_json(out/'HOST_PREPARED.json',65536)==prepared,'original prepared bytes/owner binding mismatch')
    require(activation['request_file_sha256']==pin(out/'LIVE_REQUEST.json')['sha256'],'actual complete request file pin differs')
    unsigned=dict(request);claimed=unsigned.pop('request_hash')
    require(claimed==activation['request_hash']==hashlib.sha256(canonical(unsigned)).hexdigest(),'logical request hash mismatch')
    require(request['context']==prepared['context_seed'] and
            request['agent_source_commit']==activation['agent_source_commit']==prepared['agent_source_commit'] and
            request['context']['tested_commit']==request['agent_source_commit'],'new exact source/clock/session activation required')
    remote='/tmp/deepeye-a-private-live-'+claimed[:16]
    require(activation['remote_directory']==remote,'new exclusive remote session root required')
    save(out/'ACTIVATION_CONSUMED.json',{'prepared_sha256':activation['prepared_sha256'],'request_hash':claimed,
         'request_file_sha256':activation['request_file_sha256'],'actual_original_pid':os.getpid(),
         'owner_thread_id':threading.get_ident(),'automatic_retry':False,'state':'started_unknown_before_SSH'})
    return {'activation':activation,'request':request,'remote':remote}


class _Job:
    """Actual original Windows Job handle, only assigned before sending credentials."""
    def __init__(self,process):
        require(os.name=='nt','Windows original SSH Job required')
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        class IO(ctypes.Structure):_fields_=[(x,ctypes.c_uint64) for x in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
        class Basic(ctypes.Structure):
            _fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',wintypes.DWORD),
                      ('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),
                      ('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
        class Extended(ctypes.Structure):
            _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),
                      ('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];k.CreateJobObjectW.restype=wintypes.HANDLE
        k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];k.SetInformationJobObject.restype=wintypes.BOOL
        k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];k.AssignProcessToJobObject.restype=wintypes.BOOL
        k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
        self.k=k;self.handle=k.CreateJobObjectW(None,None);require(bool(self.handle),'create original SSH Job failed')
        try:
            limits=Extended();limits.BasicLimitInformation.LimitFlags=0x2000
            require(k.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)),'set original Job policy failed')
            require(k.AssignProcessToJobObject(self.handle,int(process._handle)),'assign original SSH process Job failed')
        except BaseException:self.close();raise
    def close(self):
        if self.handle:
            handle=self.handle;self.handle=None;require(self.k.CloseHandle(handle),'close original Job handle failed')


class _Transport:
    """Single original SSH process. No retry, replacement process or background reader."""
    def __init__(self,argv,out,clock):
        self.clock=clock;self.out=out;self.buffer=bytearray();self.stdout_count=self.stderr_count=0
        self.stdout_log=(out/'SSH.stdout.bin').open('xb');self.stderr_log=(out/'SSH.stderr.bin').open('xb')
        self.process=None;self.job=None;self.started=time.monotonic();self.timeout=180
        try:
            self.process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                          creationflags=subprocess.CREATE_NO_WINDOW,shell=False)
            self.job=_Job(self.process)  # Relay cannot start sudo/PL before credential arrives below.
            os.set_blocking(self.process.stdin.fileno(),False)
        except BaseException as primary:
            cleanup=[];waited=False;code=None
            if self.process is not None:
                try:self.process.kill();code=self.process.wait(timeout=10);waited=True
                except BaseException as error:cleanup.append({'stage':'original_process_wait','type':type(error).__name__})
                try:self._drain()
                except BaseException as error:cleanup.append({'stage':'original_output_readback','type':type(error).__name__})
                for stream in (self.process.stdin,self.process.stdout,self.process.stderr):
                    try:
                        if stream is not None and not stream.closed:stream.close()
                    except BaseException as error:cleanup.append({'stage':'original_pipe_close','type':type(error).__name__})
                try:self.process._handle.Close()
                except BaseException as error:cleanup.append({'stage':'original_process_handle_close','type':type(error).__name__})
            if self.job is not None:
                try:self.job.close()
                except BaseException as error:cleanup.append({'stage':'original_job_close','type':type(error).__name__})
            self.stdout_log.close();self.stderr_log.close()
            save(out/'SSH_CONSTRUCTOR_TERMINAL.json',{'original_pid':None if self.process is None else self.process.pid,
                 'original_exit':code,'original_wait_completed':waited,'primary_error':type(primary).__name__,
                 'cleanup_errors':cleanup,'credentials_never_sent':True,'remote_STOP_or_exit_not_inferred':True,'automatic_retry':False})
            raise
    def _available(self,stream):
        import msvcrt
        k=ctypes.WinDLL('kernel32',use_last_error=True);available=wintypes.DWORD()
        k.PeekNamedPipe.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
        k.PeekNamedPipe.restype=wintypes.BOOL
        ok=k.PeekNamedPipe(msvcrt.get_osfhandle(stream.fileno()),None,0,None,ctypes.byref(available),None)
        if not ok:
            error=ctypes.get_last_error()
            if error==109:return 0  # Actual closed-writer ERROR_BROKEN_PIPE; no other error is EOF.
            raise OSError(error,'original pipe observation failed')
        return available.value
    def _drain(self):
        for stream,log,name,bound in ((self.process.stdout,self.stdout_log,'stdout',512*1024),(self.process.stderr,self.stderr_log,'stderr',1024*1024)):
            available=self._available(stream)
            if available:
                count=getattr(self,name+'_count');data=os.read(stream.fileno(),min(available,bound-count+1))
                log.write(data);log.flush();setattr(self,name+'_count',count+len(data));require(count+len(data)<=bound,'finite original SSH output exceeded')
                if name=='stdout':self.buffer.extend(data)
    def line(self,seconds):
        end=min(self.started+self.timeout,time.monotonic()+seconds)
        while True:
            self.clock();self._drain()
            if b'\n' in self.buffer:
                pos=self.buffer.index(10)+1;require(pos<=16384,'original diagnostic line too large')
                raw=bytes(self.buffer[:pos]);del self.buffer[:pos];return raw
            require(len(self.buffer)<=16384,'unterminated original diagnostic line exceeds bound')
            if self.process.poll() is not None:
                self._drain();require(not self.buffer,'original SSH ended inside a record');return None
            if time.monotonic()>=end:raise TimeoutError('original SSH local wait expired; remote outcome unknown')
            time.sleep(0.001)
    def send_once(self,raw):
        require(type(raw) is bytes and 0<len(raw)<=2048,'bounded original input required')
        # Nonblocking single original write. Any partial/error is unknown and is NEVER retried.
        count=os.write(self.process.stdin.fileno(),raw)
        require(count==len(raw),'partial/unknown original write; no replay')
    def close_input(self):self.process.stdin.close()
    def finish(self):
        process=self.process;timed_out=False;error=None;error_details=None;cleanup_errors=[];job_closed=False;handle_closed=False
        try:
            while process.poll() is None:
                self._drain()
                if time.monotonic()-self.started>=self.timeout:
                    timed_out=True;process.kill();break
                time.sleep(0.005)
            code=process.wait(timeout=10);self._drain()
        except BaseException as failure:
            error=type(failure).__name__;error_details={'stage':'finish','type':error,'errno':getattr(failure,'errno',None),'winerror':getattr(failure,'winerror',None)};process.kill();code=process.wait(timeout=10)
        finally:
            for stream in (process.stdin,process.stdout,process.stderr):
                try:
                    if stream is not None and not stream.closed:stream.close()
                except BaseException as failure:cleanup_errors.append({'stage':'pipe_close','type':type(failure).__name__})
            if self.job is not None:
                try:self.job.close();job_closed=True
                except BaseException as failure:cleanup_errors.append({'stage':'job_close','type':type(failure).__name__})
            try:process._handle.Close();handle_closed=True
            except BaseException as failure:cleanup_errors.append({'stage':'process_handle_close','type':type(failure).__name__})
            self.stdout_log.close();self.stderr_log.close()
        value={'original_pid':process.pid,'original_exit':code,'original_wait_completed':True,'local_timed_out':timed_out,
               'error':error,'error_details':error_details,'remote_STOP_or_exit_not_inferred':True,'automatic_retry':False,
               'stdout':pin(self.out/'SSH.stdout.bin'),'stderr':pin(self.out/'SSH.stderr.bin'),'original_job_closed':job_closed,
               'original_process_handle_closed':handle_closed,'cleanup_errors':cleanup_errors}
        save(self.out/'SSH-process.json',value);return value


def _save_response_timing(owner,out,timings):
    if owner.last_response_timing is not None:
        measured=dict(owner.last_response_timing);timings.append(measured)
        save(out/('response-timing-%02d.json' % (len(timings)-1)),measured)


def _exchange(owner,transport,codec,values,qualities,scans,out):
    ready=transport.line(180);require(ready is not None,'original READY absent');owner.accept_ready(ready)
    records=[];timings=[]
    for _ in range(scans):
        raw=owner.next_request(values,qualities)
        save(out/('request-%02d.json' % len(records)),{'raw_hex':raw.hex(),'raw_sha256':hashlib.sha256(raw).hexdigest(),
             'state':'started_unknown_before_write','clock':dict(owner.host_clock.metadata)})
        transport.send_once(raw)
        returned=transport.line(owner.response_timeout_seconds);require(returned is not None,'original capture absent')
        # Retain exact stale/invalid bytes BEFORE freshness or correlation rejection.
        with (out/('response-%02d.bin' % len(records))).open('xb') as stream:stream.write(returned)
        try:accepted=owner.accept(returned)
        except BaseException as primary:
            try:_save_response_timing(owner,out,timings)
            except BaseException as secondary:
                # Keep scalar evidence only; re-raise the exact original rejection.
                primary._private_timing_save_errors=({'stage':'response_timing_save',
                    'type':type(secondary).__name__,'message':str(secondary)[:512]},)
            raise
        else:
            _save_response_timing(owner,out,timings)  # A save failure here remains primary.
            records.append(accepted)
    transport.close_input();terminal_raw=transport.line(5)
    require(terminal_raw is not None,'original terminal absent');terminal=codec.decode(terminal_raw)
    require(set(terminal)=={'schema','kind','context','cleanup','error','frames_completed','movement_authorized'} and
            type(terminal['schema']) is int and terminal['schema']==1 and terminal['kind']=='diagnostic_stopped' and
            codec.context(terminal['context'])==owner.context and terminal['movement_authorized'] is False and
            type(terminal['frames_completed']) is int and terminal['frames_completed']==scans and terminal['error'] is None,
            'original terminal identity/error mismatch')
    cleanup=terminal['cleanup'];require(cleanup['attempted'] is True and cleanup['confirmed'] is True and
            type(cleanup['status']) is int and cleanup['status']==0 and type(cleanup['active_tag']) is int and cleanup['active_tag']==0 and
            not cleanup['secondary_errors'],'original raw final STOP/secondary error mismatch')
    result={'context':owner.context,'captures':records,'original_terminal':terminal,
         'movement_authorized':False,'formal_acceptance':'not_run','100ms_physical_acceptance':False}
    if owner.functional_timing_profile is not None:
        result.update(functional_timing_profile=dict(owner.functional_timing_profile),
                      response_timing=timings,formal_100ms_acceptance='not_run')
    save(out/'HOST_RESULT.json',result)


def main(argv=None):
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--template',type=Path,required=True);parser.add_argument('--template-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--prepare-seconds',type=int,default=120)
    parser.add_argument('--import-check-only',action='store_true')
    args=parser.parse_args(argv)
    require(os.name=='nt','original A Windows QPC host required')
    require(pin(args.template)['sha256']==args.template_sha256,'reviewed template bytes mismatch')
    # Run only after Root integrates this source into the reviewed package.
    sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
    from competition.deepeye.integration import host_clock,private_pl_stream as codec
    if args.import_check_only:
        print(json.dumps({'scope':'imports_and_bytes_only','driver':pin(Path(__file__)),'host_clock':pin(Path(host_clock.__file__)),
                          'codec':pin(Path(codec.__file__)),'QPC_prepared':False,'SSH_started':False},sort_keys=True))
        return 0
    clock=host_clock.qpc_clock_for_new_run();template=read_json(args.template)
    out=args.out.absolute();out.mkdir(exist_ok=False)
    sources={'driver':pin(Path(__file__)),'codec':pin(Path(codec.__file__)),'host_clock':pin(Path(host_clock.__file__)),
             'agent':pin(Path(__file__).with_name('private_pl_live_agent.py')),
             'collector':pin(Path(__file__).with_name('a_b56_memory_safe_collector.py')),'template':pin(args.template)}
    prepared=_prepare(out,template,clock,sources,_original_process_identity())
    transport=None;owner=None;primary=None;secondary_errors=()
    try:
        _wait_activation(out,args.prepare_seconds);clock()
        require(pin(Path(__file__))==sources['driver'] and pin(Path(codec.__file__))==sources['codec'] and
                pin(Path(host_clock.__file__))==sources['host_clock'] and pin(args.template)==sources['template'] and
                pin(Path(__file__).with_name('private_pl_live_agent.py'))==sources['agent'] and
                pin(Path(__file__).with_name('a_b56_memory_safe_collector.py'))==sources['collector'],'prepared original source drift')
        released=_claim(out,prepared);request=released['request'];activation=released['activation'];remote=released['remote']
        timing=codec.request_timing(request,activation)
        ctx=codec.context({**request['context'],'request_hash':request['request_hash']})
        owner=codec.HostOwner(ctx,clock,max_age_ns=timing['max_age_ns'],
                              functional_timing_profile=timing['functional_timing_profile'])
        require(type(activation['scans']) is int and 1<=activation['scans']<=request['max_scans']<=16 and
                type(request['max_scans']) is int,'finite actual scan count required')
        for field,bits in (('values',16),('qualities',8)):
            require(type(activation[field]) is list and len(activation[field])==4,'four original diagnostic inputs required')
            for value in activation[field]:codec.uint(value,bits)
        require(request['agent_sha256']==sources['agent']['sha256'] and request['codec_sha256']==sources['codec']['sha256'],
                'prepared actual agent/codec bytes differ')
        # Existing strict route/provider is read only after actual one-time activation.
        root=Path(template['original_repository_root'])
        prior=read_json(root/'.planning/deepeye-resume-20261018/board-preflight-20261021/started.private.json',65536)
        base=prior['argv'][:-1];require(base[-1].startswith('xilinx@') and base[-1].endswith('%8') and
                all(x in base for x in ('StrictHostKeyChecking=yes','BatchMode=yes','IdentitiesOnly=yes')),'original strict SSH route required')
        require(pin_system_ssh(Path(base[0]))['sha256']==prior['ssh_sha256'],'original SSH binary changed')
        known=next(x.split('=',1)[1] for x in base if x.startswith('UserKnownHostsFile='))
        require(pin(Path(known))['sha256']==prior['pinned_known_hosts_sha256'],'knownhost bytes changed')
        legacy=root/'.planning/deepeye-resume-20261018/board-baseline-20261021/run.py'
        providers=[n for n in ast.parse(legacy.read_text('utf-8-sig')).body if isinstance(n,ast.Assign) and
                   any(isinstance(t,ast.Name) and t.id=='credential' for t in n.targets)]
        require(len(providers)==1 and ast.unparse(providers[0].value)=="base[-1].split('@', 1)[0]",'original provider recipe changed')
        private_value=base[-1].split('@',1)[0]
        command=('/usr/local/share/pynq-venv/bin/python3 -I -B '+shlex.quote(remote+'/private_pl_live_agent.py')+
                 ' --relay-original --request '+shlex.quote(remote+'/LIVE_REQUEST.json')+
                 ' --request-sha256 '+shlex.quote(activation['request_file_sha256']))
        save(out/'SSH-started.json',{'original_argv':base+[command],'stdin_logged':False,'automatic_retry':False,
             'prepared_sha256':activation['prepared_sha256'],'request_hash':request['request_hash'],'native_job_before_credential':True})
        transport=_Transport(base+[command],out,clock)
        transport.send_once((private_value+'\n').encode());private_value=None
        _exchange(owner,transport,codec,activation['values'],activation['qualities'],activation['scans'],out)
    except BaseException as error:
        primary={'type':type(error).__name__,'message':str(error)[:512]}
        secondary_errors=getattr(error,'_private_timing_save_errors',())
        if owner is not None:owner.retire()
    finally:
        process=None
        if transport is not None:
            try:
                if not transport.process.stdin.closed:transport.close_input()
                process=transport.finish()
            except BaseException as error:
                process={'local_cleanup_error':type(error).__name__,'remote_outcome':'unknown'}
        terminal={'primary_error':primary,'original_process':process,
             'SSH_started':transport is not None or (out/'SSH_CONSTRUCTOR_TERMINAL.json').exists(),
             'remote_STOP_not_inferred_from_local_cleanup':True,'movement_authorized':False,'automatic_retry':False}
        if secondary_errors:terminal['secondary_errors']=list(secondary_errors)
        save(out/'HOST_TERMINAL.json',terminal)
    return (0 if primary is None and process is not None and process.get('original_exit')==0 and not process.get('error') and not process.get('cleanup_errors') and
            process.get('original_job_closed') and process.get('original_process_handle_closed') else 2)


if __name__=='__main__':raise SystemExit(main())
