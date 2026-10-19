"""Independent bounded numerical checks; all source/runtime evidence is fixture-only."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from competition.deepeye.tests.simulation import test_motion_executor as fixture

m,p,s=fixture.m,fixture.p,fixture.s
DT=fixture.DT

class IndependentMotion(unittest.TestCase):
 def setUp(self):
  self.f=fixture.MotionExecutorTests();self.f.setUp()
 def test_success_suffix_has_no_geometric_hash_materialization_or_replace_call(self):
  ex=self.f.make();h=self.f.prepare(ex);calls=[];fenced=False
  originals=[(m.cp,'CanonicalPath'),(m.p,'materialize_committed_transition'),(m.w,'digest'),(m.s,'certify_scene'),(m.hashlib,'sha256'),(m,'replace')]
  from contextlib import ExitStack
  def guard(function):
   def call(*a,**kw):
    self.assertFalse(fenced,'expensive work happened after final callback');return function(*a,**kw)
   return call
  def final():
   nonlocal fenced
   calls.append(1);fenced=True;return self.f.fence()
  with ExitStack() as stack:
   for module,name in originals:stack.enter_context(patch.object(module,name,side_effect=guard(getattr(module,name))))
   receipt=ex.commit_step(h,final)
  self.assertEqual(calls,[1]);self.assertEqual(receipt.pose_revision,1)
 def test_gap_mapping_retains_prior_events_and_original_anchor(self):
  ex=self.f.make((0,0,15.522));first_handle=self.f.prepare(ex)
  anchor=ex.prepared_audit(first_handle).relative
  ex.commit_step(first_handle,lambda:self.f.fence(start=1_000_000_000))
  first=ex.passage_state();second_handle=self.f.prepare(ex)
  ex.commit_step(second_handle,lambda:self.f.fence(start=1_300_000_000))
  second=ex.passage_state()
  self.assertEqual(second.history[:len(first.history)],first.history)
  self.assertEqual(anchor.anchor_ns,0)
  self.assertEqual(anchor.preview.candidate.monotonic_ns,DT)
  self.assertEqual(second.monotonic_ns,1_310_000_000)
  self.assertEqual(ex.renderer_view().pose_revision,2)
 def test_retired_pending_handle_cannot_reach_fence_or_revive_new_pending(self):
  ex=self.f.make();old=self.f.prepare(ex);new=self.f.prepare(ex);calls=[]
  with self.assertRaises(ValueError):ex.commit_step(old,lambda:(calls.append(1),self.f.fence())[1])
  with self.assertRaises(ValueError):ex.commit_step(new,lambda:(calls.append(1),self.f.fence())[1])
  self.assertEqual(calls,[]);self.assertEqual(ex.renderer_view().pose_revision,0)
 def test_malformed_or_wrong_identity_fence_does_not_move_and_is_single_attempt(self):
  for changes in ({'boot':replace(self.f.f.binding)}, {'command_seq':True}, {'checked_ns':True},
                  {'step_end_ns':1_009_999_999},{'deadline_ns':1_010_000_000},
                  {'deadline_ns':2_000_000_001},{'checked_ns':999_999_999,'step_end_ns':1_009_999_999}):
   with self.subTest(changes=changes):
    ex=self.f.make();h=self.f.prepare(ex);calls=[]
    def final():calls.append(1);return replace(self.f.fence(),**changes)
    with self.assertRaises(ValueError):ex.commit_step(h,final)
    with self.assertRaises(ValueError):ex.commit_step(h,final)
    self.assertEqual(calls,[1]);self.assertEqual(ex.renderer_view().pose_revision,0)
    self.assertTrue(ex.controller_view().stopped)
 def test_world_invalidation_in_callback_preserves_pose_and_retires_world(self):
  ex=self.f.make();h=self.f.prepare(ex);pose=ex.renderer_view().pose
  def final():ex.invalidate_world('fixture scene epoch advanced');return self.f.fence()
  with self.assertRaises(ValueError):ex.commit_step(h,final)
  with self.assertRaises(ValueError):ex.activate_boot(self.f.f.boot_binding(generation=2,session=8))
  self.assertEqual(ex.renderer_view().pose,pose);self.assertEqual(ex.renderer_view().pose_revision,0)
 def test_trial_latch_and_committed_history_survive_stop_and_new_boot(self):
  ex=self.f.make((0,0,15.522));ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  history=ex.passage_state().history;ex.revoke('fixture proven violation',trial_failed=True)
  ex.activate_boot(self.f.f.boot_binding(generation=2,session=8))
  self.assertTrue(ex.controller_view().trial_failed);self.assertTrue(ex.controller_view().stopped)
  self.assertEqual(ex.passage_state().history,history);self.assertEqual(ex.renderer_view().pose_revision,1)
 def test_overlapping_committed_interval_is_rejected_without_second_pose(self):
  ex=self.f.make();ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  with self.assertRaises(ValueError):ex.commit_step(self.f.prepare(ex),lambda:self.f.fence(start=1_009_999_999))
  self.assertEqual(ex.renderer_view().pose_revision,1)
 def test_later_materialization_failure_latches_stop_without_new_motion(self):
  ex=self.f.make();ex.commit_step(self.f.prepare(ex),lambda:self.f.fence())
  pose=ex.renderer_view()
  with patch.object(m.p,'materialize_committed_transition',side_effect=MemoryError('independent materialization allocation fault')):
   with self.assertRaises(MemoryError):ex.passage_state()
  self.assertEqual(ex.renderer_view(),pose)
  self.assertTrue(ex.controller_view().stopped,'authority materialization error did not fail-stop the store')

if __name__=='__main__':unittest.main(verbosity=2)
