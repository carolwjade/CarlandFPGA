from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
A=H.parent/'g02-gate-numeric-policy-repair-20261020'
I=H.parent/'g02-gate-numeric-independent-20261020'
P=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def files(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts and q.name!='lease.private.json'}
pins=json.loads((A/'candidate-pins.json').read_bytes())
assert sha(A/'candidate.patch')==pins['patch_sha256']=='e403b274483c3074423950a4d12a358a0b95b4263345cfd62c339e7429e3c292'
for rel,digest in pins['files'].items():assert sha(A/'candidate'/rel)==digest
integrity={}
for base in [A,I]:
 manifest=json.loads((base/'manifest.json').read_bytes())
 for row in manifest['files']:assert sha(base/row['path'])==row['sha256'],row['path']
 integrity[base.name]={'manifest_sha256':sha(base/'manifest.json'),'verified_entries':len(manifest['files'])}
for base in [ROOT,ROOT/'.local/deepeye-implementation-a']:
 d=json.loads((base/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
 assert hashlib.sha256(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [x['id'] for x in d['requirements']]==['H%02d'%i for i in range(1,16)]
assert json.loads((ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())['status']=='active'
dump(H/'source-before.json',{'product':files(P),'author':files(A),'independent':files(I),'integrity':integrity,'candidate':pins})
S=H/'stage';assert not S.exists()
shutil.copytree(A/'stage/competition/deepeye/simulator',S,ignore=shutil.ignore_patterns('.godot','__pycache__','numeric_observations.json','limb_observations.json'))
for rel in pins['files']:shutil.copyfile(A/'candidate'/rel,S/rel)
shutil.copytree(A/'candidate',H/'baseline')
shutil.copytree(I/'grammar-fixtures',S/'grammar-fixtures')
shutil.copyfile(I/'grammar_probe.gd',S/'original_grammar_probe.gd')
good=(I/'grammar-fixtures/valid-exponent.json').read_text(encoding='utf8').replace('"schema": 1e+0','"schema": 1')
(S/'good.json').write_text(good,encoding='utf8')
shutil.copyfile(H/'grammar_probe.gd',S/'tests/grammar_probe.gd')
(H/'oracle').mkdir()
shutil.copyfile(I/'oracle/gate_geometry.py',H/'oracle/gate_geometry.py')
invalid=['01','-01','1.','1.e0','1e','1e+','1e-','+1','.1','--1','0x1','1_0']
valid=['0','-0','1','-1','1.0','-0.1','1e+0','1E-000','1e309','1e-9999','16','0.'+'1'*2050]
contexts=[('object','{"value":TOKEN}'),('array','{"values":[true,null,[TOKEN],false]}'),('obstacle','{"layout":{"obstacles":[{"position":{"x":TOKEN,"y":0,"z":0}}]}}')]
rows=[]
for label,template in contexts:
 for token in invalid+valid:
  text=template.replace('TOKEN',token)
  try:json.loads(text);want=True
  except json.JSONDecodeError:want=False
  assert want==(token in valid)
  rows.append({'label':label+':'+token[:24],'text':text,'want':want,'preserve':True})
for text in [json.dumps({'decoy':'01 1. 1.e0 +1 .1 --1 "u":01 \\ 1e','value':1}),'{"layout":[{"gates":{"entry":{"u":16}}}]}','{"layout":{"gates":[{"entry":{"u":16}}]}}','{"layout":{"gates":{"entry":[{"u":16}]}}}', '{"value":1.234567890123456789012345678901234567890123456789e2}']:
 json.loads(text);rows.append({'label':'string-or-fake-path','text':text,'want':True,'preserve':True})
for token in ['01','1.','1.e0','1e+0']:
 text='{"layout":{"gates":{"entry":{"u":'+token+'}}}}'
 try:json.loads(text);want=True
 except json.JSONDecodeError:want=False
 rows.append({'label':'real-gate:'+token,'text':text,'want':want,'preserve':False})
dump(S/'tests/grammar_cases.json',rows)
dump(H/'preparation.json',{'rows':len(rows),'original_fixture_pins':files(S/'grammar-fixtures'),'integrity':integrity,'contract_verified':True,'node_id':'A'})
print(json.dumps({'prepared':True,'grammar_rows':len(rows),'old_evidence_verified':integrity}))
