"""Main-only, gated real Windows checks; no fake native success results."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
import traceback
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
DEEPEYE = PRODUCT / 'competition/deepeye'
sys.path.insert(0, str(DEEPEYE))
LIVE_RESULTS = []
LIVE_OWNERS = []

def save_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def hold_unresolved():
    held = [owner for owner in LIVE_OWNERS if owner.unresolved]
    if not held:
        return
    print(json.dumps({'status': 'HOLD_UNRESOLVED_OWNERSHIP', 'runner_pid': os.getpid(),
                      'owner_ids': [getattr(x.provenance, 'owner_id', None) for x in held]}), flush=True)
    # No automatic native recovery. Retain the live objects even if stdin is EOF.
    while True:
        line = sys.stdin.readline()
        if not line:
            threading.Event().wait()
        elif line.strip() == 'status':
            print(json.dumps({'held': [[r.resource_id for r in x.unresolved]
                                      for x in held]}), flush=True)
        else:
            print('Only read-only status is supported; no recovery performed.', flush=True)

class ObservedNativeApi:
    def __init__(self, actual):
        self.actual = actual
        self.owner = None
        self.events = []

    def __getattr__(self, name):
        return getattr(self.actual, name)

    def remember_owner(self, owner):
        self.owner = owner
        if not any(owner is value for value in LIVE_OWNERS):
            LIVE_OWNERS.append(owner)

    def user_sid(self, *args, **kwargs):
        # Capture the owner before the first native acquisition, even if the
        # launcher later raises unexpectedly instead of returning RunEvidence.
        self.remember_owner(kwargs['owner'])
        return self.actual.user_sid(*args, **kwargs)

    def create_suspended(self, *args, **kwargs):
        self.remember_owner(kwargs['owner'])
        pi = self.actual.create_suspended(*args, **kwargs)
        self.events.append({'action': 'actual_create_suspended_return', 'pid': pi.dwProcessId,
                            'process_handle': pi.hProcess, 'thread_handle': pi.hThread})
        return pi

    def Wait(self, handle, timeout):
        value = self.actual.Wait(handle, timeout)
        last_error = ctypes.get_last_error()
        self.events.append({'action': 'actual_wait', 'handle': handle,
                            'timeout_ms': timeout, 'result': value, 'last_error': last_error})
        ctypes.set_last_error(last_error)
        return value

    def CloseHandle(self, handle):
        # This extra readback occurs before the real close on the original handle.
        previous_last_error = ctypes.get_last_error()
        if self.owner is not None:
            process = next((r for r in self.owner.references
                            if r.kind == 'process' and r.native == handle), None)
            if process is not None:
                state = self.actual.Wait(handle, 0)
                try:
                    exit_code = self.actual.exit_code(handle)
                    error = None
                except BaseException as exc:
                    exit_code, error = None, {'type': type(exc).__name__, 'message': str(exc)}
                self.events.append({'action': 'independent_terminal_before_close',
                                    'resource_id': process.resource_id, 'handle': handle,
                                    'wait_result': state, 'exit_code': exit_code, 'error': error})
        ctypes.set_last_error(previous_last_error)
        value = self.actual.CloseHandle(handle)
        last_error = ctypes.get_last_error()
        self.events.append({'action': 'actual_close', 'handle': handle,
                            'result': bool(value), 'last_error': last_error})
        ctypes.set_last_error(last_error)
        return value

    def TerminateProcess(self, handle, code):
        value = self.actual.TerminateProcess(handle, code)
        last_error = ctypes.get_last_error()
        self.events.append({'action': 'actual_terminate', 'handle': handle,
                            'code': code, 'result': bool(value), 'last_error': last_error})
        ctypes.set_last_error(last_error)
        return value

    def DeleteProfile(self, name):
        value = self.actual.DeleteProfile(name)
        last_error = ctypes.get_last_error()
        self.events.append({'action': 'actual_delete_profile', 'profile_name': name, 'hresult': value})
        ctypes.set_last_error(last_error)
        return value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'attempt-[0-9]{2}', args.attempt)
    assert os.name == 'nt' and sys.version_info[:2] == (3, 12)
    gate = json.loads((HERE / 'native-execution-gate.json').read_text(encoding='utf-8'))
    assert gate['main_accepted_independent_review'] is True
    manifest_path = ROOT / gate['source_manifest']
    assert digest(manifest_path) == gate['source_manifest_sha256']
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    for name, expected in manifest.items():
        assert digest(PRODUCT / name) == expected['sha256'], name
    attempt = HERE / args.attempt
    attempt.mkdir(exist_ok=False)
    save_new(attempt / 'preflight.json', {'runner_pid': os.getpid(), 'gate': gate,
                                         'sources': manifest, 'python': sys.version})
    os.environ['DEEPEYE_ISOLATION_EVIDENCE_PARENT'] = str(attempt)
    from simulation.isolation import prototype, win32
    module_path = DEEPEYE / 'tests/isolation/test_windows_live.py'
    spec = importlib.util.spec_from_file_location('main_native_tests', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_run = prototype.run
    records = []
    def observed_run(parent, **kwargs):
        assert 'api' not in kwargs
        observer = ObservedNativeApi(win32)
        receipt, evidence = original_run(parent, api=observer, **kwargs)
        LIVE_RESULTS.append(evidence)
        observation = {'events': observer.events, 'receipt_path': str(receipt),
                       'unresolved': [ref.resource_id for ref in evidence.ownership.unresolved]}
        path = evidence.get('profile_path')
        observation['profile_absence_after_return'] = None
        if path:
            profile = Path(path)
            assert profile.is_absolute() and evidence['profile_name'].startswith('DeepEye.P1a.')
            try:
                profile.stat()
                observation['profile_absence_after_return'] = False
            except FileNotFoundError:
                observation['profile_absence_after_return'] = True
            except OSError as exc:
                observation['profile_stat_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        folder = receipt.parent
        save_new(folder / 'main-observation.json', observation)
        save_new(folder / 'main-returned-memory.json', evidence)
        records.append({'run_directory': str(folder), 'case_verdict': evidence['verdict'],
                        'observation_sha256': digest(folder / 'main-observation.json'),
                        'memory_sha256': digest(folder / 'main-returned-memory.json')})
        hold_unresolved()
        return receipt, evidence
    prototype.run = observed_run
    names = [
        'test_real_boundary_and_profile_cleanup',
        'test_timeout_is_failed_and_own_process_profile_are_cleaned',
        'test_persistence_failure_after_process_creation_still_cleans_owned_objects',
    ]
    passed = True
    for name in names:
        count_before = len(records)
        with (attempt / (name + '.unittest.log')).open('x', encoding='utf-8') as log:
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(module.WindowsLiveTests(name))
        assert len(records) == count_before + 1, 'Named native path did not return one result'
        evidence = LIVE_RESULTS[-1]
        observation = json.loads((Path(evidence['run_directory']) / 'main-observation.json').read_text(encoding='utf-8'))
        terminal = [event for event in observation['events']
                    if event['action'] == 'independent_terminal_before_close']
        case_pass = result.wasSuccessful() and not result.skipped
        case_pass = case_pass and len(terminal) == 1 and terminal[0]['wait_result'] == 0
        case_pass = case_pass and terminal[0]['error'] is None
        case_pass = case_pass and observation['profile_absence_after_return'] is True
        case_pass = case_pass and not observation['unresolved']
        records[-1].update(test=name, test_passed=case_pass,
                           tests_run=result.testsRun, skipped=len(result.skipped))
        print(json.dumps(records[-1], ensure_ascii=False), flush=True)
        if not case_pass:
            passed = False
            break
    for name, expected in manifest.items():
        assert digest(PRODUCT / name) == expected['sha256'], name
    save_new(attempt / 'campaign-result.json', {'passed': passed and len(records) == 3,
                                               'cases': records, 'formal_acceptance': 'not_run'})
    return 0 if passed and len(records) == 3 else 1

if __name__ == '__main__':
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
        hold_unresolved()
        raise
    hold_unresolved()
    raise SystemExit(code)
