"""Read-only numerical diagnostics; no new passage implementation or motion commit."""
import hashlib,json
from pathlib import Path
from competition.deepeye.tests.simulation import test_motion_executor as fixture

O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a'
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,data):(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((O.parent/'trusted-motion-repair/source-manifest.json').read_text(encoding='utf-8'))
assert sha((O.parent/'trusted-motion-repair/source-manifest.json').read_bytes())=='1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533'
for path,item in manifest.items():assert sha((P/path).read_bytes())==item['sha256'],path
paths=list(manifest)+['competition/deepeye/simulation/authority/motion/workspace_boundaries.py','competition/deepeye/simulation/authority/motion/certified_path.py','competition/deepeye/simulation/authority/motion/gate_clearance.py','competition/deepeye/tests/simulation/test_passage_phase.py','competition/deepeye/tests/simulation/test_workspace_boundaries.py','competition/deepeye/docs/workspace_passage.md','docs/competition/deepeye-2026/taskbook_final.md','docs/competition/deepeye-2026/immutable_scope.json','docs/competition/deepeye-2026/immutable_scope.md']
before={name:{'bytes':len((P/name).read_bytes()),'sha256':sha((P/name).read_bytes())} for name in paths}
for root in (R,P):
 root.joinpath('docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf-8')
 data=json.loads(root.joinpath('docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 pin=sha(json.dumps(data['requirements'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
 assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
 assert [r['id'] for r in data['requirements']]==['H%02d'%n for n in range(1,16)]
f=fixture.MotionExecutorTests();f.setUp();p,w,cp=fixture.p,fixture.w,fixture.cp
cases=[]
for phase,z,yaw in [('EXIT_CROSSING',-15.519,7000),('EXIT_CROSSING',-15.5184,7000),('EXIT_CROSSING',-15.5199,7000),('EXIT_CROSSING',-15.519,0),('ENTRY_CROSSING',14.481,7000),('ENTRY_CROSSING',14.4815,7000)]:
 state=f.seeded(phase,(0,0,z));path=cp.CanonicalPath(state.pose,'fast_9600',20,yaw,0,fixture.DT,inherited_errors=p.required_inherited_errors(state,fixture.DT),error_budget_reference='explicit seeded mathematical diagnostic, not executed history')
 result=p.preview(state,path,state.context,expected_pose_revision=state.pose_revision,start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=state.monotonic_ns+fixture.DT+1,hard_stop=False)
 prepared=w.prepare(path,state.context.layout,state.context.envelope,start_monotonic_ns=state.monotonic_ns,deadline_monotonic_ns=state.monotonic_ns+fixture.DT+1,hard_stop=False)
 rows=[]
 for index,record in enumerate(prepared.plan.slices):
  row={'index':index,'start_elapsed_ns':record.start.elapsed_ns,'end_elapsed_ns':record.end.elapsed_ns,'end_z':record.end.state.position_m[2]}
  for role in ('entry','exit'):
   proof=w.check_slice(prepared,index,role)
   gate=state.context.layout.blue if role=='entry' else state.context.layout.red
   side=next(q for q in proof.end_sides if q.face==gate.face)
   row[role]={'status':proof.status,'active_face':gate.face,'end_inside':side.inside,'end_outside':side.outside,'monotone_at_gate':proof.monotone_at_gate,'face_methods':{q.face:q.method for q in proof.faces},'rho_m':proof.rho_m}
  rows.append(row)
 cases.append({'fixture_phase':phase,'fixture_z':z,'yaw_code':yaw,'count':len(rows),'current_preview':{'status':result.status,'reason':result.reason,'proof_count':len(result.proofs),'candidate_is_original':result.candidate is state},'slices':rows})
save('observations.json',{'software_fixtures_only':True,'no_preview_commit_or_motion_grant':True,'cases':cases})
save('source_hashes.json',{'requirements_sha256':pin,'files':before,'repaired_executor_manifest':manifest})
assert all(sha((P/name).read_bytes())==value['sha256'] for name,value in before.items())
print(json.dumps([{'phase':x['fixture_phase'],'z':x['fixture_z'],'yaw':x['yaw_code'],'slices':x['count'],'current':x['current_preview'],'exit_methods':[r['exit']['face_methods'].get('back') for r in x['slices']]} for x in cases],ensure_ascii=False))
