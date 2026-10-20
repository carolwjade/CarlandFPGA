from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Preserve the exact original signed-zero assertion source alongside its RED.
text=(H/'finite_probe.gd').read_text(encoding='utf-8').replace('\tprint("ZERO_EMITTER token=",JSON.stringify(-0.0,"",true,true))\n','').replace('"00000000000000000000000000000000","existing emitter normalizes signed zero without value change"','"00000000000000800000000000000000","signed zero roundtrip bits"')
want=read(H/'raw/finite-zeros-final/result.json')['source_before']['tests/test_gate_finite.gd']
for payload in [text.encode(),text.replace('\n','\r\n').encode()]:
 if hashlib.sha256(payload).hexdigest()==want:
  (H/'preserved/signed-zero-original.gd').write_bytes(payload);break
else:raise AssertionError('Cannot recover exact signed-zero RED script')
pins=read(H/'candidate-pins.json')
txt='''Private G02 gate numeric candidate complete; PRODUCT adoption and independent algorithm review pending. All29 formal cards not_run.
Contract DEEPEYE-HUMAN-LOCK-20261014/revision1; H01-H15 canonical requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 verified root/PRODUCT; active director generation2 retained.
Four private candidate files share strict finite binary64 gate predicates and a gate-only exact decimal reader without schema changes. No epsilon or double-rounding acceptance. Existing Python geometry/clearance unchanged. JSON parser originally changed192/2100 input rows and bypassed48 invalid geometries; all observed bypasses fixed in candidate. Independent Fraction/Decimal/actual Python Gate oracles agree.
Fresh final native evidence: numeric2100rows/14628checks/0failures; reader183decimalfixtures/427checks/0; finite195/0; frozen-stage document696/0; frozen-stage persistence618/0. Python independent oracle rerun exit0;1116 legal corpus save/open layouts preserve exact coordinate bits. Existing emitter normalizes negative zero to positive zero; geometrically equivalent and explicitly accepted by main. Raw negative-zero tokens are correctly restored. Gate numeral tokens above2048 characters conservatively reject with reason; supported saved tokens are short. No tested residual predicate/reader mismatch remains; algorithm and worst-case performance still require independent review.
Preserved baseline RED14280checks/5024failures, parser-loss RED144failures, numeric-grammar RED2failures, both signed-zero extra probes6failures, first candidate parse errors/55s killed timeout and raw execution evidence. Prior final-combined150 manifest entries verify. No PRODUCT writes; concurrent unrelated PRODUCT UI/viewer/test deltas recorded, editor inputs unchanged. Broad results bind frozen pre-adoption stage. Final runs source/product maps unchanged. Expected invalid-input exponent and inherited Unicode diagnostics remain; no final script/parse/compile failure. No Git, external messages, GUI, Run, board, services, providers/credentials, queues/locks or children.
Adoption root competition/deepeye/simulator. Candidate: candidate/editor/{scene_document.gd,layout_codec.gd,gate_numeric.gd,gate_json_numbers.gd}. Exact source pins and editor baseline pins: candidate-pins.json. Patch SHA256 e403b274483c3074423950a4d12a358a0b95b4263345cfd62c339e7429e3c292. Review findings.md/design.md, candidate.patch, verification-summary.json, execution-ledger.json and raw/.
'''
(H/'final-result.txt').write_text(txt,encoding='utf-8')
rows=[]
excluded={'lease.private.json','assignment-record.json','manifest.json','receipt.json','native-complete-response.json'}
for p in sorted(H.rglob('*')):
 if not p.is_file() or p.name in excluded or 'tmp' in p.relative_to(H).parts or '.godot' in p.parts or '__pycache__' in p.parts:continue
 rows.append({'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
dump(H/'manifest.json',{'schema':1,'files':rows,'exclusions':['private lease and assignment metadata','manifest/receipt/completion response to avoid circularity','private engine temp/cache directories']})
dump(H/'receipt.json',{'schema':1,'candidate_only':True,'product_writes':False,'independent_review_pending':True,'formal_cards':'all29 not_run','manifest_sha256':sha(H/'manifest.json'),'result_sha256':sha(H/'final-result.txt'),'candidate_pins_sha256':sha(H/'candidate-pins.json'),'patch_sha256':pins['patch_sha256'],'native_terminal':'completion pending'})
for row in rows:assert sha(H/row['path'])==row['sha256']
print(json.dumps({'manifest_entries':len(rows),'manifest_sha256':sha(H/'manifest.json'),'result_sha256':sha(H/'final-result.txt'),'candidate_pins_sha256':sha(H/'candidate-pins.json'),'receipt_sha256':sha(H/'receipt.json')}))
