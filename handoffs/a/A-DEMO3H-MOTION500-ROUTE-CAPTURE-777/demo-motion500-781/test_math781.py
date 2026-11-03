from pathlib import Path
import sys,json,ast,dataclasses
from decimal import Decimal,localcontext
from fractions import Fraction
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发");D=Path(__file__).resolve().parent;base=Path(R/'.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07/route-capture-budget-772/python-source');stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/'python-source';sys.path[:0]=[str(stage),str(R/'.local/deepeye-host-deps')]
from competition.deepeye.simulation.authority.motion import demo_motion_profile as h,certified_path as cp,gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
profile=getattr(h,'DEMO_500MS',None);assert profile is not None,'new explicit500ms profile missing'
passed=[]
def reject(fn):
 try:fn()
 except (ValueError,TypeError):return
 raise AssertionError('expected proof-domain refusal')
assert h.max_dt_ns(None)==10_000_000 and h.max_dt_ns(h.DEMO_100MS)==100_000_000 and h.max_dt_ns(profile)==500_000_000
reject(lambda:h.validate_profile(dataclasses.replace(profile)));reject(lambda:h.validate_profile({'max_dt_ns':500000000}));passed.append('exact_new500_default10_old100_and_foreign_rejection')
# Same directed implementation is compared to original AST for old domains.
oldtext=(base/'competition/deepeye/simulation/authority/motion/certified_path.py').read_text(encoding='utf8');tree=ast.parse(oldtext);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_trig_from_square');ns=dict(vars(cp));exec(compile(ast.Module(body=[fn],type_ignores=[]),'original trig','exec'),ns)
for p,z in ((None,Decimal('.0000015625')),(h.DEMO_100MS,Decimal('.00015625'))):
 for cos in (False,True):
  x=cp._I.exact(z);new=cp._trig_from_square(x,cosine=cos,motion_profile=p);old=ns['_trig_from_square'](x,cosine=cos,motion_profile=p);assert (new.lo,new.hi)==(old.lo,old.hi)
passed.append('old_trig_outputs_exact_same_intervals')
for z in (Decimal(0),Decimal('.00015625'),Decimal('.001'),Decimal('.00390625')):
 for cos in (False,True):
  got=cp._trig_from_square(cp._I.exact(z),cosine=cos,motion_profile=profile)
  # Fraction alternating series gives independent exact true-function bracket.
  x=Fraction(z);total=Fraction(1);term=Fraction(1)
  for j in range(1,21):
   term=term*x/((2*j-1)*(2*j) if cos else (2*j)*(2*j+1));total=total-term if j%2 else total+term
  rem=term*x/(41*42 if cos else 42*43)
  assert Fraction(got.lo)<=total-rem<=total<=Fraction(got.hi)
reject(lambda:cp._trig_from_square(cp._I.exact(Decimal('.003906250001')),motion_profile=profile))
reject(lambda:cp._trig_from_square(cp._I.exact(Decimal('.00390625')),motion_profile=h.DEMO_100MS));passed.append('new_square_domain_endpoint_true_sinc_cos_bounds_plus1_rejection')
assert gc._slice_rotation_limit(None)==gc._MAX_SLICE_ROTATION and gc._slice_rotation_limit(h.DEMO_100MS)==gc._MAX_SLICE_ROTATION
assert gc._slice_rotation_limit(profile).lo>gc._MAX_SLICE_ROTATION.hi
passed.append('new500_slice250millideg_only_old50millideg_unchanged')
# Full-speed worst-ROM numerical path: original complete interval generation.
path=cp.CanonicalPath(RigidState((0.,0.,0.),(0.,0.,0.,1.),.25),'fast_9600',20,7161,0,500_000_000,inherited_errors=gc.ErrorBounds(0.,0.,0.),error_budget_reference=h.bind_reference('pure781',profile),motion_profile=profile)
plan=path.plan(start_monotonic_ns=0,deadline_monotonic_ns=500_000_001,hard_stop=False);assert plan.covered_ns==500_000_000 and 1<=len(plan.slices)<=16
assert all(Decimal.from_float(x.gate_bounds.rotation_upper_rad)<=gc._slice_rotation_limit(profile).lo for x in plan.slices)
passed.append('worst_speed_ROM500ms_contiguous_complete_plan_fits16_slices')
reject(lambda:cp.CanonicalPath(path.provenance.start_state,'fast_9600',20,7161,0,500_000_001,inherited_errors=gc.ErrorBounds(0.,0.,0.),error_budget_reference=h.bind_reference('pure781',profile),motion_profile=profile));passed.append('new500ms_exact_upper_and_plus1_refusal')
# The selected coarser slice domain cannot relax original angle/radial gates.
import math
g=gc.g;gate=g.Gate('right',0.,11.8);capsule=g.Capsule((15.,11.8,0.),(1.,0.,0.))
bounds=gc.SliceBounds((15.01,11.8,0.),.011,0.,math.radians(.2));errors=gc.ErrorBounds(0.,0.,0.)
assert gc.sweep_clearance(capsule,gate,direction=1,errors=errors,bounds=bounds).status=='UNKNOWN'
cert=gc.sweep_clearance(capsule,gate,direction=1,errors=errors,bounds=bounds,motion_profile=profile)
assert cert.status=='SAFE_IF_INTERSECTING' and cert.motion_grant is False
badangle=g.Capsule((15.,11.8,0.),(math.cos(math.radians(7)),math.sin(math.radians(7)),0.))
assert gc.sweep_clearance(badangle,gate,direction=1,errors=errors,bounds=bounds,motion_profile=profile).status=='UNKNOWN'
badradial=g.Capsule((15.,11.8,.04),(1.,0.,0.));radialbounds=gc.SliceBounds((15.01,11.8,.04),.011,0.,0.)
assert gc.sweep_clearance(badradial,gate,direction=1,errors=errors,bounds=radialbounds,motion_profile=profile).status=='UNKNOWN'
overbounds=gc.SliceBounds((15.01,11.8,0.),.011,0.,math.radians(.251))
assert gc.sweep_clearance(capsule,gate,direction=1,errors=errors,bounds=overbounds,motion_profile=profile).status=='UNKNOWN'
passed.append('new_slice_domain_preserves_strict5deg_radial_and250millideg_failure')
r=dict(passed=True,controls=passed,profile_commitment=h.commitment(profile),worst_plan_slices=len(plan.slices),new_domain='.00390625',proof='Alternating decreasing directedTaylorj4 with unchangedj5 remainder; exactFraction20-term bracket reference',model=False,PDE=False,board=False,native=False,UI=False,source_authority_minted=False)
(D/'MATH_CONTROLS.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps(r))
