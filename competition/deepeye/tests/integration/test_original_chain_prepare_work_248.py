"""Synthetic owner/worker preparation controls; no board, SSH or native run."""
import json,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.integration import host_clock
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan,original_chain_source_pump_a as pm,functional50_ssh_a as ssh,functional50_b131_loader as loader

class Token:pass
class Preparation:
 def __init__(self,request,source,companions):self.status='TRACE94_PLAN_PREPARED';self.plan=object();self.original=types.SimpleNamespace(request=request,source=source,companions=companions)
class Ledger:
 def _observe_time(self,*args):pass
 def accept(self,payload,**kwargs):return types.SimpleNamespace(record=types.SimpleNamespace(adc_tick_ms=payload['tick'],em_tick_ms=payload.get('em')))

class Tests(unittest.TestCase):
 def fixture(self):
  clock=host_clock.QpcHostClock(host_clock._FACTORY,dict(domain_id='a'*32));owner=threading.get_ident();book=types.SimpleNamespace(_samples=[],_active=None,_origin=1_000_000_000)
  source=types.SimpleNamespace(state='RUNNING',_origin=book._origin,_clock=clock,_count=0);source._source_book=book;book._source=source
  source._handoff_bytes=lambda p:scan._raw(p)
  f=types.SimpleNamespace(_retained_samples=[],book=book,source=source,clock=clock)
  f._retained_sample=lambda p:next(x for x in f._retained_samples if x['payload'] is p)
  bundle=object.__new__(loader._Bundle);bundle.adapter=types.SimpleNamespace(Preparation=Preparation,prepare_bytes=lambda r,s,c,build_binding:Preparation(r,s,c));bundle.reducer=object()
  sc=object.__new__(scan.OriginalSourceTraceScan)
  for k,v in dict(_thread=owner,_functional=f,_book=book,_source=source,_clock=clock,_origin=book._origin,_domain='a'*32,_bundle=bundle,_ledger=Ledger(),_admitted=[],_failed=False,_prepared=False,_source_scan_cycle_v2=True,_activated=True,_prepare_count=0,_last_prepared_index=None,_last_prepared_tick=None,_attempts=[],_results=[],_attempt=None,_result=None).items():setattr(sc,k,v)
  session=object.__new__(ssh.Session);session._thread=owner;session._clock=clock;session._protocol='functional50_chain_v2';session._check=lambda:None
  pump=object.__new__(pm.OriginalChainSourcePump);pump._session=session;pump._source=f;pump._scanner=sc;pump._clock=clock;pump._enabled=True;pump._failed=False;session._source_pump=pump
  def append(tick):
   payload=dict(tick=tick);raw=scan._raw(payload);tok=Token();tok._book=book;tok._ended=True;tok._draft=dict(status='complete',tick_ms=tick,source_count=len(book._samples)+1,finish_qpc_ns=1_000_000_000,canonical_source_hex=raw.hex(),source_sha256=scan._sha(raw));book._samples.append(tok._draft);entry=dict(book=book,payload=payload,token=tok,raw=raw);f._retained_samples.append(entry);source._count+=1;sc.admit(payload);return payload
  return sc,pump,session,append
 def controls(self,sc,session,pump,now,poll,check_bundle=None):
  def check(x):
   if threading.get_ident()!=x._thread or x._failed:raise ValueError('original thread or failed')
  def construct(payload,raw,draft,origin,domain,received,evaluated,facts,provenance,clock_metadata=None):return (b'req'+raw,raw,(b'a',b'b',b'c',b'd'))
  stack=[patch.object(scan.OriginalSourceTraceScan,'_check',check),patch.object(scan.root_source_book,'_Sample',Token),patch.object(host_clock.QpcHostClock,'__call__',lambda _:now[0]),patch.object(pm.OriginalChainSourcePump,'poll_once',poll),patch.object(scan,'_construct_bytes',construct),patch.object(scan,'_check_bundle',check_bundle or (lambda _:None)),patch.dict(ssh._SESSION_PUMPS,{session:pump})]
  for p in stack:p.start();self.addCleanup(p.stop)
 def test_interleaved_admission_and_next_original_selection(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];started=threading.Event();release=threading.Event();added=[];calls=[]
  def check_bundle(_):
   calls.append(1)
   if len(calls)==1:started.set();release.wait(1)
  def poll(p,s):
   if started.is_set() and not added:
    with self.assertRaises(ValueError):sc.prepare(first,facts={},build_binding={})
    with self.assertRaises(ValueError):sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
    added.append(append(10));release.set()
  self.controls(sc,session,pump,now,poll,check_bundle);first=append(0)
  result=sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
  self.assertEqual(result.original.source,scan._raw(first));self.assertEqual(len(sc._admitted),2)
  self.assertEqual(sc._prepared_work_deadline(result),1_520_000_000)
  self.assertEqual(sc._check_prepared_dispatch(result),1_520_000_000)
  with self.assertRaises(ValueError):sc._check_prepared_dispatch(result)
  second=sc.prepare_with_pump(added[0],facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
  self.assertEqual(second.original.source,scan._raw(added[0]));self.assertEqual(sc._prepare_count,2)
 def test_current_original_draft_mutation_during_work_is_refused(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];started=threading.Event();release=threading.Event();changed=[]
  def check_bundle(_):started.set();release.wait(1)
  def poll(p,s):
   if started.is_set() and not changed:sc._admitted[0]['draft']['tampered']=True;changed.append(True);release.set()
  self.controls(sc,session,pump,now,poll,check_bundle);first=append(0)
  with self.assertRaises(ValueError):sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
  self.assertTrue(sc._failed);self.assertEqual(sc._prepare_count,1)
 def test_wrong_pump_and_wrong_owner_are_rejected(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];self.controls(sc,session,pump,now,lambda *_:None);first=append(0)
  with self.assertRaises(ValueError):sc.prepare_with_pump(first,facts={},build_binding={},pump=object(),timeout_ns=10)
  errors=[]
  def other():
   try:sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=10)
   except Exception as e:errors.append(e)
  t=threading.Thread(target=other);t.start();t.join();self.assertEqual(len(errors),1);self.assertIsInstance(errors[0],ValueError)
 def test_timeout_preserves_pending_original_job_and_consumes_attempt(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];started=threading.Event();release=threading.Event()
  def check_bundle(_):started.set();release.wait(2)
  def poll(p,s):
   if started.is_set():now[0]+=1_000_000
  self.controls(sc,session,pump,now,poll,check_bundle);first=append(0)
  try:
   with self.assertRaises(TimeoutError):sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=3_000_000)
   self.assertTrue(sc._failed);self.assertEqual(sc._prepare_count,1);self.assertIsNotNone(sc._prepare_job);self.assertTrue(sc._prepare_job.thread.is_alive())
   with self.assertRaises(ValueError):sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=3_000_000)
  finally:release.set();sc._prepare_job.thread.join(1)
 def test_freshness_expiry_is_not_refreshed_or_reselected(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];started=threading.Event();release=threading.Event()
  def check_bundle(_):started.set();release.wait(1)
  def poll(p,s):
   if started.is_set():now[0]=1_101_000_000;release.set()
  self.controls(sc,session,pump,now,poll,check_bundle);first=append(0)
  with self.assertRaises(ValueError):sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
  self.assertTrue(sc._failed);self.assertEqual(sc._prepare_count,1)
  sc2,pump2,session2,append2=self.fixture();later=[1_110_000_000];self.controls(sc2,session2,pump2,later,lambda *_:None);selected=append2(20)
  sc2._admitted[0]['admission'].record.em_tick_ms=0
  with self.assertRaises(ValueError):sc2.prepare_with_pump(selected,facts={},build_binding={},pump=pump2,timeout_ns=500_000_000)
  self.assertTrue(sc2._failed)
 def test_default_prepare_still_refuses_new_pump_argument(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];self.controls(sc,session,pump,now,lambda *_:None);first=append(0)
  with self.assertRaises(TypeError):sc.prepare(first,facts={},build_binding={},pump=pump)
 def test_exact_dispatch_guard_rechecks_freshness_and_is_consumed(self):
  sc,pump,session,append=self.fixture();now=[1_020_000_000];self.controls(sc,session,pump,now,lambda *_:None);first=append(0)
  result=sc.prepare_with_pump(first,facts={},build_binding={},pump=pump,timeout_ns=500_000_000)
  with self.assertRaises(ValueError):sc._prepared_work_deadline(Preparation(b'fake',b'fake',(b'a',)*4))
  now[0]=1_101_000_000
  with self.assertRaises(ValueError):sc._check_prepared_dispatch(result)
  self.assertTrue(sc._failed)
  with self.assertRaises(ValueError):sc._check_prepared_dispatch(result)
 def test_fixed_job_uses_real_b131_on_synthetic_original_bytes(self):
  from competition.deepeye.tools.diagnostic import original_chain_prepare_work_a as work
  bundle=loader.load_selected(Path.cwd())
  lineage=dict(operation_id='fixture',request_id='fixture-request',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='fixture-boot',session_id=4,tag=5,trigger_id=6,generation=1,request_seq=7,capture_seq=8)
  facts=dict(work_id='fixture-work',declared_by='synthetic-test',scan_id_uint63=1,view=2,frame_seq_start=5,sample_index=8,binding_receipt_id='fixture-bind',lineage=lineage)
  binding=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='fixture',request_hash='a'*64)
  payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=90,em_tick_ms=None,channel_values=[None,None,None,.1],channel_counts=[None,None,None,205],quality=4104)
  draft=dict(status='complete',tick_ms=90,source_count=10,finish_qpc_ns=1090000001,adc={'begin_qpc_ns':1090000000,'end_qpc_ns':1090000001})
  job=work._PrepareJob(work._KEY,bundle,scan._raw(payload),scan._raw(draft),scan._raw(facts),scan._raw(binding),scan._raw(dict(domain_id='a'*32)),1000000000,'a'*32,1090000001,1090000002)
  job.start(work._KEY);job.thread.join(5)
  self.assertFalse(job.thread.is_alive());self.assertIsNone(job.error);self.assertIs(type(job.result),bundle.adapter.Preparation)
  self.assertEqual(job.result.status,'TRACE94_PLAN_PREPARED');self.assertEqual(job.result.original.source,scan._raw(payload));self.assertEqual(len(job.result.original.companions),4)
if __name__=='__main__':unittest.main()
