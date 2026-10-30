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

class GetterCommitmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot,cls.policy,cls.pose=fixture()
        cls.golden=json.loads((BASE/'explicit-getter-budget-construction/original-baseline.json').read_text(encoding='utf8'))

    def test_invalid_caps_rejected_by_pack_before_freeze_effect(self):
        for value in (False,0,0.0,None,True,'0',F(-1),F(1,99),F(1,2**1024),F(2**1024)):
            with self.subTest(value=repr(value)):
                p=replace(self.policy,getter_endpoint_cap_m=value)
                effects=[]
                with self.assertRaises(v.ConstructionRefusal):
                    commitment=v._digest(p)
                    effects.append(('freeze',commitment))
                self.assertEqual(effects,[])

    def test_zero_legacy_policy_hash_and_pack_work(self):
        p=replace(self.policy,getter_endpoint_cap_m=F(0))
        packed=v._pack(p)
        self.assertNotIn('getter_endpoint_cap_m',packed)
        self.assertEqual(v._digest(p),self.golden['policy_digest'])
        # Original dataclass packing counts all old field names plus child costs.
        old_names=('document_source_sha256','canonical_source_sha256','catalog_source_sha256',
                   'writer_inventory_sha256','source_bundle_sha256','catalog','presentation_part_ids',
                   'allowed_script_sha256','run_id','guard_m')
        expected=[128+sum(len(name)*6 for name in old_names)]
        for name in old_names: v._pack(getattr(p,name),expected)
        actual=[0]; v._pack(p,actual)
        self.assertEqual(actual,expected)
        x=v._construct_values(self.snapshot,p,self.pose,initial_monotonic_ns=0)
        self.assertEqual(x.geometry_identity,self.golden['geometry_identity'])
        self.assertEqual(x.scene.digest,self.golden['scene_digest'])
        self.assertEqual(x.budget.source,self.golden['source'])

    def test_nonzero_freeze_commitment_matches_new_construction(self):
        p=replace(self.policy,getter_endpoint_cap_m=F(1,100000))
        freeze_commitment=v._digest(p)
        packed=v._pack(p)
        self.assertEqual(packed['__getter_endpoint_cap_domain__'],'DEEPEYE-ENDPOINT-AFFINE-SET-GETTER-CAP-V1')
        self.assertEqual(packed['getter_endpoint_cap_m'],['r','1','100000'])
        self.assertNotEqual(freeze_commitment,v._digest(self.policy))
        self.assertNotEqual(freeze_commitment,v._digest(replace(p,getter_endpoint_cap_m=F(1,100001))))
        original=p
        x=v._construct_values(self.snapshot,p,self.pose,initial_monotonic_ns=0)
        self.assertIs(p,original)
        self.assertEqual(p.getter_endpoint_cap_m,F(1,100000))
        self.assertEqual(x.budget_derivation.source_pins_digest,freeze_commitment)
        self.assertIn(':'+freeze_commitment+':',x.budget.source)
        self.assertEqual(x.budget_derivation.getter_endpoint_cap_m,F(1,100000))
        self.assertEqual(x.budget.numeric,v.GUARD+F(1,100000))
        self.assertEqual(str(x.budget.asset),self.golden['asset'])
        self.assertEqual(str(x.budget.obstacle),self.golden['obstacle'])
        self.assertEqual(len(x.scene.objects),2)
        self.assertEqual(x.initial_scene_proof.status,'CLEAR')
        self.assertTrue(all(c.status=='CLEAR' for c in x.static_corridor_proofs))

if __name__=='__main__': unittest.main(verbosity=2)
