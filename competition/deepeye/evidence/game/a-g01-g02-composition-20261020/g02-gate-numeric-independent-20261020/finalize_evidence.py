from pathlib import Path
import json,hashlib,datetime
H=Path(__file__).resolve().parent;ROOT=H.parents[2];A=H.parent/'g02-gate-numeric-policy-repair-20261020';S=H/'stage'
P=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sources(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts}
pins=json.loads((A/'candidate-pins.json').read_bytes())
for rel,digest in pins['files'].items():assert sha(A/'candidate'/rel)==sha(S/rel)==digest
author_manifest=json.loads((A/'manifest.json').read_bytes())
for entry in author_manifest['files']:
 p=A/entry['path'];assert p.is_relative_to(A) and p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'],entry['path']
completion=json.loads((A/'native-complete-response.json').read_bytes())
assert completion['terminal'] is True and completion['status']=='completed'
assert completion['result']['text']==(A/'final-result.txt').read_text(encoding='utf8')
ledger=[]
for r in sorted((H/'raw').glob('*/result.json')):
 d=json.loads(r.read_bytes());assert d['terminal'] is True and not d['timed_out'] and not d['script_errors']
 assert not d['changed_product_files']
 assert sha(r.parent/'stdout.txt')==d['stdout_sha256'];assert sha(r.parent/'stderr.txt')==d['stderr_sha256']
 assert d['exit_code']==(1 if r.parent.name in ['candidate-grammar','baseline-grammar'] else 0)
 if r.parent.name not in ['prepare','python-checks']:assert d['source_unchanged']
 ledger.append({k:d[k] for k in ['argv','pid','terminal','exit_code','timed_out','elapsed_seconds','source_unchanged','changed_product_files','executable_sha256']})
before=json.loads((H/'input-pins.json').read_bytes())['product_before'];after=sources(P)
delta={k:{'before':before.get(k),'after':after.get(k)} for k in set(before)|set(after) if before.get(k)!=after.get(k)}
for rel,digest in pins['product_editor_baseline'].items():assert sha(P/rel)==digest
dump(H/'source-final.json',dict(candidate=pins['files'],product_editor_baseline=pins['product_editor_baseline'],product_delta=delta,product_after=after,author_verified_manifest_files=len(author_manifest['files']),author_native_terminal=True,author_exact_result=True))
dump(H/'execution-ledger.json',ledger)
receipt=dict(schema=1,job_id='child-1d03916dd1ca4cc18240fe9491f9da5a',agent_id='/root/g02_gate_numeric_independent_20261020',candidate_only=True,product_writes=False,product_editor_baseline_unchanged=True,product_delta=delta,formal_cards='all29 not_run',contract='DEEPEYE-HUMAN-LOCK-20261014/revision1',requirements_sha256='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',candidate_patch_sha256=pins['patch_sha256'],author_manifest_sha256=sha(A/'manifest.json'),author_verified_manifest_files=len(author_manifest['files']),independent_checks=1729,independent_failures=0,original_corpus_checks=14628,original_corpus_failures=0,preexisting_grammar_negative_runs=2,preexisting_grammar_failures_each=3,main_adoption_decision_pending=True,combined_current_integration_not_run=True,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
dump(H/'receipt.json',receipt)
print(json.dumps(dict(author_manifest_files=len(author_manifest['files']),verified_terminal_runs=len(ledger),product_delta=delta,candidate_pins_unchanged=True)))
