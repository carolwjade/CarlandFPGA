"""Safety expectation converted from the old unsafe continuation observer."""
from unittest.mock import patch
import unittest
from competition.deepeye.tests.simulation import test_motion_executor as fixture

class SafeContinuation(unittest.TestCase):
 def setUp(self):self.f=fixture.MotionExecutorTests();self.f.setUp()
 def test_original_continuation_now_requires_new_admission_after_successful_read(self):
  ex=self.f.make();ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  frame=ex.authority_snapshot().frame;phase=ex.passage_state();pose=ex.renderer_view()
  error=MemoryError('same original materialization fault')
  with patch.object(fixture.p,'materialize_committed_transition',side_effect=error):
   with self.assertRaises(MemoryError) as caught:ex.passage_state()
  self.assertIs(caught.exception,error)
  self.assertEqual(ex.passage_state(),phase)  # successful later access is not recovery
  self.assertTrue(ex.controller_view().stopped);self.assertFalse(ex.controller_view().trial_failed)
  with self.assertRaises(ValueError):self.f.prepare(ex)
  self.assertEqual(ex.renderer_view(),pose);self.assertIs(ex.authority_snapshot().frame,frame)
 def test_pending_handle_is_retired_and_cancellation_identity_is_preserved(self):
  ex=self.f.make();ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  pending=self.f.prepare(ex);pose=ex.renderer_view();error=KeyboardInterrupt('local cancellation')
  with patch.object(fixture.p,'materialize_committed_transition',side_effect=error):
   with self.assertRaises(KeyboardInterrupt) as caught:ex.passage_state()
  self.assertIs(caught.exception,error);calls=[]
  with self.assertRaises(ValueError):ex.commit_step(pending,lambda:(calls.append(1),self.f.fence(start=1_020_000_000))[1])
  self.assertEqual(calls,[]);self.assertEqual(ex.renderer_view(),pose)
  self.assertTrue(ex.controller_view().stopped);self.assertFalse(ex.controller_view().trial_failed)
 def test_caught_fault_inside_final_callback_cannot_publish_after_root_revoke(self):
  ex=self.f.make();ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  pending=self.f.prepare(ex);root=ex.authority_snapshot();pose=ex.renderer_view();calls=[]
  def fence():
   calls.append(1)
   try:ex.passage_state()
   except ValueError:pass
   return self.f.fence(start=1_020_000_000)
  with patch.object(fixture.p,'materialize_committed_transition',side_effect=ValueError('local proof validation error')):
   with self.assertRaises(ValueError):ex.commit_step(pending,fence)
  self.assertEqual(calls,[1]);self.assertEqual(ex.renderer_view(),pose)
  self.assertIs(ex.authority_snapshot().frame,root.frame)
  self.assertTrue(ex.controller_view().stopped);self.assertFalse(ex.controller_view().trial_failed)

if __name__=='__main__':unittest.main(verbosity=2)
