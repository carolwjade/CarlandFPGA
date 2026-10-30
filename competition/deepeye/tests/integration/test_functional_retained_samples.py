"""New retained-sample controls; no actual Root, board, model or old tests."""
import threading,unittest
from types import SimpleNamespace
from competition.deepeye.tools import run_causal_functional_chain as c
class Tests(unittest.TestCase):
 def fixture(self):
  f=object.__new__(c.FunctionalSource);f._thread=threading.get_ident();f._pending=None;f._last_transition=None;f._start_attempted=True;f._retained_samples=[]
  f.book=SimpleNamespace(_actor_custody=SimpleNamespace(transitions=[]));counter=[0];held=[None];captures=[]
  def poll():
   counter[0]+=1;held[0]={'tick':counter[0]};return held[0]
  def claim(p):return object()
  def release(p):held[0]=None
  import json
  raw=lambda p:json.dumps(p,sort_keys=True,separators=(',',':')).encode()
  f.source=SimpleNamespace(_source_book=f.book,state='RUNNING',poll=poll,claim_completed_sample=claim,release_completed_sample=release,_handoff_bytes=raw,_handoff_check=lambda p,claimed:None)
  f.session=SimpleNamespace(_check=lambda:None,observe_capture=lambda ref,token,**kw:captures.append((ref,token)))
  return f,captures
 def test_release_keeps_original_for_later_capture(self):
  f,captures=self.fixture();p1,t1=f.poll_sample();f.release_sample(p1);p2,t2=f.poll_sample();f.release_sample(p2)
  ref=object();f.capture(ref,p1,candidate={},fields={});self.assertIs(captures[0][0],ref);self.assertIs(captures[0][1],t1)
  with self.assertRaises(ValueError):f.capture(object(),p1,candidate={},fields={})
  self.assertIs(f._retained_samples[1]['token'],t2)
 def test_held_sample_and_mutations_fail_closed(self):
  f,captures=self.fixture();p,t=f.poll_sample()
  with self.assertRaises(ValueError):f.poll_sample()
  with self.assertRaises(ValueError):f.release_sample(dict(p))
  f.release_sample(p);p['tick']=99
  with self.assertRaises(ValueError):f.capture(object(),p,candidate={},fields={})
  self.assertEqual(captures,[])
 def test_capture_then_release_and_transition_keeps_history(self):
  f,captures=self.fixture();p,t=f.poll_sample();f.capture(object(),p,candidate={},fields={})
  self.assertIsNone(f._pending);self.assertIs(f._retained_samples[0]['token'],t)
  transition=object();f.session.observe_finished_transition=lambda *a,**k:None
  f.observe_finished_transition(transition,successor_root=object(),fields={});self.assertIs(f._retained_samples[0]['payload'],p)
if __name__=='__main__':unittest.main()
