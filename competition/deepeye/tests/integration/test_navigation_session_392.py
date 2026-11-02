"""SYNTHETIC_TEST: pure scheduling/gates; no native sensor or authority proof."""
import unittest
import os
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from competition.deepeye.tools.diagnostic.causal_pl_exchange import _CausalSourcePump
from competition.deepeye.simulation.authority import root_source_book

try:
    from competition.deepeye.simulation.authority import navigation_session_profile as nav
except ImportError:
    nav = None


class _Signal:
    def __init__(self): self.ticks = []
    def acquire_em(self, tick, pose, **kwargs): self.ticks.append(tick)
    def sample_adc(self, tick, **kwargs):
        return SimpleNamespace(to_payload=lambda: {'tick_ms': tick})


class NavigationSourceControls(unittest.TestCase):
    def profile(self):
        self.assertIsNotNone(nav, 'explicit navigation revision is not implemented')
        return nav.NAV_ADJACENT_180S

    def test_cadence_reserves_only_actual_current_bin_and_never_backfills(self):
        profile = self.profile(); clock = [1_000_000_000]; signal = _Signal()
        source = _CausalSourcePump(signal, lambda: object(), lambda *a: None,
                                  navigation_profile=profile)
        source.start(clock[0], lambda: clock[0])
        self.assertEqual(source.poll(), {'tick_ms': 0})
        clock[0] += 990_000_000
        self.assertIsNone(source.poll()); self.assertEqual(source._count, 1)
        clock[0] += 20_000_000
        self.assertIsNone(source.poll()); self.assertEqual(source._count, 1)
        clock[0] = 4_000_000_000  # missed second slot is not replayed
        self.assertEqual(source.poll(), {'tick_ms': 3000})
        self.assertEqual(signal.ticks, [0, 3000]); self.assertEqual(source._count, 2)
        clock[0] = 181_000_000_000
        self.assertEqual(source.poll(), {'tick_ms': 180000})
        clock[0] += 1
        with self.assertRaises(TimeoutError): source.poll()
        with self.assertRaises(ValueError): source.start(clock[0], lambda: clock[0])

    def test_book_uses_captured_profile_and_legacy_duration_stays_ten_seconds(self):
        profile = self.profile()
        for selected, good, bad in ((None, 10_000_000_000, 10_000_000_001),
                                    (profile, 180_000_000_000, 180_000_000_001)):
            clock = [good]
            gate = SimpleNamespace(_clock=lambda: clock[0], _high=0,
                _deadline=200_000_000_000, _origin=0, _navigation_profile=selected)
            self.assertEqual(root_source_book._SourceBookCore._time(gate), good)
            clock[0] = bad
            with self.assertRaises(ValueError): root_source_book._SourceBookCore._time(gate)
        clock = [0]; legacy = _CausalSourcePump(_Signal(), lambda: object(), lambda *a: None)
        legacy.start(0, lambda: clock[0]); clock[0] = 10_000_000_001
        with self.assertRaises(TimeoutError): legacy.poll()

    def test_typed_identity_rejects_forgery_and_prospective_io_covers_all_status(self):
        profile = self.profile()
        self.assertEqual(nav.from_wire(nav.to_wire(profile)), profile)
        for value in ({'profile_id': profile.profile_id, 'sha256': '0'*64},
                      {'profile_id': profile.profile_id, 'sha256': profile.sha256, 'duration_ns': 1}):
            with self.assertRaises(ValueError): nav.from_wire(value)
        with self.assertRaises(TypeError): nav.validate_profile(SimpleNamespace(**vars(profile)))
        self.assertEqual(nav.prospective_io(profile), 1754)
        self.assertLessEqual(nav.prospective_io(profile), 2048)
        rebound=_CausalSourcePump(_Signal(),lambda:object(),lambda *a:None)
        rebound.start(0,lambda:0); rebound._navigation_profile=profile
        with self.assertRaises(ValueError):rebound.poll()
        self.assertEqual(rebound._count,0)


class NavigationProtocolControls(unittest.TestCase):
    """Real G05/issuer/session ledger with synthetic MMIO and virtual clock.

    Fixture fsync is suppressed only to keep this file-backed protocol control
    finite on Windows; production durability, clock and I/O code stay unchanged.
    """
    def setUp(self):
        from competition.deepeye.tools.diagnostic import functional50_g05_session_a as session
        self.ns = 1_000_000
        def clock(): self.ns += 1000; return self.ns
        self.enterContext(patch.object(session.time, 'monotonic_ns', clock))
        self.enterContext(patch.object(os, 'fsync', lambda fd: None))

    def fixture(self, polls=8):
        from competition.deepeye.tests.integration.test_demo_four_cycle_protocol_a import MemoryMMIO
        from competition.deepeye.tools.diagnostic import functional50_board_a as b
        from competition.deepeye.tools.diagnostic import functional50_g05_a as g
        from competition.deepeye.tools.diagnostic import functional50_g05_transaction_a as tx
        from competition.deepeye.tools.diagnostic import functional50_g05_session_a as session
        profile = nav.NAV_ADJACENT_180S
        path = Path(tempfile.mkdtemp(prefix='SYNTHETIC_TEST_A392_'))
        trace = object.__new__(b._TracePort); device = object()
        trace._pid=os.getpid(); trace._boot='boot'; trace._failed=False; trace._mmio=SimpleNamespace(device=device)
        reg=(device,None,None,(('operation_id','SYNTHETIC_TEST_A392'),),None,None,os.getpid(),trace._mmio,threading.get_ident())
        b._G05_LOADS[trace]=reg; b._G05_CLAIMED.add(trace)
        self.addCleanup(b._G05_LOADS.pop,trace,None); self.addCleanup(b._G05_CLAIMED.discard,trace)
        self.addCleanup(b._G05_PORTS.pop,trace,None)
        mmio=MemoryMMIO(device,polls)
        port=g.G05Port(g._KEY,trace,reg,mmio,path,dict(binding={},policy_sha256='a'*64,
            limits=dict(begin=1,commit=16,stop=1,latch=16,release=16,total_io=2048)))
        b._G05_PORTS[trace]=port
        for off in (0,4,8,0x10): port.read32(off,'factory-'+str(off))
        try:
            limits=tx.Limits(16,128,180_000_000_000,demo_cycle_profile=profile)
            issuer=tx.TransactionIssuer(trace,port,limits)
            gs=session.G05SessionV2(issuer,demo_cycle_profile=profile)
        except (TypeError,ValueError) as error:
            self.fail('navigation session limits are not implemented: '+str(error))
        self.addCleanup(tx._ISSUERS.pop,port,None); self.addCleanup(session._SESSIONS.pop,issuer,None)
        return gs,mmio

    def test_sixteen_real_command_lifecycles_fit_1754_ios_and_293_status_reads(self):
        from competition.deepeye.tools.diagnostic import functional50_g05_a as g
        from competition.deepeye.tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
        from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as protocol
        ident=(1,0,0,0,0,0,0,0,2,0,0,0,7); selected=nav.NAV_ADJACENT_180S
        state=protocol.Sequence()
        init=dict(identity_words=list(ident),max_commands=16,max_polls=128,duration_ns=180_000_000_000,
            max_io=2048,demo_cycle_profile=nav.to_wire(selected))
        def packet(kind,payload,request_id):
            line=protocol.raw(dict(schema=protocol.SCHEMA,id=request_id,operation_id='SYNTHETIC_TEST_A392',kind=kind,payload=payload))+b'\n'
            x=protocol.decode_request(line,'SYNTHETIC_TEST_A392',g,state); state.consume(x)
        try: packet('init',init,'init')
        except (TypeError,ValueError) as error:self.fail('navigation wire profile rejected: '+str(error))
        with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
            gs,mmio=self.fixture(); first=gs.init(ident); deadline=first.deadline_board_monotonic_ns
            for i in range(1,17):
                packet('trace_scan',dict(request_hex='00',source_hex='01',companions_hex=['02']*4,
                    build_binding={},max_io=900),'scan'+str(i))
                words=(0,0,1,20,3000,i,i+6)
                packet('apply',dict(command_words=list(words)),'apply'+str(i)); facts=gs.apply_one(words)
                self.assertEqual(facts.capture.words32[1:3],(i,i+6))
                self.assertEqual(facts.deadline_board_monotonic_ns,deadline)
                packet('status',{},'status'+str(i)); gs.observe_status()
            before=len(mmio.calls)
            with self.assertRaises(ValueError):packet('status',{},'status17')
            with self.assertRaises(ValueError):gs.observe_status()
            self.assertEqual(len(mmio.calls),before)
            packet('close',dict(stop=True),'close'); end=gs.close(stop=True)
            self.assertEqual((state.counts['trace_scan'],state.counts['apply'],state.counts['status']),(16,16,16))
            self.assertEqual((gs._capture_polls,gs._total_status_reads,mmio.status_reads),(128,293,294))
            self.assertEqual((len(mmio.calls),gs.issuer.port._count,len(end.receipts)),(1754,1754,1754))
            self.assertEqual(end.state,'CLOSED'); self.assertEqual(len(state.ids),50)
            self.assertEqual(demo.request_cap(selected),50)
            self.assertEqual(demo.to_wire(demo.DEMO_FOUR_CYCLE)['sha256'],'23cade475cd4128d653142ef27bc8384d79fcb8e05f4e0c4b89145264e1b38c0')

    def test_capture_status_io_and_expired_origin_each_refuse_before_next_mmio(self):
        from competition.deepeye.tools.diagnostic import functional50_g05_a as g
        ident=(1,0,0,0,0,0,0,0,2,0,0,0,7)
        with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
            capture,cm=self.fixture(polls=129); capture.init(ident)
            with self.assertRaises(ValueError): capture.apply_one((0,0,1,1,3000,1,7))
            self.assertEqual(capture._capture_polls,128)
            status,sm=self.fixture(); status.init(ident)
            for _ in range(289):status._step('read32',8)
            before=len(sm.calls)
            with self.assertRaises(ValueError):status._step('read32',8)
            self.assertEqual(len(sm.calls),before)
            from competition.deepeye.tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
            before=len(sm.calls)
            with self.assertRaises(ValueError):demo.validate_caps(nav.NAV_ADJACENT_180S,
                max_commands=16,max_polls=128,duration_ns=180_000_000_000,max_io=2049)
            self.assertEqual(len(sm.calls),before)
            expired,em=self.fixture(); expired.init(ident); self.ns=expired.issuer._deadline
            before=len(em.calls)
            with self.assertRaises((ValueError,TimeoutError)):expired.apply_one((0,0,1,1,3000,1,7))
            self.assertEqual(len(em.calls),before)
class NavigationRollingControls(unittest.TestCase):
    def test_public_window_retains_actual_recent_refs_without_trimming_journal(self):
        self.assertTrue(hasattr(nav,'rolling_refs'),'navigation rolling refs are not implemented')
        actions=tuple((i,object()) for i in range(1,71)); latest=object()
        observations=((71,latest),)
        selected_observations,selected_actions=nav.rolling_refs(nav.NAV_ADJACENT_180S,observations,actions,latest)
        self.assertEqual(selected_observations,(latest,))
        self.assertEqual(selected_actions,tuple(x[1] for x in actions[39:]))
        self.assertEqual(len(actions),70)
        with self.assertRaises(ValueError):nav.rolling_refs(None,observations,actions,latest)
        with self.assertRaises(ValueError):nav.rolling_refs(nav.NAV_ADJACENT_180S,((0,latest),),actions,latest)
class NavigationCommandControls(unittest.TestCase):
    def test_three_second_command_requires_typed_session_and_preserves_old_caps(self):
        from competition.deepeye.simulation.authority.owned_invocation_v1 import mechanics,adapter
        from competition.deepeye.integration import motion
        profile=nav.NAV_ADJACENT_180S
        args=(dict(status='ADVISE',speed_limit_m_s=.25,direction_world=[0.,0.,1.]),
              dict(pose=dict(orientation_xyzw=[0.,0.,0.,1.])), 'fast_9600', 3000, motion)
        try: target=mechanics.quantize_target(*args,max_duration_ms=3000,navigation_profile=profile)
        except (TypeError,ValueError) as error:self.fail('typed navigation command duration unavailable: '+str(error))
        self.assertEqual((target['duration_ms'],target['speed_code']),(3000,20))
        with self.assertRaises(ValueError):mechanics.quantize_target(*args,max_duration_ms=3000)
        policy=adapter.OwnedInvocationPolicy('SYNTHETIC_TEST_A392','a'*64,'b'*40,16,256,65536,3000,
            navigation_profile=profile)
        policy.check()
        with self.assertRaises(ValueError):adapter.OwnedInvocationPolicy(
            'SYNTHETIC_TEST_A392','a'*64,'b'*40,16,256,65536,3000).check()
        with self.assertRaises(ValueError):adapter.OwnedInvocationPolicy(
            'SYNTHETIC_TEST_A392','a'*64,'b'*40,16,256,65536,1001,demo_duration_v1=True).check()

class NavigationTraceBudgetControls(unittest.TestCase):
    def test_actual_four_result_reducer_scan_cost_is_explicit_under_existing_trace_cap(self):
        from competition.deepeye.tests.integration import test_trace_batch_cancel_collect_order as fixture
        from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader
        from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as batch
        bundle=loader.load_selected(Path.cwd()); _prepared,_companions,frames,packet=fixture.synthetic_packet(bundle)
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_TEST_A392_TRACE_') as tmp:
            port=fixture.SyntheticPort(Path(tmp),frames)
            response=batch.run_batch(port,bundle,packet,SimpleNamespace(_TracePort=fixture.SyntheticPort),
                dict(operation_id='op',build_id='c'*32))
            document=batch._json(response)
            self.assertEqual(document['status'],'COMPLETE')
            self.assertEqual(len(document['results']),4)
            print('A392_SYNTHETIC_FOUR_RESULT_TRACE_IO',port._count,'SIXTEEN',16*port._count)
            self.assertGreater(16*port._count,5000)  # original failure remains in A392 evidence
            self.assertLessEqual(16*port._count,nav.NAV_ADJACENT_180S.max_trace_io)

class NavigationFactsControls(unittest.TestCase):
    def test_complete_failure_deadlines_and_larger_replies_require_same_selected_profile(self):
        from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client
        profile=nav.NAV_ADJACENT_180S; ident=(1,0,0,0,0,0,0,0,2,0,0,0,7)
        receipts=[dict(index=i,started_raw_hex='7b7d',returned_raw_hex='7b7d') for i in range(1,502)]
        facts=dict(schema='g05_csr_session_v2',kind='status',operation_id='fixture',policy_sha256='a'*64,
            deadline_selected_lower_board_monotonic_ns=1,deadline_board_monotonic_ns=180_000_000_001,
            phase_io_first=1,phase_io_last=501,identity_words=list(ident),status=1,fault=0,capture=None,
            receipts=receipts,unresolved_receipts=[],state='ACTIVE',authority='not_evaluated')
        deadline=client._facts(facts,'status','fixture',ident,None,profile)
        self.assertEqual(deadline,(1,180_000_000_001))
        with self.assertRaises(ValueError):client._facts(facts,'status','fixture',ident,None)
        shifted=dict(facts,deadline_board_monotonic_ns=180_000_000_002)
        with self.assertRaises(ValueError):client._facts(shifted,'status','fixture',ident,deadline,profile)
        failed=dict(facts,kind='close',state='CLOSED_AFTER_FAILURE')
        client._failure_facts(failed,'fixture',profile)
        with self.assertRaises(ValueError):client._failure_facts(
            dict(failed,deadline_board_monotonic_ns=181_000_000_001),'fixture',profile)
        response=client.protocol.raw(dict(schema=client.protocol.SCHEMA,id='x',operation_id='fixture',
            kind='status',status='COMPLETE',result={'SYNTHETIC_TEST_padding':'x'*1_100_000},error=None,unknown=False))+b'\n'
        client._response(response,'x','fixture','status',profile)
        with self.assertRaises(ValueError):client._response(response,'x','fixture','status')
        with self.assertRaises(ValueError):client._response(b'x'*4_194_305,'x','fixture','status',profile)




class NavigationTracePortBoundaryControls(unittest.TestCase):
    """True port gate, synthetic counter checkpoints; no priorIO execution claim."""
    def test_default_four_and_navigation_caps_deadline_and_forgery_keep_real_port_ledger(self):
        from competition.deepeye.tools.diagnostic import functional50_board_a as b
        from competition.deepeye.tools.diagnostic import functional50_trace_cycles_a as cycles
        from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader
        from competition.deepeye.tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
        from competition.deepeye.tests.integration.test_trace_batch_cancel_collect_order import synthetic_packet
        bundle=loader.load_selected(Path.cwd()); self.ns=1000
        self.enterContext(patch.object(b.time,'monotonic_ns',lambda:self.ns))
        self.enterContext(patch.object(b,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')))
        def fixture(selected,bind=True):
            directory=Path(tempfile.mkdtemp(prefix='SYNTHETIC_TEST_A392_BOUNDARY_')); calls=[];device=object()
            mmio=SimpleNamespace(device=device,read=lambda off:(calls.append(('read',off)) or 0),
                                  write=lambda off,value:calls.append(('write',off,value)))
            port=b._TracePort(b._KEY,mmio,directory,'boot',b.select_trace_cycle_v2());port._cycle_ready=True
            reg=(device,None,None,(),None,None,os.getpid(),mmio,threading.get_ident())
            b._G05_LOADS[port]=reg;self.addCleanup(b._G05_LOADS.pop,port,None)
            owner=cycles.TraceCycles(port,bundle);self.addCleanup(cycles._OWNERS.pop,port,None)
            if selected is not None:owner.select_demo_cycle_profile(selected)
            if bind:
                owner.bind_deadline(self.ns+demo.duration_cap(selected))
                port._cycle_active=True;port._cycle_commands={1:0,2:0,3:0,4:0,5:0,8:0}
            return owner,port,calls,directory
        for selected,cap in ((None,5000),(demo.DEMO_FOUR_CYCLE,5000),(nav.NAV_ADJACENT_180S,32768)):
            owner,port,calls,directory=fixture(selected)
            port._count=cap-1  # boundary checkpoint only; do not claim these old I/Os occurred
            port._call('read',0,None,'boundary',_cycle_owner=owner)
            self.assertEqual((port._count,len(calls)),(cap,1))
            self.assertTrue((directory/('io-%05d-started.json'%cap)).is_file())
            self.assertTrue((directory/('io-%05d-returned.json'%cap)).is_file())
            with self.assertRaises(ValueError):port._call('read',0,None,'over',_cycle_owner=owner)
            self.assertEqual((port._count,len(calls)),(cap,1))
        owner,port,calls,directory=fixture(None,bind=False)
        forged=SimpleNamespace(profile_id=nav.NAV_ADJACENT_180S.profile_id,sha256=nav.NAV_ADJACENT_180S.sha256)
        owner._demo_cycle_profile=forged  # corrupted metadata must not grant a larger port budget
        with self.assertRaises((TypeError,ValueError)):port._bind_navigation_trace_profile(owner,forged)
        self.assertEqual((port._count,len(calls)),(0,0))
        owner,port,calls,directory=fixture(nav.NAV_ADJACENT_180S)
        self.ns=port._cycle_deadline
        with self.assertRaises(TimeoutError):port._call('read',0,None,'expired',_cycle_owner=owner)
        self.assertEqual((port._count,len(calls)),(1,0))
        self.assertTrue((directory/'io-00001-not-attempted.json').is_file())
        self.assertFalse((directory/'io-00001-returned.json').exists())
        _prepared,_companions,frames,_packet=synthetic_packet(bundle)
        self.assertLessEqual(16*sum(map(len,frames)),4096)  # unchanged global POP cap
        self.assertEqual((nav.NAV_ADJACENT_180S.max_trace_scan_io,nav.NAV_ADJACENT_180S.max_trace_io),(2000,32768))




class NavigationStatusPhaseControls(unittest.TestCase):
    def test_seventeenth_status_phase_has_no_mmio_and_does_not_renew_deadline(self):
        from competition.deepeye.tools.diagnostic import functional50_g05_a as g
        helper=NavigationProtocolControls('test_capture_status_io_and_expired_origin_each_refuse_before_next_mmio')
        helper.setUp();self.addCleanup(helper.doCleanups)
        with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
            gs,mmio=helper.fixture();first=gs.init((1,0,0,0,0,0,0,0,2,0,0,0,7))
            gs._status_phases=16  # boundary checkpoint; sixteen real phases are retained in positive02
            before=len(mmio.calls)
            with self.assertRaises(ValueError):gs.observe_status()
            self.assertEqual((len(mmio.calls),gs._state),(before,'ACTIVE'))
            end=gs.close(stop=True)
            self.assertEqual(end.deadline_board_monotonic_ns,first.deadline_board_monotonic_ns)
            self.assertEqual(len(mmio.calls),42)


if __name__ == '__main__': unittest.main()