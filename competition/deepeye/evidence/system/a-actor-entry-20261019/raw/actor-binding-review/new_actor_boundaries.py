"""Additional software boundaries using existing fake native seams only."""
from dataclasses import replace
import pathlib,json,threading,unittest
from unittest.mock import patch
from competition.deepeye.tests.simulation import test_actor_owner as owner_fixture
from competition.deepeye.tests.simulation import test_actor_lifetime as lifetime_fixture
from competition.deepeye.simulation.isolation import actor_owner as actor_module
H=pathlib.Path(__file__).resolve().parent
def save(name,x):(H/(name+'.json')).write_text(json.dumps(x,indent=2),encoding='utf-8')


class MoreBindingBoundaries(unittest.TestCase):
 def fixture(self,bound=True):
  f=lifetime_fixture.ActorLifetimeTests() if bound else owner_fixture.OwnerFixture()
  f.setUp();self.addCleanup(f.doCleanups);return f
 def replace_actor(self,f):
  fresh=f.launch();f.f.binding=replace(f.f.boot_binding(generation=2,session=8),ai_instance=fresh.instance_id)
  f.f.activate();f.ex.activate_boot(f.f.binding);fresh.bind_verified_boot(f.f.binding,runtime=f.f.owner,executor=f.ex)
  f.f.provider.ai_lease=fresh.ai_lease;f.f.observe();event=f.f.command();f.ex.admit_command(f.f.binding,event.raw)
  return fresh

 def test_stop_advances_both_targets_then_BaseException_does_not_stop_successor(self):
  f=self.fixture();old=f.actor;primary=OSError('original sample boundary failure')
  class CallbackAbort(BaseException):pass
  abort=CallbackAbort('callback aborted after both targets advanced')
  boot=replace(f.f.boot_binding(generation=2,session=8),ai_instance='future fixture identity, no real AI')
  original_stop=old._stop
  def advance_then_fail(reason):
   original_stop(reason)
   f.f.owner.boot(boot);f.ex.activate_boot(boot)
   raise abort
  old._stop=advance_then_fail
  def fail_wait():raise primary
  f.api.wait_hook=fail_wait
  with self.assertRaises(OSError) as caught:f.sample()
  self.assertIs(caught.exception,primary);self.assertIs(old._primary_error,primary)
  self.assertIn(abort,old._callback_errors)
  self.assertIs(f.f.owner._boot,boot);self.assertIs(f.ex.authority_snapshot().boot,boot)
  self.assertFalse(f.f.owner._latched);self.assertFalse(f.ex.controller_view().stopped)
  old.close('retire erroring original binding')
  self.assertEqual('QUARANTINED',old.state);self.assertTrue(old._cleanup_result.resources_complete)
  self.assertIs(old._primary_error,primary)
  self.assertFalse(f.f.owner._latched);self.assertFalse(f.ex.controller_view().stopped)
  save('callback-abort-after-target-advance',{'old_state':old.state,'original_error_preserved':old._primary_error is primary,'callback_abort_recorded':abort in old._callback_errors,'resources_complete':old._cleanup_result.resources_complete,'successor_runtime_latched':f.f.owner._latched,'successor_executor_stopped':f.ex.controller_view().stopped,'scope':'software callback seam, no real activation authentication'})

 def test_foreign_old_entry_then_malformed_close_cannot_poison_fresh_motion(self):
  f=self.fixture();old=f.actor;old.close('old resources definitely closed');fresh=self.replace_actor(f);errors=[]
  native=list(f.api.calls)
  def foreign():
   try:old.poll()
   except ValueError as error:errors.append(str(error))
  t=threading.Thread(target=foreign);t.start();t.join()
  self.assertEqual(1,len(errors))
  with self.assertRaises(ValueError):old.close()
  old.close('late same-thread teardown after foreign flag')
  self.assertEqual(native,f.api.calls)
  self.assertFalse(f.f.owner._latched);self.assertFalse(f.ex.controller_view().stopped)
  result=f.f.owner.step(expected_pose_revision=0,dt_ns=1_000_000)
  self.assertTrue(result.committed);self.assertEqual(1,f.ex.renderer_view().pose_revision)
  save('foreign-late-malformed-close',{'foreign_rejected':errors,'native_cleanup_replayed':native!=f.api.calls[:len(native)],'fresh_state':fresh.state,'committed':result.committed,'pose_revision':f.ex.renderer_view().pose_revision})

 def test_evidence_only_quarantine_late_bind_leaves_fresh_binding_current(self):
  f=self.fixture();old=f.actor
  def fail_report(owner):raise OSError('controlled old-owner evidence failure')
  with patch.object(actor_module,'_persist',fail_report):old.close('cleanup still required despite report failure')
  self.assertEqual('QUARANTINED',old.state);self.assertTrue(old._cleanup_result.resources_complete)
  self.assertFalse(old._resources.unresolved)  # No reuse of an unconfirmed fake HANDLE.
  fresh=self.replace_actor(f);native=list(f.api.calls)
  with self.assertRaises(ValueError):old.bind_verified_boot(f.f.binding,runtime=f.f.owner,executor=f.ex)
  self.assertEqual(native,f.api.calls);self.assertFalse(f.f.owner._latched);self.assertFalse(f.ex.controller_view().stopped)
  result=f.f.owner.step(expected_pose_revision=0,dt_ns=1_000_000);self.assertTrue(result.committed)
  save('evidence-quarantine-late-bind',{'old_state':old.state,'old_resources_complete':old._cleanup_result.resources_complete,'old_evidence_errors':len(old._evidence_errors),'fresh_state':fresh.state,'fresh_committed':result.committed})

 def test_malformed_terminal_after_successful_terminate_stays_quarantined_without_retry(self):
  f=self.fixture(False);old=f.launch();original=f.api.Wait
  def malformed_terminal(handle,timeout):
   value=original(handle,timeout)
   return 0.0 if timeout==5000 else value
  f.api.Wait=malformed_terminal
  old.close('single terminate then malformed terminal observation')
  self.assertEqual('QUARANTINED',old.state);self.assertFalse(f.api.live)
  self.assertFalse(old._process.terminal_confirmed);self.assertFalse(old._cleanup_result.resources_complete)
  self.assertNotIn(('close',300),f.api.calls);self.assertNotIn(('close',200),f.api.calls);self.assertNotIn(('profile_delete',),f.api.calls)
  self.assertEqual(1,sum(c[0]=='terminate' for c in f.api.calls))
  before=list(f.api.calls);old.close('do not retry an ambiguous terminal readback');self.assertEqual(before,f.api.calls)
  self.assertIs(f.registry._owners[0],old)
  save('malformed-post-terminate',{'state':old.state,'fake_process_live':f.api.live,'terminal_confirmed':old._process.terminal_confirmed,'unresolved':[r.resource_id for r in old._resources.unresolved],'terminate_calls':sum(c[0]=='terminate' for c in f.api.calls),'second_close_native_effects':before!=f.api.calls,'shape':'float0 terminal readback, fake API only'})


if __name__=='__main__':unittest.main()
