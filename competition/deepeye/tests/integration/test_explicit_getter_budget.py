import hashlib
import json
import pathlib
import sys
import unittest
from dataclasses import replace
from fractions import Fraction as F

from competition.deepeye.simulation.authority import _world_values as v
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

BASE = pathlib.Path(r'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07')
OWN = BASE/'explicit-getter-budget-construction'
BOOK = BASE/'book-source-attempt-01'

def fixture():
    plan_bytes=(BOOK/'owned-world-plan-02.json').read_bytes()
    if hashlib.sha256(plan_bytes).hexdigest() != 'b54107c9addc049b6759e059f325c09d0f54cb4ef1df3e6536c38a6b2fe7e321':
        raise ValueError('plan mismatch')
    plan=json.loads(plan_bytes)
    raw=(BOOK/'native-runs/source-01/original-snapshot.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != '2837758ade9124bb3118e5629b48a8d794a71f4b7845aa0d342732e4243271e7':
        raise ValueError('snapshot mismatch')
    catalog_raw=pathlib.Path(plan['source_catalog_path']).read_bytes()
    if hashlib.sha256(catalog_raw).hexdigest()!=plan['source_catalog_sha256']:
        raise ValueError('catalog mismatch')
    cat=json.loads(catalog_raw); pins=dict(plan['project_files']); project=pathlib.Path(plan['project_path'])
    def digest(name):
        out=hashlib.sha256((project/name).read_bytes()).hexdigest()
        if pins.get(name)!=out: raise ValueError('source pin mismatch '+name)
        return out
    writers=cat['writer_paths']
    if len(writers)!=11 or len(set(writers))!=11: raise ValueError('writer inventory mismatch')
    material=b'DEY-WRITERS-1\n'+b''.join(name.encode()+b'\0'+bytes.fromhex(digest(name)) for name in sorted(writers))
    p=v.ValuePolicy(digest(cat['document_path']),digest(cat['canonical_path']),digest(cat['catalog_path']),
        hashlib.sha256(material).hexdigest(),plan['source_bundle_sha256'],
        tuple(v.CatalogEntry(x['kind'],tuple(x['part_ids'])) for x in cat['catalog']),
        tuple(cat['presentation_part_ids']),tuple(digest(x) for x in cat['allowed_script_paths']),run_id=plan['run_id'])
    hist=json.loads((BOOK/'native-runs/source-01/result.json').read_text(encoding='utf8'))['initial_pose']
    return v.snapshot_from_wire(raw),p,RigidState(tuple(hist['position_m']),tuple(hist['orientation_xyzw']),0.)

def build(s,p,pose): return v._construct_values(s,p,pose,initial_monotonic_ns=0)

def summary(x):
    b=x.budget; d=x.budget_derivation
    return dict(policy_digest=d.source_pins_digest,geometry_identity=x.geometry_identity,scene_digest=x.scene.digest,
        numeric=str(b.numeric),asset=str(b.asset),obstacle=str(b.obstacle),source=b.source,
        additional=F(x.initial_state.errors.additional_margin_m).__str__(),scene_status=x.initial_scene_proof.status,
        corridors=[y.status for y in x.static_corridor_proofs],scene_objects=len(x.scene.objects))

if __name__ == '__main__' and sys.argv[1:]==['--baseline']:
    s,p,pose=fixture(); out=summary(build(s,p,pose))
    (OWN/'original-baseline.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print(json.dumps(out,sort_keys=True)); sys.exit(0)

class ExplicitBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot,cls.policy,cls.pose=fixture()
        cls.default=build(cls.snapshot,cls.policy,cls.pose)
        cls.original=json.loads((OWN/'original-baseline.json').read_text(encoding='utf8'))

    def test_default_reproduces_original_identity_and_all_terms(self):
        self.assertEqual(summary(self.default),self.original)
        self.assertEqual(self.default.budget_derivation.getter_endpoint_cap_m,F(0))

    def test_explicit_cap_is_separate_and_recertified(self):
        cap=F(1,100000)
        x=build(self.snapshot,replace(self.policy,getter_endpoint_cap_m=cap),self.pose)
        a=self.default
        self.assertEqual(x.budget.numeric,a.budget.numeric+cap)
        self.assertEqual(x.budget.asset,a.budget.asset)
        self.assertEqual(x.budget.obstacle,a.budget.obstacle)
        self.assertEqual(x.budget_derivation.getter_endpoint_cap_m,cap)
        self.assertNotEqual(x.geometry_identity,a.geometry_identity)
        self.assertNotEqual(x.scene.digest,a.scene.digest)
        self.assertNotEqual(x.budget_derivation.source_pins_digest,a.budget_derivation.source_pins_digest)
        self.assertGreaterEqual(F(x.initial_state.errors.additional_margin_m),x.budget.numeric+x.budget.asset+x.budget.obstacle)
        self.assertEqual(x.initial_scene_proof.status,'CLEAR')
        self.assertEqual(len(x.scene.objects),2)
        self.assertTrue(all(c.status=='CLEAR' for c in x.static_corridor_proofs))
        self.assertIn('endpoint',x.budget.source)

    def test_invalid_cap_refused_before_geometry(self):
        for value in (True,0,0.0,'0',F(-1),F(1,99),F(1,2**1024),F(2**1024)):
            with self.subTest(value=str(value)),self.assertRaises(v.ConstructionRefusal):
                build(self.snapshot,replace(self.policy,getter_endpoint_cap_m=value),self.pose)

    def test_geometrically_blocked_initial_state_still_refused(self):
        bad=RigidState((0.,0.,0.),self.pose.orientation_xyzw,0.)
        with self.assertRaises(v.ConstructionRefusal) as caught:
            build(self.snapshot,replace(self.policy,getter_endpoint_cap_m=F(1,100000)),bad)
        self.assertEqual(str(caught.exception), 'strict whole-body legal outside-blue initializer not certified')
        print('geometric refusal:', str(caught.exception))

if __name__=='__main__': unittest.main(verbosity=2)
