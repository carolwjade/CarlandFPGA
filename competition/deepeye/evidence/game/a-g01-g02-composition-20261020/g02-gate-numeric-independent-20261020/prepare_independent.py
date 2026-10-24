from pathlib import Path
import hashlib,json,shutil,sys,struct,math,random,importlib.util
from fractions import Fraction as F
from decimal import Decimal,localcontext
H=Path(__file__).resolve().parent; ROOT=H.parents[2]
A=H.parent/'g02-gate-numeric-policy-repair-20261020'; S=H/'stage'
P=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def files(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts}
pins=json.loads((A/'candidate-pins.json').read_bytes())
for rel,digest in pins['files'].items():assert sha(A/'candidate'/rel)==digest
assert sha(A/'candidate.patch')==pins['patch_sha256']=='e403b274483c3074423950a4d12a358a0b95b4263345cfd62c339e7429e3c292'
assert sha(A/'manifest.json')=='2630b35ae6dda34dddf8bca434d6af0c21d79ac6b94485e2fd6411452ede2cb8'
for base in [ROOT,ROOT/'.local/deepeye-implementation-a']:
 d=json.loads((base/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
 assert hashlib.sha256(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [x['id'] for x in d['requirements']]==['H%02d'%i for i in range(1,16)]
assert json.loads((ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())['status']=='active'
assert not S.exists()
shutil.copytree(A/'stage/competition/deepeye/simulator',S,ignore=shutil.ignore_patterns('.godot','__pycache__','numeric_observations.json','limb_observations.json'))
for rel in pins['files']:shutil.copyfile(A/'candidate'/rel,S/rel)
(H/'oracle').mkdir()
authority=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulation/authority/motion/gate_geometry.py'
shutil.copyfile(authority,H/'oracle/gate_geometry.py')
spec=importlib.util.spec_from_file_location('independent_authority',H/'oracle/gate_geometry.py');g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
faces=['top','bottom','left','right','front','back'];rng=random.Random(2026102027)
rows=[]
def geometry(values,ef,xf,label):
 finite=all(math.isfinite(x) and abs(x)<=14.85 for x in values)
 want=finite and (ef!=xf or sum((F(values[i])-F(values[i+2]))**2 for i in (0,1))>=F(.3)**2)
 try:g.validate_gate_pair(g.Gate(ef,*values[:2]),g.Gate(xf,*values[2:]));actual=True
 except (ValueError,TypeError):actual=False
 assert actual==want,(label,values,want,actual)
 rows.append(dict(hex=struct.pack('<4d',*values).hex(),entry_face=ef,exit_face=xf,name=label,want=want))
for i in range(96):
 angle=rng.uniform(-math.pi,math.pi);a=rng.uniform(-14.3,14.3);b=rng.uniform(-14.3,14.3)
 c=a+.3*math.cos(angle);d=b+.3*math.sin(angle)
 for n in [-math.inf,math.inf]:geometry([a,b,math.nextafter(c,n),d],faces[i%6],faces[i%6],'translated-angular-nextafter')
for i in range(36):geometry([14.85,-14.85,-14.85,14.85],faces[i//6],faces[i%6],'directed-faces')
for v in [0.,-0.,math.ulp(0.),-math.ulp(0.),2**-1022,math.nextafter(14.85,math.inf),float('inf'),float('-inf'),float('nan')]:
 geometry([v,0.,.3,0.],'top','top','nonfinite-edge-subnormal')
for k in range(-40,5):
 x=math.ldexp(1.,k)
 geometry([-x,math.ulp(0.),.3-x,0.],'left','left','carry-cancellation-powers')
dump(S/'tests/independent_geometry.json',rows)
tokens=[]
def tok(t,label):
 if '9'*100 in t:
  want=(t.startswith('0e') or t.startswith('-1e-')) and len(t)<=2048
 else:
  try:q=F(t);want=abs(q)<16 and len(t)<=2048
  except ValueError:want=False
 value=float(t) if want else 0.
 tokens.append(dict(token=t,label=label,want=want,hex=struct.pack('<d',value).hex()))
with localcontext() as ctx:
 ctx.prec=4000
 for x in [0.,math.ulp(0.),2*math.ulp(0.),math.nextafter(2**-1022,0),2**-1022,2**-900,2**-53,.1,.3,1.,math.nextafter(1.,2.),7.75,14.85,math.nextafter(16.,0)]:
  y=math.nextafter(x,math.inf);mid=(Decimal.from_float(x)+Decimal.from_float(y))/2
  exact=format(mid,'f');delta=Decimal(10)**(-len(exact)-5)
  for v in [mid-delta,mid,mid+delta]:
   tok(format(v,'f'),'independent-exact-midpoint');tok('-'+format(v,'f'),'negative-midpoint')
 for i in range(24):
  x=math.ldexp(rng.uniform(.5,1.),rng.randint(-1073,3));tok(format(Decimal.from_float(x),'f'),'exact-represented')
 # 2048-byte supported finite tokens with dense coefficients and long scale.
 for exp in [-2041,-2365]:tok('1'+('2345678901'*205)[:2041]+'e'+str(exp),'maximum-dense-token')
 near=format((Decimal.from_float(.3)+Decimal.from_float(math.nextafter(.3,math.inf)))/2,'f')
 near=near+'0'*(2047-len(near))+'1';assert len(near)==2048
 tok(near,'maximum-near-midpoint')
 for t in ['1e'+'9'*2046,'-1e-'+'9'*2044,'0e'+'9'*2046,'0.'+'0'*2045+'1','0.'+'0'*2046+'1','16','-16','15.99999999999999999999999999','1e-324','2e-324','3e-324','1e+000000000000000000000000000000000000000000000000000000000000000001']:tok(t,'lexical-limits')
dump(S/'tests/independent_decimal.json',tokens)
dump(H/'input-pins.json',dict(candidate=pins,authority_sha256=sha(authority),author_authority_same=sha(authority)==sha(A/'oracle/gate_geometry.py'),product_before=files(P),stage_before=files(S),geometry_rows=len(rows),decimal_rows=len(tokens),contract_verified=True))
shutil.copyfile(H/'independent_probe.gd',S/'tests/independent_probe.gd')
print(json.dumps(dict(geometry_rows=len(rows),decimal_rows=len(tokens),candidate_verified=True)))
