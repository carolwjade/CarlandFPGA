"""Synthetic age controls; no native, board, SSH, or authority claims."""
import types, unittest
from unittest.mock import patch
from competition.deepeye.integration import sensor_source
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan

class Producer(types.SimpleNamespace):
 __hash__=object.__hash__

class DemoAgeTests(unittest.TestCase):
 def setUp(self):
  from competition.deepeye.tools.diagnostic import demo30h_age_budget_a as demo
  self.demo=demo
  self.clock=types.SimpleNamespace(metadata={'domain_id':'a'*32})
  self.source=types.SimpleNamespace(clock=self.clock,_start_attempted=False)
  self.world=types.SimpleNamespace(source=self.source,clock=self.clock,operation_id='op-295')
  self.session=Producer(_unknown=False,_closed=False,_dir=types.SimpleNamespace(name='op-295'))
  self.origin=object()
  self.chain=types.SimpleNamespace(clock=self.clock,duration=2_000_000_000,s=self.session,sequence=types.SimpleNamespace(closed=False),_phase_binding=lambda:self.origin)
  self.producer=Producer(_world=self.world,_source=self.source,_chain=self.chain,_clock=self.clock,_session=self.session,_origin=self.origin,_operation='op-295',_scanner=None,_failed=False,_closed=False,_check=lambda:None)
  self.sc=object.__new__(scan.OriginalSourceTraceScan)
  self.sc._functional=self.source;self.sc._clock=self.clock;self.sc._origin=1_000_000_000
  self.patch=patch.object(demo,'_validate_original',return_value=None);self.patch.start();self.addCleanup(self.patch.stop)
  self.cap=demo.select_demo_age_budget(self.world,self.producer,max_source_age_ns=500_000_000)
  demo._bind_scanner(self.cap,self.sc)
  self.producer._scanner=self.sc
  self.sc._demo_age_budget=self.cap
 def payload(self):
  return dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=0,em_tick_ms=None,channel_values=[None,None,None,None],channel_counts=[None,None,None,None],quality=4096)
 def test_opt_in_admission_and_dispatch_freshness(self):
  ledger=sensor_source.SourceLedger(start_tick_ms=0,start_monotonic_ns=self.sc._origin,_demo_age_budget=self.cap,_scanner=self.sc)
  ledger.accept(self.payload(),received_monotonic_ns=1_200_000_000)
  self.assertFalse(ledger.healthy(now_monotonic_ns=1_200_000_000))
  self.sc._work_fresh(0,None,1_200_000_000)
  self.assertEqual(self.cap.max_source_age_ns,500_000_000)
  self.assertFalse(ledger.demo_age_observations[0]['target_100ms_met'])
  self.assertFalse(self.sc.demo_age_observations[0]['target_100ms_met'])
  self.assertEqual(self.sc.demo_age_observations[0]['adc_age_ns'],200_000_000)
 def test_default_expired_future_and_cross_operation_refused(self):
  default=sensor_source.SourceLedger(start_tick_ms=0,start_monotonic_ns=self.sc._origin)
  with self.assertRaises(ValueError):default.accept(self.payload(),received_monotonic_ns=1_200_000_000)
  ledger=sensor_source.SourceLedger(start_tick_ms=0,start_monotonic_ns=self.sc._origin,_demo_age_budget=self.cap,_scanner=self.sc)
  with self.assertRaises(ValueError):ledger.accept(self.payload(),received_monotonic_ns=1_500_000_001)
  with self.assertRaises(ValueError):self.sc._work_fresh(1,None,1_000_000_000)
  self.producer._operation='other'
  with self.assertRaises(ValueError):self.sc._work_fresh(0,None,1_200_000_000)

 def test_wrong_bound_scanner_or_failed_producer_rejected(self):
  self.producer._scanner=object()
  with self.assertRaises(ValueError):self.sc._work_fresh(0,None,1_200_000_000)
  self.producer._scanner=self.sc;self.producer._failed=True
  with self.assertRaises(ValueError):self.sc._work_fresh(0,None,1_200_000_000)

 def test_close_intent_allows_age_observation_until_actual_close_or_unknown(self):
  from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as protocol
  ledger=sensor_source.SourceLedger(start_tick_ms=0,start_monotonic_ns=self.sc._origin,_demo_age_budget=self.cap,_scanner=self.sc)
  # Real protocol state; world/producer and original factory remain synthetic.
  sequence=protocol.Sequence();sequence.initialized=True;self.chain.sequence=sequence
  close=protocol.raw(dict(schema=protocol.SCHEMA,id='close-intent',operation_id='op-295',kind='close',payload={'stop':False}))+b'\n'
  sequence.consume(protocol.decode_request(close,'op-295',None,sequence))
  self.assertTrue(sequence.closed)
  ledger.accept(self.payload(),received_monotonic_ns=1_200_000_000)
  self.sc._work_fresh(0,None,1_200_000_000)
  self.assertEqual(len(ledger.demo_age_observations),1)
  self.assertEqual(len(self.sc.demo_age_observations),1)
  status=protocol.raw(dict(schema=protocol.SCHEMA,id='after-close',operation_id='op-295',kind='status',payload={}))+b'\n'
  with self.assertRaisesRegex(ValueError,'one use request identity'):
   protocol.decode_request(status,'op-295',None,sequence)
  for owner,flag in ((self.producer,'_failed'),(self.producer,'_closed'),(self.session,'_closed'),(self.session,'_unknown')):
   with self.subTest(flag=flag,owner='producer' if owner is self.producer else 'session'):
    setattr(owner,flag,True)
    try:
     with self.assertRaisesRegex(ValueError,'original operation-bound demo age selection required'):
      ledger.accept(dict(self.payload(),adc_tick_ms=10),received_monotonic_ns=1_210_000_000)
     with self.assertRaisesRegex(ValueError,'original operation-bound demo age selection required'):
      self.sc._work_fresh(10,None,1_210_000_000)
    finally:setattr(owner,flag,False)
