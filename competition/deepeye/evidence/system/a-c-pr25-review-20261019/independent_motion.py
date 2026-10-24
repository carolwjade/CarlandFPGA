import importlib.util,json,sys,unittest
from pathlib import Path
P=Path(sys.argv.pop(1))
sys.path.insert(0,str(P))
s=importlib.util.spec_from_file_location('current_fixtures',P/'tests/ai/control_broker/test_motion_request.py')
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
C=sys.modules['ai_pc.control_broker.motion_request']

class IndependentMotion(unittest.TestCase):
 def setup_adapter(self,callback):
  class V:
   def verify_motion(v,check):return callback(check)
  a=C.MotionRequestAdapter(context=f.CONTEXT,verifier=V());a.register_observation(f.observation());return a
 def test_prior_nested_stop_witness_now_blocks_outer(self):
  stops=[]
  a=self.setup_adapter(lambda check:stops.append(a.safe_stop(now_ns=check.now_ns)))
  result=f.submit(a,f.candidate(10))
  self.assertIsNone(result.request_bytes);self.assertEqual(result.reason,'superseded_during_verification')
  self.assertEqual((stops[0].candidate_id,stops[0].command_seq),(11,0))
  self.assertEqual(json.loads(stops[0].request_bytes)['target']['action'],0)
  with self.assertRaises(C.MotionRequestError):f.submit(a,f.candidate(10))
 def test_prior_retained_timing_witness_now_detached(self):
  checks=[];a=self.setup_adapter(lambda check:checks.append(check));r=f.submit(a)
  original=r.timing.deadline_ns
  object.__setattr__(checks[0].timing,'deadline_ns',original+999_000_000_000)
  self.assertEqual(r.timing.deadline_ns,original)
 def test_stop_then_exception_keeps_retirement_and_sequence(self):
  stops=[]
  def callback(check):
   stops.append(a.safe_stop(now_ns=21*f.MS));raise C.RuntimeBlocked('after STOP')
  a=self.setup_adapter(callback);r=f.submit(a,f.candidate(10));self.assertIsNone(r.request_bytes)
  next_stop=a.safe_stop(now_ns=22*f.MS)
  self.assertEqual((next_stop.candidate_id,next_stop.command_seq),(12,1))
  self.assertEqual(r.reason,'superseded_during_verification')
 def test_blocked_newer_candidate_also_retires_older_outer(self):
  nested=[]
  def callback(check):
   doc=f.candidate(20,seq=999);nested.append(f.submit(a,doc))
  a=self.setup_adapter(callback);r=f.submit(a,f.candidate(10))
  self.assertIsNone(r.request_bytes);self.assertIsNone(nested[0].request_bytes)
  stop=a.safe_stop(now_ns=21*f.MS);self.assertEqual((stop.candidate_id,stop.command_seq),(21,0))
 def test_model_stop_candidate_also_supersedes_outer(self):
  nested=[]
  def callback(check):nested.append(f.submit(a,f.candidate(12,action=0,speed=0,duration=0,seq=None)))
  a=self.setup_adapter(callback);r=f.submit(a,f.candidate(10))
  self.assertIsNone(r.request_bytes);self.assertEqual(nested[0].command_seq,0)
  self.assertEqual(json.loads(nested[0].request_bytes)['target']['action'],0)
 def test_callback_context_observation_and_timing_aliases_stay_detached(self):
  checks=[]
  def callback(check):
   checks.append(check)
   for obj,name,val in [(check.context,'session',999),(check.observation.context,'session',998),
                        (check.observation,'sample_lower_ns',99_000_000_000),(check.timing,'sample_lower_ns',88_000_000_000)]:
    object.__setattr__(obj,name,val)
  a=self.setup_adapter(callback);r=f.submit(a)
  self.assertEqual(json.loads(r.request_bytes)['context']['session'],42)
  self.assertEqual(r.timing.sample_lower_ns,0);self.assertEqual(a.retained_observations[0].sample_lower_ns,0)
  self.assertEqual(r.timing.deadline_ns,1020*f.MS)
 def test_new_observation_supersedes_outer_but_exact_duplicate_does_not(self):
  for changed in (False,True):
   def callback(check):a.register_observation(f.observation(sequence=8,ordinal=70001,tick=101,lower=f.MS) if changed else f.observation())
   a=self.setup_adapter(callback);r=f.submit(a)
   self.assertEqual(r.request_bytes is None,changed)
 def test_command_exhaustion_stop_still_revokes_outer_without_old_output(self):
  def callback(check):
   a._next_command_seq=65536
   stop=a.safe_stop(now_ns=check.now_ns)
   self.assertIsNone(stop.request_bytes)
  a=self.setup_adapter(callback);r=f.submit(a,f.candidate(10))
  self.assertIsNone(r.request_bytes);self.assertEqual(r.reason,'superseded_during_verification')
  with self.assertRaises(C.MotionRequestError):f.submit(a,f.candidate(11))

if __name__=='__main__':unittest.main(verbosity=2)
