"""New SYNTHETIC_TEST numeric controls; no native/source/board authority claim.

Catch default identity drift, missing same-profile transmission/100ms proof,
or a longer horizon bypassing unchanged whole-body/CAS/refusal boundaries.
"""
import hashlib
import importlib
import json
import pathlib
import unittest
from dataclasses import replace
from fractions import Fraction as F

from competition.deepeye.simulation.authority import _world_values as v
from competition.deepeye.simulation.authority import motion_executor as m
from competition.deepeye.simulation.authority import _offboard_motion_component as off
from competition.deepeye.simulation.authority.motion import certified_path as cp
from competition.deepeye.simulation.authority.motion import passage_phase as p
from competition.deepeye.simulation.authority.motion import workspace_boundaries as w
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion import solid_clearance as s
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
try:
    mh = importlib.import_module('competition.deepeye.simulation.authority.motion.demo_motion_profile')
except ModuleNotFoundError as exc:
    if not exc.name.endswith('demo_motion_profile'):
        raise
    mh = None

BASE = pathlib.Path('C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07')

def policy():
    return v.ValuePolicy(*(['0'*64]*5), (), (), (), run_id='SYNTHETIC_TEST_A379')

def numeric_executor(profile=None, scene=None):
    budget = (m.GeometryBudget(0,0,0,'SYNTHETIC_TEST_A379') if profile is None else
              m.GeometryBudget(0,0,0,'SYNTHETIC_TEST_A379',motion_profile=profile))
    context = p.RunContext('SYNTHETIC_TEST_A379','numeric-scene',0,
        w.Layout(g.Gate('front',0,0),g.Gate('back',0,0)),w.Envelope(.4,.12,.52,'numeric-body',False),'numeric-only')
    kwargs = {} if profile is None else dict(motion_profile=profile)
    initial = p.initialize(context,RigidState((0,0,15.6),(0,1,0,0),.25),gc.ErrorBounds(0.,0.,0.),
        pose_revision=0,monotonic_ns=0,error_budget_reference=budget.source,**kwargs).state
    ex = m.OwnedMotionExecutor(initial_state=initial,
        scene=scene or s.Scene('numeric-scene','v1',(),()),model=s.CapsuleModel('numeric-body','v1',.4,.12,.52),budget=budget)
    component = off.Component(ex)  # explicit pure fixture; timestamps are not QPC authority
    component.activate()
    component.command(sequence=1,issue_ns=0,deadline_ns=1_000_000_000,
        profile='fast_9600',speed_code=20,yaw_q=0,pitch_q=0)
    return ex, component

def archived_numeric_values(profile):
    # Reuse archived immutable input data, without importing/running any old test.
    book = BASE/'book-source-attempt-01'
    raw_plan = (book/'owned-world-plan-02.json').read_bytes()
    if hashlib.sha256(raw_plan).hexdigest() != 'b54107c9addc049b6759e059f325c09d0f54cb4ef1df3e6536c38a6b2fe7e321':
        raise ValueError('archived plan drift')
    plan = json.loads(raw_plan)
    raw = (book/'native-runs/source-01/original-snapshot.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != '2837758ade9124bb3118e5629b48a8d794a71f4b7845aa0d342732e4243271e7':
        raise ValueError('archived numerical snapshot drift')
    catalog_raw = pathlib.Path(plan['source_catalog_path']).read_bytes()
    if hashlib.sha256(catalog_raw).hexdigest() != plan['source_catalog_sha256']:
        raise ValueError('archived catalog drift')
    cat = json.loads(catalog_raw); pins = dict(plan['project_files']); project = pathlib.Path(plan['project_path'])
    def digest(name):
        actual = hashlib.sha256((project/name).read_bytes()).hexdigest()
        if pins.get(name) != actual: raise ValueError('archived source drift '+name)
        return actual
    writers = cat['writer_paths']
    if len(writers) != 11 or len(set(writers)) != 11: raise ValueError('writer inventory drift')
    material = b'DEY-WRITERS-1\n' + b''.join(name.encode()+b'\0'+bytes.fromhex(digest(name)) for name in sorted(writers))
    selected = v.ValuePolicy(digest(cat['document_path']),digest(cat['canonical_path']),digest(cat['catalog_path']),
        hashlib.sha256(material).hexdigest(),plan['source_bundle_sha256'],
        tuple(v.CatalogEntry(x['kind'],tuple(x['part_ids'])) for x in cat['catalog']),
        tuple(cat['presentation_part_ids']),tuple(digest(x) for x in cat['allowed_script_paths']),
        run_id=plan['run_id'],getter_endpoint_cap_m=F(1,1000),motion_profile=profile)
    pose = json.loads((book/'native-runs/source-01/result.json').read_text())['initial_pose']
    return selected, v._construct_values(v.snapshot_from_wire(raw),selected,
        RigidState(tuple(pose['position_m']),tuple(pose['orientation_xyzw']),0.),initial_monotonic_ns=0)

class DemoHorizonControls(unittest.TestCase):
    def test_default_10ms_preserves_original_identity_and_duration(self):
        selected = policy(); work = [0]; v._pack(selected,work)
        self.assertEqual(v._digest(selected),'406b93898f7c70078900aa884d8466cd11d84811a7da15c71157d84e76c649ca')
        self.assertEqual(work[0],3471)
        self.assertNotIn('motion_profile',v._pack(selected))
        budget = m.GeometryBudget(0,0,0,'SYNTHETIC_TEST_A379')
        self.assertEqual(w.digest(budget),'c29c8765cf4e4c87ad3a43d9d6785694e9b63ef1e2d9c0e36f23969dca398970')
        path = cp.CanonicalPath(RigidState((0,0,15.6),(0,1,0,0),.25),'fast_9600',20,0,0,10_000_000,
            inherited_errors=gc.ErrorBounds(0.,0.,0.),error_budget_reference=budget.source)
        self.assertEqual(w.digest(path.provenance),'d4a052ae11ecf88beeced5f007f0267c3792ace6e8399f647b74e2424539587e')
        self.assertEqual(path.sample(10_000_000).exact_distance_m,F(1,400))
        ex, component = numeric_executor()
        self.assertEqual(component.prepare(0,10_000_000).relative.duration_ns,10_000_000)
        with self.assertRaises(ValueError): component.prepare(0,10_000_001)

    def test_explicit_100ms_is_bound_through_world_budget_provenance_and_cas(self):
        self.assertIsNotNone(mh,'explicit typed horizon profile is not implemented')
        profile = mh.DEMO_100MS
        selected, world = archived_numeric_values(profile)
        self.assertIs(world.budget.motion_profile,profile)
        self.assertEqual(world.budget_derivation.source_pins_digest,v._digest(selected))
        self.assertNotEqual(v._digest(replace(selected,motion_profile=None)),v._digest(selected))
        self.assertIn(profile.sha256,world.budget.source)
        self.assertIn(profile.sha256,world.initial_state.error_budget_reference)
        self.assertEqual(world.budget.numeric,v.GUARD+F(1,1000))
        self.assertEqual(world.initial_scene_proof.status,'CLEAR')
        self.assertTrue(all(proof.status=='CLEAR' for proof in world.static_corridor_proofs))
        ex, component = numeric_executor(profile)
        before = ex.renderer_view()
        prepared = component.prepare(0,100_000_000)
        self.assertEqual(ex.renderer_view(),before)
        self.assertIs(prepared.path.provenance.motion_profile,profile)
        self.assertIn(profile.sha256,prepared.path.provenance.error_budget_reference)
        self.assertEqual(prepared.path.sample(100_000_000).exact_distance_m,F(1,40))
        self.assertTrue(prepared.solids and all(result.status=='CLEAR' for result in prepared.solids))
        receipt = component.commit(prepared,checked_ns=1,deadline_ns=500_000_000)
        self.assertEqual(receipt.end_ns-receipt.start_ns,100_000_000)
        self.assertEqual(ex.renderer_view().pose_revision,1)
        component.acknowledge(receipt)
        with self.assertRaises(ValueError): component.commit(prepared,checked_ns=100_000_001,deadline_ns=500_000_000)

    def test_invalid_mixed_profile_and_whole_body_obstacle_still_refuse(self):
        self.assertIsNotNone(mh,'explicit typed horizon profile is not implemented')
        for bad in (True,'100ms',{},100_000_000):
            with self.subTest(bad=repr(bad)),self.assertRaises((TypeError,ValueError)):
                v._digest(replace(policy(),motion_profile=bad))
        with self.assertRaises((TypeError,ValueError)):
            replace(mh.DEMO_100MS,max_dt_ns=100_000_001)
        with self.assertRaises((TypeError,ValueError)):
            replace(mh.DEMO_100MS,sha256='0'*64)
        profile = mh.DEMO_100MS
        ex, component = numeric_executor(profile)
        with self.assertRaises(ValueError): component.prepare(0,100_000_001)
        default, _ = numeric_executor()
        with self.assertRaises((TypeError,ValueError)):
            m.OwnedMotionExecutor(initial_state=default.passage_state(),scene=ex._scene,model=ex._model,budget=ex._budget)
        with self.assertRaises((TypeError,ValueError)):
            cp.CanonicalPath(ex.renderer_view().pose,'fast_9600',20,0,0,100_000_000,
                inherited_errors=gc.ErrorBounds(0.,0.,0.),error_budget_reference='unbound',motion_profile=profile)
        part = s.Solid('numeric-body-blocker','v1','box',(0,0,15.6),(.2,.2,.2),(0,0,0,1))
        scene = s.Scene('numeric-scene','v1',(('blocker',('numeric-body-blocker',)),),
            (s.SceneObject('blocker','hard_rock',(part,)),))
        blocked, block_component = numeric_executor(profile,scene)
        before = blocked.renderer_view()
        with self.assertRaises(m.PreparationRejected): block_component.prepare(0,100_000_000)
        self.assertEqual(blocked.renderer_view(),before)

if __name__ == '__main__': unittest.main(verbosity=2)
