from pathlib import Path
import sys,json,math
from fractions import Fraction
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发");D=Path(__file__).resolve().parent;N=R/".local/a750/nav";plan=json.loads((N/'plan.json').read_bytes())
stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/'python-source';sys.path[:0]=[str(stage),plan['hostdeps']]
from competition.deepeye.simulation.authority import _world_values as v,g05_csr_projection_v1 as g
from competition.deepeye.simulation.authority.motion.demo_motion_profile import DEMO_100MS
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import OwnedInvocationPolicy
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1 as NAV
from competition.deepeye.simulation.authority.owned_invocation_v1.mechanics import DEMO_STEERING_3S_V1
catalog=json.loads(Path(plan['catalog_path']).read_bytes());pins=dict(plan['project_files']);entries=tuple(v.CatalogEntry(x['kind'],tuple(x['part_ids'])) for x in catalog['catalog'])
policy=v.ValuePolicy(pins[catalog['document_path']],pins[catalog['canonical_path']],pins[catalog['catalog_path']],plan['writer_inventory_sha256'],plan['source_bundle_sha256'],entries,tuple(catalog['presentation_part_ids']),tuple(pins[x] for x in catalog['allowed_script_paths']),run_id=plan['run_id'],getter_endpoint_cap_m=Fraction(1,1000),motion_profile=DEMO_100MS)
fs=list((N/'a').glob('actor-*/c46-invocation-*.jsonl'));first=min(fs,key=lambda p:int(p.stem.split('-')[-1]));last=max(fs,key=lambda p:int(p.stem.split('-')[-1]))
def public(f):
 row=json.loads(f.read_text(encoding='utf8').splitlines()[0]);return json.loads(bytes.fromhex(row['request_raw_hex'])[4:])['input']
p0=public(first);actual=public(last)
snapshot=v.snapshot_from_wire((N/'n/original-snapshot.json').read_bytes());initial=RigidState(tuple(p0['pose']['position_m']),tuple(p0['pose']['orientation_xyzw']),0.)
values=v._construct_values(snapshot,policy,initial,initial_monotonic_ns=0)
derived=values.budget_derivation
assert type(derived) is v.BudgetDerivation and type(derived.numeric_m) is Fraction and type(derived.asset_m) is Fraction
args=(actual['pose']['position_m'],actual['pose']['orientation_xyzw'],values.layout.red.center_m,values.layout.red.normal,values.envelope.half_segment_m,values.envelope.radius_m,derived.numeric_m,derived.asset_m,actual['goal_m'],'INSIDE')
# Actual public pose is still3.2m from red; legal Fraction values must reach
# unchanged out-of-domain return, rather than fail the type seam first.
result=g._public_exit_normal_goal(*args);assert result is None
print('actual BudgetDerivation/public750 seam accepted; out-of-domain None retained',flush=True)
def reject(fn):
 try:fn()
 except (ValueError,TypeError):return
 raise AssertionError('expected bound rejection')
for bad in (True,float('nan'),float('inf'),Fraction(-1,1000),Fraction(10001,1000)):
 row=list(args);row[6]=bad;reject(lambda row=row:g._public_exit_normal_goal(*row))
# Type-only fix must preserve float/Fraction-equivalent in-domain guidance.
q=[0.,math.sqrt(.5),0.,math.sqrt(.5)];a=([14.,11.8,0.],q,[15.,11.8,0.],[1.,0.,0.],Fraction(2,5),Fraction(3,25),derived.numeric_m,derived.asset_m,[15.571,11.8,0.],'INSIDE')
x=g._public_exit_normal_goal(*a);b=list(a);b[4:8]=[float(z) for z in a[4:8]];y=g._public_exit_normal_goal(*b);assert x==y and x is not None
owned=OwnedInvocationPolicy('pure757','a'*64,'b'*40,64,64,4096,12000,navigation_profile=NAV,steering_profile=DEMO_STEERING_3S_V1);owned.check();assert owned.public_goal_profile is None
out=dict(passed=True,controls=['actual_real_BudgetDerivation_and_actual750_public_pose_goal','bool_nonfinite_negative_over10_rejected','Fraction_float_in_domain_equivalence','defaultNone_policy_and_original_out_domain_None'],real_numeric=str(derived.numeric_m),real_asset=str(derived.asset_m),actual_public_file=str(last),actual_public_pose=actual['pose'],actual_public_goal=actual['goal_m'],AI=False,PDE=False,native=False,board=False,authority_minted=False)
(D/'CONTROLS.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
