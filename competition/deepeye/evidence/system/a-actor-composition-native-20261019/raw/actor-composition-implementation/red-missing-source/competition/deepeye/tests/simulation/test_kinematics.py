"""G06 authority kinematics: numerical evidence, not collision/authority acceptance.

Expected poses below use hand-derived straight segments, circles and the
composition of a 90 degree world roll with a body yaw. No production geometry
helper computes an expected value. Run with unittest discover from repo root.
"""
from dataclasses import FrozenInstanceError
import importlib
import math
from pathlib import Path
import unittest


MODULE = "competition.deepeye.simulation.authority.motion.kinematics"
SOURCE = Path(__file__).resolve().parents[2] / "simulation/authority/motion/kinematics.py"


class KinematicsTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.is_file(), "RED: authority kinematics is not implemented")
        self.k = importlib.import_module(MODULE)

    def state(self, speed=0.0, position=(0.0, 0.0, 0.0), orientation=(0.0, 0.0, 0.0, 1.0)):
        return self.k.RigidState(position, orientation, speed)

    def assert_vector(self, actual, expected, tolerance=2e-15):
        self.assertEqual(len(actual), len(expected))
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want, delta=tolerance)

    def test_acceleration_from_rest_integrates_average_speed(self):
        step = self.k.advance(self.state(), "fast_9600", 10, 0, 0, 10_000_000)
        self.assertAlmostEqual(step.end_state.speed_m_s, 0.0025, delta=1e-17)
        self.assertAlmostEqual(step.distance_m, 0.0000125, delta=1e-19)
        self.assert_vector(step.end_state.position_m, (0, 0, 0.0000125))

    def test_straight_ramp_does_not_use_final_speed_for_whole_step(self):
        step = self.k.advance(self.state(0.1), "fast_9600", 10, 0, 0, 10_000_000)
        self.assertAlmostEqual(step.distance_m, 0.0010125, delta=1e-18)
        self.assertAlmostEqual(step.end_state.speed_m_s, 0.1025, delta=2e-17)

    def test_acceleration_reaching_target_splits_the_step(self):
        step = self.k.advance(self.state(0.124), "fast_9600", 10, 0, 0, 10_000_000)
        self.assertEqual(step.end_state.speed_m_s, 0.125)
        self.assertAlmostEqual(step.distance_m, 0.001248, delta=1e-18)
        for ns, distance, speed in [(2_000_000, 0.0002485, 0.1245),
                                    (4_000_000, 0.000498, 0.125),
                                    (8_000_000, 0.000998, 0.125)]:
            with self.subTest(ns=ns):
                sample = step.sample_at_time_ns(ns)
                self.assertEqual(sample.elapsed_ns, ns)
                self.assertAlmostEqual(sample.distance_m, distance, delta=1e-18)
                self.assertAlmostEqual(sample.state.speed_m_s, speed, delta=1e-17)

    def test_deceleration_reaching_target_splits_the_step(self):
        step = self.k.advance(self.state(0.126), "fast_9600", 10, 0, 0, 10_000_000)
        self.assertEqual(step.end_state.speed_m_s, 0.125)
        self.assertAlmostEqual(step.distance_m, 0.001252, delta=1e-18)
        sample = step.sample_at_time_ns(2_000_000)
        self.assertAlmostEqual(sample.distance_m, 0.0002515, delta=1e-18)
        self.assertAlmostEqual(sample.state.speed_m_s, 0.1255, delta=1e-17)

    def test_zero_target_is_straight_braking_and_not_an_authorization_stop(self):
        state = self.state(0.001, orientation=(0, math.sqrt(0.5), 0, math.sqrt(0.5)))
        step = self.k.advance(state, "fast_9600", 0, 0, 0, 10_000_000)
        self.assertEqual(step.end_state.speed_m_s, 0.0)
        self.assertAlmostEqual(step.distance_m, 0.000002, delta=1e-20)
        self.assert_vector(step.end_state.position_m, (0.000002, 0, 0))
        self.assert_vector(step.end_state.orientation_xyzw, state.orientation_xyzw)
        self.assert_vector(step.sample_at_time_ns(8_000_000).state.position_m,
                           step.end_state.position_m)

    def test_zero_speed_and_zero_target_never_rotate_or_translate(self):
        state = self.state(position=(1, 2, 3), orientation=(0.5, 0.5, 0.5, 0.5))
        step = self.k.advance(state, "fast_9600", 0, 0, 0, 10_000_000)
        self.assertEqual(step.distance_m, 0)
        self.assertEqual(step.end_state, state)
        self.assertEqual(step.sample_at_distance_m(0).elapsed_ns, 0)
        self.assertEqual(step.sample_at_time_ns(10_000_000).elapsed_ns, 10_000_000)
        with self.assertRaises(ValueError):
            self.k.advance(state, "fast_9600", 0, 1, 0, 1)

    def test_zero_distance_preserves_an_arbitrary_orientation_exactly(self):
        # Repeated quaternion normalization must not perturb an unmoved pose.
        q = (0.4775698668289185, -0.49555614020933253,
             -0.27371218030226185, -0.671887473132235)
        stopped = self.state(orientation=q)
        self.assertEqual(self.k.advance(stopped, "fast_9600", 0, 0, 0, 1).end_state, stopped)
        moving = self.state(0.125, orientation=q)
        step = self.k.advance(moving, "fast_9600", 10, 2000, 0, 10_000_000)
        self.assertEqual(step.sample_at_time_ns(0).state, moving)
        self.assertEqual(step.sample_at_distance_m(0).state, moving)

    def test_signed_yaw_follows_horizontal_circle(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                step = self.k.advance(self.state(0.125), "fast_9600", 10, sign*2000, 0, 10_000_000)
                angle = math.pi / 9000  # 2 degrees/s for 0.01 seconds.
                radius = 0.125 / math.radians(2)
                self.assert_vector(step.end_state.position_m,
                                   (sign*radius*2*math.sin(angle/2)**2, 0, radius*math.sin(angle)))
                self.assert_vector(step.end_state.orientation_xyzw,
                                   (0, sign*math.sin(angle/2), 0, math.cos(angle/2)))

    def test_signed_pitch_uses_negative_body_x_axis(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                step = self.k.advance(self.state(0.125), "fast_9600", 10, 0, sign*2000, 10_000_000)
                angle, radius = math.pi / 9000, 0.125 / math.radians(2)
                self.assert_vector(step.end_state.position_m,
                                   (0, sign*radius*2*math.sin(angle/2)**2, radius*math.sin(angle)))
                self.assert_vector(step.end_state.orientation_xyzw,
                                   (-sign*math.sin(angle/2), 0, 0, math.cos(angle/2)))

    def test_combined_yaw_pitch_is_one_three_dimensional_rotation(self):
        step = self.k.advance(self.state(0.125), "fast_9600", 10, 1800, 2400, 10_000_000)
        angle, radius = math.pi / 6000, 0.125 / math.radians(3)
        radial = radius*2*math.sin(angle/2)**2
        self.assert_vector(step.end_state.position_m, (0.6*radial, 0.8*radial, radius*math.sin(angle)))
        self.assert_vector(step.end_state.orientation_xyzw,
                           (-0.8*math.sin(angle/2), 0.6*math.sin(angle/2), 0, math.cos(angle/2)))

    def test_body_rotation_right_multiplies_nonidentity_world_orientation(self):
        root_half = math.sqrt(0.5)
        step = self.k.advance(self.state(0.125, (1, 2, 3), (0, 0, root_half, root_half)),
                              "fast_9600", 10, 2000, 0, 10_000_000)
        angle, radius = math.pi / 9000, 0.125 / math.radians(2)
        sh, ch = math.sin(angle/2), math.cos(angle/2)
        self.assert_vector(step.end_state.position_m,
                           (1, 2+radius*2*sh*sh, 3+radius*math.sin(angle)))
        self.assert_vector(step.end_state.orientation_xyzw,
                           (-root_half*sh, root_half*sh, root_half*ch, root_half*ch))

    def test_angular_motion_scales_with_actual_accelerating_speed(self):
        step = self.k.advance(self.state(), "fast_9600", 10, 2000, 0, 10_000_000)
        # Travel is only 1/100 of steady-speed travel in this step.
        angle = math.pi / 900000
        radius = 0.125 / math.radians(2)
        self.assert_vector(step.end_state.orientation_xyzw, (0, math.sin(angle/2), 0, math.cos(angle/2)))
        self.assert_vector(step.end_state.position_m,
                           (radius*2*math.sin(angle/2)**2, 0, radius*math.sin(angle)))

    def test_postquantization_profile_boundaries_are_not_clipped(self):
        for profile, code, speed, good, bad in [
            ("fast_9600", 20, 0.25, (7161, 0), (7162, 0)),
            ("fast_9600", 20, 0.25, (5000, 5000), (6000, 4000)),
            ("stress_300", 20, 0.002, (57, 0), (58, 0)),
            ("stress_300", 20, 0.002, (40, 40), (41, 41)),
            ("stress_300", 1, 0.0001, (2, 2), (3, 0)),
        ]:
            with self.subTest(profile=profile, code=code, good=good):
                self.k.advance(self.state(speed), profile, code, *good, 10_000_000)
                with self.assertRaises(ValueError):
                    self.k.advance(self.state(speed), profile, code, *bad, 10_000_000)

    def test_profile_change_cannot_hide_excess_actual_speed(self):
        self.k.advance(self.state(0.002), "stress_300", 20, 0, 0, 10_000_000)
        for speed in (0.00200000001, 0.01, 0.25):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                self.k.advance(self.state(speed), "stress_300", 0, 0, 0, 10_000_000)

    def test_command_fields_reject_bool_nonintegers_and_unknown_profiles(self):
        for args in [("FAST_9600", 10, 0, 0), (True, 10, 0, 0),
                     ("fast_9600", True, 0, 0), ("fast_9600", 1.0, 0, 0),
                     ("fast_9600", 21, 0, 0), ("fast_9600", -1, 0, 0),
                     ("fast_9600", 10, True, 0), ("fast_9600", 10, 0, 0.0),
                     ("fast_9600", 10, 15001, 0), ("fast_9600", 10, 0, float("nan"))]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.k.advance(self.state(), *args, 10_000_000)

    def test_substep_duration_is_strict_integer_nanoseconds(self):
        for ns in (True, False, 1.0, 0, -1, 10_000_001, float("nan"), float("inf"), "1"):
            with self.subTest(ns=ns), self.assertRaises(ValueError):
                self.k.advance(self.state(), "fast_9600", 0, 0, 0, ns)
        for ns in (1, 10_000_000):
            self.assertEqual(self.k.advance(self.state(), "fast_9600", 0, 0, 0, ns).dt_ns, ns)

    def test_invalid_state_shapes_nonfinite_and_nonunit_inputs_are_rejected(self):
        for position in ((0, 0), (0, 0, 0, 0), (0, True, 0), (0, float("nan"), 0),
                         (0, float("inf"), 0), (0, 10**1000, 0), "abc", (0, "0", 0)):
            with self.subTest(position=str(position)[:60]), self.assertRaises(ValueError):
                self.state(position=position)
        for orientation in ((0, 0, 1), (0, 0, 0, 0, 1), (0, 0, 0, 0),
                            (0, 0, 0, 1+1e-9), (0, 0, True, 0), (0, float("nan"), 0, 1),
                            (0, float("inf"), 0, 1), (0, 0, 0, "1")):
            with self.subTest(orientation=orientation), self.assertRaises(ValueError):
                self.state(orientation=orientation)
        for speed in (True, -1e-12, 0.25000000001, float("inf"), float("nan"), "0"):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                self.state(speed)

    def test_vectors_are_snapshotted_and_all_results_are_immutable(self):
        position, orientation = [1, 2, 3], [0, 0, 0, 1]
        state = self.state(0.125, position, orientation)
        position[2], orientation[3] = 100, 0
        step = self.k.advance(state, "fast_9600", 10, 0, 0, 1)
        self.assertEqual(state.position_m, (1, 2, 3))
        self.assertEqual(state.orientation_xyzw, (0, 0, 0, 1))
        sample = step.sample_at_time_ns(0)
        for value, field, replacement in [(state, "speed_m_s", 0), (step, "dt_ns", 0),
                                           (sample, "distance_m", 5), (step.end_state, "position_m", (4, 5, 6))]:
            with self.subTest(field=field), self.assertRaises((FrozenInstanceError, AttributeError)):
                setattr(value, field, replacement)
        self.assertIsInstance(step.end_state.position_m, tuple)
        self.assertIsInstance(step.end_state.orientation_xyzw, tuple)
        self.assertEqual(state.speed_m_s, 0.125)

    def test_distance_sampling_inverts_acceleration_and_cruise(self):
        step = self.k.advance(self.state(0.124), "fast_9600", 10, 0, 0, 10_000_000)
        for distance, elapsed_ns, speed in [(0, 0, 0.124), (0.0002485, 2_000_000, 0.1245),
                                           (0.000498, 4_000_000, 0.125),
                                           (0.000998, 8_000_000, 0.125)]:
            with self.subTest(distance=distance):
                sample = step.sample_at_distance_m(distance)
                self.assertAlmostEqual(sample.elapsed_ns, elapsed_ns, delta=1e-7)
                self.assertEqual(sample.distance_m, distance)
                self.assert_vector(sample.state.position_m, (0, 0, distance))
                self.assertAlmostEqual(sample.state.speed_m_s, speed, delta=1e-17)

    def test_distance_sampling_braking_plateau_chooses_earliest_time(self):
        step = self.k.advance(self.state(0.001), "fast_9600", 0, 0, 0, 10_000_000)
        sample = step.sample_at_distance_m(0.0000015)
        self.assertAlmostEqual(sample.elapsed_ns, 2_000_000, delta=1e-7)
        self.assertAlmostEqual(sample.state.speed_m_s, 0.0005, delta=1e-18)
        stopped = step.sample_at_distance_m(step.distance_m)
        self.assertAlmostEqual(stopped.elapsed_ns, 4_000_000, delta=1e-7)
        self.assertEqual(stopped.state.speed_m_s, 0)

    def test_subnormal_positive_distance_has_finite_accurate_inverse(self):
        # Independent decimal oracle: forming v0**2 or 2*a*s first can
        # underflow, either raising or silently clipping a tiny time to dt.
        from decimal import Decimal, localcontext
        distance = math.nextafter(0.0, 1.0)
        for speed in (0.0, distance, 1e-170, 1e-162, 1e-155):
            with self.subTest(speed=speed), localcontext() as ctx:
                ctx.prec = 80
                v, s, a = map(Decimal.from_float, (speed, distance, 0.25))
                expected_time = 2*s / (v + (v*v + 2*a*s).sqrt())
                expected_speed = v + a*expected_time
                step = self.k.advance(self.state(speed), "fast_9600", 10, 0, 0, 10_000_000)
                sample = step.sample_at_distance_m(distance)
                self.assertTrue(math.isclose(sample.elapsed_ns, float(expected_time*10**9),
                                             rel_tol=4e-15, abs_tol=0))
                self.assertTrue(math.isclose(sample.state.speed_m_s, float(expected_speed),
                                             rel_tol=4e-15, abs_tol=0))
                self.assertEqual(sample.distance_m, distance)

    def test_samples_cannot_leave_the_step_domain(self):
        step = self.k.advance(self.state(0.125), "fast_9600", 10, 2000, 0, 10_000_000)
        for ns in (-1, 10_000_001, True, 1.5, float("nan")):
            with self.subTest(ns=ns), self.assertRaises(ValueError):
                step.sample_at_time_ns(ns)
        for distance in (-1e-30, math.nextafter(step.distance_m, math.inf), True,
                         float("nan"), float("inf"), "0"):
            with self.subTest(distance=distance), self.assertRaises(ValueError):
                step.sample_at_distance_m(distance)
        self.assertEqual(step.sample_at_time_ns(10_000_000).state, step.end_state)
        self.assertEqual(step.sample_at_distance_m(step.distance_m).state, step.end_state)

    def test_interior_samples_follow_the_arc_not_an_endpoint_chord(self):
        step = self.k.advance(self.state(0.125), "fast_9600", 10, 1800, -2400, 10_000_000)
        radius = 0.125 / math.radians(3)
        angle = math.pi / 12000  # Half of this 3 degree/s, 10 ms step.
        radial = radius*2*math.sin(angle/2)**2
        for sample in (step.sample_at_time_ns(5_000_000), step.sample_at_distance_m(0.000625)):
            self.assertAlmostEqual(sample.elapsed_ns, 5_000_000, delta=1e-7)
            self.assert_vector(sample.state.position_m,
                               (0.6*radial, -0.8*radial, radius*math.sin(angle)))
            self.assert_vector(sample.state.orientation_xyzw,
                               (0.8*math.sin(angle/2), 0.6*math.sin(angle/2), 0, math.cos(angle/2)))

    def test_low_speed_small_turns_are_not_erased_by_an_angle_threshold(self):
        step = self.k.advance(self.state(), "stress_300", 1, 2, 2, 1)
        distance = 1.25e-19
        curvature = math.pi / 9  # 0.002 deg/s / 0.0001 m/s.
        self.assertAlmostEqual(step.distance_m, distance, delta=1e-34)
        self.assertAlmostEqual(step.end_state.position_m[0], 0.5*curvature*distance**2, delta=1e-53)
        self.assertAlmostEqual(step.end_state.position_m[1], 0.5*curvature*distance**2, delta=1e-53)
        self.assertAlmostEqual(step.end_state.orientation_xyzw[0], -0.5*curvature*distance, delta=1e-34)
        self.assertAlmostEqual(step.end_state.orientation_xyzw[1], 0.5*curvature*distance, delta=1e-34)
        self.assertGreater(step.end_state.position_m[0], 0)

    def test_step_partition_preserves_curved_acceleration_and_deceleration(self):
        for initial_speed in (0.0005, 0.002):
            with self.subTest(initial_speed=initial_speed):
                start = self.state(initial_speed, (1, 2, 3), (0.5, 0.5, 0.5, 0.5))
                whole = self.k.advance(start, "stress_300", 10, 20, -20, 10_000_000)
                state, travelled = start, 0.0
                for ns in (1, 999_999, 2_000_000, 3_000_000, 4_000_000):
                    step = self.k.advance(state, "stress_300", 10, 20, -20, ns)
                    state = step.end_state
                    travelled += step.distance_m
                self.assertAlmostEqual(travelled, whole.distance_m, delta=1e-19)
                self.assert_vector(state.position_m, whole.end_state.position_m, tolerance=2e-15)
                self.assert_vector(state.orientation_xyzw, whole.end_state.orientation_xyzw)
                self.assertAlmostEqual(state.speed_m_s, whole.end_state.speed_m_s, delta=1e-17)

    def test_many_steps_follow_analytic_half_circle_without_quaternion_drift(self):
        state = self.state(0.125)
        for _ in range(6000):
            state = self.k.advance(state, "fast_9600", 10, 3000, 0, 10_000_000).end_state
            self.assertAlmostEqual(math.hypot(*state.orientation_xyzw), 1, delta=4e-16)
        self.assert_vector(state.position_m, (15/math.pi, 0, 0), tolerance=2e-11)
        self.assert_vector(state.orientation_xyzw, (0, 1, 0, 0), tolerance=2e-12)

    def test_sequential_distinct_turn_axes_accumulate_rigid_orientation(self):
        # Tiny yaw then pitch: their noncommuting product has positive z term.
        first = self.k.advance(self.state(0.125), "fast_9600", 10, 2000, 0, 10_000_000)
        second = self.k.advance(first.end_state, "fast_9600", 10, 0, 2000, 10_000_000)
        h = math.pi / 18000
        s, c = math.sin(h), math.cos(h)
        self.assert_vector(second.end_state.orientation_xyzw, (-c*s, s*c, s*s, c*c))
        self.assertGreater(second.end_state.orientation_xyzw[2], 0)

    def test_rejected_command_does_not_change_input_pose(self):
        state = self.state(0.125, (1, 2, 3), (0.5, 0.5, 0.5, 0.5))
        snapshot = (state.position_m, state.orientation_xyzw, state.speed_m_s)
        with self.assertRaises(ValueError):
            self.k.advance(state, "fast_9600", 10, 15000, 15000, 10_000_000)
        self.assertEqual((state.position_m, state.orientation_xyzw, state.speed_m_s), snapshot)


if __name__ == "__main__":
    unittest.main()
