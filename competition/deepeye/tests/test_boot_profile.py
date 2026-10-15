# -*- coding: utf-8 -*-
"""Bounded software tests for integration/boot_profile.py (R03 BOOT/profile reference).

Run from competition/deepeye:
    python -X utf8 tests/test_boot_profile.py -v

These tests freeze software behaviour only. They establish no hardware timing,
no measured USB/clock/holdover bounds, no channel calibration, no product gate.
"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration"))

import boot_profile  # noqa: E402  (RED until the module lands)
import wire  # noqa: E402

DOC_PATH = ROOT / "docs" / "boot_profiles.json"
ENUMS_PATH = ROOT / "docs" / "enums.json"


def load_doc():
    return boot_profile.load_document(DOC_PATH)


class CanonicalTests(unittest.TestCase):
    def test_canonical_sorted_compact_utf8(self):
        data = boot_profile.canonical_bytes({"b": 1, "a": "\u5f00\u53d1", "c": [2, "x"]})
        self.assertEqual(data, "{\"a\":\"\u5f00\u53d1\",\"b\":1,\"c\":[2,\"x\"]}".encode("utf-8"))

    def test_canonical_rejects_nonfinite(self):
        for bad in (float("inf"), float("-inf"), float("nan")):
            with self.assertRaises(boot_profile.ProfileError):
                boot_profile.canonical_bytes({"x": bad})

    def test_load_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "dup.json"
            tmp.write_text("{\"a\": 1, \"a\": 2}", encoding="utf-8")
            with self.assertRaises(boot_profile.ProfileError):
                boot_profile.load_document(tmp)

    def test_load_rejects_nonfinite_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "nan.json"
            tmp.write_text("{\"a\": NaN}", encoding="utf-8")
            with self.assertRaises(boot_profile.ProfileError):
                boot_profile.load_document(tmp)

    def test_validate_rejects_float_boolean_and_unknown(self):
        doc = load_doc()
        mutated = copy.deepcopy(doc)
        mutated["profiles"]["fast_9600"]["window_ms"] = 500.0
        self.assertTrue(any("float" in e for e in boot_profile.validate_document(mutated)))
        mutated = copy.deepcopy(doc)
        mutated["task_version"] = True
        self.assertTrue(any("bool" in e for e in boot_profile.validate_document(mutated)))
        mutated = copy.deepcopy(doc)
        mutated["unexpected_section"] = 1
        self.assertTrue(any("unknown" in e for e in boot_profile.validate_document(mutated)))
        mutated = copy.deepcopy(doc)
        mutated["profile_name"] = "not_a_profile"
        self.assertTrue(any("enum" in e for e in boot_profile.validate_document(
            mutated, enums=json.loads(ENUMS_PATH.read_text(encoding="utf-8")))))

    def test_validate_rejects_missing_required_key(self):
        doc = load_doc()
        del doc["pwm_capture"]
        self.assertTrue(any("missing" in e for e in boot_profile.validate_document(doc)))


class DigestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()
        cls.base = boot_profile.canonical_sha256(cls.doc)
        cls.sha128 = boot_profile.slot_profile_sha128(cls.doc)

    def test_digest_lengths_and_sha128_prefix(self):
        self.assertEqual(len(self.base), 32)
        self.assertEqual(len(self.sha128), 16)
        self.assertEqual(self.sha128, self.base[:16])

    def test_original_profile_hash_mutations_rejected(self):
        mutated = copy.deepcopy(self.doc)
        mutated["profiles"]["fast_9600"]["window_ms"] = 501
        self.assertFalse(boot_profile.verify_profile_digest(mutated, self.sha128))
        self.assertTrue(boot_profile.verify_profile_digest(copy.deepcopy(self.doc), self.sha128))

    def test_every_covered_group_changes_digest(self):
        mutations = {
            "abi": lambda d: d["abi"].__setitem__("version", 4),
            "abi_digest_binding": lambda d: d["digests"]["abi_interface_json"].__setitem__("mode", "frozen_verified"),
            "topology_source_acquisition": lambda d: d["topology_source_acquisition"]["source_id"].__setitem__("sensor_live", 9),
            "transport_baud": lambda d: d["transport_profiles"]["fast_9600"].__setitem__("baud", 19200),
            "slot_offset": lambda d: d["profiles"]["fast_9600"]["slots"]["control_primary"].__setitem__("start_ms", 211),
            "guard": lambda d: d["profiles"]["stress_300"].__setitem__("guard_total_ms", 201),
            "retry_offset": lambda d: d["profiles"]["fast_9600"].__setitem__("retry_offset_ms", 156),
            "speed_mapping": lambda d: d["speed_mappings"]["stress_300"].__setitem__("per_code_m_s", "1/10001"),
            "ttl_age": lambda d: d["ttl_and_age"]["pc_direct_observation_age_limit_ms"].__setitem__("fast_9600", 1501),
            "kinematics_curvature": lambda d: d["motion_kinematics"].__setitem__("curvature_limit_per_m", "1/3"),
            "kinematics_rom": lambda d: d["motion_kinematics"].__setitem__("rom_check", "other"),
            "pwm_encoding": lambda d: d["pwm_capture"].__setitem__("angle_high_ticks", "10001+16*(q+15000)"),
            "capture_tolerance": lambda d: d["pwm_capture"].__setitem__("capture_tolerance_ticks", "<=1 tick"),
            "channel_unit": lambda d: d["channels"][3].__setitem__("unit", "milli-g"),
            "channel_calibration_ref": lambda d: d["channels"][0].__setitem__("calibration_reference", "cal-1"),
            "time_usb_identity": lambda d: d["time_measurement_identities"]["usb_processing_upper_ns"].__setitem__("status", "verified"),
            "holdover_identity": lambda d: d["time_measurement_identities"]["anchor_holdover_cap_ms"].__setitem__("unit", "s"),
            "acquisition_profile": lambda d: d["acquisition_profiles"]["force_lithology_v1"].__setitem__("shared_scaling_with", "pga_voltage_v1"),
            "frame_layout_bytes": lambda d: d["boot_frames"]["BOOT"].__setitem__("frame_bytes", 42),
            "profile_name": lambda d: d.__setitem__("profile_name", "em_surrogate_v3"),
        }
        for name, mutate in mutations.items():
            mutated = copy.deepcopy(self.doc)
            mutate(mutated)
            with self.subTest(group=name):
                self.assertNotEqual(boot_profile.canonical_sha256(mutated), self.base,
                                    "digest must change for covered group %s" % name)

    def test_real_document_valid(self):
        enums = json.loads(ENUMS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(boot_profile.validate_document(self.doc, enums=enums), [])
        self.assertFalse(self.doc["hardware_enable_eligible"])


class BootModeTests(unittest.TestCase):
    def test_compose_and_parse_roundtrip(self):
        for transport, source, topology in (
                ("fast_9600", "sensor_live", "hil_pc_fpga"),
                ("stress_300", "twin_fixture", "pc_direct"),
                ("fast_9600", "software_fixture", "fpga_local")):
            mode = boot_profile.compose_boot_mode(transport, source, topology)
            parsed = boot_profile.parse_boot_mode(mode)
            self.assertEqual(parsed["transport"], transport)
            self.assertEqual(parsed["source"], source)
            self.assertEqual(parsed["topology"], topology)

    def test_rejects_zero_reserved_and_unknown(self):
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.parse_boot_mode(0)
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.parse_boot_mode(37 | 128)
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.compose_boot_mode("fast_9600", "sensor_live", "no_such_topology")
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.compose_boot_mode("no_such_transport", "sensor_live", "hil_pc_fpga")


class BootFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()
        cls.mode = boot_profile.compose_boot_mode("fast_9600", "sensor_live", "hil_pc_fpga")

    def test_roundtrip_via_existing_wire(self):
        frame = boot_profile.boot_frame(self.doc, session=7, mode=self.mode,
                                        config_epoch=3, sequence=11, tick_ms=1234)
        self.assertEqual(len(frame), 41)
        parsed = boot_profile.parse_boot_frame(frame)
        self.assertEqual(parsed["type"], 12)
        self.assertEqual(parsed["session"], 7)
        self.assertEqual(parsed["mode"], self.mode)
        self.assertEqual(parsed["slot_profile_sha128"], boot_profile.slot_profile_sha128(self.doc).hex())
        self.assertEqual(parsed["guard_total_ms"], 40)
        self.assertEqual(parsed["primary_slot_ms"], 210)
        self.assertEqual(parsed["config_slot_ms"], 365)
        again = boot_profile.parse_boot_payload(boot_profile.boot_payload(self.doc, 7, self.mode))
        self.assertEqual(again["session"], 7)

    def test_exact_equality_ack_accepts_and_rejects_differences(self):
        req = boot_profile.boot_frame(self.doc, session=7, mode=self.mode, config_epoch=3)
        ack = boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode, config_epoch=3)
        self.assertEqual(len(ack), 41)
        self.assertTrue(boot_profile.verify_boot_ack(req, ack, expected_epoch=3)["ok"])

        other_mode = boot_profile.compose_boot_mode("stress_300", "sensor_live", "hil_pc_fpga")
        cases = {
            "session": boot_profile.boot_ack_frame(self.doc, session=8, mode=self.mode, config_epoch=3),
            "mode": boot_profile.boot_ack_frame(self.doc, session=7, mode=other_mode, config_epoch=3),
            "guard_total_ms": boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode, config_epoch=3,
                                                 guard_override_ms=41),
            "primary_slot_ms": boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode, config_epoch=3,
                                                   primary_override_ms=211),
            "config_slot_ms": boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode, config_epoch=3,
                                                       config_override_ms=366),
        }
        for name, frame in cases.items():
            with self.subTest(mismatch=name):
                result = boot_profile.verify_boot_ack(req, frame, expected_epoch=3)
                self.assertFalse(result["ok"])
                self.assertIn(name, result["mismatches"])
        ack_echo_wrong_sha = boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode, config_epoch=3,
                                                         sha128_override=bytes(16))
        result = boot_profile.verify_boot_ack(req, ack_echo_wrong_sha, expected_epoch=3)
        self.assertFalse(result["ok"])
        self.assertIn("slot_profile_sha128", result["mismatches"])
        epoch_result = boot_profile.verify_boot_ack(req, ack, expected_epoch=9)
        self.assertFalse(epoch_result["ok"])
        self.assertIn("config_epoch", epoch_result["mismatches"])

    def test_malformed_frames_rejected(self):
        req = boot_profile.boot_frame(self.doc, session=7, mode=self.mode)
        ack = boot_profile.boot_ack_frame(self.doc, session=7, mode=self.mode)
        with self.assertRaises(ValueError):
            boot_profile.parse_boot_frame(ack)               # wrong type for BOOT parser
        with self.assertRaises(ValueError):
            boot_profile.parse_boot_ack_frame(req)           # wrong type for BOOT_ACK parser
        with self.assertRaises(ValueError):
            boot_profile.parse_boot_frame(req[:-1])          # truncated prefix
        corrupted = bytearray(req)
        corrupted[-1] ^= 0xff
        with self.assertRaises(ValueError):
            boot_profile.parse_boot_frame(bytes(corrupted))  # CRC failure
        bad_mode = bytearray(boot_profile.boot_payload(self.doc, 7, self.mode))
        bad_mode[4] = 0
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.parse_boot_payload(bytes(bad_mode))
        bad_mode[4] = 200
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.parse_boot_payload(bytes(bad_mode))


class SlotReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()

    def test_fast_branch_anchors_exact(self):
        ends = {
            "event": Fraction(125, 6), "telem": Fraction(205, 3),
            "control_primary": Fraction(965, 4), "ack_primary": Fraction(3485, 12),
            "state": Fraction(4085, 12), "retry_control": Fraction(1585, 4),
            "retry_ack": Fraction(5345, 12), "config": Fraction(390),
            "config_ack": Fraction(1315, 3),
        }
        for slot, end in ends.items():
            with self.subTest(slot=slot):
                self.assertEqual(boot_profile.segment_ms(self.doc, "fast_9600", slot)["end_ms"], end)

    def test_stress_branch_anchors_exact(self):
        ends = {
            "event": Fraction(2000, 3), "telem": Fraction(5300, 3),
            "control_primary": Fraction(3050), "ack_primary": Fraction(12700, 3),
            "state": Fraction(16300, 3), "retry_control": Fraction(6500),
            "retry_ack": Fraction(23050, 3), "config": Fraction(6300),
            "config_ack": Fraction(22850, 3),
        }
        for slot, end in ends.items():
            with self.subTest(slot=slot):
                self.assertEqual(boot_profile.segment_ms(self.doc, "stress_300", slot)["end_ms"], end)

    def test_branches_disjoint_ordered_within_window_with_guard(self):
        for name in ("fast_9600", "stress_300"):
            window = self.doc["profiles"][name]["window_ms"]
            guard = self.doc["profiles"][name]["guard_total_ms"]
            for branch in ("normal", "config", "retry"):
                with self.subTest(profile=name, branch=branch):
                    self.assertEqual(boot_profile.validate_branch(self.doc, name, branch), [])
                    segments = boot_profile.branch_segments(self.doc, name, branch)
                    last_end = Fraction(0)
                    for seg in segments:
                        self.assertGreaterEqual(seg["start_ms"], last_end)
                        last_end = seg["end_ms"]
                    self.assertLessEqual(last_end, window)
                    self.assertGreaterEqual(window - last_end, guard)

    def test_budget_variants_match_frozen_anchors(self):
        anchors = {
            ("fast_9600", "normal"): (150, Fraction(157, 400)),
            ("fast_9600", "config"): (206, Fraction(611, 1200)),
            ("fast_9600", "control_retry"): (214, Fraction(631, 1200)),
            ("fast_9600", "event_retry"): (170, Fraction(521, 1200)),
            ("fast_9600", "gain_normal"): (140, Fraction(223, 600)),
            ("fast_9600", "pc_direct_normal"): (84, Fraction(51, 200)),
            ("stress_300", "normal"): (150, Fraction(13, 20)),
            ("stress_300", "config"): (206, Fraction(53, 60)),
            ("stress_300", "control_retry"): (214, Fraction(11, 12)),
            ("stress_300", "event_retry"): (170, Fraction(11, 15)),
            ("stress_300", "gain_normal"): (140, Fraction(73, 120)),
            ("stress_300", "pc_direct_normal"): (84, Fraction(3, 8)),
        }
        for (name, variant), (wire_bytes, fraction) in anchors.items():
            with self.subTest(profile=name, variant=variant):
                budget = boot_profile.window_budget(self.doc, name, variant)
                self.assertEqual(budget["wire_bytes"], wire_bytes)
                self.assertEqual(budget["fraction"], fraction)

    def test_validate_flags_overlapping_slot_and_guard_break(self):
        mutated = copy.deepcopy(self.doc)
        mutated["profiles"]["fast_9600"]["slots"]["control_primary"]["start_ms"] = 40
        self.assertTrue(boot_profile.validate_branch(mutated, "fast_9600", "normal"))
        mutated = copy.deepcopy(self.doc)
        mutated["profiles"]["stress_300"]["guard_total_ms"] = 3000
        self.assertTrue(any("guard" in e for e in boot_profile.validate_document(mutated)))

    def test_retry_offset_fixed_and_absolute_shift(self):
        for name in ("fast_9600", "stress_300"):
            profile = self.doc["profiles"][name]
            primary = boot_profile.slot_start_ms(self.doc, name, "control_primary")
            retry = boot_profile.slot_start_ms(self.doc, name, "retry_control")
            self.assertEqual(retry - primary, profile["retry_offset_ms"])
            for k in (0, 1, 5):
                shifted = boot_profile.segment_ms(self.doc, name, "retry_control", k=k)
                self.assertEqual(shifted["start_ms"], retry + k * profile["window_ms"])

    def test_primary_response_anchored_to_slot_not_receipt(self):
        derived = boot_profile.response_deadlines_ms(self.doc, "fast_9600")
        declared = self.doc["profiles"]["fast_9600"]["response_deadlines_ms"]
        for key, value in declared.items():
            with self.subTest(key=key):
                self.assertEqual(derived[key], Fraction(str(value)))
        self.assertEqual(derived["primary_ack_latest_ms"],
                         boot_profile.segment_ms(self.doc, "fast_9600", "ack_primary")["end_ms"])
        self.assertEqual(derived["retry_ack_latest_ms"],
                         boot_profile.segment_ms(self.doc, "fast_9600", "retry_ack")["end_ms"])
        self.assertEqual(derived["retry_decision_ms"],
                         Fraction(boot_profile.slot_start_ms(self.doc, "fast_9600", "retry_control")))

    def test_grant_masks_legal_and_invalid(self):
        legal = [1 << 15, 1 << 14, (1 << 15) | (1 << 14), (1 << 15) | (1 << 13), 0]
        for mask in legal:
            self.assertEqual(boot_profile.grant_mask_errors(mask), [], "mask %#x must be legal" % mask)
        invalid = [1 << 13, (1 << 14) | (1 << 13), (1 << 15) | (1 << 14) | (1 << 13), 1 << 16, -1]
        for mask in invalid:
            self.assertTrue(boot_profile.grant_mask_errors(mask), "mask %#x must be rejected" % mask)

    def test_no_grant_no_send_and_suppress_after_success(self):
        plan = boot_profile.plan_window(self.doc, "fast_9600", grants=0, first_ack_ok=False)
        self.assertNotIn("control_primary", plan["transmits"])
        self.assertNotIn("retry_control", plan["transmits"])
        self.assertFalse(plan["retry_used"])
        plan = boot_profile.plan_window(self.doc, "fast_9600", grants=(1 << 15) | (1 << 13), first_ack_ok=True)
        self.assertIn("control_primary", plan["transmits"])
        self.assertNotIn("retry_control", plan["transmits"])
        self.assertTrue(plan["retry_suppressed"])
        plan = boot_profile.plan_window(self.doc, "fast_9600", grants=(1 << 15) | (1 << 13), first_ack_ok=False)
        self.assertIn("retry_control", plan["transmits"])
        self.assertTrue(plan["retry_used"])
        plan = boot_profile.plan_window(self.doc, "fast_9600", grants=(1 << 14), first_ack_ok=False)
        self.assertIn("config", plan["transmits"])
        self.assertNotIn("control_primary", plan["transmits"])
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.plan_window(self.doc, "fast_9600", grants=(1 << 14) | (1 << 13), first_ack_ok=False)

    def test_lost_grant_and_lost_ack_keep_slots_unshifted(self):
        plan = boot_profile.plan_window(self.doc, "fast_9600", grants=1 << 15, first_ack_ok=False)
        self.assertFalse(plan["retry_used"])
        self.assertIn("defer_next_window", plan["advisories"])
        action = boot_profile.late_candidate_action(self.doc, "fast_9600", ready_ms=211, deadline_ms=1500)
        self.assertEqual(action["action"], "defer")
        self.assertEqual(action["deferred_start_ms"], boot_profile.slot_start_ms(self.doc, "fast_9600", "control_primary")
                         + self.doc["profiles"]["fast_9600"]["window_ms"])
        action = boot_profile.late_candidate_action(self.doc, "fast_9600", ready_ms=210, deadline_ms=1500)
        self.assertEqual(action["action"], "send")
        action = boot_profile.late_candidate_action(self.doc, "fast_9600", ready_ms=1500, deadline_ms=1500)
        self.assertEqual(action["action"], "stop")

    def test_rolling_window_occupancy_across_three_periods(self):
        for name in ("fast_9600", "stress_300"):
            for branch, total in (("normal", 150), ("config", 206), ("retry", 214)):
                with self.subTest(profile=name, branch=branch):
                    observed = boot_profile.rolling_window_max_bytes(self.doc, name, branch, periods=3)
                    self.assertLessEqual(observed, total)
                    self.assertEqual(observed, total)

    def test_ceil_bounds(self):
        self.assertEqual(boot_profile.ceil_ms(Fraction(125, 6)), 21)
        self.assertEqual(boot_profile.ceil_ms(Fraction(100, 3)), 34)
        self.assertEqual(boot_profile.ceil_ms(35), 35)

    def test_speed_mapping_not_mixed(self):
        self.assertEqual(boot_profile.speed_m_s(self.doc, "fast_9600", 20), Fraction(1, 4))
        self.assertEqual(boot_profile.speed_m_s(self.doc, "stress_300", 20), Fraction(1, 500))
        self.assertEqual(boot_profile.speed_m_s(self.doc, "fast_9600", 5), Fraction(1, 16))
        with self.assertRaises(boot_profile.ProfileError):
            boot_profile.speed_m_s(self.doc, "fast_9600", 21)


class RuntimeDigestTests(unittest.TestCase):
    def test_runtime_digests_runtime_loaded_unverified(self):
        digests = boot_profile.runtime_digests(ROOT)
        for key in ("abi_interface_json", "host_contract_json", "host_enums_json"):
            with self.subTest(key=key):
                entry = digests[key]
                self.assertEqual(entry["mode"], "runtime_loaded_unverified")
                path = ROOT / entry["path"]
                self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIsNone(digests["frame_layouts"]["sha256"])
        self.assertEqual(digests["frame_layouts"]["mode"], "computed_at_runtime_unverified")

    def test_unmeasured_values_must_stay_null(self):
        doc = load_doc()
        mutated = copy.deepcopy(doc)
        mutated["time_measurement_identities"]["usb_processing_upper_ns"]["value"] = 1000000
        self.assertTrue(any("unverified" in e for e in boot_profile.validate_document(mutated)))


if __name__ == "__main__":
    unittest.main(verbosity=2)