from pathlib import Path
import json,sys,math,dataclasses
from types import SimpleNamespace as N
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发");D=Path(__file__).resolve().parent
base=json.loads((R/".local/a740/nav/plan.json").read_text(encoding="utf8"));stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/"python-source";sys.path[:0]=[str(stage),base['hostdeps']]
from competition.deepeye.simulation.authority import g05_csr_projection_v1 as g
from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import OwnedInvocationPolicy
from competition.deepeye.simulation.authority.owned_invocation_v1.mechanics import DEMO_STEERING_3S_V1
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1 as NAV,NAV_FAST_LONGTTL_180S as OLD
marker=getattr(g,'DEMO_PUBLIC_EXIT_NORMAL_V1',None);assert marker is not None,'explicit typed public-exit marker missing'
q0=[0.,math.sqrt(.5),0.,math.sqrt(.5)];c=[15.,11.8,0.];n=[1.,0.,0.];ordinary=[15.571002,11.8,0.]
def call(p=[14.,11.8,0.],q=q0,phase='INSIDE',active=False):return g._public_exit_normal_goal(p,q,c,n,.4,.12,.001,.000002,ordinary,phase,active=active)
def reject(f):
 try:f()
 except (ValueError,TypeError):return
 raise AssertionError('expected rejection')
passed=[]
#1 default policy and old projection branch remain default-off.
args=dict(operation_id='pure744',request_hash='a'*64,tested_commit='b'*40,max_invocations=64,max_reads=64,max_polls=4096,duration_ms=12000,navigation_profile=NAV,steering_profile=DEMO_STEERING_3S_V1)
OwnedInvocationPolicy(**args).check();assert OwnedInvocationPolicy(**args).public_goal_profile is None
OwnedInvocationPolicy(**args,public_goal_profile=marker).check();passed.append('defaultNone_and_actual_new_policy_constructor')
#2 foreign identity and old navigation rejected.
reject(lambda:OwnedInvocationPolicy(**args,public_goal_profile=dataclasses.replace(marker)).check());reject(lambda:OwnedInvocationPolicy(**dict(args,navigation_profile=OLD,max_invocations=16,steering_profile=None),public_goal_profile=marker).check());passed.append('foreign_equal_marker_and_old_profile_rejected')
#3 angular counterexample and new helper response; no model execution.
angle=math.radians(7);q=[0.,math.sin((math.pi/2-angle)/2),0.,math.cos((math.pi/2-angle)/2)]
out=call(q=q);assert out is not None and math.dist(out,[14.,11.8,0.])>.499999 and abs(out[2])>0
assert 1-math.cos(angle)<1-math.cos(math.atan(.35)-angle);passed.append('analytic7deg_deadband_and_public_goal_response')
#4 finite shapes and denominator checks.
reject(lambda:call(p=[True,11.8,0.]));reject(lambda:call(q=[0.,0.,0.,2.]));reject(lambda:call(p=[float('nan'),11.8,0.]));assert call(q=[0.,0.,0.,1.]) is None;passed.append('finite_bool_quaternion_normal_denominator_controls')
#5 near plane and far/lateral domains cannot initiate.
assert call(p=[14.6,11.8,0.]) is None and call(p=[13.,11.8,0.]) is None and call(p=[14.,12.4,0.]) is None;passed.append('first_activation_public_domain_limits')
#6 entry and arrival phases are never refined.
for phase in ('OUTSIDE_ENTRY','ENTRY_CROSSING','ARRIVED'):assert call(phase=phase) is None
passed.append('entry_and_ARRIVED_unchanged')
#7 real callback latch pointer/monotonic regression tests below use DTO-only stubs.
context=object();layout=N();root=N(pose_revision=10,phase=N(context=context));channel=object();gate=N(center_m=c,normal=n);pose=dict(position_m=[14.,11.8,0.],orientation_xyzw=q0)
assert g._refine_public_exit_goal(channel,root,layout,pose,gate,ordinary,.4,.12,.001,.000002,'INSIDE')!=ordinary
bad=N(pose_revision=9,phase=N(context=context));reject(lambda:g._refine_public_exit_goal(channel,bad,layout,pose,gate,ordinary,.4,.12,.001,.000002,'INSIDE'))
reject(lambda:g._refine_public_exit_goal(channel,root,N(),pose,gate,ordinary,.4,.12,.001,.000002,'INSIDE'));passed.append('strong_channel_layout_context_and_monotone_Root_latch')
#8 latched crossing keeps finite .5m normal goal but does not alter phase.
out=call(p=[14.9,11.8,0.],phase='EXIT_CROSSING',active=True);assert out is not None and abs(out[0]-15.4)<1e-12 and abs(out[1]-11.8)<1e-12 and abs(out[2])<1e-12;passed.append('latched_EXIT_CROSSING_normal_followthrough_no_near_goal_STOP')
#9 source/solid/gate authority code not modified.
manifest=json.loads((D/'SOURCE_MANIFEST.json').read_text(encoding='utf8'));assert len(manifest['changes'])==2;passed.append('only2host_files_no_gate_or_core_changes')
#10 narrow pure helper has no access to truth/material/query; exact input list only.
import inspect
helper=inspect.getsource(g._public_exit_normal_goal)
assert all(token not in helper for token in ('values.scene','sigma','conductivity','obstacle','certify_scene'))
assert len(inspect.signature(g._public_exit_normal_goal).parameters)==11;passed.append('pure_public_only_inputs_no_truth_channel')
#11 new projection selection is guarded by use_exit and same original Root path; default None exact.
source=(stage/'competition/deepeye/simulation/authority/g05_csr_projection_v1.py').read_text(encoding='utf8')
assert source.count('goal=_refine_public_exit_goal(')==1 and 'if use_exit and public_goal_profile is not None:' in source
passed.append('single_guarded_original_projection_callsite')
result=dict(passed=True,controls=passed,AI=False,model=False,PDE=False,native=False,board=False,UI=False,authority_minted=False,convergence_guaranteed=False)
(D/'CONTROLS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
