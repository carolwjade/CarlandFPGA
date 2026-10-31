"""Fixed owner-bound local chain work. Never performs transport or authority effects."""
import json
import threading
import time

_JOBS={}
_PERMITS={}
_CLOSING={}
_KEY=object()

class _Job:
    __slots__=('kind','args','end','consumed','thread','done','value','error')
    def __init__(self,key,chain,kind,args,end):
        if key is not _KEY:raise ValueError('fixed work factory required')
        self.kind=kind;self.args=args;self.end=end;self.consumed=False;self.done=threading.Event();self.value=None;self.error=None
        self.thread=threading.Thread(target=_execute,args=(self,),daemon=True)

def _execute(job):
    from . import functional50_chain_v2_client_a as client
    from . import functional50_chain_v2_board_a as protocol
    from . import functional50_board_trace_batch_a as batch
    from . import functional50_trace_batch_client_a as trace
    from . import functional50_g05_a as g05
    from .functional50_ssh_a import _record
    try:
        a=job.args
        if job.kind=='encode':
            ident,kind,payload,operation,snapshot=a
            seq=protocol.Sequence();seq.initialized,seq.closed,counts,ids,seq.max_commands,seq.last,seq.profile=snapshot
            seq.counts=dict(counts);seq.ids=set(ids)
            wire=protocol.raw(dict(schema=protocol.SCHEMA,id=ident,operation_id=operation,kind=kind,payload=payload))+b'\n'
            doc=protocol.decode_request(wire,operation,g05,seq);job.value=(wire,doc)
        elif job.kind=='intent':
            folder,n,ident,kind,wire,lower=a
            _record(folder,f'{n:02d}-started.json',dict(id=ident,kind=kind,raw_hex=wire.hex(),lower_qpc_ns=lower));job.value=True
        elif job.kind=='reply':
            folder,n,response,upper,ident,operation,kind=a
            trace.put(folder/f'{n:02d}-response.bin',response);_record(folder,f'{n:02d}-returned.json',dict(upper_qpc_ns=upper,response_sha256=protocol.digest(response)))
            doc=client._response(response,ident,operation,kind)
            job.value=doc
        elif job.kind=='failure_post':
            result,operation=a;client._failure_facts(result,operation);job.value=True
        elif job.kind=='trace_prepare':
            bundle,request,source,companions,binding,ident,operation,max_io,folder,index=a
            fixed=bundle.adapter.prepare_bytes(request,source,companions,build_binding=binding)
            client.need(fixed.status=='TRACE94_PLAN_PREPARED' and fixed.plan is not None and fixed.plan.facts()['lineage']['operation_id']==operation,'original inputs and operation')
            payload=dict(request_hex=request.hex(),source_hex=source.hex(),companions_hex=[v.hex() for v in companions],build_binding=binding,max_io=max_io)
            p={k:payload[k] for k in ('request_hex','source_hex','companions_hex','build_binding')}
            batch.decode_batch_request(batch.raw(dict(schema=batch.SCHEMA,id=ident,operation_id=operation,**p))+b'\n')
            path=folder/('scan-%02d'%index);path.mkdir(mode=0o700)
            for name,data in [('request.bin',request),('source.bin',source),*[(f'companion-{i}.bin',v) for i,v in enumerate(companions)]]:trace.put(path/name,data)
            job.value=(fixed,payload)
        elif job.kind=='trace_post':
            bundle,fixed,request,source,companions,binding,ident,operation,index,max_io,response=a
            doc=client._response(response,ident,operation,'trace_scan');correlation=None
            if doc['status']=='COMPLETE':
                result=doc['result'];keys={'schema','index','request_sha256','source_sha256','response','phase_io_first','phase_io_last','correlation_status','directory','evidence_manifest_sha256','authority'}
                client.need(type(result) is dict and set(result)==keys and result['schema']=='trace_cycle_v2' and result['index']==index and result['authority']=='not_evaluated' and result['request_sha256']==protocol.digest(request) and result['source_sha256']==protocol.digest(source),'original trace result')
                client.need(result['correlation_status']=='FOUR_FRAME_CORRELATION_CONSISTENT' and type(result['directory']) is str and result['directory'].startswith('/') and len(result['directory'])<=1024 and type(result['evidence_manifest_sha256']) is str and client.re.fullmatch('[0-9a-f]{64}',result['evidence_manifest_sha256']) is not None,'board evidence manifest reference')
                first=result['phase_io_first'];last=result['phase_io_last'];client.need(type(first) is int and type(last) is int and 1<=first<=last<=5000 and last-first+1<=max_io,'actual TRACE phase')
                observed,wire=trace._response(protocol.raw(result['response'])+b'\n',ident,operation,protocol.digest(request),binding['request_hash']);client.need(observed['status']=='COMPLETE','complete trace required')
                correlation=bundle.adapter.correlate_collected(fixed.plan,wire,companions,observed['results']);client.need(correlation['status']=='FOUR_FRAME_CORRELATION_CONSISTENT','host correlation required')
            job.value=(doc,correlation)
        elif job.kind=='g05_post':
            result,kind,operation,identity,deadline,duration,policy_sha,receipts,payload=a
            new=client._facts(result,kind,operation,identity,deadline)
            client.need(new[1]-new[0]==duration and (policy_sha is None or policy_sha==result['policy_sha256']),'fixed duration and policy')
            client.need(result['receipts'][:len(receipts)]==receipts,'original cumulative receipts changed')
            if kind=='apply':client.need(result['capture']['words32'][1:3]==payload['command_words'][5:7],'capture command association')
            job.value=new
        else:raise ValueError('unknown fixed job')
    except BaseException as exc:job.error=exc
    finally:job.done.set()

def _start(chain,kind,args,end):
    from .functional50_chain_v2_client_a import ChainSessionV2
    if (type(chain) is not ChainSessionV2 or threading.get_ident()!=chain.thread or kind not in ('encode','intent','reply','failure_post','trace_prepare','trace_post','g05_post')
        or type(args) is not tuple or type(end) is not int or not 0<end<(1<<63) or not chain.owner_work_v1
        or chain.s._unknown or chain.s._closed or any(old.thread.is_alive() or not old.done.is_set() for old in _JOBS.get(chain,()))):
        raise ValueError('original fixed owner work required')
    ChainSessionV2._phase_binding(chain)
    closing=_closing_for(chain.s)
    if closing is not None and (kind not in ('reply','failure_post','g05_post') or end!=closing.end):raise ValueError('only original close post-work permitted')
    if closing is not None and kind=='reply' and (closing.reply_started or len(args)!=7 or args[2] is not closing.raw or args[4]!=closing.ident or args[6]!='close' or args[1]!=closing.index):raise ValueError('original close reply job required')
    if closing is not None and kind in ('failure_post','g05_post') and (closing.post_started or type(closing.parsed) is not dict or args[0] is not closing.parsed.get('result') or (kind=='failure_post' and closing.parsed.get('status')!='UNKNOWN') or (kind=='g05_post' and (len(args)!=9 or args[1]!='close' or closing.parsed.get('status')!='COMPLETE'))):raise ValueError('original close semantic job required')
    ChainSessionV2._work_pump(chain,_closing=closing)
    if kind in ('intent','reply') and (not args or args[0] is not chain.folder):raise ValueError('original evidence directory required')
    if kind=='trace_prepare' and (len(args)!=10 or args[0] is not chain.bundle or args[8] is not chain.folder):raise ValueError('original trace preparation scope required')
    if kind=='trace_post' and (len(args)!=11 or args[0] is not chain.bundle):raise ValueError('original trace correlation scope required')
    if kind=='encode' and (len(args)!=5 or args[3]!=chain.s._dir.name):raise ValueError('original operation scope required')
    if kind=='failure_post' and (len(args)!=2 or args[1]!=chain.s._dir.name):raise ValueError('original failure operation scope required')
    if kind=='g05_post' and (len(args)!=9 or args[2]!=chain.s._dir.name):raise ValueError('original G05 operation scope required')
    if closing is not None:
        if kind=='reply':closing.reply_started=True
        elif kind in ('failure_post','g05_post'):closing.post_started=True
    job=_Job(_KEY,chain,kind,args,end);_JOBS.setdefault(chain,[]).append(job);job.thread.start();return job

def _wait(chain,job,end):
    from . import functional50_ssh_a as ssh
    from .original_chain_source_pump_a import OriginalChainSourcePump
    session=chain.s;pump=getattr(session,'_source_pump',None)
    if (threading.get_ident()!=chain.thread or type(job) is not _Job
        or not any(x is job for x in _JOBS.get(chain,())) or type(end) is not int or end!=job.end
        or type(pump) is not OriginalChainSourcePump or ssh._SESSION_PUMPS.get(session) is not pump
        or pump.session is not session or pump.clock is not chain.clock or not pump.enabled):
        raise ValueError('fixed original job/pump/owner required')
    try:
        while True:
            if chain.clock()>=end:raise TimeoutError('fixed owner work deadline expired')
            if job.done.is_set() and not job.thread.is_alive():break
            closing=_closing_for(session)
            if closing is None:OriginalChainSourcePump.poll_once(pump,session)
            else:OriginalChainSourcePump.poll_once(pump,session,_closing=closing)
            remaining=end-chain.clock()
            if remaining<=0:raise TimeoutError('fixed owner work deadline expired')
            if not job.done.is_set() or job.thread.is_alive():time.sleep(min(remaining,1_000_000)/1_000_000_000)
        if job.error is not None:raise job.error
        closing=_closing_for(session)
        if closing is not None and job.kind=='reply':closing.parsed=job.value
        return job.value
    except BaseException:session._unknown=True;raise

class _Permit:
    __slots__=('chain','session','end','wire','used','owner','kind','ident','index')
    def __init__(self,key,chain,end,wire,intent):
        if key is not _KEY:raise ValueError('fixed permit required')
        self.chain=chain;self.session=chain.s;self.end=end;self.wire=wire;self.used=False;self.owner=threading.get_ident()
        self.index=intent.args[1];self.ident=intent.args[2];self.kind=intent.args[3]

def _permit(chain,end,wire,intent_job,prepared=None):
    if (threading.get_ident()!=chain.thread or type(end) is not int or type(wire) is not bytes
        or not chain.owner_work_v1 or type(intent_job) is not _Job
        or not any(x is intent_job for x in _JOBS.get(chain,())) or intent_job.kind!='intent'
        or intent_job.end!=end or intent_job.args[4] is not wire or intent_job.consumed
        or not intent_job.done.is_set() or intent_job.error is not None or intent_job.value is not True):
        raise ValueError('completed original started intent required')
    intent_job.consumed=True
    if intent_job.args[3]=='trace_scan':
        if prepared is None:raise ValueError('original trace guard required')
        from .functional50_chain_v2_client_a import ChainSessionV2
        from .original_source_trace_scan_a import OriginalSourceTraceScan
        scanner=ChainSessionV2._work_pump(chain).scanner;expected=OriginalSourceTraceScan._prepared_work_deadline(scanner,prepared)
        if OriginalSourceTraceScan._check_prepared_dispatch(scanner,prepared)!=expected or end>expected:raise ValueError('original selected dispatch guard failed')
    elif prepared is not None:raise ValueError('unexpected trace guard')
    if chain.clock()>=end:raise TimeoutError('original phase expired before transport')
    p=_Permit(_KEY,chain,end,wire,intent_job);_PERMITS[p]=p;return p

def _consume(session,wire,permit):
    if (type(permit) is not _Permit or _PERMITS.get(permit) is not permit or permit.used
        or permit.session is not session or permit.chain.s is not session or permit.owner!=threading.get_ident()
        or permit.chain.thread!=permit.owner or permit.wire is not wire or not permit.chain.owner_work_v1):
        raise ValueError('exact original one-use owner permit required')
    from .functional50_chain_v2_client_a import ChainSessionV2
    ChainSessionV2._phase_binding(permit.chain)
    permit.used=True
    if permit.kind=='close':
        if not permit.chain.sequence.closed or permit.ident not in permit.chain.sequence.ids or session in _CLOSING:raise ValueError('one original close phase required')
        _CLOSING[session]=_Closing(_KEY,permit)
    return permit.end

class _Closing:
    __slots__=('chain','session','process','stdin','stdout','clock','owner','end','wire','ident','index','active','raw','origin','parsed','reply_started','post_started')
    def __init__(self,key,permit):
        if key is not _KEY:raise ValueError('private original close required')
        self.chain=permit.chain;self.session=permit.session;self.process=self.session._proc
        from .functional50_chain_v2_client_a import ChainSessionV2
        self.origin=ChainSessionV2._phase_binding(self.chain)
        if self.process is not self.origin[1] or self.process.stdin is not self.origin[7] or self.process.stdout is not self.origin[8]:raise ValueError('original close pipes changed')
        self.stdin=self.process.stdin;self.stdout=self.process.stdout;self.clock=self.chain.clock
        self.owner=permit.owner;self.end=permit.end;self.wire=permit.wire;self.ident=permit.ident;self.index=permit.index
        self.active=True;self.raw=None;self.parsed=None;self.reply_started=False;self.post_started=False

def _closing_for(session):
    context=_CLOSING.get(session)
    return context if context is not None and context.active else None

def _verify_closing(session,context):
    from .functional50_chain_v2_client_a import ChainSessionV2
    if (type(context) is not _Closing or _CLOSING.get(session) is not context or not context.active
        or context.session is not session or context.chain.s is not session or context.owner!=threading.get_ident()
        or context.chain.thread!=context.owner or session._thread!=context.owner or session._unknown or session._closed
        or session._proc is not context.process or context.process.stdin is not context.stdin or context.process.stdout is not context.stdout
        or session._clock is not context.clock or context.chain.clock is not context.clock or not context.chain.sequence.closed
        or context.ident not in context.chain.sequence.ids or context.clock()>=context.end):
        raise ValueError('original close context invalid or expired')
    if ChainSessionV2._phase_binding(context.chain) is not context.origin or context.origin[1] is not context.process or context.origin[2] is not context.clock or context.origin[7] is not context.stdin or context.origin[8] is not context.stdout:raise ValueError('original close origin changed')
    state=context.process.poll()
    if state is not None and (type(state) is not int or state!=0):raise ValueError('original close process failed')
    if session._stderr_overflow:raise ValueError('stderr budget exceeded')

def _finish_closing(session):
    context=_CLOSING.get(session)
    if context is not None:context.active=False


def _await_close_exit(session):
    from .original_chain_source_pump_a import OriginalChainSourcePump
    context=_closing_for(session)
    if context is None:return
    pump=getattr(session,'_source_pump',None)
    try:
        while True:
            _verify_closing(session,context)
            state=context.process.poll()
            if state is not None:return
            OriginalChainSourcePump.poll_once(pump,session,_closing=context)
            remaining=context.end-context.clock()
            if remaining<=0:raise TimeoutError('original close exit deadline expired')
            time.sleep(min(remaining,1_000_000)/1_000_000_000)
    except BaseException:session._unknown=True;raise
