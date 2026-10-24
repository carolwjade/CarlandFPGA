"""DeepEye candidate forward-profile tests (software checkpoint only).

Run from the product worktree root with bytecode disabled:

    <repo>/.local/venv/Scripts/python.exe -B -m unittest discover -s competition/deepeye/tests/simulation -p test_forward_profile.py -v

Scope: deterministic kernel arithmetic, pose/lattice cropping, causal timing and
zero-order hold, the contact-only vibration model and the serialization
whitelist of simulation/sensors/forward_profile.py.

GREEN here is NOT physical validity, NOT a calibration, NOT an independent 3D
FDEM or mesh-convergence gate; G03/G09 remain not_run and no product card PASS
is implied.  The independent recomputation helper re-implements the frozen
quadrature definition only to cross-check the module implementation (mutation
detection), not to validate the physics model against reality.
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve()
DEEPEYE_ROOT = HERE.parents[2]
MODULE_PATH = DEEPEYE_ROOT / "simulation" / "sensors" / "forward_profile.py"


def load_module():
    if not MODULE_PATH.is_file():
        raise AssertionError("RED: %s is not implemented yet" % MODULE_PATH)
    spec = importlib.util.spec_from_file_location("deepeye_forward_profile_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load %s" % MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fp = load_module()

PAYLOAD_KEYS = {
    "profile_id",
    "profile_status",
    "profile_note",
    "source_mode",
    "adc_tick_ms",
    "em_tick_ms",
    "channel_values",
    "channel_counts",
    "quality",
}
FORBIDDEN_PAYLOAD_TOKENS = (
    "seed", "obstacle", "truth", "distance", "class", "collision",
    "contact", "callback", "label", "editor", "boundary", "screenshot",
)


class NoiseStub:
    """Deterministic rand.gauss replacement: value = mu + sigma*z."""

    def __init__(self, z=0.0):
        self.z = z
        self.calls = []

    def gauss(self, mu, sigma):
        self.calls.append((mu, sigma))
        return mu + sigma * self.z


class ConstantField:
    """Homogeneous conductivity sampler with call recording."""

    def __init__(self, sigma):
        self.sigma = sigma
        self.calls = []

    def __call__(self, x, y, z):
        self.calls.append((x, y, z))
        return self.sigma


class RecordingField(ConstantField):
    """Records every queried world position (no labels, no geometry classes)."""

    def __call__(self, x, y, z):
        self.calls.append((x, y, z))
        return self.sigma


class ScriptedField:
    """Returns per-query values from a rule callable; records calls."""

    def __init__(self, rule):
        self.rule = rule
        self.calls = []

    def __call__(self, x, y, z):
        self.calls.append((x, y, z))
        return self.rule(x, y, z)


class TickField:
    """Selects a sampler by acquisition tick (simulates a changing medium)."""

    def __init__(self, by_tick, default_sigma=0.01):
        self.by_tick = dict(by_tick)
        self.default_sigma = default_sigma

    def for_tick(self, tick):
        outer = self
        inner = self.by_tick.get(tick)

        class _Bound:
            def __call__(self, x, y, z):
                if inner is None:
                    return outer.default_sigma
                return inner(x, y, z)

        return _Bound()

class HalfSpaceField:
    """sigma_high for coordinate[axis] > 0 in world metres, else sigma_bg."""

    def __init__(self, axis, sigma_high=1.0, sigma_bg=0.01):
        self.axis = axis
        self.sigma_high = sigma_high
        self.sigma_bg = sigma_bg

    def __call__(self, x, y, z):
        value = (x, y, z)[self.axis]
        return self.sigma_high if value > 0.0 else self.sigma_bg


class BallField:
    """sigma_ball inside a world-space sphere, else sigma_bg; labels stay private."""

    def __init__(self, centre, radius, sigma_ball=5.0, sigma_bg=0.01, private_label=None):
        self.centre = centre
        self.radius = radius
        self.sigma_ball = sigma_ball
        self.sigma_bg = sigma_bg
        self.private_label = private_label
        self.calls = 0

    def __call__(self, x, y, z):
        self.calls += 1
        dx = x - self.centre[0]
        dy = y - self.centre[1]
        dz = z - self.centre[2]
        if dx * dx + dy * dy + dz * dz <= self.radius * self.radius:
            return self.sigma_ball
        return self.sigma_bg


def identity_pose(x=0.0, y=0.0, z=0.0):
    return fp.Pose((x, y, z), (0.0, 0.0, 0.0, 1.0))


def yaw_pose(deg, x=0.0, y=0.0, z=0.0):
    half = math.radians(deg) * 0.5
    return fp.Pose((x, y, z), (0.0, math.sin(half), 0.0, math.cos(half)))


def quat_multiply(a, b):
    """xyzw Hamilton product a*b (apply b first, then a)."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def rotation_from_xyzw(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        (1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)),
        (2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)),
        (2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)),
    )


COS_HALF_ANGLE = math.cos(math.radians(30.0))
_AXES = (
    (0.0, 0.0, 1.0),
    (math.sin(math.radians(20.0)), 0.0, math.cos(math.radians(20.0))),
    (-math.sin(math.radians(20.0)), 0.0, math.cos(math.radians(20.0))),
    (0.0, math.sin(math.radians(20.0)), math.cos(math.radians(20.0))),
    (0.0, -math.sin(math.radians(20.0)), math.cos(math.radians(20.0))),
)


def independent_channels(position, orientation_xyzw, sampler, step=0.25, support=8.0):
    """Independent recomputation of the frozen quadrature definition.

    Only a cross-check of the module implementation; the same documented
    formula (body-local 0.25 m lattice, r<=8 m, five 30-degree cones at
    0/+/-20 deg, w = cos^2(theta)*exp(-r/4)/(r+0.25)^2*dV) is re-implemented
    here rather than reused, so implementation mutations are caught.
    """
    rot = rotation_from_xyzw(orientation_xyzw)
    lim = int(round(support / step))
    d_v = step ** 3
    sum_w = [0.0] * 5
    sum_ws = [0.0] * 5
    for i in range(-lim, lim + 1):
        dx = i * step
        for j in range(-lim, lim + 1):
            dy = j * step
            for k in range(0, lim + 1):
                dz = k * step
                r2 = dx * dx + dy * dy + dz * dz
                if r2 > support * support:
                    continue
                r = math.sqrt(r2)
                if r == 0.0:
                    cosines = (1.0, 1.0, 1.0, 1.0, 1.0)
                else:
                    ux, uy, uz = dx / r, dy / r, dz / r
                    cosines = tuple(
                        ux * axis[0] + uy * axis[1] + uz * axis[2] for axis in _AXES
                    )
                sigma = None
                for lobe in range(5):
                    cos_t = cosines[lobe]
                    if cos_t >= COS_HALF_ANGLE:
                        if sigma is None:
                            sigma = sampler(
                                position[0] + rot[0][0] * dx + rot[0][1] * dy + rot[0][2] * dz,
                                position[1] + rot[1][0] * dx + rot[1][1] * dy + rot[1][2] * dz,
                                position[2] + rot[2][0] * dx + rot[2][1] * dy + rot[2][2] * dz,
                            )
                        weight = cos_t * cos_t * math.exp(-r / 4.0) / ((r + step) ** 2) * d_v
                        sum_w[lobe] += weight
                        sum_ws[lobe] += weight * sigma
    log10_rho = [-math.log10(sum_ws[lobe] / sum_w[lobe]) for lobe in range(5)]
    return (log10_rho[0], log10_rho[1] - log10_rho[2], log10_rho[3] - log10_rho[4])

class ForwardProfileSoftwareTests(unittest.TestCase):
    def test_sampler_exception_invalidates_held_em_until_new_success(self):
        profile = fp.ForwardProfile(em_rng=NoiseStub(), vibration_rng=NoiseStub())
        field = ConstantField(0.01)
        profile.acquire_em(0, identity_pose(), context='formation', sampler=field)
        self.assertEqual(profile.sample_adc(0).to_payload()['quality'] & 7, 7)

        def unavailable(*position):
            raise RuntimeError('source unavailable')

        with self.assertRaisesRegex(RuntimeError, 'source unavailable'):
            profile.acquire_em(50, identity_pose(), context='formation', sampler=unavailable)
        for tick in (50, 60, 90):
            payload = profile.sample_adc(tick).to_payload()
            self.assertTrue(payload['quality'] & (1 << 12))
            self.assertEqual(payload['quality'] & 0x707, 0)
            self.assertEqual(payload['channel_values'][:3], [None] * 3)
            self.assertEqual(payload['channel_counts'][:3], [None] * 3)
        with self.assertRaises(ValueError):
            profile.acquire_em(50, identity_pose(), context='formation', sampler=field)
        profile.acquire_em(100, identity_pose(), context='formation', sampler=field)
        payload = profile.sample_adc(100).to_payload()
        self.assertEqual(payload['quality'] & 7, 7)
        self.assertEqual(payload['quality'] & (1 << 12), 0)
        self.assertEqual(payload['em_tick_ms'], 100)

    def _fresh(self, sampler, tick=100, pose_obj=None, context="formation", em_rng=None, vib_rng=None):
        profile = fp.ForwardProfile(
            em_rng=NoiseStub(0.0) if em_rng is None else em_rng,
            vibration_rng=NoiseStub(0.0) if vib_rng is None else vib_rng,
        )
        profile.acquire_em(
            tick,
            pose_obj if pose_obj is not None else identity_pose(),
            context=context,
            sampler=sampler,
        )
        return profile

    def _read_after_acquire(self, profile, tick, sampler, context="formation", pose_obj=None, contact=None):
        profile.acquire_em(tick, pose_obj if pose_obj is not None else identity_pose(), context=context, sampler=sampler)
        return profile.sample_adc(tick, contact_accel_g=contact)

    # ------------------------------------------------------------------ pose
    def test_pose_requires_finite_position_and_usable_orientation(self):
        bad_positions = ((float("nan"), 0.0, 0.0), (0.0, float("inf"), 0.0), (0.0, 0.0), (0.0, 0.0, "far"))
        for position in bad_positions:
            with self.assertRaises(ValueError):
                fp.Pose(position, (0.0, 0.0, 0.0, 1.0))
        bad_orientations = (
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1e-12),
            (0.0, 0.0, float("nan"), 1.0),
            (0.0, 0.0, 0.0, float("inf")),
            (0.0, 0.0, 1.0),
            (False, 0.0, 0.0, 1.0),
        )
        for orientation in bad_orientations:
            with self.assertRaises(ValueError):
                fp.Pose((0.0, 0.0, 0.0), orientation)
        normalized = fp.Pose((1.0, 2.0, 3.0), (0.0, 0.0, 0.0, 2.0))
        self.assertEqual(normalized.orientation_xyzw, (0.0, 0.0, 0.0, 1.0))

    def test_invalid_pose_rejects_before_scene_query_and_keeps_slot(self):
        field = RecordingField(0.01)
        profile = fp.ForwardProfile(em_rng=NoiseStub(0.0), vibration_rng=NoiseStub(0.0))
        with self.assertRaises(ValueError):
            profile.acquire_em(100, (0.0, 0.0, 0.0), context="formation", sampler=field)
        self.assertEqual(field.calls, [])
        profile.acquire_em(100, identity_pose(), context="formation", sampler=field)
        self.assertGreater(len(field.calls), 0)

    # ------------------------------------------------------------ validation
    def test_tick_grid_and_clock_rules_are_explicit(self):
        field = ConstantField(0.01)
        profile = self._fresh(field, tick=100)
        with self.assertRaises(ValueError):
            profile.acquire_em(125, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(100, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(50, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(-50, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(150.0, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(True, identity_pose(), context="formation", sampler=field)
        profile.sample_adc(100)
        with self.assertRaises(ValueError):
            profile.sample_adc(100)
        with self.assertRaises(ValueError):
            profile.sample_adc(90)
        with self.assertRaises(ValueError):
            profile.sample_adc(105)
        with self.assertRaises(ValueError):
            profile.sample_adc(110.0)
        profile.sample_adc(150)
        with self.assertRaises(ValueError):
            profile.acquire_em(150, identity_pose(), context="formation", sampler=field)
        profile.acquire_em(200, identity_pose(), context="formation", sampler=field)

    def test_unknown_context_and_missing_sampler_are_rejected(self):
        profile = fp.ForwardProfile(em_rng=NoiseStub(0.0), vibration_rng=NoiseStub(0.0))
        field = ConstantField(0.01)
        with self.assertRaises(ValueError):
            profile.acquire_em(100, identity_pose(), context="mud", sampler=field)
        with self.assertRaises(ValueError):
            profile.acquire_em(100, identity_pose(), context="formation", sampler=None)
        with self.assertRaises(ValueError):
            profile.acquire_em(100, identity_pose(), context="formation", sampler="not-callable")
        self.assertEqual(field.calls, [])

    def test_unsupported_medium_and_shield_context_are_invalid_not_fabricated(self):
        for context in (fp.CONTEXT_AIR, fp.CONTEXT_CONDUCTING_SHIELD):
            field = RecordingField(0.01)
            profile = fp.ForwardProfile(em_rng=NoiseStub(0.0), vibration_rng=NoiseStub(0.0))
            profile.acquire_em(0, identity_pose(), context=context, sampler=field)
            self.assertEqual(field.calls, [])
            sample = profile.sample_adc(0)
            for channel in (0, 1, 2):
                self.assertFalse(sample.is_valid(channel))
                self.assertIsNone(sample.channel_values[channel])
                self.assertIsNone(sample.channel_counts[channel])
            self.assertIsNone(sample.em_tick_ms)
            self.assertTrue(sample.source_fault)
            self.assertTrue(sample.quality & (1 << 12))

    def test_bad_conductivity_values_fault_without_believable_reading(self):
        for bad in (None, float("nan"), float("inf"), float("-inf"), 0.0, -0.05, 1e-9, 6.0, True):
            profile = fp.ForwardProfile(em_rng=NoiseStub(0.0), vibration_rng=NoiseStub(0.0))
            profile.acquire_em(100, identity_pose(), context="formation", sampler=ConstantField(bad))
            sample = profile.sample_adc(100)
            for channel in (0, 1, 2):
                self.assertIsNone(sample.channel_values[channel], bad)
                self.assertFalse(sample.is_valid(channel), bad)
            self.assertTrue(sample.source_fault, bad)
        boundary = self._fresh(ConstantField(fp.SIGMA_MAX_S_PER_M))
        self.assertAlmostEqual(boundary.sample_adc(100).channel_values[0], fp.LOG10_RHO_MIN, delta=1e-12)

    def test_faulted_attempt_consumes_no_noise_stream(self):
        selector = TickField({100: ConstantField(0.01), 150: ConstantField(float("nan")), 200: ConstantField(0.01)})
        profile_a = self._fresh(selector.for_tick(100), tick=100, em_rng=random.Random(7))
        profile_a.acquire_em(150, identity_pose(), context="formation", sampler=selector.for_tick(150))
        profile_a.acquire_em(200, identity_pose(), context="formation", sampler=selector.for_tick(200))
        profile_b = self._fresh(ConstantField(0.01), tick=100, em_rng=random.Random(7))
        profile_b.acquire_em(200, identity_pose(), context="formation", sampler=selector.for_tick(200))
        sample_a = profile_a.sample_adc(200)
        sample_b = profile_b.sample_adc(200)
        self.assertTrue(sample_a.is_valid(0))
        self.assertEqual(sample_a.channel_values[0], sample_b.channel_values[0])
        self.assertEqual(sample_a.channel_values[1], sample_b.channel_values[1])

    # ---------------------------------------------------------------- kernel
    def test_homogeneous_medium_hand_derived(self):
        case = self._fresh(ConstantField(0.01))
        sample = case.sample_adc(100)
        self.assertAlmostEqual(sample.channel_values[0], 2.0, delta=1e-9)
        self.assertAlmostEqual(sample.channel_values[1], 0.0, delta=1e-9)
        self.assertAlmostEqual(sample.channel_values[2], 0.0, delta=1e-9)
        unit = self._fresh(ConstantField(1.0))
        self.assertAlmostEqual(unit.sample_adc(100).channel_values[0], 0.0, delta=1e-9)

    def test_kernel_matches_independent_recomputation(self):
        orientation = quat_multiply(
            (0.0, math.sin(math.radians(17.5)), 0.0, math.cos(math.radians(17.5))),
            (math.sin(math.radians(7.5)), 0.0, 0.0, math.cos(math.radians(7.5))),
        )
        pose_obj = fp.Pose((0.5, -1.25, 0.75), orientation)
        field = BallField((1.0, -1.0, 4.0), 1.0)
        case = self._fresh(field, pose_obj=pose_obj)
        sample = case.sample_adc(100)
        expected = independent_channels(pose_obj.position_m, pose_obj.orientation_xyzw, field)
        for channel in (0, 1, 2):
            self.assertAlmostEqual(sample.channel_values[channel], expected[channel], delta=1e-9)

    def test_half_space_differentials_have_defined_signs(self):
        right = self._fresh(HalfSpaceField(0))
        sample = right.sample_adc(100)
        self.assertLess(sample.channel_values[1], -0.05)
        self.assertAlmostEqual(sample.channel_values[2], 0.0, delta=1e-9)
        up = self._fresh(HalfSpaceField(1))
        sample = up.sample_adc(100)
        self.assertLess(sample.channel_values[2], -0.05)
        self.assertAlmostEqual(sample.channel_values[1], 0.0, delta=1e-9)

    def test_moved_pose_changes_lobe_asymmetry(self):
        field = BallField((0.0, 0.0, 3.0), 1.0)
        ahead = self._fresh(field, pose_obj=identity_pose())
        sample_ahead = ahead.sample_adc(100)
        self.assertAlmostEqual(sample_ahead.channel_values[1], 0.0, delta=1e-9)
        self.assertAlmostEqual(sample_ahead.channel_values[2], 0.0, delta=1e-9)
        self.assertLess(sample_ahead.channel_values[0], 1.5)
        aside = self._fresh(field, pose_obj=identity_pose(-3.0, 0.0, 0.0))
        sample_aside = aside.sample_adc(100)
        self.assertLess(sample_aside.channel_values[1], -0.05)
        self.assertAlmostEqual(sample_aside.channel_values[2], 0.0, delta=1e-9)
        self.assertGreater(sample_aside.channel_values[0], sample_ahead.channel_values[0] + 0.2)

    def test_rotated_pose_flips_which_lobe_sees_the_object(self):
        straight = self._fresh(BallField((2.0, 0.0, 3.0), 1.0), pose_obj=identity_pose())
        self.assertLess(straight.sample_adc(100).channel_values[1], -0.05)
        turned = self._fresh(BallField((0.0, 0.0, 3.0), 1.0), pose_obj=yaw_pose(40.0))
        sample = turned.sample_adc(100)
        self.assertGreater(sample.channel_values[1], 0.05)
        self.assertAlmostEqual(sample.channel_values[2], 0.0, delta=1e-9)

    def test_quadrature_support_cropping_is_software_only(self):
        field = RecordingField(0.01)
        case = self._fresh(field)
        case.sample_adc(100)
        points = field.calls
        self.assertGreater(len(points), 3000)
        farthest = 0.0
        for x, y, z in points:
            r = math.sqrt(x * x + y * y + z * z)
            farthest = max(farthest, r)
            self.assertLessEqual(r, fp.SUPPORT_M + 1e-9)
            if r == 0.0:
                continue
            ux, uy, uz = x / r, y / r, z / r
            inside = any(
                ux * axis[0] + uy * axis[1] + uz * axis[2] >= COS_HALF_ANGLE - 1e-12
                for axis in _AXES
            )
            self.assertTrue(inside, (x, y, z))
        self.assertGreater(farthest, 7.5)

    def test_hidden_far_and_behind_changes_do_not_affect_prototype_input(self):
        def rule(x, y, z):
            if z > 12.0 or z < -1e-9:
                return 5.0
            return 0.01

        plain = self._fresh(ConstantField(0.01))
        hidden = self._fresh(ScriptedField(rule))
        self.assertEqual(plain.sample_adc(100).to_payload(), hidden.sample_adc(100).to_payload())

    def test_private_labels_do_not_change_records(self):
        first = BallField((0.0, 0.0, 3.0), 1.0, private_label="water-body-17")
        second = BallField((0.0, 0.0, 3.0), 1.0, private_label="casing-03")
        profile_a = self._fresh(first, em_rng=random.Random(3))
        profile_b = self._fresh(second, em_rng=random.Random(3))
        self.assertEqual(profile_a.sample_adc(100).to_payload(), profile_b.sample_adc(100).to_payload())
        self.assertEqual(profile_a.sample_adc(110).to_payload(), profile_b.sample_adc(110).to_payload())

    # --------------------------------------------------------------- temporal
    def test_20hz_acquisition_holds_to_100hz_without_scene_repeats(self):
        field = RecordingField(0.01)
        case = self._fresh(field, tick=100)
        calls_after_acquisition = len(field.calls)
        values = []
        for tick in (100, 110, 120, 130, 140):
            sample = case.sample_adc(tick)
            values.append(sample.channel_values[0])
            self.assertEqual(sample.em_tick_ms, 100)
            self.assertTrue(sample.is_valid(0))
            if tick == 100:
                self.assertFalse(sample.is_held(0))
            else:
                self.assertTrue(sample.is_held(0))
                self.assertTrue(sample.is_held(1))
                self.assertTrue(sample.is_held(2))
        self.assertEqual(len(set(values)), 1)
        self.assertEqual(len(field.calls), calls_after_acquisition)

    def test_held_reads_do_not_advance_em_noise(self):
        field = ConstantField(0.01)
        profile_a = self._fresh(field, tick=100, em_rng=random.Random(11))
        for tick in (110, 120, 130, 140):
            profile_a.sample_adc(tick)
        profile_a.acquire_em(150, identity_pose(), context="formation", sampler=field)
        sample_a = profile_a.sample_adc(150)
        profile_b = self._fresh(field, tick=100, em_rng=random.Random(11))
        profile_b.acquire_em(150, identity_pose(), context="formation", sampler=field)
        sample_b = profile_b.sample_adc(150)
        self.assertEqual(sample_a.channel_values[0], sample_b.channel_values[0])
        self.assertEqual(sample_a.channel_values[1], sample_b.channel_values[1])
        self.assertEqual(sample_a.channel_values[2], sample_b.channel_values[2])

    def test_first_order_response_agrees_with_hand_derived_100ms(self):
        step_target = 2.0 * (1.0 - math.exp(-1.0))
        selector = TickField({100: ConstantField(1.0), 150: ConstantField(0.01), 200: ConstantField(0.01)})
        case = self._fresh(selector.for_tick(100), tick=100)
        self.assertAlmostEqual(case.sample_adc(100).channel_values[0], 0.0, delta=1e-9)
        case.acquire_em(150, identity_pose(), context="formation", sampler=selector.for_tick(150))
        self.assertAlmostEqual(case.sample_adc(150).channel_values[0], 2.0 * (1.0 - math.exp(-0.5)), delta=1e-9)
        case.acquire_em(200, identity_pose(), context="formation", sampler=selector.for_tick(200))
        self.assertAlmostEqual(case.sample_adc(200).channel_values[0], step_target, delta=1e-9)
        skipped = self._fresh(selector.for_tick(100), tick=100)
        skipped.acquire_em(200, identity_pose(), context="formation", sampler=selector.for_tick(200))
        self.assertAlmostEqual(skipped.sample_adc(200).channel_values[0], step_target, delta=1e-9)

    def test_white_noise_and_random_walk_scaling(self):
        em_rng = NoiseStub(1.0)
        selector = TickField({100: ConstantField(1.0), 200: ConstantField(0.01)})
        case = self._fresh(selector.for_tick(100), tick=100, em_rng=em_rng)
        case.acquire_em(200, identity_pose(), context="formation", sampler=selector.for_tick(200))
        sample = case.sample_adc(200)
        expected = 2.0 * (1.0 - math.exp(-1.0)) + fp.WHITE_SIGMA_LOG10 + fp.RW_SIGMA_PER_SQRT_S * math.sqrt(0.1)
        self.assertAlmostEqual(sample.channel_values[0], expected, delta=1e-9)
        sigmas = [sigma for _mu, sigma in em_rng.calls]
        self.assertEqual([round(s, 12) for s in sigmas[:3]], [round(fp.WHITE_SIGMA_LOG10, 12)] * 3)
        self.assertEqual(
            [round(s, 12) for s in sigmas[3:]],
            [round(fp.WHITE_SIGMA_LOG10, 12)] * 3 + [round(fp.RW_SIGMA_PER_SQRT_S * math.sqrt(0.1), 12)] * 3,
        )
        self.assertTrue(all(mu == 0.0 for mu, _sigma in em_rng.calls))

    def test_heartbeat_gap_faults_and_recovers_without_fabrication(self):
        field = ConstantField(0.01)
        case = self._fresh(field, tick=100)
        at_200 = case.sample_adc(200)
        self.assertTrue(at_200.is_valid(0))
        self.assertTrue(at_200.is_held(0))
        faulted = case.sample_adc(210)
        self.assertFalse(faulted.is_valid(0))
        self.assertIsNone(faulted.channel_values[0])
        self.assertIsNone(faulted.em_tick_ms)
        self.assertTrue(faulted.source_fault)
        case.acquire_em(250, identity_pose(), context="formation", sampler=field)
        recovered = case.sample_adc(250)
        self.assertTrue(recovered.is_valid(0))
        self.assertFalse(recovered.is_held(0))
        self.assertFalse(recovered.source_fault)
        self.assertEqual(recovered.em_tick_ms, 250)

    def test_future_acquisition_is_never_reported_to_an_earlier_read(self):
        field = ConstantField(0.01)
        case = self._fresh(field, tick=100)
        self.assertEqual(case.sample_adc(110).em_tick_ms, 100)
        case.acquire_em(150, identity_pose(), context="formation", sampler=field)
        with self.assertRaises(ValueError):
            case.sample_adc(140)
        fresh = case.sample_adc(150)
        self.assertEqual(fresh.em_tick_ms, 150)
        self.assertFalse(fresh.is_held(0))
        held = case.sample_adc(160)
        self.assertEqual(held.em_tick_ms, 150)
        self.assertTrue(held.is_held(0))

    # -------------------------------------------------------------- vibration
    def test_vibration_startup_window_is_invalid_not_invented(self):
        case = self._fresh(ConstantField(0.01), tick=0)
        for tick in range(0, 90, 10):
            sample = case.sample_adc(tick)
            self.assertFalse(sample.is_valid(3))
            self.assertIsNone(sample.channel_values[3])
            self.assertIsNone(sample.channel_counts[3])
        ready = case.sample_adc(90)
        self.assertTrue(ready.is_valid(3))
        self.assertEqual(ready.channel_values[3], 0.0)

    def test_vibration_gap_requires_fresh_window(self):
        case = self._fresh(ConstantField(0.01), tick=0)
        for tick in range(0, 100, 10):
            sample = case.sample_adc(tick)
        self.assertTrue(sample.is_valid(3))
        gap = case.sample_adc(200)
        self.assertFalse(gap.is_valid(3))
        self.assertIsNone(gap.channel_values[3])
        for tick in range(210, 290, 10):
            self.assertFalse(case.sample_adc(tick).is_valid(3))
        self.assertTrue(case.sample_adc(290).is_valid(3))

    def test_vibration_contact_step_uses_100ms_bandlimited_rms(self):
        case = self._fresh(ConstantField(0.01), tick=0)
        a = fp.VIB_AR_A
        samples = [0.0] * 10
        state = 0.0
        for _ in range(10):
            state = a * state + (1.0 - a) * 1.0
            samples.append(min(max(state, -fp.VIB_RANGE_G), fp.VIB_RANGE_G))
        expected = [
            math.sqrt(sum(value * value for value in samples[max(0, index - 9):index + 1]) / 10.0)
            for index in range(len(samples))
        ]
        self.assertAlmostEqual(expected[10], math.sqrt((1.0 - a) ** 2 / 10.0), delta=1e-12)
        for index, tick in enumerate(range(0, 200, 10)):
            value = case.sample_adc(tick, contact_accel_g=1.0 if tick >= 100 else None).channel_values[3]
            if index < 9:
                self.assertIsNone(value, tick)
            else:
                self.assertAlmostEqual(value, expected[index], delta=1e-9, msg=tick)

    def test_vibration_saturates_at_full_scale_and_stays_bounded(self):
        field = ConstantField(0.01)
        case = self._fresh(field, tick=0)
        for tick in range(10, 100, 10):
            case.sample_adc(tick)
        for tick in range(100, 210, 10):
            if tick % 50 == 0:
                case.acquire_em(tick, identity_pose(), context="formation", sampler=field)
            sample = case.sample_adc(tick, contact_accel_g=4.0)
        self.assertEqual(sample.channel_values[3], fp.VIB_RANGE_G)
        self.assertTrue(sample.is_saturated(3))
        self.assertEqual(sample.channel_counts[3], fp.COUNTS_MAX)
        self.assertFalse(sample.source_fault)
        edge = self._fresh(field, tick=0)
        for tick in range(10, 300, 10):
            if tick % 50 == 0:
                edge.acquire_em(tick, identity_pose(), context="formation", sampler=field)
            sample = edge.sample_adc(tick, contact_accel_g=2.0)
        self.assertLess(sample.channel_values[3], fp.VIB_RANGE_G)
        self.assertFalse(sample.is_saturated(3))

    def test_vibration_only_responds_to_current_contact(self):
        field = BallField((0.0, 0.0, 1.0), 0.5)
        case = fp.ForwardProfile(em_rng=random.Random(5), vibration_rng=random.Random(6))
        for tick in range(0, 300, 10):
            if tick % 50 == 0:
                case.acquire_em(tick, identity_pose(), context="formation", sampler=field)
            sample = case.sample_adc(tick)
            if sample.is_valid(3):
                self.assertLessEqual(sample.channel_values[3], 0.002, tick)
        for tick in range(300, 400, 10):
            if tick % 50 == 0:
                case.acquire_em(tick, identity_pose(), context="formation", sampler=field)
            sample = case.sample_adc(tick, contact_accel_g=0.5)
        self.assertGreater(sample.channel_values[3], 0.05)

    # ---------------------------------------------------- record and quality
    def test_payload_whitelist_and_json_safety(self):
        case = self._fresh(ConstantField(0.01), em_rng=random.Random(1))
        payload = case.sample_adc(100).to_payload()
        self.assertEqual(set(payload.keys()), PAYLOAD_KEYS)
        self.assertEqual(payload["profile_status"], fp.PROFILE_STATUS)
        self.assertEqual(payload["source_mode"], fp.SOURCE_MODE)
        self.assertEqual(payload["profile_id"], fp.PROFILE_ID)
        self.assertIn("candidate_only", payload["profile_status"])
        self.assertIn("twin_fixture", payload["source_mode"])
        self.assertIn("not_calibrated", payload["profile_note"])
        self.assertIn("not_em_surrogate_v2", payload["profile_note"])
        self.assertEqual(len(payload["channel_values"]), 4)
        self.assertEqual(len(payload["channel_counts"]), 4)
        self.assertIsInstance(payload["quality"], int)
        self.assertGreaterEqual(payload["quality"], 0)
        self.assertEqual(payload["quality"] & 0xE000, 0)
        text = json.dumps(payload)
        self.assertEqual(json.loads(text), payload)
        lowered = text.lower()
        for token in FORBIDDEN_PAYLOAD_TOKENS:
            self.assertNotIn(token, lowered)

    def test_invalid_channels_are_explicit_nulls_never_plausible_zeros(self):
        case = fp.ForwardProfile(em_rng=NoiseStub(0.0), vibration_rng=NoiseStub(0.0))
        sample = case.sample_adc(0)
        for channel in (0, 1, 2):
            self.assertIsNone(sample.channel_values[channel])
            self.assertIsNone(sample.channel_counts[channel])
            self.assertFalse(sample.is_valid(channel))
        self.assertIsNone(sample.channel_values[3])
        self.assertTrue(sample.source_fault)

    def test_quality_bits_layout_valid_saturated_held_fault(self):
        field = ConstantField(0.01)
        case = self._fresh(field, tick=100)
        qualities = {}
        for tick in range(100, 280, 10):
            if tick == 250:
                case.acquire_em(tick, identity_pose(), context="formation", sampler=field)
            qualities[tick] = case.sample_adc(tick).quality
            self.assertEqual(qualities[tick] & (1 << 11), 0, tick)
        self.assertEqual(qualities[100], 0x0007)
        self.assertEqual(qualities[190], 0x070F)
        self.assertEqual(qualities[200], 0x070F)
        self.assertEqual(qualities[210], 0x1008)
        self.assertEqual(qualities[240], 0x1008)
        self.assertEqual(qualities[250], 0x000F)
        self.assertEqual(qualities[260], 0x070F)

    def test_counts_map_to_frozen_ranges(self):
        case = self._fresh(ConstantField(0.01))
        sample = case.sample_adc(100)
        span = fp.LOG10_RHO_MAX - fp.LOG10_RHO_MIN
        expected_c0 = round((2.0 - fp.LOG10_RHO_MIN) / span * fp.COUNTS_MAX)
        self.assertEqual(sample.channel_counts[0], expected_c0)
        self.assertIsNone(sample.channel_counts[3])
        for channel in (0, 1, 2):
            self.assertGreaterEqual(sample.channel_counts[channel], 0)
            self.assertLessEqual(sample.channel_counts[channel], fp.COUNTS_MAX)

    def test_saturation_clips_and_flags_without_faulting(self):
        case = fp.ForwardProfile(em_rng=NoiseStub(1000.0), vibration_rng=NoiseStub(0.0))
        case.acquire_em(100, identity_pose(), context="formation", sampler=ConstantField(0.01))
        sample = case.sample_adc(100)
        self.assertTrue(sample.is_valid(0))
        self.assertFalse(sample.source_fault)
        self.assertAlmostEqual(sample.channel_values[0], fp.LOG10_RHO_MAX, delta=1e-12)
        self.assertTrue(sample.is_saturated(0))
        self.assertEqual(sample.channel_counts[0], fp.COUNTS_MAX)
        for channel in (1, 2):
            self.assertTrue(sample.is_saturated(channel))
            self.assertLessEqual(abs(sample.channel_values[channel]), fp.DIFF_LIMIT + 1e-12)

    def test_rng_streams_are_independent_and_channel_indices_checked(self):
        shared = NoiseStub(0.0)
        with self.assertRaises(ValueError):
            fp.ForwardProfile(em_rng=shared, vibration_rng=shared)
        case = self._fresh(ConstantField(0.01))
        with self.assertRaises(ValueError):
            case.sample_adc(100).is_valid(4)
        with self.assertRaises(ValueError):
            case.sample_adc(110).is_held(-1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
