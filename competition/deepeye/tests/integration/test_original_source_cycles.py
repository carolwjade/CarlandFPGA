"""New source-cycle software controls; no native source or board."""
import unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan, functional50_b131_loader as loader

class Clock:
 def __init__(self):self.now=1000000000;self.metadata={'domain_id':'a'*32}
 def __call__(self):return self.now
class Book:
 def __init__(self):self._samples=[];self._origin=1000000000;self._active=None
 def _check(self):pass
class Token:pass
class Source:
 def __init__(self,book,clock):self.state='RUNNING';self._clock=clock;self._source_book=book;self._origin=book._origin;self._count=0
 def _handoff_bytes(self,payload):return scan._raw(payload)
class Functional:
 def __init__(self):
  self.clock=Clock();self.book=Book();self.source=Source(self.book,self.clock);self.book._source=self.source;self.book._clock=self.clock;self._retained_samples=[]
 def _check_thread(self):pass
 def _retained_sample(self,payload):
  matches=[v for v in self._retained_samples if v['payload'] is payload]
  if len(matches)!=1:raise ValueError('original identity required')
  return matches[0]
 def add(self,tick):
  valid=tick>=90;payload=dict(profile_id='deepeye_forward_profile_candidate_v1',profile_status='candidate_only',profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',source_mode='twin_fixture',adc_tick_ms=tick,em_tick_ms=None,channel_values=[None,None,None,.1 if valid else None],channel_counts=[None,None,None,205 if valid else None],quality=4096+(8 if valid else 0))
  raw=scan._raw(payload);self.source._count+=1;self.clock.now=self.book._origin+tick*1000000+1
  token=Token();token._book=self.book;token._ended=True;token._draft=dict(status='complete',tick_ms=tick,source_count=self.source._count,finish_qpc_ns=self.clock.now,canonical_source_hex=raw.hex(),source_sha256=scan._sha(raw),adc={'begin_qpc_ns':self.clock.now-1,'end_qpc_ns':self.clock.now})
  self.book._samples.append(token._draft);self._retained_samples.append(dict(book=self.book,payload=payload,token=token,raw=raw));return payload

def facts(n):
 lineage=dict(operation_id='fixture',request_id='request-'+str(n),request_hash='a'*64,tested_commit='b'*40,build_id_hex128='c'*32,boot_id='fixture-boot',session_id=4,tag=5+n,trigger_id=6+n,generation=1,request_seq=7+n,capture_seq=8+n)
 return dict(work_id='fixture-work',declared_by='software-control',scan_id_uint63=1+n,view=2,frame_seq_start=5+n*4,sample_index=8+n,binding_receipt_id='fixture-bind-'+str(n),lineage=lineage)
BINDING=dict(canonical_build_id_full_sha256='c'*64,source_closure_file_sha256='d'*64,operation_id='fixture',request_hash='a'*64)
class Controls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.bundle=loader.load_selected(Path.cwd())
 def make(self):
  f=Functional();p=scan.OriginalSourceTraceScan(f,self.bundle,source_scan_cycle_v2=True)
  for tick in range(0,100,10):v=f.add(tick);p.admit(v)
  return f,p,v
 def test_two_original_slots_one_ledger(self):
  f,p,first=self.make();ledger=p._ledger;origin=p._origin;book=p._book;token=f._retained_samples[-1]['token']
  a=p.prepare(first,facts=facts(0),build_binding=BINDING);self.assertEqual(a.status,'TRACE94_PLAN_PREPARED')
  second=f.add(100);p.admit(second);b=p.prepare(second,facts=facts(1),build_binding=BINDING)
  self.assertEqual(b.status,'TRACE94_PLAN_PREPARED');self.assertIs(p._ledger,ledger);self.assertIs(p._book,book);self.assertEqual(p._origin,origin);self.assertEqual(ledger.snapshot.accepted_records,11);self.assertIs(p._admitted[9]['token'],token);self.assertEqual(len(p._attempts),2);self.assertNotEqual(p._attempts[0][0],p._attempts[1][0]);self.assertNotEqual(p._attempts[0][1],p._attempts[1][1]);self.assertTrue(p._prepared)
  with self.assertRaises(ValueError):p.prepare(second,facts=facts(1),build_binding=BINDING)
 def test_duplicate_and_missing_admission_retire(self):
  f,p,first=self.make();p.prepare(first,facts=facts(0),build_binding=BINDING)
  with self.assertRaises(ValueError):p.prepare(first,facts=facts(1),build_binding=BINDING)
  self.assertTrue(p._failed);self.assertEqual(p._prepare_count,2)
  f,p,first=self.make();p.prepare(first,facts=facts(0),build_binding=BINDING)
  f.add(100);target=f.add(110)
  with self.assertRaises(ValueError):p.admit(target)
  self.assertTrue(p._failed)
 def test_expired_sample_fails_closed(self):
  f,p,first=self.make();p.prepare(first,facts=facts(0),build_binding=BINDING);second=f.add(100);p.admit(second);f.clock.now=f.book._origin+201000001
  with self.assertRaisesRegex(ValueError,'expired'):p.prepare(second,facts=facts(1),build_binding=BINDING)
  self.assertTrue(p._failed);self.assertEqual(p._prepare_count,2)
 def test_changed_history_token_rejected(self):
  f,p,first=self.make();p.prepare(first,facts=facts(0),build_binding=BINDING);second=f.add(100);p.admit(second)
  f._retained_samples[0]['token']._ended=False
  with self.assertRaisesRegex(ValueError,'history token'):p.prepare(second,facts=facts(1),build_binding=BINDING)
  self.assertTrue(p._failed)
 def test_default_remains_one_attempt(self):
  f=Functional();p=scan.OriginalSourceTraceScan(f,self.bundle)
  for tick in range(0,100,10):v=f.add(tick);p.admit(v)
  p.prepare(v,facts=facts(0),build_binding=BINDING)
  with self.assertRaises(ValueError):p.admit(v)

if __name__=='__main__':unittest.main()
