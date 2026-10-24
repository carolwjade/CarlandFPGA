"""Read-only design evidence and tiny interface probes, no executor implementation."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
BASE='9d29d4c87b964de98479fe62067aeb0da91ace63'
PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
MOTION='competition/deepeye/simulation/authority/motion/'
NAMES=['competition/deepeye/simulation/authority/pc_direct_runtime.py',
 'competition/deepeye/tests/simulation/test_pc_direct_runtime.py',
 'competition/deepeye/docs/pc_direct_runtime.md','competition/deepeye/docs/workspace_passage.md',
 'competition/deepeye/docs/authority_solid_clearance.md','competition/deepeye/docs/certified_motion_path.md',
 'competition/deepeye/integration/host_envelope.py','competition/deepeye/integration/pc_direct_watchdog.py',
 'competition/deepeye/integration/motion.py','competition/deepeye/docs/interface.json','competition/deepeye/docs/host_contract.json',
 'docs/competition/deepeye-2026/immutable_scope.json','docs/competition/deepeye-2026/immutable_scope.md',
 'docs/competition/deepeye-2026/taskbook_final.md','docs/competition/deepeye-2026/execution_plan_final.json',
 'docs/competition/deepeye-2026/simulation_contract_final.json']+[MOTION+n+'.py' for n in
 ('certified_path','passage_phase','workspace_boundaries','solid_clearance','kinematics','gate_clearance','gate_geometry')]
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def snapshot():return {p:sha((PRODUCT/p).read_bytes()) for p in NAMES}
env=os.environ.copy();env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
def git(*args):
    p=subprocess.run(['git','-C',str(PRODUCT),*args],capture_output=True,env=env)
    assert p.returncode==0,p.stderr.decode('utf8','replace')
    return p.stdout

def probes():
    sys.path[:0]=[str(PRODUCT),str(ROOT/'.local/deepeye-host-deps')]
    from competition.deepeye.tests.simulation import test_pc_direct_runtime as t
    from competition.deepeye.simulation.authority.motion import certified_path as cp
    from competition.deepeye.simulation.authority.motion import passage_phase as pp
    from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
    from competition.deepeye.simulation.authority.motion import gate_geometry as g
    from competition.deepeye.simulation.authority.motion import gate_clearance as gc
    from competition.deepeye.simulation.authority.motion.kinematics import RigidState
    f=t.PcDirectRuntimeTests();f.setUp();f.arm()
    started=f.clock.value
    f.provider.prepare_hook=lambda:setattr(f.clock,'value',f.clock.value+10_000)
    result=f.step()
    assert result.committed and result.receipt.start_ns==started+10_000
    body=w.Envelope(.4,.12,.52,'explicit independent mathematical fixture only',False)
    layout=w.Layout(g.Gate('front',0,0),g.Gate('back',0,0))
    context=pp.RunContext('fixture-run','frozen-static-scene',1,layout,body,'numeric owner assertion')
    state=pp.initialize(context,RigidState((0,0,15.522),(0,1,0,0),.25),gc.ErrorBounds(0.,0.,0.),
       pose_revision=0,monotonic_ns=started,error_budget_reference='exact fixture; not calibrated').state
    dt=10_000_000;drift=10_000
    path=cp.CanonicalPath(state.pose,'fast_9600',20,0,0,dt,
       inherited_errors=pp.required_inherited_errors(state,dt),error_budget_reference='carried fixture error')
    def preview(anchor):
        return pp.preview(state,path,context,expected_pose_revision=0,start_monotonic_ns=anchor,
                          deadline_monotonic_ns=anchor+dt+1,hard_stop=False)
    old=preview(started);new=preview(started+drift)
    assert old.status==new.status=='SAFE' and old.candidate.pose==new.candidate.pose
    assert old.candidate.trace_hash!=new.candidate.trace_hash
    assert len(old.candidate.history)==len(new.candidate.history)==2
    assert old.candidate.history[0]==new.candidate.history[0]
    assert new.candidate.history[-1].start_ns-old.candidate.history[-1].start_ns==drift
    assert new.candidate.history[-1].end_ns-old.candidate.history[-1].end_ns==drift
    capped=path.plan(start_monotonic_ns=started,deadline_monotonic_ns=started+dt,hard_stop=False)
    full=path.plan(start_monotonic_ns=started,deadline_monotonic_ns=started+dt+1,hard_stop=False)
    assert capped.covered_ns==dt-1 and full.covered_ns==dt
    data={'scope':'three tiny actual-interface design probes; no production executor/provider or full-suite acceptance',
      'runtime_clock_drift':{'prepare_clock_ns':started,'final_fence_start_ns':result.receipt.start_ns,'drift_ns':drift,
                            'fixture_commit':True},
      'phase_time_shift':{'same_numeric_pose':True,'same_old_history':True,'new_event_shift_ns':drift,
                         'trace_hash_changes':True,'phase':new.candidate.phase},
      'cp_deadline_convention':{'dt_ns':dt,'end_equal_deadline_covers_ns':capped.covered_ns,'full_step_requires_strict_end_before_deadline':True},
      'actual_hardware_AI_authentication_or_motion':False}
    save('interface_probe_results.json',data)
    print(json.dumps(data,ensure_ascii=False,indent=2))

def main():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    scope=json.loads((PRODUCT/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    assert sha(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==PIN
    assert [r['id'] for r in scope['requirements']]==['H%02d'%i for i in range(1,16)]
    before=snapshot();save('source_before.json',before)
    manifest={}
    api={}
    targets={'AuthorityDependencies','prepare_step','commit_step','StepFence','CommitReceipt','step',
      'CanonicalPath','CertifiedSample','CertifiedSlice','plan','sample','RunContext','PassageState','preview',
      'required_inherited_errors','initialize','prepare','check_slice','ErrorBounds','CapsuleModel','Sweep','Scene','certify_scene','RigidState','validate'}
    for name in NAMES:
        data=(PRODUCT/name).read_bytes();blob=git('show',BASE+':'+name)
        manifest[name]={'working_sha256':sha(data),'committed_blob_sha256':sha(blob),'working_equals_base_blob':data==blob}
        if name.endswith('.py'):
            nodes=ast.walk(ast.parse(data.decode('utf8')))
            api[name]=[{'name':node.name,'line':node.lineno,'kind':type(node).__name__} for node in nodes
                       if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in targets]
    save('dependency_manifest.json',{'base_commit':BASE,'requirements_sha256':PIN,'files':manifest})
    save('api_lines.json',api)
    command=[sys.executable,'-B','-X','utf8',str(Path(__file__)),'probes']
    with (OUT/'probes.stdout.raw.log').open('wb') as stdout,(OUT/'probes.stderr.raw.log').open('wb') as stderr:
        p=subprocess.run(command,cwd=PRODUCT,env=env,stdout=stdout,stderr=stderr,timeout=180)
    save('command.json',{'command':command,'cwd':str(PRODUCT),'exit_code':p.returncode,
      'scope':'three selected interface probes only; no R03/full runtime/math rerun','PYTHONDONTWRITEBYTECODE':'1'})
    assert p.returncode==0
    after=snapshot();assert before==after;save('source_after.json',after)
    print(json.dumps({'dependencies':len(manifest),'scoped_source_unchanged':True,'interface_probe_exit':0,
      'requirements_sha256':PIN,'isolation_files_read_or_written':False},indent=2))

if sys.argv[1:]==['probes']:probes()
else:main()
