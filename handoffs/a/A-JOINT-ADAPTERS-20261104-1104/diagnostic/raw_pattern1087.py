"""Root-only non-MTR4 UART wiring pattern actor; import is inert.

Startup reads/locks/maps only. Root dispatches each phase only after reviewing
authentic B capture readiness. Receipt hashes below are audit references, never
automatic peer/human authority. This code cannot control the MCU or actuators.
"""
import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

SCOPE='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
BOOTSTRAP_SHA='f459d18bda342267dd9d239067af52bf2665c16e6df9a11f8ac31681c66ee676'
READER_SHA='d3be22472808418cc9fef164fe8ca3021987b84ecde1cef9261568155e6da57b'
BUILD_REVIEW_SHA='beb8c519ec26998d03a6393a358e9dbe253d86d640de1cc2babf1ff3ee7fedf9'
PATTERN=bytes.fromhex('55a533cc0ff06996')
STATE=Path('/home/xilinx/deepeye-uart-state')
RX,TX,STATUS=0,4,8
ERRORS,RX_PENDING,TX_FULL,TX_EMPTY=0xe0,3,8,4

def need(ok,message):
    if not ok:raise ValueError(message)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def strict_json(blob):
    def unique(pairs):
        value={}
        for key,item in pairs:
            need(key not in value,'duplicate JSON key');value[key]=item
        return value
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def text(value):
    need(type(value) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',value) is not None,'bounded ASCII identifier required')
    return value

def request_shape(value):
    need(type(value) is dict and value.get('op') in ('tx8','rx8','close'),'raw phase required')
    keys={'op','request_id'} if value['op']=='close' else {'op','request_id','capture_id','b_receipt_sha256','timeout_ms'}
    need(set(value)==keys,'exact raw request fields required');text(value['request_id'])
    if value['op']!='close':
        text(value['capture_id'])
        need(type(value['b_receipt_sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['b_receipt_sha256']) is not None,'receipt SHA256 audit reference required')
        need(type(value['timeout_ms']) is int and 1<=value['timeout_ms']<=5000,'capture timeout1..5000ms required')
    return value

def safe(path):
    path=Path(path);need(path.is_absolute() and '..' not in path.parts,'absolute path required')
    for part in (path,*path.parents):need(not part.is_symlink(),'symlink refused')
    return path

class Journal:
    def __init__(self,path,context):
        self.context=context
        fd=os.open(str(safe(path)),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        self.file=os.fdopen(fd,'wb',buffering=0)
    def record(self,event,durable=False):
        line=canonical(dict(event,physical_parent=self.context,monotonic_ns=time.monotonic_ns()))+b'\n'
        need(len(line)<=65536 and self.file.write(line)==len(line),'bounded journal write failed')
        if durable:os.fsync(self.file.fileno())
    def close(self):self.file.close()

class RawActor:
    def __init__(self,mmio,read_current,binding,journal,*,clock=time.monotonic,sleep=time.sleep):
        self.mmio,self.read_current,self.binding,self.journal=mmio,read_current,binding,journal
        self.clock,self.sleep=clock,sleep;self.used=set();self.tx_used=False;self.rx_used=False
        self.tx_done=False;self.poisoned=False;self.tx_bytes=[];self.rx_bytes=[];self.effect_attempted=False
        self.status_count=0;self.started=False
    def physical(self):need(self.read_current()==self.binding,'actual physical parent changed')
    def status(self,phase):
        value=int(self.mmio.read(STATUS));need(0<=value<=0xffffffff,'raw status uint32 required')
        self.status_count+=1;self.journal.record(dict(event='status',phase=phase,value=value))
        need(value&ERRORS==0,'UART overrun/frame/parity error; no flush')
        return value
    def startup(self):
        need(not self.started,'startup status check is one-shot')
        self.physical();value=self.status('startup')
        need(value==TX_EMPTY,'startup UART must be idle/empty/error-free; leave unknown bytes unread')
        self.physical();self.started=True;return value
    def deadline(self,end):need(self.clock()<end,'raw phase deadline expired; no replay')
    def phase(self,request):
        request_shape(request);need(request['op']!='close','close releases in the outer owner only')
        need(self.started,'startup idle/empty status must be verified first')
        need(not self.poisoned and request['request_id'] not in self.used,'raw actor poisoned or request reused')
        op=request['op'];need(not (self.tx_used if op=='tx8' else self.rx_used),'one attempt per direction; no replay')
        self.used.add(request['request_id'])
        if op=='tx8':self.tx_used=True
        else:self.rx_used=True
        self.effect_attempted=False;start=self.clock();end=start+request['timeout_ms']/1000
        self.journal.record(dict(event='phase-intent',request=request),True)
        try:
            self.physical()
            if op=='tx8':
                for octet in PATTERN:
                    while True:
                        self.deadline(end);status=self.status(op)
                        need(not status&RX_PENDING,'unexpected RX during TX; leave FIFO untouched')
                        if not status&TX_FULL:break
                        self.sleep(.0002)
                    self.journal.record(dict(event='tx-write-intent',offset=TX,octet=octet,index=len(self.tx_bytes)),True)
                    self.deadline(end);self.effect_attempted=True
                    self.mmio.write(TX,octet);self.tx_bytes.append(octet)
                    self.journal.record(dict(event='tx-write-returned',octet=octet,index=len(self.tx_bytes)-1))
                while True:
                    self.deadline(end);status=self.status(op)
                    need(not status&RX_PENDING,'unexpected RX during TX; leave FIFO untouched')
                    if status&TX_EMPTY:break
                    self.sleep(.0002)
                self.tx_done=True
                result=dict(bytes_written=list(self.tx_bytes),tx_empty_observed=True,B_receive_proven=False)
            else:
                reads=[]
                while len(self.rx_bytes)<8:
                    self.deadline(end);status=self.status(op)
                    if not status&1:self.sleep(.0002);continue
                    self.journal.record(dict(event='rx-read-intent',offset=RX,index=len(self.rx_bytes),status=status),True)
                    self.deadline(end);self.effect_attempted=True
                    raw=int(self.mmio.read(RX));need(0<=raw<=0xffffffff,'raw RX uint32 required')
                    octet=raw&255;self.rx_bytes.append(octet)
                    row=dict(index=len(self.rx_bytes)-1,status=status,raw=raw,octet=octet);reads.append(row)
                    self.journal.record(dict(event='rx-read-returned',**row))
                status=self.status(op)
                need(not status&RX_PENDING,'unread extra RX bytes remain; never flush or ignore prefix')
                result=dict(bytes_read=list(self.rx_bytes),raw_reads=reads,
                            matches_expected_pattern=bytes(self.rx_bytes)==PATTERN,extra_rx_pending=False)
            self.physical()
            result.update(status_last=status,status_reads_total=self.status_count,elapsed_ms=(self.clock()-start)*1000)
            self.journal.record(dict(event='phase-returned',request=request,result=result),True)
            return dict(event='raw_phase_returned',status='COMPLETE',request=request,result=result,
                        evidence='non_MTR4_digital_pattern_only',MCU_READY_proven=False)
        except BaseException as error:
            self.poisoned=True
            after=None
            try:self.physical();after='same_actual_parent'
            except BaseException as parent_error:after=type(parent_error).__name__+': '+str(parent_error)[:256]
            outcome=dict(event='phase-failed',request=request,error_type=type(error).__name__,message=str(error)[:512],
                         effect_attempted=self.effect_attempted,tx_bytes_returned=list(self.tx_bytes),
                         rx_bytes_read=list(self.rx_bytes),physical_after=after,automatic_retry=False)
            self.journal.record(outcome,True);return dict(outcome,status='FAILED_OR_UNKNOWN')

def bootstrap(stage):
    for name,expected in (('diagnostic_stdio1041.py',BOOTSTRAP_SHA),('root_loaded_product1031.py',READER_SHA)):
        path=safe(stage/name)
        with path.open('rb') as stream:
            a=os.fstat(stream.fileno());blob=stream.read(2*1024*1024+1);b=os.fstat(stream.fileno())
        key=lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
        need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and 0<a.st_size<=2*1024*1024 and len(blob)==a.st_size and
             key(a)==key(b)==key(path.lstat()) and hashlib.sha256(blob).hexdigest()==expected,'pinned read-only source required')
    spec=importlib.util.spec_from_file_location('raw1087_bootstrap1041',stage/'diagnostic_stdio1041.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def run(args,inp,out):
    need(args.allow_non_mtr4_pattern is True,'explicit non-MTR4 flag required before runtime imports')
    import fcntl
    stage=safe(Path(__file__).parent);entry=bootstrap(stage)
    need(args.build_review_sha256==BUILD_REVIEW_SHA,'actual adopted build-review hash required')
    entry._read_pinned(args.build_review,args.build_review_sha256,131072)
    service,unused_facade,reader=entry._load_apis(stage)
    root=reader.build_actual_reader(service,approved_plan_path=safe(args.approved_plan),
        approved_plan_sha256=args.approved_plan_sha256,actual_operation_directory=safe(args.operation_directory),
        transfer_review_path=safe(args.build_review),transfer_review_sha256=args.build_review_sha256)
    binding=root.read_current();need(root.simulation is False and root._authorized is None and root._uart_mmio is None,'actual read-only parent only')
    context=dict(binding=asdict(binding),approved_plan_sha256=args.approved_plan_sha256,
                 requirements_sha256=SCOPE,raw_operation_id=text(args.raw_operation_id),pid=os.getpid())
    lock_path=safe(STATE/'mcu_uart.owner.lock')
    fd=os.open(str(lock_path),os.O_RDWR|os.O_NOFOLLOW)
    locked=False;journal=None
    try:
        info=os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and
             (info.st_dev,info.st_ino)==(lock_path.lstat().st_dev,lock_path.lstat().st_ino),'existing stable lock inode required')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);locked=True
        parent=safe(STATE/'raw-operations');parent.mkdir(mode=0o700,exist_ok=True)
        directory=parent/text(args.raw_operation_id);directory.mkdir(mode=0o700)
        context.update(lock_device=info.st_dev,lock_inode=info.st_ino,lock_path=str(lock_path))
        journal=Journal(directory/'journal.jsonl',context)
        mmio=root._MMIO(binding.uart.phys_addr,binding.uart.addr_range,device=root._device)
        need(mmio.device is root._device and root._clocks._instance._slcr_mmio.device is root._device,'same actual Device required')
        def current():
            current_lock=safe(lock_path).lstat();held=os.fstat(fd)
            need(held.st_nlink==1 and (held.st_dev,held.st_ino)==(current_lock.st_dev,current_lock.st_ino)==
                 (info.st_dev,info.st_ino),'original hardware lock inode changed')
            return root.read_current()
        actor=RawActor(mmio,current,binding,journal);status=actor.startup()
        ready=dict(event='raw_pattern_ready',physical_parent=context,pid=os.getpid(),status=status,
                   actual_ps_clock=root._ps(root._clocks),default_transmission=False,
                   pattern_hex=PATTERN.hex(),MCU_READY_proven=False,UART_scope='NON_MTR4_DIAGNOSTIC_ONLY')
        journal.record(ready,True);out.write(canonical(ready)+b'\n');out.flush()
        while True:
            line=inp.readline(8193)
            if not line:break
            need(len(line)<=8192 and line.endswith(b'\n'),'bounded raw request line required')
            request=request_shape(strict_json(line))
            if request['op']=='close':break
            response=actor.phase(request);out.write(canonical(response)+b'\n');out.flush()
            if actor.poisoned:break
        journal.record(dict(event='raw-owner-release-intent',UART_cleanup=False,FIFO_flush=False,automatic_STOP=False),True)
        return 2 if actor.poisoned else 0
    finally:
        try:
            if locked:fcntl.flock(fd,fcntl.LOCK_UN)
            if journal is not None:journal.record(dict(event='raw-owner-lock-released',UART_cleanup=False,FIFO_flush=False),True)
        finally:
            try:
                if journal is not None:journal.close()
            finally:os.close(fd)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-non-mtr4-pattern',action='store_true')
    for name in ('approved-plan','approved-plan-sha256','operation-directory','build-review','build-review-sha256','raw-operation-id'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv)
    if not args.allow_non_mtr4_pattern:parser.error('--allow-non-mtr4-pattern is required; no UART access')
    need(os.name=='posix' and os.geteuid()==0 and os.uname().machine=='armv7l','actual root armv7l PS required')
    sys.stdout.flush();sys.stderr.flush();fd=os.dup(sys.stdout.fileno());out=os.fdopen(fd,'wb',buffering=0)
    try:
        os.dup2(sys.stderr.fileno(),sys.stdout.fileno())
        with redirect_stdout(sys.stderr):return run(args,sys.stdin.buffer,out)
    except Exception as error:
        print(json.dumps(dict(event='raw_pattern_failed',error_type=type(error).__name__,message=str(error)[:512],retry=False),sort_keys=True),file=sys.stderr,flush=True)
        return 2
    finally:out.close()

if __name__=='__main__':raise SystemExit(main())
