import unittest
from competition.deepeye.simulation.isolation import actor_invocation_series as s
from competition.deepeye.tests.isolation import test_serial_invocation_series as fixture

class ResponsePairTests(unittest.TestCase):
    def test_pair_mode_fragmented(self):
        wire=fixture.frame(b"ready")+fixture.frame(b"result")
        req,snap=fixture.observation([wire[:2],wire[2:9],wire[9:]])
        self.assertEqual((fixture.frame(b"ready"),fixture.frame(b"result")),s._raw_pair_from_snapshot(snap,req))

    def test_pair_boundaries_and_exact_framing(self):
        good=fixture.frame(b'a'*2048)+fixture.frame(b'b'*16384)
        for chunks in ([good[i:i+8192] for i in range(0,len(good),8192)], [fixture.frame(b'a')+fixture.frame(b'b')]):
            req,snap=fixture.observation(chunks)
            self.assertEqual(b''.join(s._raw_pair_from_snapshot(snap,req)),b''.join(chunks))
        for wire in (fixture.frame(b'a'),fixture.frame(b'')+fixture.frame(b'x'),fixture.frame(b'a'*2049)+fixture.frame(b'x'),fixture.frame(b'a')+fixture.frame(b'b'*16385),fixture.frame(b'a')+fixture.frame(b'b')+b'x',fixture.frame(b'a')+fixture.frame(b'b')+fixture.frame(b'c'),fixture.frame(b'a')+fixture.frame(b'b')[:-1]):
            req,snap=fixture.observation([wire[i:i+8192] for i in range(0,len(wire),8192)])
            with self.assertRaises(ValueError): s._raw_pair_from_snapshot(snap,req)

    def test_invalid_io_cannot_seal(self):
        import copy
        req,base=fixture.observation([fixture.frame(b'a')+fixture.frame(b'b')])
        for key,value in [('pending',True),('os_result_observed',False),('cancel_attempted',True),('unknown_consumption',True),('stream_start',1)]:
            snap=copy.deepcopy(base);snap['reads'][0][key]=value
            with self.assertRaises(ValueError): s._raw_pair_from_snapshot(snap,req)
        base['eof']=True
        with self.assertRaises(ValueError):s._raw_pair_from_snapshot(base,req)

    def test_fixed_modes_and_budget_next(self):
        with self.assertRaises(ValueError):s.SerialInvocationLimits(2,100,100,5,'other')
        self.assertEqual('single_frame_v1',s.SerialInvocationLimits(2,100,100,5).response_mode)
        l=s._SerialLedger(s.SerialInvocationLimits(2,100,100,5,'ready_result_frames_v1'))
        def reserve(n):return l.reserve(fixture.identity(n),request_raw=fixture.frame(b'{}'),journal_name=f'n{n}',max_output_bytes=40,max_reads=2,read_size=16,io_deadline_ns=1000)
        a=reserve(1);l.claim_write(a);wire=fixture.frame(b'a')+fixture.frame(b'b');l.seal(a,wire)
        self.assertEqual((fixture.frame(b'a'),fixture.frame(b'b')),a.sealed_pair)
        b=reserve(2);self.assertEqual(len(wire),b.stream_start)
        with self.assertRaises(ValueError):l.claim_write(a)
        l=s._SerialLedger(s.SerialInvocationLimits(2,100,50,5,'ready_result_frames_v1'))
        a=l.reserve(fixture.identity(1),request_raw=fixture.frame(b'{}'),journal_name='a',max_output_bytes=40,max_reads=2,read_size=16,io_deadline_ns=1000);l.claim_write(a);l.seal(a,wire)
        with self.assertRaises(ValueError):l.reserve(fixture.identity(2),request_raw=fixture.frame(b'{}'),journal_name='b',max_output_bytes=40,max_reads=2,read_size=16,io_deadline_ns=1000)

    def test_owner_mode_guards_and_original_journal(self):
        import threading,os,json
        from pathlib import Path
        from types import SimpleNamespace as NS
        from unittest.mock import patch
        from competition.deepeye.simulation.isolation.actor_owner import ActorOwner
        from competition.deepeye.simulation.isolation.actor_pipe_io import _ActorPipeIO
        root=Path(os.environ['SERIAL_CONTROL_EVIDENCE_DIR'])/'pair';root.mkdir()
        owner=object.__new__(ActorOwner);owner._thread=threading.get_ident();owner._foreign_call=threading.Event();owner._busy=False;owner._epoch=0;owner._state='RUNNING_UNBOUND';owner._registry=NS(_contains=lambda item:item is owner,_clock_binding=None);owner._policy=NS(run_id='software-run');owner._instance='software-actor';owner._root=root;owner._acl_ready=True;owner._cleanup_attempted=False;owner._invocation=owner._invocation_series=None;owner._invocation_claimed=False;owner._run_deadline=owner._ready_deadline=10000;owner._primary_error=owner._cleanup_error=None
        io=object.__new__(_ActorPipeIO);owner._pending_io=io;io.actor=owner;io.operations=[];io.write_reserved=False;io.teardown_started=io.quarantined=io.cleanup_consumed=False;io.endpoints={'input_write':(NS(native=11),),'output_read':(NS(native=12),)};io.continuity=lambda:None
        wire=fixture.frame(b'ready')+fixture.frame(b'result'); chunks=[wire[:3],wire[3:10],wire[10:]]; now=[100]
        def clock(_):now[0]+=1;return now[0]
        def operation(endpoint,kind,size,raw=None):
            op=NS(kind=kind,size=size,raw=raw,record=None,row=None,issued=False,issue_returned=False,settled=False,unknown=False,cancel_attempted=False,count=None,error=None,data=None,result_bool=False,accounted=False)
            op.diagnostic=lambda:dict(issued=op.issued,pending=op.issued and not op.settled,os_result_observed=op.settled,winerror=op.error,cancel_attempted=op.cancel_attempted,unknown_consumption=op.unknown)
            io.operations.append(op);return op
        def issue(op):
            op.issued=op.issue_returned=op.settled=op.result_bool=True;op.error=0
            if op.kind=='write':op.count=len(op.raw)
            else:op.data=chunks.pop(0);op.count=len(op.data)
        io.operation=operation;io.issue=issue;io.observe=lambda op:None
        with patch.object(ActorOwner,'_invocation_check',clock),patch.object(ActorOwner,'_report',lambda self:None):
            owner.begin_serial_invocations(s.SerialInvocationLimits(2,100,100,8,'ready_result_frames_v1'))
            owner.prepare_invocation(fixture.identity(),request_raw=fixture.frame(b'{}'),journal_name='pair.jsonl',max_output_bytes=50,max_reads=4,read_size=16,io_deadline_ns=1000)
            owner.dispatch_invocation_once()
            for _ in range(3):owner.read_invocation_once()
            with self.assertRaises(ValueError):owner.seal_serial_invocation_frame.__wrapped__(owner)
            result=owner.seal_serial_invocation_response_pair();self.assertEqual(wire.hex(),result['raw_wire_hex']);self.assertFalse(result['completion_verified']);self.assertFalse(result['authenticated']);self.assertEqual(2,len(result['raw_frames_hex']))
            self.assertEqual(result['response_observed_qpc_ns'],owner._invocation_series.ledger.tickets[0].observed_qpc_ns)
            self.assertTrue(owner._invocation._close_attempted); self.assertTrue(owner._invocation_series.summary()['invocations'][0]['raw_pair_sealed'])
        self.assertIn(b'original_serial_response_pair_observed',(root/'pair.jsonl').read_bytes())
        self.assertEqual(3,len(owner._invocation.reads))
        fake=NS(_invocation_series=NS(seal_current=lambda mode='single_frame_v1': (_ for _ in ()).throw(ValueError('mode'))),_invocation_check=lambda:None)
        with self.assertRaises(ValueError):ActorOwner.seal_serial_invocation_response_pair.__wrapped__(fake)
