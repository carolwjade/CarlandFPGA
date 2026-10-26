"""Private source4 diagnostic lines only. Never wire/BOOT/observation/motion authority."""
import hashlib
import json
import re

MAX_LINE = 16384
MAX_INT = (1 << 63) - 1
CONTEXT_FIELDS = {'operation_id','request_hash','tested_commit','build_manifest_sha256',
                  'boot_id','session_id','tag','clock_domain_id'}


def require(value, message):
    if not value: raise ValueError(message)


def uint(value, bits=64):
    require(type(value) is int and 0 <= value < (1 << bits), 'strict bounded integer required')
    return value


def context(value):
    require(type(value) is dict and set(value) == CONTEXT_FIELDS, 'exact diagnostic context required')
    for name in CONTEXT_FIELDS - {'tag'}:
        require(type(value[name]) is str and 0 < len(value[name]) <= 192 and
                all(32 <= ord(c) < 127 for c in value[name]), 'bounded ASCII context label required')
    for name,size in (('request_hash',64),('tested_commit',40),('build_manifest_sha256',64),('clock_domain_id',32)):
        require(re.fullmatch('[0-9a-f]{%d}' % size,value[name]) is not None, 'complete context digest/domain required')
    require(0 < uint(value['tag'],32), 'nonzero session tag required')
    return dict(value)


def encode(value):
    try: raw=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('utf-8')
    except (TypeError,UnicodeError) as error: raise ValueError('unencodable diagnostic record') from error
    require(0 < len(raw) <= MAX_LINE,'diagnostic line exceeds bound')
    return raw


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_LINE and raw.endswith(b'\n') and
            raw.count(b'\n') == 1 and b'\r' not in raw, 'one bounded newline-terminated record required')
    def pairs(items):
        obj={}
        for key,value in items:
            require(key not in obj,'duplicate diagnostic JSON field');obj[key]=value
        return obj
    def constant(_):raise ValueError('nonfinite diagnostic JSON')
    try: obj=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as error: raise ValueError('malformed diagnostic JSON') from error
    require(type(obj) is dict,'diagnostic object required')
    return obj


def decode_request(raw, expected_context, next_sequence):
    obj=decode(raw)
    require(set(obj)=={'schema','kind','context','request_seq','source_id','source','values','qualities','original_host_qpc_ns'},
            'exact diagnostic scan fields required; no authority fields')
    require(type(obj['schema']) is int and obj['schema']==1 and obj['kind']=='diagnostic_scan','diagnostic scan only')
    require(type(obj['source_id']) is int and obj['source_id']==4 and obj['source']=='software_fixture','explicit source4 software fixture only')
    require(context(obj['context'])==context(expected_context),'diagnostic identity/clock domain mismatch')
    require(0 < uint(obj['request_seq'],32) == next_sequence,'new contiguous diagnostic sequence required')
    for field,bits in (('values',16),('qualities',8),('original_host_qpc_ns',63)):
        require(type(obj[field]) is list and len(obj[field])==4,'four original channels required')
        for value in obj[field]:uint(value,bits)
    times=obj['original_host_qpc_ns']
    require(all(a <= b for a,b in zip(times,times[1:])) and times[0]>0,'original QPC readings reversed')
    require(encode(obj)==raw,'canonical original diagnostic request bytes required')
    return obj


def record(kind, ctx, **fields):
    require(kind in ('diagnostic_ready','diagnostic_capture','diagnostic_stopped'),'private diagnostic type only')
    return {'schema':1,'kind':kind,'context':context(ctx),**fields}


class _HostOwner:
    """Component core; real production owner below requires the actual fixed QPC type."""
    def __init__(self, ctx, clock, *, max_age_ns=100_000_000):
        self.context=context(ctx);self._clock=clock;self._high=0;self._sequence=1
        self._pending=None;self._generation=None;self._trigger=None;self._baseline=None
        self._last_qpc=0;self.state='IDLE';self._age=uint(max_age_ns,63)
        require(0<self._age<=100_000_000,'diagnostic age bound cannot exceed100ms');self._now()
    def _fail(self,message):self.state='FAILED';raise ValueError(message)
    def _now(self):
        try:
            now=self._clock();uint(now,63)
            require(now >= self._high,'original QPC owner clock regressed')
            self._high=now;return now
        except BaseException:
            self.state='FAILED';raise
    def next_request(self,values,qualities):
        if self.state!='IDLE':self._fail('started/unknown request cannot be repeated or replaced')
        try:
            times=[self._now() for _ in range(4)]
            require(times[0]>self._last_qpc,'new request must have original new QPC')
            obj={'schema':1,'kind':'diagnostic_scan','context':self.context,'request_seq':self._sequence,
                 'source_id':4,'source':'software_fixture',
                 'values':values,'qualities':qualities,'original_host_qpc_ns':times}
            raw=encode(obj);decode_request(raw,self.context,self._sequence)
            self._pending=(raw,obj);self._last_qpc=times[-1]
            self.state='STARTED_UNKNOWN'  # Before any external transport write.
            return raw
        except BaseException:self.state='FAILED';raise
    def accept_ready(self,raw):
        try:
            require(self.state=='IDLE' and self._generation is None,'single ready required')
            obj=decode(raw)
            require(set(obj)=={'schema','kind','context','generation','trigger_id','baseline_counters'},'exact ready fields')
            require(obj['schema']==1 and type(obj['schema']) is int and obj['kind']=='diagnostic_ready' and
                    context(obj['context'])==self.context,'ready identity/type mismatch')
            require(0<uint(obj['generation'],32),'actual positive generation required')
            uint(obj['trigger_id'],32)
            require(type(obj['baseline_counters']) is list and len(obj['baseline_counters'])==3,'actual baseline required')
            for value in obj['baseline_counters']:uint(value,32)
            self._generation=obj['generation'];self._trigger=obj['trigger_id'];self._baseline=obj['baseline_counters']
            return obj
        except BaseException:self.state='FAILED';raise
    def accept(self,raw):
        try:
            require(self.state=='STARTED_UNKNOWN' and self._pending is not None,'only original pending response allowed')
            now=self._now();original,request=self._pending;obj=decode(raw)
            require(set(obj)=={'schema','kind','context','request_seq','request_sha256','generation','trigger_id','captures','final_counters'},
                    'exact diagnostic capture fields required')
            require(type(obj['schema']) is int and obj['schema']==1 and obj['kind']=='diagnostic_capture' and
                    context(obj['context'])==self.context and obj['request_seq']==self._sequence and
                    type(obj['request_seq']) is int and obj['request_sha256']==hashlib.sha256(original).hexdigest(),
                    'original pending request correlation mismatch')
            uint(obj['generation'],32);uint(obj['trigger_id'],32)
            require(self._generation is not None and obj['generation']==self._generation and
                    obj['trigger_id']==self._trigger+1,'stable generation and next actual trigger required')
            require(0 <= now-request['original_host_qpc_ns'][0] <= self._age,'diagnostic response expired; arrival cannot renew source')
            captures=obj['captures'];require(type(captures) is list and len(captures)==4,'four actual lanes required')
            for channel,lane in enumerate(captures):
                require(type(lane) is dict and set(lane)=={'channel','raw_words','pipeline_counters','ack_returned'},'exact original lane fields')
                raw_words=lane['raw_words'];ticks=request['original_host_qpc_ns'][channel]
                expected=[request['values'][channel],channel|(request['qualities'][channel]<<8),ticks&0xffffffff,ticks>>32,
                          4*(self._sequence-1),4*self._sequence-1,self.context['tag'],obj['trigger_id'],self._generation]
                require(type(raw_words) is list and len(raw_words)==10 and raw_words[:9]==expected and
                        all(type(x) is int and 0<=x<2**32 for x in raw_words) and lane['channel']==channel and
                        type(lane['channel']) is int and lane['ack_returned'] is True,'raw diagnostic lane mismatch')
                require(type(lane['pipeline_counters']) is list and len(lane['pipeline_counters'])==3,'three exact counters required')
                for value in lane['pipeline_counters']:uint(value,32)
                require(lane['pipeline_counters']==[self._baseline[0]+4*self._sequence,self._baseline[1]+self._sequence,
                                                   self._baseline[2]+4*(self._sequence-1)+channel+1],'actual lane counters mismatch')
            require(type(obj['final_counters']) is list and len(obj['final_counters'])==3,'three exact final counters required')
            for value in obj['final_counters']:uint(value,32)
            require(obj['final_counters']==[self._baseline[0]+4*self._sequence,self._baseline[1]+self._sequence,
                                           self._baseline[2]+4*self._sequence],'final counters mismatch')
            self._trigger=obj['trigger_id'];self._sequence+=1;self._pending=None;self.state='IDLE'
            return obj
        except BaseException:self.state='FAILED';raise
    def retire(self):self.state='FAILED'


class HostOwner(_HostOwner):
    """Production owner: caller must retain one real, fixed fresh-run QPC binding."""
    def __init__(self,ctx,host_clock,*,max_age_ns=100_000_000):
        from . import host_clock as clocks
        require(type(host_clock) is clocks.QpcHostClock,'actual fixed QPC binding required; no component clock')
        clocks._require_binding(host_clock)
        require(context(ctx)['clock_domain_id']==host_clock.metadata['domain_id'],'original QPC domain required')
        self.host_clock=host_clock
        super().__init__(ctx,host_clock,max_age_ns=max_age_ns)
    def next_request(self,values,qualities):
        require(self._generation is not None,'original READY required before new host input')
        return super().next_request(values,qualities)


__all__=['HostOwner','encode','decode','decode_request','record']
