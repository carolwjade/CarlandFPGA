import importlib.util,json,pathlib,sys,hashlib,math
from decimal import Decimal,localcontext
D=pathlib.Path(__file__).parent;f=json.loads((D/'ACTUAL670_FAILED_INPUT.json').read_bytes());sys.path.insert(0,f['source_stage'])
from competition.deepeye.simulation.authority.motion import certified_path as original
from competition.deepeye.simulation.authority.motion import demo_motion_profile as h,gate_clearance as gc,gate_geometry as g
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
cp=original
if len(sys.argv)>1:
 name=original.__name__;spec=importlib.util.spec_from_file_location(name,pathlib.Path(sys.argv[1]));cp=importlib.util.module_from_spec(spec);sys.modules[name]=cp;spec.loader.exec_module(cp)
state=RigidState(**{k:tuple(v) if isinstance(v,list) else v for k,v in f['state'].items()});t=f['target'];path=cp.CanonicalPath(state,'fast_9600',t['speed_code'],t['yaw_q'],t['pitch_q'],f['dt_ns'],inherited_errors=gc.ErrorBounds(0.,0.,0.),error_budget_reference=h.bind_reference('ACTUAL670-ONE-INPUT',h.DEMO_100MS),motion_profile=h.DEMO_100MS)
distance,speed=path.distance_speed(f['dt_ns']);sq=path._curvature_squared*cp._fraction_interval(distance).square();sample=path.sample(f['dt_ns']);assert all(math.isfinite(x) for x in sample.state.position_m)
checks=['actual670 endpoint sample red->green']
try:cp._trig_from_square(g._Interval.exact(Decimal('.000002')))
except ValueError:checks.append('legacy default exact old domain still rejects')
else:raise AssertionError('legacy default enlarged')
# 70-digit independent power-series enclosure check for the actual argument and demo bound.
for z in (sq.lo,sq.hi,Decimal('.00015626')):
 for cosine in (False,True):
  interval=cp._trig_from_square(g._Interval.exact(z),cosine=cosine,motion_profile=h.DEMO_100MS)
  with localcontext() as c:
   c.prec=90;term=Decimal(1);total=term
   for n in range(1,15):term=term*z/Decimal((2*n-1)*(2*n) if cosine else (2*n)*(2*n+1));total=total-term if n%2 else total+term
   err=abs(term*z/Decimal(870 if cosine else 930))
   assert interval.lo<=total-err and total+err<=interval.hi,(z,cosine,interval,total)
checks.append('actual and full DEMO100 domain sinc/cos within independent90digit series bounds')
try:cp._trig_from_square(g._Interval.exact(Decimal('.000156261')),motion_profile=h.DEMO_100MS)
except ValueError:checks.append('new demo beyond explicit proved bound rejects')
else:raise AssertionError('demo bound bypassed')
print(json.dumps(dict(passed=True,checks=checks,actual_arc_m=float(distance),actual_square=[str(sq.lo),str(sq.hi)],old_domain='.0000015626',demo_domain='.00015626',new_endpoint_position=list(sample.state.position_m),new_endpoint_speed=sample.state.speed_m_s,board=False,AI_model=False,PDE=False)))