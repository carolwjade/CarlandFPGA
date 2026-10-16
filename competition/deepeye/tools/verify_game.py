"""Bounded game reference-test runner. No formal game/board gate is implemented."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid


PRODUCT = Path(__file__).resolve().parents[1]
CHECKOUT = PRODUCT.parents[1]
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
SCOPE = CHECKOUT / 'docs/competition/deepeye-2026/immutable_scope.json'
VERSION = '4.7.2.stable.official.ed1daf0bf'
# Existing official portable Windows build; unknown builds require independent review.
ENGINE_SHA = 'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
CONSOLE_SHA = 'c8f0a6bc45a19b33541501e57f6f7cd972ab18453743266339d495cbbe846643'
GAPS = {
    'editor': ['G02: 200-step real UI recording/replay and saved/reopened layout hashes',
               'G02/G06: independent 36 directed face-pair geometry cases',
               'G02: 1080p/1440p, 125%/150% scaling and camera/control isolation evidence'],
    'sensors': ['G03/G09: independent 3D FDEM reference, mesh convergence and frozen error/noise budget',
                'G03: distance/contrast/orientation/multiple-target matrix with 30 trials per cell',
                'G03/G09: beyond-support response, actual 20 Hz/ADC and physical excitation evidence'],
    'timing': ['C05/G05/G06: complete authenticated PC_DIRECT and HIL control/observation/capture paths',
               'C05: first-send TTL retry/lost ACK/STATE/EVENT same-trace end-to-end fault cases',
               'C05/G05: disconnect/model crash/restart and physical-board execution evidence'],
    'assets': ['G01: B-owned test_asset_contract.gd runnable contract and closed five-class meshes',
               'G01: sourced dimensions/volumes, drill collision envelope and 30-instance loading',
               'G01: licensed final assets and real six-face/oblique/close-up rendered evidence'],
    'secrecy': ['G03: four-process isolation and OS file/screenshot/debug ACL enforcement',
                'G03: same observations/different far-field layouts command-equivalence traces',
                'G03: restricted controller/schema and no truth/oracle leakage audit'],
    'motion_authority': ['G06: three-topology authority, actual motion executor and same-trace render/physics linkage',
                         'G06: at least 1000 independent geometry/fault cases and full-volume gate crossings',
                         'G06: postquantization curvature, acceleration, tail/thin-layer/contact and unreachable cases'],
}
REFERENCES = {'editor', 'sensors', 'timing', 'motion_authority', 'secrecy'}


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_child(root, name):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in ('.', '..'):
        raise ValueError('invalid evidence filename/label')
    root = Path(root).resolve()
    target = root / name
    if target.is_symlink() or not target.resolve().is_relative_to(root):
        raise ValueError('evidence path escapes caller directory')
    return target


def snapshot(paths):
    return {str(Path(path).absolute()): sha256(path) if Path(path).is_file() else None
            for path in sorted(set(map(Path, paths)))}


def tree_snapshot(root):
    return snapshot(p for p in Path(root).rglob('*') if p.is_file() and '.godot' not in p.parts)


def changed_paths(before, after):
    return [key for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]


def run_command(command, *, cwd, evidence_dir, label, timeout_seconds, expectation=None):
    """Run argv without a shell, save raw bytes, require exit + suite summary."""
    stdout_path = safe_child(evidence_dir, label + '.stdout.log')
    stderr_path = safe_child(evidence_dir, label + '.stderr.log')
    result = dict(command=list(map(str, command)), cwd=str(cwd), exit_code=None,
                  timed_out=False, status='failed', expectation=expectation)
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
               TEMP=str(evidence_dir), TMP=str(evidence_dir),
               APPDATA=str(evidence_dir), LOCALAPPDATA=str(evidence_dir),
               XDG_DATA_HOME=str(evidence_dir), XDG_CONFIG_HOME=str(evidence_dir),
               XDG_CACHE_HOME=str(evidence_dir))
    result['environment'] = {key: env.get(key) for key in (
        'PYTHONDONTWRITEBYTECODE', 'PYTHONUTF8', 'PYTHONPATH', 'TEMP', 'TMP',
        'APPDATA', 'LOCALAPPDATA', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME')}
    with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
        try:
            child = subprocess.run(result['command'], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err, timeout=timeout_seconds)
            result['exit_code'] = child.returncode
            result['status'] = 'passed' if child.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired:
            result.update(timed_out=True, reason='subprocess timeout')
        except OSError as error:
            result.update(status='blocked', reason=str(error))
    result['duration_seconds'] = round(time.monotonic() - started, 6)
    raw = stdout_path.read_bytes() + b'\n' + stderr_path.read_bytes()
    output = raw.decode('utf-8', errors='replace')
    if result['status'] == 'passed' and expectation:
        valid = False
        if expectation == 'unittest':
            count = re.search(r'(?m)^Ran (\d+) tests? in ', output)
            valid = bool(count and int(count[1]) > 0 and re.search(r'(?m)^OK\s*$', output))
        elif expectation == 'editor':
            count = re.search(r'(?m)^TESTS checks=(\d+) failures=0\s*$', output)
            valid = bool(count and int(count[1]) > 0 and re.search(r'(?m)^RESULT PASS\s*$', output))
        elif expectation == 'version':
            valid = stdout_path.read_text(encoding='utf-8').strip() == VERSION
        if not valid:
            result.update(status='failed', reason='missing/invalid suite summary or runtime error')
    if result['status'] == 'passed' and re.search(
            r'(?m)^(?:SCRIPT ERROR:|ERROR:|FAILED\b|FAILURE:)', output):
        result.update(status='failed', reason='runtime error in subprocess output')
    for name, path in (('stdout', stdout_path), ('stderr', stderr_path)):
        result[name] = dict(path=str(path), sha256=sha256(path), bytes=path.stat().st_size)
    return result


def run_checked(commands, source_paths, *, cwd, evidence_dir, timeout_seconds):
    before = snapshot(source_paths)
    steps = []
    if not commands or any(value is None for value in before.values()):
        return dict(status='blocked', commands=[], source_before=before, source_after=before,
                    changed_sources=[], reason='missing commands or source dependencies')
    for entry in commands:
        step = run_command(**entry, cwd=cwd, evidence_dir=evidence_dir,
                           timeout_seconds=timeout_seconds)
        steps.append(step)
        if step['status'] != 'passed':
            break
    after = snapshot(source_paths)
    changed = changed_paths(before, after)
    status = 'reference_passed'
    if changed or any(step['status'] == 'failed' for step in steps):
        status = 'failed'
    elif any(step['status'] == 'blocked' for step in steps):
        status = 'blocked'
    return dict(status=status, commands=steps, source_before=before, source_after=after,
                changed_sources=changed)


def source_paths(suite):
    paths = [Path(__file__).resolve(), SCOPE, SCOPE.with_suffix('.md')]
    if suite == 'editor':
        paths += [p for p in (PRODUCT / 'simulator').rglob('*')
                  if p.is_file() and '.godot' not in p.parts]
    if suite == 'sensors':
        paths += [PRODUCT / name for name in (
            'tests/simulation/test_forward_profile.py', 'simulation/sensors/forward_profile.py',
            'integration/test_sensor_source.py', 'integration/sensor_source.py')]
    if suite == 'timing':
        paths += [PRODUCT / ('integration/' + name) for name in (
            'test_pc_direct_watchdog.py', 'pc_direct_watchdog.py', 'test_host_envelope.py',
            'host_envelope.py', 'wire.py', 'motion.py')]
        paths += [PRODUCT / 'docs/host_contract.json']
    if suite == 'motion_authority':
        paths += [PRODUCT / name for name in (
            'simulation/authority/motion/kinematics.py',
            'simulation/authority/motion/gate_geometry.py',
            'simulation/authority/motion/gate_clearance.py',
            'tests/simulation/test_kinematics.py', 'tests/simulation/test_gate_geometry.py',
            'tests/simulation/test_gate_clearance.py',
            'integration/motion.py', 'integration/test_motion.py')]
    if suite == 'secrecy':
        # Bind the complete reviewed P1a context. The live test is provenance
        # only; reference execution copies and selects test_policy.py alone.
        paths += [PRODUCT / name for name in (
            'simulation/isolation/__init__.py', 'simulation/isolation/policy.py',
            'simulation/isolation/win32.py', 'simulation/isolation/prototype.py',
            'simulation/isolation/fixture.py', 'tests/isolation/test_policy.py',
            'tests/isolation/test_windows_live.py')]
    return paths


def reference_commands(suite, stage=None):
    python = [sys.executable, '-B']
    if suite == 'secrecy':
        if stage is None:
            return []
        return [dict(label='isolation-policy', command=python + ['-m', 'unittest', 'discover',
            '-s', str(stage), '-p', 'test_policy.py', '-v'], expectation='unittest')]
    if suite == 'sensors':
        return [dict(label='forward-profile', command=python + ['-m', 'unittest', 'discover',
                    '-s', str(PRODUCT / 'tests/simulation'), '-p', 'test_forward_profile.py', '-v'],
                    expectation='unittest'),
                dict(label='sensor-source', command=python + [str(PRODUCT / 'integration/test_sensor_source.py'), '-v'],
                     expectation='unittest')]
    if suite == 'timing':
        return [dict(label='pc-direct-watchdog', command=python +
                    [str(PRODUCT / 'integration/test_pc_direct_watchdog.py'), '-v'], expectation='unittest')]
    if suite == 'motion_authority':
        return [dict(label='motion-primitives', command=python + ['-m', 'unittest',
            'competition.deepeye.tests.simulation.test_kinematics',
            'competition.deepeye.tests.simulation.test_gate_geometry',
            'competition.deepeye.tests.simulation.test_gate_clearance',
            'competition.deepeye.integration.test_motion', '-v'], expectation='unittest')]
    return []


def validate_engine(path):
    engine = Path(path).resolve()
    if not engine.is_file():
        raise ValueError('missing dependency: explicit existing Godot executable')
    digest = sha256(engine)
    hashes = {str(engine): digest}
    if digest == CONSOLE_SHA:
        companion = engine.with_name('Godot_v4.7.2-stable_win64.exe')
        if not companion.is_file() or sha256(companion) != ENGINE_SHA:
            raise ValueError('Godot console companion identity is missing/unverified')
        hashes[str(companion)] = sha256(companion)
        # Execute the engine itself so timeout owns its process, not the console launcher.
        engine = companion
    elif digest != ENGINE_SHA:
        raise ValueError('unsupported/unverified Godot executable identity; no mock fallback')
    return engine, hashes


def execute(args, run_dir):
    report = dict(schema_version=1, suite=args.suite, evidence_level='reference_only' if args.reference_only
                  else 'formal_requested', formal_acceptance=False, status='blocked',
                  contract_id='DEEPEYE-HUMAN-LOCK-20261014/revision1', requirements_sha256=PIN,
                  missing_evidence=list(GAPS[args.suite]), commands=[],
                  product_checkout=str(CHECKOUT), interpreter=str(Path(sys.executable).resolve()),
                  interpreter_sha256=sha256(sys.executable), thread_id=os.environ.get('CODEX_THREAD_ID'),
                  started_utc=datetime.now(timezone.utc).isoformat(), run_dir=str(run_dir),
                  requested_actions=args.actions, requested_trials_per_cell=args.trials_per_cell)
    if args.suite == 'secrecy':
        report.update(reference_scope='P1a policy/parser/helper unit tests only',
                      live_os_probes_run=False, historical_windows_evidence_revalidated=False)
        report['missing_evidence'].append(
            'Historical Windows P1a receipts bind their recorded source hashes; these unit tests '
            'do not revalidate OS probes for the current final-parser bytes')
    paths = source_paths(args.suite)
    before = snapshot(paths)
    report['source_before'] = before
    stage = None
    try:
        scope = json.loads(SCOPE.read_text(encoding='utf-8'))
        digest = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False,
                    sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        if digest != PIN or scope['requirements_sha256'] != PIN:
            raise ValueError('immutable scope hash mismatch')
        git = run_command(['git', '-C', str(CHECKOUT), 'rev-parse', 'HEAD'], cwd=run_dir,
                          evidence_dir=run_dir, label='git-head', timeout_seconds=args.timeout_seconds)
        report['git_head_command'] = git
        if git['status'] != 'passed':
            report['status'] = git['status']
            raise ValueError('cannot bind source checkout HEAD')
        report['product_head'] = Path(git['stdout']['path']).read_text(encoding='utf-8').strip()
        if args.actions is not None or args.trials_per_cell is not None:
            raise ValueError('unsupported action/trial execution: --actions and --trials-per-cell are not implemented')
        if not args.reference_only:
            return report
        if args.suite not in REFERENCES:
            raise ValueError('no implemented reference-only runner for this suite')
        if any(value is None for value in before.values()):
            raise ValueError('missing dependency: required source file(s)')
        commands = reference_commands(args.suite)
        if args.suite == 'timing' and importlib.util.find_spec('jsonschema') is None:
            raise ValueError('missing dependency: jsonschema in the existing Python interpreter')
        if args.suite == 'secrecy':
            # Policy helper tests create temporary files beside __file__. Keep
            # those writes in caller evidence, and never copy/import live tests.
            stage = safe_child(run_dir, 'policy-tests')
            stage.mkdir()
            source = PRODUCT / 'tests/isolation/test_policy.py'
            copied = stage / 'test_policy.py'
            shutil.copyfile(source, copied)
            report['staged_source_before'] = tree_snapshot(stage)
            if report['staged_source_before'] != {str(copied): before[str(source)]}:
                report['status'] = 'failed'
                raise ValueError('staged policy test does not match original source snapshot')
            commands = reference_commands(args.suite, stage)
        if args.suite == 'editor':
            if not args.godot_exe:
                raise ValueError('missing dependency: --godot-exe must explicitly name a verified existing engine')
            engine, hashes = validate_engine(args.godot_exe)
            report['engine_sha256'] = hashes
            version = run_command([str(engine), '--version'], cwd=run_dir,
                evidence_dir=run_dir, label='godot-version', timeout_seconds=args.timeout_seconds,
                expectation='version')
            report['commands'].append(version)
            if version['status'] != 'passed':
                report['status'] = version['status']
                raise ValueError('Godot version verification failed')
            stage = safe_child(run_dir, 'simulator')
            # Run the real copied scripts. Engine import/cache/logs stay in caller evidence.
            for path in (PRODUCT / 'simulator').rglob('*'):
                if '.godot' not in path.parts and (path.is_symlink() or
                    not path.resolve().is_relative_to(PRODUCT / 'simulator')):
                    raise ValueError('simulator source links may not escape input tree')
            shutil.copytree(PRODUCT / 'simulator', stage, ignore=shutil.ignore_patterns('.godot'))
            report['staged_source_before'] = tree_snapshot(stage)
            original = {str(Path(key).relative_to(PRODUCT / 'simulator')): value
                        for key, value in before.items() if Path(key).is_relative_to(PRODUCT / 'simulator')}
            copied = {str(Path(key).relative_to(stage)): value
                      for key, value in report['staged_source_before'].items()}
            if copied != original:
                report['status'] = 'failed'
                raise ValueError('staged source does not match original source snapshot')
            base = [str(engine), '--headless', '--path', str(stage)]
            commands = [dict(label='godot-import', command=base + ['--editor', '--import', '--log-file',
                             str(safe_child(run_dir, 'godot-import.engine.log'))]),
                        dict(label='editor-document', command=base + ['--script',
                             'res://tests/test_editor_document.gd', '--log-file',
                             str(safe_child(run_dir, 'editor-document.engine.log'))], expectation='editor')]
        # The motion tests use repository-qualified imports. They are fixed,
        # pure software tests; all temporary/log output still goes to run_dir.
        command_cwd = (CHECKOUT if args.suite == 'motion_authority' else
                       PRODUCT if args.suite == 'secrecy' else run_dir)
        result = run_checked(commands, paths, cwd=command_cwd, evidence_dir=run_dir,
                             timeout_seconds=args.timeout_seconds)
        previous = report['commands']
        report.update(result)
        report['commands'] = previous + result['commands']
    except (OSError, ValueError, KeyError) as error:
        report['missing_evidence'].append(str(error))
    finally:
        after = snapshot(source_paths(args.suite))
        report.update(source_before=before, source_after=after,
                      changed_sources=changed_paths(before, after))
        if report['changed_sources']:
            report['status'] = 'failed'
            report['missing_evidence'].append('source changed during verification')
        if stage is not None and 'staged_source_before' in report:
            report['staged_source_after'] = tree_snapshot(stage)
            report['changed_staged_sources'] = changed_paths(
                report['staged_source_before'], report['staged_source_after'])
            if report['changed_staged_sources']:
                report['status'] = 'failed'
                report['missing_evidence'].append('staged source changed during verification')
        if report.get('engine_sha256'):
            report['engine_sha256_after'] = snapshot(report['engine_sha256'])
            if report['engine_sha256_after'] != report['engine_sha256']:
                report['status'] = 'failed'
                report['missing_evidence'].append('engine changed during verification')
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True, choices=tuple(GAPS))
    parser.add_argument('--reference-only', action='store_true', help='run software references; never formal acceptance')
    parser.add_argument('--evidence-dir', required=True, type=Path, help='caller-owned directory outside product sources')
    parser.add_argument('--godot-exe', type=Path)
    parser.add_argument('--timeout-seconds', type=float, default=60)
    parser.add_argument('--actions', type=int, help='reserved formal option: currently blocked, never silently ignored')
    parser.add_argument('--trials-per-cell', type=int, help='reserved formal option: currently blocked')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= 300:
        parser.error('--timeout-seconds must be finite and in (0, 300]')
    evidence = args.evidence_dir.resolve()
    if evidence.is_relative_to(PRODUCT) or evidence == CHECKOUT:
        parser.error('evidence directory must be outside product sources/checkout root')
    try:
        evidence.mkdir(parents=True, exist_ok=True)
        run_dir = safe_child(evidence, 'run-' + uuid.uuid4().hex)
        run_dir.mkdir()
        report = execute(args, run_dir)
        report_path = safe_child(run_dir, 'report.json')
        report['report_path'] = str(report_path)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Machine-readable stdout must survive Windows legacy console encodings.
        print(json.dumps(report, ensure_ascii=True))
        return {'reference_passed': 0, 'failed': 1, 'blocked': 2}[report['status']]
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
