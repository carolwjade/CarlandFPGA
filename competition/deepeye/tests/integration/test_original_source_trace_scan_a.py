"""New synthetic producer controls; no Root/board/old experiment."""
import json, unittest
from pathlib import Path
from competition.deepeye.integration import sensor_source as sensor
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan
from competition.deepeye.tools.diagnostic import functional50_exchange_a as exchange

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.bundle=exchange.load_selected(Path.cwd())
 def fixture(self):
  lineage=dict(operation_id='fixture',request_id='fixture-request',request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='fixture-boot',session_id=4,tag=5,trigger_id=6,generation=1,request_seq=7,capture_seq=8)
  facts=dict(work_id='fixture-work',declared_by='software-control',scan_id_uint63=1,view=2,frame_seq_start=5,sample_index=8,binding_receipt_id='fixture-bind',lineage=lineage)
  build=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='fixture',request_hash='a'*64)
  ledger=sensor.SourceLedger(start_tick_ms=0,start_monotonic_ns=1000000000)
  for tick in range(0,100,10):
   valid=tick>=90;payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=tick,em_tick_ms=None,channel_values=[None,None,None,.1 if valid else None],channel_counts=[None,None,None,round(.1/2*4095) if valid else None],quality=4096+(8 if valid else 0))
   ledger.accept(payload,received_monotonic_ns=1000000000+tick*1000000+1)
  raw=scan._raw(payload);draft=dict(status='complete',tick_ms=90,source_count=10,finish_qpc_ns=1090000001,adc={'begin_qpc_ns':1090000000,'end_qpc_ns':1090000001},held_em_association='unavailable;original_em_invalid_or_source_fault')
  return payload,raw,draft,facts,build,ledger
 def test_four_full_companions_and_original_normalizer(self):
  payload,raw,draft,facts,build,ledger=self.fixture()
  request,source,companions=scan._construct_bytes(payload,raw,draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
  self.assertEqual(source,raw);self.assertEqual(len(companions),4)
  for i,body in enumerate(companions):
   c=json.loads(body);self.assertEqual(c['payload_utf8_hex'],raw.hex());self.assertEqual(c['book_draft'],draft);self.assertEqual(c['channel'],i)
  p=self.bundle.adapter.prepare_bytes(request,source,companions,build_binding=build)
  self.assertEqual(p.status,'TRACE94_PLAN_PREPARED');self.assertEqual(p.original.companions,companions)
  n=p.plan.facts()['scan'];self.assertEqual([x['raw_sample_uint16'] for x in n['lanes']],[None,None,None,205]);self.assertEqual([x['staged_quality_uint4'] for x in n['lanes']],[8,8,8,9])
  self.assertEqual(n['lanes'][3]['source_qpc_ns'],1090000000);self.assertEqual(ledger.snapshot.accepted_records,10)
 def test_missing_history_cannot_start_from_ninety(self):
  payload,raw,draft,facts,build,ledger=self.fixture();empty=sensor.SourceLedger(start_tick_ms=0,start_monotonic_ns=1000000000)
  with self.assertRaises(ValueError):empty.accept(payload,received_monotonic_ns=1090000001)
 def test_frame_wrap_and_changed_payload_rejected(self):
  payload,raw,draft,facts,build,ledger=self.fixture();facts['frame_seq_start']=65533
  with self.assertRaises(ValueError):scan._construct_bytes(payload,raw,draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
  facts['frame_seq_start']=5;payload['quality']=0
  with self.assertRaises(ValueError):scan._construct_bytes(payload,raw,draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
 def test_original_held_em_nominal_mapping(self):
  payload,raw,draft,facts,build,ledger=self.fixture()
  payload['em_tick_ms']=50;payload['channel_values']=[0.0,0.0,0.0,0.1]
  payload['channel_counts']=[round((0.0-lo)/(hi-lo)*4095) for lo,hi in sensor.LIMITS[:3]]+[205]
  payload['quality']=7+8+0x700;raw=scan._raw(payload)
  request,source,companions=scan._construct_bytes(payload,raw,draft,1000000000,'a'*32,1090000001,1090000002,facts,'SYNTHETIC_TEST')
  p=self.bundle.adapter.prepare_bytes(request,source,companions,build_binding=build)
  self.assertEqual(p.status,'TRACE94_PLAN_PREPARED');lanes=p.plan.facts()['scan']['lanes']
  self.assertEqual([lane['staged_quality_uint4'] for lane in lanes],[5,5,5,1])
  self.assertEqual([lane['source_qpc_ns'] for lane in lanes],[1050000000]*3+[1090000000])
 def test_software_sequence_refuses_skipping_original_entry(self):
  from types import SimpleNamespace
  from unittest.mock import patch
  payload,_,_,_,_,_=self.fixture();payload['adc_tick_ms']=0;payload['channel_values']=[None]*4;payload['channel_counts']=[None]*4;payload['quality']=4096
  raw=scan._raw(payload);book=SimpleNamespace(_samples=[])
  class Token:pass
  token=Token();token._book=book;token._ended=True;token._draft=dict(status='complete',tick_ms=0,source_count=1,finish_qpc_ns=1000000001,canonical_source_hex=raw.hex(),source_sha256=scan._sha(raw));book._samples.append(token._draft)
  first=dict(book=book,payload=payload,token=token,raw=raw);other=dict(book=book,payload=dict(payload),token=object(),raw=raw);skipped=dict(book=book,payload=dict(payload),token=object(),raw=raw)
  f=SimpleNamespace(_retained_samples=[first,skipped,other]);f._retained_sample=lambda p: next(e for e in f._retained_samples if e['payload'] is p)
  producer=object.__new__(scan.OriginalSourceTraceScan);producer._functional=f;producer._book=book;producer._clock=lambda:1000000001;producer._ledger=sensor.SourceLedger(start_tick_ms=0,start_monotonic_ns=1000000000);producer._admitted=[];producer._failed=False
  with patch.object(scan.OriginalSourceTraceScan,'_check',lambda self:None),patch.object(scan.root_source_book,'_Sample',Token):
   producer.admit(payload);self.assertEqual(producer._ledger.snapshot.accepted_records,1)
   with self.assertRaises(ValueError):producer.admit(other['payload'])
   self.assertTrue(producer._failed)
if __name__=='__main__':unittest.main()
