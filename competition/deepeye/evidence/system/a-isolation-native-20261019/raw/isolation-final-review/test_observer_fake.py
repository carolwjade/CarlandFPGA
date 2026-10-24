"""Only fake delegated functions; no native opt-in or real Windows APIs."""
from pathlib import Path
import ast,hashlib,importlib.util,json,unittest
from types import SimpleNamespace
from unittest.mock import patch
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_native_observer',OUT/'run_native.reviewed.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

class ObserverTests(unittest.TestCase):
    def setUp(self):
        h.LIVE_RESULTS.clear();h.LIVE_OWNERS.clear()
        self.error=11;self.calls=[]
        self.ctypes=SimpleNamespace(get_last_error=lambda:self.error,set_last_error=self.set_error)
        self.owner=SimpleNamespace(references=(SimpleNamespace(kind='process',native=17,resource_id='process-ref'),),
                                  unresolved=(SimpleNamespace(resource_id='process-ref'),))
    def set_error(self,n):self.error=n

    def test_original_held_process_handle_and_real_close_error_survive_readback(self):
        def wait(handle,timeout):self.calls.append(('Wait',handle,timeout));self.error=77;return 0
        def exit_code(handle):self.calls.append(('exit_code',handle));self.error=88;return 42
        def close(handle):self.calls.append(('CloseHandle',handle,self.error));self.error=5;return 0
        api=h.ObservedNativeApi(SimpleNamespace(Wait=wait,exit_code=exit_code,CloseHandle=close))
        api.remember_owner(self.owner)
        with patch.object(h,'ctypes',self.ctypes):result=api.CloseHandle(17)
        self.assertEqual(0,result);self.assertEqual(5,self.error)
        self.assertEqual([('Wait',17,0),('exit_code',17),('CloseHandle',17,11)],self.calls)
        terminal=api.events[0]
        self.assertEqual(('process-ref',17,0,42,None),(terminal['resource_id'],terminal['handle'],terminal['wait_result'],terminal['exit_code'],terminal['error']))

    def test_wait_terminate_delete_return_values_and_last_error_are_delegated(self):
        def wait(handle,timeout):self.calls.append(('Wait',handle,timeout));self.error=6;return 0xffffffff
        def terminate(handle,code):self.calls.append(('TerminateProcess',handle,code));self.error=7;return 0
        def delete(name):self.calls.append(('DeleteProfile',name));self.error=8;return -1
        api=h.ObservedNativeApi(SimpleNamespace(Wait=wait,TerminateProcess=terminate,DeleteProfile=delete))
        with patch.object(h,'ctypes',self.ctypes):
            self.assertEqual(0xffffffff,api.Wait(17,100));self.assertEqual(6,self.error)
            self.assertEqual(0,api.TerminateProcess(17,123));self.assertEqual(7,self.error)
            self.assertEqual(-1,api.DeleteProfile('fresh-fake-profile'));self.assertEqual(8,self.error)
        self.assertEqual([('Wait',17,100),('TerminateProcess',17,123),('DeleteProfile','fresh-fake-profile')],self.calls)

    def test_first_acquisition_exception_still_retains_exact_owner_and_primary_exception(self):
        original=OSError('fake first acquisition reporting error')
        def acquire(*args,**kwargs):
            self.assertIs(self.owner,h.LIVE_OWNERS[0]);raise original
        api=h.ObservedNativeApi(SimpleNamespace(user_sid=acquire))
        with self.assertRaises(OSError) as error:api.user_sid(owner=self.owner)
        self.assertIs(original,error.exception);self.assertIs(self.owner,h.LIVE_OWNERS[0])

    def test_successful_process_pair_is_returned_without_substitution(self):
        pair=SimpleNamespace(hProcess=17,hThread=18,dwProcessId=99)
        def create(*args,**kwargs):
            self.assertIs(self.owner,h.LIVE_OWNERS[0]);return pair
        api=h.ObservedNativeApi(SimpleNamespace(create_suspended=create))
        self.assertIs(pair,api.create_suspended(owner=self.owner))
        self.assertEqual((99,17,18),(api.events[0]['pid'],api.events[0]['process_handle'],api.events[0]['thread_handle']))

    def test_observation_save_failure_keeps_owner_and_returned_memory(self):
        # Extract only the nested observer function into fake globals. main(),
        # gate handling, environment opt-in, profile stat and native import never run.
        module=ast.parse((OUT/'run_native.reviewed.py').read_bytes())
        main=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        node=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='observed_run')
        class Evidence(dict):pass
        evidence=Evidence(profile_name='fresh-fake',verdict={'passed':False})
        evidence.ownership=self.owner
        def original(parent,api,**kwargs):api.remember_owner(self.owner);return Path('owned-fake/receipt.json'),evidence
        failure=OSError('fake main observation persistence error')
        def save(*args):raise failure
        values=dict(vars(h),original_run=original,records=[],win32=object(),save_new=save)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<extracted-observed_run>','exec'),values)
        with self.assertRaises(OSError) as error:values['observed_run'](Path('fake-parent'))
        self.assertIs(failure,error.exception);self.assertIs(self.owner,h.LIVE_OWNERS[0])
        self.assertIs(evidence,h.LIVE_RESULTS[0]);self.assertEqual([],values['records'])

if __name__=='__main__':unittest.main(verbosity=2)
