import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCT = ROOT / '.local/deepeye-implementation-a'
BASE = PRODUCT / 'competition/deepeye'
OWNED = ['simulation/isolation/owned_resources.py', 'simulation/isolation/windows_cleanup.py',
         'simulation/isolation/prototype.py', 'simulation/isolation/win32.py', 'simulation/isolation/policy.py',
         'tests/isolation/test_owned_resources.py', 'tests/isolation/test_windows_cleanup.py',
         'tests/isolation/test_prototype_cleanup.py', 'tests/isolation/test_policy.py',
         'tests/isolation/test_windows_live.py', 'docs/isolation_resource_cleanup.md',
         'docs/process_isolation_prototype.md']


def digest(path):
    raw = path.read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def inputs():
    files = list((BASE / 'simulation/isolation').glob('*.py')) + list((BASE / 'tests/isolation').glob('*.py'))
    files += [BASE / name for name in OWNED if (BASE / name).exists()]
    files += list((PRODUCT / 'docs/superpowers/specs').glob('2026-10-19-isolation-launcher-cleanup*'))
    files += list((PRODUCT / 'docs/superpowers/plans').glob('2026-10-19-isolation-launcher-cleanup*'))
    files += list((PRODUCT / 'docs/competition/deepeye-2026').glob('immutable_scope.*'))
    files += [PRODUCT / 'AGENTS.md']
    files += list((ROOT / '.planning/deepeye-implementation-a/process-isolation-p1b-prototype-20261016').rglob('*'))
    return sorted(set(p for p in files if p.is_file()))


mode = sys.argv[1]
if mode == 'baseline':
    assert all(not (BASE / name).exists() for name in OWNED if name.endswith(('owned_resources.py', 'windows_cleanup.py', 'test_owned_resources.py', 'test_windows_cleanup.py', 'test_prototype_cleanup.py')))
    scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
    canonical = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert canonical == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    manifest = {}
    for path in inputs():
        relative = path.relative_to(ROOT)
        manifest[relative.as_posix()] = digest(path)
        if path.is_relative_to(PRODUCT):
            target = HERE / 'before' / path.relative_to(PRODUCT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    save('baseline.json', {'requirements_sha256': canonical, 'files': manifest, 'owned': OWNED})
elif mode.startswith(('red', 'green')):
    command = [str(ROOT / '.local/venv/Scripts/python.exe'), '-B', '-X', 'utf8', str(HERE / 'unit_suite.py')]
    result = subprocess.run(command, cwd=BASE, capture_output=True)
    (HERE / (mode + '.stdout.bin')).write_bytes(result.stdout)
    (HERE / (mode + '.stderr.bin')).write_bytes(result.stderr)
    (HERE / (mode + '.log')).write_bytes(result.stdout + result.stderr)
    save(mode + '.json', {'command': command, 'cwd': str(BASE), 'exit_code': result.returncode,
                         'sources': {name: digest(BASE / name) for name in OWNED if (BASE / name).exists()}})
    print((result.stdout + result.stderr).decode('utf-8', errors='replace'))
    print('RECORDED_EXIT_CODE=' + str(result.returncode))
else:
    raise ValueError(mode)
