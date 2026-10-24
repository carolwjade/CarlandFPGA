"""Read-only current-source diagnostics. No proposed reducer or motion grant.

Seeded histories are numerical fixtures, not proof of a preceding route.
The candidate lemma arithmetic is a necessary design diagnostic only.
"""
from pathlib import Path
from dataclasses import replace
from decimal import Decimal
import hashlib,json,subprocess,unittest
from competition.deepeye.tests.simulation.test_passage_phase import PassagePhaseTests
from competition.deepeye.simulation.authority.motion import passage_phase as p
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc

ROOT=Path(__file__).resolve().parents[3]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
OUT=Path(__file__).resolve().parent
PIN='3f702903f1e16fa72eae15f03ba431b78de24bd0'
SCOPE='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
DT=10_000_000
OBS=[]
PATHS=[
 'competition/deepeye/simulation/authority/motion/'+x for x in
 ('passage_phase.py','workspace_boundaries.py','certified_path.py','gate_clearance.py','gate_geometry.py','kinematics.py','solid_clearance.py')]
PATHS += ['competition/deepeye/simulation/authority/'+x for x in ('motion_executor.py','pc_direct_runtime.py')]
PATHS += ['competition/deepeye/tests/simulation/'+x for x in ('test_passage_phase.py','test_motion_executor.py','test_workspace_boundaries.py')]
PATHS += ['competition/deepeye/docs/'+x for x in ('certified_motion_path.md','workspace_passage.md','motion_executor.md','authority_solid_clearance.md','passage_suffix_checkpoint_20261019.md')]
PATHS += ['docs/competition/deepeye-2026/'+x for x in ('taskbook_final.md','simulation_contract_final.json','immutable_scope.md','immutable_scope.json','execution_plan_final.json')]

def sha(b):return hashlib.sha256(b).hexdigest()
def manifest():
    files={}
    for n in PATHS:
        path=PRODUCT/n
        if not path.exists():raise AssertionError('missing exact dependency '+n)
        raw=path.read_bytes();files[n]={'sha256':sha(raw),'bytes':len(raw)}
    scope=json.loads((PRODUCT/'docs/competition/deepeye-2026/immutable_scope.json').read_text('utf-8'))
    canonical=json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert sha(canonical)==SCOPE and [x['id'] for x in scope['requirements']]==['H%02d'%i for i in range(1,16)]
    git=subprocess.run(['git','rev-parse','HEAD'],cwd=PRODUCT,capture_output=True,text=True,check=True)
    assert git.stdout.strip()==PIN,git.stdout
    return {'head':git.stdout.strip(),'requirements_sha256':sha(canonical),'files':files}

def summary(proof):
    return {'status':proof.status,'role':proof.role,'binding':proof.binding,'rho_m':proof.rho_m,
      'monotone_at_gate':proof.monotone_at_gate,'faces':[{ 'face':f.face,'method':f.method,
      'lower':str(f.lower),'upper':str(f.upper),'gate_status':f.gate_certificate.status if f.gate_certificate else None} for f in proof.faces],
      'start_sides':[{k:str(getattr(s,k)) for k in ('face','minimum_lower','maximum_upper')} for s in proof.start_sides],
      'end_sides':[{k:str(getattr(s,k)) for k in ('face','minimum_lower','maximum_upper')} for s in proof.end_sides]}

class Diagnostics(unittest.TestCase):
    def setUp(self):self.fx=PassagePhaseTests();self.fx.setUp()
    def inspect(self,name,position,*,q=(0,1,0,0),yaw=7000,context=None,errors=None):
        state=self.fx.numerical_seed('ENTRY_CROSSING',position,q,context)
        if errors is not None:
            values={k:getattr(state,k) for k in state.__dataclass_fields__ if k!='seal'};values['errors']=errors;state=p._state(**values)
        path=self.fx.path(state,yaw=yaw)
        prepared=w.prepare(path,state.context.layout,state.context.envelope,start_monotonic_ns=10,deadline_monotonic_ns=10+DT+1,hard_stop=False)
        result=self.fx.step(state,path=path,context=state.context)
        row={'name':name,'position':position,'orientation':q,'yaw_q':yaw,'preview_status':result.status,
          'original_candidate':result.candidate is state,'candidate_phase':result.candidate.phase,
          'retained_proofs':[summary(x) for x in result.proofs],'records':[]}
        for i,r in enumerate(prepared.plan.slices):
            entry=w.check_slice(prepared,i,'entry');exit_=w.check_slice(prepared,i,'exit')
            # This upper bound deliberately uses whole-record error, NOT the
            # weaker point-time errors. Full cast rho remains in entry proof.
            sample=replace(r.start,errors=r.errors)
            upper=next(s.maximum_upper for s in w.point_sides(sample,state.context.envelope) if s.face==state.context.layout.blue.face)
            k=g._exact(r.gate_bounds.curvature_upper_per_m)
            slope=g._DOWN.subtract(w._COS5_LOWER,(g._exact(state.context.envelope.pivot_radius_m)*k).hi)
            row['records'].append({'index':i,'start_ns':r.start.elapsed_ns,'end_ns':r.end.elapsed_ns,
              'distance_start':str(r.start.exact_distance_m),'distance_end':str(r.end.exact_distance_m),
              'errors':w._canonical(r.errors),'arc_upper_m':r.gate_bounds.arc_length_upper_m,
              'rotation_upper_rad':r.gate_bounds.rotation_upper_rad,
              'candidate_uniform_start_blue_support_upper':str(upper),'candidate_inward_slope_lower':str(slope),
              'entry':summary(entry),'exit':summary(exit_)})
        OBS.append(row);return row,result
    def test_nominal_gap_and_supported_neighbor(self):
        for z,expected in ((14.481,'SAFE'),(14.4815,'UNKNOWN')):
            row,res=self.inspect(str(z),(0,0,z));self.assertEqual(expected,res.status)
            self.assertEqual([(0,7142857),(7142857,DT)],[(r['start_ns'],r['end_ns']) for r in row['records']])
            self.assertTrue(all(r['entry']['status']=='SAFE' for r in row['records']))
            tail=row['records'][1];self.assertLess(Decimal(tail['candidate_uniform_start_blue_support_upper']),Decimal('-1e-12'))
            self.assertGreater(Decimal(tail['candidate_inward_slope_lower']),0)
            self.assertEqual('SAFE' if z==14.481 else 'UNKNOWN',tail['exit']['status'])
            self.assertTrue(all(r['entry']['rho_m']>=.0005 for r in row['records']))
    def test_real_direction_rotation_wrong_face_corner_and_contact_fail_closed(self):
        for name,pos,q,yaw,ctx in (
          ('reverse blue',(0,0,14.4815),(0,0,0,1),7000,None),
          ('rotation rim',(.0295,0,15.),(0,1,0,0),7000,None),
          ('wrong right face',(15.6,0,14.4815),(0,1,0,0),7000,None),
          ('corner',(14.8794,0,14.4815),(0,1,0,0),7000,replace(self.fx.context,layout=w.Layout(g.Gate('front',14.85,0),g.Gate('back',0,0)))),
          ('exact rim contact',(.03,0,15.),(0,1,0,0),0,replace(self.fx.context,envelope=replace(self.fx.body,exact_fixture=True)))):
            with self.subTest(name=name):
                row,res=self.inspect(name,pos,q=q,yaw=yaw,context=ctx)
                self.assertNotEqual('SAFE',res.status);self.assertTrue(row['original_candidate'])
                if name=='exact rim contact':self.assertEqual('VIOLATION_PROVED',res.status)
    def test_same_face_legal_editor_pair_and_role_separation(self):
        ctx=replace(self.fx.context,layout=w.Layout(g.Gate('front',-.15,0),g.Gate('front',.15,0)))
        row,res=self.inspect('same-face inward at blue',(-.15,0,14.4815),context=ctx)
        self.assertEqual('UNKNOWN',res.status)
        self.assertTrue(all(r['entry']['status']=='SAFE' for r in row['records']))
        row,res=self.inspect('same-face outward through blue',(-.15,0,14.4815),q=(0,0,0,1),context=ctx)
        self.assertNotEqual('SAFE',res.status)
        with self.assertRaises(ValueError):w.Layout(g.Gate('front',-.149,0),g.Gate('front',.149,0))
    def test_whole_record_error_can_destroy_stronger_handoff(self):
        row,res=self.inspect('source uncertainty dominates',(0,0,14.4815),errors=gc.ErrorBounds(.001,0.,0.))
        tail=row['records'][1]
        self.assertGreater(Decimal(tail['candidate_uniform_start_blue_support_upper']),0)
        # This seed never meets ENTERED at the middle edge. The existing entry
        # role legitimately continues and only records ENTERED at the final edge;
        # it does not need or qualify for the proposed after-ENTERED bridge.
        self.assertEqual(('SAFE','INSIDE'),(res.status,res.candidate.phase))
        self.assertEqual(10+DT,res.candidate.history[-1].end_ns)

if __name__=='__main__':
    before=manifest();(OUT/'before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Diagnostics)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'observations.json').write_text(json.dumps(OBS,indent=2)+'\n',encoding='utf-8')
    after=manifest();(OUT/'after.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    assert before==after,'exact dependencies changed'
    raise SystemExit(0 if result.wasSuccessful() else 1)
