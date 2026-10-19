"""Tests for the pure host-clock arithmetic reference (red-first).

Contract: competition/deepeye/docs/host_timing_contract.md revision 1,
DEEPEYE-IMPLEMENTATION-20261014/v1. Pure stdlib, pure integer arithmetic.
"""

import importlib.util
import sys
import unittest
from dataclasses import fields
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("clock_bounds.py")

spec = importlib.util.spec_from_file_location("host_timing_reference", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load reference module from %s" % MODULE_PATH)
ref = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ref
spec.loader.exec_module(ref)

SESSION = 7
BOOT = "ab" * 32
TICK = 1000


def fast_bounds(**overrides):
    values = dict(
        total_delay_lower_ns=200_000,
        total_delay_upper_ns=400_000,
        tick_quantum_upper_ns=1_000_100,
        rate_error_ppm=50,
        max_anchor_age_ns=1_500_000_000,
    )
    values.update(overrides)
    return ref.ClockBounds(**values)


def fast_anchor(receipt_lo=5_000_000, receipt_hi=6_000_000, tick_ms=TICK, session=SESSION, boot=BOOT, bounds=None):
    return ref.make_anchor(
        session=session,
        boot_sha256=boot,
        tick_ms=tick_ms,
        receipt_lo_ns=receipt_lo,
        receipt_hi_ns=receipt_hi,
        bounds=bounds if bounds is not None else fast_bounds(),
    )


class IntervalTests(unittest.TestCase):
    def test_interval_accepts_closed_range(self):
        iv = ref.Interval(3, 3)
        self.assertEqual((iv.lo_ns, iv.hi_ns), (3, 3))

    def test_interval_rejects_empty_and_negative(self):
        with self.assertRaises(ValueError):
            ref.Interval(5, 4)
        with self.assertRaises(ValueError):
            ref.Interval(-1, 4)

    def test_interval_rejects_bool_and_none(self):
        with self.assertRaises(TypeError):
            ref.Interval(True, 4)
        with self.assertRaises(TypeError):
            ref.Interval(None, 4)
        with self.assertRaises(TypeError):
            ref.Interval(0, False)


class ClockBoundsTests(unittest.TestCase):
    def test_bounds_accepts_boundary_values(self):
        bounds = fast_bounds(rate_error_ppm=0, tick_quantum_upper_ns=1_000_000)
        self.assertEqual(bounds.rate_error_ppm, 0)
        edge = fast_bounds(rate_error_ppm=999_999, tick_quantum_upper_ns=1_999_999)
        self.assertEqual(edge.tick_quantum_upper_ns, 1_999_999)

    def test_bounds_requires_quantum_floor(self):
        with self.assertRaises(ValueError):
            fast_bounds(tick_quantum_upper_ns=1_000_049)
        fast_bounds(tick_quantum_upper_ns=1_000_050)

    def test_bounds_rejects_rate_out_of_range(self):
        with self.assertRaises(ValueError):
            fast_bounds(rate_error_ppm=-1)
        with self.assertRaises(ValueError):
            fast_bounds(rate_error_ppm=1_000_000)
        with self.assertRaises(TypeError):
            fast_bounds(rate_error_ppm=True)

    def test_bounds_rejects_delay_order_and_negative(self):
        with self.assertRaises(ValueError):
            fast_bounds(total_delay_lower_ns=400_001)
        with self.assertRaises(ValueError):
            fast_bounds(total_delay_lower_ns=-1)
        with self.assertRaises(TypeError):
            fast_bounds(total_delay_upper_ns=None)

    def test_bounds_age_limits(self):
        limit = (2 ** 31 - 1) * 1_000_000
        self.assertEqual(fast_bounds(max_anchor_age_ns=limit).max_anchor_age_ns, limit)
        with self.assertRaises(ValueError):
            fast_bounds(max_anchor_age_ns=limit + 1)
        with self.assertRaises(ValueError):
            fast_bounds(max_anchor_age_ns=0)

    def test_bounds_reject_none(self):
        with self.assertRaises(TypeError):
            ref.ClockBounds(None, 1, 2_000_000, 0, 1)


class AnchorTests(unittest.TestCase):
    def test_make_anchor_main_formula_and_expiry(self):
        anchor = fast_anchor()
        self.assertEqual(anchor.derived_interval.lo_ns, 3_599_900)
        self.assertEqual(anchor.derived_interval.hi_ns, 5_800_000)
        self.assertEqual(anchor.valid_until, 5_000_000 + 1_500_000_000)

    def test_make_anchor_clips_negative_lower_to_zero(self):
        anchor = fast_anchor(receipt_lo=100_000, receipt_hi=900_000)
        self.assertEqual(anchor.derived_interval.lo_ns, 0)
        self.assertEqual(anchor.derived_interval.hi_ns, 700_000)

    def test_make_anchor_rejects_negative_upper(self):
        with self.assertRaises(ValueError):
            fast_anchor(receipt_lo=0, receipt_hi=100_000)

    def test_make_anchor_rejects_identity_and_types(self):
        with self.assertRaises(TypeError):
            fast_anchor(session=None)
        with self.assertRaises(ValueError):
            fast_anchor(session=2 ** 32)
        with self.assertRaises(ValueError):
            fast_anchor(boot="AB" * 32)
        with self.assertRaises(ValueError):
            fast_anchor(boot="ab" * 31)
        with self.assertRaises(TypeError):
            fast_anchor(boot=None)
        with self.assertRaises(TypeError):
            fast_anchor(tick_ms=True)
        with self.assertRaises(ValueError):
            fast_anchor(tick_ms=2 ** 32)
        with self.assertRaises(TypeError):
            fast_anchor(tick_ms="1000")
        with self.assertRaises(TypeError):
            ref.make_anchor(session=SESSION, boot_sha256=BOOT, tick_ms=TICK,
                            receipt_lo_ns=5, receipt_hi_ns=None, bounds=fast_bounds())
        with self.assertRaises(TypeError):
            ref.make_anchor(session=SESSION, boot_sha256=BOOT, tick_ms=TICK,
                            receipt_lo_ns=5, receipt_hi_ns=6, bounds=None)
        with self.assertRaises(TypeError):
            ref.make_anchor(session=SESSION, boot_sha256=BOOT, tick_ms=TICK,
                            receipt_lo_ns=5, receipt_hi_ns=6, bounds=fast_bounds(), unknown=1)

    def test_constructor_cannot_forge_derived_fields(self):
        with self.assertRaises(TypeError):
            ref.Anchor(session=SESSION, boot_sha256=BOOT, tick_ms=TICK,
                       receipt_interval=ref.Interval(5, 6), bounds=fast_bounds(),
                       derived_interval=ref.Interval(0, 0))
        with self.assertRaises(TypeError):
            ref.Anchor(session=SESSION, boot_sha256=BOOT, tick_ms=TICK,
                       receipt_interval=ref.Interval(5, 6), bounds=fast_bounds(),
                       valid_until=1)
        init_state = {f.name: f.init for f in fields(ref.Anchor)}
        self.assertFalse(init_state["derived_interval"])
        self.assertFalse(init_state["valid_until"])


class MapTickTests(unittest.TestCase):
    def test_forward_mapping_exact_interval(self):
        anchor = fast_anchor()
        got = ref.map_tick(anchor, SESSION, BOOT, TICK + 30, 40_000_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (33_598_400, 36_801_600))
        self.assertIs(type(got.lo_ns), int)
        self.assertIs(type(got.hi_ns), int)

    def test_upper_bound_may_exceed_now_but_lower_must_not(self):
        anchor = fast_anchor()
        got = ref.map_tick(anchor, SESSION, BOOT, TICK + 30, 35_000_000)
        self.assertGreater(got.hi_ns, 35_000_000)
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, BOOT, TICK + 30, 33_000_000)

    def test_containment_of_true_sample_times(self):
        anchor = fast_anchor()
        got = ref.map_tick(anchor, SESSION, BOOT, TICK + 30, 40_000_000)
        delta_ns = 30_000_000
        err = 1_500
        for base in (3_599_900, 4_000_000, 5_800_000):
            for drift in (-err, 0, err):
                true_time = base + delta_ns + drift
                self.assertLessEqual(got.lo_ns, true_time)
                self.assertLessEqual(true_time + 1_000_100, got.hi_ns)

    def test_ceiling_drift_is_integer_exact(self):
        bounds = fast_bounds(rate_error_ppm=1, tick_quantum_upper_ns=1_000_001)
        anchor = fast_anchor(bounds=bounds)
        got = ref.map_tick(anchor, SESSION, BOOT, TICK + 1, 40_000_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (3_599_999 + 1_000_000 - 1, 5_800_000 + 1_000_000 + 1 + 1_000_001))

    def test_delayed_sample_before_anchor_allowed_but_bounded(self):
        anchor = fast_anchor()
        got = ref.map_tick(anchor, SESSION, BOOT, TICK - 5, 40_000_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (0, 1_800_350))
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, BOOT, TICK - 40, 40_000_000)

    def test_large_clock_is_float_free(self):
        bounds = fast_bounds(max_anchor_age_ns=2_147_483_647_000_000)
        anchor = fast_anchor(tick_ms=3_999_000_000, bounds=bounds)
        got = ref.map_tick(anchor, SESSION, BOOT, 4_000_000_000, 1_000_100_000_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (999_953_599_900, 1_000_056_800_100))
        self.assertIs(type(got.lo_ns), int)
        self.assertIs(type(got.hi_ns), int)

    def test_wrap_and_half_wrap(self):
        anchor = fast_anchor(tick_ms=0xFFFFFFF0)
        got = ref.map_tick(anchor, SESSION, BOOT, 0x00000010, 40_000_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (35_598_300, 38_801_700))
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, BOOT, (0xFFFFFFF0 + 2 ** 31) % 2 ** 32, 40_000_000)

    def test_expired_and_regressing_now(self):
        anchor = fast_anchor()
        boundary = ref.map_tick(anchor, SESSION, BOOT, TICK, anchor.valid_until)
        self.assertIsInstance(boundary, ref.Interval)
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, BOOT, TICK, anchor.valid_until + 1)
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, BOOT, TICK, anchor.receipt_interval.hi_ns - 1)

    def test_identity_mismatch_and_bad_arguments(self):
        anchor = fast_anchor()
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION + 1, BOOT, TICK, 40_000_000)
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, "cd" * 32, TICK, 40_000_000)
        with self.assertRaises(TypeError):
            ref.map_tick(anchor, SESSION, BOOT, TICK, "40")
        with self.assertRaises(TypeError):
            ref.map_tick(anchor, SESSION, BOOT, TICK, None)
        with self.assertRaises(TypeError):
            ref.map_tick(anchor, SESSION, BOOT, True, 40_000_000)
        with self.assertRaises(TypeError):
            ref.map_tick(None, SESSION, BOOT, TICK, 40_000_000)
        with self.assertRaises(ValueError):
            ref.map_tick(anchor, SESSION, "AB" * 32, TICK, 40_000_000)


class AdcWindowTests(unittest.TestCase):
    def test_nominal_spans_are_not_frame_times(self):
        self.assertEqual(ref.adc_window_nominal_span_ns(50), 490_000_000)
        self.assertEqual(ref.adc_window_nominal_span_ns(800), 7_990_000_000)
        with self.assertRaises(ValueError):
            ref.adc_window_nominal_span_ns(0)
        with self.assertRaises(TypeError):
            ref.adc_window_nominal_span_ns(True)

    def test_first_sample_interval_from_measured_period(self):
        got = ref.adc_first_sample_interval(ref.Interval(499_000_000, 499_600_000), 50, 9_999_000, 10_001_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (8_951_000, 9_649_000))

    def test_single_sample_and_no_concealment(self):
        last = ref.Interval(100, 200)
        got = ref.adc_first_sample_interval(last, 1, 9_999_000, 10_001_000)
        self.assertEqual((got.lo_ns, got.hi_ns), (100, 200))
        with self.assertRaises(ValueError):
            ref.adc_first_sample_interval(last, 0, 1, 2)
        with self.assertRaises(ValueError):
            ref.adc_first_sample_interval(last, 2, 10_001_000, 9_999_000)
        with self.assertRaises(TypeError):
            ref.adc_first_sample_interval(None, 2, 1, 2)

    def test_window_helper_stays_integer_on_large_clock(self):
        got = ref.adc_first_sample_interval(ref.Interval(2 ** 53, 2 ** 53 + 1_000), 800, 9_999_999, 10_000_001)
        self.assertIs(type(got.lo_ns), int)
        self.assertEqual(got.hi_ns, 2 ** 53 + 1_000 - 799 * 9_999_999)

    def test_no_em_inference_api(self):
        for banned in ("em_time", "native_em", "em_update_time"):
            self.assertFalse(hasattr(ref, banned))


if __name__ == "__main__":
    unittest.main(verbosity=2)
