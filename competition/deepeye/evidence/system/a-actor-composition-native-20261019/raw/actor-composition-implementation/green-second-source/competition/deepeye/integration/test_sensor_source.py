"""Adversarial source boundary tests; actual ForwardProfile outputs, software only.

Run: python -B competition/deepeye/integration/test_sensor_source.py -v
No physical calibration, DAC/XADC, transport, G03 or G09 acceptance claim.
"""
import copy
import functools
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
MODULE = HERE.with_name('sensor_source.py')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fp = load('source_boundary_forward_fixture', HERE.parents[1] / 'simulation/sensors/forward_profile.py')
ref = load('source_boundary_under_test', MODULE) if MODULE.exists() else None


class TestNoise:
    """Deterministic noise input for software tests, not measured sensor noise."""
    def __init__(self, value=0.0):
        self.value = value

    def gauss(self, mu, sigma):
        return self.value


@functools.lru_cache(maxsize=None)
def records(end=300, failed_tick=None, failed_from=None, adc_gap=None, saturation=False, em_noise=0.0):
    model = fp.ForwardProfile(em_rng=TestNoise(em_noise), vibration_rng=TestNoise())
    pose = fp.Pose((0, 0, 0), (0, 0, 0, 1))
    output = {}
    for tick in range(0, end + 1, 10):
        if tick % 50 == 0:
            model.acquire_em(tick, pose, context='formation',
                             sampler=lambda x, y, z: None if (tick == failed_tick or
                                 failed_from is not None and tick >= failed_from) else 0.01)
        if tick != adc_gap:
            output[tick] = model.sample_adc(tick, contact_accel_g=100.0 if saturation else None).to_payload()
    return output


def record(tick=0, **options):
    return copy.deepcopy(records(**options)[tick])


class ImplementationTest(unittest.TestCase):
    def test_candidate_source_boundary_exists(self):
        self.assertTrue(MODULE.is_file(), 'RED: candidate source validator/ledger not implemented')


@unittest.skipIf(ref is None, 'candidate validator absent: existence test supplies RED')
class RecordValidationTests(unittest.TestCase):
    def test_accepts_unmodified_real_model_stream(self):
        for payload in records().values():
            result = ref.validate_record(payload)
            self.assertEqual(result.adc_tick_ms, payload['adc_tick_ms'])
            self.assertEqual(result.channel_counts, tuple(payload['channel_counts']))

    def test_exact_whitelist_rejects_truth_or_control_fields(self):
        for key in ('object_id', 'obstacle_position', 'map_seed', 'collision', 'distance',
                    'editor_history', 'screen', 'future_sensor', 'motion_command', 'run_id'):
            payload = record(); payload[key] = 'forbidden'
            with self.subTest(key=key), self.assertRaises(ValueError):
                ref.validate_record(payload)
        for key in record():
            payload = record(); del payload[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                ref.validate_record(payload)

    def test_metadata_cannot_upgrade_candidate_to_calibrated_or_another_mode(self):
        for key, value in (('profile_id', 'em_surrogate_v2'), ('profile_status', 'calibrated'),
                           ('profile_note', 'physical_pass'), ('source_mode', 'sensor_live')):
            payload = record(); payload[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                ref.validate_record(payload)

    def test_exact_json_types_reject_boolean_integer_impersonation(self):
        for key in ('adc_tick_ms', 'em_tick_ms', 'quality'):
            for value in (True, False, 0.0, '0'):
                payload = record(); payload[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    ref.validate_record(payload)
        for key in ('channel_values', 'channel_counts'):
            payload = record(); payload[key][0] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                ref.validate_record(payload)

    def test_non_finite_nested_and_bad_vector_shapes_rejected(self):
        for value in (math.nan, math.inf, -math.inf, {'truth': [1, 2, 3]}, '2', True):
            payload = record(); payload['channel_values'][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.validate_record(payload)
        for value in (None, (), [1, 2, 3], [1, 2, 3, 4, 5], {'0': 2}):
            payload = record(); payload['channel_values'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.validate_record(payload)

    def test_counts_match_values_and_validity(self):
        for value in (-1, 4096, 1.5, '2048', True, None):
            payload = record(); payload['channel_counts'][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.validate_record(payload)
        payload = record(); payload['channel_counts'][0] += 1
        with self.assertRaises(ValueError):
            ref.validate_record(payload)

    def test_all_channel_ranges_and_count_types_are_checked(self):
        for channel, value in enumerate((4.0, -2.01, 2.01, -0.01)):
            payload = record(90); payload['channel_values'][channel] = value
            with self.subTest(channel=channel), self.assertRaises(ValueError):
                ref.validate_record(payload)
        payload = record(); payload['quality'] = -1
        with self.assertRaises(ValueError):
            ref.validate_record(payload)
        payload = record(90); payload['channel_counts'] = tuple(payload['channel_counts'])
        with self.assertRaises(ValueError):
            ref.validate_record(payload)
        payload = record(0, failed_tick=0); payload['channel_values'][0] = 2.0
        with self.assertRaises(ValueError):
            ref.validate_record(payload)

    def test_quality_reserved_partial_em_and_false_fault_rejected(self):
        for mask in (1 << 13, 1 << 14, 1 << 15, 1 << 11, 1 << 12, 1):
            payload = record(); payload['quality'] ^= mask
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                ref.validate_record(payload)
        payload = record(0, failed_tick=0); payload['quality'] &= ~(1 << 12)
        with self.assertRaises(ValueError):
            ref.validate_record(payload)

    def test_saturation_requires_validity_and_em_endpoint(self):
        payload = record(); payload['quality'] |= 1 << 4
        with self.assertRaises(ValueError):
            ref.validate_record(payload)
        payload = record(); payload['quality'] |= 1 << 7
        with self.assertRaises(ValueError):
            ref.validate_record(payload)
        # A vibration RMS can be saturated because one window sample clipped;
        # the RMS itself need not equal the endpoint.
        ref.validate_record(record(90, saturation=True))

    def test_future_off_grid_negative_out_of_range_and_stale_ticks_rejected(self):
        for key, value in (('adc_tick_ms', -10), ('adc_tick_ms', 1),
                           ('adc_tick_ms', 2147483650), ('em_tick_ms', 50),
                           ('em_tick_ms', -50), ('em_tick_ms', 10)):
            payload = record(); payload[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ref.validate_record(payload)
        payload = record(10); payload['adc_tick_ms'] = 110
        with self.assertRaises(ValueError):
            ref.validate_record(payload)

    def test_hold_bits_track_original_em_time(self):
        payload = record(10); payload['quality'] &= ~0x700
        with self.assertRaises(ValueError):
            ref.validate_record(payload)
        payload = record(); payload['quality'] |= 0x700
        with self.assertRaises(ValueError):
            ref.validate_record(payload)

    def test_source_fault_may_keep_real_vibration_but_no_em(self):
        payload = record(150, failed_tick=150)
        result = ref.validate_record(payload)
        self.assertEqual(result.quality, 0x1008)
        self.assertEqual(result.channel_values[:3], (None, None, None))
        self.assertIsNotNone(result.channel_values[3])

    def test_actual_saturated_model_em_and_vibration_records_are_accepted(self):
        payload = record(90, em_noise=100.0, saturation=True)
        self.assertEqual(payload['channel_counts'], [4095, 4095, 4095, 4095])
        ref.validate_record(payload)

    def test_strict_json_rejects_duplicate_keys_nonfinite_and_extra_fields(self):
        raw = json.dumps(record())
        nonfinite = record(); nonfinite['channel_values'][0] = math.nan
        ref.validate_json(raw)
        for malformed in (raw[:-1] + ', "quality":7}', json.dumps(nonfinite),
                          raw[:-1] + ', "map_seed":1}', '[1,2,3]', 'null', b'\xff'):
            with self.subTest(raw=repr(malformed)[:100]), self.assertRaises(ValueError):
                ref.validate_json(malformed)

    def test_validated_record_is_detached_and_immutable(self):
        payload = record()
        validated = ref.validate_record(payload)
        original = validated.channel_values[0]
        payload['channel_values'][0] = 0.0
        self.assertEqual(validated.channel_values[0], original)
        with self.assertRaises((AttributeError, TypeError)):
            validated.adc_tick_ms = 100


@unittest.skipIf(ref is None, 'candidate validator absent: existence test supplies RED')
class SourceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = ref.SourceLedger(start_tick_ms=0, start_monotonic_ns=1_000_000_000)

    def accept(self, tick, *, payload=None, delay_ms=0):
        return self.ledger.accept(record(tick) if payload is None else payload,
            received_monotonic_ns=1_000_000_000 + (tick + delay_ms) * 1_000_000)

    def test_100hz_adc_does_not_claim_100hz_native_em(self):
        admitted = [self.accept(tick) for tick in range(0, 301, 10)]
        self.assertEqual(sum(a.new_em_sample for a in admitted), 7)
        self.assertEqual(self.ledger.snapshot.accepted_records, 31)
        self.assertEqual(self.ledger.snapshot.native_em_acquisitions, 7)

    def test_duplicate_reverse_and_delayed_backfill_do_not_renew_health(self):
        self.accept(0); self.accept(20)
        before = self.ledger.snapshot
        for tick in (20, 0, 10):
            with self.subTest(tick=tick), self.assertRaises(ValueError):
                self.ledger.accept(record(tick), received_monotonic_ns=1_050_000_000)
        self.assertEqual(self.ledger.snapshot, before)
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_101_000_000))

    def test_future_claim_rejected_against_independent_receiver_clock(self):
        self.accept(0)
        before = self.ledger.snapshot
        with self.assertRaises(ValueError):
            self.ledger.accept(record(50), received_monotonic_ns=1_049_999_999)
        self.assertEqual(self.ledger.snapshot, before)
        self.accept(50)

    def test_fast_burst_cannot_invent_20hz_elapsed_acquisitions(self):
        self.accept(0)
        for tick in (50, 100, 150):
            with self.subTest(tick=tick), self.assertRaises(ValueError):
                self.ledger.accept(record(tick), received_monotonic_ns=1_001_000_000)
        self.assertEqual(self.ledger.snapshot.native_em_acquisitions, 1)

    def test_stale_adc_record_cannot_reanimate_source(self):
        with self.assertRaises(ValueError):
            self.accept(0, delay_ms=101)
        self.assertEqual(self.ledger.snapshot.accepted_records, 0)
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_101_000_000))

    def test_held_em_cannot_mutate_value_count_or_saturation(self):
        self.accept(0)
        payload = record(10)
        payload['channel_values'][0] = 1.0
        payload['channel_counts'][0] = 1739  # independently rounded from log10 range
        with self.assertRaises(ValueError):
            self.accept(10, payload=payload)
        self.accept(10)

    def test_held_saturation_cannot_be_cleared(self):
        self.accept(0, payload=record(0, em_noise=100.0))
        payload = record(10, em_noise=100.0)
        payload['quality'] &= ~(1 << 4)
        ref.validate_record(payload)  # individually plausible endpoint without clipping
        with self.assertRaises(ValueError):
            self.accept(10, payload=payload)

    def test_new_em_must_be_seen_at_its_actual_adc_slot(self):
        self.accept(0)
        with self.assertRaises(ValueError):
            self.accept(60)  # cannot first introduce the unreceived 50ms acquisition
        self.assertEqual(self.ledger.snapshot.native_em_acquisitions, 1)

    def test_fault_invalidates_hold_until_new_real_slot(self):
        for tick in range(0, 50, 10):
            self.accept(tick)
        self.accept(50, payload=record(50, failed_tick=50))
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_050_000_000))
        payload = record(10); payload['adc_tick_ms'] = 60
        with self.assertRaises(ValueError):
            self.accept(60, payload=payload)
        for tick in range(60, 101, 10):
            self.accept(tick, payload=record(tick, failed_tick=50))
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_100_000_000))

    def test_valid_fault_records_do_not_flip_source_heartbeat(self):
        self.accept(0)
        for tick in range(10, 151, 10):
            self.accept(tick, payload=record(tick, failed_from=50))
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_150_000_000))
        self.assertEqual(self.ledger.snapshot.last_healthy_received_ns, 1_040_000_000)

    def test_heartbeat_100ms_boundary_and_uart_like_fields(self):
        self.accept(0)
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_100_000_000))
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_100_000_001))
        payload = record(10); payload['state_heartbeat'] = True
        with self.assertRaises(ValueError):
            self.accept(10, payload=payload)

    def test_held_delivery_does_not_move_original_em_deadline(self):
        self.accept(0, delay_ms=90)
        self.accept(10, delay_ms=90)
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_100_000_000))
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_100_000_001))

    def test_missing_adc_slot_resets_observable_vibration_window(self):
        # Use a real producer ADC gap at 20ms, before an EM slot.
        for tick, payload in records(adc_gap=20).items():
            self.accept(tick, payload=payload)
        self.assertEqual(self.ledger.snapshot.accepted_records, 30)

    def test_fabricated_vibration_valid_after_transport_gap_rejected(self):
        for tick in range(0, 90, 10):
            if tick != 20:
                self.accept(tick)
        with self.assertRaises(ValueError):
            self.accept(90)  # producer has 10 samples, receiver has only 7 contiguous

    def test_receiver_time_reversal_and_boolean_clocks_rejected(self):
        self.accept(0, delay_ms=1)
        before = self.ledger.snapshot
        for now in (1_000_000_000, True, 1.0, -1):
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.ledger.accept(record(10), received_monotonic_ns=now)
        self.assertEqual(self.ledger.snapshot, before)
        with self.assertRaises(ValueError):
            self.ledger.healthy(now_monotonic_ns=1_000_000_000)

    def test_expired_health_query_cannot_reverse_to_healthy(self):
        self.accept(0)
        before = self.ledger.snapshot
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        with self.assertRaises(ValueError):
            self.ledger.healthy(now_monotonic_ns=1_090_000_000)
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        self.assertEqual(self.ledger.snapshot, before)

    def test_accept_cannot_reverse_below_latest_health_query(self):
        self.accept(0)
        before = self.ledger.snapshot
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        # This new EM50 record is individually fresh at receive90; the earlier
        # receive time must still be rejected after an observed health110 query.
        with self.assertRaises(ValueError):
            self.ledger.accept(record(50), received_monotonic_ns=1_090_000_000)
        self.assertEqual(self.ledger.snapshot, before)

    def test_accept_json_cannot_reverse_below_latest_health_query(self):
        self.accept(0)
        before = self.ledger.snapshot
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        with self.assertRaises(ValueError):
            self.ledger.accept_json(json.dumps(record(50)), received_monotonic_ns=1_090_000_000)
        self.assertEqual(self.ledger.snapshot, before)

    def test_rejected_payload_still_observes_trusted_clock_without_sample_mutation(self):
        for attack in ('unknown_field', 'future_sample', 'duplicate'):
            with self.subTest(attack=attack):
                ledger = ref.SourceLedger(start_tick_ms=0, start_monotonic_ns=1_000_000_000)
                ledger.accept(record(), received_monotonic_ns=1_000_000_000)
                before = ledger.snapshot
                payload = record(150) if attack == 'future_sample' else record()
                if attack == 'unknown_field':
                    payload['map_seed'] = 9
                with self.assertRaises(ValueError):
                    ledger.accept(payload, received_monotonic_ns=1_110_000_000)
                self.assertEqual(ledger.snapshot, before)
                with self.assertRaises(ValueError):
                    ledger.healthy(now_monotonic_ns=1_090_000_000)
                self.assertEqual(ledger.clock_high_water_ns, 1_110_000_000)
                self.assertFalse(ledger.healthy(now_monotonic_ns=1_110_000_000))

    def test_rejected_json_still_observes_trusted_clock_before_decoding(self):
        self.accept(0)
        before = self.ledger.snapshot
        with self.assertRaises(ValueError):
            self.ledger.accept_json('{malformed', received_monotonic_ns=1_110_000_000)
        self.assertEqual(self.ledger.snapshot, before)
        with self.assertRaises(ValueError):
            self.ledger.accept(record(50), received_monotonic_ns=1_090_000_000)
        self.assertEqual(self.ledger.clock_high_water_ns, 1_110_000_000)

    def test_invalid_clock_inputs_do_not_poison_clock_observations(self):
        self.accept(0)
        before = self.ledger.snapshot
        for now in (True, 1.5, -1, float('inf')):
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.ledger.healthy(now_monotonic_ns=now)
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_010_000_000))
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_010_000_000))  # equality allowed
        with self.assertRaises(ValueError):
            self.ledger.healthy(now_monotonic_ns=1_000_000_000)
        self.assertEqual(self.ledger.snapshot, before)
        self.assertEqual(self.ledger.clock_high_water_ns, 1_010_000_000)

    def test_fresh_admission_at_equal_observed_time_can_restore_health(self):
        self.accept(0)
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        self.ledger.accept(record(50), received_monotonic_ns=1_110_000_000)
        self.assertTrue(self.ledger.healthy(now_monotonic_ns=1_110_000_000))
        self.assertEqual(self.ledger.snapshot.native_em_acquisitions, 2)
        self.assertEqual(self.ledger.clock_high_water_ns, 1_110_000_000)

    def test_json_admission_and_rejection_preserve_ledger_and_deadline(self):
        self.ledger.accept_json(json.dumps(record()), received_monotonic_ns=1_000_000_000)
        before = self.ledger.snapshot
        raw = json.dumps(record(10))[:-1] + ', "quality":7}'
        with self.assertRaises(ValueError):
            self.ledger.accept_json(raw, received_monotonic_ns=1_099_000_000)
        self.assertEqual(self.ledger.snapshot, before)
        self.assertFalse(self.ledger.healthy(now_monotonic_ns=1_100_000_001))

    def test_receiver_delay_cannot_admit_em_expired_before_arrival(self):
        self.accept(0)
        before = self.ledger.snapshot
        with self.assertRaises(ValueError):
            self.accept(40, delay_ms=61)  # ADC fresh enough, original EM is 101ms old
        self.assertEqual(self.ledger.snapshot, before)

    def test_regular_stream_accepts_bounded_receiver_jitter(self):
        for tick in range(0, 301, 10):
            self.accept(tick, delay_ms=(tick // 10) % 3)
        self.assertEqual(self.ledger.snapshot.native_em_acquisitions, 7)

    def test_false_invalid_vibration_after_complete_window_rejected(self):
        for tick in range(0, 90, 10):
            self.accept(tick)
        payload = record(90)
        payload['quality'] &= ~0x88
        payload['channel_values'][3] = None
        payload['channel_counts'][3] = None
        ref.validate_record(payload)  # local schema cannot know the window history
        with self.assertRaises(ValueError):
            self.accept(90, payload=payload)

    def test_session_origin_requires_full_stream_and_explicit_new_ledger(self):
        for kwargs in ({'start_tick_ms': True, 'start_monotonic_ns': 0},
                       {'start_tick_ms': 1, 'start_monotonic_ns': 0},
                       {'start_tick_ms': 0, 'start_monotonic_ns': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ref.SourceLedger(**kwargs)
        with self.assertRaises(ValueError):
            self.accept(10)  # no midstream attach to earlier unseen EM0
        self.accept(0, delay_ms=10)  # retry origin record without rewinding receipt time


if __name__ == '__main__':
    unittest.main()
