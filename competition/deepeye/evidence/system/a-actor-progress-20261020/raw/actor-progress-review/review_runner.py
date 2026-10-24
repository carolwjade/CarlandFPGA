"""Independent bounded review runner; writes only under actor-progress-review."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
MAIN_EVIDENCE = ROOT / '.planning/deepeye-resume-20261018/actor-progress-main'
HOST_DEPS = ROOT / '.local/deepeye-host-deps'
COMPOSITION_REL = 'competition/deepeye/tests/simulation/test_actor_composition.py'
SOURCE_REL = 'competition/deepeye/simulation/authority/actor_composition.py'
BASELINE_TEST = MAIN_EVIDENCE / 'baseline' / COMPOSITION_REL


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_inputs() -> dict[str, str]:
    manifest = json.loads((MAIN_EVIDENCE / 'candidate-manifest.json').read_text(encoding='utf-8'))
    return {rel: sha256(PRODUCT / rel) for rel in sorted(manifest['candidate_pins'])}


def original_test_asts(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    actor = next(node for node in tree.body
                 if isinstance(node, ast.ClassDef) and node.name == 'ActorCompositionTests')
    return {node.name: ast.dump(node, include_attributes=False)
            for node in actor.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}


def run_payload() -> int:
    expected_paths = [PRODUCT, PRODUCT / 'competition/deepeye', HOST_DEPS]
    resolved = [Path(item).resolve() for item in sys.path if item]
    missing = [str(path) for path in expected_paths if path.resolve() not in resolved]
    if missing:
        raise SystemExit('missing process imports: ' + repr(missing))
    old = original_test_asts(BASELINE_TEST)
    new = original_test_asts(PRODUCT / COMPOSITION_REL)
    changed = sorted(name for name, value in old.items() if new.get(name) != value)
    if len(old) != 24 or changed:
        raise SystemExit('original test AST drift: count={} changed={}'.format(len(old), changed))
    names = [
        'competition.deepeye.tests.simulation.test_actor_composition.ActorCompositionTests',
        'competition.deepeye.tests.simulation.test_actor_owner.ActorOwnerTests',
        'competition.deepeye.tests.simulation.test_actor_lifetime.ActorLifetimeTests',
        'competition.deepeye.tests.simulation.test_pc_direct_runtime.PcDirectRuntimeTests',
        'competition.deepeye.tests.simulation.test_motion_executor.MotionExecutorTests',
    ]
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    origins = {}
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_file() and Path(path).resolve().is_relative_to(PRODUCT):
            path = Path(path).resolve()
            origins[name] = {'path': str(path), 'sha256': sha256(path)}
    payload = {
        'tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'successful': result.wasSuccessful(),
        'expected_tests': 193,
        'count_exact': result.testsRun == 193,
        'original_24_test_methods_ast_unchanged': not changed and len(old) == 24,
        'python_executable': sys.executable,
        'pythonpath': os.environ.get('PYTHONPATH'),
        'module_origins': origins,
    }
    with (BASE / 'affected193-result.json').open('x', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write('\n')
    return 0 if result.wasSuccessful() and result.testsRun == 193 else 1


def run_once() -> int:
    out_path = BASE / 'affected193.stdout.log'
    err_path = BASE / 'affected193.stderr.log'
    for path in (out_path, err_path, BASE / 'affected193-result.json', BASE / 'affected193-command.json'):
        if path.exists():
            raise SystemExit('refusing to overwrite prior evidence: ' + str(path))
    temp = BASE / 'temp' / 'affected193'
    temp.mkdir(exist_ok=False)
    before = snapshot_inputs()
    env = os.environ.copy()
    env.update(
        PYTHONDONTWRITEBYTECODE='1',
        PYTHONIOENCODING='utf-8',
        PYTHONPATH=os.pathsep.join((str(PRODUCT), str(PRODUCT / 'competition/deepeye'), str(HOST_DEPS))),
        TEMP=str(temp),
        TMP=str(temp),
    )
    command = [sys.executable, '-B', str(Path(__file__).resolve()), 'payload']
    with out_path.open('xb') as out, err_path.open('xb') as err:
        completed = subprocess.run(command, cwd=PRODUCT, env=env, stdout=out, stderr=err, timeout=180)
    after = snapshot_inputs()
    record = {
        'command': command,
        'cwd': str(PRODUCT),
        'returncode': completed.returncode,
        'pythonpath': env['PYTHONPATH'],
        'temp': str(temp),
        'input_count': len(before),
        'inputs_unchanged': before == after,
        'before': before,
        'after': after,
    }
    with (BASE / 'affected193-command.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({'returncode': completed.returncode, 'inputs_unchanged': before == after,
                      'input_count': len(before)}))
    return completed.returncode if before == after else 2


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('payload', 'run'):
        raise SystemExit('usage: review_runner.py payload|run')
    raise SystemExit(run_payload() if sys.argv[1] == 'payload' else run_once())