import dataclasses,json,math,pathlib,runpy,types
from fractions import Fraction
D=pathlib.Path(__file__).parent;x=runpy.run_path(str(D/'test_red_green704.py'));p=x['p'];cp=x['cp'];h=x['h'];v=x['values'];base=x['entry_start_state'];checks=[]
from competition.deepeye.simulation.authority import motion_executor as me,g05_csr_projection_v1 as projection,navigation_session_profile as nav
T=types.SimpleNamespace
command=me._Command(None,b'numeric-only',1,0,1,'fast_9600',1,0,0);owner=object.__new__(me.OwnedMotionExecutor);owner._root=T(command=command);owner._budget=v.budget;owner._admitted_navigation_profile=nav.NAV_ROUTE_LONGTTL_600S_V1
assert owner._demo_entry_inward_clearance(base,command) is True;checks.append('original exact route100ms minimum-speed straight selector allows bridge')
for foreign in (None,nav.NAV_FAST_LONGTTL_180S,object()):owner._admitted_navigation_profile=foreign;assert owner._demo_entry_inward_clearance(base,command) is False
owner._admitted_navigation_profile=nav.NAV_ROUTE_LONGTTL_600S_V1;checks.append('default/old180/foreign navigation selection denies')
for profile,code,yaw,pitch in [('fast_9600',14,0,0),('fast_9600',1,1607,0),('fast_9600',1,0,1),('stress_300',1,0,0)]:
 c=me._Command(None,b'numeric-only',1,0,1,profile,code,yaw,pitch);owner._root=T(command=c);assert owner._demo_entry_inward_clearance(base,c) is False
owner._root=T(command=command);checks.append('higher speed/angular/stress commands denied')
assert owner._demo_entry_inward_clearance(x['state'],command) is False;checks.append('beyond public clearance no retained bridge selection')
def path_for(state,code=1,yaw=0):return cp.CanonicalPath(state.pose,'fast_9600',code,yaw,0,100_000_000,inherited_errors=p.required_inherited_errors(state,100_000_000,motion_profile=h.DEMO_100MS),error_budget_reference=state.error_budget_reference,motion_profile=h.DEMO_100MS)
assert p.prepare_relative_transition(base,path_for(base),base.context).preview.status=='UNKNOWN';checks.append('old default still UNKNOWN for actual690 straight input')
try:p.prepare_relative_transition(base,path_for(base,14,1607),base.context,entry_inward_clearance_v1=True)
except ValueError:pass
else:raise AssertionError('turn used retained bridge')
checks.append('new numerical option rejects angular/higher-speed request')
fields={f.name:getattr(base,f.name) for f in dataclasses.fields(base) if f.init}
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
for label,position,q in [('outward',base.pose.position_m,(-math.sqrt(.5),0.,0.,math.sqrt(.5))),('other-wall',(14.9,base.pose.position_m[1],0.),base.pose.orientation_xyzw),('aperture-miss',(12.8,base.pose.position_m[1],0.),base.pose.orientation_xyzw)]:
 state=p._state(**dict(fields,pose=RigidState(position,q,base.pose.speed_m_s)));preview=p.prepare_relative_transition(state,path_for(state),state.context,entry_inward_clearance_v1=True).preview;assert preview.status!='SAFE',(label,preview.status);checks.append(label+' remains rejected')
path=path_for(base);preview=p.preview(base,path,base.context,expected_pose_revision=base.pose_revision,start_monotonic_ns=base.monotonic_ns,deadline_monotonic_ns=base.monotonic_ns+100_000_000+1,hard_stop=False,max_bridge_checks=0,entry_inward_clearance_v1=True);assert preview.status=='UNKNOWN' and 'work budget' in preview.reason;checks.append('original bridge work budget remains mandatory')
f=projection._nav_entry_clearance_reached
assert not f((0.,.041,0.),(0.,0.,0.),(0.,-1.,0.));assert f((0,Fraction(4,100),0),(0,0,0),(0,-1,0));assert f((0.,.039,0.),(0.,0.,0.),(0.,-1.,0.));checks.append('public normal remaining41mm hold/40mm switch/39mm switch')
class Channel:pass
key=Channel();layout=object();ctx=object();r=T(pose_revision=10,phase=T(context=ctx));ready=projection._nav_entry_clearance_ready
assert not ready(key,r,layout,(0.,.05,0.),(0.,0.,0.),(0.,-1.,0.));assert ready(key,r,layout,(0.,.02,0.),(0.,0.,0.),(0.,-1.,0.));assert ready(key,T(pose_revision=11,phase=T(context=ctx)),layout,(0.,.1,0.),(0.,0.,0.),(0.,-1.,0.));checks.append('own Root witness latches exit and never returns blue')
try:ready(key,T(pose_revision=9,phase=T(context=ctx)),layout,(0.,0.,0.),(0.,0.,0.),(0.,-1.,0.))
except ValueError:pass
else:raise AssertionError('stale clearance root accepted')
checks.append('stale Root clearance witness rejects')
result=dict(passed=True,controls=checks,source_authority_minted=False,board=False,AI_model=False,PDE=False,all29='not_run');(D/'BOUNDARY_CONTROLS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf8');print(json.dumps(result))