"""Focused synthetic producer selection and custody controls."""
import tempfile,types,unittest
from unittest.mock import patch,PropertyMock
from competition.deepeye.tests.integration import test_original_chain_receipt_producer_a as oldfixture
from competition.deepeye.tools.diagnostic import original_chain_receipt_producer_a as pmod, original_chain_source_pump_a as pm, original_source_trace_scan_a as sm, functional50_chain_v2_client_a as cm, functional50_ssh_a as ssh

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.helper=oldfixture.Tests();self.addCleanup(self.helper.doCleanups)
  self.world,self.source,self.bundle,self.scanner,self.session,self.chain,self.clock=self.helper.fixture(self.tmp.name)
  class Preparation:pass
  self.bundle.adapter=types.SimpleNamespace(Preparation=Preparation);self.prepared=Preparation();self.prepared.original=types.SimpleNamespace(request=b'r',source=b's',companions=(b'1',b'2',b'3',b'4'))
  self.producer=pmod.OriginalChainReceiptProducer(self.world,self.chain,self.scanner)
  self.chain.sequence.initialized=True  # synthetic precondition; phase receipt still allocated by real _send
  self.pump=object.__new__(pm.OriginalChainSourcePump);self.pump._session=self.session;self.pump._source=self.source;self.pump._scanner=self.scanner;self.pump._clock=self.clock;self.pump._enabled=True;self.pump._failed=False;self.pump._history=[];self.pump._pending=None
  self.producer._source_pump=self.pump;self.session._source_pump=self.pump
  self.registry=patch.dict(ssh._SESSION_PUMPS,{self.session:self.pump});self.registry.start();self.addCleanup(self.registry.stop)
  self.selected=self.make_item('selected');self.scanner._admitted.append(self.selected);self.producer._admission_count=1
 def make_item(self,label):
  payload=object();draft={'label':label};token=types.SimpleNamespace(_draft=draft,_handle=object(),_em_handle=None);admission=object();return dict(entry={'payload':payload},token=token,draft=draft,admission=admission,payload_bytes=label.encode(),received=15)
 def test_selected_pumps_new_history_before_phase_and_retains_selected_sample(self):
  later=self.make_item('later');calls=[]
  def prepare(scanner,payload,**kw):
   calls.append((payload,kw['pump']));scanner._admitted.append(later);self.pump._history.append(pm.PumpRecord(later['entry']['payload'],later['token'],later['entry'],later['draft'],later['admission'],18,True));scanner._result=self.prepared;return self.prepared
  def trace(chain,ident,*args,**kw):return self.helper.issue(chain,ident,'trace_scan',correlation={'status':'FOUR_FRAME_CORRELATION_CONSISTENT'})
  with patch.object(cm.ChainSessionV2,'owner_work_v1',new_callable=PropertyMock,return_value=True,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare_with_pump',prepare,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare',side_effect=AssertionError('selected path used legacy prepare')),patch.object(cm.ChainSessionV2,'trace_scan',trace):
   ev=self.producer.scan_actual('scan',self.selected['entry']['payload'],facts={},build_binding={},max_io=20,timeout_ns=100)
  pending=self.producer.take_pending_events();self.assertEqual(len(pending),1);facts,refs=pmod.consume_original_receipt(pending[0]);self.assertIs(refs['token'],later['token']);facts,refs=pmod.consume_original_receipt(ev);self.assertIs(refs['token'],self.selected['token']);self.assertIs(refs['preparation'],self.prepared);self.assertEqual(calls,[(self.selected['entry']['payload'],self.pump)])
 def test_prepare_failure_latches_unknown_and_never_replays(self):
  calls=[]
  def fail(scanner,payload,**kw):calls.append(payload);raise RuntimeError('prepare failed')
  with patch.object(cm.ChainSessionV2,'owner_work_v1',new_callable=PropertyMock,return_value=True,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare_with_pump',fail,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare',side_effect=AssertionError('selected path used legacy prepare')):
   with self.assertRaises(RuntimeError):self.producer.scan_actual('scan',self.selected['entry']['payload'],facts={},build_binding={},max_io=20,timeout_ns=100)
   self.assertTrue(self.session._unknown)
   with self.assertRaises(ValueError):self.producer.scan_actual('scan',self.selected['entry']['payload'],facts={},build_binding={},max_io=20,timeout_ns=100)
  self.assertEqual(calls,[self.selected['entry']['payload']])
 def test_changed_facts_during_preparation_fail_before_dispatch(self):
  facts={'limit':1};dispatch=[]
  def prepare(scanner,payload,**kw):facts['limit']=2;scanner._result=self.prepared;return self.prepared
  def trace(*args,**kwargs):dispatch.append(True);raise AssertionError('must not dispatch')
  with patch.object(cm.ChainSessionV2,'owner_work_v1',new_callable=PropertyMock,return_value=True,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare_with_pump',prepare,create=True),patch.object(cm.ChainSessionV2,'trace_scan',trace):
   with self.assertRaises(ValueError):self.producer.scan_actual('scan',self.selected['entry']['payload'],facts=facts,build_binding={},max_io=20,timeout_ns=100)
  self.assertFalse(dispatch);self.assertTrue(self.session._unknown)
 def test_default_keeps_synchronous_prepare(self):
  calls=[]
  def prepare(scanner,payload,**kw):calls.append(payload);scanner._result=self.prepared;return self.prepared
  def trace(chain,ident,*args,**kw):return self.helper.issue(chain,ident,'trace_scan',correlation={'status':'FOUR_FRAME_CORRELATION_CONSISTENT'})
  with patch.object(cm.ChainSessionV2,'owner_work_v1',new_callable=PropertyMock,return_value=False,create=True),patch.object(sm.OriginalSourceTraceScan,'prepare',prepare),patch.object(sm.OriginalSourceTraceScan,'prepare_with_pump',side_effect=AssertionError('unexpected selected path'),create=True),patch.object(cm.ChainSessionV2,'trace_scan',trace):
   ev=self.producer.scan_actual('scan',self.selected['entry']['payload'],facts={},build_binding={},max_io=20,timeout_ns=100)
  self.assertEqual(calls,[self.selected['entry']['payload']]);self.assertIs(pmod.consume_original_receipt(ev)[1]['token'],self.selected['token'])
if __name__=='__main__':
 names=('test_selected_pumps_new_history_before_phase_and_retains_selected_sample','test_prepare_failure_latches_unknown_and_never_replays','test_default_keeps_synchronous_prepare','test_changed_facts_during_preparation_fail_before_dispatch')
 suite=unittest.TestSuite(Tests(name) for name in names)
 print('selected_test_ids:',*[t.id() for t in suite],flush=True)
 raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
