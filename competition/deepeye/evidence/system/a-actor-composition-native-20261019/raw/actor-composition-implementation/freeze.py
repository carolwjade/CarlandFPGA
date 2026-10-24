import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
GIT = Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')
OWNED = ['competition/deepeye/simulation/authority/actor_composition.py',
         'competition/deepeye/tests/simulation/test_actor_composition.py',
         'competition/deepeye/docs/actor_composition.md']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

baseline = json.loads((HERE / 'baseline.json').read_bytes())
for rel, expected in baseline['source_hashes'].items():
    assert sha(PRODUCT / 'competition/deepeye' / rel) == expected, rel
green = json.loads((HERE / 'green-final.result.json').read_bytes())
assert green['successful'] and green['tests'] == 172 and green['skipped'] == 0
for rel in OWNED[:2]:
    assert sha(PRODUCT / rel) == sha(HERE / 'green-final-source' / rel), rel
files = []
for rel in OWNED:
    source = PRODUCT / rel
    raw = source.read_bytes()
    raw.decode('utf-8'); assert b'\r' not in raw
    if rel.endswith('.py'): ast.parse(raw)
    plain = subprocess.check_output([str(GIT), '-C', str(PRODUCT), 'hash-object', '--no-filters', str(source)], text=True).strip()
    clean = subprocess.check_output([str(GIT), '-C', str(PRODUCT), 'hash-object', '--path=' + rel, '--stdin'], input=raw).decode().strip()
    assert plain == clean
    target = HERE / 'candidate' / rel
    assert not target.exists(), 'freeze is immutable'
    target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
    files.append(dict(path=rel, sha256=sha(source), bytes=len(raw), raw_git_object=plain, clean_git_object=clean))
manifest = dict(schema=1, job_id='child-31468257c4304dcab47f85ea86fd6659',
    work_id='A-actor-composition-implementation-20261019-v1',
    owner='/root/worker_results_review_20261018', files=files,
    requirements_sha256=baseline['requirements_sha256'],
    selected_design_sha256=sha(HERE.parent / 'actor-composition-design/design.md'),
    selected_main_record_sha256=sha(HERE.parent / 'actor-bridge-main-selection.json'),
    dependency_baseline_sha256=sha(HERE / 'baseline.json'),
    baseline_source_files=len(baseline['source_hashes']), baseline_bytes_unchanged=True,
    observed_head=subprocess.check_output([str(GIT), '-C', str(PRODUCT), 'rev-parse', 'HEAD'], text=True).strip(),
    new_source_format='UTF-8 LF; raw Git object equals clean-filter object',
    tests=dict(result_sha256=sha(HERE / 'green-final.result.json'), tests=172, skipped=0, exit_code=0),
    native='not_run', all29='not_run')
write(HERE / 'source-manifest.json', manifest)
print(json.dumps(dict(manifest_sha256=sha(HERE / 'source-manifest.json'), files=files, dependency_files=len(baseline['source_hashes']))))
