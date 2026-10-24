import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
PYTHON = ROOT / '.local/venv/Scripts/python.exe'
GIT = 'C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
OWNED = ['simulation/isolation/actor_owner.py', 'simulation/isolation/actor_lifetime.py',
         'tests/simulation/test_actor_owner.py', 'tests/simulation/test_actor_lifetime.py', 'docs/actor_lifetime.md']
DEPENDENCIES = ['simulation/isolation/' + p + '.py' for p in
                ('owned_resources', 'windows_cleanup', 'win32', 'resource_cleanup', 'policy', 'prototype')]
DEPENDENCIES += ['simulation/authority/' + p + '.py' for p in ('pc_direct_runtime', 'motion_executor')]
DEPENDENCIES += ['tests/simulation/' + p + '.py' for p in ('test_pc_direct_runtime', 'test_motion_executor')]
DEPENDENCIES += ['simulation/authority/motion/' + p.name for p in (PRODUCT / 'competition/deepeye/simulation/authority/motion').glob('*.py')]

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name, data): (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
def snapshot():
    result = {p: sha((PRODUCT / 'competition/deepeye' / p).read_bytes()) for p in DEPENDENCIES}
    scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert sha(canonical) == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    result['requirements'] = sha(canonical)
    return result

if sys.argv[1] == 'baseline':
    assert not (HERE / 'baseline.json').exists()
    save('baseline.json', snapshot())
elif sys.argv[1] == 'freeze':
    assert snapshot() == json.loads((HERE / 'baseline.json').read_bytes()), 'Unowned dependency drift'
    rows = []
    for relative in OWNED:
        path = 'competition/deepeye/' + relative
        raw = (PRODUCT / path).read_bytes()
        raw.decode('utf-8'); assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
        hashes = []
        for args in [('--no-filters', path), ('--path=' + path, path)]:
            hashes.append(subprocess.run([GIT, '-C', str(PRODUCT), 'hash-object', *args], check=True, capture_output=True).stdout.decode().strip())
        assert hashes[0] == hashes[1], 'raw bytes differ from Git clean bytes'
        rows.append(dict(path=path, sha256=sha(raw), bytes=len(raw), raw_git_object=hashes[0], clean_git_object=hashes[1]))
        copied = HERE / 'candidate' / path
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes(raw)
        assert copied.read_bytes() == raw
    head = subprocess.run([GIT, '-C', str(PRODUCT), 'rev-parse', 'HEAD'], check=True, capture_output=True).stdout.decode().strip()
    save('source-manifest.json', {'base': 'b19a528344d8675fedb41f37e7de23f1112f1871', 'observed_head': head,
         'files': rows, 'dependencies': snapshot(), 'native': 'not_run', 'all29': 'not_run'})
    print(json.dumps({'files': len(rows), 'manifest_sha256': sha((HERE / 'source-manifest.json').read_bytes())}))
else:
    label = sys.argv[1]
    modules = sys.argv[2:] or ['competition.deepeye.tests.simulation.test_actor_owner', 'competition.deepeye.tests.simulation.test_actor_lifetime']
    command = [str(PYTHON), '-B', '-X', 'utf8', '-m', 'unittest', *modules, '-v']
    temporary = HERE / 'temporary'; temporary.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT / '.local/deepeye-host-deps'), PYTHONDONTWRITEBYTECODE='1',
               TEMP=str(temporary), TMP=str(temporary))
    result = subprocess.run(command, cwd=PRODUCT, env=env, capture_output=True)
    (HERE / (label + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(result.stderr)
    save(label + '.json', {'command': command, 'cwd': str(PRODUCT), 'exit_code': result.returncode,
                          'stdout_sha256': sha(result.stdout), 'stderr_sha256': sha(result.stderr)})
    print(json.dumps({'label': label, 'exit_code': result.returncode, 'tail': result.stderr.decode('utf-8')[-2500:]}))
