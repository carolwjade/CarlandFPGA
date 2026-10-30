"""Fresh bootstrap sequence controls; no native world, actor, board or PDE."""
import unittest,threading
from types import SimpleNamespace
from competition.deepeye.tools import run_causal_functional_chain as c
class Tests(unittest.TestCase):
 def test_missing_real_spec_rejected_before_acquire(self):
  with self.assertRaises(ValueError):c.acquire_functional_world(None,None,1,operation_id="test",output_dir=None,field_policy={})
 def test_start_is_explicit_and_once(self):
  calls=[];f=object.__new__(c.FunctionalSource);f._thread=threading.get_ident();f.clock=lambda:42;f.source=SimpleNamespace(state='NEW',start=lambda origin,clock:calls.append((origin,clock)));f._start_attempted=False
  f.start();self.assertEqual(calls,[(42,f.clock)])
  with self.assertRaises(ValueError):f.start()
 def test_start_failure_not_retried(self):
  f=object.__new__(c.FunctionalSource);f._thread=threading.get_ident();f.clock=lambda:42;f._start_attempted=False
  def fail(*args):raise RuntimeError('failure')
  f.source=SimpleNamespace(state='NEW',start=fail)
  with self.assertRaises(RuntimeError):f.start()
  with self.assertRaises(ValueError):f.start()
 def test_actual_close_result_not_promoted(self):
  closed={'slots':{'process':{'state':'UNKNOWN'},'job':{'state':'NOT_ACQUIRED'}},'state':'QUARANTINED'}
  self.assertFalse(c._native_closed(closed))
 def test_bad_initial_view_rejected(self):
  owner=SimpleNamespace(_commits=[],_diagnostic_used=False)
  view=SimpleNamespace(kind='INITIAL_VIEW',revision=0,resolved=True,state='APPLIED',readback_ns=None,deadline_ns=9,readback=None,differences=None)
  with self.assertRaises(ValueError):c._check_initial_view(owner,view)
 def test_prestart_poll_does_not_touch_source(self):
  f=object.__new__(c.FunctionalSource);f._thread=threading.get_ident();f._start_attempted=False;called=[]
  f.source=SimpleNamespace(state='NEW',poll=lambda:called.append(True));f._pending=None
  with self.assertRaises(ValueError):f.poll_sample()
  self.assertEqual(called,[]);self.assertEqual(f.source.state,'NEW')
 def test_initial_view_requires_real_getter_evidence(self):
  owner=SimpleNamespace(_commits=[],_diagnostic_used=False)
  differences={'local':tuple((0,1) for _ in range(12)),'global_transform':tuple((0,1) for _ in range(12))}
  view=SimpleNamespace(kind='INITIAL_VIEW',revision=0,resolved=True,state='APPLIED',readback_ns=5,deadline_ns=9,readback=object(),differences=differences)
  c._check_initial_view(owner,view);view.differences=None
  with self.assertRaises(ValueError):c._check_initial_view(owner,view)
 def test_unknown_cleanup_is_preserved_and_not_replayed(self):
  history=[];record={'state':'QUARANTINED','slots':{'process':{'state':'UNKNOWN'},'job':{'state':'NOT_ACQUIRED'}}}
  owner=SimpleNamespace(_native=object(),close=lambda reason:(history.append(reason) or record))
  world=c.FunctionalWorld(lambda:1,'test',None);world.owner=owner
  self.assertEqual(world.close('test'),[record]);self.assertEqual(world.close('again'),[record]);self.assertEqual(history,['test'])
 def test_windows_path_accepted_before_clock_guard_without_effect(self):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  class Spec:pass
  class Policy:pass
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'unused';spec=Spec();spec.run_id='run';spec.source_bundle_sha256='p';spec.stdout_path=out/'stdout';spec.stderr_path=out/'stderr'
   policy=Policy();policy.run_id='run';policy.source_bundle_sha256='p'
   with patch.object(c._owned_godot,'ApprovedLaunchSpec',Spec), patch.object(c._world_values,'ValuePolicy',Policy):
    with self.assertRaisesRegex(ValueError,'original QPC binding'):
     c.acquire_functional_world(spec,policy,1,operation_id='new',output_dir=out,field_policy={},clock=object())
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
