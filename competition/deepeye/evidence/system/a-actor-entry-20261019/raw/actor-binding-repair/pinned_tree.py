"""Evidence-owned committed source tree; never copy live moving G06 files."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
TREE = HERE / 'pinned-source'
GIT = 'C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
BASE = '3f702903f1e16fa72eae15f03ba431b78de24bd0'
PREFIX = 'competition/deepeye/'
OWNED = ['simulation/isolation/actor_owner.py', 'simulation/isolation/windows_cleanup.py',
         'tests/simulation/test_actor_owner.py', 'tests/simulation/test_actor_lifetime.py',
         'tests/isolation/test_windows_cleanup.py', 'docs/actor_lifetime.md']
UNCHANGED = 'simulation/isolation/actor_lifetime.py'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
def git(*args):
    return subprocess.run([GIT, '-C', str(PRODUCT), *args], check=True, capture_output=True,
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).stdout

mode = sys.argv[1]
if mode == 'setup':
    assert not TREE.exists(), 'preserve original pinned tree'
    review = HERE.parent / 'actor-owner-review'
    assert sha((review / 'findings.md').read_bytes()) == '85c01193a3878a41cbd69fd516e649efb67e7a82a1de45fac01534ab2a6bdeca'
    assert sha((review / 'receipt.json').read_bytes()) == '67801b054f57f8e031c73c4bcec51d630762a9572be569a2e0bd6278c218b0c9'
    independent = (review / 'independent_actor_tests.py').read_bytes()
    assert sha(independent) == 'de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f'
    (HERE / 'independent_actor_tests.py').write_bytes(independent)
    selected = [PREFIX + part for part in ('simulation', 'integration', 'tests')]
    entries = {}
    for row in git('ls-tree', '-r', '-z', BASE, '--', *selected).split(b'\0'):
        if not row: continue
        meta, name = row.split(b'\t', 1); mode_bits, kind, oid = meta.decode().split()
        assert kind == 'blob' and mode_bits in ('100644', '100755')
        entries[name.decode('utf-8')] = {'mode': mode_bits, 'git_blob': oid}
    archive = git('archive', '--format=tar', BASE, *selected)
    TREE.mkdir()
    exported = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        for member in tar.getmembers():
            if member.isdir(): continue
            assert member.isfile() and member.name in entries
            path = TREE / member.name
            assert path.resolve().is_relative_to(TREE.resolve())
            raw = tar.extractfile(member).read()
            assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entries[member.name]['git_blob']
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            exported[member.name] = dict(entries[member.name], bytes=len(raw), sha256=sha(raw))
    assert set(exported) == set(entries)
    author_dir = HERE.parent / 'actor-owner-implementation'
    author_manifest = (author_dir / 'source-manifest.json').read_bytes()
    assert sha(author_manifest) == '2bace7921cd89ff2cf7e9d1dd8b87dbd1be6f4d34abd1ac3cc3d37026dc39630'
    actor_sources = {}
    for row in json.loads(author_manifest)['files']:
        raw = (author_dir / 'candidate' / row['path']).read_bytes()
        assert sha(raw) == row['sha256'] and raw == (PRODUCT / row['path']).read_bytes()
        target = TREE / row['path']; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        actor_sources[row['path']] = dict(bytes=len(raw), sha256=sha(raw), origin='original frozen actor candidate')
    controls = ['.agents/skills/fpga-multi-node/SKILL.md', '.agents/skills/fpga-multi-node/skill-role.json',
        '.agents/skills/fpga-multi-node/references/protocol.md',
        '.planning/deepeye-desktop-handoff-20261015/transfer.json']
    scope_path = PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json'
    scope = json.loads(scope_path.read_bytes())
    canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert sha(canonical) == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    transfer = json.loads((ROOT / controls[3]).read_bytes())
    assert transfer['status'] == 'active' and transfer['director_generation'] == 2
    saved = {}
    for name in OWNED + [UNCHANGED]:
        raw = (PRODUCT / PREFIX / name).read_bytes()
        destination = HERE / 'before-source' / PREFIX / name
        destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
        saved[PREFIX + name] = sha(raw)
    save('baseline.json', dict(base=BASE, tar_sha256=sha(archive), exported_git_blobs=exported,
        actor_overlay=actor_sources, before_owned_and_lifetime=saved,
        independent_source_sha256=sha(independent),
        controls={p: sha((ROOT / p).read_bytes()) for p in controls}, requirements_sha256=sha(canonical)))
    print(json.dumps({'base': BASE, 'git_blobs': len(exported), 'actor_files': len(actor_sources), 'independent_methods': 8}))
elif mode == 'schemas':
    # Import-time runtime dependencies; exact committed JSON, never live docs.
    result = {}
    for name in ('host_contract.json', 'interface.json', 'enums.json'):
        path = PREFIX + 'docs/' + name
        raw = git('show', BASE + ':' + path)
        oid = git('rev-parse', BASE + ':' + path).decode().strip()
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == oid
        target = TREE / path; assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        result[path] = dict(git_blob=oid, sha256=sha(raw), bytes=len(raw), base=BASE)
    save('schema-pins.json', result)
elif mode == 'overlay':
    baseline = json.loads((HERE / 'baseline.json').read_bytes())
    assert sha((PRODUCT / PREFIX / UNCHANGED).read_bytes()) == baseline['before_owned_and_lifetime'][PREFIX + UNCHANGED]
    for name in OWNED:
        raw = (PRODUCT / PREFIX / name).read_bytes()
        target = TREE / PREFIX / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    print(json.dumps({'overlaid_only': OWNED}))
else:
    label = mode
    target = HERE / (label + '.result.json')
    assert not target.exists(), 'preserve raw test result'
    modules = sys.argv[2:] or ['competition.deepeye.tests.simulation.test_actor_owner',
        'competition.deepeye.tests.simulation.test_actor_lifetime', 'competition.deepeye.tests.simulation.test_pc_direct_runtime',
        'independent_actor_tests', 'test_windows_cleanup']
    temporary = HERE / 'temporary'; temporary.mkdir(exist_ok=True)
    witness = HERE / 'runs' / label; witness.mkdir(parents=True, exist_ok=False)
    independent = (HERE / 'independent_actor_tests.py').read_bytes()
    assert sha(independent) == 'de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f'
    (witness / 'independent_actor_tests.py').write_bytes(independent)
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, [TREE, TREE / PREFIX,
        TREE / PREFIX / 'tests/isolation', ROOT / '.local/deepeye-host-deps', witness, HERE])),
        PYTHONDONTWRITEBYTECODE='1', TEMP=str(temporary), TMP=str(temporary))
    command = [str(ROOT / '.local/venv/Scripts/python.exe'), '-B', '-X', 'utf8', '-c',
        "import sys,runpy;sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')",
        str(HERE / 'pinned_unittest.py'), label, *modules]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=TREE, env=env, capture_output=True, timeout=120)
    (HERE / (label + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (label + '.stderr.txt')).write_bytes(result.stderr)
    save(target.name, dict(command=command, cwd=str(TREE), environment_overrides={k: env[k] for k in
        ('PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'TEMP', 'TMP')}, started_utc=started,
        exit_code=result.returncode, stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr),
        overlay_hashes={PREFIX + p: sha((TREE / PREFIX / p).read_bytes()) for p in OWNED + [UNCHANGED]}))
    print(json.dumps({'label': label, 'exit_code': result.returncode, 'tail': result.stderr.decode('utf-8')[-4500:]}))
