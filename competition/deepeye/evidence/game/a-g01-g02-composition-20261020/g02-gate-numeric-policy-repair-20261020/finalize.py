from pathlib import Path
import json,hashlib,difflib,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
candidate=H/'candidate';pins={p.relative_to(candidate).as_posix():sha(p) for p in candidate.rglob('*') if p.is_file()}
assert len(pins)==4
for rel,h in pins.items():assert sha(H/'stage/competition/deepeye/simulator'/rel)==h
patch=[]
for rel in sorted(pins):
 old=(H/'baseline'/rel).read_text(encoding='utf-8') if (H/'baseline'/rel).exists() else ''
 new=(candidate/rel).read_text(encoding='utf-8')
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel if old else '/dev/null',tofile='b/'+rel))
(H/'candidate.patch').write_text(''.join(patch),encoding='utf-8')
dump(H/'candidate-pins.json',{'adoption_root':'competition/deepeye/simulator','files':pins,'patch_sha256':sha(H/'candidate.patch'),'product_editor_baseline':{p.relative_to(H/'baseline').as_posix():sha(p) for p in (H/'baseline').rglob('*') if p.is_file()}})
required={'numeric-final':(0,'NUMERIC checks=14628 failures=0 rows=2100'),'reader-final':(0,'READER checks=427 failures=0 cases=183'),'finite-zero-policy-final':(0,'FINITE checks=195 failures=0'),'document-regression':(0,'TESTS checks=696 failures=0'),'persistence-regression':(0,'TESTS checks=618 failures=0'),'red':(1,'NUMERIC checks=14280 failures=5024 rows=2100'),'transport-diagnostic':(1,'NUMERIC checks=13512 failures=144 rows=2100'),'reader-grammar-red':(1,'READER checks=419 failures=2 cases=183'),'finite-zeros-final':(1,'FINITE checks=195 failures=6')}
for label,(exit_code,marker) in required.items():
 r=read(H/'raw'/label/'result.json');out=(H/'raw'/label/'stdout.bin').read_text(encoding='utf-8')
 assert r['terminal'] and not r['timed_out'] and r['exit_code']==exit_code and marker in out
 if label.endswith('final') or label.endswith('regression'):
  assert r['source_unchanged'] and r['product_unchanged']
  for rel,h in pins.items():assert r['source_before'][rel]==h
 assert 'SCRIPT ERROR' not in (H/'raw'/label/'stderr.bin').read_text(encoding='utf-8')
py=read(H/'raw/python-independent-oracles/result.json');assert py['terminal'] and py['exit_code']==0 and not py['timed_out']
ledger=[]
for p in sorted((H/'raw').glob('*/result.json')):
 r=read(p);row={k:r[k] for k in ['pid','exit_code','terminal','timed_out']};row.update(label=p.parent.name,result_sha256=sha(p))
 if 'product_before' in r:row.update(source_unchanged=r['source_unchanged'],product_unchanged=r['product_unchanged'],external_product_deltas=sorted(k for k in set(r['product_before'])|set(r['product_after']) if r['product_before'].get(k)!=r['product_after'].get(k)))
 ledger.append(row)
dump(H/'execution-ledger.json',ledger)
# Recover only bytes whose exact execution-time hash verifies; do not invent a
# replacement for failed evidence. All raw streams/results remain untouched.
r=read(H/'raw/green/result.json');recovered=[]
doc=(candidate/'editor/scene_document.gd').read_text(encoding='utf-8')
codec=(H/'baseline/editor/layout_codec.gd').read_text(encoding='utf-8').replace('extends RefCounted','extends RefCounted\n\nconst GateNumericScript = preload("res://editor/gate_numeric.gd")',1).replace('const EPSILON := 0.000000001\n','').replace('absf(float(gate.u)) > GATE_EDGE_LIMIT + EPSILON or absf(float(gate.v)) > GATE_EDGE_LIMIT + EPSILON','not GateNumericScript.valid_coordinate(float(gate.u)) or not GateNumericScript.valid_coordinate(float(gate.v))').replace('separation < MIN_SAME_FACE_SEPARATION - EPSILON','GateNumericScript.circles_overlap(float(gates.entry.u), float(gates.entry.v), float(gates.exit.u), float(gates.exit.v))')
helper=(candidate/'editor/gate_numeric.gd').read_text(encoding='utf-8').split('\nstatic func _small_product')[0].replace('\t\tif a[i] == 0:\n\t\t\tcontinue\n','')
for rel,text in [('editor/scene_document.gd',doc),('editor/layout_codec.gd',codec),('editor/gate_numeric.gd',helper)]:
 for payload in [text.encode(),text.replace('\n','\r\n').encode()]:
  if hashlib.sha256(payload).hexdigest()==r['source_before'][rel]:
   p=H/'preserved/first-candidate-parse'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload);assert sha(p)==r['source_before'][rel];recovered.append(rel);break
dump(H/'preserved/first-candidate-recovery.json',{'recovered_execution_exact_files':recovered,'all_raw_failure_evidence_unchanged':True})
print(json.dumps({'candidate_files':pins,'patch_sha256':sha(H/'candidate.patch'),'verified_runs':list(required),'processes':len(ledger),'recovered_first_candidate_files':recovered}))
