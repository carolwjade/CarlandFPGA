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
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    # Same owned directory, no global configuration. Failed writes are preserved;
    # never delete a partially persisted attempt or rewrite another run's files.
    with temporary.open('x', encoding='utf-8') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


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


class RunEvidence(dict):
    """JSON-compatible evidence plus a strong live ownership/recovery context.

    Keep this returned object alive when ownership is unresolved. Serialization
    deliberately excludes the live context; a disk receipt cannot recover handles.
    """
    ownership = None
    primary_exception = None


def run(evidence_parent: Path, *, timeout_ms=15000, api=None, report_save=None, runtime_stage=None):
    from dataclasses import asdict
    from .owned_resources import OwnedResources, error_info
    from .resource_cleanup import Provenance, Outcome
    from .windows_cleanup import WindowsCleanupBackend
    if api is None:
        from . import win32 as api
    report_save = save if report_save is None else report_save
    runtime_stage = stage_runtime if runtime_stage is None else runtime_stage
    w = api
    if not 100 <= timeout_ms <= 30000:
        raise ValueError('timeout must be 100..30000 ms')
    run_id = 'r-' + uuid.uuid4().hex[:12]
    root = create_run_directory(evidence_parent, run_id)
    sources = {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
    provenance = Provenance('DEEPEYE-IMPLEMENTATION-20261014/v1', run_id, run_id,
                            tuple(sorted(sources.items())) + (('requirements', CONTRACT),))
    owner = OwnedResources(provenance)
    backend = WindowsCleanupBackend(w, owner)
    result = RunEvidence({
        'schema': 2, 'task': 'A-G03-isolation-launcher-cleanup-20261019-v1',
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'run_directory': str(root), 'requirements_sha256': CONTRACT,
        'profile_name': 'DeepEye.P1a.' + uuid.uuid4().hex,
        'launcher_source_hashes': sources,
        'requested_policy': {'appcontainer': True, 'capabilities': [], 'win32k_disabled': True,
                             'child_process_restricted': True, 'suspended': True,
                             'job_kill_on_close': True, 'job_active_process_limit': 1,
                             'job_process_memory_limit': 268435456, 'job_ui_restrictions': 255},
        'created_objects': [], 'acl_changes': [], 'parent_controls': {}, 'lifecycle': {},
        'evidence_errors': [], 'cleanup_events': [],
        'not_run': ['LPAC', 'GDI_capture', 'DXGI', 'WGC', 'shared_texture', 'GPU_inference',
                    'four_product_processes', 'FPGA_hardware', 'G03_formal_acceptance'],
    })
    result.ownership = owner
    receipt = root / 'receipt.json'
    primary, captured = None, False
    output_ref = None

    def persist(target, value):
        try:
            report_save(target, value)
        except BaseException as error:
            result['evidence_errors'].append(asdict(error_info('persist:' + target.name, error)))
            raise

    def audit(event):
        result['cleanup_events'].append({
            'sequence': event.sequence, 'phase': event.phase, 'action': event.action,
            'resource_id': event.resource_id,
            'outcome': event.operation.outcome.value if event.operation else None,
            'error': asdict(event.operation.error) if event.operation and event.operation.error else None,
        })
        persist(receipt, result)

    def capture_output():
        nonlocal captured
        raw = w.available_output(output_ref.native)
        if type(raw) is not bytes or len(raw) > 8192:
            raise ValueError('bounded fixture output exceeded')
        (root / 'fixture_stdout.bin').write_bytes(raw)
        captured = True
        return raw

    # No evidence files are written until the new root's ACL is installed.
    try:
        user = w.user_sid(owner=owner)
        result['acl_changes'].append(w.set_new_object_acl(root, root, user, owner=owner))
        persist(receipt, result)
        profile_sid = w.create_profile(result['profile_name'], owner=owner)
        # Profile and SID are already in owner before conversion/persistence.
        result['profile_sid'] = w.sid_text(profile_sid, owner=owner)
        result['created_objects'].append({'kind': 'AppContainerProfile', 'name': result['profile_name'],
                                          'sid': result['profile_sid']})
        persist(receipt, result)
        profile_path = w.profile_path(result['profile_sid'], owner=owner)
        owner.set_profile_path(profile_path)
        result['profile_path'] = str(profile_path)
        stage = root / 'r'
        stage.mkdir()
        result['acl_changes'].append(w.set_new_object_acl(stage, root, user, result['profile_sid'], owner=owner))
        manifest = runtime_stage(Path(sys.base_prefix), stage)
        persist(root / 'runtime_manifest.json', manifest)
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
        result['model_sha256'], result['truth_canary_sha256'] = digest(model.read_bytes()), digest(secret)
        canary = w.own_canary(truth, owner=owner)
        canary_handle = canary.native
        controls['canary_handle_read_ok'] = w.canary_read(canary_handle, 32) == secret
        controls['process_access_ok'] = w.parent_controls(owner=owner)
        input_read, input_write = w.pipe(owner=owner, read_label='input_read', write_label='input_write')
        output_read, output_write = w.pipe(owner=owner, read_label='output_read', write_label='output_write')
        output_ref = owner.find('output_read')
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
        job = w.create_job(owner=owner)
        result['created_objects'].append({'kind': 'anonymous_job', 'handle': job})
        persist(receipt, result)
        environment = minimal_environment(profile_path / 'Temp', os.environ['SystemRoot'], os.environ['LOCALAPPDATA'])
        result['environment_keys'] = sorted(environment)
        argv = ['-I', '-S', '-B', '-X', 'utf8', str(stage / 'fixture.py'), str(model), str(truth),
                os.getpid(), canary_handle, input_read, output_write]
        pi = w.create_suspended(stage / 'python.exe', argv, stage, environment,
                                profile_sid, input_read, output_write, owner=owner)
        # Both native handles were registered inside the acquisition helper.
        result['pid'] = pi.dwProcessId
        result['created_objects'].append({'kind': 'process', 'pid': pi.dwProcessId})
        persist(receipt, result)
        w.check(w.AssignJob(job, pi.hProcess), 'AssignProcessToJobObject')
        trusted = w.inspect_process(pi.hProcess, job, result['profile_sid'], owner=owner)
        result['trusted'] = trusted
        required = ('is_appcontainer', 'sid_matches', 'win32k_disabled', 'child_process_restricted',
                    'in_job', 'job_limits_match')
        if not all(trusted[name] is True for name in required) or trusted['capability_count'] != 0:
            raise RuntimeError('independent suspended-process inspection failed; refusing resume')
        for label in ('input_read', 'output_write'):
            owner.release_checked(owner.find(label))
        w.write(input_write, b'authorized-causal-observation-v1\n')
        owner.release_checked(owner.find('input_write'))
        persist(receipt, result)
        previous = w.ResumeThread(pi.hThread)
        if previous != 1:
            raise RuntimeError(f'ResumeThread expected one suspended count, got {previous}')
        trusted['resumed_after_verification'] = True
        state = w.Wait(pi.hProcess, timeout_ms)
        if state != 0:
            raise TimeoutError(f'fixture wait failed or timed out: 0x{state:08x}')
        result['lifecycle']['exit_code'] = w.exit_code(pi.hProcess)
        raw = capture_output()  # Peek + bounded read; never an EOF-dependent read.
        result['fixture'] = parse_fixture(raw, result['lifecycle']['exit_code'], canary_handle)
    except BaseException as error:
        primary = error
        result.primary_exception = error
        primary_info = error_info('primary', error)
        result['error'] = {**asdict(primary_info), 'type': primary_info.type_name,
                           'winerror': getattr(error, 'winerror', None)}
        try:
            (root / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        except BaseException as write_error:
            result['evidence_errors'].append(asdict(error_info('failure.txt', write_error)))
    finally:
        # Bounded diagnostic capture precedes closing the held reader. Reporting
        # failures are contained and can never jump over coordinator cleanup.
        if output_ref is not None and not captured and not output_ref.attempted:
            try:
                capture_output()
            except BaseException as error:
                result['evidence_errors'].append(asdict(error_info('output_capture', error)))
        try:
            cleanup = owner.cleanup(backend, audit, primary)
            result['cleanup'] = {
                'resources_complete': cleanup.resources_complete,
                'evidence_complete': cleanup.evidence_complete and not result['evidence_errors'],
                'coordinator_success': cleanup.success,
                'cleanup_errors': [asdict(error) for error in cleanup.cleanup_errors],
                'audit_errors': [asdict(error) for error in cleanup.audit_errors],
            }
        except BaseException as error:
            result['cleanup'] = {'resources_complete': False, 'evidence_complete': False,
                                  'coordinator_error': asdict(error_info('coordinator', error))}
        result['cleanup']['owner_errors'] = [asdict(error) for error in owner.errors]
        result['cleanup']['resources'] = owner.summary()
        result['cleanup']['unresolved'] = [ref.resource_id for ref in owner.unresolved]
        processes = [ref for ref in owner.references if ref.kind == 'process']
        result['lifecycle'].update(
            terminal=all(ref.terminal_confirmed for ref in processes) if processes else False,
            terminated_by_launcher=backend.terminated,
            profile_deleted=owner.profile is not None and owner.profile.outcome is Outcome.CONFIRMED,
            profile_directory_absent=backend.profile_absence,
            profile_delete_hresult=backend.profile_delete_hresult)
        if len(processes) == 1 and processes[0].resource_id in backend.exit_codes:
            result['lifecycle']['exit_code'] = backend.exit_codes[processes[0].resource_id]
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        result['verdict'] = evaluate(result)
        try:
            persist(receipt, result)
        except BaseException:
            result['cleanup']['evidence_complete'] = False
            result['verdict'] = evaluate(result)
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
