"""NEW root-owned two-call serial diagnostic extension, never an A AI lease.
Retains the byte-identical qualified ActorOwner and original resources. It does
not reset its one-slot flag or write reservation; call two has its own permanent
reservation. No generic callback, PID adoption, retry, completion slot or BOOT.
UNEXECUTED: independently review and qualify before Root actual release.
"""
from dataclasses import asdict
import hashlib
import threading
import time
from competition.deepeye.simulation.isolation import actor_owner as retained
from competition.deepeye.simulation.isolation.actor_lifetime import _sample
from competition.deepeye.integration.cpu_invocation_transcript import InvocationIdentity, _new_actor_record
from framing_contract import need, integer, identity, typed_equal, response_total, decode_response, verify_result, verify_ended

_READY_KEY=object()

class _ModelReadyProof:
    def __init__(self,key,owner,reference,event,before,after,readback,wait_result):
        need(key is _READY_KEY,'only original event observation can prepare readiness proof')
        self.owner,self.reference,self.event=owner,reference,event
        self.process,self.native,self.creation=owner._original_process,owner._original_native,owner._creation_filetime
        self.interval=[before,after]; self.readback=readback; self.wait_result=wait_result

@retained._entry
def _poll_original_ready(owner,event_ref):
    owner._invocation_check(); io=owner._pending_io; io.continuity()
    need(owner._resources.find('model_ready') is event_ref and owner._model_ready_reference is event_ref and event_ref.native==owner._model_ready_native and not event_ref.attempted and not event_ref.ambiguous,'original model-ready event continuity required')
    ready_flags=owner._api.handle_flags(event_ref.native)
    need(type(ready_flags) is int and ready_flags==0,'parent model-ready event must remain noninheritable')
    before=owner._time(); state=owner._api.Wait(event_ref.native,0)
    need(type(state) is int and state in (0,258),'original ready wait failed/unknown')
    _sample(owner)
    if state==258: return None
    job=owner._resources.find('job')
    sid=owner._api.sid_text(owner._resources.find('profile_sid').native,owner=owner._resources)
    readback=owner._api.inspect_process(owner._original_native,job.native,sid,owner=owner._resources)
    need(type(readback.get('creation_filetime')) is int and readback['creation_filetime']==owner._creation_filetime,'ready event must bind same original process creation')
    for name in ('is_appcontainer','sid_matches','win32k_disabled','child_process_restricted','in_job','job_limits_match'):
        need(readback.get(name) is True,'model-ready original policy readback failed')
    need(type(readback.get('capability_count')) is int and readback['capability_count']==0,'model-ready original zero capabilities required')
    _sample(owner); after=owner._time()
    return _ModelReadyProof(_READY_KEY,owner,event_ref,event_ref.native,before,after,readback,state)

def wait_original_model_ready(owner):
    """Finite original event observation; not wire readiness/BOOT/AI completion."""
    need(type(owner) is retained.ActorOwner and owner._registry._contains(owner),'fresh original owner required')
    ref=owner._model_ready_reference
    need(ref is not None and owner._invocation is None and owner._invocation_claimed is False,'ready precedes first invocation only')
    try:
        for _ in range(40001):
            proof=_poll_original_ready(owner,ref)
            if proof is not None: return proof
            time.sleep(.001)
        raise ValueError('fixed model-ready poll budget exhausted')
    except BaseException:
        try: owner.close('new model-ready gate failed; no invocation/retry')
        except BaseException: pass
        raise

@retained._entry
def _prove_original(owner,session):
    need(session.owner is owner,'original session owner required')
    session._continuity()
    owner._invocation_check()
    io=owner._pending_io; io.continuity()
    need(not io.teardown_started and not io.quarantined and not io.errors,'original IO retired/unknown')
    job=owner._resources.find('job')
    sid=owner._api.sid_text(owner._resources.find('profile_sid').native,owner=owner._resources)
    readback=owner._api.inspect_process(owner._original_native,job.native,sid,owner=owner._resources)
    need(type(readback.get('creation_filetime')) is int and readback['creation_filetime']==session.creation,'same original creation FILETIME required')
    need(type(readback.get('capability_count')) is int and readback['capability_count']==0,'original zero capabilities required')
    for name in ('is_appcontainer','sid_matches','win32k_disabled','child_process_restricted','in_job','job_limits_match'):
        need(readback.get(name) is True,'original process policy changed: '+name)
    _sample(owner)
    session._continuity()
    return dict(original_process_native=owner._original_native,creation_filetime=session.creation,
                original_input_write=io.endpoints['input_write'][1],original_output_read=io.endpoints['output_read'][1],
                instance_id=owner.instance_id,readback=readback)

@retained._entry
def _prepare_second(owner,session,ident,request):
    need(type(session) is RootSerialSession and session.state=='RESULT_VERIFIED','previous actual RESULT gate required')
    session._continuity(); session._settled_clean()
    previous=owner._invocation
    need(previous is session.records[0] and previous._close_attempted and previous._close_error is None,'first original journal cleanly closed')
    need(not previous._failed and not previous._journal_failed and not previous._unknown_consumption and not previous._eof and not previous._zero_read_stop,'first original invocation not complete/known')
    need(owner._invocation_claimed is True and owner._pending_io.write_reserved is True,'original one-slot reservation must remain consumed')
    owner._invocation_check()
    record=_new_actor_record(owner,ident,request_raw=request,journal_name='c22-invocation-02.jsonl',
        max_output_bytes=min(6160,8192-session.total_output),max_reads=32-session.total_reads,
        read_size=6160,io_deadline_ns=session.owner_deadline)
    session.records.append(record)  # Retain before open/fsync can fail.
    owner._invocation=record
    record.prepare(); owner._invocation_check()

@retained._entry
def _dispatch_serial(owner,session,index):
    need(type(session) is RootSerialSession and type(index) is int and index in (1,2) and session.state==('OBSERVING' if index==1 else 'ENDING'),'exact original serial dispatch state required')
    if index==1:
        need(owner._pending_io.write_reserved is False,'first original write permanently reserved')
        owner._pending_io.write_reserved=True
    else:
        need(not session.second_write_reserved,'second original write permanently reserved')
        session.second_write_reserved=True
    # Reserve before clock, marker, journal or native side effect; never reset.
    session._continuity(); record=owner._require_invocation()
    need(record is session.records[index-1],'exact original serial record required')
    row=record.start_dispatch(); row['started_marker_ns']=owner._invocation_check()
    record._append(row)  # fsync before this sole WriteFile; never a remainder/retry.
    session._continuity()
    op=owner._pending_io.operation(owner._pending_io.endpoints['input_write'][0],'write',len(record.request),record.request)
    op.row=row; row['raw_call_bracket_ns'][0]=owner._invocation_check()
    try:
        session._continuity()  # After marker fsync, immediately before original IO.
        owner._pending_io.issue(op)
        session._continuity()
    finally: owner._pending_io.account(op,journal=False)
    if op.result_bool:
        observed_before=owner._time();session._continuity();owner._pending_io.observe(op)
        observed_after=owner._time();session._continuity()
        if op.settled: row['result_observation_bracket_ns']=[observed_before,observed_after]
    owner._pending_io.account(op)
    row['raw_call_bracket_ns'][1]=owner._invocation_check()
    if op.settled: need(op.error==0 and type(op.count) is int and op.count==len(record.request),'second original write failed/short; no remainder')
    record._append(row); session._continuity()
    return record.snapshot()

@retained._entry
def _read_exact_part(owner,session,maximum):
    integer(maximum,1,6160); session._continuity()
    record=owner._require_invocation(); owner._invocation_check()
    need(record.dispatch is not None and record.dispatch.get('bytes_written')==len(record.request),'complete original write before read')
    need(not any(op.issued and not op.settled for op in owner._pending_io.operations),'no pending operation before next original read')
    need(session.total_reads+len(record.reads)<32,'session cumulative read budget exhausted')
    row=record.start_read()
    row['requested_bytes']=min(row['requested_bytes'],maximum)
    record._append(row)
    session._continuity()
    op=owner._pending_io.operation(owner._pending_io.endpoints['output_read'][0],'read',row['requested_bytes'])
    op.row=row; row['raw_call_bracket_ns'][0]=owner._invocation_check()
    try:
        session._continuity()  # After marker fsync, immediately before original IO.
        owner._pending_io.issue(op)
        session._continuity()
    finally: owner._pending_io.account(op,journal=False)
    if op.result_bool:
        observed_before=owner._time();session._continuity();owner._pending_io.observe(op)
        observed_after=owner._time();session._continuity()
        if op.settled: row['result_observation_bracket_ns']=[observed_before,observed_after]
    owner._pending_io.account(op)
    row['raw_call_bracket_ns'][1]=owner._invocation_check(); record._append(row)
    if op.settled: need(op.error==0 and type(op.count) is int and op.count>0,'original read failed/EOF/zero; no next invocation')
    session._continuity()
    return record.snapshot()

@retained._entry
def _poll_serial(owner,session):
    session._continuity(); owner._invocation_check()
    record=owner._require_invocation()
    for op in owner._pending_io.operations:
        if op.kind=='connect' or not op.issued or op.settled: continue
        session._continuity();observed_before=owner._time()
        owner._pending_io.observe(op)
        observed_after=owner._time();session._continuity()
        if op.settled: op.row['result_observation_bracket_ns']=[observed_before,observed_after]
        owner._pending_io.account(op)
        if op.settled:
            need(op.error==0 and type(op.count) is int and op.count>0,'serial original pending result failed/EOF/zero')
            if op.kind=='write': need(op.count==len(record.request),'serial original asynchronous short write; no remainder')
    owner._invocation_check();session._continuity()
    return record.snapshot()

class RootSerialSession:
    """Fresh original unbound actor; fixed OBSERVE->RESULT->END->ENDED only."""
    def __init__(self,owner,*,readiness,expected_result_raw,oracle_raw,expected_end_raw):
        need(type(owner) is retained.ActorOwner and owner._registry._contains(owner),'original registry-acquired owner required')
        need(owner.state=='RUNNING_UNBOUND' and owner._boot is None,'diagnostic must remain unbound; no forged BOOT')
        io=owner._pending_io
        need(io is not None and owner._invocation is None and owner._invocation_claimed is False and io.write_reserved is False,'fresh original overlapped actor, not an upgrade/replay')
        need(len(io.operations)==2 and all(op.kind=='connect' and op.settled and op.error in (0,535) for op in io.operations),'only original settled pipe connections may precede session')
        self.owner=owner; self.thread=threading.get_ident(); self.state='READY'
        self.creation=owner._creation_filetime; self.process=owner._original_process
        self.native=owner._original_native; self.io=io
        self.endpoints=tuple(io.endpoints[name] for name in ('input_write','output_read'))
        need(type(readiness) is _ModelReadyProof and readiness.owner is owner and readiness.process is self.process and readiness.native==self.native and readiness.creation==self.creation and readiness.reference is owner._model_ready_reference and readiness.event==owner._model_ready_native,'original model-ready event proof required before dispatch')
        self.readiness=readiness
        self.owner_deadline=min(owner._ready_deadline,owner._run_deadline)
        self.feedback_started_ns=self.deadline=None
        need(owner._time()<self.owner_deadline,'original readiness/lifetime expired')
        self.expected_result=expected_result_raw; self.oracle=oracle_raw; self.expected_end=expected_end_raw
        need(all(type(raw) is bytes and 1<=len(raw)<=4096 for raw in (expected_result_raw,oracle_raw,expected_end_raw)),'pinned bounded diagnostic oracle bytes required')
        self.records=[]; self.results=[]; self.inspections=[]; self.first_identity=None
        self.total_input=self.total_output=self.total_reads=0; self.second_write_reserved=False
        self._continuity()

    def _continuity(self):
        owner=self.owner
        need(threading.get_ident()==self.thread,'original root session thread required')
        need(owner._registry._contains(owner) and owner._original_process is self.process and owner._process is self.process and owner._original_native==self.native and owner._creation_filetime==self.creation,'same original process/reference/creation required')
        need(owner._pending_io is self.io and owner._resources._pending_io is self.io,'same original IO resource cohort required')
        for name,bound in zip(('input_write','output_read'),self.endpoints):
            current=self.io.endpoints[name]
            need(current[0] is bound[0] and current[1]==bound[1],'same original HANDLE endpoint required')
        self.io.continuity()
        now=owner._time()
        need(now<self.owner_deadline,'original readiness/lifetime expired')
        if self.deadline is not None: need(now<self.deadline,'fixed cumulative 100ms feedback deadline expired')

    def _settled_clean(self):
        io=self.io; self._continuity()
        need(io.all_settled and not io.teardown_started and not io.quarantined and not io.errors,'pending/teardown/unknown forbids next call')
        for op in io.operations:
            need(op.issued and op.settled and not op.unknown and not op.cancel_attempted,'every original operation must be settled and uncancelled')
            need(op.error in ((0,535) if op.kind=='connect' else (0,)),'every original operation must have known successful raw result')
            if op.kind!='connect': need(type(op.count) is int and op.count>0,'exact nonzero original count required')

    def _wait(self,condition):
        for _ in range(20001):
            self._continuity()
            snap=self.owner.invocation_snapshot()
            need(not snap['failed'] and not snap['journal_failed'] and not snap['eof'] and not snap['zero_read_stop'],'original invocation failed/EOF')
            if condition(snap): return snap
            _poll_serial(self.owner,self); time.sleep(.001)
        raise ValueError('fixed finite poll budget exhausted; no retry')

    def _receive(self,request):
        self._wait(lambda snap: snap['dispatch']['bytes_written']==len(request))
        raw=b''; target=16
        while len(raw)<target:
            need(len(self.owner._invocation.reads)<32-self.total_reads,'cumulative read count exhausted')
            before=len(self.owner._invocation.reads)
            _read_exact_part(self.owner,self,target-len(raw))
            snap=self._wait(lambda value: value['reads'][before]['returned_bytes'] is not None)
            row=snap['reads'][before]
            need(row.get('winerror')==0 and row.get('cancel_attempted') is False and row.get('unknown_consumption') is False and row.get('os_result_observed') is True,'original completed read result required')
            part=bytes.fromhex(row['raw_hex'])
            need(type(row['returned_bytes']) is int and len(part)==row['returned_bytes'] and 0<len(part)<=target-len(raw),'original exact read count/bytes mismatch')
            raw+=part
            if len(raw)==16 and target==16:
                target=response_total(raw)
                need(target<=min(6160,8192-self.total_output),'response exceeds remaining cumulative output cap')
        self._settled_clean()
        snap=self.owner.invocation_snapshot()
        need(snap['unknown_consumption'] is False,'unknown original consumption forbids completion')
        payload=decode_response(raw,request)
        return raw,payload,snap

    def invoke(self,ident,request):
        """Only fixed call1 OBSERVE then call2 END; no user completion callback."""
        try:
            need(type(ident) is InvocationIdentity,'exact retained InvocationIdentity required')
            value=asdict(ident); identity(value)
            index=1 if self.state=='READY' else 2 if self.state=='RESULT_VERIFIED' else 0
            need(index in (1,2) and ident.invocation_id==index,'fixed fresh invocation order 1,2 required')
            need(type(request) is bytes and 16<=len(request)<=16384,'original full bounded request required')
            from framing_contract import HEADER,document
            magic,version,kind,flags,ml,pl=HEADER.unpack(request[:16])
            need(magic==b'C22E' and version==1 and flags==0 and kind==index and len(request)==16+ml+pl and 1<=ml<=2048,'exact OBSERVE then END request frame required')
            meta=document(request[16:16+ml])
            need(type(meta) is dict and meta.keys()=={'identity','frame_index','payload_sha256'} and typed_equal(meta['identity'],value) and type(meta['frame_index']) is int and meta['frame_index']==index,'request original identity/frame binding invalid')
            need(meta['payload_sha256']==hashlib.sha256(request[16+ml:]).hexdigest(),'request payload hash invalid')
            need((index==1 and pl==354 and meta['payload_sha256']=='9c9200453ca7feab036ee9e41b9b78f9b61df5d672792961379d5daa920d1eb8') or (index==2 and pl==0),'only original typed FORCE diagnostic and empty END supported')
            need(self.total_input+len(request)<=32768,'cumulative input budget exceeded')
            if index==1:
                self.feedback_started_ns=self.owner._time()
                self.deadline=self.feedback_started_ns+100_000_000
                need(self.deadline<self.owner_deadline,'original lifetime must contain whole 100ms session window')
                self.first_identity=value
            else:
                frozen=dict(value); frozen['invocation_id']=1
                need(typed_equal(frozen,self.first_identity),'all original frozen identity fields must remain unchanged')
            self.inspections.append(_prove_original(self.owner,self))
            if index==1:
                self.owner.prepare_invocation(ident,request_raw=request,journal_name='c22-invocation-01.jsonl',max_output_bytes=6160,max_reads=32,read_size=6160,io_deadline_ns=self.owner_deadline)
                self.records.append(self.owner._invocation); self.state='OBSERVING'
                _dispatch_serial(self.owner,self,1)
            else:
                _prepare_second(self.owner,self,ident,request)
                self.state='ENDING'; _dispatch_serial(self.owner,self,2)
            self.total_input+=len(request)
            raw,payload,snap=self._receive(request)
            verdict=verify_result(payload,self.expected_result,self.oracle) if index==1 else verify_ended(payload,self.expected_end)
            completion=dict(kind='root_frame_validation',invocation_id=index,request_sha256=hashlib.sha256(request).hexdigest(),response_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=hashlib.sha256(payload).hexdigest(),
                dispatch_to_complete_bytes_interval_ns=[snap['dispatch']['raw_call_bracket_ns'][0],snap['reads'][-1]['result_observation_bracket_ns'][1]],
                model_clock_not_reported=True,authority_completion_created=False,verdict=verdict)
            self.owner._invocation._append(completion)
            self.owner._invocation.close_journal()
            self.total_output+=len(raw); self.total_reads+=len(snap['reads'])
            self.results.append(dict(identity=value,request_raw_hex=request.hex(),response_raw_hex=raw.hex(),payload_raw_hex=payload.hex(),transcript=snap,validation=completion))
            self._continuity()  # Parsing/fsync cannot silently cross the feedback deadline.
            self.state='RESULT_VERIFIED' if index==1 else 'ENDED'
            return self.results[-1]
        except BaseException:
            self.state='FAILED'
            try: self.owner.close('new serial C22 session rejected; no retry')
            except BaseException: pass  # Owner retains original/quarantined resources and errors.
            raise
