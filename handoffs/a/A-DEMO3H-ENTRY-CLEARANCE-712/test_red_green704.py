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
last=run['cycles'][-1];t=last['target'];dt=100_000_000
path=cp.CanonicalPath(state.pose,'fast_9600',t['speed_code'],t['yaw_q'],t['pitch_q'],dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS);failed=p.prepare_relative_transition(state,path,state.context,max_slices=16).preview
record=dict(actual_operation=run['operation_id'],reconstructed_pose_revision=state.pose_revision,reconstructed_pose={'position_m':list(state.pose.position_m),'orientation_xyzw':list(state.pose.orientation_xyzw),'speed_m_s':state.pose.speed_m_s},actual_retained_pose=run['failed_step_owner_diagnostic']['position_m'],red_preview=dict(status=failed.status,reason=failed.reason,failure_candidate=failed.failure_candidate,proofs=[dict(status=x.status,reason=x.reason,faces=[dict(face=y.face,method=y.method) for y in x.faces]) for x in failed.proofs]),numeric_only=True,synthetic_relative_time_anchor=0,source_authority_minted=False,board=False,AI_model=False,PDE=False)
(D/'ACTUAL690_PREVIEW_RED.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n',encoding='utf8');print(json.dumps(record),flush=True)# Counterfactual pure preview only: keep the public inward goal until30mm remaining.
from competition.deepeye.simulation.authority.g05_csr_projection_v1 import _nav_exit_goal
entry=values.layout.blue;inward=tuple(-x for x in entry.normal);goal=_nav_exit_goal(entry.center_m,inward,values.envelope.half_segment_m,values.envelope.radius_m,values.budget_derivation.numeric_m,values.budget_derivation.asset_m,.05)
entry_start_state=state
extra=0;bridge_counts=[];solid_checks=[]
from competition.deepeye.simulation.authority.motion_executor import OwnedMotionExecutor
from competition.deepeye.simulation.authority.motion import solid_clearance as sc
import types
probe=types.SimpleNamespace(_budget=values.budget,_model=values.model)
while sum((Fraction(g)-Fraction(x))*Fraction(n) for g,x,n in zip(goal,state.pose.position_m,inward))>Fraction(4,100):
 dt=100_000_000;path=cp.CanonicalPath(state.pose,'fast_9600',1,0,0,dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS);q=p.prepare_relative_transition(state,path,state.context,max_slices=16,entry_inward_clearance_v1=True).preview;assert q.status=='SAFE',(q.status,q.reason);bridge_counts.append(len(q.bridges))
 for cast_record in path.plan(start_monotonic_ns=0,deadline_monotonic_ns=dt+1,hard_stop=False).slices:
  status=sc.certify_scene(OwnedMotionExecutor._sweep(probe,cast_record),values.scene).status;assert status=='CLEAR',status;solid_checks.append(status)
 state=q.candidate;extra+=1;assert extra<=64
path=cp.CanonicalPath(state.pose,'fast_9600',t['speed_code'],t['yaw_q'],t['pitch_q'],dt,inherited_errors=p.required_inherited_errors(state,dt,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS);green=p.prepare_relative_transition(state,path,state.context,max_slices=16).preview;assert green.status=='SAFE',(green.status,green.reason)
remaining=float(sum((Fraction(g)-Fraction(x))*Fraction(n) for g,x,n in zip(goal,state.pose.position_m,inward)))
risk=run['cycles'][-2]['advice']['risk']
minimum_distance=.0125/(.5*(1.-risk))
actual_speed_limit=.5*remaining*(1.-risk)
assert minimum_distance<remaining<=.04 and int(actual_speed_limit/.0125)>=1
assert extra==8 and len(bridge_counts)==extra
for cast_record in path.plan(start_monotonic_ns=0,deadline_monotonic_ns=dt+1,hard_stop=False).slices:
 status=sc.certify_scene(OwnedMotionExecutor._sweep(probe,cast_record),values.scene).status;assert status=='CLEAR',status;solid_checks.append(status)
out=dict(original_red=record['red_preview'],entry_goal=goal,new_public_remaining_threshold_m=.04,counterfactual_inward100ms_steps=extra,bridge_counts_each_step=bridge_counts,complete_scene_solid_checks=solid_checks,simulation_only_extra_ns=extra*100_000_000,new_numeric_start_pose=list(state.pose.position_m),new_remaining_distance_m=remaining,actual_entry_risk=risk,original_quantization_minimum_distance_m=minimum_distance,calculated_original_speed_limit_m_s=actual_speed_limit,old_AI_minimum_speed_trap_avoided=remaining>minimum_distance,identical_actual690_turn_target=t,new_preview=dict(status=green.status,reason=green.reason,faces=[[dict(face=y.face,method=y.method) for y in x.faces] for x in green.proofs]),all_prior_strict_gates_unchanged=True,source_authority_minted=False,board=False,AI_model=False,PDE=False,actual_new_motion=False)
(D/'ACTUAL690_COUNTERFACTUAL_GREEN.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n',encoding='utf8');print(json.dumps(out),flush=True)