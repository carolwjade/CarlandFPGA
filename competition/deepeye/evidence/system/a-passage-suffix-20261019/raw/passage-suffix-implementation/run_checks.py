"""Owned numerical author evidence; never executes the historical design script."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCT = ROOT / '.local/deepeye-implementation-a'
OWNED = ['competition/deepeye/' + name for name in (
    'simulation/authority/motion/passage_phase.py', 'tests/simulation/test_passage_phase.py',
    'tests/simulation/test_motion_executor.py', 'docs/workspace_passage.md')]


def digest(path):
    raw = path.read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


mode = sys.argv[1]
if mode == 'baseline':
    head = subprocess.check_output(['git', '-C', str(PRODUCT), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == 'b19a528344d8675fedb41f37e7de23f1112f1871'
    design = HERE.parent / 'passage-refinement-design/design.md'
    assert digest(design)['sha256'] == '2e0b5eaa18f6e1197befc5fd1e76513f3e54b0199823827e2fb6994777800596'
    scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
    (PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf-8')
    requirements = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert requirements == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    paths = [PRODUCT / name for name in OWNED]
    for directory in ('simulation/authority', 'tests/simulation', 'integration', 'ai_pc', 'tests/ai', 'evidence/ai'):
        folder = PRODUCT / 'competition/deepeye' / directory
        paths += [p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts] if folder.exists() else []
    paths += [PRODUCT / '.gitattributes', PRODUCT / 'AGENTS.md']
    paths += list((PRODUCT / 'docs/competition/deepeye-2026').glob('immutable_scope.*'))
    manifest = {p.relative_to(PRODUCT).as_posix(): digest(p) for p in sorted(set(paths))}
    old_evidence = {p.relative_to(ROOT).as_posix(): digest(p) for p in (HERE.parent / 'passage-refinement-design').rglob('*') if p.is_file()}
    for rel in OWNED:
        target = HERE / 'before' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PRODUCT / rel, target)
    save('baseline.json', {'head': head, 'files': manifest, 'old_evidence': old_evidence,
                          'owned': OWNED, 'design': digest(design), 'requirements_sha256': requirements})
elif mode.startswith(('red', 'green')):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPATH'] = str(ROOT / '.local/deepeye-host-deps')
    temp = HERE / 'temp'
    temp.mkdir(exist_ok=True)
    env['TEMP'] = env['TMP'] = str(temp)
    modules = ['test_passage_phase', 'test_motion_executor']
    if mode.startswith('green'):
        modules += ['test_workspace_boundaries', 'test_solid_clearance', 'test_pc_direct_runtime',
                    'test_certified_path', 'test_gate_clearance', 'test_gate_geometry', 'test_kinematics']
    command = [str(ROOT / '.local/venv/Scripts/python.exe'), '-B', '-X', 'utf8', '-m', 'unittest', '-v']
    command += ['competition.deepeye.tests.simulation.' + name for name in modules]
    result = subprocess.run(command, cwd=PRODUCT, env=env, capture_output=True)
    (HERE / (mode + '.stdout.bin')).write_bytes(result.stdout)
    (HERE / (mode + '.stderr.bin')).write_bytes(result.stderr)
    save(mode + '.json', {'command': command, 'cwd': str(PRODUCT), 'exit_code': result.returncode,
                         'TEMP': env['TEMP'], 'TMP': env['TMP'], 'PYTHONPATH': env['PYTHONPATH'],
                         'sources': {name: digest(PRODUCT / name) for name in OWNED}})
    print((result.stdout + result.stderr).decode('utf-8', errors='replace'))
    print('RECORDED_EXIT_CODE=' + str(result.returncode))
else:
    raise ValueError(mode)
