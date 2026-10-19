"""Fake Win32 boundary tests; every invoked native API is replaced."""
import ctypes as C
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from simulation.isolation import win32 as w
from simulation.isolation.resource_cleanup import Outcome, Provenance
try:
    from simulation.isolation.owned_resources import OwnedResources
    from simulation.isolation.windows_cleanup import WindowsCleanupBackend
except ImportError:
    OwnedResources = WindowsCleanupBackend = None


class FakeCleanupApi:
    def __init__(self):
        self.calls = []
        self.waits = [258, 0]
        self.close_ok = True
        self.absent = True
        self.delete_hr = 0
    def check(self, ok, label):
        if not ok:
            raise OSError(label)
    def Wait(self, handle, milliseconds):
        self.calls.append(('wait', handle, milliseconds))
        value = self.waits.pop(0)
        if isinstance(value, Exception):
            raise value
        return value
    def TerminateProcess(self, handle, code):
        self.calls.append(('terminate', handle))
        return True
    def CloseHandle(self, handle):
        self.calls.append(('close', handle))
        return self.close_ok
    def FreeSid(self, value):
        self.calls.append(('free_sid', value))
        return None
    def DeleteProfile(self, name):
        self.calls.append(('delete', name))
        return self.delete_hr
    def profile_absent(self, path):
        self.calls.append(('absent', path))
        return self.absent


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(WindowsCleanupBackend, 'checked Windows backend is missing')
        self.owner = OwnedResources(Provenance('task/v1', 'work', 'owner', (('source', 'a' * 64),)))
        self.api = FakeCleanupApi()
        self.backend = WindowsCleanupBackend(self.api, self.owner)

    def test_process_thread_and_job_survive_unconfirmed_terminal(self):
        self.owner.own_profile('fresh', 1000)
        self.owner.set_profile_path('C:/dedicated/fresh')
        self.owner.own_handle('job', 10, recovery=True)
        self.owner.own_process(SimpleNamespace(hProcess=21, hThread=22, dwProcessId=99))
        self.api.waits = [258, 258]
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertEqual({r.label for r in self.owner.unresolved}, {'profile', 'job', 'process', 'primary_thread'})
        self.assertNotIn(('close', 10), self.api.calls)
        self.assertNotIn(('close', 21), self.api.calls)
        self.assertNotIn(('close', 22), self.api.calls)
        self.assertNotIn(('delete', 'fresh'), self.api.calls)

    def test_already_terminal_never_receives_a_termination_request(self):
        self.owner.own_process(SimpleNamespace(hProcess=21, hThread=22, dwProcessId=99))
        self.api.waits = [0, 0]
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertTrue(result.resources_complete)
        self.assertNotIn(('terminate', 21), self.api.calls)
        self.assertEqual(self.api.calls, [('wait', 21, 0), ('wait', 21, 5000), ('close', 21), ('close', 22)])

    def test_unknown_early_close_is_not_replayed_by_coordinator(self):
        ref = self.owner.own_handle('writer', 30)
        self.api.close_ok = False
        self.assertEqual(self.owner.release_once(ref), Outcome.UNKNOWN)
        self.api.close_ok = True
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertEqual(self.api.calls.count(('close', 30)), 1)
        self.assertEqual(self.owner.unresolved, (ref,))

    def test_unknown_profile_path_never_counts_as_absence_or_deletes(self):
        self.owner.own_profile('fresh', 1000)
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertNotIn(('delete', 'fresh'), self.api.calls)

    def test_profile_requires_successful_delete_and_explicit_absence(self):
        for hr, absent, complete in ((0, True, True), (0, None, False), (0, False, False), (-1, True, False)):
            with self.subTest(hr=hr, absent=absent):
                self.setUp()
                self.owner.own_profile('fresh', 1000)
                self.owner.set_profile_path('C:/dedicated/fresh')
                self.api.delete_hr, self.api.absent = hr, absent
                result = self.owner.cleanup(self.backend, lambda event: None)
                self.assertEqual(result.resources_complete, complete)

    def test_job_is_owned_before_setup_failure(self):
        with patch.object(w, 'CreateJob', return_value=41), patch.object(w, 'SetJobInfo', return_value=False):
            with self.assertRaises(OSError):
                w.create_job(owner=self.owner)
        self.assertEqual([(r.label, r.native) for r in self.owner.unresolved], [('job', 41)])

    def test_both_process_handles_are_owned_before_attribute_release_failure(self):
        self.backend.api = w
        def initialize(buffer, count, flags, size):
            size._obj.value = 256
            return True
        def create(*args):
            pi = args[-1]._obj
            pi.hProcess, pi.hThread, pi.dwProcessId = 51, 52, 99
            return True
        with patch.object(w, 'InitAttributes', side_effect=initialize), patch.object(w, 'UpdateAttribute', return_value=True), \
             patch.object(w, 'CreateProcess', side_effect=create), patch.object(w, 'DeleteAttributes', side_effect=OSError('free attributes failed')):
            with self.assertRaises(Exception):
                w.create_suspended('fake.exe', [], 'C:/fake', {}, w.P(1000), 1, 2, owner=self.owner)
        self.assertTrue({'process', 'primary_thread', 'attributes'} <= {r.label for r in self.owner.unresolved})
        self.assertEqual(self.owner.errors[0].message, 'free attributes failed')

    def test_helper_close_failure_never_replaces_its_primary_error(self):
        self.backend.api = w
        def open_token(process, access, output):
            output._obj.value = 42
            return True
        with patch.object(w, 'GetCurrentProcess', return_value=-1), patch.object(w, 'OpenProcessToken', side_effect=open_token), \
             patch.object(w, 'token_buffer', side_effect=OSError('primary token read failed')), patch.object(w, 'CloseHandle', return_value=False):
            with self.assertRaisesRegex(OSError, 'primary token read failed'):
                w.user_sid(owner=self.owner)
        self.assertEqual([(ref.label, ref.native) for ref in self.owner.unresolved], [('self_token', 42)])
        self.assertEqual(len(self.owner.errors), 1)

    def test_profile_cannot_be_released_directly_with_live_dependents(self):
        profile = self.owner.own_profile('fresh', 1000)
        self.owner.set_profile_path('C:/dedicated/fresh')
        self.owner.own_process(SimpleNamespace(hProcess=21, hThread=22, dwProcessId=99))
        self.assertEqual(self.owner.release_once(profile), Outcome.UNKNOWN)
        self.assertNotIn(('delete', 'fresh'), self.api.calls)

    def test_sid_allocation_survives_unresolved_attribute_storage(self):
        self.owner.own_profile('fresh', 1000)
        self.owner.set_profile_path('C:/dedicated/fresh')
        keepalive = object()
        attributes = self.owner.own_handle('attributes', 2000, release='attributes', keepalive=keepalive)
        # Fake API lacks DeleteAttributes: its uncertain release stays owned.
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertNotIn(('free_sid', 1000), self.api.calls)
        self.assertIs(attributes.keepalive, keepalive)
        self.assertTrue({'profile_sid', 'attributes', 'profile'} <= {r.label for r in self.owner.unresolved})

    def test_profile_sid_is_owned_before_text_conversion_failure(self):
        def create(*args):
            args[-1]._obj.value = 1000
            return 0
        with patch.object(w, 'CreateProfile', side_effect=create):
            sid = w.create_profile('fresh', owner=self.owner)
        with patch.object(w, 'ConvertSidToStringSidW', return_value=False), self.assertRaises(OSError):
            w.sid_text(sid, owner=self.owner)
        self.assertEqual({r.label for r in self.owner.unresolved}, {'profile', 'profile_sid'})

    def test_wait_failure_is_unknown_and_independent_handle_still_closes(self):
        self.owner.own_process(SimpleNamespace(hProcess=21, hThread=22, dwProcessId=99))
        self.owner.own_handle('independent', 31)
        self.api.waits = [OSError('initial wait'), OSError('final wait')]
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertIn(('close', 31), self.api.calls)
        self.assertNotIn(('close', 21), self.api.calls)

    def test_pipe_pair_retains_every_member_and_only_closes_safe_companion(self):
        for conflicts in ((81,), (82,), (81, 82)):
            with self.subTest(conflicts=conflicts):
                self.setUp()
                self.api.close_ok = False
                for value in conflicts:
                    self.owner.release_once(self.owner.own_handle('old_' + str(value), value))
                self.api.close_ok = True
                self.api.calls.clear()
                def create(read, write, attributes, size):
                    read._obj.value, write._obj.value = 81, 82
                    return True
                with patch.object(w, 'CreatePipe', side_effect=create) as created:
                    with self.assertRaisesRegex(ValueError, 'ambiguous native reuse') as raised:
                        w.pipe(owner=self.owner, read_label='new_read', write_label='new_write')
                created.assert_called_once()
                self.assertEqual([(ref.label, ref.native) for ref in self.owner.references][-2:],
                                 [('new_read', 81), ('new_write', 82)])
                result = self.owner.cleanup(self.backend, lambda event: None, raised.exception)
                self.assertFalse(result.resources_complete)
                self.assertEqual(result.primary_error.message, str(raised.exception))
                for value in (81, 82):
                    self.assertEqual(self.api.calls.count(('close', value)), 0 if value in conflicts else 1)

    def test_mocked_createprocess_records_pair_before_ambiguity_and_secondary_free_error(self):
        for conflicts in ((51,), (52,), (51, 52)):
            with self.subTest(conflicts=conflicts):
                self.setUp()
                self.api.close_ok = False
                for value in conflicts:
                    self.owner.release_once(self.owner.own_handle('old_' + str(value), value))
                self.backend.api = w
                def initialize(buffer, count, flags, size):
                    size._obj.value = 256
                    return True
                def create(*args):
                    pair = args[-1]._obj
                    pair.hProcess, pair.hThread, pair.dwProcessId = 51, 52, 99
                    return True
                with patch.object(w, 'InitAttributes', side_effect=initialize), patch.object(w, 'UpdateAttribute', return_value=True), \
                     patch.object(w, 'CreateProcess', side_effect=create) as created, \
                     patch.object(w, 'DeleteAttributes', side_effect=OSError('secondary attribute release failed')):
                    with self.assertRaisesRegex(ValueError, 'ambiguous native reuse'):
                        w.create_suspended('fake.exe', [], 'C:/fake', {}, w.P(1000), 1, 2, owner=self.owner)
                created.assert_called_once()
                self.assertEqual([(ref.label, ref.native) for ref in self.owner.references][-2:],
                                 [('process', 51), ('primary_thread', 52)])
                self.assertTrue(any(error.message == 'secondary attribute release failed' for error in self.owner.errors))

    def test_unambiguous_primary_thread_remains_recovery_control_for_ambiguous_process(self):
        self.api.close_ok = False
        self.owner.release_once(self.owner.own_handle('old', 51))
        self.api.close_ok = True
        self.api.calls.clear()
        with self.assertRaisesRegex(ValueError, 'ambiguous native reuse'):
            self.owner.own_process(SimpleNamespace(hProcess=51, hThread=52, dwProcessId=99))
        result = self.owner.cleanup(self.backend, lambda event: None)
        self.assertFalse(result.resources_complete)
        self.assertEqual({ref.label for ref in self.owner.unresolved}, {'old', 'process', 'primary_thread'})
        self.assertNotIn(('close', 51), self.api.calls)
        self.assertNotIn(('close', 52), self.api.calls)

    def test_mocked_createprofile_records_sid_before_profile_registration_ambiguity(self):
        self.owner._releaser = lambda ref: Outcome.UNKNOWN
        prior = self.owner.own_handle('old_profile', 'fresh', release='profile', kind='profile', profile_dependent=False)
        self.owner.release_once(prior)
        def create(*args):
            args[-1]._obj.value = 1000
            return 0
        with patch.object(w, 'CreateProfile', side_effect=create) as created:
            with self.assertRaisesRegex(ValueError, 'ambiguous native reuse'):
                w.create_profile('fresh', owner=self.owner)
        created.assert_called_once()
        self.assertEqual([(ref.label, ref.native) for ref in self.owner.references],
                         [('old_profile', 'fresh'), ('profile', 'fresh'), ('profile_sid', 1000)])
