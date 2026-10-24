"""Private numerical phase seeds only; no route, runtime or hardware acceptance."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
sys.path[:0] = [str(PRODUCT), str(ROOT / '.local/deepeye-host-deps')]
from competition.deepeye.tests.simulation import test_motion_executor as fixture

f=fixture.MotionExecutorTests();f.setUp()
p,w,cp=fixture.p,fixture.w,fixture.cp
cases=[]
for phase,z,yaw in [('EXIT_CROSSING',-15.519,7000),('EXIT_CROSSING',-15.5199,7000),
                    ('EXIT_CROSSING',-15.5184,7000),('EXIT_CROSSING',-15.519,0),
                    ('ENTRY_CROSSING',14.481,7000),('ENTRY_CROSSING',14.4815,7000)]:
    state=f.seeded(phase,(0,0,z))
    path=cp.CanonicalPath(state.pose,'fast_9600',20,yaw,0,fixture.DT,
        inherited_errors=p.required_inherited_errors(state,fixture.DT),
        error_budget_reference='explicit numerical phase fixture; not a preceding route')
    result=p.preview(state,path,state.context,expected_pose_revision=state.pose_revision,
        start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=state.monotonic_ns+fixture.DT+1,
        hard_stop=False)
    plan=path.plan(start_monotonic_ns=state.monotonic_ns,
        deadline_monotonic_ns=state.monotonic_ns+fixture.DT+1,hard_stop=False)
    cases.append({'phase_seed':phase,'z':z,'yaw':yaw,'software_numerical_seed_only':True,
                  'requested_dt_ns':fixture.DT,'covered_ns':plan.covered_ns,
                  'slice_windows':[[r.start.elapsed_ns,r.end.elapsed_ns] for r in plan.slices],
                  'status':result.status,'candidate_is_original':result.candidate is state,
                  'motion_grant':result.motion_grant,'cas_completed':result.atomic_cas_completed,
                  'candidate_seal':result.candidate.seal,'preview':w._canonical(result)})
(HERE/'numerical-traces.json').write_text(json.dumps({'workspace_version':w.VERSION,'cases':cases},
    ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([{'phase':r['phase_seed'],'z':r['z'],'yaw':r['yaw'],'status':r['status'],
                  'proof_count':len(r['preview']['proofs'])} for r in cases],indent=2))
