import hashlib,json,pathlib,sys,time
from fractions import Fraction
D=pathlib.Path(__file__).parent;N=pathlib.Path('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/a690/nav');plan=json.loads((N/'plan.json').read_bytes());run=json.loads((N/'run-result.json').read_bytes());sys.path[:0]=[str(D/'python-source'),plan['hostdeps']]
from competition.deepeye.simulation.authority import _world_values as v
from competition.deepeye.simulation.authority.motion import certified_path as cp,demo_motion_profile as h,passage_phase as p
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
catalog=json.loads(pathlib.Path(plan['catalog_path']).read_bytes());pins=dict(plan['project_files']);entries=tuple(v.CatalogEntry(x['kind'],tuple(x['part_ids'])) for x in catalog['catalog']);pol=v.ValuePolicy(pins[catalog['document_path']],pins[catalog['canonical_path']],pins[catalog['catalog_path']],plan['writer_inventory_sha256'],plan['source_bundle_sha256'],entries,tuple(catalog['presentation_part_ids']),tuple(pins[x] for x in catalog['allowed_script_paths']),run_id=plan['run_id'],getter_endpoint_cap_m=Fraction(1,1000),motion_profile=h.DEMO_100MS)
# Pure immutable DTO construction only; never a native owner/source/authority.
snapshot=v.snapshot_from_wire((N/'n/original-snapshot.json').read_bytes());first=run['cycles'][0]['advice']['observation']['em_pose'];initial=RigidState(tuple(first['position_m']),tuple(first['orientation_xyzw']),0.)
print('constructing actual snapshot numerical values',flush=True);values=v._construct_values(snapshot,pol,initial,initial_monotonic_ns=0);state=values.initial_state
print('numerical values constructed; reconstruct already closed preview prefix',flush=True)
for row in run['cycles']:
 t=row['target']
 for step in row['steps']:
  dt=step['dt_ns'];path=cp.CanonicalPath(state.pose,'fast_9600',t['speed_code'],t['yaw_q'],t['pitch_q'],dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS);tr=p.prepare_relative_transition(state,path,state.context,max_slices=16)
  assert tr.preview.status=='SAFE',(state.pose_revision,tr.preview.status,tr.preview.reason)
  state=tr.preview.candidate
print('closed numeric prefix reconstructed',state.pose_revision,flush=True)
from competition.deepeye.simulation.authority.g05_csr_projection_v1 import _nav_exit_goal
from competition.deepeye.simulation.authority.motion_executor import OwnedMotionExecutor
from competition.deepeye.simulation.authority.motion import solid_clearance as sc
import types
entry=values.layout.blue;inward=tuple(-x for x in entry.normal)
goal=_nav_exit_goal(entry.center_m,inward,values.envelope.half_segment_m,values.envelope.radius_m,values.budget_derivation.numeric_m,values.budget_derivation.asset_m,.05)
extra=0
while sum((Fraction(g)-Fraction(x))*Fraction(n) for g,x,n in zip(goal,state.pose.position_m,inward))>Fraction(4,100):
 dt=100_000_000
 path=cp.CanonicalPath(state.pose,'fast_9600',1,0,0,dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS)
 q=p.prepare_relative_transition(state,path,state.context,max_slices=16,entry_inward_clearance_v1=True).preview
 assert q.status=='SAFE',(q.status,q.reason)
 state=q.candidate;extra+=1;assert extra<=64
assert extra==8 and abs(state.pose.position_m[1]-14.468526388750007)<1e-12
probe=types.SimpleNamespace(_budget=values.budget,_model=values.model)
results=[]
for name,yaw,pitch in [('new_pure_yaw5013',5013,0),('new_actual_diagonal3638_3448',3638,3448)]:
 dt=100_000_000
 path=cp.CanonicalPath(state.pose,'fast_9600',14,yaw,pitch,dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS)
 q=p.prepare_relative_transition(state,path,state.context,max_slices=16).preview
 solids=[]
 for cast_record in path.plan(start_monotonic_ns=0,deadline_monotonic_ns=dt+1,hard_stop=False).slices:
  solid=sc.certify_scene(OwnedMotionExecutor._sweep(probe,cast_record),values.scene)
  solids.append(dict(status=solid.status))
 row=dict(name=name,speed_code=14,yaw_q=yaw,pitch_q=pitch,dt_ns=dt,preview_status=q.status,reason=q.reason,
  face_proofs=[[dict(face=y.face,cast_status=x.status,method=y.method) for y in x.faces] for x in q.proofs],
  solid_scene_checks=solids,bridges=len(q.bridges))
 results.append(row)
 print(json.dumps(row),flush=True)
 assert q.status=='SAFE' and all(s['status']=='CLEAR' for s in solids),(name,q.status,q.reason,solids)
 assert all(x.status=='SAFE' for x in q.proofs)
 assert len(q.bridges)==0
record=dict(passed=True,original_actual690_closed_prefix_reconstructed=True,entry_clearance_extra_steps=extra,
 original_704_target_pose_unchanged=list(state.pose.position_m),pose_revision=state.pose_revision,
 source_authority_minted=False,board=False,native=False,AI_model=False,PDE=False,
 scope='Pure exact actual snapshot/retained-prefix reconstruction and two new100ms previews at original entry40mm point; no execution authority',tests=results)
(D/'ENTRY40_NEW_STEERING_PREVIEW.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
