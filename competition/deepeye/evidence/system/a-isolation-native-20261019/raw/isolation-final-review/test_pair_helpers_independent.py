"""Independent narrow pair matrices; all native acquisition/release calls fake."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from simulation.isolation import win32 as w
from simulation.isolation.owned_resources import OwnedResources
from simulation.isolation.windows_cleanup import WindowsCleanupBackend
from simulation.isolation.resource_cleanup import Provenance,Outcome
from test_windows_cleanup import FakeCleanupApi

class IndependentPairHelpers(unittest.TestCase):
    def owner(self):
        owner=OwnedResources(Provenance('task/v1','final-pair-review','owned-fake-only',(('source','a'*64),)))
        api=FakeCleanupApi();backend=WindowsCleanupBackend(api,owner)
        return owner,api,backend

    def kernel_conflicts(self,owner,api,values):
        api.close_ok=False
        for value in values:
            self.assertIs(Outcome.UNKNOWN,owner.release_once(owner.own_handle('prior-'+str(value),value)))
        api.close_ok=True;api.calls.clear()

    def tracker(self,owner,errors):
        actual=owner._record_handle
        def record(*args,**kwargs):
            result=actual(*args,**kwargs)
            if result[1] is not None:errors.append(result[1])
            return result
        return record

    def test_actual_pipe_first_second_both_collision_retains_all_without_close_replay(self):
        for conflicts in ((81,),(82,),(81,82)):
            with self.subTest(conflicts=conflicts):
                owner,api,backend=self.owner();self.kernel_conflicts(owner,api,conflicts);errors=[]
                def create(r,wr,sa,size):r._obj.value=81;wr._obj.value=82;return True
                with patch.object(w,'CreatePipe',side_effect=create),patch.object(owner,'_record_handle',side_effect=self.tracker(owner,errors)):
                    with self.assertRaises(ValueError) as raised:w.pipe(owner=owner,read_label='new-read',write_label='new-write')
                self.assertIs(raised.exception,errors[0]);self.assertEqual(len(conflicts),len(errors))
                self.assertEqual([('new-read',81),('new-write',82)],[(r.label,r.native) for r in owner.references][-2:])
                cleanup=owner.cleanup(backend,lambda event:None,raised.exception)
                self.assertFalse(cleanup.resources_complete)
                for value in (81,82):self.assertEqual(0 if value in conflicts else 1,api.calls.count(('close',value)))
                self.assertTrue(all(r.ambiguous for r in owner.references if r.native in conflicts))

    def test_actual_createprocess_pair_and_secondary_attribute_error_preserve_primary_and_recovery(self):
        for conflicts in ((51,),(52,),(51,52)):
            with self.subTest(conflicts=conflicts):
                owner,api,backend=self.owner();self.kernel_conflicts(owner,api,conflicts);errors=[]
                backend.api=w
                def initialize(buf,count,flags,size):size._obj.value=256;return True
                def create(*args):
                    pi=args[-1]._obj;pi.hProcess=51;pi.hThread=52;pi.dwProcessId=99;return True
                secondary=OSError('independent secondary DeleteAttributes error')
                with patch.object(w,'InitAttributes',side_effect=initialize),patch.object(w,'UpdateAttribute',return_value=True), \
                     patch.object(w,'CreateProcess',side_effect=create) as native,patch.object(w,'DeleteAttributes',side_effect=secondary) as released, \
                     patch.object(owner,'_record_handle',side_effect=self.tracker(owner,errors)):
                    with self.assertRaises(ValueError) as raised:
                        w.create_suspended('fake.exe',[],'C:/fake',{},w.P(1000),1,2,owner=owner)
                self.assertEqual(1,native.call_count);self.assertEqual(1,released.call_count)
                self.assertIs(raised.exception,errors[0]);self.assertEqual(len(conflicts),len(errors))
                self.assertEqual([('process',51),('primary_thread',52)],[(r.label,r.native) for r in owner.references][-2:])
                self.assertTrue(owner.find('primary_thread').recovery)
                self.assertTrue(any(e.message==str(secondary) for e in owner.errors))
                backend.api=api;api.waits=[0,0]
                cleanup=owner.cleanup(backend,lambda event:None,raised.exception)
                self.assertEqual('ValueError',cleanup.primary_error.type_name)
                self.assertEqual(str(raised.exception),cleanup.primary_error.message)
                self.assertEqual(0 if 51 in conflicts else 1,api.calls.count(('close',51)))
                self.assertEqual(0,api.calls.count(('close',52)))
                self.assertEqual(1,released.call_count,'unknown attribute release must not replay')

    def test_actual_createprofile_first_second_both_collision_retains_sid_dependency(self):
        for conflicts in (('profile',),('sid',),('profile','sid')):
            with self.subTest(conflicts=conflicts):
                owner,api,backend=self.owner();name='fresh-fake-pair-profile'
                if 'profile' in conflicts:
                    old=owner.own_handle('old-profile',name,release='profile',kind='profile',profile_dependent=False)
                    self.assertIs(Outcome.UNKNOWN,owner.release_once(old))
                if 'sid' in conflicts:
                    old=owner.own_handle('old-sid',1000,release='sid',profile_dependent=False)
                    with patch.object(api,'FreeSid',return_value=1000):self.assertIs(Outcome.UNKNOWN,owner.release_once(old))
                api.calls.clear();errors=[]
                def create(*args):args[-1]._obj.value=1000;return 0
                with patch.object(w,'CreateProfile',side_effect=create) as native,patch.object(owner,'_record_handle',side_effect=self.tracker(owner,errors)):
                    with self.assertRaises(ValueError) as raised:w.create_profile(name,owner=owner)
                self.assertEqual(1,native.call_count);self.assertIs(raised.exception,errors[0])
                self.assertEqual(len(conflicts),len(errors))
                profile,sid=owner.find('profile'),owner.find('profile_sid')
                self.assertIs(profile,owner.profile);self.assertEqual(profile.resource_id,sid.profile_id)
                self.assertEqual([('profile',name),('profile_sid',1000)],[(r.label,r.native) for r in owner.references][-2:])
                owner.set_profile_path('C:/fake-owned-profile')
                cleanup=owner.cleanup(backend,lambda event:None,raised.exception)
                self.assertFalse(cleanup.resources_complete)
                self.assertEqual(0 if 'sid' in conflicts else 1,api.calls.count(('free_sid',1000)))
                self.assertEqual(0,api.calls.count(('delete',name)))

if __name__=='__main__':unittest.main(verbosity=2)
