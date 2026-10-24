"""Actual launcher orchestration against an explicitly fake API and stage."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from simulation.isolation import prototype
from test_windows_cleanup import FakeCleanupApi


class LauncherApi(FakeCleanupApi):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.next_handle = 50
        self.waits = [0, 0, 0]
        self.fail = None
        self.P = lambda: None
        self.pid = 123
    def user_sid(self, *, owner):
        return 'S-1-5-21-fake'
    def set_new_object_acl(self, path, root, user, package=None, *, owner):
        return {'path': str(path), 'fake': True}
    def create_profile(self, name, *, owner):
        owner.own_profile(name, 1000)
        return 1000
    def sid_text(self, sid, *, owner):
        if self.fail == 'sid_text':
            raise OSError('SID conversion failed')
        return 'S-1-15-2-fake'
    def profile_path(self, sid, *, owner):
        return self.root / 'fake-profile'
    def own_canary(self, path, *, owner):
        return owner.own_handle('canary', 40)
    def parent_controls(self, *, owner):
        return True
    def read(self, *args):
        raise AssertionError('blocking ReadFile must not be used')
    def canary_read(self, handle, size):
        return self.secret
    def pipe(self, *, owner, read_label, write_label):
        self.next_handle += 2
        read, write = self.next_handle, self.next_handle + 1
        owner.own_handle(read_label, read)
        owner.own_handle(write_label, write)
        return read, write
    def SetHandleInformation(self, *args):
        return True
    def handle_flags(self, handle):
        return 0 if handle in (53, 54) else 1
    def create_job(self, *, owner):
        ref = owner.own_handle('job', 60, recovery=True)
        if self.fail == 'job':
            raise OSError('job limits failed')
        return ref.native
    def create_suspended(self, *args, owner):
        pi = SimpleNamespace(hProcess=70, hThread=71, dwProcessId=123)
        owner.own_process(pi)
        if self.fail == 'after_process':
            raise OSError('helper failed after creation')
        return pi
    def AssignJob(self, *args):
        return True
    def inspect_process(self, *args, owner):
        return dict(is_appcontainer=True, sid_matches=True, win32k_disabled=True,
                    child_process_restricted=True, in_job=True, job_limits_match=True,
                    capability_count=0)
    def write(self, *args):
        return None
    def ResumeThread(self, *args):
        return 1
    def exit_code(self, handle):
        return 0
    def available_output(self, handle):
        self.calls.append(('available_output', handle))
        return b'{}'


class PrototypeCleanupTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(prototype, 'RunEvidence'), 'launcher still drops live ownership on failure')
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.api = LauncherApi(self.root)
        self.saves = []

    def run_fake(self, fail_save=None):
        def stage(base, target):
            return []
        def save(path, value):
            self.saves.append((path.name, set(value) if isinstance(value, dict) else None))
            if fail_save and fail_save(path, value):
                raise OSError('disk full')
            prototype.save(path, value)
        from unittest.mock import patch
        with patch.object(self.api, 'canary_read', side_effect=lambda handle, size: self.api.secret), \
             patch.object(prototype.os, 'urandom', side_effect=self.secret), \
             patch.object(prototype, 'parse_fixture', return_value={
                 'model_ok': True, 'pipe_ok': True, 'truth_open_error': 5, 'canary_handle_error': 6,
                 'process_access_errors': {str(access): 5 for access in (8, 16, 32, 64, 128)}}):
            return prototype.run(self.root, api=self.api, report_save=save, runtime_stage=stage)

    def secret(self, size):
        self.api.secret = b'k' * size
        return self.api.secret

    def test_process_is_owned_even_if_helper_fails_before_returning_pi(self):
        self.api.fail = 'after_process'
        receipt, result = self.run_fake()
        self.assertEqual(result['error']['message'], 'helper failed after creation')
        self.assertIn(('close', 70), self.api.calls)
        self.assertIn(('close', 71), self.api.calls)
        self.assertEqual(result.ownership.unresolved, ())
        self.assertEqual(result['error'].get('type'), 'OSError')

    def test_successful_fake_fixture_passes_only_with_complete_cleanup_and_evidence(self):
        receipt, result = self.run_fake()
        self.assertTrue(result['verdict']['passed'], result)
        self.assertEqual(result.ownership.unresolved, ())

    def test_serialization_failure_at_every_cleanup_event_still_closes_safe_resources(self):
        receipt, result = self.run_fake(lambda path, value: isinstance(value, dict) and bool(value.get('cleanup_events')))
        self.assertTrue(result['cleanup']['resources_complete'])
        self.assertFalse(result['cleanup']['evidence_complete'])
        self.assertFalse(result['verdict']['passed'])
        self.assertIn(('close', 70), self.api.calls)
        self.assertIn(('close', 71), self.api.calls)

    def test_profile_sid_failure_still_frees_sid_and_retains_unknown_path_profile(self):
        self.api.fail = 'sid_text'
        receipt, result = self.run_fake()
        self.assertEqual(result['error']['message'], 'SID conversion failed')
        self.assertIn(('free_sid', 1000), self.api.calls)
        self.assertEqual({r.label for r in result.ownership.unresolved}, {'profile'})
        self.assertFalse(result['lifecycle']['profile_deleted'])

    def test_save_failure_after_process_creation_cannot_skip_cleanup(self):
        receipt, result = self.run_fake(lambda path, value: isinstance(value, dict) and 'pid' in value)
        self.assertEqual(result['error']['message'], 'disk full')
        self.assertIn(('close', 70), self.api.calls)
        self.assertIn(('close', 71), self.api.calls)
        self.assertTrue(result['cleanup']['resources_complete'])
        self.assertFalse(result['cleanup']['evidence_complete'])
        self.assertFalse(result['verdict']['passed'])

    def test_unconfirmed_terminal_retains_live_process_thread_job_context(self):
        self.api.fail = 'after_process'
        self.api.waits = [258, 258]
        receipt, result = self.run_fake()
        self.assertTrue({'process', 'primary_thread', 'job', 'profile'} <= {r.label for r in result.ownership.unresolved})
        self.assertNotIn(('close', 70), self.api.calls)
        self.assertNotIn(('close', 71), self.api.calls)
        self.assertNotIn(('close', 60), self.api.calls)

    def test_early_close_failure_is_never_replayed_or_followed_by_blocking_read(self):
        self.api.close_ok = False
        receipt, result = self.run_fake()
        self.assertFalse(result['verdict']['passed'])
        self.assertEqual(self.api.calls.count(('close', 52)), 1)
        self.assertFalse(result['cleanup']['resources_complete'])

    def test_final_save_failure_returns_in_memory_failed_evidence(self):
        receipt, result = self.run_fake(lambda path, value: isinstance(value, dict) and 'verdict' in value)
        self.assertTrue(result['cleanup']['resources_complete'])
        self.assertFalse(result['cleanup']['evidence_complete'])
        self.assertFalse(result['verdict']['passed'])
        self.assertTrue(result['evidence_errors'])

    def test_job_failure_retains_allocated_job_and_cleans_it(self):
        self.api.fail = 'job'
        receipt, result = self.run_fake()
        self.assertEqual(result['error']['message'], 'job limits failed')
        self.assertIn(('close', 60), self.api.calls)
        self.assertEqual(result.ownership.unresolved, ())

    def test_real_fsync_failure_after_creation_is_contained_during_cleanup(self):
        from unittest.mock import patch
        def stage(base, target):
            return []
        def save(path, value):
            if isinstance(value, dict) and 'pid' in value:
                with patch.object(prototype.os, 'fsync', side_effect=OSError('fsync injection')):
                    prototype.save(path, value)
            else:
                prototype.save(path, value)
        with patch.object(self.api, 'canary_read', side_effect=lambda handle, size: self.api.secret), \
             patch.object(prototype.os, 'urandom', side_effect=self.secret):
            receipt, result = prototype.run(self.root, api=self.api, report_save=save, runtime_stage=stage)
        self.assertEqual(result['error']['message'], 'fsync injection')
        self.assertEqual(result.ownership.unresolved, ())
        self.assertFalse(result['cleanup']['evidence_complete'])
        self.assertIn(('close', 70), self.api.calls)
