"""Independent solid-section checks; no full G06/CCD/asset acceptance claim.

Replacing the solver with tip/centre tests, whole-body projection, sampled
endpoints, or optimistic budget handling must break these tests. Closed-form
expectations below do not call production helpers.
"""
from dataclasses import FrozenInstanceError
from decimal import localcontext
from fractions import Fraction
import importlib
import math
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'simulation/authority/motion/gate_geometry.py'
MODULE = 'competition.deepeye.simulation.authority.motion.gate_geometry'


class GateGeometryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.is_file(), 'RED: gate geometry is not implemented')
        self.g = importlib.import_module(MODULE)

    def capsule(self, position=(0, 0, 15), axis=(0, 0, 1), h=.4, r=.12):
        return self.g.Capsule(position, axis, h, r)

    def gate(self):
        return self.g.Gate('front', 0, 0)

    def assert_contains(self, result, expected, slack=1e-14):
        self.assertEqual(result.status, 'bounded')
        self.assertLessEqual(result.lower_radius_m, expected+slack)
        self.assertGreaterEqual(result.upper_radius_m, expected-slack)
        self.assertLessEqual(result.upper_radius_m-result.lower_radius_m, 1.0001e-5)

    def test_candidate_capsule_is_104m_not_080m(self):
        cap = self.capsule()
        self.assertAlmostEqual(cap.total_length_m, 1.04)
        self.assertAlmostEqual(cap.pivot_bound_radius_m, .52)
        self.assertEqual(cap.envelope_status, 'candidate_requires_asset_containment_measurement')

    def test_pivot_radius_bound_rounds_outward(self):
        cap=self.capsule(h=.4,r=.3)
        self.assertGreaterEqual(Fraction(cap.pivot_bound_radius_m),Fraction(.4)+Fraction(.3))

    def test_exact_normal_section_is_radius(self):
        r = self.g.aperture_radius_bounds(self.capsule(), self.gate())
        self.assert_contains(r, .12)
        self.assertEqual(r.classification, 'clear')

    def test_axis_sign_and_scale_do_not_change_solid(self):
        results = [self.g.aperture_radius_bounds(self.capsule(axis=a), self.gate())
                   for a in [(0,0,1), (0,0,-1), (0,0,1000), (0,0,5e-324)]]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])
        self.assertEqual(results[0], results[3])

    def test_plane_support_requires_whole_body_to_cross(self):
        plane = self.gate().plane
        for z, expected_min, expected_max in [(15, -.52,.52),
                                              (15.4,-.12,.92),
                                              (15.6,.08,1.12)]:
            s = self.g.plane_support(self.capsule(position=(0,0,z)), plane)
            self.assertLessEqual(s.minimum.lower, expected_min+1e-14)
            self.assertGreaterEqual(s.minimum.upper, expected_min-1e-14)
            self.assertLessEqual(s.maximum.lower, expected_max+1e-14)
            self.assertGreaterEqual(s.maximum.upper, expected_max-1e-14)
        self.assertFalse(self.g.plane_support(self.capsule(position=(0,0,15.4)),plane).entirely_positive)
        self.assertTrue(self.g.plane_support(self.capsule(position=(0,0,15.6)),plane).entirely_positive)

    def test_arbitrary_plane_normal_is_normalized(self):
        cap = self.capsule(position=(0,0,0),axis=(0,0,2))
        s = self.g.plane_support(cap,self.g.Plane((0,0,0),(1,2,2)))
        expected = .4*2/3+.12
        self.assertLessEqual(s.maximum.lower,expected)
        self.assertGreaterEqual(s.maximum.upper,expected)

    def test_no_section_is_not_gate_passage(self):
        r = self.g.aperture_radius_bounds(self.capsule(position=(0,0,16)),self.gate())
        self.assertEqual(r.status,'empty')
        self.assertEqual(r.classification,'empty')
        self.assertIsNone(r.lower_radius_m)
        self.assertIsNone(r.upper_radius_m)

    def test_parallel_axis_has_finite_stadium_section(self):
        r = self.g.aperture_radius_bounds(self.capsule(axis=(1,0,0)),self.gate())
        self.assert_contains(r,.52)
        self.assertEqual(r.classification,'contact_or_outside')

    def test_parallel_offset_plane_section_has_smaller_radius(self):
        r = self.g.aperture_radius_bounds(self.capsule(position=(0,0,15.1),axis=(1,0,0)),self.gate())
        expected = .4+math.sqrt(.12**2-(15.1-15)**2)
        self.assert_contains(r,expected)

    def test_sphere_degenerate_segment(self):
        r = self.g.aperture_radius_bounds(self.capsule(position=(.02,0,15.06),h=0),self.gate())
        expected = .02+math.sqrt(.12**2-(15.06-15)**2)
        self.assert_contains(r,expected)

    def test_five_degree_section_is_not_whole_projection(self):
        angle=math.radians(5)
        r=self.g.aperture_radius_bounds(self.capsule(axis=(math.sin(angle),0,math.cos(angle))),self.gate())
        self.assert_contains(r,.12/math.cos(angle))
        self.assertEqual(r.classification,'clear')
        self.assertGreater(.4*math.sin(angle)+.12,.15)

    def test_finite_cap_cannot_use_infinite_cylinder(self):
        r=self.g.aperture_radius_bounds(self.capsule(position=(0,0,15.5)),self.gate())
        self.assert_contains(r,math.sqrt(.12**2-.1**2))
        self.assertLess(r.upper_radius_m,.07)

    def test_eccentric_section_catches_centre_only_false_clear(self):
        r=self.g.aperture_radius_bounds(self.capsule(position=(.04,0,15)),self.gate())
        self.assert_contains(r,.16)
        self.assertEqual(r.classification,'contact_or_outside')
        self.assertLess(.04,.15)

    def test_circle_tangency_never_clear(self):
        r=self.g.aperture_radius_bounds(self.capsule(position=(.03,0,15)),self.gate())
        self.assertNotEqual(r.classification,'clear')

    def test_tiny_positive_and_negative_clearance(self):
        for x, expected in [(.03-1e-7,'clear'),(.03+1e-7,'contact_or_outside')]:
            with self.subTest(x=x):
                r=self.g.aperture_radius_bounds(self.capsule(position=(x,0,15)),self.gate())
                self.assertEqual(r.classification,expected)

    def test_plane_near_tangency_is_not_falsely_empty(self):
        # Gate plane at origin on a custom Plane is not an aperture API. Use
        # right face so the capsule's small normal offset is stored as X.
        gate=self.g.Gate('right',0,0)
        touching=15+.52
        for x in (math.nextafter(touching,-math.inf),touching):
            result=self.g.aperture_radius_bounds(self.capsule(position=(x,0,0),axis=(1,0,0)),gate)
            # Binary64 15+.52 can lie just outside the exact encoded capsule;
            # the explicit 1pm separation guard must retain uncertainty.
            self.assertNotEqual(result.status,'empty')

    def test_solver_budget_exhaustion_cannot_clear(self):
        angle=math.radians(5)
        r=self.g.aperture_radius_bounds(self.capsule(axis=(math.sin(angle),0,math.cos(angle))),self.gate(),max_intervals=1)
        self.assertEqual(r.status,'unknown')
        self.assertEqual(r.classification,'unknown')
        self.assertIn('budget',r.reason)

    def test_tighter_error_bound_cannot_widen_interval(self):
        angle=math.radians(5)
        cap=self.capsule(position=(.01,.015,15),axis=(math.sin(angle),0,math.cos(angle)))
        a=self.g.aperture_radius_bounds(cap,self.gate(),tolerance_m=1e-4)
        b=self.g.aperture_radius_bounds(cap,self.gate(),tolerance_m=1e-6)
        self.assertEqual(a.status,'bounded')
        self.assertEqual(b.status,'bounded')
        self.assertGreaterEqual(b.lower_radius_m,a.lower_radius_m)
        self.assertLessEqual(b.upper_radius_m,a.upper_radius_m)

    def test_ambient_decimal_context_cannot_corrupt_bounds(self):
        angle=math.radians(5)
        cap=self.capsule(position=(.01,.015,15),axis=(math.sin(angle),0,math.cos(angle)))
        expected=self.g.aperture_radius_bounds(cap,self.gate())
        support=self.g.plane_support(cap,self.gate().plane)
        with localcontext() as ambient:
            ambient.prec=6
            self.assertEqual(self.g.aperture_radius_bounds(cap,self.gate()),expected)
            self.assertEqual(self.g.plane_support(cap,self.gate().plane),support)

    def test_six_face_mapping_and_all_36_directed_pairs(self):
        expected={
            'top':((1.25,15,-2.5),(0,1,0),'+Y'),
            'bottom':((1.25,-15,-2.5),(0,-1,0),'-Y'),
            'front':((1.25,-2.5,15),(0,0,1),'+Z'),
            'back':((1.25,-2.5,-15),(0,0,-1),'-Z'),
            'right':((15,-2.5,1.25),(1,0,0),'+X'),
            'left':((-15,-2.5,1.25),(-1,0,0),'-X'),
        }
        for enter,(center,normal,abi) in expected.items():
            blue=self.g.Gate(enter,1.25,-2.5)
            self.assertEqual(blue.center_m,center)
            self.assertEqual(blue.normal,normal)
            self.assertEqual(blue.abi_face,abi)
            self.assertEqual(blue.radius_m,.15)
            for leave,(exit_center,exit_normal,_) in expected.items():
                with self.subTest(enter=enter,leave=leave):
                    red=self.g.Gate(leave,2.5,1.25)
                    self.g.validate_gate_pair(blue,red)
                    for gate in (blue,red):
                        result=self.g.aperture_radius_bounds(self.capsule(position=gate.center_m,axis=gate.normal),gate)
                        self.assert_contains(result,.12)

    def test_same_face_circle_overlap_is_rejected_not_auto_moved(self):
        blue=self.g.Gate('front',0,0)
        with self.assertRaises(ValueError):
            self.g.validate_gate_pair(blue,self.g.Gate('front',.29,0))
        self.g.validate_gate_pair(blue,self.g.Gate('front',.30,0))
        self.assertEqual(blue.center_m,(0,0,15))

    def test_values_are_immutable_and_input_lists_are_copied(self):
        pos=[0,0,15]
        cap=self.capsule(position=pos)
        pos[0]=99
        self.assertEqual(cap.position_m,(0,0,15))
        with self.assertRaises(FrozenInstanceError):
            cap.radius_m=.2
        with self.assertRaises(FrozenInstanceError):
            self.gate().u=1

    def test_bad_vectors_shapes_and_numbers_are_rejected(self):
        for value in [float('nan'),float('inf'),-float('inf'),True,'0',1001]:
            with self.subTest(value=repr(value)):
                with self.assertRaises((ValueError,TypeError)):
                    self.capsule(position=(value,0,0))
        for axis in [(0,0,0),(1,2),(1,2,3,4),(True,0,1)]:
            with self.assertRaises((ValueError,TypeError)):
                self.capsule(axis=axis)
        for h,r in [(-1,.12),(.4,0),(.4,-.12),(True,.12),(.4,True),(11,.12),(.4,11)]:
            with self.assertRaises((ValueError,TypeError)):
                self.capsule(h=h,r=r)
        with self.assertRaises((ValueError,TypeError)):
            self.g.Plane((0,0,0),(0,0,0))

    def test_invalid_gates_and_solver_limits_are_rejected(self):
        for face,u,v in [('TOP',0,0),('front',14.851,0),('front',True,0),('front',0,float('nan'))]:
            with self.assertRaises((ValueError,TypeError)):
                self.g.Gate(face,u,v)
        for tol in [0,-1,True,float('nan'),.00010001]:
            with self.assertRaises((ValueError,TypeError)):
                self.g.aperture_radius_bounds(self.capsule(),self.gate(),tolerance_m=tol)
        for budget in [0,-1,True,1.1,1000001]:
            with self.assertRaises((ValueError,TypeError)):
                self.g.aperture_radius_bounds(self.capsule(),self.gate(),max_intervals=budget)


if __name__=='__main__':
    unittest.main()
