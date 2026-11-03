"""Serial transport adapter; owns no SSH process and never reconnects/retries.

Root provides pipes of one already contained, pinned SSH worker. Call this in
one IO thread; native animation and model computation remain independent.
"""
import hashlib
import json
import threading
import time

ABI='DEEPEYE-LIVE-BOARD-791-v1'
MAX_RESPONSE=32768

class StreamClient:
    def __init__(self,writer,reader,*,boot_id,build_id,request_hash):
        self.writer,self.reader=writer,reader
        self.binding=dict(boot_id=boot_id,build_id=build_id,request_hash=request_hash)
        self.seq=0;self.source_seq=0;self.unknown=False;self.closed=False;self.ready=False
        self.lock=threading.Lock();self.last=None

    def initialize(self):
        """Worker CLI plan is immutable; stdin init must name that exact plan."""
        with self.lock:
            if self.ready or self.unknown or self.closed:raise ValueError('INIT_ONCE')
            request=dict(abi=ABI,op='init',request_seq=0,**self.binding)
            self.unknown=True
            self.writer.write(json.dumps(request,separators=(',',':')).encode()+b'\n');self.writer.flush()
            response=self._read()
            self._binding(response)
            if response.get('op')!='init' or response.get('status')!='COMPLETE':raise ValueError('INIT_REJECTED')
            self.ready=True;self.unknown=False;return response

    def _read(self):
        raw=self.reader.readline(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE or not raw.endswith(b'\n'):raise ValueError('RESPONSE_UNKNOWN_OR_OVERSIZE')
        return json.loads(raw)

    def _binding(self,r):
        if r.get('abi')!=ABI or any(r.get(k)!=v for k,v in self.binding.items()):
            raise ValueError('RESPONSE_IDENTITY_UNKNOWN')

    def request(self,op,**fields):
        """Blocking serial operation. Root's contained transport bounds pipe IO.

        Once write is attempted, every transport/parse/correlation exception
        permanently poisons the client. No resend or synthetic timeout success.
        """
        with self.lock:
            if not self.ready or self.closed or self.unknown:raise ValueError('CLIENT_NOT_LIVE')
            self.seq+=1
            r=dict(abi=ABI,op=op,request_seq=self.seq,**fields)
            raw=json.dumps(r,separators=(',',':'),allow_nan=False).encode()+b'\n'
            if len(raw)>16384:raise ValueError('REQUEST_BOUND')
            self.unknown=True;before=time.monotonic_ns()
            self.writer.write(raw);self.writer.flush()
            response=self._read();returned=time.monotonic_ns();self._binding(response)
            if response.get('request_seq')!=self.seq or response.get('op')!=op or response.get('status')!='COMPLETE' or response.get('unknown') is not False:
                raise ValueError('ORIGINAL_RESPONSE_REQUIRED')
            self.unknown=False
            self.last=dict(request_sha256=hashlib.sha256(raw[:-1]).hexdigest(),
                           local_before_ns=before,local_returned_ns=returned)
            if op in ('stop','shutdown'):self.closed=True
            return response

    def sense(self,*,adc_tick_ms,em_tick_ms,counts,quality,source_digest):
        self.source_seq+=1
        return self.request('sense',source_seq=self.source_seq,adc_tick_ms=adc_tick_ms,
                            em_tick_ms=em_tick_ms,counts=counts,quality=quality,source_digest=source_digest)

    def apply(self,*,yaw_q,pitch_q,speed_code=2,duration_ms=12000):
        return self.request('apply',yaw_q=yaw_q,pitch_q=pitch_q,speed_code=speed_code,duration_ms=duration_ms)

    def stop(self):return self.request('stop')
    def shutdown(self):return self.request('shutdown')
