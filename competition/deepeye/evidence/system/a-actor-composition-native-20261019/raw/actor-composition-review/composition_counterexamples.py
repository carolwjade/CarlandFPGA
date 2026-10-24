"""Independent facade boundaries. All native acquisitions remain original fakes."""
import json,pathlib,threading,unittest
from dataclasses import replace
from unittest.mock import patch
from competition.deepeye.tests.simulation import test_actor_composition as fixture
H=pathlib.Path(__file__).resolve().parent
def save(name,x):(H/(name+'.json')).write_text(json.dumps(x,indent=2),encoding='utf-8')


class CompositionCounterexamples(unittest.TestCase):
 def fx(self):
  f=fixture.ActorCompositionTests();f.setUp();self.addCleanup(f.doCleanups);return f

 def test_unavailable_gate_precedes_invalid_world_registry_and_retention(self):
  f=self.fx();c=fixture.c
  class UnavailableWorld:
   def __getattribute__(self,name):raise AssertionError('world must not be evaluated before unavailable verifier')
  bad=replace(f.config,initial_state=UnavailableWorld(),scene=UnavailableWorld(),model=UnavailableWorld(),budget=UnavailableWorld())
  retained=len(c._RETAINED);f.api.calls.clear()
  with patch.object(c,'ActorRegistry',side_effect=AssertionError('registry before gate')),patch.object(c,'OwnedMotionExecutor',side_effect=AssertionError('executor before gate')):
   with self.assertRaises(c.ActivationUnavailable):c.create_authority(bad)
  self.assertEqual(retained,len(c._RETAINED));self.assertEqual([],f.api.calls)
  save('unavailable-no-acquisition',{'new_retained_roots':len(c._RETAINED)-retained,'fake_native_calls':f.api.calls,'world_evaluated':False,'production_activation':'unavailable'})

 def test_replaced_process_reference_cannot_use_static_channel_life_fallback(self):
  f=self.fx();f.arm();comp=f.comp;original=comp._actor._original_process
  # Validation-boundary injection: change only the current pointer, not the
  # original registry's acquired resource/native identity used for cleanup.
  comp._actor._process=replace(original)
  f.channels.ai_lease=lambda boot,now:fixture.rt.runtime.AiLease(boot,boot.ai_instance,10**20)
  result=f.step()
  self.assertFalse(result.committed);self.assertEqual(0,comp._executor.renderer_view().pose_revision)
  self.assertEqual(1,f.api.calls.count(('terminate',original.native)))
  self.assertIs(comp._registry._owners[0]._original_process,original)
  save('original-reference-no-fallback',{'committed':result.committed,'pose_revision':comp._executor.renderer_view().pose_revision,'state':comp.status().state,'original_cleanup_terminate_calls':f.api.calls.count(('terminate',original.native)),'scope':'private pointer continuity seam, not arbitrary Python mutation security'})

 def test_foreign_veto_during_activation_wait_never_opens_admission(self):
  f=self.fx();f.create();comp=f.comp;errors=[];native_unchanged=[]
  def foreign():
   try:comp.status()
   except fixture.c.CompositionRejected as e:errors.append(str(e))
  def hook():
   before=list(f.api.calls);t=threading.Thread(target=foreign);t.start();t.join();native_unchanged.append(before==f.api.calls)
  f.api.wait_hook=hook
  with self.assertRaises(fixture.c.CompositionRejected):comp.accept_boot(f.channels.ready)
  self.assertEqual([True],native_unchanged);self.assertEqual(1,len(errors))
  self.assertEqual(0,comp._executor.renderer_view().pose_revision)
  self.assertTrue(comp._runtime._latched);self.assertTrue(comp._executor.controller_view().stopped)
  self.assertNotEqual('ACTIVE',comp.status().state)
  self.assertIs(comp._registry._owners[0],comp._actor)
  save('activation-foreign-wait',{'foreign_rejection':errors,'foreign_native_effects':not all(native_unchanged),'state':comp.status().state,'pose_revision':comp._executor.renderer_view().pose_revision,'original_owner_retained':True})

 def test_callback_failure_after_successor_preserves_second_target_and_quarantine(self):
  f=self.fx();f.activate();comp=f.comp;old=comp._boot
  successor=replace(old,generation=2,context_json=fixture.rt.encode(dict(fixture.rt.PC,session=8)))
  original=comp._runtime.stop;failure=OSError('private callback failed after advancing executor')
  def stop(reason):
   original(reason);comp._executor.activate_boot(successor);raise failure
  with patch.object(comp._runtime,'stop',stop):self.assertIsNone(comp.stop('explicit stop'))
  self.assertIs(comp._executor._root.boot,successor);self.assertFalse(comp._executor.controller_view().stopped)
  self.assertIn(failure,comp._errors);self.assertEqual('QUARANTINED',comp.status().state)
  self.assertEqual(1,f.api.calls.count(('terminate',300)))
  native=list(f.api.calls);comp.close('late close');self.assertEqual(native,f.api.calls)
  self.assertFalse(comp._executor.controller_view().stopped)
  save('callback-error-successor',{'state':comp.status().state,'callback_error_retained':failure in comp._errors,'successor_stopped':comp._executor.controller_view().stopped,'native_cleanup_replayed':native!=f.api.calls})

 def test_completed_cas_plus_reentrant_late_veto_and_cleanup_failure_keeps_fact(self):
  f=self.fx();f.arm();comp=f.comp;original=comp._runtime.step
  before=comp._executor.renderer_view().pose
  def after_commit(**kwargs):
   result=original(**kwargs);self.assertTrue(result.committed)
   f.api.close_ok=False
   try:comp.close('late reentry after observed actual CAS')
   except fixture.c.CompositionRejected:pass
   return result
  with patch.object(comp._runtime,'step',after_commit):result=f.step()
  self.assertTrue(result.committed);self.assertEqual(1,result.pose_revision)
  self.assertEqual(1,comp._executor.renderer_view().pose_revision);self.assertNotEqual(before,comp._executor.renderer_view().pose)
  self.assertEqual('QUARANTINED',comp.status().state);self.assertTrue(comp._actor._resources.unresolved)
  self.assertFalse(f.step().committed);self.assertEqual(1,comp._executor.renderer_view().pose_revision)
  self.assertIs(comp._registry._owners[0],comp._actor)
  save('commit-plus-quarantine',{'reported_committed':result.committed,'reported_revision':result.pose_revision,'actual_revision':comp._executor.renderer_view().pose_revision,'state':comp.status().state,'unresolved':[r.resource_id for r in comp._actor._resources.unresolved],'original_owner_retained':True})

 def test_progress_loss_after_prepare_is_documented_remaining_fence_dependency(self):
  f=self.fx();f.arm();comp=f.comp;original=comp._executor.prepare_step
  def lose_progress(*args):
   prepared=original(*args);f.channels.healthy=False;return prepared
  with patch.object(comp._executor,'prepare_step',lose_progress):result=f.step()
  # Explicit negative integration witness, not a passing AI-safety claim.
  # Current production remains unavailable; docs disclose that a synthetic
  # pre-step checkpoint is not final-fence measured progress/deadline evidence.
  self.assertTrue(result.committed);self.assertEqual(1,comp._executor.renderer_view().pose_revision)
  with self.assertRaises(fixture.c.CompositionRejected):comp.poll()
  save('progress-final-fence-gap',{'committed_after_synthetic_progress_loss':result.committed,'actual_revision':comp._executor.renderer_view().pose_revision,'state_after_owner_poll':comp.status().state,'scope':'documented missing final-fence progress producer, not production acceptance'})


if __name__=='__main__':unittest.main()
