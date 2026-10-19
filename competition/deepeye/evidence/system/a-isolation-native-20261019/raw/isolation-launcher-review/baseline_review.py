import hashlib,json,shutil,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'isolation-launcher-implementation'
def identity(p):
 b=p.read_bytes();return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert identity(A/'source-manifest.json')['sha256']=='0bdabec4a3c465e269c090bffd8fb690b2797750f47c4e4c7165e8e4d6a51376'
assert identity(A/'report.md')['sha256']=='1ad8e50427a88a4fdcfec70839de9b32ddff7fe6d0f97272095c8390308a742b'
m=json.loads((A/'source-manifest.json').read_text(encoding='utf-8'));assert len(m)==12
for rel,expected in m.items():
 assert identity(P/rel)==expected and identity(A/'frozen'/rel)==expected,rel
 target=O/'frozen'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/rel,target)
for root in (R,P):
 d=json.loads((root/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 pin=hashlib.sha256(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [q['id'] for q in d['requirements']]==['H%02d'%i for i in range(1,16)]
 (root/'docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf-8')
b=json.loads((A/'baseline.json').read_text(encoding='utf-8'));deps={}
for rel,expected in b['files'].items():
 if rel.startswith('.local/deepeye-implementation-a/') and rel.removeprefix('.local/deepeye-implementation-a/') in m:continue
 assert identity(R/rel)==expected,rel;deps[rel]=expected
assert len(deps)==236,len(deps)
assert identity(P/'competition/deepeye/simulation/isolation/resource_cleanup.py')['sha256']=='4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f'
save('before.json',{'source_manifest':m,'dependencies':deps,'requirements_sha256':pin,'head':subprocess.check_output(['git','-C',str(P),'rev-parse','HEAD']).decode().strip()})
shutil.copyfile(A/'unit_suite.py',O/'author_unit_suite.py')
print(json.dumps({'candidate_matches_frozen':12,'dependencies_match':len(deps),'requirements_sha256':pin}))
