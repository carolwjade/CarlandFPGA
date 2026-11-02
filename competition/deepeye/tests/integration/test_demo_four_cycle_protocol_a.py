"""New SYNTHETIC_TEST protocol controls; no SSH/native/vendor/board authority.

The real G05 port, issuer and session execute against an explicit in-memory
register fixture. Every modeled MMIO call still uses the original disk ledger.
The fixture clock is virtual; these controls do not qualify board timing.
"""
import importlib
import os
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_board_a as b
from competition.deepeye.tools.diagnostic import functional50_g05_a as g
from competition.deepeye.tools.diagnostic import functional50_g05_transaction_a as tx
from competition.deepeye.tools.diagnostic import functional50_g05_session_a as session
from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as protocol
try:
    demo = importlib.import_module('competition.deepeye.tools.diagnostic.functional50_demo_four_cycle_profile_a')
except ModuleNotFoundError as exc:
    if not exc.name.endswith('functional50_demo_four_cycle_profile_a'): raise
    demo = None

IDENTITY = (1,0,0,0,0,0,0,0,2,0,0,0,7)

class MemoryMMIO:
    def __init__(self,device,polls):
        self.device=device; self.status=0; self.reg={}; self.controls=[]; self.calls=[]
        self.polls=polls; self.pending=0; self.status_reads=0; self.unknown=False
    def read(self,off):
        self.calls.append(('read',off))
        if self.unknown: raise OSError('SYNTHETIC_TEST unknown MMIO')
        if off==8:
            self.status_reads+=1
            if self.pending:
                self.pending-=1
                if not self.pending: self.status=0x11
            return self.status
        if off==0: return 0x47303550
        if off==4: return 2
        if off==0x10: return 0
        if off in (0x1c,0x300,0x304): return self.reg.get(0x214,0)
        if off==0x308: return self.reg.get(0x218,0)
        if off==0x378: return 7
        if off==0x37c: return 0x47303550
        return self.reg.get(off,0)
    def write(self,off,value):
        self.calls.append(('write',off)); self.reg[off]=value
        if off==0xc:
            self.controls.append(value)
            if value==1: self.status=1
            elif value==2:
                self.reg[0x14]=self.reg[0x214]; self.status=1
                self.pending=self.polls+1  # commit's own status + exact capture polls
            elif value==4: self.status=0x21
            elif value==5: self.status=1
            elif value==3: self.status=2

class FourCycleControls(unittest.TestCase):
    def setUp(self):
        self.virtual_ns=1_000_000
        def virtual_board_clock():
            self.virtual_ns+=1000
            return self.virtual_ns
        # Windows fsync latency is outside this pure protocol fixture's model.
        # Production clock comparisons remain active; expiry is tested below.
        self.enterContext(patch.object(session.time,'monotonic_ns',virtual_board_clock))
    def fixture(self,profile=None,polls=4):
        path=Path(tempfile.mkdtemp(prefix='SYNTHETIC_TEST_A380_'))
        device=object(); trace=object.__new__(b._TracePort)
        trace._pid=os.getpid(); trace._boot='boot'; trace._failed=False; trace._mmio=NS(device=device)
        reg=(device,None,None,(('operation_id','SYNTHETIC_TEST_A380'),),None,None,os.getpid(),trace._mmio,threading.get_ident())
        b._G05_LOADS[trace]=reg; b._G05_CLAIMED.add(trace)
        self.addCleanup(b._G05_LOADS.pop,trace,None); self.addCleanup(b._G05_CLAIMED.discard,trace)
        self.addCleanup(b._G05_PORTS.pop,trace,None)
        mmio=MemoryMMIO(device,polls)
        n=2 if profile is None else 4
        port=g.G05Port(g._KEY,trace,reg,mmio,path,dict(binding={},policy_sha256='a'*64,
            limits=dict(begin=1,commit=n,stop=1,latch=n,release=n,total_io=450)))
        b._G05_PORTS[trace]=port
        for off in (0,4,8,0x10): port.read32(off,'factory-'+str(off))
        issuer=tx.TransactionIssuer(trace,port,tx.Limits(n,64 if profile is None else 16,10_000_000_000))
        self.addCleanup(tx._ISSUERS.pop,port,None)
        gs=session.G05SessionV2(issuer,**({} if profile is None else dict(demo_cycle_profile=profile)))
        self.addCleanup(session._SESSIONS.pop,issuer,None)
        return gs,mmio
    def packet(self,state,kind,payload,ident):
        line=protocol.raw(dict(schema=protocol.SCHEMA,id=ident,operation_id='SYNTHETIC_TEST_A380',kind=kind,payload=payload))+b'\n'
        x=protocol.decode_request(line,'SYNTHETIC_TEST_A380',g,state);state.consume(x);return x
    def test_default_two_cycle_caps_remain_and_optin_is_explicit(self):
        state=protocol.Sequence()
        init=dict(identity_words=list(IDENTITY),max_commands=2,max_polls=64,duration_ns=10_000_000_000,max_io=450)
        self.packet(state,'init',init,'init')
        scan=dict(request_hex='00',source_hex='01',companions_hex=['02']*4,build_binding={},max_io=900)
        for i in range(2): self.packet(state,'trace_scan',scan,'scan'+str(i))
        with self.assertRaises(ValueError): self.packet(state,'trace_scan',scan,'scan3')
        with self.assertRaises(ValueError): self.packet(protocol.Sequence(),'init',dict(init,max_commands=4,max_polls=16),'four_without_selection')
        with patch.object(g,'Path',return_value=NS(read_text=lambda:'boot')):
            gs,mmio=self.fixture()
            gs.init(IDENTITY); gs.apply_one((0,0,1,1,100,1,7));gs.apply_one((0,0,1,1,100,2,8))
            before=len(mmio.calls)
            with self.assertRaises(ValueError): gs.apply_one((0,0,1,1,100,3,9))
            self.assertEqual(len(mmio.calls),before)
    def test_explicit_four_commands_account_all_438_ios_and_61_status_reads(self):
        self.assertIsNotNone(demo,'typed four-cycle selection not implemented')
        profile=demo.DEMO_FOUR_CYCLE
        state=protocol.Sequence()
        init=dict(identity_words=list(IDENTITY),max_commands=4,max_polls=16,duration_ns=10_000_000_000,max_io=450,
            demo_cycle_profile=demo.to_wire(profile))
        self.packet(state,'init',init,'init')
        scan=dict(request_hex='00',source_hex='01',companions_hex=['02']*4,build_binding={},max_io=900)
        with patch.object(g,'Path',return_value=NS(read_text=lambda:'boot')):
            gs,mmio=self.fixture(profile); first=gs.init(IDENTITY); deadline=first.deadline_board_monotonic_ns
            for i in range(1,5):
                self.packet(state,'trace_scan',scan,'scan'+str(i))
                words=(0,0,1,1,100,i,i+6)
                self.packet(state,'apply',dict(command_words=list(words)),'apply'+str(i))
                facts=gs.apply_one(words)
                self.assertEqual(facts.capture.words32[1:3],(i,i+6))
                self.assertEqual(facts.identity_words,IDENTITY)
                self.assertEqual(facts.deadline_board_monotonic_ns,deadline)
                self.packet(state,'status',{},'status'+str(i)); gs.observe_status()
            self.packet(state,'close',dict(stop=True),'close'); end=gs.close(stop=True)
            self.assertEqual((state.counts['trace_scan'],state.counts['apply'],state.counts['status']),(4,4,4))
            self.assertEqual((gs._capture_polls,gs._total_status_reads),(16,61))
            self.assertEqual(mmio.status_reads,62)  # one original factory status + session61
            self.assertEqual(len(mmio.calls),438)
            self.assertEqual(gs.issuer.port._count,438)
            self.assertEqual(len(end.receipts),438)
            self.assertTrue(all(r.started_raw and r.returned_raw for r in end.receipts))
            self.assertEqual(end.state,'CLOSED'); self.assertEqual(mmio.controls,[1]+[2,4,5]*4+[3])
            journal=b._json((gs.issuer.directory/'transaction-started.json').read_bytes())
            self.assertEqual(journal['demo_cycle_profile'],demo.to_wire(profile))
    def test_each_new_budget_and_unknown_is_independently_fail_closed(self):
        self.assertIsNotNone(demo,'typed four-cycle selection not implemented')
        profile=demo.DEMO_FOUR_CYCLE
        for bad in (True,{},'four',4):
            with self.assertRaises((TypeError,ValueError)): demo.validate_profile(bad)
        with self.assertRaises(ValueError): replace(profile,sha256='0'*64)
        with patch.object(g,'Path',return_value=NS(read_text=lambda:'boot')):
            gs,mmio=self.fixture(profile,polls=17); gs.init(IDENTITY)
            with self.assertRaises(ValueError): gs.apply_one((0,0,1,1,100,1,7))
            self.assertEqual(gs._capture_polls,16)
            calls=len(mmio.calls)
            with self.assertRaises(ValueError): gs.apply_one((0,0,1,1,100,1,7))
            self.assertEqual(len(mmio.calls),calls)
            status,sm=self.fixture(profile); status.init(IDENTITY)
            for _ in range(57): status._step('read32',8)
            self.assertEqual(status._total_status_reads,61)
            calls=len(sm.calls)
            with self.assertRaises(ValueError): status._step('read32',8)
            self.assertEqual(len(sm.calls),calls)
            io,im=self.fixture(profile); io.init(IDENTITY)
            while io.issuer.port._count<450: io._step('read32',0x100)
            with self.assertRaises(ValueError): io._step('read32',0x100)
            self.assertEqual((io.issuer.port._count,len(im.calls)),(450,450))
            unknown,um=self.fixture(profile); unknown.init(IDENTITY); um.unknown=True
            with self.assertRaises(OSError): unknown.observe_status()
            count=len(um.calls)
            with self.assertRaises(ValueError): unknown.apply_one((0,0,1,1,100,1,7))
            with self.assertRaises(ValueError): unknown.close(stop=True)
            self.assertEqual(len(um.calls),count)
            self.assertEqual(unknown.close().state,'CLOSED_AFTER_FAILURE')
            expired,em=self.fixture(profile); expired.init(IDENTITY)
            self.virtual_ns=expired.issuer._deadline
            count=len(em.calls)
            with self.assertRaises((ValueError,TimeoutError)): expired.apply_one((0,0,1,1,100,1,7))
            self.assertEqual(len(em.calls),count)

    def test_client_typed_init_survives_original_owner_work_snapshot(self):
        self.assertIsNotNone(demo,'typed four-cycle selection not implemented')
        from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client
        from competition.deepeye.tools.diagnostic import original_chain_client_work_a as work
        # Only intent serialization is under test; no Session/SSH is acquired.
        host=object.__new__(client.ChainSessionV2);host.sequence=protocol.Sequence()
        def serialize(ident,kind,payload,timeout): return self.packet(host.sequence,kind,payload,ident)
        host._g05=serialize
        result=host.init('init',IDENTITY,max_commands=4,max_polls=16,duration_ns=10_000_000_000,
            max_io=450,timeout_ns=1000,demo_cycle_profile=demo.DEMO_FOUR_CYCLE)
        self.assertEqual(result['payload']['demo_cycle_profile'],demo.to_wire(demo.DEMO_FOUR_CYCLE))
        scan=dict(request_hex='00',source_hex='01',companions_hex=['02']*4,build_binding={},max_io=900)
        for i in range(3): self.packet(host.sequence,'trace_scan',scan,'s'+str(i))
        snapshot=host._sequence_snapshot();self.assertEqual(len(snapshot),8)
        def encode(ident):
            job=NS(kind='encode',args=(ident,'trace_scan',scan,'SYNTHETIC_TEST_A380',host._sequence_snapshot()),
                value=None,error=None,done=threading.Event())
            work._execute(job);return job
        fourth=encode('fourth');self.assertIsNone(fourth.error);self.assertTrue(fourth.done.is_set())
        host.sequence.consume(fourth.value[1])
        fifth=encode('fifth');self.assertIsInstance(fifth.error,ValueError)

if __name__=='__main__': unittest.main(verbosity=2)
