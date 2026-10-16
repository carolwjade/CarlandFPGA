"""Run one temporary, CPU-only AppContainer probe; preserve every attempt.

The caller is the trusted fixture parent, never a long-lived service or Codex.
No API accepts an existing sandbox identity or existing output directory.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import uuid
import zipfile

from .policy import create_run_directory, minimal_environment, evaluate, parse_fixture

CONTRACT = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def stage_runtime(base: Path, stage: Path):
    """Copy an app-local CPython 3.12 runtime; never ACL or link source files."""
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('this P1a stage manifest supports CPython 3.12 only')
    manifest = []

    def source_bytes(source):
        if source.is_symlink() or (hasattr(source, 'is_junction') and source.is_junction()):
            raise ValueError(f'reparse runtime source rejected: {source}')
        return source.read_bytes()

    def copy(source, relative):
        data = source_bytes(source)
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest.append({'source': str(source), 'stage': relative,
                         'size': len(data), 'sha256': digest(data)})

    for name in ('python.exe', 'python3.dll', 'python312.dll',
                 'vcruntime140.dll', 'vcruntime140_1.dll'):
        copy(base / name, name)
    for name in ('_ctypes.pyd', 'libffi-8.dll'):
        copy(base / 'DLLs' / name, f'DLLs/{name}')
    excluded = {'site-packages', '__pycache__', 'test', 'tests', 'idlelib',
                'tkinter', 'turtledemo', 'ensurepip'}
    with zipfile.ZipFile(stage / 'python312.zip', 'x', compression=zipfile.ZIP_STORED) as archive:
        for source in sorted((base / 'Lib').rglob('*.py')):
            relative = source.relative_to(base / 'Lib')
            if excluded.intersection(relative.parts):
                continue
            data = source_bytes(source)
            archive.writestr(relative.as_posix(), data)
            manifest.append({'source': str(source), 'zip_member': relative.as_posix(),
                             'size': len(data), 'sha256': digest(data)})
    (stage / 'python312._pth').write_text('python312.zip\nDLLs\n.\n', encoding='ascii')
    copy(Path(__file__).with_name('fixture.py'), 'fixture.py')
    for name in ('python312.zip', 'python312._pth'):
        data = (stage / name).read_bytes()
        manifest.append({'stage': name, 'size': len(data), 'sha256': digest(data)})
    return manifest


def run(evidence_parent: Path, *, timeout_ms=15000):
    from . import win32 as w
    if not 100 <= timeout_ms <= 30000:
        raise ValueError('timeout must be 100..30000 ms')
    run_id = 'r-' + uuid.uuid4().hex[:12]
    root = create_run_directory(evidence_parent, run_id)
    result = {
        'schema': 1, 'task': 'A-G03-isolation-prototype-20261015-v1',
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'run_directory': str(root), 'requirements_sha256': CONTRACT,
        'profile_name': 'DeepEye.P1a.' + uuid.uuid4().hex,
        'requested_policy': {'appcontainer': True, 'capabilities': [], 'win32k_disabled': True,
                             'child_process_restricted': True, 'suspended': True,
                             'job_kill_on_close': True, 'job_active_process_limit': 1,
                             'job_process_memory_limit': 268435456, 'job_ui_restrictions': 255},
        'created_objects': [], 'acl_changes': [], 'parent_controls': {}, 'lifecycle': {},
        'not_run': ['LPAC', 'GDI_capture', 'DXGI', 'WGC', 'shared_texture', 'GPU_inference',
                    'four_product_processes', 'FPGA_hardware', 'G03_formal_acceptance'],
    }
    receipt = root / 'receipt.json'
    handles, pi, profile_sid, profile_created, profile_path, job = [], None, w.P(), False, None, None
    output_read = None
    # Keep the new directory empty until its inheritable ACL is installed.
    # The receipt is saved before profile/process creation, and the exception
    # path below also records an ACL-preparation failure without creating them.
    try:
        sources = {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
        result['launcher_source_hashes'] = sources
        user = w.user_sid()
        result['acl_changes'].append(w.set_new_object_acl(root, root, user))
        save(receipt, result)
        w.check_hr(w.CreateProfile(result['profile_name'], result['profile_name'],
                                  'Temporary DeepEye CPU boundary fixture', None, 0,
                                  C.byref(profile_sid)), 'CreateAppContainerProfile')
        profile_created = True
        result['profile_sid'] = w.sid_text(profile_sid)
        result['created_objects'].append({'kind': 'AppContainerProfile', 'name': result['profile_name'],
                                          'sid': result['profile_sid']})
        save(receipt, result)
        raw_path = W.LPWSTR()
        w.check_hr(w.GetProfilePath(result['profile_sid'], C.byref(raw_path)), 'GetAppContainerFolderPath')
        try:
            profile_path = Path(raw_path.value)
            result['profile_path'] = str(profile_path)
            result['profile_directory_existed'] = profile_path.is_dir()
        finally:
            w.CoTaskMemFree(C.cast(raw_path, w.P))
        stage = root / 'r'
        stage.mkdir()
        result['acl_changes'].append(w.set_new_object_acl(stage, root, user, result['profile_sid']))
        manifest = stage_runtime(Path(sys.base_prefix), stage)
        save(root / 'runtime_manifest.json', manifest)
        result['runtime_manifest_sha256'] = digest((root / 'runtime_manifest.json').read_bytes())
        model = stage / 'model.json'
        model.write_text('{"weights":[2,3,5]}', encoding='utf-8')
        truth = root / 'truth.canary'
        secret = os.urandom(32)
        truth.write_bytes(secret)
        result['created_objects'].extend([{'kind': 'runtime_stage', 'path': str(stage)},
                                          {'kind': 'truth_canary', 'path': str(truth)}])
        controls = result['parent_controls']
        controls.update(truth_exists=truth.is_file(), truth_read_ok=truth.read_bytes() == secret,
                        model_hash_ok=digest(model.read_bytes()) == digest(b'{"weights":[2,3,5]}'))
        result['model_sha256'] = digest(model.read_bytes())
        result['truth_canary_sha256'] = digest(secret)
        sa = w.SA(C.sizeof(w.SA), None, True)
        canary_handle = w.CreateFileW(str(truth), 0x80000000, 7, C.byref(sa), 3, 0x80, None)
        w.check(canary_handle != C.c_void_p(-1).value, 'CreateFileW canary parent')
        handles.append(canary_handle)
        controls['canary_handle_read_ok'] = w.read(canary_handle, 32) == secret
        controls['process_access_ok'] = True
        for access in (8, 16, 32, 64, 128):
            own = w.OpenProcess(access, False, os.getpid())
            w.check(own, f'OpenProcess parent positive control {access}')
            w.CloseHandle(own)
        input_read, input_write = w.pipe()
        handles.extend([input_read, input_write])
        output_read, output_write = w.pipe()
        handles.extend([output_read, output_write])
        for handle in (input_write, output_read):
            w.check(w.SetHandleInformation(handle, 1, 0), 'SetHandleInformation parent endpoint')
        result['inheritance'] = {'allowed': [input_read, output_write],
                                  'deliberately_excluded_inheritable_canary': canary_handle,
                                  'excluded_canary_inheritable': bool(w.handle_flags(canary_handle) & 1),
                                  'allowed_flags': [w.handle_flags(input_read), w.handle_flags(output_write)],
                                  'parent_endpoint_flags': [w.handle_flags(input_write), w.handle_flags(output_read)]}
        inheritance = result['inheritance']
        inheritance['verified'] = (inheritance['excluded_canary_inheritable'] is True and
                                   inheritance['allowed_flags'] == [1, 1] and
                                   inheritance['parent_endpoint_flags'] == [0, 0])
        if not inheritance['verified']:
            raise RuntimeError('handle inheritance flags failed independent readback')
        result['created_objects'].extend([
            {'kind': 'anonymous_pipe', 'child_access': 'read', 'child_handle': input_read},
            {'kind': 'anonymous_pipe', 'child_access': 'write', 'child_handle': output_write}])
        job = w.create_job()
        handles.append(job)
        result['created_objects'].append({'kind': 'anonymous_job', 'handle': job})
        save(receipt, result)
        # CreateProcess needs this nonsecret base path to resolve/reroute the
        # new AppContainer profile. It grants no access to the base directory.
        environment = minimal_environment(profile_path / 'Temp', os.environ['SystemRoot'],
                                          os.environ['LOCALAPPDATA'])
        result['environment_keys'] = sorted(environment)
        argv = ['-I', '-S', '-B', '-X', 'utf8', str(stage / 'fixture.py'), str(model), str(truth),
                os.getpid(), canary_handle, input_read, output_write]
        pi = w.create_suspended(stage / 'python.exe', argv, stage, environment,
                                profile_sid, input_read, output_write)
        result['pid'] = pi.dwProcessId
        result['created_objects'].append({'kind': 'process', 'pid': pi.dwProcessId})
        save(receipt, result)
        w.check(w.AssignJob(job, pi.hProcess), 'AssignProcessToJobObject')
        trusted = w.inspect_process(pi.hProcess, job, result['profile_sid'])
        result['trusted'] = trusted
        required = ('is_appcontainer', 'sid_matches', 'win32k_disabled', 'child_process_restricted',
                    'in_job', 'job_limits_match')
        if not all(trusted[name] is True for name in required) or trusted['capability_count'] != 0:
            raise RuntimeError('independent suspended-process inspection failed; refusing resume')
        for handle in (input_read, output_write):
            w.CloseHandle(handle)
            handles.remove(handle)
        w.write(input_write, b'authorized-causal-observation-v1\n')
        w.CloseHandle(input_write)
        handles.remove(input_write)
        save(receipt, result)
        previous = w.ResumeThread(pi.hThread)
        if previous != 1:
            raise RuntimeError(f'ResumeThread expected one suspended count, got {previous}')
        trusted['resumed_after_verification'] = True
        state = w.Wait(pi.hProcess, timeout_ms)
        if state != 0:
            raise TimeoutError(f'fixture wait failed or timed out: 0x{state:08x}')
        result['lifecycle']['terminal'] = True
        code = W.DWORD()
        w.check(w.GetExitCodeProcess(pi.hProcess, C.byref(code)), 'GetExitCodeProcess')
        result['lifecycle']['exit_code'] = code.value
        raw = w.read(output_read)
        (root / 'fixture_stdout.bin').write_bytes(raw)
        result['fixture'] = parse_fixture(raw, code.value, canary_handle)
    except BaseException as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error),
                           'winerror': getattr(error, 'winerror', None)}
        (root / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        life = result['lifecycle']
        if pi:
            try:
                if w.Wait(pi.hProcess, 0) != 0:
                    w.check(w.TerminateProcess(pi.hProcess, 0xdead), 'TerminateProcess owned fixture')
                    life['terminated_by_launcher'] = True
                life['terminal'] = w.Wait(pi.hProcess, 5000) == 0
                code = W.DWORD()
                w.check(w.GetExitCodeProcess(pi.hProcess, C.byref(code)), 'GetExitCodeProcess cleanup')
                life['exit_code'] = code.value
            except BaseException as error:
                life['termination_error'] = str(error)
            finally:
                w.CloseHandle(pi.hThread)
                w.CloseHandle(pi.hProcess)
        if output_read and not (root / 'fixture_stdout.bin').exists():
            try:
                (root / 'fixture_stdout.bin').write_bytes(w.available_output(output_read))
            except BaseException as error:
                life['output_capture_error'] = str(error)
        for handle in reversed(handles):
            w.CloseHandle(handle)
        if profile_created and (pi is None or life.get('terminal') is True):
            hr = w.DeleteProfile(result['profile_name'])
            life['profile_delete_hresult'] = f'0x{hr & 0xffffffff:08x}'
            life['profile_directory_absent'] = profile_path is None or not profile_path.exists()
            life['profile_deleted'] = hr >= 0 and life['profile_directory_absent']
        elif profile_created:
            life['profile_deleted'] = False
            life['profile_retained_reason'] = 'process termination unconfirmed; do not remove live profile'
        if profile_sid:
            w.FreeSid(profile_sid)
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        result['verdict'] = evaluate(result)
        save(receipt, result)
    return receipt, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-parent', required=True, type=Path)
    parser.add_argument('--timeout-ms', type=int, default=15000)
    args = parser.parse_args()
    path, result = run(args.evidence_parent, timeout_ms=args.timeout_ms)
    print(json.dumps({'receipt': str(path), 'verdict': result['verdict'],
                      'error': result.get('error')}, ensure_ascii=False))
    return 0 if result['verdict']['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
