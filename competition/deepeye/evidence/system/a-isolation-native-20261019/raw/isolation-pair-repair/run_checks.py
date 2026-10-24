"""Pair repair evidence; stage independent witnesses byte-for-byte in owned output."""
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
BASE = PRODUCT / 'competition/deepeye'
ORIGINAL = HERE.parent / 'isolation-launcher-implementation'
REVIEW = HERE.parent / 'isolation-launcher-review'
OWNED = ['competition/deepeye/' + relative for relative in (
    'simulation/isolation/owned_resources.py', 'simulation/isolation/win32.py',
    'tests/isolation/test_owned_resources.py', 'tests/isolation/test_windows_cleanup.py')]


def digest(path):
    raw = path.read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


mode = sys.argv[1]
if mode == 'baseline':
    assert digest(ORIGINAL / 'source-manifest.json')['sha256'] == '0bdabec4a3c465e269c090bffd8fb690b2797750f47c4e4c7165e8e4d6a51376'
    manifest = json.loads((ORIGINAL / 'source-manifest.json').read_text(encoding='utf-8'))
    for rel, expected in manifest.items():
        assert digest(PRODUCT / rel) == expected
        destination = HERE / 'before' / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PRODUCT / rel, destination)
    scope_path = PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json'
    scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
    requirements = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert requirements == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    dependencies = json.loads((ORIGINAL / 'dependencies-after.json').read_text(encoding='utf-8'))['files']
    for rel, expected in dependencies.items():
        assert digest(ROOT / rel) == expected, rel
    historical = {p.relative_to(ROOT).as_posix(): digest(p) for folder in (ORIGINAL, REVIEW)
                  for p in folder.rglob('*') if p.is_file()}
    staged = {}
    for source, name in ((REVIEW / 'test_pair_acquisition.py', 'test_pair_acquisition.py'),
                         (REVIEW / 'test_independent_boundaries.py', 'test_independent_boundaries.py'),
                         (ORIGINAL / 'unit_suite.py', 'unit_suite.py')):
        shutil.copyfile(source, HERE / name)
        assert digest(source) == digest(HERE / name)
        staged[name] = {'source': source.relative_to(ROOT).as_posix(), **digest(source)}
    save('baseline.json', {'original_manifest': manifest, 'dependencies': dependencies,
                          'historical': historical, 'staged': staged, 'owned': OWNED,
                          'requirements_sha256': requirements})
elif mode in ('red-witness', 'green-witness', 'green-independent', 'red-regressions', 'green-offline'):
    temporary = HERE / 'temp'
    temporary.mkdir(exist_ok=True)
    env = dict(os.environ)
    env['PYTHONPATH'] = str(BASE) + os.pathsep + str(BASE / 'tests/isolation')
    env['TEMP'] = env['TMP'] = str(temporary)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT', None)
    command = [str(ROOT / '.local/venv/Scripts/python.exe'), '-B', '-X', 'utf8']
    if mode.endswith('witness'):
        command += [str(HERE / 'test_pair_acquisition.py')]
    elif mode == 'green-independent':
        command += [str(HERE / 'test_independent_boundaries.py')]
    elif mode == 'red-regressions':
        command += ['-m', 'unittest', '-v', 'test_owned_resources', 'test_windows_cleanup']
    else:
        command += [str(HERE / 'unit_suite.py')]
    result = subprocess.run(command, cwd=BASE, env=env, capture_output=True, timeout=30)
    (HERE / (mode + '.stdout.bin')).write_bytes(result.stdout)
    (HERE / (mode + '.stderr.bin')).write_bytes(result.stderr)
    save(mode + '.json', {'command': command, 'cwd': str(BASE), 'exit_code': result.returncode,
                         'TEMP': env['TEMP'], 'TMP': env['TMP'], 'native_opt_in': 'unset',
                         'PYTHONPATH': env['PYTHONPATH'],
                         'source_hashes': {rel: digest(PRODUCT / rel) for rel in OWNED}})
    print((result.stdout + result.stderr).decode('utf-8', errors='replace'))
    print('RECORDED_EXIT_CODE=' + str(result.returncode))
else:
    raise ValueError(mode)
