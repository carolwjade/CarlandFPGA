"""NEW bounded serial transport controls; no native/model/board execution."""
import copy
import importlib
from dataclasses import replace
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from pathlib import Path
import os
import tempfile
import shutil
import threading
from competition.deepeye.integration.cpu_invocation_transcript import InvocationIdentity

try:
    serial = importlib.import_module('competition.deepeye.simulation.isolation.actor_invocation_series')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.isolation.actor_invocation_series': raise
    serial = None


def identity(n=1):
    return InvocationIdentity('new-serial-control', 'a'*64, 'b'*40, 'c'*64,
                              'software-run', n, 'software-actor')


def frame(payload): return len(payload).to_bytes(4, 'little')+payload


def observation(chunks):
    request = frame(b'{"invocation":1}')
    rows=[];offset=0
    for i,chunk in enumerate(chunks):
        rows.append(dict(issued=True, pending=False, os_result_observed=True, winerror=0,
            cancel_attempted=False, unknown_consumption=False, raw_hex=chunk.hex(),
            returned_bytes=len(chunk), stream_start=offset, stream_end=offset+len(chunk),
            raw_call_bracket_ns=[20+i*2,21+i*2]))
        offset+=len(chunk)
    return request,dict(schema=2,failed=False,journal_failed=False,eof=False,
        zero_read_stop=False,unknown_consumption=False,bytes_read=offset,
        dispatch=dict(issued=True,pending=False,os_result_observed=True,winerror=0,
            cancel_attempted=False,unknown_consumption=False,bytes_written=len(request),
            requested_bytes=len(request),raw_hex=request.hex(),raw_call_bracket_ns=[10,11]),
        reads=rows)


class SerialInvocationControls(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(serial, 'explicit bounded serial invocation support is missing')

    def test_fragmented_frame_closes_without_inventing_completion(self):
        wire=frame(b'{"status":"STOP"}')
        request,snap=observation([wire[:2],wire[2:7],wire[7:]])
        self.assertEqual(wire,serial._raw_frame_from_snapshot(snap,request))
        self.assertNotIn('completion_verified',snap)

    def test_partial_extra_and_multiple_frames_refuse(self):
        for wire in (b'\x03',frame(b'abc')[:-1],frame(b'abc')+b'x',frame(b'a')+frame(b'b')):
            with self.subTest(wire=wire):
                request,snap=observation([wire])
                with self.assertRaises(ValueError):serial._raw_frame_from_snapshot(snap,request)

    def test_pending_cancel_eof_and_offset_contradictions_refuse(self):
        request,base=observation([frame(b'abc')])
        for key,value in [('pending',True),('os_result_observed',False),('cancel_attempted',True),
                          ('unknown_consumption',True),('winerror',995),('stream_start',1)]:
            snap=copy.deepcopy(base);snap['reads'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                serial._raw_frame_from_snapshot(snap,request)
        snap=copy.deepcopy(base);snap['eof']=True
        with self.assertRaises(ValueError):serial._raw_frame_from_snapshot(snap,request)

    def ledger(self,**overrides):
        options=dict(max_invocations=2,max_total_request_bytes=128,
            max_total_output_bytes=128,max_total_reads=8)
        options.update(overrides)
        return serial._SerialLedger(serial.SerialInvocationLimits(**options))

    def reserve(self,ledger,n=1,**overrides):
        options=dict(request_raw=frame(b'{}'),journal_name=f'new-{n}.jsonl',
                     max_output_bytes=32,max_reads=2,read_size=16,io_deadline_ns=1000)
        options.update(overrides)
        return ledger.reserve(identity(n),**options)

    def test_two_frames_keep_distinct_tickets_and_original_labels(self):
        ledger=self.ledger();one=self.reserve(ledger)
        ledger.claim_write(one);ledger.seal(one,frame(b'{"id":1}'))
        two=self.reserve(ledger,2);ledger.claim_write(two);ledger.seal(two,frame(b'{"id":2}'))
        self.assertIsNot(one,two);self.assertEqual(2,len(ledger.tickets))
        self.assertTrue(one.write_reserved);self.assertTrue(two.write_reserved)
        self.assertEqual(frame(b'{"id":1}'),one.sealed_frame)
        with self.assertRaises(ValueError):self.reserve(ledger,3)

    def test_unsealed_predecessor_and_duplicate_write_cannot_advance(self):
        ledger=self.ledger();one=self.reserve(ledger);ledger.claim_write(one)
        with self.assertRaises(ValueError):self.reserve(ledger,2)
        ledger=self.ledger();one=self.reserve(ledger);ledger.claim_write(one)
        with self.assertRaises(ValueError):ledger.claim_write(one)

    def test_global_budgets_are_reserved_before_next_request(self):
        ledger=self.ledger(max_total_output_bytes=48)
        one=self.reserve(ledger);ledger.claim_write(one);ledger.seal(one,frame(b'a'))
        with self.assertRaises(ValueError):self.reserve(ledger,2)
        self.assertEqual(1,len(ledger.tickets))

    def test_request_prefix_counts_toward_original_16384_limit(self):
        ledger=self.ledger(max_total_request_bytes=32768)
        self.reserve(ledger,request_raw=frame(b'x'*16380))
        ledger=self.ledger(max_total_request_bytes=32768)
        with self.assertRaises(ValueError):self.reserve(ledger,request_raw=frame(b'x'*16381))

    def test_changed_package_or_reused_journal_does_not_join_series(self):
        for wrong in ('package','journal'):
            ledger=self.ledger();one=self.reserve(ledger);ledger.claim_write(one);ledger.seal(one,frame(b'a'))
            with self.assertRaises(ValueError):
                if wrong=='journal':self.reserve(ledger,2,journal_name='new-1.jsonl')
                else:
                    ledger.reserve(replace(identity(2),package_manifest_sha256='d'*64),
                        request_raw=frame(b'{}'),journal_name='new-2.jsonl',max_output_bytes=32,
                        max_reads=2,read_size=16,io_deadline_ns=1000)

    def test_legacy_once_claim_is_not_reset_and_series_cannot_adopt_plain_owner(self):
        from competition.deepeye.simulation.isolation.actor_owner import ActorOwner
        owner=object.__new__(ActorOwner)
        owner._invocation_claimed=True;owner._invocation_series=None
        options=dict(request_raw=frame(b'{}'),journal_name='new.jsonl',max_output_bytes=32,
                     max_reads=2,read_size=16,io_deadline_ns=1000)
        # Only the refusal prefixes of these undecorated methods are exercised;
        # this specimen has no registry or native handle and grants nothing.
        with self.assertRaises(ValueError):ActorOwner.prepare_invocation.__wrapped__(owner,identity(),**options)
        with self.assertRaises(ValueError):ActorOwner.prepare_next_invocation.__wrapped__(owner,identity(2),**options)
        self.assertTrue(owner._invocation_claimed)
        with self.assertRaises(ValueError):
            serial._new_original_series(NS(),serial.SerialInvocationLimits(2,128,128,8))

    def test_settled_old_operation_stays_bound_to_its_original_record(self):
        from competition.deepeye.simulation.isolation.actor_pipe_io import _ActorPipeIO
        old=NS(_bytes=5,_unknown_consumption=False,_zero_read_stop=False,_eof=False)
        current=NS(_bytes=0,_unknown_consumption=False)
        io=object.__new__(_ActorPipeIO);io.actor=NS(_invocation=current,_invocation_series=object())
        op=NS(record=old,row={},kind='read',settled=True,accounted=False,count=3,
              data=b'abc',unknown=False,issued=True,error=0,diagnostic=lambda:{})
        io.account(op,journal=False)
        self.assertEqual(8,old._bytes);self.assertEqual(0,current._bytes)
        self.assertEqual(8,op.row['stream_end']);self.assertTrue(op.accounted)

    def test_two_owned_api_calls_keep_real_journals_under_explicit_fake_native_boundary(self):
        from competition.deepeye.simulation.isolation.actor_owner import ActorOwner
        from competition.deepeye.simulation.isolation.actor_pipe_io import _ActorPipeIO
        parent=os.environ.get('SERIAL_CONTROL_EVIDENCE_DIR')
        if parent:
            root=Path(parent).resolve()/self._testMethodName;root.mkdir(parents=True)
        else:
            temp_parent=Path(tempfile.gettempdir()).resolve()
            root=Path(tempfile.mkdtemp(prefix='deepeye-serial105-',dir=temp_parent)).resolve()
            def clean():
                if root.parent != temp_parent or not root.name.startswith('deepeye-serial105-'):
                    raise AssertionError('temporary cleanup target escaped its intended directory')
                shutil.rmtree(root)
            self.addCleanup(clean)
        owner=object.__new__(ActorOwner)
        owner._thread=threading.get_ident();owner._foreign_call=threading.Event()
        owner._busy=False;owner._epoch=0;owner._state='RUNNING_UNBOUND'
        owner._registry=NS(_contains=lambda item:item is owner,_clock_binding=None)
        owner._policy=NS(run_id='software-run');owner._instance='software-actor'
        owner._root=root;owner._acl_ready=True;owner._cleanup_attempted=False
        owner._invocation=owner._invocation_series=None;owner._invocation_claimed=False
        owner._run_deadline=owner._ready_deadline=10000
        owner._primary_error=owner._cleanup_error=None
        io=object.__new__(_ActorPipeIO);owner._pending_io=io
        io.actor=owner;io.operations=[];io.write_reserved=False
        io.teardown_started=io.quarantined=io.cleanup_consumed=False
        io.endpoints={'input_write':(NS(native=11),),'output_read':(NS(native=12),)}
        io.continuity=lambda:None
        now=[100];writes=[];outputs=[frame(b'{"id":1}'),frame(b'{"id":2}')]
        def clock(_owner):
            now[0]+=1
            if _owner._invocation is not None and now[0]>=_owner._invocation.deadline:
                raise ValueError('software invocation expired')
            return now[0]
        def operation(endpoint,kind,size,raw=None):
            op=NS(kind=kind,size=size,raw=raw,record=None,row=None,issued=False,
                issue_returned=False,settled=False,unknown=False,cancel_attempted=False,
                count=None,error=None,data=None,result_bool=False,accounted=False)
            op.diagnostic=lambda:dict(issued=op.issued,pending=op.issued and not op.settled,
                os_result_observed=op.settled,winerror=op.error,
                cancel_attempted=op.cancel_attempted,unknown_consumption=op.unknown)
            io.operations.append(op);return op
        def issue(op):
            op.issued=op.issue_returned=op.settled=op.result_bool=True;op.error=0
            if op.kind=='write':writes.append(op.raw);op.count=len(op.raw)
            else:op.data=outputs.pop(0);op.count=len(op.data)
        io.operation=operation;io.issue=issue;io.observe=lambda op:None
        # These replacements are explicit software boundaries, not a real
        # registry, QPC, model-ready event, original process or motion grant.
        with patch.object(ActorOwner,'_invocation_check',clock),patch.object(ActorOwner,'_report',lambda self:None):
            owner.begin_serial_invocations(serial.SerialInvocationLimits(2,128,128,8))
            old=None
            for n in (1,2):
                options=dict(request_raw=frame(str(n).encode()),journal_name=f'owned-{n}.jsonl',
                    max_output_bytes=32,max_reads=2,read_size=16,io_deadline_ns=1000)
                if n==1:owner.prepare_invocation(identity(n),**options)
                else:owner.prepare_next_invocation(identity(n),**options)
                owner.dispatch_invocation_once();owner.read_invocation_once()
                observed=owner.seal_serial_invocation_frame()
                self.assertFalse(observed['completion_verified']);self.assertFalse(observed['authenticated'])
                self.assertEqual(frame(f'{{"id":{n}}}'.encode()).hex(),observed['raw_frame_hex'])
                if old is None:old=owner._invocation
            self.assertIsNot(old,owner._invocation)
            self.assertEqual(12,old._bytes);self.assertEqual(12,owner._invocation._bytes)
            self.assertTrue(old._close_attempted);self.assertTrue(owner._invocation._close_attempted)
            self.assertTrue(owner._invocation_claimed);self.assertTrue(io.write_reserved)
            self.assertEqual([frame(b'1'),frame(b'2')],writes)
            self.assertEqual(2,len(owner._invocation_series.ledger.tickets))
        for n in (1,2):
            self.assertIn(b'original_serial_frame_observed',(root/f'owned-{n}.jsonl').read_bytes())


if __name__=='__main__':unittest.main()
