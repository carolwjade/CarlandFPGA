"""Fresh fake-only backend/orchestration checks; native fixture opt-in is unset."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from simulation.isolation import prototype, win32 as w
from simulation.isolation.owned_resources import OwnedResources
from simulation.isolation.windows_cleanup import WindowsCleanupBackend
from simulation.isolation.resource_cleanup import Provenance
from test_prototype_cleanup import LauncherApi
from test_windows_cleanup import FakeCleanupApi

O=Path(__file__).resolve().parent

class IndependentBoundaries(unittest.TestCase):
 def test_timeout_plus_audit_failure_preserves_primary_and_recovery_handles(self):
  with tempfile.TemporaryDirectory(dir=O/'temp') as directory:
   parent=Path(directory);api=LauncherApi(parent);api.secret=b'z'*32;api.waits=[258,258,258]
   def save(path,value):
    if isinstance(value,dict) and value.get('cleanup_events'):raise OSError('independent audit disk failure')
    prototype.save(path,value)
   with patch.object(prototype.os,'urandom',return_value=api.secret):
    _,evidence=prototype.run(parent,timeout_ms=100,api=api,report_save=save,runtime_stage=lambda b,s:[])
   self.assertEqual(evidence['error']['type'],'TimeoutError')
   self.assertIsInstance(evidence.primary_exception,TimeoutError)
   self.assertEqual({r.label for r in evidence.ownership.unresolved},{'profile','job','process','primary_thread'})
   self.assertIn(('close',54),api.calls)
   for value in (60,70,71):self.assertNotIn(('close',value),api.calls)
   self.assertEqual([call for call in api.calls if call[0]=='wait'],[('wait',70,100),('wait',70,0),('wait',70,5000)])
   self.assertEqual(api.calls.count(('terminate',70)),1)
   self.assertFalse(evidence['verdict']['passed']);self.assertFalse(evidence['cleanup']['evidence_complete'])
 def test_profile_absence_error_is_retained_without_delete_replay(self):
  api=FakeCleanupApi();owner=OwnedResources(Provenance('task/v1','review','owner',(('s','a'*64),)))
  backend=WindowsCleanupBackend(api,owner);owner.own_profile('fresh-review',1000);owner.set_profile_path('fake-path')
  with patch.object(api,'profile_absent',side_effect=PermissionError('unknown stat')):
   result=owner.cleanup(backend,lambda e:None)
  self.assertEqual([r.label for r in owner.unresolved],['profile'])
  self.assertFalse(result.resources_complete)
  with self.assertRaises(RuntimeError):owner.cleanup(backend,lambda e:None)
  self.assertEqual(api.calls.count(('delete','fresh-review')),1)
 def test_pipe_capture_reads_available_bytes_once_with_hard_cap(self):
  def peek(handle,buffer,size,read,count,left):count._obj.value=1_000_000;return True
  with patch.object(w,'PeekNamedPipe',side_effect=peek) as called,patch.object(w,'read',return_value=b'x'*8192) as read:
   self.assertEqual(len(w.available_output(123)),8192)
  called.assert_called_once();read.assert_called_once_with(123,8192)

if __name__=='__main__':unittest.main(verbosity=2)
