import datetime, hashlib, json
from pathlib import Path
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
selection = json.loads((OUT / 'main-design-selection.json').read_bytes())
scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
requirements_hash = hashlib.sha256(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert requirements_hash == selection['requirements_sha256']
current = {p: sha(PRODUCT / p) for p in selection['baseline_pins']}
changes = [p for p in current if current[p] != selection['baseline_pins'][p]]
assert sorted(changes) == sorted(selection['owned_product_paths']), changes
result = json.loads((OUT / 'regression-01-result.json').read_bytes())
assert result['tests'] == 193 and result['successful'] and result['original_24_test_methods_ast_unchanged']
manifest = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                work_id=selection['work_id'], candidate_pins=current,
                changed_product_paths=changes, unmodified_dependency_count=len(current)-len(changes),
                author_regression=dict(tests=193,failures=0,errors=0,skipped=0),
                requirements_sha256=requirements_hash, formal29='not_run',
                production_channels='unavailable', native_ai='not_run')
manifest['evidence_pins'] = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.glob('*')) if p.is_file()}
with (OUT / 'candidate-manifest.json').open('x',encoding='utf-8') as f:
    json.dump(manifest,f,indent=2); f.write('\n')
print(json.dumps(dict(manifest_sha256=sha(OUT/'candidate-manifest.json'), changed=changes, unchanged_dependencies=len(current)-len(changes))))
