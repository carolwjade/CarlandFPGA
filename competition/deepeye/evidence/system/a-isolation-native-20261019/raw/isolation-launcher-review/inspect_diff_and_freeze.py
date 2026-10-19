import difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'isolation-launcher-implementation'
def identity(p):
 b=p.read_bytes();return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((O/'before.json').read_text(encoding='utf-8'));baseline=json.loads((A/'baseline.json').read_text(encoding='utf-8'))
diff=[];originals={}
for rel,expected in b['source_manifest'].items():
 assert identity(P/rel)==expected and identity(O/'frozen'/rel)==expected
 old=A/'before'/rel
 if old.exists():
  assert identity(old)==baseline['files']['.local/deepeye-implementation-a/'+rel],rel
  originals[rel]=identity(old);before=old.read_text(encoding='utf-8').splitlines(True)
 else:before=[]
 diff.extend(difflib.unified_diff(before,(P/rel).read_text(encoding='utf-8').splitlines(True),fromfile='before/'+rel,tofile='candidate/'+rel))
for rel,expected in b['dependencies'].items():assert identity(R/rel)==expected,rel
(O/'candidate.diff').write_text(''.join(diff),encoding='utf-8')
save('after.json',{'candidate_unchanged':12,'dependencies_unchanged':len(b['dependencies']),'before_copies_verified':originals,'candidate':b['source_manifest']})
print(json.dumps({'candidate_unchanged':12,'dependencies_unchanged':len(b['dependencies']),'before_copies_verified':len(originals),'diff_lines':len(diff)}))
