from pathlib import Path
import sys,json,math,ast,dataclasses
R=Path(r"C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发")
D=Path(__file__).resolve().parent
plan=json.loads((R/".local/a710/nav/plan.json").read_text(encoding="utf8"))
stage=Path(sys.argv[1]) if len(sys.argv)>1 else D/"python-source"
sys.path[:0]=[str(stage),plan["hostdeps"]]
from competition.deepeye.simulation.authority.owned_invocation_v1 import mechanics as m
from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import OwnedInvocationPolicy
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ROUTE_LONGTTL_600S_V1 as NAV,NAV_FAST_LONGTTL_180S as OLDNAV
from competition.deepeye.integration import motion
marker=getattr(m,"DEMO_STEERING_3S_V1",None)
assert marker is not None,"new explicit typed steering-horizon marker is required"
run=json.loads((R/".local/a710/nav/run-result.json").read_text(encoding="utf8"))
passed=[];fixture=[]
def good(name):passed.append(name)
def reject(fn):
 try:fn()
 except (ValueError,TypeError):return
 raise AssertionError("expected finite-policy rejection")
for row in run["cycles"]:
 if row["cycle"]<16:continue
 advice=row["advice"];public=dict(pose=advice["observation"]["adc_pose"])
 old=m.quantize_target(advice,public,"fast_9600",12000,motion,max_duration_ms=12000,navigation_profile=NAV)
 assert old==row["target"],(old,row["target"])
 new=m.quantize_target(advice,public,"fast_9600",12000,motion,max_duration_ms=12000,navigation_profile=NAV,steering_profile=marker)
 assert new["duration_ms"]==12000 and new["speed_code"]==old["speed_code"]
 assert new["yaw_q"]**2+new["pitch_q"]**2<=motion.curvature_limit_squared("fast_9600",new["speed_code"])
 assert new["yaw_q"]>old["yaw_q"]
 fixture.append(dict(cycle=row["cycle"],old=old,new=new,risk=advice["risk"]))
good("six_actual710_public_direction_fixtures_old_exact_new_ROM_bounded")
advice=run["cycles"][15]["advice"];public=dict(pose=advice["observation"]["adc_pose"])
q=lambda **kw:m.quantize_target(advice,public,"fast_9600",12000,motion,max_duration_ms=12000,**kw)
reject(lambda:q(navigation_profile=OLDNAV,steering_profile=marker));good("old180_profile_rejects_new_marker")
reject(lambda:q(navigation_profile=NAV,steering_profile=dataclasses.replace(marker)));good("foreign_equal_marker_rejected")
reject(lambda:q(navigation_profile=NAV,steering_profile={"horizon_ms":3000}));good("untyped_marker_rejected")
reject(lambda:m.quantize_target(advice,public,"fast_9600",3000,motion,max_duration_ms=12000,navigation_profile=NAV,steering_profile=marker));good("marker_requires_actual12s_target")
stop=dict(advice,status="STOP")
assert m.quantize_target(stop,public,"fast_9600",12000,motion,max_duration_ms=12000,navigation_profile=NAV,steering_profile=marker)==dict(action=0,yaw_q=0,pitch_q=0,speed_code=0,duration_ms=0);good("STOP_unchanged")
args=dict(operation_id="local-seam",request_hash="a"*64,tested_commit="b"*40,max_invocations=64,max_reads=64,max_polls=1024,duration_ms=12000,navigation_profile=NAV)
OwnedInvocationPolicy(**args,steering_profile=marker).check();OwnedInvocationPolicy(**args).check();good("actual_policy_constructor_new_and_old_default")
reject(lambda:OwnedInvocationPolicy(**dict(args,navigation_profile=OLDNAV,max_invocations=16),steering_profile=marker).check());good("actual_policy_rejects_wrong_navigation")
source=(stage/"competition/deepeye/simulation/authority/owned_invocation_v1/adapter.py").read_text(encoding="utf8")
assert source.count("steering_profile=self.policy.steering_profile")==1;good("original_completion_projection_calls_typed_quantizer_once")
identity=dict(pose=dict(orientation_xyzw=[0.,0.,0.,1.]))
for signx,signy in ((1,0),(-1,0),(1,1),(-1,-1)):
 v=[.35*signx,.35*signy,1.];norm=math.sqrt(sum(x*x for x in v));a=dict(status='ADVISE',direction_world=[x/norm for x in v],speed_limit_m_s=.18)
 out=m.quantize_target(a,identity,'fast_9600',12000,motion,max_duration_ms=12000,navigation_profile=NAV,steering_profile=marker)
 assert out['yaw_q']*signx>0 and (out['pitch_q']==0 if signy==0 else out['pitch_q']*signy>0)
 assert out['yaw_q']**2+out['pitch_q']**2<=motion.curvature_limit_squared('fast_9600',14)
good('all_steering_signs_and_combined_ROM_preserved')
a=dict(status='ADVISE',direction_world=[math.sin(math.pi/180),0.,math.cos(math.pi/180)],speed_limit_m_s=.18)
base=m.quantize_target(a,identity,'fast_9600',12000,motion,max_duration_ms=12000,navigation_profile=NAV)
new=m.quantize_target(a,identity,'fast_9600',12000,motion,max_duration_ms=12000,navigation_profile=NAV,steering_profile=marker)
assert (base['yaw_q'],new['yaw_q'])==(83,333) and new['duration_ms']==base['duration_ms']==12000
good('small_unsaturated_error_gain4_target_TTL_unchanged')
legacy=m.quantize_target(a,identity,'fast_9600',100,motion)
assert legacy==dict(action=1,yaw_q=5013,pitch_q=0,speed_code=14,duration_ms=100)
good('legacy_default100ms_target_exact')
result=dict(passed=True,controls=passed,actual710_fixtures=fixture,model=False,board=False,native=False,PDE=False)
(D/"QUANTIZATION_RESULTS.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8");print(json.dumps(result))
