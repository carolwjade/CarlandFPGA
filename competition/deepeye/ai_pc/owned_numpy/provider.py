"""Callable one-use fixed FORCE diagnostic; this supplies no production channel.
One ActorRegistry and one original launch_overlapped own the whole lifecycle.
No BOOT, motion authority, service loop, caller callback or source override.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from .closure import preflight,need,pin,write_new,copy_rows,CONTRACT,WORK,OneUseLifecycle,repository_root,ordinary_directory,require_private_origins
_RETAINED=[]
def wait_with_startup_diagnostic(owner,evidence):
    # Observational peek only: it does not consume pipe bytes or create a C22
    # completion. No output is legal before READY in this fixed child.
    import ctypes as C
    from ctypes import wintypes as W
    from serial_session import _poll_original_ready
    k=C.WinDLL('kernel32',use_last_error=True)
    peek=k.PeekNamedPipe;peek.argtypes=[W.HANDLE,C.c_void_p,W.DWORD,C.POINTER(W.DWORD),C.POINTER(W.DWORD),C.POINTER(W.DWORD)];peek.restype=W.BOOL
    handle=owner._resources.find('output_read').native
    for _ in range(40001):
        buffer=C.create_string_buffer(2048);count=W.DWORD();available=W.DWORD()
        ok=peek(handle,buffer,len(buffer),C.byref(count),C.byref(available),None)
        if ok and count.value:
            raw=buffer.raw[:count.value]
            with (evidence/'preREADY-child-diagnostic.raw').open('xb') as f:
                need(f.write(raw)==len(raw),'short diagnostic evidence write');f.flush();os.fsync(f.fileno())
            write_new(evidence/'preREADY-child-diagnostic.json',dict(bytes=len(raw),available_bytes=int(available.value),nonconsuming_original_handle_query=True,scope='failure diagnostic only; not an authenticated response or observation'))
            raise ValueError('child emitted failure diagnostic before READY; original raw bytes retained')
        if not ok and C.get_last_error() not in (109,232):raise C.WinError(C.get_last_error(),'original startup diagnostic PeekNamedPipe')
        proof=_poll_original_ready(owner,owner._model_ready_reference)
        if proof is not None:return proof
        time.sleep(.001)
    raise ValueError('fixed original READY poll limit')

class OwnedNumpyQualification:
    """A consumed object cannot launch again, including after preflight failure."""
    def __init__(self):
        self._lifecycle=OneUseLifecycle()

    def run(self,config_path,config_sha256):
        self._lifecycle.claim_start()
        release,plan,runtime,child_rows=preflight(config_path,config_sha256)
        need(os.name=='nt' and sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode is True,'Windows -I -S -B required')
        need(Path(sys.executable).resolve()==Path(release['runtime_root'])/'runtime/python.exe','fixed external pinned host Python required')
        return _execute(release,plan,runtime,child_rows,config_sha256,self._lifecycle)

def _execute(release,plan,runtime,child_rows,config_sha256,lifecycle):
    FINAL=Path(release['final_dir'])
    args=argparse.Namespace(release_sha256=config_sha256)
    # Exclusive target and permanent launch slot BEFORE copies/product imports/acquisition.
    # Any failure after this point remains consumed; never resume this target.
    FINAL.mkdir(exist_ok=False)
    operation_slot=Path(release['runtime_root'])/'operation-slots'/release['operation_id']
    operation_slot.parent.mkdir(exist_ok=True)
    ordinary_directory(operation_slot.parent)
    operation_slot.mkdir(exist_ok=False)
    write_new(FINAL/'launch-slot.json',dict(work_id=WORK,root_release_sha256=args.release_sha256,
        source_plan_sha256=release['source_plan_sha256'],runtime_closure_sha256=release['runtime_closure_sha256'],
        outer_config_raw_sha256=pin(release['outer_config_path'])['sha256'],status='started_unknown',max_new_actors=1,max_invocations=2,replay_allowed=False))
    host=FINAL/'host';child=Path(release['runtime_root']);evidence=FINAL/'evidence'
    host.mkdir();evidence.mkdir()
    copy_rows(plan['host_files'],host)
    layout=dict(schema=1,requirements_sha256=CONTRACT,runtime_closure_sha256=release['runtime_closure_sha256'],numpy_version='2.5.4',
        files=[{name:row[name] for name in ('path','bytes','sha256')} for row in child_rows])
    cache_layout_raw=(child/'child-layout.json').read_bytes()
    need(len(cache_layout_raw)<=2*1024*1024 and json.loads(cache_layout_raw)==layout,'direct source layout must equal fixed child file list; original owner makes the only private copy')
    child_files=[(row['path'],row['sha256']) for row in child_rows]+[('child-layout.json',pin(child/'child-layout.json')['sha256'])]
    need(sum(row['bytes'] for row in child_rows)+pin(child/'child-layout.json')['bytes']<=268435456,'layout-inclusive retained stage cap exceeded')
    for row in plan['host_files']: need(pin(host/row['path'])=={'bytes':row['bytes'],'sha256':row['sha256']},'host stage final mismatch')
    sys.path[:0]=[str(host),str(repository_root()),str(host/'deps')]
    require_private_origins(host)
    # All native/product imports are deliberately below exact release, closure,
    # review, fresh target and irreversible one-new-launch reservation gates.
    from competition.deepeye.simulation.isolation import actor_owner,win32
    from competition.deepeye.integration.cpu_invocation_transcript import InvocationIdentity
    from competition.deepeye.integration.host_clock import qpc_clock_for_new_run
    from serial_session import RootSerialSession,wait_original_model_ready
    from framing_contract import encode_request
    import native_readback
    require_private_origins(host,all_loaded=True)
    need(Path(actor_owner.__file__).resolve()==repository_root()/'competition/deepeye/simulation/isolation/actor_owner.py','new private owner only')
    need(Path(win32.__file__).resolve()==repository_root()/'competition/deepeye/simulation/isolation/win32.py','new fixed Win32 copy only')
    need('torch' not in sys.modules and 'ai_pc.cpu_package.numpy_stream_core' not in sys.modules,'host never imports/executes model')
    for name,module in list(sys.modules.items()):
        if name=='competition' or name.startswith('competition.') or name.split('.')[0] in plan['external_top_levels']:
            file=getattr(module,'__file__',None)
            if file: need(Path(file).resolve().is_relative_to(repository_root() if name=='competition' or name.startswith('competition.') else host/'deps'),'product/dependency origin outside fixed closed source')
            else: need(all(Path(item).resolve().is_relative_to(repository_root()) for item in module.__path__),'host namespace outside fixed product root')
    clock=qpc_clock_for_new_run(); registry=actor=session=query=None; primary=None; snapshots=[]; close_started=False
    _RETAINED.append(registry)
    began=time.perf_counter_ns(); stop_bracket=None; terminal_observed_ns=None
    job_before=job_after=query_close=None
    def snapshot(label):
        io=actor._pending_io
        item=dict(label=label,host_qpc_ns=clock(),clock=dict(clock.metadata),state=actor.state,instance_id=actor.instance_id,
            original_process_native=actor._original_native,creation_filetime=getattr(actor,'_creation_filetime',None),
            original_model_ready_native=actor._model_ready_native,original_model_ready_launch_readback=actor._model_ready_launch_readback,
            resources=actor._resources.summary(),stop_claim=asdict(io.stop_claim),operations=[op.diagnostic() for op in io.operations],
            all_settled=io.all_settled,cleanup_consumed=io.cleanup_consumed,quarantined=io.quarantined,
            private_acquisitions=io.private_acquisition_diagnostics(),invocation=actor.invocation_snapshot())
        snapshots.append(item);write_new(evidence/('%02d-%s.json'%(len(snapshots),label)),item)
    try:
        registry=actor_owner.ActorRegistry(host_clock=clock);_RETAINED.append(registry)
        policy=actor_owner.ActorPolicy(run_id=release['run_id'],evidence_parent=evidence,source_root=child,
            files=tuple(child_files),executable='runtime/python.exe',
            arguments=('-I','-S','-B','-X','utf8','endpoint_handles.py',pin(child/'child-layout.json')['sha256']),
            system_root=release['system_root'],local_appdata=release['local_appdata'],max_stage_bytes=268435456,output_limit=8192,
            readiness_timeout_ns=40_000_000_000,lifetime_timeout_ns=45_000_000_000,sample_age_cap_ns=4_000_000_000,max_probe_ns=2_000_000_000)
        write_new(evidence/'policy.json',{**asdict(policy),'evidence_parent':str(policy.evidence_parent),'source_root':str(policy.source_root)})
        actor=registry.launch_overlapped(policy)  # Sole new native actor acquisition.
        need(len(registry._owners)==1 and registry._owners[0] is actor,'one original registry acquisition required')
        snapshot('original-acquired')
        query=native_readback.OriginalJobQuery(actor._resources.find('job').native);_RETAINED.append(query)
        before=query.snapshot();job_before=before;write_new(evidence/'original-job-before.json',before)
        need(type(before['accounting']['ActiveProcesses']) is int and before['accounting']['ActiveProcesses']==1,'one original Job process required')
        ready=wait_with_startup_diagnostic(actor,evidence)  # Real original inherited event, finite, no fake BOOT.
        write_new(evidence/'original-model-ready.json',dict(original_event_native=ready.event,original_process_native=ready.native,creation_filetime=ready.creation,
            original_event_wait_bracket_ns=ready.interval,original_event_wait_result=ready.wait_result,readback=ready.readback,scope='fixed real core loaded/eval; no forward, BOOT, source freshness or motion authority'))
        snapshot('real-model-ready')
        lifecycle.mark_ready()
        fixture=Path(plan['diagnostic']['fixture_path']).read_bytes()
        need(len(fixture)==354 and hashlib.sha256(fixture).hexdigest()=='9c9200453ca7feab036ee9e41b9b78f9b61df5d672792961379d5daa920d1eb8','original typed FORCE input only')
        intent=dict(work_id=WORK,run_id=release['run_id'],operation_id=release['operation_id'],requirements_sha256=CONTRACT,
            source_plan_sha256=release['source_plan_sha256'],runtime_closure_sha256=release['runtime_closure_sha256'],published_head=plan['published_head'],C_source_commit=plan['C_source_commit'],
            fixture_sha256=hashlib.sha256(fixture).hexdigest(),model_manifest_sha256=plan['diagnostic']['model_manifest_sha256'],
            interaction='OBSERVE1->actual RESULT1 verified->END2->actual ENDED2',source_fixture_live=False,movement_authorized=False)
        intent_raw=(json.dumps(intent,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
        with (evidence/'invocation-intent.raw').open('xb') as stream: need(stream.write(intent_raw)==len(intent_raw),'short intent evidence write');stream.flush();os.fsync(stream.fileno())
        request_hash=hashlib.sha256(intent_raw).hexdigest()
        session=RootSerialSession(actor,readiness=ready,
            expected_result_raw=Path(plan['diagnostic']['expected_result_path']).read_bytes(),oracle_raw=Path(plan['diagnostic']['oracle_path']).read_bytes(),expected_end_raw=Path(plan['diagnostic']['expected_end_path']).read_bytes())
        _RETAINED.append(session)
        for index,payload in ((1,fixture),(2,b'')):
            lifecycle.claim_observe() if index==1 else lifecycle.claim_end()
            ident=InvocationIdentity(operation_id=release['operation_id'],request_hash=request_hash,tested_commit=plan['published_head'],package_manifest_sha256=release['source_plan_sha256'],run_id=release['run_id'],invocation_id=index,actor_instance_id=actor.instance_id)
            raw=encode_request(asdict(ident),index,payload,kind=index)
            actual=session.invoke(ident,raw)  # Second call cannot occur before real verified first response.
            lifecycle.mark_result() if index==1 else lifecycle.mark_ended()
            write_new(evidence/('actual-invocation-%02d.json'%index),actual)
        need(session.state=='ENDED' and len(session.results)==2 and len(session.records)==2,'actual bounded serial pair required')
        need(clock()<session.deadline,'whole serial feedback window exceeded fixed 100ms')
        snapshot('complete-original-serial-responses')
    except BaseException as error:
        primary={'type':type(error).__name__,'message':str(error)}
        if actor is None and registry is not None and len(registry._owners)==1: actor=registry._owners[0]
    finally:
        if actor is not None:
            try:
                if not actor._cleanup_attempted:
                    close_started=True;stop_bracket=[clock(),None]
                    actor.close('new serial C22 diagnostic terminal/failure; no retry')
                    stop_bracket[1]=clock()
                for _ in range(10001):
                    if actor.state in ('CLOSED','QUARANTINED'): break
                    if time.perf_counter_ns()-began>=55_000_000_000: break
                    actor.poll_teardown();time.sleep(.001)
                terminal_observed_ns=clock()
                snapshot('original-terminal-owner')
                need(actor.state=='CLOSED' and actor._cleanup_result is not None and actor._cleanup_result.resources_complete is True and actor._cleanup_result.evidence_complete is True,'original owner STOP/reap/Close not proved complete')
                io=actor._pending_io
                need(io.all_settled and io.cleanup_consumed and io.stop_claim.terminal is True and type(io.stop_claim.wait_result) is int and io.stop_claim.wait_result==0 and type(io.stop_claim.exit_code) is int,'actual same-original terminal Wait/exit and settled IO required')
            except BaseException as error:
                cleanup={'type':type(error).__name__,'message':str(error)}
                if primary is None: primary={'stage':'original_teardown','error':cleanup}
                else: primary['teardown_error']=cleanup
        if query is not None:
            try:
                after=query.snapshot();job_after=after;write_new(evidence/'original-job-after.json',after)
                need(type(after['accounting']['ActiveProcesses']) is int and after['accounting']['ActiveProcesses']==0,'original Job not proved empty')
                query_close=query.close_after_empty();write_new(evidence/'original-query-close.json',query_close)
            except BaseException as error:
                if primary is None: primary={'stage':'original_job_or_query','type':type(error).__name__,'message':str(error)}
                else: primary['job_or_query_error']={'type':type(error).__name__,'message':str(error)}
        final_clock=clock()
        result=dict(schema=1,work_id=WORK,requirements_sha256=CONTRACT,
            status='new_C22_serial_diagnostic_passed' if primary is None and session is not None and session.state=='ENDED' else 'failed_or_unknown_preserved',primary_error=primary,
            root_release_sha256=args.release_sha256,source_plan_sha256=release['source_plan_sha256'],runtime_closure_sha256=release['runtime_closure_sha256'],outer_config_raw_sha256=pin(release['outer_config_path'])['sha256'],
            actor_created_original=actor is not None and actor._pending_io.process_state=='ACQUIRED',
            source_fixture_live=False,model_forward_calls_expected=1,actual_serial_results=0 if session is None else len(session.results),
            session_state=None if session is None else session.state,feedback_started_ns=None if session is None else session.feedback_started_ns,
            feedback_deadline_ns=None if session is None else session.deadline,final_after_cleanup_qpc_ns=final_clock,
            feedback_window_includes_new_session_overhead=True,cleanup_interval_separate_from_feedback=True,
            feedback_last_complete_byte_observation_ns=None if session is None or not session.results else session.results[-1]['validation']['dispatch_to_complete_bytes_interval_ns'][1],
            original_owner_close_call_bracket_ns=stop_bracket,original_terminal_owner_observed_ns=terminal_observed_ns,physical_stop_time_proven=False,
            authority_completion_created=False,BOOT_created=False,movement_authorized=False,formal_H12='not_run',digital_twin_error_lt_1_percent='not_proven',whole_call_hard_realtime='not_proven',
            actual_actor_cleanup_complete=actor is not None and actor.state=='CLOSED',outer_original_supervisor_receipt='requires independent original raw receipt/Wait/exit/Job0/Close readback')
        write_new(FINAL/'result.json',result)
    records=[] if session is None else list(session.results)
    return dict(result=result, actual_responses=records,
        raw_responses=tuple(bytes.fromhex(record['response_raw_hex']) for record in records),
        transcripts=tuple(record['transcript'] for record in records),original_owner_snapshots=snapshots,
        cleanup_report=dict(original_owner=None if actor is None or actor._cleanup_result is None else asdict(actor._cleanup_result),
            original_job_before=job_before,original_job_after=job_after,original_job_query_close=query_close,
            owner_close_interval_ns=stop_bracket,terminal_observed_ns=terminal_observed_ns),evidence_dir=str(evidence))
