"""A-only bounded Linux private digital session. Explicit physical flag required.

One checked image load and START, then original per-scan TRIGGER/ACK FSM.
Private JSON never becomes negotiated wire, AI input, BOOT or motion authority.
"""
import argparse
import errno
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import select
import signal
import stat as stat_mode
import sys
import subprocess
import time
import threading

COLLECTOR_SHA='723435f542b050405d8a6286a806a6561fbb613e6608ebf5f84407c7418407e6'
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
PYNQ_SHA='d2ea2a5b61df23214e3d7990e6c103e23d2bada59be0abbf2a7d36db8f4ab384'
BUILD_SHA='e906b1517d328e05b123346ea71c0c5c7c6552be7baa31dde2eb42833f0ef13a'
BIT_SHA='8455b5f8648ff913926c7f55495c5e2ed7328e92a312558eed131f3edb0d11db'
HWH_SHA='aa0ce7094eb0f1ed6a12684713cefe3a1635ef8c32af9fc32f8e1cc3cbef3ee1'
RUNTIME_SOURCE_MANIFEST_SHA='9b0646628fef08bca9540a40efaf68f2080c785d090fee51c80b61f0a4c713dd'
RUNTIME_SOURCE_PINS={'__init__.py': {'bytes': 766, 'sha256': 'd2ea2a5b61df23214e3d7990e6c103e23d2bada59be0abbf2a7d36db8f4ab384'}, 'bitstream.py': {'bytes': 7430, 'sha256': 'b7e37302fefca9f2d09ebf487aa14abac8e603e12c544e8888d9ebaca9bf2914'}, 'overlay.py': {'bytes': 39749, 'sha256': '949bbd3a1d296b487702f4c49013de24c3d6eb44da9fb2ebe1ada70d054237d7'}, 'pl_server/embedded_device.py': {'bytes': 24231, 'sha256': 'cfd41079517552329914c125ecfec97293e0d3160db008ed18de9afa7834dee1'}, 'ps.py': {'bytes': 23304, 'sha256': '7c9cd379fcb34415e4c664ec262eff2ab4b0e212ab417d128e7b19dec83522ba'}, 'registers.py': {'bytes': 14907, 'sha256': '3ecb2e19c4aa8a6972ae39e335c9de65c48993bac5796d8a693b27ac672b66ea'}, 'pl_server/device.py': {'bytes': 15268, 'sha256': 'cbfac4c5d0e78b1c2aa726ac18dcd5bf52d3d693159e8f948a0977b4af30ed74'}, 'pl_server/global_state.py': {'bytes': 2927, 'sha256': 'd04390c6647f9b8e2e8b55d49001b1daba739afd3203734c3753055611b397c6'}, 'pl_server/xrt_device.py': {'bytes': 20471, 'sha256': 'b79765ec53d92ac97657e95a7c990e8d1bdacb133161b278e1a8c3e4159fcd5e'}}
U32=(1<<32)-1
QUALIFICATION_SENTINEL=b'DEEPEYE_PRIVATE_RELAY_QUALIFICATION_V1\n'
PRIVATE_PRELUDE=b'DEEPEYE_PRIVATE_INPUT_V1\n'  # Transport startup only; never BOOT/auth/wire evidence.


def require(value,message):
    if not value:raise ValueError(message)


def _runtime_sources(package):
    """Bounded static byte checks, not a measured-clock or hardware guarantee."""
    require(package.is_dir() and not package.is_symlink(),'runtime package directory required')
    identities=set();observed={}
    for name,wanted in RUNTIME_SOURCE_PINS.items():
        path=package/name
        for part in (path,)+tuple(path.parents):
            require(not part.is_symlink(),'runtime source symlink refused')
            if part==package:break
        descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        with os.fdopen(descriptor,'rb') as source:
            before=os.fstat(source.fileno());identity=(before.st_dev,before.st_ino)
            require(stat_mode.S_ISREG(before.st_mode) and before.st_nlink==1 and identity not in identities and
                    0<before.st_size==wanted['bytes']<=65536,'regular bounded unique runtime source required')
            identities.add(identity);digest=hashlib.sha256();count=0
            while True:
                block=source.read(min(65536,before.st_size-count+1))
                if not block:break
                count+=len(block);require(count<=before.st_size,'runtime source grew during read');digest.update(block)
            after=os.fstat(source.fileno())
        require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns,before.st_nlink)==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_nlink) and
                count==before.st_size and digest.hexdigest()==wanted['sha256'],'runtime source bytes changed')
        observed[name]={'bytes':count,'sha256':digest.hexdigest()}
    require(hashlib.sha256(json.dumps(observed,sort_keys=True,separators=(',',':')).encode()).hexdigest()==
            RUNTIME_SOURCE_MANIFEST_SHA,'frozen runtime manifest mismatch')
    return RUNTIME_SOURCE_MANIFEST_SHA


def _configured_clock(value):
    require(type(value) in (int,float) and math.isfinite(value) and value==100.0,
            'configured FCLK0 must be finite numeric100; not a physical frequency measurement')
    return value


def _startup_preflight(request,ctx,pynq,clocks):
    mode='require_operating';expected_manager='operating'
    if 'startup_policy' in request:
        policy=request['startup_policy']
        require(type(policy) is dict and set(policy)=={'mode','expected_boot_id','expected_manager_state',
                'expected_fclk0_mhz','runtime_source_manifest_sha256','vendor_download_effects_acknowledged'},
                'exact six-key cold policy required')
        require(type(policy['mode']) is str and policy['mode']=='root_released_unknown_start' and
                type(policy['expected_boot_id']) is str and policy['expected_boot_id']==ctx['boot_id'] and
                type(policy['expected_manager_state']) is str and policy['expected_manager_state']=='unknown' and
                type(policy['runtime_source_manifest_sha256']) is str and
                policy['runtime_source_manifest_sha256']==RUNTIME_SOURCE_MANIFEST_SHA and
                policy['vendor_download_effects_acknowledged'] is True,'explicit current-boot pinned cold policy required')
        _configured_clock(policy['expected_fclk0_mhz'])
        mode=policy['mode'];expected_manager='unknown'
    require(pynq.__version__=='3.0.1' and RUNTIME_SOURCE_PINS['__init__.py']['sha256']==PYNQ_SHA,
            'current runtime module mismatch')
    runtime_manifest=_runtime_sources(Path(pynq.__file__).parent)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    manager=Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()
    configured=_configured_clock(clocks.fclk0_mhz)
    require(boot==ctx['boot_id'] and manager==expected_manager,'current startup boot/manager mismatch; no fallback')
    return {'mode':mode,'boot_id':boot,'manager_state':manager,'configured_fclk0_mhz':configured,
            'runtime_source_manifest_sha256':runtime_manifest,'physical_clock_proof':False,
            'vendor_download_effects':'unchanged PYNQ clock/internalMMIO/cache/global-state/firmware/XRT path'}


def _post_programming(ctx,clocks):
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    manager=Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()
    configured=_configured_clock(clocks.fclk0_mhz)
    require(boot==ctx['boot_id'] and manager=='operating','post-download boot/manager mismatch')
    return {'boot_id':boot,'manager_state':manager,'configured_fclk0_mhz':configured,'physical_clock_proof':False}


def _read_credential(fd):
    data=bytearray();end=time.monotonic()+5
    os.set_blocking(fd,False)
    while len(data)<128:
        remaining=end-time.monotonic();require(remaining>0,'private credential deadline')
        readable,_,_=select.select([fd],[],[],remaining);require(readable,'private credential deadline')
        try:byte=os.read(fd,1)  # Deliberately no read-ahead into protocol data.
        except BlockingIOError:continue
        require(byte and byte not in (b'\r',b'\x00'),'invalid private credential line')
        data.extend(byte)
        if byte==b'\n':
            require(len(data)>1,'empty private credential');return bytes(data)
    raise ValueError('private credential line exceeds bound')


def _send_sudo_credential(private_pipe,credential):
    require(type(credential) is bytes and 1<len(credential)<=128 and credential.endswith(b'\n'),'bounded private credential required')
    try:
        require(private_pipe.write(credential)==len(credential),'private credential pipe write failed')
        private_pipe.flush()
    finally:private_pipe.close()


def _validate_fifo(path,fd,device,inode,owner):
    for part in (path,)+tuple(path.parents):require(not part.is_symlink(),'FIFO symlink refused')
    value=path.lstat() if fd is None else os.fstat(fd)
    require(stat_mode.S_ISFIFO(value.st_mode) and value.st_nlink==1 and stat_mode.S_IMODE(value.st_mode)==0o600 and
            (value.st_dev,value.st_ino,value.st_uid)==(device,inode,owner),'original FIFO type/mode/identity/owner mismatch')
    return value


def _relay_stage(root,stage,request_sha,agent_sha,fifo_identity,*,child_pid=None,exit_code=None,
                 reason_code=None,child_start_ticks=None,forwarded_data_bytes=0):
    require(stage in ('created','sudo_started','unknown','local_cleanup','completed'),'fixed relay stage required')
    require(reason_code in (None,'RELAY_ERROR_UNKNOWN','ORIGINAL_CHILD_TERMINAL'),'fixed nonsecret reason code only')
    require(all(type(x) is int and x>=0 for x in fifo_identity),'original numeric FIFO identity required')
    value={'stage':stage,'request_file_sha256':request_sha,'agent_sha256':agent_sha,
           'fifo_identity':dict(zip(('device','inode','owner'),fifo_identity)),
           'original_child_pid':child_pid,'original_child_start_ticks':child_start_ticks,
           'child_identity_basis':'original subprocess.Popen object; PID alone is correlation',
           'original_child_exit':exit_code,'original_wait_completed':exit_code is not None,
           'reason_code':reason_code,'forwarded_data_bytes':forwarded_data_bytes,
           'credential_recorded_or_hashed':False,'remote_STOP_not_inferred':True,'automatic_retry':False}
    with (root/('RELAY_'+stage+'.json')).open('xb') as stream:
        stream.write(json.dumps(value,sort_keys=True,allow_nan=False).encode());stream.flush();os.fsync(stream.fileno())


def _pump_input(fd,writer,child,total_seconds):
    end=time.monotonic()+total_seconds;buffer=bytearray();total=0
    try:
        os.set_blocking(fd,False);os.set_blocking(writer,False)
        while child.poll() is None:
            remaining=end-time.monotonic()
            if remaining<=0:raise TimeoutError('original relay deadline; remote outcome unknown')
            reads,writes,_=select.select([fd] if not buffer else [],[writer] if buffer else [],[],min(remaining,0.1))
            if reads:
                block=os.read(fd,4096)
                if not block:return {'data_bytes':total,'input_EOF':True}
                total+=len(block);require(total<=32768,'finite original relay data budget exceeded');buffer.extend(block)
            if writes:
                try:count=os.write(writer,buffer)
                except BlockingIOError:continue
                require(type(count) is int and 0<count<=len(buffer),'original FIFO forward failed')
                del buffer[:count]
        return {'data_bytes':total,'child_terminal_before_EOF':True}
    finally:os.close(writer)  # Only this relay owns the one writer; EOF reaches root agent.


def _read_prelude(fd,end):
    position=0
    while position<len(PRIVATE_PRELUDE):
        remaining=end-time.monotonic();require(remaining>0,'private transport prelude deadline')
        ready,_,_=select.select([fd],[],[],min(remaining,0.05))
        if not ready:continue
        try:byte=os.read(fd,1)
        except BlockingIOError:continue
        if not byte:
            require(position==0,'private transport prelude ended early');time.sleep(0.001);continue
        require(byte==PRIVATE_PRELUDE[position:position+1],'fixed private prelude mismatch')
        position+=1


def _send_prelude(fd,end):
    remaining=end-time.monotonic();require(remaining>0,'private transport write deadline')
    _,ready,_=select.select([],[fd],[],remaining);require(ready,'private transport prelude write timeout')
    require(os.write(fd,PRIVATE_PRELUDE)==len(PRIVATE_PRELUDE),'partial original prelude; no retry')


def _qualification_output(item,end):
    raw=(json.dumps(item,sort_keys=True,allow_nan=False)+'\n').encode();require(len(raw)<=4096,'fixed qualification output bound')
    os.set_blocking(1,False)
    remaining=end-time.monotonic();require(remaining>0,'qualification output deadline')
    _,ready,_=select.select([],[1],[],remaining);require(ready,'qualification output blocked')
    require(os.write(1,raw)==len(raw),'qualification output short/unknown')


def _open_fifo(args,request):
    deadline=time.monotonic()+5  # Established before any open/read; no runtime/image before handshake.
    root=args.request.absolute().parent;path=args.input_fifo
    require(path==root/'LIVE_INPUT.fifo' and request['relay_owner_uid']==args.fifo_owner,'fixed fresh FIFO owner/path required')
    value=root.lstat();require(root.is_dir() and not root.is_symlink() and
            stat_mode.S_IMODE(value.st_mode)==0o700 and value.st_uid==args.fifo_owner,'fresh0700 operation owner required')
    _validate_fifo(path,None,args.fifo_device,args.fifo_inode,args.fifo_owner)
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|getattr(os,'O_NOFOLLOW',0))
    try:
        _validate_fifo(path,fd,args.fifo_device,args.fifo_inode,args.fifo_owner)
        _read_prelude(fd,deadline)
    except BaseException:os.close(fd);raise
    # Replace raw fd0 before any runtime import. No old sys.stdin buffered reads occur.
    if fd!=0:os.dup2(fd,0,inheritable=False);os.close(fd)
    _validate_fifo(path,0,args.fifo_device,args.fifo_inode,args.fifo_owner)
    return 0


def _qualification(args,request):
    require(os.geteuid()==0 and request['phase']=='relay_qualification' and request['execute_a'] is False,
            'fixed root FIFO-only qualification required')
    fd=None
    try:
        fd=_open_fifo(args,request)
        os.set_blocking(fd,False)
        require('pynq' not in sys.modules,'PYNQ not permitted in FIFO-only qualification')
        deadline=time.monotonic()+5
        # No PYNQ import, helper load, image or register operation in this entry.
        ready={'kind':'relay_qualification_ready','root_euid':os.geteuid(),'fifo_inode':args.fifo_inode,
               'fifo_owner':args.fifo_owner,'PYNQ_imported':'pynq' in sys.modules}
        _qualification_output(ready,min(deadline,time.monotonic()+1))
        data=bytearray();eof=False
        while time.monotonic()<deadline:
            read,_,_=select.select([fd],[],[],max(0,deadline-time.monotonic()))
            if not read:break
            block=os.read(fd,65-len(data));require(len(data)+len(block)<=64,'fixed sentinel input bound')
            if not block:eof=True;break
            data.extend(block)
        require(eof and bytes(data)==QUALIFICATION_SENTINEL,'fixed nonsecret sentinel/EOF mismatch')
        terminal={'kind':'relay_qualification_complete','sentinel_match':True,'FIFO_EOF':True,'root_euid':0,
                  'fifo_inode':args.fifo_inode,'fifo_owner':args.fifo_owner,'PYNQ_imported':'pynq' in sys.modules,'physical_board':'not_run'}
        path=args.request.parent/'QUALIFICATION_TERMINAL.json'
        with path.open('xb') as stream:stream.write(json.dumps(terminal,sort_keys=True).encode());stream.flush();os.fsync(stream.fileno())
        _qualification_output(terminal,min(deadline,time.monotonic()+1));return 0
    except BaseException as error:
        failure={'reason_code':'QUALIFICATION_IO_FAILURE','error_type':type(error).__name__,
                 'fifo_inode':args.fifo_inode,'fifo_owner':args.fifo_owner,
                 'PYNQ_imported':'pynq' in sys.modules,'physical_board':'not_run','exit_code':2}
        with (args.request.parent/'QUALIFICATION_FAILURE.json').open('xb') as stream:
            stream.write(json.dumps(failure,sort_keys=True).encode());stream.flush();os.fsync(stream.fileno())
        return 2
    finally:
        if fd is not None:os.close(fd)


def _relay(args,qualification=False):
    require(os.name=='posix' and os.geteuid()!=0,'original unprivileged Linux relay required')
    credential=_read_credential(0);child=None;writer=None;created=None;terminal=False;root=args.request.absolute().parent
    identity=None;child_ticks=None;agent_sha=None
    try:
        raw=args.request.read_bytes();require(len(raw)<=16384 and hashlib.sha256(raw).hexdigest()==args.request_sha256,'relay request pin mismatch')
        request=json.loads(raw);agent_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        require(request['agent_sha256']==agent_sha,'relay source pin differs')
        require(request['phase']==('relay_qualification' if qualification else 'private_live') and
                request['execute_a'] is (not qualification) and type(request['attempts']) is int and request['attempts']==1,
                'fixed relay phase/attempt required')
        owner=os.geteuid();value=root.lstat()
        require(not root.is_symlink() and value.st_uid==owner and stat_mode.S_IMODE(value.st_mode)==0o700 and
                request['relay_owner_uid']==owner,'fresh0700 own operation directory required')
        fifo=root/'LIVE_INPUT.fifo';os.mkfifo(fifo,0o600);created=fifo.lstat();_validate_fifo(fifo,None,created.st_dev,created.st_ino,owner)
        identity=(created.st_dev,created.st_ino,owner)
        _relay_stage(root,'created',args.request_sha256,agent_sha,identity)
        command=['/usr/bin/sudo','-S','-p','','/usr/bin/env','BOARD=Pynq-Z2','XILINX_XRT=/usr',
                 '/usr/local/share/pynq-venv/bin/python3','-I','-B',str(Path(__file__).absolute()),
                 '--request',str(args.request.absolute()),'--request-sha256',args.request_sha256,
                 '--input-fifo',str(fifo),'--fifo-device',str(created.st_dev),'--fifo-inode',str(created.st_ino),'--fifo-owner',str(owner)]
        command+=['--fifo-qualification'] if qualification else ['--execute-a']
        child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=None,stderr=None,close_fds=True)
        try:child_ticks=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()[19]
        except OSError:pass
        _relay_stage(root,'sudo_started',args.request_sha256,agent_sha,identity,child_pid=child.pid,child_start_ticks=child_ticks)
        _send_sudo_credential(child.stdin,credential);credential=None
        end=time.monotonic()+180
        while writer is None:
            require(child.poll() is None,'original sudo exited before FIFO open')
            require(time.monotonic()<end,'original FIFO peer open timed out')
            try:writer=os.open(fifo,os.O_WRONLY|os.O_NONBLOCK|getattr(os,'O_NOFOLLOW',0))
            except OSError as error:
                if error.errno!=errno.ENXIO:raise
                time.sleep(0.001)
        _validate_fifo(fifo,writer,created.st_dev,created.st_ino,owner)
        _send_prelude(writer,time.monotonic()+5)
        owned_writer=writer;writer=None
        forwarded=_pump_input(0,owned_writer,child,max(0.001,end-time.monotonic()))
        code=child.wait(timeout=max(0.001,end-time.monotonic()));terminal=True
        _relay_stage(root,'completed',args.request_sha256,agent_sha,identity,child_pid=child.pid,exit_code=code,
                     child_start_ticks=child_ticks,reason_code='ORIGINAL_CHILD_TERMINAL',forwarded_data_bytes=forwarded['data_bytes'])
        if code==0:
            _validate_fifo(fifo,None,created.st_dev,created.st_ino,owner);fifo.unlink()
        return code
    except BaseException:
        # Credential contents/hash/repr never enter records or exception text.
        raise ValueError('RELAY_ERROR_UNKNOWN') from None
    finally:
        credential=None
        if writer is not None:os.close(writer)
        if identity is not None and not terminal:
            try:_relay_stage(root,'unknown',args.request_sha256,agent_sha,identity,child_pid=None if child is None else child.pid,
                             child_start_ticks=child_ticks,reason_code='RELAY_ERROR_UNKNOWN')
            except BaseException:pass  # Record-I/O failure cannot suppress original-handle cleanup/EOF.
        if child is not None and not terminal:
            # Exact original handle only. Its exit does NOT establish root-agent STOP/exit.
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
            try:_relay_stage(root,'local_cleanup',args.request_sha256,agent_sha,identity,child_pid=child.pid,
                             child_start_ticks=child_ticks,exit_code=child.returncode,reason_code='RELAY_ERROR_UNKNOWN')
            except BaseException:pass
            # Unknown FIFO/root-agent state is deliberately retained; no unlink/replay.


def _session_limits(total_seconds,poll_seconds,max_scans,idle_timeout_ms=None):
    require(type(total_seconds) in (int,float) and 0<total_seconds<=10,'bounded total required')
    require(type(poll_seconds) in (int,float) and 0<poll_seconds<=2,'bounded poll required')
    require(type(max_scans) is int and 1<=max_scans<=16,'finite scan budget required')
    if idle_timeout_ms is not None:
        require(type(idle_timeout_ms) is int and 1<=idle_timeout_ms<=100,'input idle cap100ms required')


def _validated_session_timing(request,codec):
    """Pinned codec policy, before FIFO/runtime/image/MMIO; no physical side effects."""
    timing=codec.request_timing(request)
    _session_limits(request['total_seconds'],request['poll_seconds'],request['max_scans'])
    return timing


class _CleanupSignals:
    def __enter__(self):
        self.old={};self.errors=[]
        for sig in (signal.SIGINT,signal.SIGTERM):
            try:self.old[sig]=signal.signal(sig,signal.SIG_IGN)
            except BaseException as error:self.errors.append({'stage':'mask_signal','type':type(error).__name__})
        return self
    def __exit__(self,*ignored):
        for sig,handler in self.old.items():
            try:signal.signal(sig,handler)
            except BaseException as error:self.errors.append({'stage':'restore_signal','type':type(error).__name__})


def _stop_without_session(bus,reason):
    """Raw STOP first, independent of normal Bus/clock/log, with signal masking."""
    mmio=getattr(bus,'mmio',bus)
    result={'attempted':False,'confirmed':False,'reason':reason,'outcome':'unknown',
            'physical_deadline_proven':False,'secondary_errors':[],'raw_readback':[]}
    with _CleanupSignals() as mask:
        try:
            result['attempted']=True;mmio.write(0x0c,1)
        except BaseException as error:result['secondary_errors'].append({'stage':'raw_STOP_write','type':type(error).__name__,'message':str(error)[:512]})
        for _ in range(32):
            try:
                status=mmio.read(8);tag=mmio.read(0x14);result['raw_readback'].append({'status':status,'active_tag':tag})
                if type(status) is int and type(tag) is int and status==0 and tag==0:
                    result.update(confirmed=True,status=0,active_tag=0,outcome='confirmed');break
            except BaseException as error:
                result['secondary_errors'].append({'stage':'raw_STOP_readback','type':type(error).__name__,'message':str(error)[:512]});break
    result['secondary_errors'].extend(mask.errors)
    return result


class _LiveSession:
    """Explicit FSM core; dependency doubles are component evidence only."""
    def __init__(self,bus,helpers,ctx,clock,sleep,journal,*,total_seconds,poll_seconds,max_scans):
        _session_limits(total_seconds,poll_seconds,max_scans)
        self.bus,self.h,self.context,self.clock,self.sleep,self.journal=bus,helpers,dict(ctx),clock,sleep,journal
        self._emergency_mmio=getattr(bus,'mmio',bus)  # Actual helper.Bus exposes its original MMIO directly.
        self.total,self.poll,self.max_scans=total_seconds,poll_seconds,max_scans
        self.state='NEW';self.cleanup=None;self.sequence=1;self._high=clock();self.end=self._high+total_seconds
        self._last_qpc=0;self.generation=self.trigger=None;self.baseline=None
    def _event(self,event,**fields):self.journal({'event':event,**fields})
    def _guard(self):
        now=self.clock();require(type(now) in (int,float) and now>=self._high,'session monotonic clock reversed')
        self._high=now;require(now<self.end,'global session deadline');return now
    def _deadline(self):return min(self.end,self._guard()+self.poll)
    def _session(self):self.h.session(self.bus,self.context['tag'],self.generation,self.trigger)
    def start(self):
        require(self.state=='NEW','START is single use')
        self.state='STARTED_UNKNOWN'
        try:
            self._guard();require(self.bus.read(0)==0x44505953 and self.bus.read(4)==0x10000,'private identity mismatch')
            self._event('startup_stop_started_unknown');self.bus.write(12,1)
            self.h.wait_for(self.bus,lambda s:s==0,self.clock,self.sleep,self._deadline(),'startup STOP',check_fault=False)
            require(self.bus.read(0x14)==0,'startup active tag not zero')
            old=self.bus.read(0x18);require(type(old) is int and 0<=old<U32,'generation exhausted')
            self.bus.write(0x10,self.context['tag']);require(self.bus.read(0x10)==self.context['tag'],'staged tag mismatch')
            self._event('start_started_unknown');self.bus.write(12,2)
            self.h.wait_for(self.bus,lambda s:s==1,self.clock,self.sleep,self._deadline(),'START')
            self.generation=old+1;self.trigger=self.bus.read(0x1c);self._session()
            self.baseline=tuple(self.h.counters(self.bus));self.state='ACTIVE';self._event('start_returned',generation=self.generation)
            return {'generation':self.generation,'trigger_id':self.trigger,'baseline_counters':list(self.baseline)}
        except BaseException:self.state='FAILED';raise
    def scan(self,request):
        require(self.state=='ACTIVE','session terminal or request already started/unknown')
        try:
            require(type(request['request_seq']) is int and request['request_seq']==self.sequence<=self.max_scans,'new contiguous request required')
            require(request['context']==self.context and request['original_host_qpc_ns'][0]>self._last_qpc,'context/original QPC replay')
            self.state='STARTED_UNKNOWN';self._guard();self._session()
            require(self.bus.read(8)==1,'not idle before scan')
            require(self.trigger<U32 and all(x+n<=U32 for x,n in zip(self.baseline,(4*self.sequence,self.sequence,4*self.sequence))),
                    'counter/trigger exhaustion')
            self._last_qpc=request['original_host_qpc_ns'][-1]
            for channel in range(4):
                self._guard();tick=request['original_host_qpc_ns'][channel]
                self.bus.write(0x40+4*channel,request['values'][channel])
                self.bus.write(0x50+8*channel,tick&U32);self.bus.write(0x54+8*channel,tick>>32)
            self.bus.write(0x70,sum(q<<(8*i) for i,q in enumerate(request['qualities'])))
            self._guard();self._session();require(self.bus.read(8)==1,'state changed during staging')
            self._event('trigger_started_unknown',request_seq=self.sequence);self.bus.write(12,4)
            require(self.bus.read(0x1c)==self.trigger+1,'new actual trigger not observed')
            self.trigger+=1;self._session();captures=[]
            for channel in range(4):
                self.h.wait_for(self.bus,lambda s:s==7,self.clock,self.sleep,self._deadline(),'result lane')
                raw=tuple(self.bus.read(offset) for offset in self.h.RESULT_REGS)
                self._guard();require(self.bus.read(8)==7,'lane changed during read');self._session()
                require(tuple(self.bus.read(offset) for offset in self.h.RESULT_REGS)==raw and self.bus.read(8)==7,'lane unstable before ACK')
                tick=request['original_host_qpc_ns'][channel]
                expected=(request['values'][channel],channel|(request['qualities'][channel]<<8),tick&U32,tick>>32,
                          4*(self.sequence-1),4*self.sequence-1,self.context['tag'],self.trigger,self.generation)
                require(raw[:9]==expected,'raw lane data/quality/QPC/sequence/session mismatch')
                counts=(self.baseline[0]+4*self.sequence,self.baseline[1]+self.sequence,
                        self.baseline[2]+4*(self.sequence-1)+channel+1)
                require(tuple(self.h.counters(self.bus))==counts,'pipeline counters mismatch');self._session();self._guard()
                lane={'channel':channel,'raw_words':list(raw),'pipeline_counters':list(counts),'ack_returned':False}
                captures.append(lane);self._event('ack_started_unknown',request_seq=self.sequence,channel=channel,raw_words=list(raw))
                self.bus.write(12,8);lane['ack_returned']=True
                self._event('ack_returned',request_seq=self.sequence,channel=channel)
            self.h.wait_for(self.bus,lambda s:s==1,self.clock,self.sleep,self._deadline(),'four ACK idle');self._session();self._guard()
            require(tuple(self.h.counters(self.bus))==counts,'post-ACK counters changed')
            self.sequence+=1;self.state='ACTIVE'
            return {'generation':self.generation,'trigger_id':self.trigger,'captures':captures,'final_counters':list(counts)}
        except BaseException:self.state='FAILED';raise
    def finish(self,reason):
        if self.cleanup is not None:return self.cleanup
        self.state='CLOSED'
        # Cache only after a protected actual STOP attempt, never an unattempted placeholder.
        self.cleanup=_stop_without_session(self._emergency_mmio,reason)
        try:self.cleanup['clock_after_STOP']=self.clock()
        except BaseException as error:self.cleanup['secondary_errors'].append({'stage':'clock_after_STOP','type':type(error).__name__})
        try:self._event('session_finished',cleanup=self.cleanup)
        except BaseException as error:
            self.cleanup['secondary_errors'].append({'stage':'terminal_journal','type':type(error).__name__})
        return self.cleanup


def _serve(session,read_next,write,codec,profile=None):
    error=None
    try:
        ready=session.start();write(codec.record('diagnostic_ready',session.context,**ready))
        while session.sequence<=session.max_scans:
            raw=read_next()
            if raw is None:break
            request=codec.decode_request(raw,session.context,session.sequence)
            _arm_metric_call(profile,'set_phase',session.sequence)
            result=session.scan(request)
            _arm_metric_call(profile,'set_phase',3)
            write(codec.record('diagnostic_capture',session.context,request_seq=request['request_seq'],
                               request_sha256=hashlib.sha256(raw).hexdigest(),**result))
    except BaseException as failure:error={'type':type(failure).__name__,'message':str(failure)[:512]}
    finally:
        session.primary_error=error
        session.secondary_errors=[]
        cleanup=session.finish('input EOF/budget' if error is None else 'failure/signal')
        try:
            write(codec.record('diagnostic_stopped',session.context,cleanup=cleanup,error=error,
                               frames_completed=session.sequence-1,movement_authorized=False))
        except BaseException as failure:
            secondary={'stage':'terminal_stdout','type':type(failure).__name__,'message':str(failure)[:512]}
            session.secondary_errors.append(secondary)
            try:session._event('terminal_output_failed',primary_error=error,secondary_error=secondary)
            except BaseException as journal_error:session.secondary_errors.append({'stage':'terminal_error_journal','type':type(journal_error).__name__})
    return 0 if error is None and cleanup['confirmed'] and not cleanup['secondary_errors'] and not session.secondary_errors else 2


class _InputLines:
    def __init__(self,fd,session,idle_seconds,limit):
        self.fd,self.session,self.idle,self.limit=fd,session,idle_seconds,limit;self.buffer=bytearray()
        os.set_blocking(fd,False)
    def __call__(self):
        end=min(self.session.end,time.monotonic()+self.idle)
        while True:
            self.session._guard()
            if b'\n' in self.buffer:
                pos=self.buffer.index(10)+1;raw=bytes(self.buffer[:pos]);del self.buffer[:pos];return raw
            require(len(self.buffer)<self.limit,'input line exceeds limit')
            remaining=end-time.monotonic();require(remaining>0,'input idle/global deadline')
            available,_,_=select.select([self.fd],[],[],remaining)
            require(available,'input idle deadline')
            block=os.read(self.fd,min(4096,self.limit-len(self.buffer)))
            if not block:
                require(not self.buffer,'EOF inside diagnostic frame');return None
            self.buffer.extend(block)


class _OutputLines:
    """Original Linux stdout fd, nonblocking writes under the live session deadline."""
    def __init__(self,fd,session,codec,timeout_seconds):
        self.fd,self.session,self.codec,self.timeout=fd,session,codec,timeout_seconds
        require(0<timeout_seconds<=0.1,'bounded diagnostic output timeout required')
        os.set_blocking(fd,False)
    def __call__(self,item):
        raw=self.codec.encode(item);deadline=min(self.session.end,self.session._guard()+self.timeout);position=0
        while position<len(raw):
            remaining=deadline-self.session._guard();require(remaining>0,'original output deadline')
            _,ready,_=select.select([],[self.fd],[],remaining);require(ready,'original output blocked/deadline')
            try:count=os.write(self.fd,raw[position:])
            except BlockingIOError:continue
            require(type(count) is int and 0<count<=len(raw)-position,'short/failed original output write')
            position+=count


# Root opt-in is diagnostic only; the original execution permissions remain necessary.
_ARM_PROFILE_POLICY_SHA='ce2b05d1bcc0da2010f29f7b4125c2431b3492e44a40bbd5c3eb102e46cec1ea'
_ARM_PROFILE_U64=(1<<64)-1


def _arm_profile_enabled(request):
    if 'arm_journal_profile' not in request:return False
    option=request['arm_journal_profile']
    require(type(option) is dict and set(option)=={'schema','enabled','policy_sha256'} and
            type(option['schema']) is int and option['schema']==1 and option['enabled'] is True and
            type(option['policy_sha256']) is str and option['policy_sha256']==_ARM_PROFILE_POLICY_SHA,
            'exact Root journal profile policy required')
    require(request.get('phase')=='private_live' and request.get('execute_a') is True and
            type(request.get('attempts')) is int and request['attempts']==1 and
            type(request.get('max_scans')) is int and 1<=request['max_scans']<=2,
            'journal profiling requires original private live single attempt and one or two scans')
    return True


class _ArmJournalProfile:
    """Fixed diagnostic storage. Ordinary failures disable metrics, never evidence I/O."""
    def __init__(self):
        self.stats=[[stage,phase,0,0,0,0,0,0,None,None,None,None] for phase in range(5) for stage in range(5)]
        self.endpoints=[[None]*15 for _ in range(32)]
        self.seen=[False]*5;self.phase=0;self.slot=None;self.used=0;self.last_clock=None
        self.disabled=False;self.reason_bits=0;self.overflow_bits=0;self.binding=None
        self.publication_attempted=False
    def disable(self,reason):
        self.disabled=True;self.reason_bits|=reason
    def set_phase(self,phase):
        if type(phase) is not int or not 0<=phase<4:self.disable(16);return
        self.phase=phase
    def _add(self,row,column,value=1):
        if row[column]>_ARM_PROFILE_U64-value:
            row[column]=_ARM_PROFILE_U64;self.overflow_bits|=1<<column;self.disable(4)
        else:row[column]+=value
    def _sample(self):
        try:value=time.monotonic_ns()
        except (InterruptedError,KeyboardInterrupt,SystemExit,GeneratorExit):raise
        except Exception:self.disable(1);return None
        if type(value) is not int or not 0<=value<=_ARM_PROFILE_U64:self.disable(1);return None
        if self.last_clock is not None and value<self.last_clock:self.disable(2);return None
        self.last_clock=value;return value
    def begin_record(self,index,stamp,item):
        self.slot=None
        for i in range(5):self.seen[i]=False
        if type(stamp) is not int or not 0<=stamp<=_ARM_PROFILE_U64 or self.last_clock is not None and stamp<self.last_clock:
            self.disable(2);return
        self.last_clock=stamp
        if type(item) is not dict or type(item.get('event')) is not str:return
        event=item['event']
        if event=='session_finished':self.phase=4
        if not (event.endswith('started_unknown') or event in ('session_finished','post_programming_verified')):return
        if self.used>=32:self.disable(32);return
        names=('image_load_started_unknown','post_programming_verified','startup_stop_started_unknown',
               'start_started_unknown','trigger_started_unknown','ack_started_unknown','session_finished')
        code=names.index(event) if event in names else 7
        row=self.endpoints[self.used];self.slot=self.used;self.used+=1
        seq=item.get('request_seq',item.get('seq'));lane=item.get('channel',item.get('lane'))
        row[0]=index;row[1]=code;row[2]=self.phase
        row[3]=seq if type(seq) is int and 0<=seq<=_ARM_PROFILE_U64 else None
        row[4]=lane if type(lane) is int and 0<=lane<4 else None
        row[5]=stamp;row[14]=0
    def start(self,stage):
        begin=self._sample()
        if begin is not None and self.slot is not None:self.endpoints[self.slot][(None,7,9,11)[stage]]=begin
        return begin
    def returned(self,stage,begin):
        row=self.stats[self.phase*5+stage];self._add(row,3);self._add(row,4);self.seen[stage]=True
        if stage==4 and self.slot is not None:self.endpoints[self.slot][14]=1
        if self.disabled:return
        end=self._sample()
        if end is None:return
        if self.slot is not None:self.endpoints[self.slot][(6,8,10,12,13)[stage]]=end
        if begin is None:return
        if end<begin:self.disable(2);return
        duration=end-begin;self._add(row,6);self._add(row,7,duration)
        row[8]=duration if row[8] is None else min(row[8],duration)
        row[9]=duration if row[9] is None else max(row[9],duration)
        if row[10] is None:row[10]=begin
        row[11]=end
    def failed(self,stage):
        # No clock call while preserving an original exception or interruption.
        for value in (stage,4) if stage!=4 else (4,):
            if not self.seen[value]:
                row=self.stats[self.phase*5+value];self._add(row,3);self._add(row,5);self.seen[value]=True
        if self.slot is not None and self.endpoints[self.slot][14]!=1:self.endpoints[self.slot][14]=2
        self.disable(8)


def _arm_metric_call(profile,method,*args):
    if profile is None or profile.disabled:return None
    try:return getattr(profile,method)(*args)
    except (InterruptedError,KeyboardInterrupt,SystemExit,GeneratorExit):raise
    except Exception:profile.disable(16);return None


def _arm_profile_binding(profile,request,ctx,request_sha):
    # Called only after source/request checks and before FIFO/runtime/START; no clock sample.
    try:
        info=time.get_clock_info('monotonic');pid=os.getpid()
        with Path('/proc/self/stat').open('rb') as stream:
            raw=stream.read(4097);require(len(raw)<=4096,'bounded original process identity required')
        ticks=raw.rsplit(b')',1)[1].split()[19].decode('ascii')
        require(ticks.isdecimal() and info.monotonic,'original monotonic process identity required')
        profile.binding={'context':dict(ctx),'request_file_sha256':request_sha,
            'sources':{'agent_sha256':request['agent_sha256'],'collector_sha256':COLLECTOR_SHA,'codec_sha256':request['codec_sha256']},
            'clock':{'domain_id':os.urandom(16).hex(),'kind':'agent_linux_monotonic_ns','host_domain_id':ctx['clock_domain_id'],
                     'boot_id':ctx['boot_id'],'pid':pid,'native_thread_id':threading.get_native_id(),'process_start_ticks':ticks,
                     'implementation':info.implementation,'nominal_resolution_seconds':info.resolution,
                     'authenticated':False,'measured_timing':False,'clock_conversion':'not_established'}}
    except (InterruptedError,KeyboardInterrupt,SystemExit,GeneratorExit):raise
    except Exception:profile.disable(64)


def _arm_profile_pin(path,limit):
    require(not path.is_symlink() and not path.parent.is_symlink(),'diagnostic original link refused')
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno())
        require(stat_mode.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded closed original required')
        digest=hashlib.sha256();count=0
        while True:
            block=stream.read(min(65536,before.st_size-count+1))
            if not block:break
            count+=len(block);require(count<=before.st_size,'closed original grew');digest.update(block)
        after=os.fstat(stream.fileno())
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns,before.st_nlink)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_nlink) and count==before.st_size,
            'closed original changed during diagnostic hash')
    return {'bytes':count,'sha256':digest.hexdigest()}


def _arm_profile_publish(profile,out,cleanup,terminal_written,originals_closed):
    # A JSON payload cannot self-attest its subsequent write/flush/close. No ACK or retry.
    if profile is None or profile.publication_attempted or not terminal_written or not originals_closed or not cleanup.get('attempted'):
        return False
    profile.publication_attempted=True;stream=None
    try:
        value={'schema':1,'kind':'private_live_arm_journal_profile','policy_sha256':_ARM_PROFILE_POLICY_SHA,
               'binding':profile.binding,'stats':profile.stats,'durable_endpoints':profile.endpoints,'durable_used':profile.used,
               'status':{'measurement_complete':not profile.disabled,'producer_publication':'not_self_attested',
                         'reason_bits':profile.reason_bits,'overflow_bits':profile.overflow_bits,
                         'after_original_cleanup':True,'raw_STOP_confirmed':cleanup.get('confirmed') is True},
               'originals':{'operations.jsonl':_arm_profile_pin(out/'operations.jsonl',8*1024*1024),
                            'TERMINAL.json':_arm_profile_pin(out/'TERMINAL.json',65536)},
               'bare_mmio_available':False,'raw_STOP':{'begin_ns':None,'write_end_ns':None,'end_ns':None,'duration_ns':None},
               'append_duration':'includes_instrumentation_no_subtraction','formal_acceptance':'not_run','clock_conversion':'not_established'}
        raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
        require(len(raw)<=65536,'fixed journal profile sidecar bound')
        stream=(out/'STAGE_METRICS.json').open('xb')
        require(stream.write(raw)==len(raw),'short diagnostic sidecar write');stream.flush()
    except (InterruptedError,KeyboardInterrupt,SystemExit,GeneratorExit):raise
    except Exception:profile.disable(128);return False
    finally:
        if stream is not None:
            try:stream.close()
            except (InterruptedError,KeyboardInterrupt,SystemExit,GeneratorExit):raise
            except Exception:profile.disable(128)
    return not bool(profile.reason_bits&128)


class _Journal:
    def __init__(self,path,max_bytes=8*1024*1024,profile=None):
        require(profile is None or type(profile) is _ArmJournalProfile,'fixed journal profiler only')
        self._arm_profile=profile
        self.stream=path.open('xb');self.count=0;self.limit=max_bytes;self.index=0
        # Formatting-only cache. Bus permissions and every evidence I/O remain unchanged.
        self._mmio_fragments={}
        offsets=(('read',('0x0','0x4','0x8','0x10','0x14','0x18','0x1c','0x20','0x24','0x28','0x30','0x34',
                          '0x80','0x84','0x88','0x8c','0x90','0x94','0x98','0x9c','0xa0','0xa4')),
                 ('write',('0xc','0x10','0x40','0x44','0x48','0x4c','0x50','0x54','0x58','0x5c','0x60','0x64','0x68','0x6c','0x70')))
        for operation,allowed in offsets:
            for event in ('mmio_attempt','mmio_returned'):
                for offset in allowed:
                    middle=b', "event": "'+event.encode('ascii')+b'", "index": '
                    tail=b', "offset": "'+offset.encode('ascii')+b'", "operation": "'+operation.encode('ascii')+b'"'
                    self._mmio_fragments[(event,operation,offset)]=(middle,tail,operation=='write' or event=='mmio_returned')
    def event(self,event,**fields):self.append({'event':event,**fields})
    def _mmio_bytes(self,item,index,stamp):
        # Unsupported shapes/types always use the original generic encoder.
        if type(item) is not dict or type(index) is not int or type(stamp) is not int:return None
        if not (0<=index<(1<<64) and 0<=stamp<(1<<64)):return None
        if any(type(key) is not str for key in item):return None
        event,operation,offset=item.get('event'),item.get('operation'),item.get('offset')
        if type(event) is not str or type(operation) is not str or type(offset) is not str:return None
        fragment=self._mmio_fragments.get((event,operation,offset))
        if fragment is None:return None
        middle,tail,has_value=fragment
        # The three mandatory names above plus exact length/value presence prove exact keysets.
        if len(item)!=(4 if has_value else 3) or has_value and 'value' not in item:return None
        value_tail=b''
        if has_value:
            value=item['value']
            if type(value) is not int or not 0<=value<(1<<32):return None
            value_tail=b', "value": '+str(value).encode('ascii')
        return (b'{"agent_monotonic_ns": '+str(stamp).encode('ascii')+middle+str(index).encode('ascii')+
                tail+value_tail+b'}\n')
    def append(self,item):
        index=self.index;stamp=time.monotonic_ns()
        profile=self._arm_profile
        if profile is None:
            raw=self._mmio_bytes(item,index,stamp)
            if raw is None:
                raw=(json.dumps({'index':index,'agent_monotonic_ns':stamp,**item},sort_keys=True,allow_nan=False)+'\n').encode()
            require(self.count+len(raw)<=self.limit,'finite journal budget exhausted')
            require(self.stream.write(raw)==len(raw),'short original journal write');self.stream.flush()
            if item['event'].endswith('started_unknown') or item['event'] in ('session_finished','post_programming_verified'):os.fsync(self.stream.fileno())
            self.count+=len(raw);self.index+=1
            return
        stage=0
        try:
            _arm_metric_call(profile,'begin_record',index,stamp,item)
            raw=self._mmio_bytes(item,index,stamp)
            if raw is None:
                raw=(json.dumps({'index':index,'agent_monotonic_ns':stamp,**item},sort_keys=True,allow_nan=False)+'\n').encode()
            _arm_metric_call(profile,'returned',0,stamp)
            require(self.count+len(raw)<=self.limit,'finite journal budget exhausted')
            begin=_arm_metric_call(profile,'start',1);stage=1
            require(self.stream.write(raw)==len(raw),'short original journal write')
            _arm_metric_call(profile,'returned',1,begin)
            begin=_arm_metric_call(profile,'start',2);stage=2
            self.stream.flush()
            _arm_metric_call(profile,'returned',2,begin)
            if item['event'].endswith('started_unknown') or item['event'] in ('session_finished','post_programming_verified'):
                begin=_arm_metric_call(profile,'start',3);stage=3
                os.fsync(self.stream.fileno())
                _arm_metric_call(profile,'returned',3,begin)
            stage=4
            self.count+=len(raw);self.index+=1
            _arm_metric_call(profile,'returned',4,stamp)
        except BaseException:
            _arm_metric_call(profile,'failed',stage)
            raise
    def close(self):self.stream.close()


def _load(name,path,expected):
    require(hashlib.sha256(path.read_bytes()).hexdigest()==expected,'exact helper/source hash required')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def main(argv=None):
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--request',required=True,type=Path);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--execute-a',action='store_true')
    relay=parser.add_mutually_exclusive_group()
    relay.add_argument('--relay-original',action='store_true');relay.add_argument('--relay-qualification',action='store_true')
    parser.add_argument('--fifo-qualification',action='store_true');parser.add_argument('--input-fifo',type=Path)
    parser.add_argument('--fifo-device',type=int);parser.add_argument('--fifo-inode',type=int);parser.add_argument('--fifo-owner',type=int)
    args=parser.parse_args(argv)
    if args.relay_original or args.relay_qualification:
        require(not args.execute_a and not args.fifo_qualification and args.input_fifo is None,'fixed unprivileged relay entry only')
        return _relay(args,args.relay_qualification)
    require(args.execute_a or args.fifo_qualification,'explicit physical or fixed FIFO-only qualification required')
    require(os.name=='posix' and os.geteuid()==0 and os.environ.get('BOARD')=='Pynq-Z2' and os.environ.get('XILINX_XRT')=='/usr',
            'existing A privileged Linux runtime required')
    root=args.request.absolute().parent
    raw=args.request.read_bytes();require(len(raw)<=16384 and hashlib.sha256(raw).hexdigest()==args.request_sha256,'Root request file pin mismatch')
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate request key');result[key]=value
        return result
    request=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite request')))
    unsigned=dict(request);logical_hash=unsigned.pop('request_hash')
    require(hashlib.sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()==logical_hash,
            'canonical logical request hash mismatch')
    profile_enabled=_arm_profile_enabled(request)
    if args.fifo_qualification:
        require('functional_timing_profile' not in request,'functional profile only for private source4 live diagnostics')
        require(not args.execute_a and request['requirements_sha256']==CONTRACT and type(request['attempts']) is int and
                request['attempts']==1 and request['expected_boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and
                request['agent_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'fixed current-boot qualification request required')
        return _qualification(args,request)
    require(request['requirements_sha256']==CONTRACT and request['attempts']==1 and
                                   type(request['attempts']) is int and request['phase']=='private_live' and request['execute_a'] is True,
                                   'distinct reviewed private live request required')
    # Fixed relative paths cannot select alternate Python modules or runtime factories.
    codec=_load('_private_live_pinned_codec',root/'private_pl_stream.py',request['codec_sha256'])
    timing=_validated_session_timing(request,codec)
    helper=_load('_private_live_pinned_collector',root/'a_b56_memory_safe_collector.py',COLLECTOR_SHA)
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['agent_sha256'],'agent source pin mismatch')
    helper.no_links(root);identities=set();total=0
    require(type(request['inputs']) is dict and len(request['inputs'])==25 and
            sum(name.startswith('package/') for name in request['inputs'])==23,'exact25 inputs/23 package required')
    require(set(request['inputs'])-{name for name in request['inputs'] if name.startswith('package/')}==
            {'a_b56_memory_safe_collector.py','validation_fixture.json'},'only original source and validation fixture inputs')
    for name,wanted in request['inputs'].items():
        helper.relative_name(name);path=helper.no_links(root/name)
        with path.open('rb') as source:
            stat=os.fstat(source.fileno());identity=(stat.st_dev,stat.st_ino)
            require(stat_mode.S_ISREG(stat.st_mode) and stat.st_nlink==1 and identity not in identities and
                    0<stat.st_size<=256*1024*1024,'regular bounded input alias refused');identities.add(identity)
            digest=hashlib.sha256();count=0
            for block in iter(lambda:source.read(65536),b''):digest.update(block);count+=len(block)
            after=os.fstat(source.fileno())
        require((stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_nlink)==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_nlink) and count==stat.st_size,'input changed during hash')
        total+=count;require(total<=512*1024*1024,'selected input total limit')
        require({'bytes':count,'sha256':digest.hexdigest()}==wanted,'input bytes differ')
    require('request_hash' not in request['context'],'stored context excludes logical hash to prevent cycle')
    ctx=codec.context({**request['context'],'request_hash':logical_hash})
    require(ctx['tested_commit']==request['agent_source_commit'] and
            request['collector_source_commit']=='8b6e130c9d760ed9b4a935d8d5f6090203fa73b6' and
            ctx['build_manifest_sha256']==BUILD_SHA and request['inputs']['package/artifacts/private_diag.bit']['sha256']==BIT_SHA and
            request['inputs']['package/artifacts/private_diag.hwh']['sha256']==HWH_SHA,'source/build pins differ')
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==ctx['boot_id'],'current boot mismatch')
    profile=_ArmJournalProfile() if profile_enabled else None
    if profile is not None:_arm_profile_binding(profile,request,ctx,args.request_sha256)
    input_fd=_open_fifo(args,request)  # Separate data-only FIFO, before ANY runtime/image/MMIO/START.
    import pynq
    from pynq import Clocks
    prestate=_startup_preflight(request,ctx,pynq,Clocks)
    out=root/'live-evidence';require(not out.exists(),'new exclusive evidence required');out.mkdir()
    journal=_Journal(out/'operations.jsonl',profile=profile);session=None;bus=None;failure=None
    def interrupted(signum,frame):raise InterruptedError('signal '+str(signum))
    handlers={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        verified=helper.validate(root/'package',root/'package/ARTIFACT_MANIFEST.json',BUILD_SHA,
                                 root/'validation_fixture.json',out)
        bit=helper.snapshot(verified,out)
        require(len(verified.blobs)==24,'original24 checked snapshots required')
        require(verified.fixture.run_id==ctx['operation_id'] and verified.fixture.session_id==ctx['session_id'] and
                verified.fixture.tag==ctx['tag'] and verified.fixture.nonce==request['session_nonce'],
                'validation fixture must bind new session; its samples are never live inputs')
        journal.event('image_load_started_unknown',operation_id=ctx['operation_id'],request_sha256=args.request_sha256,context=ctx,prestate=prestate)
        runtime=helper.PynqRuntime();overlay=runtime.overlay(bit);helper.check_overlay(overlay,verified)
        overlay.download();journal.event('image_load_returned')
        poststate=_post_programming(ctx,Clocks);helper.check_overlay(overlay,verified)
        journal.event('post_programming_verified',observed=poststate,metadata_checked=True)
        bus=helper.Bus(runtime.mmio(verified.base,verified.span),journal)
        session=_LiveSession(bus,helper,ctx,time.monotonic,time.sleep,journal.append,
                             total_seconds=request['total_seconds'],poll_seconds=request['poll_seconds'],max_scans=request['max_scans'])
        reader=_InputLines(input_fd,session,timing['idle_timeout_ms']/1000,codec.MAX_LINE)
        writer=_OutputLines(1,session,codec,min(timing['idle_timeout_ms']/1000,0.1))
        code=_serve(session,reader,writer,codec,profile)
        return code
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error)[:512]}
        return 2
    finally:
        # A failure before session construction but after MMIO still needs one bounded STOP.
        if session is not None:cleanup=session.finish('agent finally')
        elif bus is not None:
            cleanup=_stop_without_session(bus,'failure before session construction')
        else:cleanup={'attempted':False,'confirmed':False,'outcome':'MMIO not established'}
        terminal_failed=False
        terminal={'context':ctx,'cleanup':cleanup,'primary_error':getattr(session,'primary_error',None) or failure,
                  'secondary_errors':getattr(session,'secondary_errors',[])+([failure] if failure and getattr(session,'primary_error',None) else []),
                  'movement_authorized':False,'formal_acceptance':'not_run','clock_conversion':'not_established'}
        try:helper.write_json(out/'TERMINAL.json',terminal)
        except BaseException as error:
            terminal_failed=True
            print(json.dumps({'terminal_write_failed':type(error).__name__,'original_terminal':terminal}),file=sys.stderr)
        try:journal.close()
        except BaseException as error:
            terminal_failed=True;print(json.dumps({'journal_close_failed':type(error).__name__,'original_terminal':terminal}),file=sys.stderr)
        finally:
            for sig,handler in handlers.items():signal.signal(sig,handler)
            os.close(input_fd)
        if terminal_failed:return 2
        _arm_profile_publish(profile,out,cleanup,True,True)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'private_diagnostic_error':type(error).__name__,'detail':str(error)[:512]}),file=sys.stderr)
        raise SystemExit(2)
