"""798 synchronous client for the frozen 794 live-native JSONL ABI.

Import is inert. Root owns actual native/board startup and containment.
No reconnect/resend, no mission count/time cap, no hidden geometry interface.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import socket
import threading
import time

ABI='DEEPEYE-CONTINUOUS-NATIVE-794-v1'
BOARD_ABI='DEEPEYE-LIVE-BOARD-791-v1'
CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'

def need(ok,reason):
    if not ok:raise ValueError(reason)

def uint(value,minimum=0,maximum=(1<<63)-1):
    need(type(value) is int and minimum<=value<=maximum,'EXACT_INTEGER_BOUND')
    return value

def tick(value):
    need(type(value) is str and value.isascii() and value.isdecimal() and str(int(value))==value,'CANONICAL_NATIVE_TICK')
    return uint(int(value))

def hex64(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'SHA256')
    return value

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

def parse(raw):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'DUPLICATE_RESPONSE_KEY');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))

@dataclass(frozen=True)
class ClockBracket:
    """One server read_now tick is genuinely inside this send/receive bracket.

    Native tick resolution is1us. ppm is a caller-owned maximum relative rate
    error assumption, not an observed clock calibration or formal clock proof.
    """
    send_qpc_ns:int
    receive_qpc_ns:int
    native_read_usec:int
    max_relative_rate_error_ppm:int=1000
    def __post_init__(self):
        uint(self.send_qpc_ns);uint(self.receive_qpc_ns,self.send_qpc_ns)
        uint(self.native_read_usec);uint(self.max_relative_rate_error_ppm,0,10000)
    @property
    def offset_min_ns(self):return self.native_read_usec*1000-self.receive_qpc_ns
    @property
    def offset_max_ns(self):return self.native_read_usec*1000+999-self.send_qpc_ns
    def _drift(self,span_ns):
        ppm=self.max_relative_rate_error_ppm
        return (abs(span_ns)*ppm+1_000_000-ppm-1)//(1_000_000-ppm)
    def accepted_tick_qpc_interval(self,native_tick_usec):
        n=uint(native_tick_usec)*1000
        need(native_tick_usec<=self.native_read_usec,'ACCEPTED_TICK_NOT_FUTURE')
        drift=self._drift(self.native_read_usec*1000-n)
        return (max(0,n-self.offset_max_ns-drift),min(self.receive_qpc_ns,n+999-self.offset_min_ns+drift))
    def conservative_native_deadline_usec(self,host_deadline_qpc_ns,*,guard_ns=1_000_000):
        uint(host_deadline_qpc_ns,self.receive_qpc_ns+1);uint(guard_ns)
        drift=self._drift(host_deadline_qpc_ns-self.send_qpc_ns)
        result=(host_deadline_qpc_ns+self.offset_min_ns-drift-guard_ns)//1000
        need(result>self.native_read_usec,'NO_CONSERVATIVE_GRANT_REMAINS')
        return result

class NativeRejected(RuntimeError):
    def __init__(self,response):
        super().__init__('Native explicitly rejected request: '+str(response.get('reason','unknown')))
        self.response=response

class NativeClient:
    def __init__(self,connected_socket,token,*,board_binding=None,timeout_s=2.0,
                 max_relative_rate_error_ppm=1000,clock=time.perf_counter_ns):
        need(type(token) is str and 32<=len(token)<=128 and token.isascii(),'TOKEN')
        need(type(timeout_s) in (int,float) and math.isfinite(timeout_s) and 0<timeout_s<=10,'PER_REQUEST_TIMEOUT')
        uint(max_relative_rate_error_ppm,0,10000)
        self.socket=connected_socket;self.token=token;self.timeout_s=float(timeout_s)
        self.ppm=max_relative_rate_error_ppm;self.clock=clock;self.lock=threading.Lock()
        self.seq=0;self.board_seq=0;self.broken=False;self.closed=False;self.ready=False
        self.bracket=None;self.last_exchange=None;self.board_binding=None
        if board_binding is not None:self.bind_board(board_binding)
    @classmethod
    def connect(cls,port,token,**kwargs):
        uint(port,1024,65535)
        sock=socket.create_connection(('127.0.0.1',port),timeout=kwargs.get('timeout_s',2.0))
        client=cls(sock,token,**kwargs)
        try:client.hello();return client
        except BaseException:sock.close();raise
    def bind_board(self,binding):
        need(self.board_binding is None,'BOARD_BIND_ONCE')
        need(type(binding) is dict and set(binding)=={'boot_id','build_id','request_hash'},'BOARD_BINDING')
        need(all(type(v) is str for v in binding.values()) and len(binding['boot_id'])==36 and len(binding['build_id'])==32,'BOARD_IDENTITY')
        hex64(binding['request_hash']);self.board_binding=dict(binding)
    def _exchange(self,op,**fields):
        with self.lock:
            need(not self.closed and not self.broken,'CLIENT_CLOSED_OR_UNKNOWN_NO_RETRY')
            need(op=='hello' or self.ready,'HELLO_REQUIRED')
            self.seq+=1;uint(self.seq,1,(1<<53)-1)
            request=dict(abi=ABI,token=self.token,seq=self.seq,op=op,**fields)
            wire=canonical(request)+b'\n';need(len(wire)<=8192,'REQUEST_BYTES')
            t0=self.clock();end=t0+int(self.timeout_s*1e9)
            attempted=False
            try:
                self.socket.settimeout(self.timeout_s)
                attempted=True;self.socket.sendall(wire)
                buf=bytearray()
                while not buf.endswith(b'\n'):
                    remaining=(end-self.clock())/1e9
                    if remaining<=0:raise TimeoutError('NATIVE_RESPONSE_TIMEOUT')
                    self.socket.settimeout(remaining)
                    chunk=self.socket.recv(min(4096,16385-len(buf)))
                    need(chunk,'NATIVE_EOF_UNKNOWN');buf.extend(chunk)
                    need(len(buf)<=16384,'RESPONSE_BYTES')
                    need(b'\n' not in buf[:-1],'EXACTLY_ONE_RESPONSE')
                t1=self.clock();need(t1<=end,'TOTAL_REQUEST_TIMEOUT')
                response=parse(buf)
                seq=response.get('seq')
                need(type(response) is dict and response.get('abi')==ABI and
                     type(seq) in (int,float) and math.isfinite(seq) and seq==self.seq and
                     type(response.get('ok')) is bool,'ORIGINAL_RESPONSE_BINDING')
                if response['ok']:
                    state=response.get('state');self._validate_state(state)
                    bracket=ClockBracket(t0,t1,tick(state['read_now_usec']),self.ppm)
                    interval=bracket.accepted_tick_qpc_interval(tick(state['tick_usec']))
                    self.bracket=bracket
                    # Host correlation is separate from unmodified native state.
                    self.last_exchange=dict(send_qpc_ns=t0,receive_qpc_ns=t1,
                                            request_sha256=hashlib.sha256(wire[:-1]).hexdigest(),
                                            accepted_tick_qpc_interval_ns=interval)
            except BaseException:
                if attempted:self.broken=True
                raise
            if not response['ok']:raise NativeRejected(response)
            return response
    @staticmethod
    def _validate_state(state):
        need(type(state) is dict and state.get('abi')==ABI,'STATE_ABI')
        required={'ready','tick_usec','read_now_usec','revision','position_m','orientation_xyzw',
                  'speed_m_s','target_speed_m_s','yaw_curvature_per_m','pitch_curvature_per_m',
                  'phase','history','fault','running','board_request_seq','board_receipt_sha256',
                  'deadline_usec','operator_request','formal_acceptance','abi'}
        need(set(state)==required,'PUBLIC_OWNPOSE_STATE_ONLY')
        for key,size in (('position_m',3),('orientation_xyzw',4)):
            need(type(state[key]) is list and len(state[key])==size and
                 all(type(v) in (int,float) and math.isfinite(v) for v in state[key]),'FINITE_POSE')
        tick(state['tick_usec']);tick(state['read_now_usec']);tick(state['deadline_usec']);tick(state['revision'])
        need(type(state['ready']) is bool and type(state['running']) is bool and
             type(state['fault']) is str and type(state['phase']) is str and
             type(state['history']) is list and len(state['history'])<=5 and
             all(type(v) is str for v in state['history']) and state['formal_acceptance']=='not_run','STATE_FIELDS')
        need(abs(sum(float(v)**2 for v in state['orientation_xyzw'])-1.0)<=0.00002,'STATE_QUATERNION')
        for key in ('speed_m_s','target_speed_m_s','yaw_curvature_per_m','pitch_curvature_per_m'):
            need(type(state[key]) in (int,float) and math.isfinite(state[key]),'STATE_MOTION_SCALAR')
        need(0<=state['speed_m_s']<=.250001 and 0<=state['target_speed_m_s']<=.25 and
             state['yaw_curvature_per_m']**2+state['pitch_curvature_per_m']**2<=.250000000001,
             'STATE_PHYSICAL_BOUNDS')
    def hello(self):
        need(not self.ready,'HELLO_ONCE')
        response=self._exchange('hello');self.ready=True;return response
    def state(self):
        response=self._exchange('state')
        return dict(native=response['state'],host=dict(self.last_exchange))
    def apply_pwm(self,board_response,*,grant_deadline_qpc_ns,pause=False):
        """Caller supplies a conservative HOST-QPC deadline from actual board IO.

        Board monotonic_ns is a different domain and must NOT be passed here.
        Real receipt shape/PWM is checked; this is not source/transport authority.
        """
        need(self.board_binding is not None and self.bracket is not None,'BOARD_AND_CLOCK_BINDING_REQUIRED')
        r=board_response
        need(type(r) is dict and r.get('abi')==BOARD_ABI and r.get('op')=='apply' and
             r.get('status')=='COMPLETE' and r.get('unknown') is False and
             all(r.get(k)==v for k,v in self.board_binding.items()),'ACTUAL_BOUND_APPLY_REQUIRED')
        seq=uint(r.get('request_seq'),self.board_seq+1,0xffffffff)
        result=r['result'];command=result['command_words'];words=result['capture_words']
        need(type(command) is list and len(command)==7 and type(words) is list and len(words)==32 and
             all(type(v) is int and 0<=v<=0xffffffff for v in command+words),'CAPTURE_WORDS')
        y,p,profile,speed,ttl,cseq,tag=command
        need(profile==1 and cseq==tag==seq and 1<=ttl<=12000 and speed<=20 and y<=65535 and p<=65535,'COMMAND_BINDING')
        signed=lambda v:v if v<32768 else v-65536
        from competition.deepeye.integration.motion import validate
        mapped=validate('fast_9600',speed,signed(y),signed(p))
        need(words[0]>0 and words[1:6]==[seq,tag,(speed<<8)|1,(p<<16)|y,ttl] and words[31]==0x47303550 and words[30]>0,'CAPTURE_COMMAND')
        u64=lambda i:words[i]|words[i+1]<<32
        need(u64(6)<u64(10)<u64(8) and u64(8)-u64(6)==ttl*50000,'ACTUAL_50MHZ_TTL')
        starts=[u64(18+2*i) for i in range(3)];ends=[u64(24+2*i) for i in range(3)]
        need(u64(10)>=u64(6)+max(ends),'CAPTURE_RESULT_AFTER_LOCAL_END_WITNESSES')
        for period,high,start,end,expected in zip(words[12:15],words[15:18],starts,ends,
                                               (125000+8*signed(y),125000+8*signed(p),25000+500*speed)):
            need(abs(period-1000000)<=1 and abs(high-expected)<=1 and 0<high<period and
                 0<start<end<=0xffffffff and end-start==period,'ACTUAL_PWM_CAPTURE')
        need(max(starts)-min(starts)<=1 and max(ends)-min(ends)<=1,'COHERENT_PWM')
        need(not pause or speed==0,'PAUSE_REQUIRES_ZERO_PWM')
        now=self.clock()
        host_deadline=uint(grant_deadline_qpc_ns,now+100_000_000)
        need(host_deadline<=now+ttl*1_000_000,'ACTUAL_TTL_CAP')
        native_deadline=self.bracket.conservative_native_deadline_usec(host_deadline)
        receipt=hashlib.sha256(canonical(r)).hexdigest()
        response=self._exchange('pause' if pause else 'apply',speed_m_s=mapped.target_speed_m_s,
                                yaw_curvature_per_m=mapped.curvature_yaw_per_m,
                                pitch_curvature_per_m=mapped.curvature_pitch_per_m,
                                native_deadline_usec=str(native_deadline),board_request_seq=seq,
                                board_receipt_sha256=receipt)
        state=response['state']
        try:
            need(type(state['board_request_seq']) in (int,float) and state['board_request_seq']==seq and
                 tick(state['deadline_usec'])==native_deadline and state['board_receipt_sha256']==receipt and
                 state['target_speed_m_s']==mapped.target_speed_m_s and
                 abs(state['yaw_curvature_per_m']-mapped.curvature_yaw_per_m)<1e-12 and
                 abs(state['pitch_curvature_per_m']-mapped.curvature_pitch_per_m)<1e-12,
                 'APPLY_STATE_CORRELATION')
        except BaseException:self.broken=True;raise
        self.board_seq=seq
        return response
    def pause(self,actual_zero_pwm_response,*,grant_deadline_qpc_ns):
        return self.apply_pwm(actual_zero_pwm_response,grant_deadline_qpc_ns=grant_deadline_qpc_ns,pause=True)
    def stop(self):
        response=self._exchange('stop')
        if response.get('board_stop_acknowledged') is not False:
            self.broken=True;raise ValueError('NATIVE_STOP_IS_NOT_BOARD_STOP')
        return response
    def close(self):
        # Disconnect is a native safety event; Root separately closes the board.
        self.closed=True;self.socket.close()
