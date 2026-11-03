"""Synthetic stationary entry policy controls; no model, actor or board launch."""
import unittest
from types import SimpleNamespace as NS
from competition.deepeye.simulation.authority import actor_composition as a

class EntryStationaryControls(unittest.TestCase):
 def owner(self):
  o=object.__new__(a.ActorComposition);o._stationary_replan=None;o._stationary_replans=[]
  old=NS(raw=b'old',sequence=1,deadline_ns=3)
  o._runtime=NS(_last_command=old,_command=None,_latched=False,_stepping=False,_busy=False)
  o._progress=NS(bound=NS(request_raw=b'old',deadline_ns=8));o._command_record=NS(raw=b'old')
  o._input_transaction=None;o._candidates=NS(_pending=None)
  o._world_action_link=NS(book=NS(_actor_custody=NS(pending=None)),slot=NS(closed=True,getter_admitted=True))
  o._owned_invocations=NS(pending=None,ready=None,failed=False,associations=[],records=[],_retained=None)
  o._actor=NS(state='BOUND_ACTIVE');o._clock=lambda:4
  profile=NS(max_commands=16);o._entry_stationary_profile=lambda:profile
  o._channel_health=lambda:None
  o._channels=NS(_board_outputs=[(b'old',(None,None,None,3),object())])
  return o
 def test_entry_wait_retains_original_command_progress_and_timestamp(self):
  self.assertTrue(hasattr(a.ActorComposition,'_stationary_replan_wait'))
  o=self.owner();old=o._runtime._last_command;bound=o._progress.bound
  self.assertTrue(o._stationary_replan_wait());record=o._stationary_replan
  o._clock=lambda:5;self.assertTrue(o._stationary_replan_wait())
  self.assertIs(o._stationary_replan,record);self.assertIs(record.command,old)
  self.assertIs(record.progress,bound);self.assertEqual(record.entered_ns,4)
  self.assertEqual(old.deadline_ns,3);self.assertEqual(bound.deadline_ns,8)
 def test_pending_step_initial_actor_pending_and_unexpired_board_refuse_wait(self):
  for kind in ('step','actor','board','old_profile','progress'):
   o=self.owner()
   if kind=='step':o._world_action_link.book._actor_custody.pending=object()
   elif kind=='actor':o._owned_invocations.pending={'foreign':True}
   elif kind=='board':o._channels._board_outputs[0]=(b'old',(None,None,None,5),object())
   elif kind=='old_profile':o._entry_stationary_profile=lambda:None
   else:o._progress.bound.deadline_ns=4
   self.assertFalse(o._stationary_replan_wait(),kind)
 def test_poll_keeps_other_expiry_reasons_on_original_retire_path(self):
  o=self.owner();o._state='ACTIVE';o._channel_health=lambda:None;o._actor.poll=lambda:None
  o._runtime.check_expiry=lambda:NS(stop_required=True,reason='health_timeout')
  reasons=[];o._retire=reasons.append
  a.ActorComposition.poll.__wrapped__(o)
  self.assertEqual(reasons,['health_timeout']);self.assertIsNone(o._stationary_replan)
 def test_old_profile_command_expiry_still_retires_and_unsettled_tx_never_enters_wait(self):
  o=self.owner();o._entry_stationary_profile=lambda:None;o._state='ACTIVE';o._actor.poll=lambda:None
  o._runtime.check_expiry=lambda:NS(stop_required=True,reason='command_deadline')
  reasons=[];o._retire=reasons.append
  a.ActorComposition.poll.__wrapped__(o)
  self.assertEqual(reasons,['command_deadline']);self.assertIsNone(o._stationary_replan)
  o=self.owner();o._input_transaction=a._InputTransaction('observation')
  self.assertFalse(o._stationary_replan_wait());self.assertIsNone(o._stationary_replan)
 def test_poll_waits_without_replacing_expired_runtime_command_or_progress(self):
  o=self.owner();o._state='ACTIVE';o._actor.poll=lambda:None
  o._runtime.check_expiry=lambda:NS(stop_required=True,reason='command_deadline')
  o._retire=lambda reason:self.fail('eligible stationary entry retired')
  self.assertEqual(a.ActorComposition.poll.__wrapped__(o),'WAITING_FRESH_OBSERVATION')
  self.assertIsNone(o._runtime._command);self.assertEqual(o._runtime._last_command.deadline_ns,3)
  self.assertEqual(o._progress.bound.deadline_ns,8)
 def test_health_failure_and_progress_expiry_do_not_create_or_renew_waiting(self):
  o=self.owner()
  def lost_health():raise ValueError('original health expired')
  o._channel_health=lost_health
  with self.assertRaises(ValueError):o._stationary_replan_wait()
  self.assertIsNone(o._stationary_replan)
  o=self.owner();self.assertTrue(o._stationary_replan_wait());held=o._stationary_replan
  o._clock=lambda:8;self.assertFalse(o._stationary_replan_wait())
  self.assertIs(o._stationary_replan,held);self.assertEqual(held.entered_ns,4)
 def test_factory_selection_accepts_only_exact_entry_descriptor_and_navigation(self):
  from competition.deepeye.simulation.authority import demo30h_ai_em3_profile_v2 as profiles
  from competition.deepeye.simulation.authority.g05_csr_channels_v1 import G05CsrChannels
  from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S
  o=self.owner();del o._entry_stationary_profile
  c=object.__new__(G05CsrChannels);c.owner=o;c._cycle_profile=lambda:NAV_ADJACENT_180S;o._channels=c
  for profile,cap,want in ((None,5_000_000_000,False),(profiles.NAV_FAST_V1,5_000_000_000,False),(profiles.NAV_ENTRY_C0_V1,8_000_000_000,True)):
   d=profiles.selected_profile(cap,navigation_profile=profile);policy=NS(demo_ai_profile=d,max_source_age_ns=cap)
   c.policy=policy;o._config=NS(g05_csr_v1=policy,g05_board_output_v1=object())
   self.assertEqual(o._entry_stationary_profile() is d,want)
  c._cycle_profile=lambda:None;self.assertIsNone(o._entry_stationary_profile())
 def test_only_original_new_association_may_progress_after_wait_entry(self):
  from competition.deepeye.simulation.authority import owned_invocation_v1
  from competition.deepeye.simulation.authority.owned_invocation_v1 import adapter
  from competition.deepeye.simulation.authority.g05_csr_channels_v1 import _Mapping,_OBSERVATIONS
  o=self.owner();self.assertTrue(o._stationary_replan_wait());o._boot=object()
  event=object();draft=object();token=object();m=object.__new__(_Mapping)
  m.channels=o._channels;m.used=True;m.refs={'draft':draft,'token':token};m.raw=b'new'
  record=NS(identity=NS(invocation_id=2));o._actor._invocation=record
  tx=a._InputTransaction('observation',original_event=event,observation_record=NS(raw=b'new'))
  association=adapter._Association(adapter._KEY,owner=o,source=o._channels,clock=o._clock,boot=o._boot,
   previous_action=None,previous_deadline_ns=None,g05_mapping=m,event=event,sample_ref=draft,
   source_bound_receipt=token,record=tx.observation_record,observation_bytes=b'new',tx=tx)
  tx.owned_association=association
  _OBSERVATIONS[event]=m
  try:
   o._owned_invocations.associations=[association];o._owned_invocations.records=[record]
   o._input_transaction=tx;o._owned_invocations.pending={'association':association,'record':record}
   self.assertTrue(o._stationary_replan_wait())
   original_pending=o._owned_invocations.pending
   o._owned_invocations.pending=None;o._owned_invocations.ready=object()
   o._owned_invocations._retained=(o._owned_invocations.ready,record,None,None,original_pending,None,None)
   self.assertTrue(o._stationary_replan_wait())
   o._owned_invocations.ready=None;o._owned_invocations._retained=None
   o._candidates._pending=NS(source=o._channels,boot=o._boot,clock_domain=o._clock,invocation_id=2)
   self.assertTrue(o._stationary_replan_wait())
   o._candidates._pending=None
   o._owned_invocations.pending={'association':NS(),'record':record}
   self.assertFalse(o._stationary_replan_wait())
  finally:_OBSERVATIONS.pop(event,None)
if __name__=='__main__':unittest.main()
