"""New software-only call sequence controls, never native Root evidence."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from competition.deepeye.tools import run_causal_functional_chain as chain

class TestFunctionalSource(unittest.TestCase):
 def test_absent_real_owner_rejected(self):
  with self.assertRaises(ValueError): chain.FunctionalSource(None,None,field_policy={})
 def fixture(self):
  f=object.__new__(chain.FunctionalSource);f._thread=__import__('threading').get_ident();f._pending=None;f._last_transition=None;f._start_attempted=True;f._retained_samples=[]
  f.source=SimpleNamespace(state='RUNNING',_completed_handoff=None,poll=lambda:{'tick':1},claim_completed_sample=lambda p:'real-token',release_completed_sample=lambda p:None,_handoff_check=lambda p,c:None)
  f.book=SimpleNamespace(_actor_custody=SimpleNamespace(transitions=[]));f.session=SimpleNamespace(observe_capture=lambda *a,**k:None,_check=lambda:None)
  import json
  f.source._source_book=f.book;f.source._handoff_bytes=lambda p:json.dumps(p,sort_keys=True,separators=(',',':')).encode()
  return f
 def test_capture_once_after_sample(self):
  f=self.fixture();p,token=f.poll_sample();self.assertEqual(token,'real-token')
  with self.assertRaises(ValueError):f.poll_sample()
  with self.assertRaises(ValueError):f.capture(object(),dict(p),candidate={},fields={})
  f.capture(object(),p,candidate={},fields={});self.assertIsNone(f._pending)
 def test_unattached_transition_refused(self):
  f=self.fixture();f.book._actor_custody.transitions.append(object())
  with self.assertRaises(ValueError):f.poll_sample()
 def test_after_transition_gated_sample(self):
  f=self.fixture();transition=object();f._last_transition=transition;f.book._actor_custody.transitions.append(transition)
  with patch.object(chain,'poll_after_finished_transition',return_value=None) as poll:
   self.assertIsNone(f.poll_sample());poll.assert_called_once_with(f.session,transition)
 def test_factory_refuses_missing_adapter(self):
  with self.assertRaises(NotImplementedError):chain.required_external_bindings()
 def test_failed_capture_preserves_handoff(self):
  f=self.fixture();p,token=f.poll_sample();released=[]
  f.source.release_completed_sample=lambda payload:released.append(payload)
  def reject(*a,**k):raise RuntimeError('capture rejected')
  f.session.observe_capture=reject
  with self.assertRaises(RuntimeError):f.capture(object(),p,candidate={},fields={})
  self.assertIs(f._pending[0],p);self.assertEqual(released,[])
 def test_real_projection_arguments_forwarded_without_fabrication(self):
  f=self.fixture();events=[];ref=object();fields={'board':'actual'};view=object();observation=object()
  f.session.observe_admission=lambda r,v:events.append(('admission',r,v))
  f.session.attach_registry=lambda *a,**k:events.append(('registry',a,k))
  f.observe_admission(ref,fields);f.attach_registry(view,{'x':1},1,as_of_qpc_ns=7,observation_ref=observation)
  self.assertIs(events[0][1],ref);self.assertIs(events[0][2],fields)
  self.assertIs(events[1][1][0],view);self.assertIs(events[1][2]['observation_ref'],observation)
 def test_foreign_thread_rejected(self):
  import threading
  f=self.fixture();errors=[]
  def call():
   try:f.poll_sample()
   except Exception as e:errors.append(type(e))
  t=threading.Thread(target=call);t.start();t.join();self.assertEqual(errors,[ValueError])
if __name__=='__main__':unittest.main()
