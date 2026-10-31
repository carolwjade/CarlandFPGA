"""New fixed client-work controls; synthetic only, no native or board."""
import unittest,runpy,threading,time,tempfile,types,io,json
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client, functional50_ssh_a as ssh

class FixedWorkTests(unittest.TestCase):
 def test_selected_mode_entrypoints_exist(self):
  self.assertTrue(callable(getattr(client.ChainSessionV2,'select_owner_work_v1',None)))
  self.assertIsInstance(getattr(client.ChainSessionV2,'owner_work_v1',None),property)
  self.assertTrue(callable(getattr(ssh.Session,'_call_until',None)))
_helper=runpy.run_path(str(Path(__file__).with_name('test_original_chain_receipt_producer_a.py')))
_fixture=_helper['Tests'].fixture

class OwnerWorkTests(unittest.TestCase):
 def fixture(self,tmp):
  from competition.deepeye.tools.diagnostic import original_chain_source_pump_a as pm
  from competition.deepeye.integration.host_clock import QpcHostClock
  world,source,bundle,scanner,session,chain,clock=_fixture(self,tmp)
  chain.select_owner_work_v1();chain.sequence.initialized=True;chain.sequence.max_commands=2;chain.sequence.ids.add('init');client._PHASE_LEDGERS[chain].append(object())
  session._threads=[];pump=object.__new__(pm.OriginalChainSourcePump);pump._enabled=True;pump._failed=False;pump._session=session;pump._clock=clock;pump._scanner=scanner;session._source_pump=pump
  self.addCleanup(patch.dict(ssh._SESSION_PUMPS,{session:pump}).stop) if False else None
  pc=patch.object(pm.OriginalChainSourcePump,'_check',lambda *_:None);pc.start();self.addCleanup(pc.stop)
  pp=patch.dict(ssh._SESSION_PUMPS,{session:pump});pp.start();self.addCleanup(pp.stop)
  cp=patch.object(QpcHostClock,'__call__',lambda _:time.monotonic_ns());cp.start();self.addCleanup(cp.stop)
  return session,chain,pump,clock
 def test_selection_is_private_and_one_use(self):
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp);self.assertTrue(chain.owner_work_v1)
   with self.assertRaises(ValueError):chain.select_owner_work_v1()
   with self.assertRaises(AttributeError):chain.owner_work_v1=False
 def test_original_phase_and_owner_pump_during_io_and_fsync(self):
  from competition.deepeye.tools.diagnostic import original_chain_source_pump_a as pm, functional50_trace_batch_client_a as trace
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp);owner=threading.get_ident();calls=[]
   response=json.dumps(dict(schema='functional50_chain_v2',id='status1',operation_id='op',kind='status',status='COMPLETE',result={},error=None,unknown=False)).encode()+b'\n'
   class Reader:
    def readline(self,n):time.sleep(.015);return response
   session._proc.stdin=io.BytesIO();session._proc.stdout=Reader();o=list(ssh._SESSION_ORIGINS[session]);o[7]=session._proc.stdin;o[8]=session._proc.stdout;ssh._SESSION_ORIGINS[session]=tuple(o);chain._phase_binding() if False else None
   # Original registry is re-seeded only inside this synthetic fixture.
   old=client._CHAIN_BINDINGS[chain];client._CHAIN_BINDINGS[chain]=(old[0],old[1],old[2],old[3],old[4],ssh._SESSION_ORIGINS[session]);client._OWNER_WORK_SELECTION[chain]=client._CHAIN_BINDINGS[chain]
   actual=ssh._record
   def delayed(*args,**kwargs):time.sleep(.015);return actual(*args,**kwargs)
   def poll(self,s):calls.append(threading.get_ident())
   with patch.object(pm.OriginalChainSourcePump,'poll_once',poll),patch.object(ssh,'_record',delayed):
    out=chain._send('status1','status',{},1_000_000_000)
   self.assertGreaterEqual(len(calls),2);self.assertTrue(all(x==owner for x in calls));self.assertIs(chain.phase_receipts[-1],out['phase_receipt']);self.assertIs(out['phase_receipt'].response_raw,response);self.assertLessEqual(out['lower_qpc_ns'],out['upper_qpc_ns']);self.assertIn(b'"id":"status1"',session._proc.stdin.getvalue())
 def test_worker_timeout_retains_thread_and_prevents_retry(self):
  from competition.deepeye.tools.diagnostic import original_chain_client_work_a as work,original_chain_source_pump_a as pm
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp);gate=threading.Event()
   def blocked(*args,**kwargs):gate.wait(1)
   with patch.object(ssh,'_record',blocked),patch.object(pm.OriginalChainSourcePump,'poll_once',lambda *a:None):
    end=clock()+10_000_000;job=work._start(chain,'intent',(chain.folder,1,'x','status',b'wire',1),end)
    with self.assertRaises(ValueError):work._wait(chain,job,end+1_000_000_000)
    with self.assertRaises(TimeoutError):work._wait(chain,job,end)
    self.assertTrue(session._unknown);self.assertTrue(job.thread.is_alive())
    with self.assertRaises(ValueError):work._start(chain,'intent',(chain.folder,1,'x','status',b'wire',1),end)
    gate.set();job.thread.join(1)
 def test_cross_thread_and_foreign_job_refused(self):
  from competition.deepeye.tools.diagnostic import original_chain_client_work_a as work
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp);errors=[]
   def other():
    try:work._start(chain,'intent',(chain.folder,1,'x','status',b'x',1),clock()+1_000_000)
    except Exception as e:errors.append(e)
   t=threading.Thread(target=other);t.start();t.join();self.assertEqual(len(errors),1)
   with self.assertRaises(ValueError):work._wait(chain,object(),clock()+1_000_000)
 def test_trace_guard_after_started_before_any_io(self):
  from competition.deepeye.tools.diagnostic import original_chain_source_pump_a as pm
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp);scanner=pump.scanner;calls=[];chosen=object();end=clock()+1_000_000_000
   def deadline(self,p):return end if p is chosen else None
   test=self
   def refuse(scanner_self,p):
    test.assertTrue((chain.folder/'02-started.json').exists());calls.append('guard');raise ValueError('selected sample expired')
   session._call_until=lambda *args:calls.append('io')
   payload=dict(request_hex='00',source_hex='01',companions_hex=['02']*4,build_binding={},max_io=900)
   with patch.object(pm.OriginalChainSourcePump,'poll_once',lambda *args:None),patch.object(type(scanner),'_prepared_work_deadline',deadline),patch.object(type(scanner),'_check_prepared_dispatch',refuse):
    with self.assertRaisesRegex(ValueError,'selected sample expired'):chain._send_selected('scan1','trace_scan',payload,end,prepared=chosen)
   self.assertEqual(calls,['guard']);self.assertTrue(session._unknown)
 def test_semantic_failure_preserves_actual_phase(self):
  from competition.deepeye.tools.diagnostic import original_chain_source_pump_a as pm
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp)
   response=json.dumps(dict(schema='functional50_chain_v2',id='status2',operation_id='op',kind='status',status='COMPLETE',result={},error=None,unknown=False)).encode()+b'\n'
   class Reader:
    def readline(self,n):return response
   session._proc.stdin=io.BytesIO();session._proc.stdout=Reader();origin=list(ssh._SESSION_ORIGINS[session]);origin[7]=session._proc.stdin;origin[8]=session._proc.stdout;ssh._SESSION_ORIGINS[session]=tuple(origin)
   old=client._CHAIN_BINDINGS[chain];client._CHAIN_BINDINGS[chain]=(old[0],old[1],old[2],old[3],old[4],ssh._SESSION_ORIGINS[session]);client._OWNER_WORK_SELECTION[chain]=client._CHAIN_BINDINGS[chain]
   original=client.ChainSessionV2._run_work
   def fail_after_parse(self,kind,args,end):
    if kind=='trace_post':raise ValueError('semantic rejection')
    return original(self,kind,args,end)
   with patch.object(pm.OriginalChainSourcePump,'poll_once',lambda *args:None),patch.object(client.ChainSessionV2,'_run_work',fail_after_parse):
    with self.assertRaisesRegex(ValueError,'semantic rejection'):chain._send_selected('status2','status',{},clock()+1_000_000_000,trace_args=('synthetic',))
   phase=chain.phase_receipts[-1];self.assertIs(type(phase),client.OriginalPhaseReceipt);self.assertIs(phase.response_raw,response);self.assertEqual(phase.status,'COMPLETE');self.assertFalse(phase.unknown);self.assertLessEqual(phase.lower_qpc_ns,phase.upper_qpc_ns);self.assertTrue(session._unknown)
   self.assertIn(b'"id":"status2"',phase.request_raw)
   with self.assertRaises(ValueError):chain._send('retry','status',{},1_000_000)
  with tempfile.TemporaryDirectory() as tmp:
   session,chain,pump,clock=self.fixture(tmp)
   response=json.dumps(dict(schema='functional50_chain_v2',id='status3',operation_id='op',kind='status',status='UNKNOWN',result={},error='Unknown',unknown=True)).encode()+b'\n'
   class Reader:
    def readline(self,n):return response
   session._proc.stdin=io.BytesIO();session._proc.stdout=Reader();origin=list(ssh._SESSION_ORIGINS[session]);origin[7]=session._proc.stdin;origin[8]=session._proc.stdout;ssh._SESSION_ORIGINS[session]=tuple(origin)
   old=client._CHAIN_BINDINGS[chain];client._CHAIN_BINDINGS[chain]=(old[0],old[1],old[2],old[3],old[4],ssh._SESSION_ORIGINS[session]);client._OWNER_WORK_SELECTION[chain]=client._CHAIN_BINDINGS[chain]
   def reject_failure(*args):raise ValueError('bad partial facts')
   with patch.object(pm.OriginalChainSourcePump,'poll_once',lambda *args:None),patch.object(client,'_failure_facts',reject_failure):
    with self.assertRaisesRegex(ValueError,'bad partial facts'):chain._send_selected('status3','status',{},clock()+1_000_000_000)
   phase=chain.phase_receipts[-1];self.assertIs(type(phase),client.OriginalPhaseReceipt);self.assertIs(phase.response_raw,response);self.assertEqual(phase.status,'UNKNOWN');self.assertTrue(phase.unknown);self.assertTrue(session._unknown)
 def test_default_not_selected(self):
  with tempfile.TemporaryDirectory() as tmp:
   world,source,bundle,scanner,session,chain,clock=_fixture(self,tmp)
   self.assertFalse(chain.owner_work_v1);self.assertFalse(chain._selected_active('status'))

if __name__=='__main__':
 ids=['__main__.FixedWorkTests.test_selected_mode_entrypoints_exist','__main__.OwnerWorkTests.test_selection_is_private_and_one_use','__main__.OwnerWorkTests.test_original_phase_and_owner_pump_during_io_and_fsync','__main__.OwnerWorkTests.test_worker_timeout_retains_thread_and_prevents_retry','__main__.OwnerWorkTests.test_cross_thread_and_foreign_job_refused','__main__.OwnerWorkTests.test_default_not_selected','__main__.OwnerWorkTests.test_trace_guard_after_started_before_any_io']
 suite=unittest.defaultTestLoader.loadTestsFromNames(ids);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
