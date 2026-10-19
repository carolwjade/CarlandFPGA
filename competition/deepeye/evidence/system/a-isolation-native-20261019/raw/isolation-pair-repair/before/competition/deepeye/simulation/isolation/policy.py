"""Pure fail-closed preparation and evidence checks shared by the prototype."""
from pathlib import Path
import json
import math
import re


def create_run_directory(parent: Path, name: str) -> Path:
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', name):
        raise ValueError('run name must be one simple component')
    if name.upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)),
                        *(f'LPT{i}' for i in range(10))}:
        raise ValueError('reserved device name')
    parent = Path(parent).absolute()
    if not parent.is_dir():
        raise ValueError('evidence parent must already exist')
    for part in (parent, *parent.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('reparse ancestors are not allowed')
    target = parent / name
    target.mkdir(exist_ok=False)
    return target


def minimal_environment(temp: Path, system_root: str, local_appdata: str) -> dict[str, str]:
    return {'SystemRoot': system_root, 'WINDIR': system_root,
            'TEMP': str(temp), 'TMP': str(temp), 'LOCALAPPDATA': local_appdata}


def evaluate(evidence: dict) -> dict:
    failures = []
    checks = {
        'trusted': ('is_appcontainer', 'sid_matches', 'win32k_disabled',
                    'child_process_restricted', 'in_job', 'resumed_after_verification',
                    'job_limits_match'),
        'fixture': ('model_ok', 'pipe_ok'),
        'parent_controls': ('truth_exists', 'truth_read_ok', 'canary_handle_read_ok',
                            'model_hash_ok', 'process_access_ok'),
        'lifecycle': ('terminal', 'profile_deleted'),
        'inheritance': ('verified',),
    }
    for group, names in checks.items():
        for name in names:
            if evidence.get(group, {}).get(name) is not True:
                failures.append(f'{group}.{name}')
    expectations = [('trusted', 'capability_count', 0), ('fixture', 'truth_open_error', 5)]
    for group, name, expected in expectations:
        if evidence.get(group, {}).get(name) != expected:
            failures.append(f'{group}.{name}')
    fixture = evidence.get('fixture', {})
    exit_code = evidence.get('lifecycle', {}).get('exit_code')
    ordinary_denial = fixture.get('canary_handle_error') == 6 and exit_code == 0
    fatal_denial = (fixture.get('canary_handle_error') == 0xc0000008 and
                    exit_code == 0xc0000008 and fixture.get('fatal_handle_denial_attested') is True and
                    bool(evidence.get('trusted', {}).get('mitigation_raw', {}).get('strict_handle', 0) & 1))
    if not (ordinary_denial or fatal_denial):
        failures.append('canary_denial_and_exit_status')
    errors = evidence.get('fixture', {}).get('process_access_errors', {})
    for access in (8, 16, 32, 64, 128):
        if errors.get(str(access)) != 5:
            failures.append(f'process_access.{access}')
    if evidence.get('error'):
        failures.append('launcher_error')
    cleanup = evidence.get('cleanup', {})
    for name in ('resources_complete', 'evidence_complete'):
        if cleanup.get(name) is not True:
            failures.append('cleanup.' + name)
    for name in ('cleanup_errors', 'audit_errors', 'owner_errors', 'unresolved'):
        if type(cleanup.get(name)) is not list or cleanup[name]:
            failures.append('cleanup.' + name)
    if cleanup.get('coordinator_error'):
        failures.append('cleanup.coordinator_error')
    if type(evidence.get('evidence_errors')) is not list or evidence['evidence_errors']:
        failures.append('evidence_errors')
    return {'passed': not failures, 'failures': failures, 'scope': 'CPU_P1a_only',
            'G03_formal_acceptance': 'not_run'}


def parse_fixture(raw: bytes, exit_code: int, excluded_handle: int) -> dict:
    """A fatal bad-handle status counts only after an exact ordered probe marker."""
    if not raw or len(raw) > 4096:
        raise ValueError('fixture protocol size invalid')
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate fixture field')
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError('nonfinite fixture field')

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('nonfinite fixture number')
        return result

    def extends(previous, current):
        # Reports accumulate probe results. Later frames may add measurements,
        # but cannot change, drop or change the type of any earlier measurement.
        if type(previous) is not type(current):
            return False
        if isinstance(previous, dict):
            return all(key in current and extends(value, current[key])
                       for key, value in previous.items())
        if isinstance(previous, list):
            return len(previous) == len(current) and all(
                extends(old, new) for old, new in zip(previous, current))
        return previous == current

    frames = [json.loads(line, object_pairs_hook=unique_object,
                         parse_constant=reject_constant, parse_float=finite_float)
              for line in raw.decode('utf-8').splitlines()]
    if any(type(frame) is not dict for frame in frames):
        raise ValueError('fixture frames must be objects')
    phases = [frame.get('phase') for frame in frames]
    prefix = ['positive_controls', 'boundaries', 'excluded_handle_attempt']
    if phases not in (prefix, prefix + ['complete']):
        raise ValueError('fixture protocol order invalid')
    if type(frames[2].get('handle')) is not int or frames[2]['handle'] != excluded_handle:
        raise ValueError('canary handle marker mismatch')
    positive, boundary = frames[0].get('result'), frames[1].get('result')
    if type(positive) is not dict or type(boundary) is not dict:
        raise ValueError('fixture results must be objects')
    for key in ('model_ok', 'pipe_ok'):
        if positive.get(key) is not True or boundary.get(key) is not True:
            raise ValueError('positive controls incomplete before handle probe')
    if not extends(positive, boundary):
        raise ValueError('boundary frame changed earlier evidence')
    if any(key in boundary for key in ('canary_handle_error', 'fatal_handle_denial_attested')):
        raise ValueError('handle result appeared before its probe marker')
    if len(frames) == 4:
        if exit_code != 0:
            raise ValueError('completed fixture has an abnormal exit')
        complete = frames[3].get('result')
        if type(complete) is not dict or not extends(boundary, complete):
            raise ValueError('complete frame changed earlier evidence')
        return complete
    if exit_code != 0xc0000008:
        raise ValueError('missing complete frame without STATUS_INVALID_HANDLE')
    result = dict(boundary)
    result.update(canary_handle_error=0xc0000008, fatal_handle_denial_attested=True)
    return result
