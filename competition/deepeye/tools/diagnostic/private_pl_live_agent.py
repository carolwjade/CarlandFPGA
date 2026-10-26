"""A-only bounded Linux private digital session. Explicit physical flag required.

One checked image load and START, then original per-scan TRIGGER/ACK FSM.
Private JSON never becomes negotiated wire, AI input, BOOT or motion authority.
"""
import argparse
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import stat as stat_mode
import sys
import subprocess
import time

COLLECTOR_SHA='723435f542b050405d8a6286a806a6561fbb613e6608ebf5f84407c7418407e6'
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
PYNQ_SHA='d2ea2a5b61df23214e3d7990e6c103e23d2bada59be0abbf2a7d36db8f4ab384'
BUILD_SHA='e906b1517d328e05b123346ea71c0c5c7c6552be7baa31dde2eb42833f0ef13a'
BIT_SHA='8455b5f8648ff913926c7f55495c5e2ed7328e92a312558eed131f3edb0d11db'
HWH_SHA='aa0ce7094eb0f1ed6a12684713cefe3a1635ef8c32af9fc32f8e1cc3cbef3ee1'
U32=(1<<32)-1
QUALIFICATION_SENTINEL=b'DEEPEYE_PRIVATE_RELAY_QUALIFICATION_V1\n'
PRIVATE_PRELUDE=b'DEEPEYE_PRIVATE_INPUT_V1\n'  # Transport startup only; never BOOT/auth/wire evidence.


def require(value,message):
    if not value:raise ValueError(message)


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


def _serve(session,read_next,write,codec):
    error=None
    try:
        ready=session.start();write(codec.record('diagnostic_ready',session.context,**ready))
        while session.sequence<=session.max_scans:
            raw=read_next()
            if raw is None:break
            request=codec.decode_request(raw,session.context,session.sequence)
            result=session.scan(request)
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


class _Journal:
    def __init__(self,path,max_bytes=8*1024*1024):
        self.stream=path.open('xb');self.count=0;self.limit=max_bytes;self.index=0
    def event(self,event,**fields):self.append({'event':event,**fields})
    def append(self,item):
        raw=(json.dumps({'index':self.index,'agent_monotonic_ns':time.monotonic_ns(),**item},sort_keys=True,allow_nan=False)+'\n').encode()
        require(self.count+len(raw)<=self.limit,'finite journal budget exhausted')
        require(self.stream.write(raw)==len(raw),'short original journal write');self.stream.flush()
        if item['event'].endswith('started_unknown') or item['event']=='session_finished':os.fsync(self.stream.fileno())
        self.count+=len(raw);self.index+=1
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
    if args.fifo_qualification:
        require(not args.execute_a and request['requirements_sha256']==CONTRACT and type(request['attempts']) is int and
                request['attempts']==1 and request['expected_boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and
                request['agent_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'fixed current-boot qualification request required')
        return _qualification(args,request)
    require(request['requirements_sha256']==CONTRACT and request['attempts']==1 and
                                   type(request['attempts']) is int and request['phase']=='private_live' and request['execute_a'] is True,
                                   'distinct reviewed private live request required')
    _session_limits(request['total_seconds'],request['poll_seconds'],request['max_scans'],request['idle_timeout_ms'])
    # Fixed relative paths cannot select alternate Python modules or runtime factories.
    helper=_load('_private_live_pinned_collector',root/'a_b56_memory_safe_collector.py',COLLECTOR_SHA)
    codec=_load('_private_live_pinned_codec',root/'private_pl_stream.py',request['codec_sha256'])
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
    require(type(request['idle_timeout_ms']) is int and 1<=request['idle_timeout_ms']<=100,'explicit bounded input idle budget required')
    input_fd=_open_fifo(args,request)  # Separate data-only FIFO, before ANY runtime/image/MMIO/START.
    import pynq
    from pynq import Clocks
    require(hashlib.sha256(Path(pynq.__file__).read_bytes()).hexdigest()==PYNQ_SHA and pynq.__version__=='3.0.1' and
            float(Clocks.fclk0_mhz)==100.0 and Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()=='operating',
            'current runtime/module/configuration mismatch')
    out=root/'live-evidence';require(not out.exists(),'new exclusive evidence required');out.mkdir()
    journal=_Journal(out/'operations.jsonl');session=None;bus=None;failure=None
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
        journal.event('image_load_started_unknown',operation_id=ctx['operation_id'],request_sha256=args.request_sha256,context=ctx)
        runtime=helper.PynqRuntime();overlay=runtime.overlay(bit);helper.check_overlay(overlay,verified)
        overlay.download();journal.event('image_load_returned');helper.check_overlay(overlay,verified)
        bus=helper.Bus(runtime.mmio(verified.base,verified.span),journal)
        session=_LiveSession(bus,helper,ctx,time.monotonic,time.sleep,journal.append,
                             total_seconds=request['total_seconds'],poll_seconds=request['poll_seconds'],max_scans=request['max_scans'])
        reader=_InputLines(input_fd,session,request['idle_timeout_ms']/1000,codec.MAX_LINE)
        writer=_OutputLines(1,session,codec,min(request['idle_timeout_ms']/1000,0.1))
        code=_serve(session,reader,writer,codec)
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


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'private_diagnostic_error':type(error).__name__,'detail':str(error)[:512]}),file=sys.stderr)
        raise SystemExit(2)
