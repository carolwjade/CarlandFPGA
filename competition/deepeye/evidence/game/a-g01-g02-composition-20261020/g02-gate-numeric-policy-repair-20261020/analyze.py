from pathlib import Path
import json,hashlib,struct,sys,importlib.util
from fractions import Fraction as F
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cases=read(H/'cases.json');old=read(H/'raw/transport-diagnostic/observations.json');new=read(H/'raw/numeric-final/observations.json')
import prepare
gp=H/'oracle/gate_geometry.py'
assert sha(gp)==sha(ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulation/authority/motion/gate_geometry.py')
spec=importlib.util.spec_from_file_location('verified_authority',gp);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
assert len(cases)==len(old)==len(new)==2100
changed=[];bypasses=[];emitter=[];reopen=[]
for case,o,n in zip(cases,old,new):
 original=struct.unpack('<4d',bytes.fromhex(case['hex']))
 expected,_=prepare.oracle(case['entry_face'],*original[:2],case['exit_face'],*original[2:])
 try:g.validate_gate_pair(g.Gate(case['entry_face'],*original[:2]),g.Gate(case['exit_face'],*original[2:]));authority=True
 except ValueError:authority=False
 assert expected==authority==case['want']
 wire=json.loads(o['envelope'])['layout']['gates']
 pybits=''.join(struct.pack('<d',float(x)).hex() for g in [wire['entry'],wire['exit']] for x in [g['u'],g['v']])
 if pybits!=case['hex']:emitter.append(o['index'])
 if o['parsed_hex']!=case['hex']:changed.append(o['index'])
 if o['decoded']!=case['want']:bypasses.append(o['index'])
 assert n['valid']==n['encoded']==n['decoded']==case['want']
 if case['want']:
  assert n['reopened_hex']==case['hex'];reopen.append(n['index'])
assert not emitter and len(changed)==192 and len(bypasses)==48
limbs=read(H/'stage/competition/deepeye/simulator/tests/limb_observations.json')
for row in limbs:
 x=struct.unpack('<d',bytes.fromhex(row['hex']))[0]
 actual=sum(d<<(15*i) for i,d in enumerate(row['magnitude']))
 assert actual==abs(F(x))*2**1074
summary={'cases':2100,'original_engine_parser_changed_rows':changed,'original_engine_parser_invalid_to_valid_rows':bypasses,'original_emitter_changed_rows':emitter,'final_direct_and_encode_and_decode_oracle_mismatches':0,'final_exact_reopened_valid_rows':len(reopen),'final_reopen_bit_mismatches':0,'independent_magnitude_checks':len(limbs),'independent_oracles':['Fraction exact binary64 rational','Decimal precision2500','actual pinned Python Gate/validate_gate_pair','Python float(decimal_token) exact IEEE conversion'],'candidate_only':True,'formal_cards':'all29 not_run'}
dump(H/'verification-summary.json',summary)
prior=ROOT/'.planning/deepeye-resume-20261018/g02-final-combined-independent-20261020'
m=read(prior/'manifest.json')
for row in m['files']:
 p=prior/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
dump(H/'prior-integrity.json',{'manifest_sha256':sha(prior/'manifest.json'),'verified_entries':len(m['files']),'numeric_gap_sha256':sha(prior/'numeric-policy-observations.json'),'unchanged_against_persisted_prior_manifest':True})
product=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
before=read(H/'source-before.json')['product']
after={p.relative_to(product).as_posix():sha(p) for p in product.rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}
delta=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
assert all(not p.startswith('editor/') for p in delta)
dump(H/'source-after.json',{'product':after,'external_product_deltas':delta,'all_editor_inputs_unchanged':True,'candidate':{p.relative_to(H/'candidate').as_posix():sha(p) for p in (H/'candidate').rglob('*') if p.is_file()}})
execution=[]
for p in sorted((H/'raw').glob('*/result.json')):
 r=read(p);changed_product=[k for k in set(r['product_before'])|set(r['product_after']) if r['product_before'].get(k)!=r['product_after'].get(k)]
 execution.append({'label':p.parent.name,'result_sha256':sha(p),'pid':r['pid'],'engine_exit':r['exit_code'],'terminal':r['terminal'],'timed_out':r['timed_out'],'source_unchanged':r['source_unchanged'],'product_unchanged':r['product_unchanged'],'external_product_deltas':changed_product})
dump(H/'execution-ledger.json',execution)
print(json.dumps({k:summary[k] for k in ['cases','final_direct_and_encode_and_decode_oracle_mismatches','final_exact_reopened_valid_rows','final_reopen_bit_mismatches','independent_magnitude_checks']}))
print('prior_entries',len(m['files']),'external_deltas',delta)
