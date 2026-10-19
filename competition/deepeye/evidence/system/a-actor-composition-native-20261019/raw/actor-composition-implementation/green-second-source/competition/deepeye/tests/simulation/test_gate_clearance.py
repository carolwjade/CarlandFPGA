"""Sufficient gate certificates; these tests do not grant motion or G06 acceptance."""
from dataclasses import FrozenInstanceError
from decimal import localcontext, ROUND_DOWN
import importlib
import math
import unittest

from competition.deepeye.simulation.authority.motion.gate_geometry import Capsule, Gate

try:
    gc = importlib.import_module('competition.deepeye.simulation.authority.motion.gate_clearance')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.simulation.authority.motion.gate_clearance':
        raise
    gc = None


class GateClearanceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gc, 'gate_clearance implementation is missing')
        self.gate = Gate('front', 0., 0.)
        self.errors = gc.ErrorBounds(position_error_m=0., angle_error_rad=0., additional_margin_m=0.)
        self.body = Capsule((0., 0., 15.), (0., 0., 1.))

    def section(self, body=None, **kwargs):
        return gc.section_clearance(body or self.body, self.gate,
                                    direction=kwargs.pop('direction', 1),
                                    errors=kwargs.pop('errors', self.errors), **kwargs)

    def sweep(self, body=None, end=(0., 0., 15.001), length=.001,
              curvature=.5, theta=.0005, **kwargs):
        bounds = gc.SliceBounds(end_position_m=end, arc_length_upper_m=length,
                               curvature_upper_per_m=curvature, rotation_upper_rad=theta)
        return gc.sweep_clearance(body or self.body, self.gate, bounds=bounds,
                                  direction=kwargs.pop('direction', 1),
                                  errors=kwargs.pop('errors', self.errors), **kwargs)

    def test_normal_section_is_strict_clear_but_not_motion(self):
        result = self.section()
        self.assertEqual(result.status, 'CLEAR_SECTION')
        self.assertTrue(result.nonempty_proved)
        self.assertTrue(result.angle_proved)
        self.assertFalse(result.motion_grant)
        self.assertGreaterEqual(result.radial_upper_m, .12)
        self.assertLess(result.radial_upper_m, .120000001)
        self.assertTrue(result.assumptions)
        self.assertEqual(result.inputs.capsule, self.body)

    def test_sphere_degeneracy_and_short_capsule(self):
        for half in (0., 1e-12, .01):
            result = self.section(Capsule((0., 0., 15.), (0., 0., 1.), half_segment_m=half))
            self.assertEqual(result.status, 'CLEAR_SECTION')

    def test_five_degree_ellipse_is_not_full_body_projection(self):
        angle = math.radians(4.99)
        body = Capsule((0., 0., 15.), (math.sin(angle), 0., math.cos(angle)))
        result = self.section(body)
        self.assertEqual(result.status, 'CLEAR_SECTION')
        self.assertAlmostEqual(result.radial_upper_m, .12/math.cos(angle), places=12)
        self.assertGreater(.4*math.sin(angle)+.12, .15)

    def test_finite_cap_may_be_unknown_even_when_actual_section_fits(self):
        body = Capsule((.07, 0., 15.5), (0., 0., 1.))
        self.assertLess(.07+math.sqrt(.12**2-.1**2), .15)
        self.assertEqual(self.section(body).status, 'UNKNOWN')

    def test_parallel_and_near_parallel_fail_closed(self):
        for z in (0., 1e-300, -1e-300):
            result = self.section(Capsule((0., 0., 15.), (1., 0., z)))
            self.assertEqual(result.status, 'UNKNOWN')
            self.assertFalse(result.angle_proved)

    def test_reverse_axis_requires_reverse_direction(self):
        body = Capsule((0., 0., 15.), (0., 0., -1.))
        self.assertEqual(self.section(body).status, 'UNKNOWN')
        self.assertEqual(self.section(body, direction=-1).status, 'CLEAR_SECTION')

    def test_all_six_faces_both_directions(self):
        for face in ('front', 'back', 'left', 'right', 'top', 'bottom'):
            gate = Gate(face, 2., -1.)
            for direction in (-1, 1):
                body = Capsule(gate.center_m, tuple(direction*x for x in gate.normal))
                result = gc.section_clearance(body, gate, direction=direction, errors=self.errors)
                self.assertEqual(result.status, 'CLEAR_SECTION')

    def test_contact_and_near_contact_do_not_clear(self):
        for radius in (.15, math.nextafter(.15, 0.), .1500001):
            body = Capsule((0., 0., 15.), (0., 0., 1.), radius_m=radius)
            self.assertEqual(self.section(body).status, 'UNKNOWN')
        self.assertEqual(self.section(Capsule((0., 0., 15.), (0., 0., 1.), radius_m=.1499999)).status,
                         'CLEAR_SECTION')

    def test_plane_tangency_and_guard_are_not_empty_or_clear(self):
        for shift in (0., 1e-13, -1e-13):
            body = Capsule((0., 0., 15.52+shift), (0., 0., 1.))
            result = self.section(body)
            self.assertEqual(result.status, 'UNKNOWN')
            self.assertFalse(result.nonempty_proved)
            self.assertFalse(result.plane_separated)

    def test_empty_is_never_arrival(self):
        result = self.section(Capsule((0., 0., 17.), (0., 0., 1.)))
        self.assertEqual(result.status, 'EMPTY')
        self.assertFalse(result.nonempty_proved)
        self.assertFalse(result.motion_grant)
        self.assertFalse(hasattr(result, 'arrived'))

    def test_errors_expand_radius_and_support(self):
        body = Capsule((.029, 0., 15.), (0., 0., 1.))
        self.assertEqual(self.section(body).status, 'CLEAR_SECTION')
        for errors in (gc.ErrorBounds(.002, 0., 0.), gc.ErrorBounds(0., 0., .002)):
            self.assertEqual(self.section(body, errors=errors).status, 'UNKNOWN')
        near_plane = Capsule((0., 0., 15.521), (0., 0., 1.))
        self.assertEqual(self.section(near_plane).status, 'EMPTY')
        self.assertEqual(self.section(near_plane, errors=gc.ErrorBounds(.002, 0., 0.)).status, 'UNKNOWN')

    def test_angular_uncertainty_consumes_angle_budget(self):
        a = math.radians(4.9)
        body = Capsule((0., 0., 15.), (math.sin(a), 0., math.cos(a)))
        self.assertEqual(self.section(body).status, 'CLEAR_SECTION')
        result = self.section(body, errors=gc.ErrorBounds(0., math.radians(.2), 0.))
        self.assertEqual(result.status, 'UNKNOWN')
        self.assertFalse(result.angle_proved)

    def test_angle_boundary_is_conservative(self):
        for degrees, expected in ((4.999999, 'CLEAR_SECTION'), (5.000001, 'UNKNOWN')):
            a = math.radians(degrees)
            self.assertEqual(self.section(Capsule((0., 0., 15.), (math.sin(a), 0., math.cos(a)))).status,
                             expected)
        self.assertEqual(self.section(errors=gc.ErrorBounds(0., math.radians(5.1), 0.)).status, 'UNKNOWN')

    def test_sweep_clearance_contains_required_inflation(self):
        result = self.sweep(end=(0., 0., 15.0016), length=.0017, theta=.00085)
        expected = .0005 + .5*.0017**2/8
        self.assertEqual(result.status, 'SAFE_IF_INTERSECTING')
        self.assertGreaterEqual(result.inflation_upper_m, expected)
        self.assertLess(result.inflation_upper_m, expected+1e-12)
        self.assertFalse(result.nonempty_proved)
        self.assertFalse(result.motion_grant)

    def test_curved_centreline_can_scrape_between_clear_end_sections(self):
        # p(t)=(.0294+.004*t*(1-t),0,15.3+.02*t), fixed +Z axis.
        # Speed in parameter t exceeds .02, so L < .025 and curvature
        # <= .008/.02**2 = 20 < 40. At t=.5 the central cylinder cuts the
        # plane and its radial extent is .0304+.12 > the .15 m aperture.
        # This generic geometry curve is not a permitted kinematics command.
        start = Capsule((.0294, 0., 15.3), (0., 0., 1.))
        end = Capsule((.0294, 0., 15.32), (0., 0., 1.))
        self.assertEqual(self.section(start).status, 'CLEAR_SECTION')
        self.assertEqual(self.section(end).status, 'CLEAR_SECTION')
        self.assertLess(15.31-15., .4)
        self.assertGreater(.0294+.004/4+.12, .15)
        bounded = self.sweep(start, end=end.position_m, length=.025,
                             curvature=40., theta=0.)
        self.assertEqual(bounded.status, 'UNKNOWN')
        # The primitive checks explicit assumptions; a falsely supplied zero
        # curvature can clear and proves why a path-binding layer is required.
        false_assumption = self.sweep(start, end=end.position_m, length=.025,
                                      curvature=0., theta=0.)
        self.assertEqual(false_assumption.status, 'SAFE_IF_INTERSECTING')
        self.assertFalse(false_assumption.motion_grant)

    def test_rotation_linear_bound_is_not_only_minimum_margin(self):
        body = Capsule((0., 0., 15.), (0., 0., 1.), half_segment_m=2.)
        result = self.sweep(body, theta=.0008)
        self.assertGreaterEqual(result.inflation_upper_m, 2.12*.0008+.5*.001**2/8)

    def test_sweep_errors_are_explicit_and_additive(self):
        result = self.sweep(errors=gc.ErrorBounds(.001, .0001, .002))
        self.assertGreaterEqual(result.inflation_upper_m, .0005+.5*.001**2/8+.001+.52*.0001+.002)

    def test_slice_larger_than_point_zero_five_degree_is_unknown(self):
        self.assertEqual(self.sweep(theta=math.radians(.050001)).status, 'UNKNOWN')
        self.assertEqual(self.sweep(theta=math.radians(.049999)).status, 'SAFE_IF_INTERSECTING')

    def test_endpoint_clear_mid_rotation_angle_violation_is_rejected(self):
        # Both endpoint axes are 4.99 deg. The path first rotates +.02 deg,
        # then -.02 deg: total rotation .04 deg, so the middle violates 5 deg.
        a = math.radians(4.99)
        body = Capsule((0., 0., 15.), (math.sin(a), 0., math.cos(a)))
        self.assertEqual(self.section(body).status, 'CLEAR_SECTION')
        result = self.sweep(body, theta=math.radians(.04))
        self.assertEqual(result.status, 'UNKNOWN')
        self.assertFalse(result.angle_proved)

    def test_clear_endpoints_do_not_bypass_rotation_radial_cover(self):
        # Axis tilt -0.0004 rad at mid-time, back to zero at the end.
        # Centre is .3m from the plane; the middle ellipse shifts into rim.
        # This adversarial geometry fixture need not be an admissible drive command.
        body = Capsule((.02995, 0., 15.3), (0., 0., 1.))
        self.assertEqual(self.section(body).status, 'CLEAR_SECTION')
        self.assertGreater(.02995+.3*math.tan(.0004)+.12/math.cos(.0004), .15)
        result = self.sweep(body, end=body.position_m, length=0., curvature=0., theta=.0008)
        self.assertEqual(result.status, 'UNKNOWN')

    def test_sweep_uses_both_axis_plane_intersections(self):
        result = self.sweep(end=(.04, 0., 15.), length=.04, curvature=0., theta=0.)
        self.assertEqual(result.status, 'UNKNOWN')
        self.assertGreaterEqual(result.radial_upper_m, .1605)

    def test_sweep_empty_is_conditional_and_never_arrival(self):
        body = Capsule((0., 0., 17.), (0., 0., 1.))
        result = self.sweep(body, end=(0., 0., 17.0009))
        self.assertTrue(result.plane_separated)
        self.assertEqual(result.status, 'SAFE_IF_INTERSECTING')
        self.assertFalse(result.motion_grant)
        self.assertFalse(result.nonempty_proved)

    def test_reverse_sweep_direction_and_parallel(self):
        body = Capsule((0., 0., 15.), (0., 0., -1.))
        self.assertEqual(self.sweep(body).status, 'UNKNOWN')
        self.assertEqual(self.sweep(body, direction=-1).status, 'SAFE_IF_INTERSECTING')
        body = Capsule((0., 0., 15.), (1., 0., 0.))
        self.assertEqual(self.sweep(body).status, 'UNKNOWN')

    def test_arc_length_cannot_be_smaller_than_chord(self):
        with self.assertRaises(ValueError):
            self.sweep(end=(0., 0., 15.01), length=.001)
        with self.assertRaises(ValueError):
            self.sweep(end=(0., 0., 15.001), length=0.)
        self.assertEqual(self.sweep(end=self.body.position_m, length=0., theta=0., curvature=0.).status,
                         'SAFE_IF_INTERSECTING')

    def test_frozen_inputs_outputs_and_copied_endpoint(self):
        end = [0., 0., 15.0009]
        bounds = gc.SliceBounds(end, .001, .5, .0005)
        end[0] = 12.
        self.assertEqual(bounds.end_position_m, (0., 0., 15.0009))
        with self.assertRaises(FrozenInstanceError):
            self.errors.additional_margin_m = 0.1
        result = self.section()
        with self.assertRaises(FrozenInstanceError):
            result.motion_grant = True

    def test_required_bounds_have_no_default_zero(self):
        with self.assertRaises(TypeError):
            gc.ErrorBounds()
        with self.assertRaises(TypeError):
            gc.section_clearance(self.body, self.gate, direction=1)
        with self.assertRaises(TypeError):
            gc.sweep_clearance(self.body, self.gate, direction=1, errors=self.errors)

    def test_illegal_numbers_in_every_error_or_slice_bound(self):
        for bad in (True, False, float('nan'), float('inf'), -1., '0'):
            for i in range(3):
                values = [0., 0., 0.]
                values[i] = bad
                with self.assertRaises((TypeError, ValueError)):
                    gc.ErrorBounds(*values)
            for i in range(3):
                values = [.001, .5, .0005]
                values[i] = bad
                with self.assertRaises((TypeError, ValueError)):
                    gc.SliceBounds((0., 0., 15.), *values)
        for direction in (True, False, 1., 0, 2, '1'):
            with self.assertRaises((TypeError, ValueError)):
                self.section(direction=direction)
        with self.assertRaises((TypeError, ValueError)):
            gc.SliceBounds((True, 0., 15.), .001, .5, .0005)

    def test_pose_and_direction_are_not_cached(self):
        self.assertEqual(self.section().status, 'CLEAR_SECTION')
        self.assertEqual(self.section(Capsule((.05, 0., 15.), (0., 0., 1.))).status, 'UNKNOWN')
        self.assertEqual(self.section(direction=-1).status, 'UNKNOWN')
        self.assertEqual(self.section().status, 'CLEAR_SECTION')

    def test_ambient_decimal_context_cannot_change_certificates(self):
        expected_section = self.section(errors=gc.ErrorBounds(.001, .00017, .00001))
        expected_sweep = self.sweep(errors=gc.ErrorBounds(.001, .00019, .00001))
        with localcontext() as context:
            context.prec = 3
            context.rounding = ROUND_DOWN
            gc._cos_limit_upper.cache_clear()
            self.assertEqual(self.section(errors=gc.ErrorBounds(.001, .00017, .00001)), expected_section)
            self.assertEqual(self.sweep(errors=gc.ErrorBounds(.001, .00019, .00001)), expected_sweep)


if __name__ == '__main__':
    unittest.main()
