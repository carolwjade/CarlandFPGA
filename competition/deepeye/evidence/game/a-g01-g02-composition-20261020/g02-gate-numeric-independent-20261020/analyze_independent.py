from pathlib import Path
import hashlib,json,struct,math,importlib.util,sys
from fractions import Fraction as F
H=Path(__file__).resolve().parent;A=H.parent/'g02-gate-numeric-policy-repair-20261020';S=H/'stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('recheck_authority',H/'oracle/gate_geometry.py');g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
cases=json.loads((S/'tests/numeric_cases.json').read_bytes());observations=json.loads((S/'tests/numeric_observations.json').read_bytes())
assert len(cases)==len(observations)==2100
legal=0
for i,(row,ob) in enumerate(zip(cases,observations)):
 values=struct.unpack('<4d',bytes.fromhex(row['hex']))
 good=all(math.isfinite(x) and abs(x)<=14.85 for x in values) and (row['entry_face']!=row['exit_face'] or sum((F(values[j])-F(values[j+2]))**2 for j in (0,1))>=F(.3)**2)
 try:g.validate_gate_pair(g.Gate(row['entry_face'],*values[:2]),g.Gate(row['exit_face'],*values[2:]));actual=True
 except (ValueError,TypeError):actual=False
 assert good==actual==row['want']==ob['valid']==ob['encoded']==ob['decoded']
 if good:
  legal+=1;assert ob['reopened_hex']==row['hex']
  gates=json.loads(ob['wire'])['layout']['gates'];assert struct.pack('<4d',gates['entry']['u'],gates['entry']['v'],gates['exit']['u'],gates['exit']['v']).hex()==row['hex']
obs=json.loads((H/'raw/independent/observations.json').read_bytes())
fixtures=H/'grammar-fixtures';fixtures.mkdir(exist_ok=False)
grammar=[]
for ob in obs['observations']:
 if ob['kind']!='schema_grammar':continue
 name={'01':'leading-zero','1.':'missing-fraction','1.e0':'missing-fraction-with-exponent','1e+0':'valid-exponent'}[ob['token']]
 (fixtures/(name+'.json')).write_text(ob['text'],encoding='utf8')
 try:json.loads(ob['text']);strict=True
 except json.JSONDecodeError:strict=False
 grammar.append(dict(token=ob['token'],candidate_ok=ob['ok'],python_json_ok=strict))
# Retain the earlier runner's copied prior independent observations, explicitly
# named as such; use fresh numeric observations only for the original rerun.
old=H/'raw/original-corpus/observations.json'
if old.exists():old.rename(old.with_name('inherited-independent-observations.json'))
(H/'raw/original-corpus/numeric-observations.json').write_bytes((S/'tests/numeric_observations.json').read_bytes())
for base in [S,H/'baseline-stage']:
 (base/'editor').mkdir(parents=True,exist_ok=True)
 (base/'good.json').write_text(next(x['text'] for x in obs['observations'] if x.get('token')=='1e+0').replace('"schema": 1e+0','"schema": 1'),encoding='utf8')
 (base/'grammar_probe.gd').write_bytes((H/'grammar_probe.gd').read_bytes())
(H/'baseline-stage/project.godot').write_text('config_version=5\n',encoding='utf8')
(H/'baseline-stage/editor/layout_codec.gd').write_bytes((A/'baseline/editor/layout_codec.gd').read_bytes())
summary=dict(original_rows=len(cases),original_legal_roundtrips=legal,oracle_disagreements=0,grammar=grammar,candidate_exact_pins={k:sha(S/k) for k in json.loads((A/'candidate-pins.json').read_bytes())['files']},baseline_codec_sha256=sha(H/'baseline-stage/editor/layout_codec.gd'))
(H/'independent-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary))
