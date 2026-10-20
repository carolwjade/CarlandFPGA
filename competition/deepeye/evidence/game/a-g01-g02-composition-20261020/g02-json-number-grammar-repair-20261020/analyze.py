from pathlib import Path
import hashlib,json,struct,math,importlib.util,sys
from fractions import Fraction as F
H=Path(__file__).resolve().parent;ROOT=H.parents[2];S=H/'stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((H/'candidate-pins.json').read_bytes())
for rel,digest in pins['files'].items():assert sha(S/rel)==sha(H/'candidate'/rel)==digest
authority=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulation/authority/motion/gate_geometry.py'
assert sha(authority)==sha(H/'oracle/gate_geometry.py')
spec=importlib.util.spec_from_file_location('recheck_authority',H/'oracle/gate_geometry.py');g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
cases=json.loads((S/'tests/numeric_cases.json').read_bytes());obs=json.loads((H/'raw/numeric-final/numeric_observations.json').read_bytes())
assert len(cases)==len(obs)==2100
legal=0
for row,ob in zip(cases,obs):
 values=struct.unpack('<4d',bytes.fromhex(row['hex']))
 good=all(math.isfinite(x) and abs(x)<=14.85 for x in values) and (row['entry_face']!=row['exit_face'] or sum((F(values[j])-F(values[j+2]))**2 for j in (0,1))>=F(.3)**2)
 try:g.validate_gate_pair(g.Gate(row['entry_face'],*values[:2]),g.Gate(row['exit_face'],*values[2:]));actual=True
 except (ValueError,TypeError):actual=False
 assert good==actual==row['want']==ob['valid']==ob['encoded']==ob['decoded']
 if good:
  legal+=1;assert ob['reopened_hex']==row['hex']
  gates=json.loads(ob['wire'])['layout']['gates'];assert struct.pack('<4d',gates['entry']['u'],gates['entry']['v'],gates['exit']['u'],gates['exit']['v']).hex()==row['hex']
rows=json.loads((S/'tests/grammar_cases.json').read_bytes())
for row in rows:
 try:json.loads(row['text']);want=True
 except json.JSONDecodeError:want=False
 assert want==row['want']
grammar=json.loads((H/'raw/grammar-state-final/grammar_observations.json').read_bytes())
assert grammar['checks']==176 and grammar['failures']==0
for ob in grammar['observations']:
 assert ob['accepted']==ob['want']
 if ob['kind']=='obstacle':
  try:json.loads(ob['text']);want=True
  except json.JSONDecodeError:want=False
  assert ob['accepted']==want
I=H.parent/'g02-gate-numeric-independent-20261020'
for q in (I/'grammar-fixtures').iterdir():
 assert sha(q)==sha(S/'grammar-fixtures'/q.name)
 try:json.loads(q.read_bytes());want=True
 except json.JSONDecodeError:want=False
 assert want==(q.stem=='valid-exponent')
summary={'original_numeric_rows':len(cases),'legal_exact_roundtrips':legal,'oracle_disagreements':0,'grammar_rows':len(rows),'grammar_assertions':grammar['checks'],'grammar_failures':grammar['failures'],'original_fixtures_reused_exact':4,'full_obstacle_cases':6,'authority_sha256':sha(authority),'candidate':pins}
(H/'verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary))
