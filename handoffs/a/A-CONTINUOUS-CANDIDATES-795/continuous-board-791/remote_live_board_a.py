"""791 reviewed-candidate live ABI. Import is inert; Root alone runs hardware.

Independent streaming owner, not an extension/reset of a finite legacy owner.
Per-request limits and natural uint counter exhaustion remain. No mission cap.
Only a Root-pinned load plan and explicit --serve entry can load the board.
"""
import binascii
import hashlib
import json
import os
from pathlib import Path
import select
import struct
import sys
import threading
import time
import stat

ABI = 'DEEPEYE-LIVE-BOARD-791-v1'
SCOPE = '2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
MAX_LINE = 16384
U32 = 0xffffffff

def need(ok, code):
    if not ok: raise ValueError(code)

def integer(v, low, high):
    need(type(v) is int and low <= v <= high, 'EXACT_INTEGER_BOUND')
    return v

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(v): return hashlib.sha256(v).hexdigest()

def strict_json(raw):
    def pairs(xs):
        out = {}
        for k,v in xs:
            need(k not in out, 'DUPLICATE_KEY'); out[k] = v
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE')))

class BoundedLines:
    """No buffered readline: partial stdin cannot bypass the live TTL guard."""
    def __init__(self, stream):self.fd=stream.fileno();self.buffer=bytearray()
    def read(self, deadline_ns):
        while b'\n' not in self.buffer:
            timeout=None if deadline_ns is None else (deadline_ns-time.monotonic_ns())/1e9
            if timeout is not None and timeout<=0:raise TimeoutError('STDIN_DEADLINE')
            ready,_,_=select.select([self.fd],[],[],timeout)
            if not ready:raise TimeoutError('STDIN_DEADLINE')
            chunk=os.read(self.fd,min(4096,MAX_LINE+1-len(self.buffer)))
            if not chunk:
                need(not self.buffer,'TRUNCATED_STDIN');return None
            self.buffer.extend(chunk);need(len(self.buffer)<=MAX_LINE,'STDIN_BOUND')
        end=self.buffer.index(10)+1
        line=bytes(self.buffer[:end]);del self.buffer[:end]
        return line

def write_response(stream, response):
    raw=canonical(response)+b'\n';need(len(raw)<=32768,'RESPONSE_BOUND')
    fd=stream.fileno();end=time.monotonic_ns()+1_000_000_000
    while raw:
        remaining=(end-time.monotonic_ns())/1e9
        if remaining<=0:raise TimeoutError('STDOUT_DEADLINE')
        _,ready,_=select.select([],[fd],[],remaining)
        if not ready:raise TimeoutError('STDOUT_DEADLINE')
        # PIPE_BUF-sized writes after writable poll avoid a large blocking write.
        n=os.write(fd,raw[:4096]);need(n>0,'STDOUT_SHORT_WRITE');raw=raw[n:]

class SDJournal:
    """Exclusive append-only SD log; no retained history or RAM spool.

    Request intent/terminal records fsync. MMIO logs flush before the effect;
    they are process-level evidence, not a power-loss durability guarantee.
    """
    def __init__(self, path):
        path=Path(path)
        need(path.is_absolute() and path.parent.is_dir(),'EXISTING_ABSOLUTE_SD_PARENT')
        for parent in (path.parent,*path.parent.parents):
            need(not parent.is_symlink(),'JOURNAL_NO_SYMLINK')
        # Only the real SD root filesystem; reject RAM spool and device paths.
        need(str(path).startswith(('/home/','/mnt/','/media/')),'SD_JOURNAL_LOCATION')
        fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        need(stat.S_ISREG(os.fstat(fd).st_mode),'REGULAR_SD_JOURNAL')
        self.file = os.fdopen(fd,'wb',buffering=0)
    def record(self, event, durable=False):
        line = canonical(event) + b'\n'
        need(len(line) <= 65536, 'JOURNAL_RECORD_BOUND')
        need(self.file.write(line) == len(line), 'JOURNAL_SHORT_WRITE')
        if durable: os.fsync(self.file.fileno())
    def close(self): self.file.close()

class LiveBoard:
    def __init__(self, trace, g05, *, boot_id, build_id, request_hash,
                 identity, codec, command_check, output_decode, journal,
                 clock=time.monotonic_ns):
        self.trace,self.g05 = trace,g05
        self.boot_id,self.build_id,self.request_hash = boot_id,build_id,request_hash
        self.identity=tuple(identity); need(len(identity)==13, 'IDENTITY13')
        self.codec,self.command_check,self.output_decode=codec,command_check,output_decode
        self.journal,self.clock=journal,clock
        self.owner=(os.getpid(),threading.get_ident())
        self.last_seq=self.last_source=self.last_command=self.last_tag=0
        self.last_em=-1; self.poisoned=False; self.closed=False
        self.deadline=None; self.io=0; self.bound=None; self.effect=False;self.arm_owned=False

    def rw(self, window, offset, value=None):
        need((os.getpid(),threading.get_ident())==self.owner, 'OWNER_CHANGED')
        need(self.clock()<self.bound and self.io<4096, 'PER_REQUEST_IO_OR_TIME')
        self.io+=1
        if value is None:
            result=int(window.read(offset)); integer(result,0,U32)
            self.journal.record(dict(event='mmio-read-returned',seq=self.last_seq,io=self.io,
                                     window='trace' if window is self.trace else 'g05',offset=offset,value=result))
            return result
        self.journal.record(dict(event='mmio-write-intent',seq=self.last_seq,
                                 io=self.io,window='trace' if window is self.trace else 'g05',
                                 offset=offset,value=value))
        self.effect=True
        window.write(offset,value)
        return None

    def tr(self,o):return self.rw(self.trace,o)
    def tw(self,o,v):return self.rw(self.trace,o,v)
    def gr(self,o):return self.rw(self.g05,o)
    def gw(self,o,v):return self.rw(self.g05,o,v)

    def live(self):
        need(not self.closed and not self.poisoned, 'WORKER_CLOSED_OR_UNKNOWN')
        need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==self.boot_id,
             'BOOT_CHANGED')

    def gstatus(self, latched=False):
        s,f=self.gr(8),self.gr(0x10)
        need(f==0 and 0<=s<=0x7f and s&1 and not s&2, 'G05_FAULT_OR_HALTED')
        if latched:need(s&0x20, 'LATCH_REQUIRED')
        return s

    def initialize(self):
        self.bound=self.clock()+4_000_000_000;self.io=0
        for o,v in ((0,0x54353046),(4,1),(8,4),(12,50000000),(16,1000000),(20,4096)):
            need(self.tr(o)==v,'TRACE_IDENTITY')
        b=int(self.build_id,16)
        for i in range(4):need(self.tr(0x60+4*i)==(b>>(32*i))&U32,'TRACE_BUILD')
        need(self.gr(0)==0x47303550 and self.gr(4)==2 and self.gr(8)==0 and self.gr(0x10)==0,'NEW_G05')
        for i,v in enumerate(self.identity):self.gw(0x100+4*i,v)
        self.gw(0x0c,1);self.gstatus()
        self.last_tag=self.tr(0x2c)

    def wait_trace(self, wanted):
        while True:
            need(self.tr(0x1c)==0,'TRACE_FAULT')
            state=self.tr(0x18)
            if state==wanted:return
            need(1<=state<=9,'TRACE_STATE')

    def sense(self, r):
        # E4's uint16 frame sequence is a genuine format boundary. A future
        # explicit new session is required before exhaustion, never reset here.
        integer(r['source_seq'],self.last_source+1,65535//4)
        adc=integer(r['adc_tick_ms'],0,U32//1000)
        em=integer(r['em_tick_ms'],self.last_em+1,adc)
        counts=r['counts'];need(type(counts) is list and len(counts)==4,'COUNTS4')
        for v in counts:need(v is None or type(v) is int and 0<=v<=4095,'COUNT12_OR_NULL')
        q=integer(r['quality'],0,65535)
        need(type(r['source_digest']) is str and len(r['source_digest'])==64 and
             all(c in '0123456789abcdef' for c in r['source_digest']),'SOURCE_DIGEST')
        # New ABI declares bit0..3 valid, bits4..7 saturation, bit12 source fault.
        need(all(bool(q&(1<<i))==(v is not None) for i,v in enumerate(counts)), 'QUALITY_VALID_MASK')
        need(not q&0x1000 or all(v is None for v in counts),'FAULT_NULL_REQUIRED')
        need(q & ~0x10ff == 0,'LIVE_QUALITY_BITS')
        need(all(v is not None or not q&(1<<(4+i)) for i,v in enumerate(counts)), 'NULL_SATURATION')
        self.last_source=r['source_seq'];self.last_em=em
        need(self.tr(0x18)==0 and self.tr(0x20)&2 and self.tr(0x30)==0 and self.tr(0x1c)==0,'TRACE_NOT_QUIET')
        prior=self.tr(0x2c);tag=max(prior,self.last_tag)+1;integer(tag,1,U32)
        result,pop,rx=self.tr(0x40),self.tr(0x38),self.tr(0x34)
        need(result<=U32-4 and pop<=U32-252 and rx<=U32-252,'NATURAL_COUNTER_EXHAUSTION')
        self.last_tag=tag
        for o,v in ((0x100,tag),(0x104,0),(0x108,0)):self.tw(o,v)
        self.arm_owned=True
        self.tw(0x80,1);self.wait_trace(3);need(self.tr(0x2c)==tag,'ARM_TAG')
        lanes=[]
        for i,v in enumerate(counts):
            flags=(1 if v is not None else 0)|(2 if q&(1<<(4+i)) else 0)|(4 if v is not None and em<adc else 0)|(8 if q&0x1000 else 0)
            need(v is not None or not flags&6,'NULL_QUALITY')
            lanes.append(flags)
            for o,x in ((0x110,i),(0x114,v or 0),(0x118,adc*1_000_000),(0x11c,0),(0x120,flags)):self.tw(o,x&U32)
            # Full acquisition ns may exceed uint32.
            self.tw(0x11c,(adc*1_000_000)>>32)
            self.tw(0x80,2);need(self.tr(0x24)==i+1,'PUSH_READBACK')
        self.wait_trace(4);rows=[]
        for i,v in enumerate(counts):
            source=em*1_000_000 if v is not None else 0
            vals=(self.identity[12],r['source_seq'],adc*1000,0,source&U32,source>>32,
                  em*1000 if v is not None else 0,0,1,4*(r['source_seq']-1)+i+1)
            integer(vals[-1],1,65535)
            for j,x in enumerate(vals):self.tw(0x130+4*j,x)
            self.tw(0x80,3);self.wait_trace(7)
            row={k:self.tr(o) for k,o in (('id',0x40),('error',0x44),('bytes',0x48),('refusal',0x4c),('rx_before',0x50),('rx_end',0x7c))}
            need(row['id']==result+1 and row['error']==row['refusal']==0 and 0<row['bytes']<=63 and
                 row['rx_before']==rx and row['rx_end']==rx+row['bytes'],'RESULT_CORRELATION')
            result,rx=row['id'],row['rx_end'];rows.append(row)
            self.tw(0x160,result);self.tw(0x80,4);self.wait_trace(9 if i==3 else 4)
            need(self.tr(0x28)==i+1,'ACK_READBACK')
        count=self.tr(0x30);need(count==sum(x['bytes'] for x in rows) and count<=252,'WIRE_LENGTH')
        wire=bytearray()
        for remaining in range(count-1,-1,-1):
            peek=self.tr(0x70);need(0x100<=peek<=0x1ff,'PEEK')
            self.tw(0x164,pop+1);self.tw(0x80,8)
            need(self.tr(0x38)==pop+1 and self.tr(0x30)==remaining,'POP_READBACK')
            wire.append(peek&255);pop+=1
        decoded=[];offset=0
        for i,row in enumerate(rows):
            frame=bytes(wire[offset:offset+row['bytes']]);offset+=row['bytes']
            magic,version,kind,length,view,seq,tick=struct.unpack_from('<2sBBBBHI',frame)
            need(magic==b'\xa5\x5a' and version==3 and kind==0xe4 and len(frame)==length+14 and view==1 and
                 seq==4*(r['source_seq']-1)+i+1 and tick==adc*1000,'E4_HEADER')
            need(struct.unpack_from('<H',frame,len(frame)-2)[0]==binascii.crc_hqx(frame[2:-2],0xffff),'CRC')
            payload=frame[12:-2];need(payload[0]==2,'E4_REVISION')
            d=self.codec.decode_payload(bytes([1])+payload[1:],{'session':self.identity[12],'config_epoch':1,'e':0})
            p=d['points'][0]
            need(d['channel']==i and d['count']==1 and p['index']==r['source_seq'] and
                 p['value']==counts[i] and p['tick_ms']==adc*1000 and
                 p['source_tick_ms']==(em*1000 if counts[i] is not None else None),'E4_SOURCE_CORRELATION')
            need(all(bool(p[k])==bool(lanes[i]&(1<<j)) for j,k in enumerate(('valid','saturated','held','source_fault'))),'E4_QUALITY')
            decoded.append(d)
        self.tw(0x80,5)
        while True:
            state,status=self.tr(0x18),self.tr(0x20)
            if state==0 and status&2 and not status&0x14:break
            need(state in (0,9),'CANCEL_STATE')
        self.arm_owned=False
        return dict(wire_hex=wire.hex(),decoded=decoded,result_rows=rows,tag=tag,
                    source_digest=r['source_digest'],source_seq=r['source_seq'],
                    correlation='FOUR_FRAME_CRC_SOURCE_CONSISTENT',quality=q,
                    adc_tick_ms=adc,em_tick_ms=em)

    def apply(self,r):
        y=integer(r['yaw_q'],-15000,15000);p=integer(r['pitch_q'],-15000,15000)
        speed=integer(r['speed_code'],0,20);ttl=integer(r['duration_ms'],1,12000)
        command=(y&65535,p&65535,1,speed,ttl,r['request_seq'],r['request_seq'])
        self.command_check(command,self.last_command,1,build_id=self.build_id)
        self.gstatus()
        need(not self.gr(8)&0x68,'G05_PENDING')
        need(tuple(self.gr(0x100+4*i) for i in range(13))==self.identity,'G05_IDENTITY')
        for i,v in enumerate(command):self.gw(0x200+4*i,v)
        before=self.clock();self.gw(0x0c,2)
        need(self.gr(0x14)==command[5],'COMMIT_READBACK')
        self.last_command=command[5]
        # Conservative grant starts before COMMIT; never fabricate a later TTL.
        self.deadline=before+ttl*1_000_000
        self.bound=min(before+4_000_000_000,self.deadline-50_000_000)
        while not self.gstatus()&0x10:pass
        self.gw(0x0c,4);self.gstatus(True)
        latest=self.gr(0x1c);held=self.gr(0x300)
        words=[self.gr(0x300+4*i) for i in range(32)]
        need(0<held==words[0]==self.gr(0x300)<=latest<=self.gr(0x1c),'TORN_CAPTURE')
        self.gstatus(True)
        if speed:
            measured=self.output_decode(words,command,session=self.identity[12],build_id=self.build_id)
        else:
            measured=decode_zero_capture(words,command,self.identity[12])
        self.gw(0x0c,5);need(not self.gstatus()&0x20,'RELEASE')
        returned=self.clock();need(returned<self.deadline,'APPLY_RETURNED_EXPIRED')
        return dict(command_words=list(command),capture_words=words,measured=measured,
                    pwm_period=words[12:15],pwm_high=words[15:18],
                    commit_before_monotonic_ns=before,returned_monotonic_ns=returned,
                    conservative_deadline_monotonic_ns=self.deadline,
                    remaining_ns=self.deadline-returned)

    def request(self,r):
        need(type(r) is dict and r.get('abi')==ABI,'ABI')
        need(not self.closed and not self.poisoned,'NO_REPLAY_CLOSED_UNKNOWN')
        integer(r.get('request_seq'),self.last_seq+1,U32)
        op=r.get('op');need(op in ('sense','apply','stop','shutdown'),'OP')
        keys={'abi','op','request_seq'}
        if op=='sense':keys|={'source_seq','adc_tick_ms','em_tick_ms','counts','quality','source_digest'}
        if op=='apply':keys|={'yaw_q','pitch_q','speed_code','duration_ms'}
        need(set(r)==keys,'EXACT_FIELDS')
        self.live();self.last_seq=r['request_seq'];self.io=0;self.effect=False
        start=self.clock();self.bound=start+4_000_000_000
        if self.deadline is not None and op not in ('stop','shutdown'):
            need(start<self.deadline-100_000_000,'LIVE_TTL_HEADROOM')
            self.bound=min(self.bound,self.deadline-50_000_000)
        self.journal.record(dict(event='request-intent',request=r,monotonic_ns=start),True)
        try:
            if op=='sense':out=self.sense(r)
            elif op=='apply':out=self.apply(r)
            else:
                self.gw(0x0c,3);out=dict(stop_write_returned=True,status=self.gr(8),fault=self.gr(0x10),
                                       physical_zero_capture_proven=False)
                self.closed=True;self.deadline=None
            response=dict(abi=ABI,request_seq=self.last_seq,op=op,status='COMPLETE',unknown=False,
                          boot_id=self.boot_id,build_id=self.build_id,request_hash=self.request_hash,
                          io_count=self.io,result=out)
            self.journal.record(dict(event='request-returned',response=response),True)
            return response
        except BaseException as e:
            self.poisoned=True
            self.journal.record(dict(event='request-failed',seq=self.last_seq,type=type(e).__name__,
                                     message=str(e)[:512],unknown=self.effect,io_count=self.io),True)
            raise

    def safety_tail(self):
        """Distinct one-shot CANCEL/STOP; never repeat the uncertain request."""
        if self.arm_owned:
            try:
                self.bound=self.clock()+500_000_000;self.io=0
                self.tw(0x80,5)
                while True:
                    state,status=self.tr(0x18),self.tr(0x20)
                    if state==0 and status&2 and not status&0x14:break
                self.arm_owned=False
                self.journal.record(dict(event='terminal-trace-quiescent'),True)
            except BaseException as e:
                self.journal.record(dict(event='terminal-trace-quiescence-unknown',type=type(e).__name__),True)
        try:
            self.bound=self.clock()+500_000_000;self.io=0
            self.gw(0x0c,3)
            self.journal.record(dict(event='terminal-safety-stop-returned',physical_zero_capture_proven=False),True)
        except BaseException as e:
            self.journal.record(dict(event='terminal-stop-unknown',type=type(e).__name__),True)
        self.closed=True

def decode_zero_capture(words,command,session):
    """Pause uses measured zero-speed PWM, not terminal eng_halted STOP.
    Same snapshot/clock/period/local-witness checks as the original positive
    output parser. A zero target still has a real finite command TTL.
    """
    need(type(words) is list and len(words)==32 and all(type(v) is int and 0<=v<=U32 for v in words),'ZERO_CAPTURE_WORDS')
    yaw,pitch,profile,speed,ttl,seq,tag=command
    need((yaw,pitch,profile,speed)==(0,0,1,0),'ZERO_TARGET')
    need(words[0]>0 and words[1:6]==[seq,tag,profile,0,ttl] and words[30:]==[session,0x47303550],'ZERO_CAPTURE_BINDING')
    u64=lambda i:words[i]|words[i+1]<<32
    need(u64(6)<u64(10)<u64(8) and u64(8)-u64(6)==ttl*50000,'ZERO_CAPTURE_TTL')
    starts=[u64(18+2*i) for i in range(3)];ends=[u64(24+2*i) for i in range(3)]
    for period,high,start,end,expected in zip(words[12:15],words[15:18],starts,ends,(125000,125000,25000)):
        need(abs(period-1000000)<=1 and 0<high<period and abs(high-expected)<=1 and
             0<start<end<=U32 and end-start==period,'ZERO_CAPTURE_PWM')
    need(max(starts)-min(starts)<=1 and max(ends)-min(ends)<=1,'ZERO_CAPTURE_COHERENCE')
    return dict(action=0,yaw_q=0,pitch_q=0,speed_code=0,duration_ms=ttl)

def serve(worker, inp, out, lines=None):
    """One serial stdin consumer; parent may run native/model asynchronously.
    No automatic resend. EOF/malformed/unknown errors terminate after best-effort
    STOP exactly once; hardware TTL remains the independent safety backstop.
    """
    lines=BoundedLines(inp) if lines is None else lines
    try:
        while not worker.closed:
            deadline=None if worker.deadline is None else worker.deadline-100_000_000
            raw=lines.read(deadline)
            if not raw:return
            need(len(raw)<=MAX_LINE and raw.endswith(b'\n'),'BOUNDED_JSON_LINE')
            r=strict_json(raw)
            response=worker.request(r)
            write_response(out,response)
    finally:
        if not worker.closed:
            # Safety STOP is a distinct operation, never a retry of an APPLY.
            worker.safety_tail()
        worker.closed=True

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--serve',action='store_true',required=True)
    p.add_argument('--plan',required=True);p.add_argument('--source-root',required=True)
    p.add_argument('--identity-json',required=True);p.add_argument('--journal',required=True)
    a=p.parse_args()
    # Root must stage and pin this source closure; no provider/network discovery.
    sys.path.insert(0,a.source_root)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from load_once_791 import open_stream_from_plan
    from competition.deepeye.tools.diagnostic.functional50_g05_a import _command,_identity
    from competition.deepeye.simulation.authority.g05_board_output_v1 import decode_board_output
    from competition.deepeye.golden.codec import trace_candidate
    identity=_identity(tuple(strict_json(Path(a.identity_json).read_bytes())))
    # Init consumes the one immutable reviewed plan; no subsequent load RPC.
    from competition.deepeye.tools.diagnostic.functional50_board_a import _json,_bytes
    plan=_json(_bytes(a.plan,131072)[0])
    lines=BoundedLines(sys.stdin.buffer)
    raw=lines.read(time.monotonic_ns()+30_000_000_000)
    need(raw is not None,'INIT_EOF')
    need(len(raw)<=MAX_LINE and raw.endswith(b'\n'),'INIT_LINE_BOUND')
    init=strict_json(raw)
    need(init==dict(abi=ABI,op='init',request_seq=0,boot_id=plan['boot_id'],
                    build_id=plan['build_id'],request_hash=plan['request_sha256']),'INIT_PLAN_BINDING')
    journal=SDJournal(a.journal);worker=None
    try:
        import contextlib
        with contextlib.redirect_stdout(sys.stderr):
            trace,g05,plan=open_stream_from_plan(a.plan)
        worker=LiveBoard(trace,g05,boot_id=plan['boot_id'],build_id=plan['build_id'],
                         request_hash=plan['request_sha256'],identity=identity,codec=trace_candidate,
                         command_check=_command,output_decode=decode_board_output,journal=journal)
        worker.initialize()
        ready=dict(abi=ABI,op='init',status='COMPLETE',scope_sha256=SCOPE,
                   boot_id=plan['boot_id'],build_id=plan['build_id'],request_hash=plan['request_sha256'],
                   initial_speed_code=2,speed_applied=False,formal_acceptance='not_run')
        write_response(sys.stdout.buffer,ready)
        serve(worker,sys.stdin.buffer,sys.stdout.buffer,lines)
    finally:
        if worker is not None and not worker.closed:
            worker.safety_tail()
        journal.close()

if __name__=='__main__':main()
