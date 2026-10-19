"""Freeze seven-file combined candidate against the pinned test tree."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
TREE = HERE / 'pinned-source'
PREFIX = 'competition/deepeye/'
GIT = 'C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
OWNED = ['simulation/isolation/actor_owner.py', 'simulation/isolation/windows_cleanup.py',
    'tests/simulation/test_actor_owner.py', 'tests/simulation/test_actor_lifetime.py',
    'tests/isolation/test_windows_cleanup.py', 'docs/actor_lifetime.md']
LIFETIME = 'simulation/isolation/actor_lifetime.py'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
def git(*args):
    return subprocess.run([GIT, '-C', str(PRODUCT), *args], capture_output=True, check=True,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).stdout.decode().strip()
baseline = json.loads((HERE / 'baseline.json').read_bytes())
schemas = json.loads((HERE / 'schema-pins.json').read_bytes())
for path, row in dict(baseline['exported_git_blobs'], **schemas).items():
    if path not in {PREFIX + item for item in OWNED}:
        assert sha((TREE / path).read_bytes()) == row['sha256'], 'pinned base drift: ' + path
for path, row in baseline['actor_overlay'].items():
    if path not in {PREFIX + item for item in OWNED}:
        assert sha((TREE / path).read_bytes()) == row['sha256']
for path, expected in baseline['controls'].items(): assert sha((ROOT / path).read_bytes()) == expected
review = HERE.parent / 'actor-owner-review'
review_manifest = json.loads((review / 'manifest.json').read_bytes())
for row in review_manifest['files']:
    assert sha((review / row['path']).read_bytes()) == row['sha256'], 'old review evidence changed'
assert sha((HERE / 'independent_actor_tests.py').read_bytes()) == baseline['independent_source_sha256']
green = json.loads((HERE / 'green-repair.result.json').read_bytes())
eight = json.loads((HERE / 'final-independent8.result.json').read_bytes())
assert green['exit_code'] == eight['exit_code'] == 0
rows = []
for relative in OWNED + [LIFETIME]:
    path = PREFIX + relative
    raw = (PRODUCT / path).read_bytes()
    assert raw == (TREE / path).read_bytes(), 'live repair differs from pinned tested overlay'
    if relative.endswith('.py'): assert sha(raw) == green['overlay_hashes'][path]
    assert sha(raw) == eight['overlay_hashes'][path]
    raw.decode('utf-8'); assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
    if relative == LIFETIME: assert sha(raw) == baseline['before_owned_and_lifetime'][path]
    raw_git = git('hash-object', '--no-filters', path)
    clean_git = git('hash-object', '--path=' + path, path)
    assert raw_git == clean_git
    target = HERE / 'candidate' / path
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    rows.append(dict(path=path, sha256=sha(raw), bytes=len(raw), raw_git_object=raw_git,
        clean_git_object=clean_git, ownership='unchanged read-only dependency' if relative == LIFETIME else 'repair-owned'))
unchanged_live = {}
for relative in ['simulation/isolation/' + name + '.py' for name in
                 ('owned_resources', 'win32', 'resource_cleanup', 'policy', 'prototype', 'actor_lifetime')]:
    path = PREFIX + relative
    assert (TREE / path).read_bytes() == (PRODUCT / path).read_bytes()
    unchanged_live[path] = sha((PRODUCT / path).read_bytes())
for name in ('pc_direct_runtime', 'motion_executor'):
    path = PREFIX + 'simulation/authority/' + name + '.py'
    assert (TREE / path).read_bytes() == (PRODUCT / path).read_bytes()
    unchanged_live[path] = sha((PRODUCT / path).read_bytes())

def tests(path):
    parsed = ast.parse(path.read_text(encoding='utf-8'))
    return {(cls.name, method.name): ast.dump(method, include_attributes=False)
            for cls in parsed.body if isinstance(cls, ast.ClassDef)
            for method in cls.body if isinstance(method, ast.FunctionDef) and method.name.startswith('test_')}
original_tests = {}
for relative in ('tests/simulation/test_actor_owner.py', 'tests/simulation/test_actor_lifetime.py', 'tests/isolation/test_windows_cleanup.py'):
    before = tests(HERE / 'before-source' / PREFIX / relative)
    after = tests(PRODUCT / PREFIX / relative)
    assert all(after.get(key) == value for key, value in before.items()), 'original assertions changed'
    original_tests[relative] = dict(original_methods=len(before), current_methods=len(after), original_AST_identical=True)
scope = json.loads((PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert sha(canonical) == baseline['requirements_sha256']
manifest = dict(base=baseline['base'], observed_live_head=git('rev-parse', 'HEAD'), files=rows,
    pinned_git_source_files=len(baseline['exported_git_blobs']), pinned_schema_files=len(schemas),
    baseline_sha256=sha((HERE / 'baseline.json').read_bytes()), schemas_sha256=sha((HERE / 'schema-pins.json').read_bytes()),
    unchanged_live_nonmoving_dependencies=unchanged_live, original_test_assertions=original_tests,
    old_review_manifest_entries_verified=len(review_manifest['files']),
    independent_source_sha256=baseline['independent_source_sha256'],
    tests=dict(pinned_combined_methods=148, combined_exit=0, independent_methods=8, independent_exit=0, skipped=0),
    requirements_sha256=sha(canonical), new_G06_joint_regression='not_run', actual_native='not_run', all29='not_run')
save('source-manifest.json', manifest)
print(json.dumps({'files': len(rows), 'source_manifest_sha256': sha((HERE / 'source-manifest.json').read_bytes()),
                  'original_assertions': original_tests, 'nonmoving_dependencies': len(unchanged_live)}))
