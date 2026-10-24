import ast,datetime,difflib,hashlib,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';E=OUT/'actor-progress-main';R=OUT/'actor-progress-review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PRODUCT).decode().strip()=='889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1'
candidate=json.loads((E/'candidate-manifest.json').read_bytes())
assert sha(E/'candidate-manifest.json')=='23e07f12b6a22b0c264b2c8ed59312e0546a364423d2008d5f63894a8317b17f'
test='competition/deepeye/tests/simulation/test_actor_composition.py'
old=(E/'pre-low-fix-test.py').read_text(encoding='utf-8');new=(PRODUCT/test).read_text(encoding='utf-8')
assert sha(E/'pre-low-fix-test.py')==candidate['candidate_pins'][test]
old_tree=ast.parse(old);new_tree=ast.parse(new)
name='test_unrelated_new_completion_does_not_extend_old_command'
old_method=next(n for n in ast.walk(old_tree) if isinstance(n,ast.FunctionDef) and n.name==name)
new_method=next(n for n in ast.walk(new_tree) if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(old_method)!=ast.dump(new_method)
for node in ast.walk(new_tree):
    if isinstance(node,ast.ClassDef):node.body=[old_method if x is new_method else x for x in node.body]
assert ast.dump(old_tree)==ast.dump(new_tree),'Changes outside the one low finding test body'
diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='reviewed-test',tofile='final-test'))
(E/'low-finding-test-only.patch').write_text(diff,encoding='utf-8')
for p,h in candidate['candidate_pins'].items():
    if p!=test:assert sha(PRODUCT/p)==h,p
for p,h in candidate['evidence_pins'].items():assert sha(E/p)==h,p
audit=json.loads((E/'review-audit-before-low-fix.json').read_bytes())
for p,h in audit['review_artifact_pins'].items():assert sha(R/p)==h,p
review=json.loads((R/'receipt.json').read_bytes());assert review['verdict']=='PASS_BOUNDED_OFFLINE_SOFTWARE_ONLY'
for command in review['commands']:assert command['exit_code']==0 and command['failures']==0 and command['errors']==0
follow=json.loads((E/'focused-low-fix-01-result.json').read_bytes())
assert (follow['tests'],follow['failures'],follow['errors'],follow['skipped'])==(45,0,0,0)
assert follow['original_24_test_methods_ast_unchanged'] is True
for row in follow['module_origins'].values():assert sha(Path(row['path']))==row['sha256'],row['path']
terminal=json.loads((OUT/'owned-jobs-20261020-1608.json').read_bytes())['jobs'][audit['review_job']]
assert terminal['terminal'] and terminal['status']=='completed' and terminal['stale'] is False
scope=json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
assert hashlib.sha256(json.dumps(scope['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
paths=json.loads((E/'main-design-selection.json').read_bytes())['owned_product_paths']
selection=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),work_id='A-ACTOR-PROGRESS-IMPLEMENTATION-20261019-v1',owner='01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2',base_head='889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1',decision='accepted bounded offline progress gate and publishable evidence',review_job=terminal['job_id'],review_candidate_sha256=sha(E/'candidate-manifest.json'),review_artifact_pins=audit['review_artifact_pins'],source_files={p:sha(PRODUCT/p) for p in paths},reviewed_implementation_and_docs_unchanged=True,dependency_pins_unchanged=55,author_regression=193,independent_regression=193,independent_counterexamples=8,main_followup_tests=45,low_finding_resolution=dict(method=name,before_sha256=candidate['candidate_pins'][test],after_sha256=sha(PRODUCT/test),patch_sha256=sha(E/'low-finding-test-only.patch'),scope='only new test body corrected after review; final test hash was not independently rerun; production remains exact reviewed source'),original24_test_methods_unchanged=True,formal29='not_run',production_channels='unavailable',native_ai='not_run',board='not_run',remaining=['genuine completion producer and authentication','original BOOT/causal source/clock providers','bounded live IPC and renderer integration','meaningful AI plus both H12 end-to-end controls'])
save(OUT/'actor-progress-main-selection.json',selection)
print(json.dumps(dict(selection_sha256=sha(OUT/'actor-progress-main-selection.json'),source_files=selection['source_files'],formal29='not_run')))
