"""Whole-interval workspace proofs; fixture bodies are not B asset acceptance."""
import importlib
import math
import unittest
from dataclasses import replace

from competition.deepeye.simulation.authority.motion import certified_path as cp
from competition.deepeye.simulation.authority.motion import gate_geometry as g
from competition.deepeye.simulation.authority.motion import gate_clearance as gc
from competition.deepeye.simulation.authority.motion.kinematics import RigidState

try:
    w=importlib.import_module('competition.deepeye.simulation.authority.motion.workspace_boundaries')
except ModuleNotFoundError as exc:
    if exc.name!='competition.deepeye.simulation.authority.motion.workspace_boundaries':raise
    w=None


class WorkspaceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(w,'workspace_boundaries implementation missing')
        self.body=w.Envelope(.4,.12,.52,'explicit mathematical capsule fixture',False)
        self.layout=w.Layout(g.Gate('front',0,0),g.Gate('back',0,0))
        self.errors=gc.ErrorBounds(0.,0.,0.)

    def prepare(self,position=(0,0,0),q=(0,0,0,1),yaw=0,*,body=None,layout=None,errors=None,dt=10_000_000):
        path=cp.CanonicalPath(RigidState(position,q,.25),'fast_9600',20,yaw,0,dt,
             inherited_errors=errors or self.errors,error_budget_reference='exact fixture assumptions; not measured')
        return w.prepare(path,layout or self.layout,body or self.body,start_monotonic_ns=0,
                         deadline_monotonic_ns=dt+1,hard_stop=False)

    def test_deep_interior_turn_is_safe_without_gate_angle_check(self):
        prepared=self.prepare(yaw=7000)
        for i in range(len(prepared.plan.slices)):
            proof=w.check_slice(prepared,i,'exit')
            self.assertEqual('SAFE',proof.status)
            self.assertTrue(all(f.method=='STRICT_INSIDE' for f in proof.faces))
            self.assertFalse(proof.motion_grant)

    def test_active_plane_can_be_outside_but_closed_wrong_face_cannot(self):
        outside=self.prepare((0,0,15.6),(0,1,0,0))
        self.assertEqual('SAFE',w.check_slice(outside,0,'entry').status)
        wrong=self.prepare((15.6,0,0),(0,0,0,1))
        self.assertEqual('UNKNOWN',w.check_slice(wrong,0,'entry').status)

    def test_complete_volume_and_tail_side_witnesses(self):
        prepared=self.prepare((0,0,15.2),(0,1,0,0))
        sides=w.point_sides(prepared.plan.slices[0].start,self.body)
        front=next(s for s in sides if s.face=='front')
        self.assertFalse(front.inside);self.assertFalse(front.outside)
        inner=self.prepare((0,0,14.4),(0,1,0,0))
        self.assertTrue(all(s.inside for s in w.point_sides(inner.plan.end,self.body)))

    def test_first_touch_of_plane_inside_hole_is_not_rim_violation(self):
        prepared=self.prepare((0,0,15.52),(0,1,0,0),body=replace(self.body,exact_fixture=True))
        proof=w.check_slice(prepared,0,'entry')
        self.assertEqual('SAFE',proof.status)
        self.assertEqual('APERTURE',next(f for f in proof.faces if f.face=='front').method)

    def test_same_face_tangent_layout_has_one_role_hole_not_union(self):
        layout=w.Layout(g.Gate('front',-.15,0),g.Gate('front',.15,0))
        prepared=self.prepare((.15,0,15.),(0,1,0,0),layout=layout)
        self.assertEqual('UNKNOWN',w.check_slice(prepared,0,'entry').status)
        outward=self.prepare((.15,0,15.),(0,0,0,1),layout=layout)
        self.assertEqual('SAFE',w.check_slice(outward,0,'exit').status)
        with self.assertRaises(ValueError):w.Layout(g.Gate('front',0,0),g.Gate('front',.3-1e-10,0))

    def test_wrong_crossing_direction_and_wrong_gate_are_not_clear(self):
        self.assertEqual('UNKNOWN',w.check_slice(self.prepare((0,0,15.),(0,0,0,1)),0,'entry').status)
        self.assertEqual('UNKNOWN',w.check_slice(self.prepare((.2,0,15.),(0,1,0,0)),0,'entry').status)

    def test_exit_role_cannot_use_string_alias_to_select_blue_entry_aperture(self):
        class RoleAlias(str):
            __hash__=str.__hash__
            def __eq__(self,other):return other in ('entry','exit')
        prepared=self.prepare((0,0,15.),(0,1,0,0))
        self.assertEqual('SAFE',w.check_slice(prepared,0,'entry').status)
        self.assertEqual('UNKNOWN',w.check_slice(prepared,0,'exit').status)
        with self.assertRaises(ValueError):w.check_slice(prepared,0,RoleAlias('exit'))

    def test_unknown_outer_envelope_differs_from_exact_fixture_wall_witness(self):
        prepared=self.prepare((15.,0,0))
        self.assertEqual('UNKNOWN',w.check_slice(prepared,0,'exit').status)
        exact=self.prepare((15.,0,0),body=replace(self.body,exact_fixture=True))
        self.assertEqual('VIOLATION_PROVED',w.check_slice(exact,0,'exit').status)

    def test_exact_aligned_rim_tangency_is_contact_not_plane_touch(self):
        q=(0,1,0,0);p=(.03,0,15.)
        self.assertEqual('UNKNOWN',w.check_slice(self.prepare(p,q),0,'entry').status)
        exact=self.prepare(p,q,body=replace(self.body,exact_fixture=True))
        self.assertEqual('VIOLATION_PROVED',w.check_slice(exact,0,'entry').status)

    def test_gate_budget_zero_only_blocks_potential_intersection(self):
        self.assertEqual('UNKNOWN',w.check_slice(self.prepare((0,0,15.),(0,1,0,0)),0,'entry',max_gate_checks=0).status)
        self.assertEqual('SAFE',w.check_slice(self.prepare(),0,'exit',max_gate_checks=0).status)

    def test_external_slice_bounds_and_noncanonical_paths_are_not_accepted(self):
        with self.assertRaises(TypeError):w.prepare(object(),self.layout,self.body,
             start_monotonic_ns=0,deadline_monotonic_ns=11,hard_stop=False)
        with self.assertRaises(TypeError):w.check_slice(object(),0,'entry')

    def test_required_body_error_and_larger_pivot_margins_remain_explicit(self):
        base=w.check_slice(self.prepare((0,0,15.),(0,1,0,0),yaw=1),0,'entry')
        larger=w.check_slice(self.prepare((0,0,15.),(0,1,0,0),yaw=1,body=replace(self.body,pivot_radius_m=1.)),0,'entry')
        self.assertGreaterEqual(larger.rho_m,base.rho_m)
        self.assertGreaterEqual(base.rho_m,.0005)
        unknown=self.prepare((0,0,15.),(0,1,0,0),errors=gc.ErrorBounds(.04,0.,0.))
        self.assertEqual('UNKNOWN',w.check_slice(unknown,0,'entry').status)

    def test_endpoint_inside_but_legal_curved_midpoint_outside_is_not_safe(self):
        # Closed-form maximum offset+R*sin(beta)+h*cos(beta)+r, endpoints below0.
        from competition.deepeye.integration.motion import validate
        k=validate('fast_9600',20,7000,0).curvature_yaw_per_m
        dt=6_548_000;angle=k*.25*(dt/1e9);beta=math.atan2(1/k,.4)-angle/2
        q=(0,math.sin(beta/2),0,math.cos(beta/2))
        amplitude=math.hypot(1/k,.4)
        peak=amplitude*(1-math.cos(angle/2))
        z=15.-.12-.4*math.cos(beta)-peak/2
        prepared=self.prepare((0,0,z),q,yaw=7000,dt=dt)
        start=cp.CanonicalPath(RigidState((0,0,z),q,.25),'fast_9600',20,7000,0,dt,
            inherited_errors=self.errors,error_budget_reference='exact bulge fixture')
        def nominal(t):
            sample=start.sample(t);body=g.Capsule(sample.state.position_m,sample.axis)
            return g.plane_support(body,g.Gate('front',0,0).plane).maximum
        self.assertLess(nominal(0).upper,0);self.assertLess(nominal(dt).upper,0)
        self.assertGreater(nominal(dt//2).lower,0)
        self.assertNotEqual('SAFE',w.check_slice(prepared,0,'exit').status)


if __name__=='__main__':unittest.main()
