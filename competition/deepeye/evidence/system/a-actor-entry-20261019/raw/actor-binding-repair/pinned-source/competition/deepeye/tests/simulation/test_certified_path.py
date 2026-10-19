"""Canonical numeric path proofs; not authority, watchdog or engine acceptance."""
from dataclasses import FrozenInstanceError, asdict
from decimal import Context, Inexact, Rounded, ROUND_UP, localcontext, Decimal
from fractions import Fraction as F
import importlib
import math
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from competition.deepeye.integration import motion
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
from competition.deepeye.simulation.authority.motion.gate_clearance import ErrorBounds, sweep_clearance
from competition.deepeye.simulation.authority.motion.gate_geometry import Capsule, Gate

try:
    cp = importlib.import_module('competition.deepeye.simulation.authority.motion.certified_path')
except ModuleNotFoundError as exc:
    if exc.name != 'competition.deepeye.simulation.authority.motion.certified_path':
        raise
    cp = None


class CertifiedPathTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(cp, 'certified_path implementation is missing')
        self.zero = ErrorBounds(0., 0., 0.)  # Exact mathematical fixture, not measured hardware.

    def path(self, *, speed=.25, pos=(0., 0., 15.), q=(0., 0., 0., 1.),
             profile='fast_9600', code=20, yaw=0, pitch=0, dt=10_000_000,
             errors=None):
        return cp.CanonicalPath(RigidState(pos, q, speed), profile, code, yaw, pitch, dt,
                                inherited_errors=errors or self.zero,
                                error_budget_reference='exact test fixture')

    def plan(self, path, **kwargs):
        return path.plan(start_monotonic_ns=kwargs.pop('start', 100),
                         deadline_monotonic_ns=kwargs.pop('deadline', 20_000_101),
                         hard_stop=kwargs.pop('stop', False), **kwargs)

    def test_exact_straight_speed_and_endpoint(self):
        path = self.path()
        self.assertEqual(path.distance_speed(10_000_000), (F(1, 400), F(1, 4)))
        result = self.plan(path)
        self.assertEqual(result.covered_ns, 10_000_000)
        self.assertEqual(len(result.slices), 1)
        item = result.slices[0]
        self.assertEqual(item.exact_arc_length_m, F(1, 400))
        self.assertGreaterEqual(F(item.path_arc_upper_m), F(1, 400))
        self.assertEqual(item.start.axis, (0., 0., 1.))
        self.assertLess(abs(item.end.state.position_m[2]-15.0025), 1e-14)
        self.assertFalse(result.motion_grant)
        self.assertFalse(hasattr(result, 'arrived'))
        self.assertTrue(result.assumptions)

    def test_one_ns_acceleration_is_not_erased(self):
        path = self.path(speed=0., dt=1, pos=(0., 0., 0.))
        self.assertEqual(path.distance_speed(1), (F(1, 8*10**18), F(1, 4*10**9)))
        item = self.plan(path).slices[0]
        self.assertGreater(item.end.state.position_m[2], 0.)
        self.assertGreaterEqual(F(item.path_arc_upper_m), item.exact_arc_length_m)

    def test_target_floor_and_ceil_preserve_exact_integral(self):
        path = self.path(speed=.001, code=0)
        result = self.plan(path)
        self.assertEqual([s.end.elapsed_ns for s in result.slices], [4_000_000, 4_000_001, 10_000_000])
        self.assertEqual(sum((s.exact_arc_length_m for s in result.slices), F(0)), 2*F(.001)**2)
        self.assertEqual(result.end.state.speed_m_s, 0.)
        self.assertEqual(path.distance_speed(4_000_000)[1], F(.001)-F(1, 1000))

    def test_target_before_first_ns_and_subnormal_braking(self):
        near = self.path(speed=math.nextafter(.25, 0.))
        self.assertEqual(self.plan(near).slices[0].end.elapsed_ns, 1)
        tiny = self.path(speed=math.ulp(0.), code=0, dt=1, pos=(0., 0., 0.))
        distance, speed = tiny.distance_speed(1)
        self.assertGreater(distance, 0)
        self.assertEqual(speed, 0)
        item = self.plan(tiny).slices[0]
        self.assertGreater(item.path_arc_upper_m, 0.)
        self.assertGreaterEqual(F(item.path_arc_upper_m), distance)
        self.assertGreater(item.end.numerical_position_error_m, 0.)

    def test_still_path_and_hard_stop_are_distinct(self):
        still = self.plan(self.path(speed=0., code=0))
        self.assertEqual(still.covered_ns, 10_000_000)
        self.assertEqual(still.slices[0].path_arc_upper_m, 0.)
        moving = self.path(code=0)
        stopped = self.plan(moving, stop=True)
        self.assertEqual(stopped.covered_ns, 0)
        self.assertEqual(stopped.slices, ())
        self.assertIs(stopped.end.state, moving.provenance.start_state)
        self.assertEqual(stopped.end.state.speed_m_s, .25)  # runtime STOP transition is separate
        self.assertEqual(stopped.reason, 'HARD_STOP')
        self.assertGreater(self.plan(moving).covered_ns, 0)

    def test_deadline_expires_on_equality_and_end_is_strictly_before_it(self):
        path = self.path()
        for remaining, covered in ((-1, 0), (0, 0), (1, 0), (2, 1), (6, 5),
                                   (5_000_001, 5_000_000), (20_000_001, 10_000_000)):
            result = self.plan(path, start=100, deadline=100+remaining)
            self.assertEqual(result.covered_ns, covered)
            if covered:
                self.assertLess(result.start_monotonic_ns+covered, result.deadline_monotonic_ns)
            else:
                self.assertEqual(result.slices, ())

    def test_rotation_slices_use_complete_arc_and_exported_bound(self):
        path = self.path(yaw=5000, pitch=5000)
        result = self.plan(path)
        self.assertGreater(len(result.slices), 1)
        self.assertEqual(result.slices[0].start.elapsed_ns, 0)
        self.assertEqual(result.slices[-1].end.elapsed_ns, 10_000_000)
        for a, b in zip(result.slices, result.slices[1:]):
            self.assertIs(a.end, b.start)
        c = path.provenance.command
        exact_k2 = F(c.curvature_yaw_per_m)**2+F(c.curvature_pitch_per_m)**2
        for item in result.slices:
            self.assertGreaterEqual(F(item.gate_bounds.curvature_upper_per_m)**2, exact_k2)
            self.assertGreaterEqual(F(item.gate_bounds.rotation_upper_rad)**2,
                                    exact_k2*item.exact_arc_length_m**2)
            self.assertLess(item.gate_bounds.rotation_upper_rad, math.pi/3600)
            self.assertGreater(item.end.elapsed_ns, item.start.elapsed_ns)

    def test_all_one_to_ten_ms_steps_and_profiles_have_contiguous_slices(self):
        for profile, speed in (('fast_9600', .25), ('stress_300', .002)):
            turn = math.isqrt(motion.curvature_limit_squared(profile, 20)//2)
            for ms in range(1, 11):
                path = self.path(profile=profile, speed=speed, yaw=turn, pitch=-turn, dt=ms*10**6)
                plan = self.plan(path)
                self.assertEqual(plan.covered_ns, ms*10**6)
                self.assertEqual(sum((x.exact_arc_length_m for x in plan.slices), F(0)), F(speed)*F(ms, 1000))

    def test_signed_turns_and_rotated_body_use_canonical_analytic_curve(self):
        root = math.sqrt(.5)
        for yaw, pitch in ((6000, 0), (-6000, 0), (0, 6000), (0, -6000)):
            identity = self.path(yaw=yaw, pitch=pitch).sample(10_000_000)
            component = identity.state.position_m[0 if yaw else 1]
            self.assertEqual(math.copysign(1., component), math.copysign(1., yaw or pitch))
            self.assertGreater(abs(component), 1e-7)
            reverse = self.path(yaw=yaw, pitch=pitch, q=(0., 1., 0., 0.)).sample(10_000_000)
            self.assertLess(reverse.state.position_m[2], 15.)
        along_x = self.path(q=(0., root, 0., root)).sample(10_000_000)
        self.assertAlmostEqual(along_x.state.position_m[0], .0025, places=14)

    def test_nominal_chord_larger_than_arc_has_separate_gate_bound(self):
        item = self.plan(self.path(pos=(0., 0., 17.), dt=1)).slices[0]
        chord = F(item.end.state.position_m[2])-F(item.start.state.position_m[2])
        self.assertGreater(chord, item.exact_arc_length_m)
        self.assertGreaterEqual(F(item.gate_bounds.arc_length_upper_m), chord)
        self.assertGreater(item.gate_bounds.arc_length_upper_m, item.path_arc_upper_m)
        self.assertGreaterEqual(F(item.errors.position_error_m), chord-item.exact_arc_length_m)

    def test_explicit_inherited_errors_propagate_full_distance_angular_drift(self):
        errors = ErrorBounds(.001, .01, .002)
        path = self.path(errors=errors, yaw=5000, pitch=5000)
        plan = self.plan(path)
        for item in plan.slices:
            required = F(errors.position_error_m)+item.end.exact_distance_m*F(errors.angle_error_rad)
            self.assertGreaterEqual(F(item.errors.position_error_m), required)
            self.assertGreaterEqual(item.errors.angle_error_rad, errors.angle_error_rad)
            self.assertEqual(item.errors.additional_margin_m, errors.additional_margin_m)
        self.assertEqual(path.provenance.error_budget_reference, 'exact test fixture')

    def test_final_normalized_quaternion_and_axis_have_separate_error_evidence(self):
        q = (.1, -.2, .3, math.sqrt(.86))
        sample = self.path(q=q, yaw=4000, pitch=-3500).sample(10_000_000)
        self.assertAlmostEqual(math.hypot(*sample.state.orientation_xyzw), 1.)
        self.assertAlmostEqual(math.hypot(*sample.axis), 1.)
        for value in (sample.numerical_position_error_m, sample.numerical_orientation_error_rad,
                      sample.numerical_axis_error_rad):
            self.assertGreater(value, 0.)
            self.assertLess(value, 1e-11)
        self.assertGreaterEqual(sample.errors.angle_error_rad, sample.numerical_axis_error_rad)
        self.assertGreaterEqual(sample.errors.angle_error_rad, sample.numerical_orientation_error_rad)

    def test_gate_consumes_derived_bounds_without_external_path_numbers(self):
        item = self.plan(self.path()).slices[0]
        body = Capsule(item.start.state.position_m, item.start.axis)
        result = sweep_clearance(body, Gate('front', 0., 0.), direction=1,
                                 errors=item.errors, bounds=item.gate_bounds)
        self.assertEqual(result.status, 'SAFE_IF_INTERSECTING')
        self.assertFalse(result.motion_grant)
        for keyword in ('step', 'curvature', 'arc_length', 'theta', 'bounds'):
            with self.assertRaises(TypeError):
                self.plan(self.path(), **{keyword: 0})

    def test_raw_codes_versions_state_and_errors_are_immutable_provenance(self):
        path = self.path(code=19, yaw=6000)
        plan = self.plan(path)
        self.assertEqual(path.provenance.raw_command, ('fast_9600', 19, 6000, 0))
        self.assertIs(plan.provenance, path.provenance)
        self.assertTrue(path.provenance.derivation_version)
        self.assertTrue(path.provenance.command_semantics)
        self.assertFalse(plan.authority_authenticated)
        for obj, attr in ((path, 'provenance'), (path.provenance, 'raw_command'),
                          (plan, 'slices'), (plan.slices[0], 'gate_bounds')):
            with self.assertRaises((FrozenInstanceError, AttributeError)):
                setattr(obj, attr, None)

    def test_invalid_inputs_and_profile_ceiling_are_rejected(self):
        for kwargs in ({'dt': True}, {'dt': 0}, {'dt': 10_000_001}, {'dt': 1.},
                       {'code': True}, {'yaw': True}, {'pitch': float('nan')},
                       {'profile': 'bogus'}, {'profile': 'stress_300'}, {'pos': (1001., 0., 0.)}):
            with self.assertRaises((ValueError, TypeError)):
                self.path(**kwargs)
        for field in ('start', 'deadline', 'stop'):
            for value in ((True, 1., -1) if field != 'stop' else (0, None, 'yes')):
                with self.assertRaises((ValueError, TypeError)):
                    self.plan(self.path(), **{field: value})
        for time in (True, -1, 10_000_001, float('nan'), 1.):
            with self.assertRaises((ValueError, TypeError)):
                self.path().sample(time)

    def test_required_error_budget_is_not_defaulted_or_authenticated(self):
        state = RigidState((0., 0., 0.), (0., 0., 0., 1.), 0.)
        with self.assertRaises(TypeError):
            cp.CanonicalPath(state, 'fast_9600', 20, 0, 0, 1)
        for reference in ('', '   ', None, True):
            with self.assertRaises((ValueError, TypeError)):
                cp.CanonicalPath(state, 'fast_9600', 20, 0, 0, 1,
                                 inherited_errors=self.zero, error_budget_reference=reference)

    def test_legacy_libm_sampling_is_not_used(self):
        with patch('competition.deepeye.simulation.authority.motion.kinematics._pose',
                   side_effect=AssertionError('legacy path must not run')):
            result = self.plan(self.path(yaw=5000, pitch=5000))
            self.assertGreater(result.covered_ns, 0)

    def test_independent_constant_curvature_circle_formula(self):
        path = self.path(yaw=6000, pos=(0., 0., 0.))
        k = path.provenance.command.curvature_yaw_per_m
        for ns in (1_000_000, 4_999_999, 10_000_000):
            sample = path.sample(ns)
            s = .25*ns/1e9
            theta = k*s
            # Closed-form circle with independent math implementation. The
            # private Decimal160 oracle separately checks certified errors.
            self.assertAlmostEqual(sample.state.position_m[0], (1-math.cos(theta))/k, delta=4e-16)
            self.assertAlmostEqual(sample.state.position_m[2], math.sin(theta)/k, delta=4e-16)
            self.assertAlmostEqual(sample.axis[0], math.sin(theta), delta=4e-16)
            self.assertAlmostEqual(sample.axis[2], math.cos(theta), delta=4e-16)

    def test_quaternion_sign_and_near_domain_boundary(self):
        q = (.1, -.2, .3, math.sqrt(.86))
        positive = self.path(q=q, yaw=4000).sample(10_000_000)
        negative = self.path(q=tuple(-x for x in q), yaw=4000).sample(10_000_000)
        self.assertEqual(positive.state.position_m, negative.state.position_m)
        self.assertEqual(positive.axis, negative.axis)
        for a,b in zip(positive.state.orientation_xyzw, negative.state.orientation_xyzw):
            self.assertEqual(a, -b)
        with self.assertRaises(ValueError):
            self.plan(self.path(pos=(0., 0., 1000.)))

    def test_error_scalars_reject_nonfinite_and_bool(self):
        for value in (True, float('nan'), float('inf'), float('-inf'), -1.):
            for args in ((value, 0., 0.), (0., value, 0.), (0., 0., value)):
                with self.assertRaises((TypeError, ValueError)):
                    self.path(errors=ErrorBounds(*args))

    def test_hostile_decimal_context_cannot_change_result(self):
        normal = asdict(self.plan(self.path(yaw=3000, pitch=-3000)))
        hostile = Context(prec=1, rounding=ROUND_UP, Emax=2, Emin=-2, traps=[Inexact, Rounded])
        with localcontext(hostile):
            actual = asdict(self.plan(self.path(yaw=3000, pitch=-3000)))
        self.assertEqual(actual, normal)

    def test_cold_import_in_hostile_context(self):
        script = '''from decimal import *
setcontext(Context(prec=1, Emax=2, Emin=-2, traps=[Inexact,Rounded]))
from competition.deepeye.simulation.authority.motion.certified_path import CanonicalPath
from competition.deepeye.simulation.authority.motion.kinematics import RigidState
from competition.deepeye.simulation.authority.motion.gate_clearance import ErrorBounds
p=CanonicalPath(RigidState((0.,0.,0.),(0.,0.,0.,1.),.25),'fast_9600',20,5000,5000,10000000,
 inherited_errors=ErrorBounds(0,0,0),error_budget_reference='cold test')
r=p.plan(start_monotonic_ns=0,deadline_monotonic_ns=20000001,hard_stop=False)
assert r.covered_ns==10000000 and len(r.slices)>1
print('COLD_CONTEXT_OK')
'''
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script],
                                cwd=Path(__file__).resolve().parents[4],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('COLD_CONTEXT_OK', result.stdout)


if __name__ == '__main__':
    unittest.main()
