"""Offline acquisition boundaries; no native API, real AI, or product Run."""
from dataclasses import replace
import hashlib
import importlib
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    a = importlib.import_module('competition.deepeye.simulation.isolation.actor_owner')
except ModuleNotFoundError as error:
    if error.name != 'competition.deepeye.simulation.isolation.actor_owner': raise
    a = None


class Clock:
    value = 1_000_000_000
    hook = None
    def __call__(self):
        hook, self.hook = self.hook, None
        if hook: hook()
        return self.value


class FakeApi:
    """Native boundary double retaining the real Python resource/cleanup code."""
    def __init__(self, root):
        self.root, self.calls, self.flags = root, [], {}
        self.next = 100
        self.live, self.close_ok, self.fail = True, True, None
        self.wait_result, self.wait_hook = None, None
    def point(self, name):
        self.calls.append((name,))
        if self.fail == name: raise OSError(name)
    def check(self, result, name):
        if not result: raise OSError(name)
    def user_sid(self, *, owner): self.point('user'); return 'S-1-5-21-fake'
    def set_new_object_acl(self, path, root, user, package=None, *, owner):
        self.point('acl'); return {}
    def create_profile(self, name, *, owner):
        owner.own_profile(name, 1000); self.point('profile'); return 1000
    def sid_text(self, sid, *, owner): self.point('sid'); return 'S-1-15-2-fake'
    def profile_path(self, sid, *, owner):
        self.point('profile_path'); return self.root / 'profile'
    def pipe(self, *, owner, read_label, write_label):
        self.next += 2; r, w = self.next, self.next + 1
        owner.own_pair((read_label, r, {}), (write_label, w, {}))
        self.flags[r] = self.flags[w] = 1
        self.point('pipe'); return r, w
    def SetHandleInformation(self, handle, mask, flags):
        self.flags[handle] = flags; return True
    def handle_flags(self, handle): return self.flags[handle]
    def create_job(self, *, owner):
        owner.own_handle('job', 200, recovery=True); self.point('job'); return 200
    def create_suspended(self, exe, argv, cwd, env, sid, inp, out, *, owner):
        self.live = True
        self.calls.append(('create', str(exe), tuple(argv), dict(env), inp, out))
        pi = SimpleNamespace(hProcess=300, hThread=301, dwProcessId=400)
        owner.own_process(pi); self.point('process'); return pi
    def AssignJob(self, job, process): self.point('assign'); return True
    def inspect_process(self, process, job, sid, *, owner):
        self.point('inspect')
        return dict(is_appcontainer=True, sid_matches=True, win32k_disabled=True,
                    child_process_restricted=True, in_job=True, job_limits_match=True,
                    capability_count=0, creation_filetime=123456)
    def ResumeThread(self, handle): self.point('resume'); return 1
    def Wait(self, handle, timeout):
        self.calls.append(('wait', handle, timeout))
        hook, self.wait_hook = self.wait_hook, None
        if hook: hook()
        if self.wait_result is not None: return self.wait_result
        return 258 if self.live else 0
    def TerminateProcess(self, handle, code): self.calls.append(('terminate', handle)); self.live = False; return True
    def CloseHandle(self, handle): self.calls.append(('close', handle)); return self.close_ok
    def FreeSid(self, sid): self.calls.append(('sid_free', sid)); return None
    def DeleteProfile(self, name): self.calls.append(('profile_delete',)); return 0
    def profile_absent(self, path): return True
    def exit_code(self, handle): return 259  # Deliberately legal terminal exit code.
    def available_output(self, handle): return b'bounded diagnostic'


class OwnerFixture(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(a, 'retained actor owner component absent')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'approved'; self.source.mkdir()
        (self.source / 'python.exe').write_bytes(b'FAKE executable, never run')
        (self.source / 'actor.py').write_bytes(b'FAKE actor, never run')
        self.clock, self.api = Clock(), FakeApi(self.root)
        self.patches = [patch.object(a, '_native_api', return_value=self.api),
                        patch.object(a, 'monotonic_ns', self.clock)]
        for item in self.patches: item.start(); self.addCleanup(item.stop)
        self.registry = a.ActorRegistry()
        self.policy = a.ActorPolicy(run_id='run-1', evidence_parent=self.root,
            source_root=self.source, files=tuple((p.name, hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(self.source.iterdir())), executable='python.exe', arguments=('-I', 'actor.py'),
            system_root='C:/Windows', local_appdata='C:/FakeLocal', max_stage_bytes=4096,
            output_limit=128, readiness_timeout_ns=50_000_000, lifetime_timeout_ns=2_000_000_000,
            sample_age_cap_ns=20_000_000, max_probe_ns=1_000_000)
    def launch(self): return self.registry.launch(self.policy)


class ActorOwnerTests(OwnerFixture):
    def test_factory_retains_original_acquisition_and_returns_before_cleanup(self):
        actor = self.launch()
        self.assertIs(actor, self.registry._owners[0])
        self.assertEqual(actor.state, 'RUNNING_UNBOUND')
        self.assertEqual(actor._process.native, 300)
        self.assertFalse(actor._process.attempted)
        self.assertNotIn(('close', 300), self.api.calls)
        self.assertIn(('wait', 300, 0), self.api.calls)
        self.assertEqual((actor._stage / 'actor.py').read_bytes(), b'FAKE actor, never run')
        self.assertNotEqual(actor.instance_id, '400')

    def test_acquisition_inspection_precedes_resume_and_no_pid_reopen(self):
        actor = self.launch(); names = [x[0] for x in self.api.calls]
        self.assertLess(names.index('assign'), names.index('inspect'))
        self.assertLess(names.index('inspect'), names.index('resume'))
        creation = next(x for x in self.api.calls if x[0] == 'create')
        self.assertEqual(creation[2][-2:], ('102', '105'))
        self.assertEqual(set(creation[3]), {'SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'LOCALAPPDATA'})
        self.assertEqual((self.api.flags[103], self.api.flags[104]), (0, 0))
        actor.close('test teardown')
        self.assertEqual(actor.state, 'CLOSED')

    def test_every_acquisition_failure_retains_context_and_cleans_owned_pairs(self):
        for name in ('user', 'acl', 'profile', 'sid', 'profile_path', 'pipe', 'job', 'process', 'assign', 'inspect', 'resume'):
            with self.subTest(name=name):
                self.api = FakeApi(self.root); self.api.fail = name
                with patch.object(a, '_native_api', return_value=self.api): registry = a.ActorRegistry()
                with self.assertRaisesRegex(OSError, name): registry.launch(self.policy)
                self.assertEqual(len(registry._owners), 1)
                actor = registry._owners[0]
                self.assertIn(actor.state, ('CLOSED', 'QUARANTINED'))
                if name in ('process', 'assign', 'inspect', 'resume'):
                    self.assertIn(('close', 300), self.api.calls)
                    self.assertIn(('close', 301), self.api.calls)

    def test_original_exception_survives_all_evidence_sink_failures(self):
        self.api.fail = 'process'
        original = a._persist
        def fail_after_acquisition(owner):
            if any(ref.kind == 'process' for ref in owner._resources.references):
                raise OSError('disk full')
            return original(owner)
        with patch.object(a, '_persist', side_effect=fail_after_acquisition):
            with self.assertRaisesRegex(OSError, '^process$'):
                self.registry.launch(self.policy)
        actor = self.registry._owners[0]
        self.assertEqual(actor.state, 'QUARANTINED')
        self.assertTrue(actor._evidence_errors)
        self.assertIn(('close', 300), self.api.calls)

    def test_cleanup_sink_failure_after_acquisition_does_not_skip_cleanup(self):
        actor = self.launch()
        with patch.object(a, '_persist', side_effect=OSError('disk full')):
            actor.close('test')
        self.assertIn(('close', 300), self.api.calls)
        self.assertIn(('close', 301), self.api.calls)
        self.assertEqual(actor.state, 'QUARANTINED')

    def test_cleanup_failure_keeps_context_and_never_retries_unknown_close(self):
        actor = self.launch(); self.api.close_ok = False
        actor.close('test'); calls = list(self.api.calls)
        actor.close('again')
        self.assertEqual(calls, self.api.calls)
        self.assertEqual(actor.state, 'QUARANTINED')
        self.assertIs(self.registry._owners[0], actor)
        self.assertEqual(self.api.calls.count(('close', 300)), 1)

    def test_unknown_terminal_preserves_process_thread_job_and_profile(self):
        actor = self.launch(); self.api.wait_result = 258
        actor.close('test')
        self.assertEqual(actor.state, 'QUARANTINED')
        for h in (200, 300, 301): self.assertNotIn(('close', h), self.api.calls)
        self.assertTrue({'process', 'primary_thread', 'job', 'profile'} <= {x.label for x in actor._resources.unresolved})

    def test_stage_hash_size_and_path_fail_before_process_creation(self):
        for policy in (replace(self.policy, max_stage_bytes=1),
                       replace(self.policy, files=(('actor.py', '0' * 64),)),
                       replace(self.policy, files=(('../actor.py', '0' * 64),)),
                       replace(self.policy, files=(('Actor.py', '0' * 64), ('actor.py', '0' * 64)))):
            with self.subTest(policy=policy):
                with self.assertRaises(ValueError): self.registry.launch(policy)
        self.assertFalse(any(x[0] == 'create' for x in self.api.calls))

    def test_policy_rejects_missing_or_boolean_timing_budget(self):
        for field in ('readiness_timeout_ns', 'lifetime_timeout_ns', 'sample_age_cap_ns', 'max_probe_ns'):
            for value in (0, True, -1):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError): self.registry.launch(replace(self.policy, **{field: value}))

    def test_clock_timeout_during_launch_cannot_return_live_owner(self):
        def delayed_resume(handle): self.clock.value += 2_000_000_000; return 1
        self.api.ResumeThread = delayed_resume
        with self.assertRaises(ValueError): self.launch()
        self.assertNotEqual(self.registry._owners[0].state, 'RUNNING_UNBOUND')
        self.assertIn(('close', 300), self.api.calls)

    def test_public_diagnostics_do_not_export_native_handles_paths_or_errors(self):
        actor = self.launch()
        actor._evidence_errors.append(ValueError('hidden truth.canary and secret path'))
        diagnostic = actor.diagnostics()
        self.assertEqual(set(diagnostic), {'state', 'instance_id', 'evidence_complete', 'cleanup_complete'})
        self.assertNotIn('truth', str(diagnostic)); self.assertNotIn(str(self.root), str(diagnostic))

    def test_direct_owner_construction_and_process_adoption_are_unavailable(self):
        with self.assertRaises(ValueError): a.ActorOwner(None)
        with self.assertRaises(ValueError): self.registry.launch(self.policy, pid=400, alive=True)

    def test_registry_retains_owner_before_first_native_acquisition(self):
        original = self.api.user_sid
        def inspect_registry(*, owner):
            self.assertIs(self.registry._owners[0]._resources, owner)
            return original(owner=owner)
        self.api.user_sid = inspect_registry
        self.launch()

    def test_reentrant_close_during_launch_never_resumes_retired_actor(self):
        def inspect(*args, **kwargs):
            actor = self.registry._owners[0]
            try: actor.close('reentrant')
            except ValueError: pass
            return dict(is_appcontainer=True, sid_matches=True, win32k_disabled=True,
                child_process_restricted=True, in_job=True, job_limits_match=True,
                capability_count=0, creation_filetime=123456)
        self.api.inspect_process = inspect
        with self.assertRaises(ValueError): self.launch()
        self.assertNotIn(('resume',), self.api.calls)

    def test_wrong_thread_close_does_not_close_inflight_original_reference(self):
        actor = self.launch(); failures = []
        def wrong_thread():
            try: actor.close('wrong thread')
            except ValueError: failures.append(True)
        thread = threading.Thread(target=wrong_thread); thread.start(); thread.join()
        self.assertEqual(failures, [True]); self.assertNotIn(('close', 300), self.api.calls)
        actor.close('owner teardown')
        self.assertEqual(actor.state, 'CLOSED')

    def test_final_launch_report_cannot_rejuvenate_readiness_or_life(self):
        original = a._persist
        def slow_report(owner):
            original(owner)
            if owner.state == 'RUNNING_UNBOUND': self.clock.value += 50_000_000
        with patch.object(a, '_persist', side_effect=slow_report):
            with self.assertRaises(ValueError): self.launch()
        self.assertNotEqual(self.registry._owners[0].state, 'RUNNING_UNBOUND')
        self.assertIn(('close', 300), self.api.calls)

    def test_unconfirmed_root_acl_cannot_write_private_receipt(self):
        self.api.fail = 'acl'
        with self.assertRaises(OSError): self.launch()
        actor = self.registry._owners[0]
        self.assertFalse((actor._root / 'receipt.json').exists())
        self.assertFalse(actor.diagnostics()['evidence_complete'])

    def test_caught_registry_launch_reentry_cannot_create_second_actor(self):
        def assign(*args):
            try: self.registry.launch(self.policy)
            except ValueError: pass
            return True
        self.api.AssignJob = assign
        with self.assertRaises(ValueError): self.launch()
        self.assertEqual(len(self.registry._owners), 1)
        self.assertNotIn(('resume',), self.api.calls)

    def test_retained_endpoints_stay_owned_until_explicit_close(self):
        actor = self.launch()
        self.assertFalse(actor._resources.find('input_write').attempted)
        self.assertFalse(actor._resources.find('output_read').attempted)
        actor.close('normal')
        self.assertIn(('close', 103), self.api.calls)
        self.assertIn(('close', 104), self.api.calls)

    def test_private_receipt_binds_stage_hashes_and_preserves_primary_failure(self):
        import json
        self.api.fail = 'process'
        with self.assertRaisesRegex(OSError, '^process$'): self.launch()
        actor = self.registry._owners[0]
        record = json.loads((actor._root / 'receipt.json').read_bytes())
        self.assertIn('primary_error', record, 'private evidence discarded original failure')
        self.assertEqual(record['primary_error']['type_name'], 'OSError')
        self.assertEqual(record['primary_error']['message'], 'process')
        self.assertEqual(dict(record['provenance']['source_hashes'])['stage:actor.py'],
                         hashlib.sha256(b'FAKE actor, never run').hexdigest())
        self.assertTrue(record['cleanup']['resources_complete'])

    def test_all_four_inheritance_masks_are_captured_and_require_exact_int(self):
        import enum
        class Mask(enum.IntEnum): ZERO = 0; ONE = 1
        class Number(int): pass
        original = self.api.handle_flags
        for convert in (bool, Mask, Number, float, lambda value: None, lambda value: 3):
            with self.subTest(convert=convert):
                seen = []
                def read(handle):
                    seen.append(handle)
                    return convert(original(handle))
                self.api.handle_flags = read
                self.api.calls.clear()
                with self.assertRaises(ValueError): self.launch()
                owner = self.registry._owners[-1]
                self.assertEqual(seen, [owner._resources.find(label).native for label in
                    ('input_read', 'output_write', 'input_write', 'output_read')])
                self.assertNotIn(('resume',), self.api.calls)


if __name__ == '__main__': unittest.main()
