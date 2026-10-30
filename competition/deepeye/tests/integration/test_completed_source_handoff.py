import unittest
from competition.deepeye.tools.diagnostic import causal_pl_exchange as c

class Profile:
 def acquire_em(self,*a,**k): pass
 def sample_adc(self,tick,**kw):
  class Sample:
   def to_payload(self): return {'tick':tick,'nested':[1]}
  return Sample()
class Book:
 software_fixture_only=True
 def __init__(self,source): self.source=source; self.fail_finish=False; self.tokens=[]
 def start(self): pass
 def open_sample(self,tick,now):
  t=object();self.tokens.append(t);return t
 def read_pose(self,token,kind): return None
 def begin_adc(self,token): return object()
 def end_adc(self,token,handle): pass
 def finish_sample(self,token,payload):
  if self.fail_finish: raise RuntimeError('finish failed')
 def fail(self,reason): pass
 def retire(self,reason): pass
class Tests(unittest.TestCase):
 def make(self,enabled=True):
  s=c._CausalSourcePump(Profile(),lambda:None,lambda *a:0); b=Book(s);s._bind_software_source_book_for_test(b)
  if enabled:s.enable_completed_sample_handoff()
  clock=[0];s.start(0,lambda:clock[0]);return s,b,clock
 def test_default_and_enable_constraints(self):
  s,b,t=self.make(False);self.assertEqual(s.poll()['tick'],0)
  with self.assertRaises(ValueError):s.enable_completed_sample_handoff()
  s=c._CausalSourcePump(Profile(),lambda:None,lambda *a:0)
  with self.assertRaises(ValueError):s.enable_completed_sample_handoff()
 def test_identity_one_slot_and_release(self):
  s,b,t=self.make();p=s.poll()
  with self.assertRaises(ValueError):s.claim_completed_sample(dict(p))
  token=s.claim_completed_sample(p);self.assertIs(token,b.tokens[0])
  with self.assertRaises(ValueError):s.claim_completed_sample(p)
  with self.assertRaises(ValueError):s.poll()
  s.release_completed_sample(p);t[0]=10_000_000;p2=s.poll();self.assertEqual(p2['tick'],10)
 def test_mutation_and_failure(self):
  s,b,t=self.make();p=s.poll();p['nested'].append(2)
  with self.assertRaises(ValueError):s.claim_completed_sample(p)
  s,b,t=self.make();p=s.poll();s.claim_completed_sample(p);p['nested'].append(2)
  with self.assertRaises(ValueError):s.release_completed_sample(p)
  s,b,t=self.make();b.fail_finish=True
  with self.assertRaises(RuntimeError):s.poll()
  self.assertIsNone(s._completed_handoff)
 def test_grid(self):
  from competition.deepeye.simulation.authority.source_projection_v1.source_poll import _not_before
  self.assertEqual(_not_before(0,201_000_000),210_000_000)
  self.assertEqual(_not_before(7,20_000_007),20_000_007)
  with self.assertRaises(ValueError):_not_before(10,9)
 def test_foreign_thread_rejected(self):
  import threading
  s,b,t=self.make();p=s.poll();errors=[]
  def attempt():
   try:s.claim_completed_sample(p)
   except Exception as e:errors.append(type(e))
  thread=threading.Thread(target=attempt);thread.start();thread.join()
  self.assertEqual(errors,[ValueError]);self.assertIs(s.claim_completed_sample(p),b.tokens[0]);s.release_completed_sample(p)
 def test_transition_grid_control_is_software_only(self):
  from types import SimpleNamespace
  from competition.deepeye.simulation.authority.source_projection_v1.provider import ProjectionSession
  from competition.deepeye.simulation.authority.source_projection_v1.source_poll import poll_after_finished_transition
  from competition.deepeye.simulation.authority._actor_source_custody import _Transition
  s,b,clock=self.make();root=object();custody=SimpleNamespace(pending=None,transitions=[])
  b._actor_custody=custody;b._root=root
  tr=object.__new__(_Transition);tr.custody=custody;tr.closed=True;tr.record={'state':'COMPLETE','completion_observed_qpc_ns':201_000_000};custody.transitions.append(tr)
  session=object.__new__(ProjectionSession);session._book=b;session._link=SimpleNamespace(source=s);session._producer=SimpleNamespace(_actions=[(tr,root,None,{})]);session._check=lambda:None
  clock[0]=202_000_000;self.assertIsNone(poll_after_finished_transition(session,tr));self.assertEqual(s._count,0)
  clock[0]=210_000_000;p,token=poll_after_finished_transition(session,tr);self.assertEqual(p['tick'],210);self.assertIs(token,b.tokens[0]);s.release_completed_sample(p)
if __name__=='__main__':unittest.main()
