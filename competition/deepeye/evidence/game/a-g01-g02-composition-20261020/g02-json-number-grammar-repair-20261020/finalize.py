from pathlib import Path
import json,hashlib,re,datetime
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
A=H.parent/'g02-gate-numeric-policy-repair-20261020';I=H.parent/'g02-gate-numeric-independent-20261020'
P=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def files(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts and q.name!='lease.private.json'}
before=json.loads((H/'source-before.json').read_bytes());pins=json.loads((H/'candidate-pins.json').read_bytes())
after={'product':files(P),'author':files(A),'independent':files(I),'candidate':files(H/'candidate'),'stage':files(H/'stage')}
assert before['author']==after['author'] and before['independent']==after['independent']
delta={k:{'before':before['product'].get(k),'after':after['product'].get(k)} for k in before['product'].keys()|after['product'].keys() if before['product'].get(k)!=after['product'].get(k)}
assert not any(k.startswith('editor/') for k in delta)
after['product_delta']=delta;after['old_evidence_unchanged']=True
for rel,digest in pins['files'].items():assert sha(H/'candidate'/rel)==sha(H/'stage'/rel)==digest
assert sha(H/'candidate-additive.patch')==pins['additive_patch_sha256']
# Apply the portable unified patch to the exact reviewed baseline without Git.
rel='editor/gate_json_numbers.gd';src=(H/'baseline'/rel).read_text(encoding='utf8').splitlines(True)
patch=(H/'candidate-additive.patch').read_text(encoding='utf8').splitlines(True)
result=[];at=0;i=2
while i<len(patch):
 m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',patch[i]);assert m,patch[i]
 start=int(m[1])-1;assert start>=at;result.extend(src[at:start]);at=start;i+=1
 while i<len(patch) and not patch[i].startswith('@@ '):
  line=patch[i];kind=line[0];assert kind in ' +-'
  if kind in ' -':assert src[at]==line[1:];at+=1
  if kind in ' +':result.append(line[1:])
  i+=1
result.extend(src[at:]);blob=''.join(result).encode('utf8')
assert blob==(H/'candidate'/rel).read_bytes()
out=H/'patch-application'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(blob)
after['additive_patch_exact_reconstruction']=True;dump(H/'source-after.json',after)
# Preserve exact earlier runner sources as verified against recorded hashes.
current=(H/'run_bounded.py').read_bytes()
v2=current.replace(b"if label=='prepare' or label.startswith('analyze'):",b"if label in ['prepare','analyze']:")
v1=v2.replace(b"if label=='grammar-red-corrected':S=H/'baseline-stage'\n",b'')
versions={hashlib.sha256(v).hexdigest():v for v in [current,v2,v1]}
for index,blob in enumerate([v1,v2,current],1):(H/'preserved'/('run_bounded_v%d.py'%index)).write_bytes(blob)
ledger=[]
for p in sorted((H/'raw').glob('*/result.json')):
 r=json.loads(p.read_bytes());assert r['harness_sha256'] in versions
 assert r['terminal'] and not r['timed_out'] and not r['script_errors'] and not r['changed_product_files']
 assert r['stdout_sha256']==sha(p.parent/'stdout.txt') and r['stderr_sha256']==sha(p.parent/'stderr.txt')
 for k,digest in pins['files'].items():
  if p.parent.name not in ['prepare','grammar-red','grammar-red-corrected']:
   assert r['source_after'][k]==digest
 ledger.append({'run':p.parent.name,'record':p.relative_to(H).as_posix(),'record_sha256':sha(p),'pid':r['pid'],'exit_code':r['exit_code'],'terminal':r['terminal'],'script_errors':r['script_errors'],'elapsed_seconds':r['elapsed_seconds']})
dump(H/'execution-ledger.json',ledger)
print(json.dumps({'actual_subprocess_records':len(ledger),'old_evidence_unchanged':True,'product_delta':delta,'additive_patch_exact_reconstruction':True,'candidate':pins['files']}))
