# -*- coding: utf-8 -*-
"""Bounded R03 BOOT/profile canonical reference (software candidate only).

This module is a pure software reference for the DeepEye BOOT handshake and the
deterministic FAST_9600 / STRESS_300 slot schedule. It performs no board,
serial, network, service or model access and it never claims ENABLE: the profile
document keeps hardware_enable_eligible=false and every unmeasured identity
stays null until an independently verified measurement record exists.

Canonical identity: UTF-8 JSON with ensure_ascii=False, sort_keys=True and
separators=(",", ":"), no trailing newline. The full 32-byte SHA256 is kept as
host evidence; the first 16 bytes travel as slot_profile_sha128 inside the
BOOT/BOOT_ACK payloads (27 B each, 41 B frames over the frozen ABI3 wire
encoder). Changing any covered semantic group -- ABI, frame layouts, host
schema/enum digest bindings, topology/source/acquisition, transport baud,
every slot/retry/config offset, response deadlines, channel units and
conversion references, speed mappings, TTL/age bounds, curvature ROM and
kinematic bounds, PWM/capture encoding, time measurement identities -- changes
the digest.

Timing arithmetic uses Fraction (exact rationals) and ceil for upper bounds;
byte time is line_bits_per_byte * 1000 / baud milliseconds per byte (8N1).
"""
from fractions import Fraction
import copy
import itertools
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import wire  # noqa: E402  (frozen ABI3 encoder, no side effects)

PROFILE_NAME = "em_surrogate_v2"
MEASUREMENT_EVIDENCE = (
    "independently verified measurement record bound to operation_id, "
    "request_hash, tested_commit, profile and tool/board evidence"
)
INFERENCE_KEY = "host_inference"

BOOT_TYPE = 12
BOOT_ACK_TYPE = 13
BOOT_PAYLOAD_BYTES = 27
BOOT_FRAME_BYTES = 41
_BOOT_PAYLOAD = struct.Struct("<IB16sHHH")

TRANSPORT_IDS = {"fast_9600": 1, "stress_300": 2}
SOURCE_IDS = {"sensor_live": 1, "geo_replay": 2, "twin_fixture": 3,
              "software_fixture": 4}
TOPOLOGY_IDS = {"hil_pc_fpga": 1, "pc_direct": 2, "fpga_local": 3}
ACQUISITION_IDS = {"em_surrogate_v2": 1, "force_lithology_v1": 2,
                   "pga_voltage_v1": 3}
RESERVED_ZERO_BITS = (7,)
BOOT_MODE_FORMULA = "transport_profile_id | (source_id << 2) | (topology_id << 5)"

MAIN_GRANT_BIT = 15
CONFIG_GRANT_BIT = 14
RETRY_GRANT_BIT = 13

PROFILE_NAMES = ("fast_9600", "stress_300")
BRANCH_NAMES = ("normal", "config", "retry")

LINE_BITS_PER_BYTE = 10
FRAMING = "8N1"
BAUD = {"fast_9600": 9600, "stress_300": 300}
GUARD_FLOOR_MS = {"fast_9600": 40, "stress_300": 200}

SLOT_FRAME_BYTES = {
    "event": 20, "telem": 32, "control_primary": 30, "ack_primary": 34,
    "state": 34, "retry_control": 30, "retry_ack": 34, "config": 24,
    "config_ack": 32,
}
SLOT_DIRECTIONS = {
    "event": "uplink", "telem": "uplink", "control_primary": "downlink",
    "ack_primary": "uplink", "state": "uplink", "retry_control": "downlink",
    "retry_ack": "uplink", "config": "downlink", "config_ack": "uplink",
}
BRANCH_SLOTS = {
    "normal": ["event", "telem", "control_primary", "ack_primary", "state"],
    "config": ["event", "telem", "control_primary", "ack_primary", "state",
               "config", "config_ack"],
    "retry": ["event", "telem", "control_primary", "ack_primary", "state",
              "retry_control", "retry_ack"],
}
MUTUAL_EXCLUSIONS = [["config", "retry"]]

BUDGET_VARIANTS = ("normal", "config", "control_retry", "event_retry",
                   "gain_normal", "pc_direct_normal")
BUDGET_VARIANT_ANCHORS = {"normal": 150, "config": 206, "control_retry": 214,
                          "event_retry": 170, "gain_normal": 140,
                          "pc_direct_normal": 84}
MODE_VARIANTS = {
    'normal': [('event', 'EVENT', 20), ('telem', 'TELEM', 32),
               ('control_primary', 'CONTROL3D', 30), ('ack_primary', 'ACK3D', 34), ('state', 'STATE3D', 34)],
    'config': [('event', 'EVENT', 20), ('telem', 'TELEM', 32),
               ('control_primary', 'CONTROL3D', 30), ('ack_primary', 'ACK3D', 34), ('state', 'STATE3D', 34),
               ('config', 'CONFIG', 24), ('config_ack', 'CONFIG_ACK', 32)],
    'control_retry': [('event', 'EVENT', 20), ('telem', 'TELEM', 32),
               ('control_primary', 'CONTROL3D', 30), ('ack_primary', 'ACK3D', 34), ('state', 'STATE3D', 34),
               ('retry_control', 'CONTROL3D', 30), ('retry_ack', 'ACK3D', 34)],
    'event_retry': [('event', 'EVENT', 20), ('telem', 'TELEM', 32),
               ('control_primary', 'CONTROL3D', 30), ('ack_primary', 'ACK3D', 34), ('state', 'STATE3D', 34),
               ('retry_control', 'EVENT', 20)],
    'gain_normal': [('event', 'EVENT', 20), ('telem', 'TELEM', 32),
               ('control_primary', 'GAIN', 24), ('ack_primary', 'GAIN_ACK', 32), ('state', 'STATE', 32)],
    'pc_direct_normal': [('event', 'EVENT', 20), ('telem', 'TELEM', 32), ('state', 'STATE', 32)],
}
# gain_normal / pc_direct_normal are the PHYSICAL GAIN window (GAIN 24 +
# GAIN_ACK 32 + physical STATE 32 + TELEM 32 + EVENT 20) and the PC_DIRECT
# idle window (TELEM 32 + physical STATE 32 + EVENT 20) of taskbook section 7;
# they are single-mode budgets and are never donated to a 3D motion window.

SPEED_ANCHORS = {
    "fast_9600": {"per_code_m_s": "1/80", "max_m_s": "1/4", "max_code": 20,
                  "ttl_max_ms": 3000},
    "stress_300": {"per_code_m_s": "1/10000", "max_m_s": "1/500",
                   "max_code": 20, "ttl_max_ms": 12000},
}
OBSERVATION_AGE_MS = {"fast_9600": 1500, "stress_300": 12000}
SUMMARY_SAMPLES = {"fast_9600": 50, "stress_300": 800}
SENSOR_HEARTBEAT_TIMEOUT_MS = 100
FPGA_OBSERVATION_HISTORY = 4

TIME_IDENTITY_UNITS = {
    "usb_processing_upper_ns": "ns",
    "frame_serial_upper_ns": "ns",
    "clock_error_upper_ns": "ns",
    "rate_bound_ppm": "ppm",
    "tick_quantization_hi_ns": "ns",
    "dispatch_delay_lo_ns": "ns",
    "dispatch_delay_hi_ns": "ns",
    "anchor_holdover_cap_ms": "ms",
}
CHANNEL_NAMES = ("log10_rho_apparent", "azimuth_log10_rho_difference",
                 "elevation_log10_rho_difference", "near_bit_vibration_rms_g")

RUNTIME_DIGEST_FILES = (
    ("abi_interface_json", "docs/interface.json"),
    ("host_contract_json", "docs/host_contract.json"),
    ("host_enums_json", "docs/enums.json"),
    ("host_timing_contract", "docs/host_timing_contract.md"),
)

_RAT_PATTERN = re.compile(r"^-?[0-9]+(?:/[0-9]+)?$")


class ProfileError(ValueError):
    """A profile/BOOT contract violation. Software reference only."""
_I = "int"
_S = "str"
_B = "bool"
_R = "rat"

_FRAME_SCHEMA = {"keys": {"type": _I, "payload_bytes": _I, "frame_bytes": _I}}
_SLOT_SCHEMA = {"keys": {"start_ms": _I, "max_bytes": _I, "direction": _S}}
_PROFILE_SCHEMA = {"keys": {
    "window_ms": _I, "guard_total_ms": _I, "primary_slot_ms": _I,
    "config_slot_ms": _I, "retry_offset_ms": _I,
    "slots": {"keys": {name: _SLOT_SCHEMA for name in SLOT_FRAME_BYTES}},
    "branches": {"keys": {name: {"list": _S} for name in BRANCH_NAMES}},
    "mutual_exclusions": {"list": {"list": _S}},
    "response_deadlines_ms": {"keys": {
        "retry_decision_ms": _R, "primary_ack_latest_ms": _R,
        "retry_ack_latest_ms": _R, "config_ack_latest_ms": _R}},
    "ai_wait": {"keys": {"after_slot": _S, "start_ms": _R,
                         "before_slot": _S, "end_ms": _I}},
    "budget_variants": {"keys": {name: _I for name in BUDGET_VARIANTS}},
    "event_retry": {"keys": {"slot": "int?", "bytes": _I, "status": _S,
                             "rule": _S}},
    "grants": {"keys": {
        "main_bit": _I, "config_bit": _I, "retry_pre_grant_bit": _I,
        "retry_rule": _S, "config_rule": _S, "no_grant_no_send": _B,
        "first_ack_success_suppresses_retry": _B,
        "primary_response_anchor": _S}},
    "bounded_targets": {"keys": {
        "p99_s": _R, "max_s": _I, "event_p99_s?": _I,
        "event_single_retry_s?": _I, "status": _S}},
}}

_DOCUMENT_SCHEMA = {"keys": {
    "schema": _I, "document": _S, "profile_name": _S, "status": _S,
    "owner": _S, "task_id": _S, "task_version": _I, "design_commit": _S,
    "immutable_scope_id": _S, "immutable_scope_sha256": _S, "hash_rule": _S,
    "boot_frames": {"keys": {"BOOT": _FRAME_SCHEMA, "BOOT_ACK": _FRAME_SCHEMA}},
    "abi": {"keys": {
        "version": _I, "magic_hex": _S, "byte_order": _S, "header_bytes": _I,
        "crc_bytes": _I, "max_payload_bytes": _I, "max_frame_bytes": _I,
        "line_bits_per_byte": _I,
        "crc": {"keys": {
            "name": _S, "polynomial": _I, "initial": _I,
            "reflect_input": _B, "reflect_output": _B, "xorout": _I,
            "check_ascii_123456789": _I, "wire_byte_order": _S}},
        "frame_layouts_digest": {"keys": {"mode": _S, "value": "str?",
                                          "source": _S}}}},
    "digests": {"keys": {
        name: {"keys": {"path": _S, "mode": _S, "value": "str?"}}
        for name in ("abi_interface_json", "host_contract_json",
                     "host_enums_json", "host_timing_contract")}},
    "topology_source_acquisition": {"keys": {
        "transport_profile_id": {"keys": {name: _I for name in TRANSPORT_IDS}},
        "source_id": {"keys": {name: _I for name in SOURCE_IDS}},
        "topology_id": {"keys": {name: _I for name in TOPOLOGY_IDS}},
        "acquisition_profile_id": {"keys": {name: _I for name in ACQUISITION_IDS}},
        "boot_mode_formula": _S,
        "reserved_zero_bits": {"list": _I},
        "zero_or_unknown": _S}},
    "transport_profiles": {"keys": {
        name: {"keys": {"baud": _I, "framing": _S, "line_bits_per_byte": _I}}
        for name in PROFILE_NAMES}},
    "profiles": {"keys": {name: _PROFILE_SCHEMA for name in PROFILE_NAMES}},
    "mode_variants": {"keys": {name: {"list": {"keys": {
        "slot": _S, "frame": _S, "bytes": _I}}} for name in BUDGET_VARIANTS}},
    "speed_mappings": {"keys": dict(
        {"maps_never_mixed": _B},
        **{name: {"keys": {"per_code_m_s": _R, "max_m_s": _R, "ttl_max_ms": _I}}
           for name in PROFILE_NAMES})},
    "ttl_and_age": {"keys": {
        "hil_observation_age_limit_ms": {"keys": {n: _I for n in PROFILE_NAMES}},
        "pc_direct_observation_age_limit_ms": {"keys": {n: _I for n in PROFILE_NAMES}},
        "sensor_heartbeat_timeout_ms": _I,
        "summary_samples": {"keys": {n: _I for n in PROFILE_NAMES}},
        "fpga_observation_history": _I,
        "deadline_rule": _S,
        "heartbeat_extends_deadline": _B}},
    "motion_kinematics": {"keys": {
        "angular_rate_quantum_deg_s": _R, "q_min": _I, "q_max": _I,
        "curvature_limit_per_m": _R, "rom_check": _S,
        "zero_speed_requires_zero_q": _B, "intermediate_bits": _I,
        "min_demo_turn_radius_m": _I, "max_accel_m_s2": _R,
        "status_note": _S}},
    "pwm_capture": {"keys": {
        "period_ms": _I, "period_ticks": _I, "clock_hz": _I,
        "angle_high_ticks": _S, "angle_high_ms_range": {"list": _R},
        "speed_high_ticks": _S, "speed_high_ms_range": {"list": _R},
        "capture_tolerance_ticks": _S, "status": _S}},
    "channels": {"list": {"keys": {
        "id": _I, "name": _S, "quantity": "str?", "unit": "str?",
        "source": _S, "conversion": "str?", "calibration_reference": "str?",
        "status": _S}}},
    "acquisition_profiles": {"keys": {
        "em_surrogate_v2": {"keys": {
            "enum_id": _I, "source_mode": _S, "channels": {"list": _I},
            "calibration": "str?", "shared_scaling_with": "str?",
            "status": _S}},
        "force_lithology_v1": {"keys": {
            "enum_id": _I, "mapping": _S, "calibration": "str?",
            "shared_scaling_with": "str?", "status": _S}},
        "pga_voltage_v1": {"keys": {
            "enum_id": _I, "mapping": _S, "calibration": "str?",
            "shared_scaling_with": "str?", "status": _S}}}},
    "time_measurement_identities": {"keys": {
        name: {"keys": {"value": "rat?", "unit": _S, "status": _S,
                        "required_evidence": _S}}
        for name in TIME_IDENTITY_UNITS}},
    "policy": {"keys": {
        "profile_or_mode_switch": _S, "enable_claim": _S,
        "event_scheduling": _S, "no_fabricated_measurements": _B,
        "first_ack_success_suppresses_retry": _B, "retry_pair_grants": _S,
        "config_grant": _S, "no_grant_no_send": _B, "ack_miss_retry": _S,
        "late_candidate": _S}},
    "hardware_enable_eligible": _B,
    "remaining_gates": {"list": _S},
    "sources": {"keys": {name: _S for name in (
        "taskbook", "interface", "enums", "host_contract",
        "host_timing_contract", "simulation_contract", "wire", "checks")}},
    "scope_note": _S,
}}


def _bool_allowed(path):
    """Booleans are only valid on these frozen policy/flag paths."""
    if path == ("hardware_enable_eligible",):
        return True
    if path in (("motion_kinematics", "zero_speed_requires_zero_q"),
                ("ttl_and_age", "heartbeat_extends_deadline"),
                ("speed_mappings", "maps_never_mixed"),
                ("abi", "crc", "reflect_input"),
                ("abi", "crc", "reflect_output"),
                ("policy", "no_fabricated_measurements"),
                ("policy", "first_ack_success_suppresses_retry"),
                ("policy", "no_grant_no_send")):
        return True
    if len(path) == 4 and path[0] == "profiles" and path[2] == "grants":
        return path[3] in ("no_grant_no_send",
                           "first_ack_success_suppresses_retry")
    return False


def _scan_types(node, path, errors):
    """Reject floats anywhere, stray booleans and non-JSON value types."""
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                errors.append("%s: object keys must be strings, got %r"
                              % (".".join(path) or "document", key))
                continue
            _scan_types(value, path + (key,), errors)
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            _scan_types(value, path + ("[%d]" % index,), errors)
        return
    where = ".".join(path) or "document"
    if type(node) is bool:
        if not _bool_allowed(path):
            errors.append("%s: bool is not valid here; integer or string "
                          "fields must not be booleans" % where)
        return
    if type(node) is float:
        errors.append("%s: float %r is forbidden in the canonical profile; "
                      "use integer units or 'p/q' rational strings" % (where, node))
        return
    if node is None or type(node) in (int, str):
        return
    errors.append("%s: unsupported value type %s" % (where, type(node).__name__))


def _walk(node, spec, path, errors):
    """Structural walk: presence, unknown keys, leaf types, rationals."""
    if isinstance(spec, dict):
        if "list" in spec:
            if not isinstance(node, list):
                errors.append("%s: expected a list" % path)
                return
            for index, item in enumerate(node):
                _walk(item, spec["list"], "%s[%d]" % (path, index), errors)
            return
        keys = spec["keys"]
        if not isinstance(node, dict):
            errors.append("%s: expected an object" % path)
            return
        known = {key[:-1] if key.endswith("?") else key for key in keys}
        for key in node:
            if key not in known:
                errors.append("%s: unknown key %r" % (path, key))
        for key, sub in keys.items():
            optional = key.endswith("?")
            name = key[:-1] if optional else key
            if name not in node:
                if not optional:
                    errors.append("%s: missing required key %r" % (path, name))
                continue
            _walk(node[name], sub, "%s.%s" % (path, name), errors)
        return
    if spec == "nullish":
        return
    if spec == "int":
        if type(node) is not int:
            if type(node) is bool:
                errors.append("%s: expected integer, got bool (booleans are "
                              "not integers here)" % path)
            elif type(node) is float:
                errors.append("%s: expected integer, got float %r; integer "
                              "units or 'p/q' rational strings only"
                              % (path, node))
            else:
                errors.append("%s: expected integer, got %s"
                              % (path, type(node).__name__))
        return
    if spec == "str":
        if not isinstance(node, str):
            errors.append("%s: expected string, got %s"
                          % (path, type(node).__name__))
        return
    if spec == "bool":
        if type(node) is not bool:
            errors.append("%s: expected bool, got %s"
                          % (path, type(node).__name__))
        return
    if spec in ("rat", "rat?"):
        if node is None and spec.endswith("?"):
            return
        if type(node) is int:
            return
        if isinstance(node, str) and _RAT_PATTERN.match(node):
            return
        if type(node) is float:
            errors.append("%s: float %r is forbidden; use integer units or "
                          "'p/q' rational strings" % (path, node))
            return
        errors.append("%s: expected integer or 'p/q' rational string, got %r"
                      % (path, node))
        return
    if spec in ("str?",):
        if node is None or isinstance(node, str):
            return
        errors.append("%s: expected string or null, got %s"
                      % (path, type(node).__name__))
        return
    if spec == "int?":
        if node is None or type(node) is int:
            return
        errors.append("%s: expected integer or null, got %s"
                      % (path, type(node).__name__))
        return
    raise ProfileError("internal schema spec is unknown: %r" % (spec,))


def _rational(value, path):
    """Exact rational from an integer or a 'p/q' / 'p' string. No floats."""
    if type(value) is int:
        return Fraction(value)
    if type(value) is float:
        raise ProfileError("%s: float %r is forbidden; unmeasured or "
                           "parameter values must be exact rationals"
                           % (path, value))
    if isinstance(value, str):
        if not _RAT_PATTERN.match(value):
            raise ProfileError("%s: %r is not an integer or 'p/q' rational "
                               "string" % (path, value))
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ProfileError("%s: invalid rational %r (%s)"
                               % (path, value, exc)) from exc
    raise ProfileError("%s: expected integer or rational string, got %r"
                       % (path, value))


def canonical_bytes(obj):
    """UTF-8 canonical JSON bytes: ensure_ascii=False, sort_keys=True,
    separators=(",", ":"). Floats are rejected outright so a float can never
    enter the canonical identity with a platform-dependent representation."""
    _reject_floats(obj, "document")
    try:
        text = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProfileError("document cannot be canonicalised: %s" % exc) from exc
    return text.encode("utf-8")


def _reject_floats(node, path):
    if type(node) is float:
        raise ProfileError("%s: float %r is forbidden in canonical form; "
                           "use integer units or 'p/q' rational strings"
                           % (path, node))
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                raise ProfileError("%s: canonical object keys must be strings"
                                   % path)
            _reject_floats(value, "%s.%s" % (path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _reject_floats(value, "%s[%d]" % (path, index))


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ProfileError("duplicate key %r in JSON object; duplicate "
                               "keys are rejected" % key)
        obj[key] = value
    return obj


def _reject_constant(token):
    raise ProfileError("non-finite JSON token %r is rejected; the canonical "
                       "profile contains finite integers and rational strings "
                       "only" % token)


def load_document(path):
    """Parse a profile document, rejecting duplicates and non-finite tokens."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProfileError("%s: document must be UTF-8: %s" % (path, exc)) from exc
    try:
        doc = json.loads(text, object_pairs_hook=_unique_object,
                         parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ProfileError("%s: invalid JSON: %s" % (path, exc)) from exc
    if not isinstance(doc, dict):
        raise ProfileError("%s: the document root must be an object" % path)
    return doc


def canonical_sha256(obj):
    """Full 32-byte SHA256 over the canonical form of the covered document.

    ``INFERENCE_KEY`` is excluded: host-side inference annotations attached
    under that key by tooling never participate in the contract identity.
    """
    covered = {key: value for key, value in obj.items() if key != INFERENCE_KEY}
    return hashlib.sha256(canonical_bytes(covered)).digest()


def slot_profile_sha128(obj):
    """First 16 bytes of the canonical digest, as carried in BOOT/BOOT_ACK."""
    return canonical_sha256(obj)[:16]


def _as_sha128(value, path="expected sha128"):
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        if len(raw) != 16:
            raise ProfileError("%s: must be exactly 16 bytes, got %d"
                               % (path, len(raw)))
        return raw
    if isinstance(value, str):
        try:
            raw = bytes.fromhex(value)
        except ValueError as exc:
            raise ProfileError("%s: %r is not valid hex" % (path, value)) from exc
        if len(raw) != 16:
            raise ProfileError("%s: must decode to exactly 16 bytes" % path)
        return raw
    raise ProfileError("%s: expected 16 bytes or a 32-character hex string" % path)


def verify_profile_digest(obj, sha128):
    """True when the document canonical digest still matches sha128."""
    return slot_profile_sha128(obj) == _as_sha128(sha128)

def _validate_semantics(doc, errors):
    """Cross-field consistency of the frozen candidate (runs without enums)."""
    def note(message):
        errors.append(message)

    if doc.get("schema") != 1:
        note("schema must be the frozen value 1")
    if doc.get("document") != "deepeye_boot_profiles":
        note("document must be the frozen value 'deepeye_boot_profiles'")
    if doc.get("profile_name") != PROFILE_NAME:
        note("profile_name %r is not the frozen enum %r"
             % (doc.get("profile_name"), PROFILE_NAME))
    if doc.get("task_id") != "DEEPEYE-IMPLEMENTATION-20261014":
        note("task_id must stay DEEPEYE-IMPLEMENTATION-20261014")
    if doc.get("task_version") != 1:
        note("task_version must stay 1")
    if doc.get("design_commit") != "1011259415a0916054eb580687612580bc1e5f09":
        note("design_commit must stay the frozen design "
             "1011259415a0916054eb580687612580bc1e5f09")
    if doc.get("immutable_scope_id") != "DEEPEYE-HUMAN-LOCK-20261014/revision1":
        note("immutable_scope_id must stay DEEPEYE-HUMAN-LOCK-20261014/revision1")
    if doc.get("immutable_scope_sha256") != (
            "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"):
        note("immutable_scope_sha256 must stay the human-pinned requirements hash")
    if "sort_keys=True" not in str(doc.get("hash_rule", "")):
        note("hash_rule must state the canonical form "
             "(ensure_ascii=False, sort_keys=True, separators=(',',':'))")
    if doc.get("hardware_enable_eligible") is not False:
        note("hardware_enable_eligible must stay false: this bounded software "
             "candidate never claims ENABLE")

    frames = doc.get("boot_frames")
    frames = frames if isinstance(frames, dict) else {}
    for key, expected in (("BOOT", (BOOT_TYPE, BOOT_PAYLOAD_BYTES, BOOT_FRAME_BYTES)),
                          ("BOOT_ACK", (BOOT_ACK_TYPE, BOOT_PAYLOAD_BYTES,
                                        BOOT_FRAME_BYTES))):
        entry = frames.get(key)
        if not isinstance(entry, dict):
            note("boot_frames.%s is missing" % key)
            continue
        got = (entry.get("type"), entry.get("payload_bytes"),
               entry.get("frame_bytes"))
        if got != expected:
            note("boot_frames.%s %r does not match the frozen ABI3 tuple %r"
                 % (key, got, expected))

    abi = doc.get("abi")
    abi = abi if isinstance(abi, dict) else {}
    for field, expected in (("version", 3), ("magic_hex", "a55a"),
                            ("byte_order", "little"), ("header_bytes", 12),
                            ("crc_bytes", 2), ("max_payload_bytes", 32),
                            ("max_frame_bytes", 46),
                            ("line_bits_per_byte", LINE_BITS_PER_BYTE)):
        if abi.get(field) != expected:
            note("abi.%s must stay %r" % (field, expected))
    if (isinstance(abi.get("header_bytes"), int)
            and isinstance(abi.get("crc_bytes"), int)
            and abi["header_bytes"] + abi["crc_bytes"] != 14):
        note("abi header_bytes + crc_bytes must stay the frozen 14-byte "
             "frame overhead")
    crc = abi.get("crc")
    crc = crc if isinstance(crc, dict) else {}
    for field, expected in (("polynomial", 0x1021), ("initial", 0xffff),
                            ("reflect_input", False), ("reflect_output", False),
                            ("xorout", 0), ("check_ascii_123456789", 0x29b1),
                            ("wire_byte_order", "little")):
        if crc.get(field) != expected:
            note("abi.crc.%s must stay %r" % (field, expected))
    layout = abi.get("frame_layouts_digest")
    layout = layout if isinstance(layout, dict) else {}
    def valid_binding(entry):
        return ((entry.get('mode') == 'runtime_loaded_unverified' and entry.get('value') is None)
                or (entry.get('mode') == 'locally_bound_software_candidate'
                    and isinstance(entry.get('value'), str)
                    and re.fullmatch('[0-9a-f]{64}', entry['value']) is not None))
    if not valid_binding(layout):
        note('abi.frame_layouts_digest must be unknown or a locally bound SHA256')

    digests = doc.get("digests")
    digests = digests if isinstance(digests, dict) else {}
    for name, entry in digests.items():
        if not isinstance(entry, dict):
            note("digests.%s must be an object" % name)
            continue
        if not valid_binding(entry):
            note('digests.%s must be unknown or a locally bound SHA256' % name)
        expected_path = dict(RUNTIME_DIGEST_FILES).get(name)
        if entry.get('path') != expected_path:
            note('digests.%s.path must equal %s' % (name, expected_path))
        if entry.get('mode') != layout.get('mode'):
            note('document and layout bindings must be resolved together')

    topology = doc.get("topology_source_acquisition")
    topology = topology if isinstance(topology, dict) else {}
    for table, constant in (("transport_profile_id", TRANSPORT_IDS),
                            ("source_id", SOURCE_IDS),
                            ("topology_id", TOPOLOGY_IDS),
                            ("acquisition_profile_id", ACQUISITION_IDS)):
        if topology.get(table) != constant:
            note("topology_source_acquisition.%s must equal the frozen enum "
                 "table" % table)
    if topology.get("boot_mode_formula") != BOOT_MODE_FORMULA:
        note("topology_source_acquisition.boot_mode_formula must stay %r"
             % BOOT_MODE_FORMULA)
    if topology.get("reserved_zero_bits") != list(RESERVED_ZERO_BITS):
        note("topology_source_acquisition.reserved_zero_bits must stay [7]")
    if topology.get("zero_or_unknown") != "reject":
        note("topology_source_acquisition.zero_or_unknown must stay 'reject'")

    transports = doc.get("transport_profiles")
    transports = transports if isinstance(transports, dict) else {}
    for name in PROFILE_NAMES:
        entry = transports.get(name)
        if not isinstance(entry, dict):
            note("transport_profiles.%s is missing" % name)
            continue
        if entry.get("baud") != BAUD[name]:
            note("transport_profiles.%s.baud must stay %d for the frozen "
                 "software schedule" % (name, BAUD[name]))
        if entry.get("framing") != FRAMING:
            note("transport_profiles.%s.framing must stay %s" % (name, FRAMING))
        if entry.get("line_bits_per_byte") != LINE_BITS_PER_BYTE:
            note("transport_profiles.%s.line_bits_per_byte must stay %d"
                 % (name, LINE_BITS_PER_BYTE))

    profiles = doc.get("profiles")
    profiles = profiles if isinstance(profiles, dict) else {}
    for name in PROFILE_NAMES:
        _validate_profile(doc, name, profiles.get(name), errors)
    expected_variants = {name: [dict(slot=s, frame=f, bytes=b) for s,f,b in values]
                         for name, values in MODE_VARIANTS.items()}
    if doc.get('mode_variants') != expected_variants:
        note('mode_variants must match the reviewed exclusive frame/slot mapping')

    _validate_speed(doc, errors)
    _validate_ttl(doc, errors)
    _validate_kinematics(doc, errors)
    _validate_pwm(doc, errors)
    _validate_channels(doc, errors)
    _validate_acquisition(doc, errors)
    _validate_time_identities(doc, errors)
    _validate_policy(doc, errors)

    gates = doc.get("remaining_gates")
    if not isinstance(gates, list) or not gates:
        note("remaining_gates must stay a non-empty list of the open product "
             "gates; this candidate closes none of them")
    sources = doc.get("sources")
    if not isinstance(sources, dict):
        note("sources must stay an object of provenance strings")


def _validate_profile(doc, name, profile, errors):
    def note(message):
        errors.append(message)

    if not isinstance(profile, dict):
        note("profiles.%s is missing" % name)
        return
    window = profile.get("window_ms")
    guard = profile.get("guard_total_ms")
    if type(window) is not int or window <= 0:
        note("profiles.%s.window_ms must be a positive integer" % name)
        return
    if type(guard) is not int or guard <= 0:
        note("profiles.%s.guard_total_ms must be a positive integer" % name)
        return
    if guard < GUARD_FLOOR_MS[name]:
        note("profiles.%s.guard_total_ms %d is below the frozen nominal guard "
             "floor %d ms" % (name, guard, GUARD_FLOOR_MS[name]))
    if guard >= window:
        note("profiles.%s.guard_total_ms %d must stay below window_ms %d"
             % (name, guard, window))

    slots = profile.get("slots")
    slots = slots if isinstance(slots, dict) else {}
    for slot, frozen_bytes in SLOT_FRAME_BYTES.items():
        entry = slots.get(slot)
        if not isinstance(entry, dict):
            note("profiles.%s.slots.%s is missing" % (name, slot))
            continue
        if entry.get("max_bytes") != frozen_bytes:
            note("profiles.%s.slots.%s.max_bytes must equal the frozen ABI3 "
                 "worst-case frame size %d B" % (name, slot, frozen_bytes))
        if entry.get("direction") != SLOT_DIRECTIONS[slot]:
            note("profiles.%s.slots.%s.direction must stay %s"
                 % (name, slot, SLOT_DIRECTIONS[slot]))

    def slot_start(slot):
        entry = slots.get(slot)
        if not isinstance(entry, dict):
            return None
        return entry.get("start_ms")

    if slot_start("control_primary") != profile.get("primary_slot_ms"):
        note("profiles.%s.primary_slot_ms must equal "
             "slots.control_primary.start_ms" % name)
    if slot_start("config") != profile.get("config_slot_ms"):
        note("profiles.%s.config_slot_ms must equal slots.config.start_ms" % name)
    control_start = slot_start("control_primary")
    retry_start = slot_start("retry_control")
    if isinstance(control_start, int) and isinstance(retry_start, int):
        if retry_start - control_start != profile.get("retry_offset_ms"):
            note("profiles.%s.retry_offset_ms must equal the fixed "
                 "retry_control - control_primary offset" % name)

    branches = profile.get("branches")
    branches = branches if isinstance(branches, dict) else {}
    for branch in BRANCH_NAMES:
        if branches.get(branch) != BRANCH_SLOTS[branch]:
            note("profiles.%s.branches.%s must stay the frozen half-duplex "
                 "slot order %r" % (name, branch, BRANCH_SLOTS[branch]))
    if profile.get("mutual_exclusions") != MUTUAL_EXCLUSIONS:
        note("profiles.%s.mutual_exclusions must keep config and retry "
             "mutually exclusive inside one window" % name)
    for branch in BRANCH_NAMES:
        errors.extend(validate_branch(doc, name, branch))

    derived = {}
    try:
        derived = response_deadlines_ms(doc, name)
    except ProfileError as exc:
        note(str(exc))
    declared = profile.get("response_deadlines_ms")
    declared = declared if isinstance(declared, dict) else {}
    for key, value in declared.items():
        if key not in derived:
            note("profiles.%s.response_deadlines_ms.%s is not a derived slot "
                 "anchor and must not be invented" % (name, key))
            continue
        try:
            parsed = _rational(value, "profiles.%s.response_deadlines_ms.%s"
                               % (name, key))
        except ProfileError as exc:
            note(str(exc))
            continue
        if parsed != derived[key]:
            note("profiles.%s.response_deadlines_ms.%s=%s does not match the "
                 "derived window/slot anchor %s (response time is anchored to "
                 "the window and slot, never to ACK receipt)"
                 % (name, key, parsed, derived[key]))
    for key in derived:
        if key not in declared:
            note("profiles.%s.response_deadlines_ms is missing %s" % (name, key))

    ai_wait = profile.get("ai_wait")
    ai_wait = ai_wait if isinstance(ai_wait, dict) else {}
    try:
        telem_end = segment_ms(doc, name, "telem")["end_ms"]
        primary_start = Fraction(slot_start_ms(doc, name, "control_primary"))
        if _rational(ai_wait.get("start_ms"), "profiles.%s.ai_wait.start_ms"
                     % name) != telem_end:
            note("profiles.%s.ai_wait.start_ms must equal the TELEM slot end %s"
                 % (name, telem_end))
        if Fraction(ai_wait.get("end_ms")) != primary_start:
            note("profiles.%s.ai_wait.end_ms must equal the primary request "
                 "slot start %s" % (name, primary_start))
    except (ProfileError, TypeError, ValueError) as exc:
        note("profiles.%s.ai_wait is inconsistent with the slot table: %s"
             % (name, exc))
    if ai_wait.get("after_slot") != "telem":
        note("profiles.%s.ai_wait.after_slot must stay 'telem'" % name)
    if ai_wait.get("before_slot") != "control_primary":
        note("profiles.%s.ai_wait.before_slot must stay 'control_primary'" % name)

    branch_bytes = {}
    for branch in BRANCH_NAMES:
        total = 0
        for slot in branches.get(branch, []):
            total += SLOT_FRAME_BYTES.get(slot, 0)
        branch_bytes[branch] = total
    expected_variants = {
        "normal": branch_bytes["normal"],
        "config": branch_bytes["config"],
        "control_retry": branch_bytes["retry"],
        "event_retry": branch_bytes["normal"] + 20,
        "gain_normal": 140,
        "pc_direct_normal": 84,
    }
    variants = profile.get("budget_variants")
    variants = variants if isinstance(variants, dict) else {}
    for variant, expected in expected_variants.items():
        got = variants.get(variant)
        if got != expected:
            note("profiles.%s.budget_variants.%s=%r does not match the frozen "
                 "worst-case byte total %d B" % (name, variant, got, expected))

    event_retry = profile.get("event_retry")
    event_retry = event_retry if isinstance(event_retry, dict) else {}
    if event_retry.get("bytes") != 20:
        note("profiles.%s.event_retry.bytes must stay 20 (single EVENT "
             "retransmission)" % name)
    if event_retry.get("slot") != profile['slots']['retry_control']['start_ms']:
        note('profiles.%s.event_retry.slot must equal the exclusive retry slot anchor' % name)
    if event_retry.get('status') != 'software_slot_selected_measurement_not_run':
        note('profiles.%s.event_retry.status must record a selected software slot with measurement not_run' % name)

    grants = profile.get("grants")
    grants = grants if isinstance(grants, dict) else {}
    for field, expected in (("main_bit", MAIN_GRANT_BIT),
                            ("config_bit", CONFIG_GRANT_BIT),
                            ("retry_pre_grant_bit", RETRY_GRANT_BIT),
                            ("no_grant_no_send", True),
                            ("first_ack_success_suppresses_retry", True)):
        if grants.get(field) != expected:
            note("profiles.%s.grants.%s must stay %r" % (name, field, expected))
    if "bit15" not in str(grants.get("retry_rule", "")) or \
            "bit13" not in str(grants.get("retry_rule", "")) or \
            "bit14" not in str(grants.get("retry_rule", "")):
        note("profiles.%s.grants.retry_rule must state bit15 + bit13 with "
             "bit14 clear" % name)
    if "bit14" not in str(grants.get("config_rule", "")) or \
            "bit13" not in str(grants.get("config_rule", "")):
        note("profiles.%s.grants.config_rule must state bit14 set with bit13 "
             "clear" % name)
    if "ACK" not in str(grants.get("primary_response_anchor", "")):
        note("profiles.%s.grants.primary_response_anchor must anchor the "
             "primary response to window/slot offsets, never ACK receipt" % name)

    targets = profile.get("bounded_targets")
    targets = targets if isinstance(targets, dict) else {}
    if not str(targets.get("status", "")).startswith("unmeasured"):
        note("profiles.%s.bounded_targets.status must declare the targets "
             "unmeasured, never achieved" % name)


def _validate_speed(doc, errors):
    maps = doc.get("speed_mappings")
    maps = maps if isinstance(maps, dict) else {}
    if maps.get("maps_never_mixed") is not True:
        note = ("speed_mappings.maps_never_mixed must stay true: the FAST and "
                "STRESS speed mappings are never mixed")
        errors.append(note)
    for name, anchor in SPEED_ANCHORS.items():
        entry = maps.get(name)
        if not isinstance(entry, dict):
            errors.append("speed_mappings.%s is missing" % name)
            continue
        try:
            per_code = _rational(entry.get("per_code_m_s"),
                                 "speed_mappings.%s.per_code_m_s" % name)
            maximum = _rational(entry.get("max_m_s"),
                                "speed_mappings.%s.max_m_s" % name)
        except ProfileError as exc:
            errors.append(str(exc))
            continue
        if per_code != Fraction(anchor["per_code_m_s"]):
            errors.append("speed_mappings.%s.per_code_m_s must stay %s m/s "
                          "per code" % (name, anchor["per_code_m_s"]))
        if maximum != Fraction(anchor["max_m_s"]):
            errors.append("speed_mappings.%s.max_m_s must stay %s m/s"
                          % (name, anchor["max_m_s"]))
        if per_code > 0 and maximum / per_code != anchor["max_code"]:
            errors.append("speed_mappings.%s must keep the frozen speed_code "
                          "range 0..%d" % (name, anchor["max_code"]))
        if entry.get("ttl_max_ms") != anchor["ttl_max_ms"]:
            errors.append("speed_mappings.%s.ttl_max_ms must stay %d ms"
                          % (name, anchor["ttl_max_ms"]))


def _validate_ttl(doc, errors):
    ttl = doc.get("ttl_and_age")
    ttl = ttl if isinstance(ttl, dict) else {}
    for table in ("hil_observation_age_limit_ms", "pc_direct_observation_age_limit_ms"):
        if ttl.get(table) != OBSERVATION_AGE_MS:
            errors.append("ttl_and_age.%s must stay %r (FAST 1500 ms / STRESS "
                          "12000 ms; repeated ACK/STATE never renews a "
                          "deadline)" % (table, OBSERVATION_AGE_MS))
    if ttl.get("sensor_heartbeat_timeout_ms") != SENSOR_HEARTBEAT_TIMEOUT_MS:
        errors.append("ttl_and_age.sensor_heartbeat_timeout_ms must stay %d ms"
                      % SENSOR_HEARTBEAT_TIMEOUT_MS)
    if ttl.get("summary_samples") != SUMMARY_SAMPLES:
        errors.append("ttl_and_age.summary_samples must stay %r"
                      % (SUMMARY_SAMPLES,))
    if ttl.get("fpga_observation_history") != FPGA_OBSERVATION_HISTORY:
        errors.append("ttl_and_age.fpga_observation_history must stay %d "
                      "recent TELEM entries" % FPGA_OBSERVATION_HISTORY)
    if ttl.get("heartbeat_extends_deadline") is not False:
        errors.append("ttl_and_age.heartbeat_extends_deadline must stay false: "
                      "repeated ACK/STATE never renews the deadline")


def _validate_kinematics(doc, errors):
    kin = doc.get("motion_kinematics")
    kin = kin if isinstance(kin, dict) else {}
    checks = (("angular_rate_quantum_deg_s", Fraction(1, 1000)),
              ("q_min", -15000), ("q_max", 15000),
              ("curvature_limit_per_m", Fraction(1, 2)),
              ("intermediate_bits", 64))
    for field, expected in checks:
        value = kin.get(field)
        try:
            parsed = _rational(value, "motion_kinematics.%s" % field)
        except ProfileError as exc:
            errors.append(str(exc))
            continue
        if parsed != expected:
            errors.append("motion_kinematics.%s must stay %s (frozen "
                          "curvature ROM / kinematic bound)"
                          % (field, expected))
    if kin.get("zero_speed_requires_zero_q") is not True:
        errors.append("motion_kinematics.zero_speed_requires_zero_q must stay "
                      "true")
    rom = str(kin.get("rom_check", ""))
    if "floor" not in rom or "64" not in rom:
        errors.append("motion_kinematics.rom_check must state the 64-bit "
                      "integer floor check; the quantized bound is rejected "
                      "rather than clipped")


def _validate_pwm(doc, errors):
    pwm = doc.get("pwm_capture")
    pwm = pwm if isinstance(pwm, dict) else {}
    if pwm.get("period_ms") != 20:
        errors.append("pwm_capture.period_ms must stay 20 ms")
    period_ticks = pwm.get("period_ticks")
    clock_hz = pwm.get("clock_hz")
    if period_ticks != 2000000:
        errors.append("pwm_capture.period_ticks must stay 2000000 "
                      "(20 ms at 100 MHz)")
    if clock_hz != 100000000:
        errors.append("pwm_capture.clock_hz must stay the 100 MHz capture clock")
    if isinstance(period_ticks, int) and period_ticks != 20 * 100000000 // 1000:
        errors.append("pwm_capture.period_ticks must equal the 20 ms capture "
                      "period at 100 MHz")
    if pwm.get("angle_high_ticks") != "10000+16*(q+15000)":
        errors.append("pwm_capture.angle_high_ticks must stay "
                      "10000+16*(q+15000)")
    if pwm.get("speed_high_ticks") != "50000+1000*speed_code":
        errors.append("pwm_capture.speed_high_ticks must stay "
                      "50000+1000*speed_code")
    if pwm.get("angle_high_ms_range") != ["1/10", "49/10"]:
        errors.append("pwm_capture.angle_high_ms_range must stay ['1/10', "
                      "'49/10'] (0.1-4.9 ms)")
    if pwm.get("speed_high_ms_range") != ["1/2", "7/10"]:
        errors.append("pwm_capture.speed_high_ms_range must stay ['1/2', "
                      "'7/10'] (0.5-0.7 ms)")
    tolerance = str(pwm.get("capture_tolerance_ticks", ""))
    if "2 tick" not in tolerance and "2 ticks" not in tolerance:
        errors.append("pwm_capture.capture_tolerance_ticks must state the "
                      "<=2 tick capture tolerance")
    if "8 tick" not in tolerance and "8 ticks" not in tolerance:
        errors.append("pwm_capture.capture_tolerance_ticks must state the "
                      "strictly-less-than-half-code 8 tick separation")


def _validate_channels(doc, errors):
    channels = doc.get("channels")
    channels = channels if isinstance(channels, list) else []
    ids = [entry.get("id") for entry in channels if isinstance(entry, dict)]
    names = [entry.get("name") for entry in channels if isinstance(entry, dict)]
    if ids != [1, 2, 3, 4] or names != list(CHANNEL_NAMES):
        errors.append("channels must stay the frozen simulation_contract_final "
                      "sensor channel list %r" % (list(CHANNEL_NAMES),))
    for entry in channels:
        if not isinstance(entry, dict):
            errors.append("channels entries must be objects")
            continue
        label = "channels[%r]" % entry.get("id")
        if not str(entry.get("status", "")).startswith("unverified"):
            errors.append("%s.status must stay unverified pending calibration"
                          % label)
        for field in ("quantity", "unit", "conversion", "calibration_reference"):
            if entry.get(field) is not None:
                errors.append("%s.%s must stay null: unverified channel "
                              "physical quantity, unit, conversion and "
                              "calibration reference may not be fabricated"
                              % (label, field))


def _validate_acquisition(doc, errors):
    acq = doc.get("acquisition_profiles")
    acq = acq if isinstance(acq, dict) else {}
    for name, enum_id in ACQUISITION_IDS.items():
        entry = acq.get(name)
        if not isinstance(entry, dict):
            errors.append("acquisition_profiles.%s is missing" % name)
            continue
        if entry.get("enum_id") != enum_id:
            errors.append("acquisition_profiles.%s.enum_id must stay the "
                          "frozen enum %d" % (name, enum_id))
        if not str(entry.get("status", "")).startswith("unverified"):
            errors.append("acquisition_profiles.%s.status must stay unverified "
                          "and uncalibrated" % name)
        if entry.get("shared_scaling_with") is not None:
            errors.append("acquisition_profiles.%s.shared_scaling_with must "
                          "stay null: FORCE and real PGA mappings remain "
                          "explicit separately uncalibrated rather than a "
                          "fake common scaling" % name)
        if entry.get("calibration") is not None:
            errors.append("acquisition_profiles.%s.calibration must stay null "
                          "until independently verified" % name)
    em = acq.get("em_surrogate_v2")
    em = em if isinstance(em, dict) else {}
    if em.get("source_mode") != "twin_fixture":
        errors.append("acquisition_profiles.em_surrogate_v2.source_mode must "
                      "stay twin_fixture")
    if em.get("channels") != [1, 2, 3, 4]:
        errors.append("acquisition_profiles.em_surrogate_v2.channels must stay "
                      "the four simulation channels [1, 2, 3, 4]")
    for name in ("force_lithology_v1", "pga_voltage_v1"):
        entry = acq.get(name)
        entry = entry if isinstance(entry, dict) else {}
        if entry.get("mapping") != "explicit_separate_uncalibrated":
            errors.append("acquisition_profiles.%s.mapping must stay "
                          "explicit_separate_uncalibrated" % name)


def _validate_time_identities(doc, errors):
    identities = doc.get("time_measurement_identities")
    identities = identities if isinstance(identities, dict) else {}
    for name, unit in TIME_IDENTITY_UNITS.items():
        entry = identities.get(name)
        if not isinstance(entry, dict):
            errors.append("time_measurement_identities.%s is missing" % name)
            continue
        if entry.get("unit") != unit:
            errors.append("time_measurement_identities.%s.unit must stay %r"
                          % (name, unit))
        if entry.get("value") is not None:
            errors.append("time_measurement_identities.%s.value must stay "
                          "null: unverified_not_measured; only an "
                          "independently verified measurement record bound to "
                          "operation_id, request_hash and tested_commit may "
                          "fill it" % name)
        if entry.get("status") != "unverified_not_measured":
            errors.append("time_measurement_identities.%s.status must stay "
                          "unverified_not_measured" % name)
        if entry.get("required_evidence") != MEASUREMENT_EVIDENCE:
            errors.append("time_measurement_identities.%s.required_evidence "
                          "must state the independently verified measurement "
                          "record requirement" % name)


def _validate_policy(doc, errors):
    policy = doc.get("policy")
    policy = policy if isinstance(policy, dict) else {}
    for field in ("no_grant_no_send", "first_ack_success_suppresses_retry",
                  "no_fabricated_measurements"):
        if policy.get(field) is not True:
            errors.append("policy.%s must stay true" % field)
    text_checks = (
        ("retry_pair_grants", ("bit15", "bit13", "bit14")),
        ("config_grant", ("bit14", "bit13")),
        ("event_scheduling", ("allocated slot",)),
        ("late_candidate", ("never shifted",)),
        ("ack_miss_retry", ("retry_offset_ms",)),
        ("profile_or_mode_switch", ("stop", "new session")),
        ("enable_claim", ("never",)),
    )
    for field, needles in text_checks:
        text = str(policy.get(field, ""))
        for needle in needles:
            if needle not in text:
                errors.append("policy.%s must state %r" % (field, needle))


def _validate_enums(doc, enums, errors):
    """Cross-check the frozen enum tables against the host enums draft."""
    names = None
    if isinstance(enums, dict):
        table = enums.get("acquisition_profile_id")
        if isinstance(table, dict):
            names = set(table)
        for key, constant in (("transport_profile_id", TRANSPORT_IDS),
                              ("source_id", SOURCE_IDS),
                              ("topology_id", TOPOLOGY_IDS),
                              ("acquisition_profile_id", ACQUISITION_IDS)):
            if key in enums and enums[key] != constant:
                errors.append("enum %s in the host enums document does not "
                              "match the frozen enum table in the profile "
                              "document" % key)
    profile_name = doc.get("profile_name")
    if names is not None and profile_name not in names:
        errors.append("profile_name %r is not in the host enum "
                      "acquisition_profile_id" % (profile_name,))
    elif names is None and profile_name != PROFILE_NAME:
        errors.append("profile_name %r is not the frozen enum %r"
                      % (profile_name, PROFILE_NAME))


def validate_document(doc, enums=None):
    """Strict validation. Returns a list of human-readable errors ([] == ok).

    Rejects duplicate keys and non-finite tokens at load time; here rejects
    floats, boolean-as-integer, unknown keys, missing required keys, enum
    drift, guard/budget inconsistencies and any attempt to fill an unverified
    measurement field. Pure: it never reads files or touches hardware.
    """
    if not isinstance(doc, dict):
        return ["missing: the document root must be an object"]
    errors = []
    _scan_types(doc, (), errors)
    _walk(doc, _DOCUMENT_SCHEMA, "document", errors)
    _validate_semantics(doc, errors)
    if enums is not None:
        _validate_enums(doc, enums, errors)
    return errors

def _profile(doc, name):
    profiles = doc.get("profiles")
    if not isinstance(profiles, dict) or name not in profiles:
        raise ProfileError("unknown transport/profile %r" % (name,))
    profile = profiles[name]
    if not isinstance(profile, dict):
        raise ProfileError("profiles.%s must be an object" % name)
    return profile


def _slot_def(profile, slot):
    slots = profile.get("slots")
    if not isinstance(slots, dict) or slot not in slots:
        raise ProfileError("unknown slot %r" % (slot,))
    entry = slots[slot]
    if not isinstance(entry, dict):
        raise ProfileError("slot %r must be an object" % (slot,))
    return entry


def _baud(doc, name):
    transports = doc.get("transport_profiles")
    entry = transports.get(name) if isinstance(transports, dict) else None
    if not isinstance(entry, dict) or type(entry.get("baud")) is not int:
        raise ProfileError("transport_profiles.%s.baud is not a frozen "
                           "integer" % name)
    return entry["baud"]


def _line_bits(doc, name):
    transports = doc.get("transport_profiles")
    entry = transports.get(name) if isinstance(transports, dict) else None
    if not isinstance(entry, dict):
        raise ProfileError("transport_profiles.%s is missing" % name)
    bits = entry.get("line_bits_per_byte", LINE_BITS_PER_BYTE)
    if type(bits) is not int or bits <= 0:
        raise ProfileError("transport_profiles.%s.line_bits_per_byte must be a "
                           "positive integer" % name)
    return bits


def slot_start_ms(doc, name, slot, k=0):
    """Absolute window start (ms) of a slot in period k. Slots never shift."""
    profile = _profile(doc, name)
    entry = _slot_def(profile, slot)
    start = entry.get("start_ms")
    if type(start) is not int or start < 0:
        raise ProfileError("slot %s start_ms must be a non-negative integer"
                           % slot)
    window = profile.get("window_ms")
    if type(window) is not int or window <= 0:
        raise ProfileError("profiles.%s.window_ms must be a positive integer"
                           % name)
    if type(k) is not int or k < 0:
        raise ProfileError("period index k must be a non-negative integer")
    return start + k * window


def segment_ms(doc, name, slot, k=0):
    """Worst-case occupied segment of one slot as exact rational millis."""
    profile = _profile(doc, name)
    entry = _slot_def(profile, slot)
    max_bytes = entry.get("max_bytes")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ProfileError("slot %s max_bytes must be a positive integer"
                           % slot)
    start = Fraction(slot_start_ms(doc, name, slot, k=k))
    end = start + Fraction(max_bytes * _line_bits(doc, name) * 1000,
                           _baud(doc, name))
    return {"slot": slot, "start_ms": start, "end_ms": end,
            "bytes": max_bytes, "direction": entry.get("direction")}


def branch_segments(doc, name, branch):
    """Segments of one branch in frozen table order (config includes the
    config/CONFIG_ACK pair; retry includes the retry request/ACK pair)."""
    profile = _profile(doc, name)
    branches = profile.get("branches")
    if not isinstance(branches, dict) or branch not in branches:
        raise ProfileError("unknown branch %r" % (branch,))
    return [segment_ms(doc, name, slot) for slot in branches[branch]]


def validate_branch(doc, name, branch):
    """Half-duplex sanity of one window branch: ordered, disjoint, inside the
    window, and the trailing margin must honour the declared guard budget."""
    try:
        profile = _profile(doc, name)
        segments = branch_segments(doc, name, branch)
    except ProfileError as exc:
        return [str(exc)]
    errors = []
    window = profile.get("window_ms")
    guard = profile.get("guard_total_ms")
    if type(window) is not int or window <= 0:
        return ["profiles.%s.window_ms must be a positive integer" % name]
    if type(guard) is not int or guard < 0:
        return ["profiles.%s.guard_total_ms must be a non-negative integer"
                % name]
    last_end = Fraction(0)
    for seg in segments:
        if seg["start_ms"] < last_end:
            errors.append("profiles.%s.branches.%s: slot %s starts at %s ms "
                          "before the previous segment ends at %s ms; "
                          "half-duplex segments must be ordered and disjoint"
                          % (name, branch, seg["slot"], seg["start_ms"],
                             last_end))
        last_end = max(last_end, seg["end_ms"])
        if seg["end_ms"] > window:
            errors.append("profiles.%s.branches.%s: slot %s ends at %s ms "
                          "beyond the %d ms window"
                          % (name, branch, seg["slot"], seg["end_ms"], window))
    margin = Fraction(window) - last_end
    if margin < guard:
        errors.append("profiles.%s.branches.%s: guard budget %d ms exceeds the "
                      "remaining window margin %s ms (window %d ms, last "
                      "segment end %s ms)"
                      % (name, branch, guard, margin, window, last_end))
    return errors


def window_budget(doc, name, variant):
    """Frozen worst-case window budget: wire bytes plus the cumulative guard,
    as seconds and as an exact fraction of the window."""
    profile = _profile(doc, name)
    variants = profile.get("budget_variants")
    if not isinstance(variants, dict) or variant not in variants:
        raise ProfileError("unknown budget variant %r" % (variant,))
    wire_bytes = variants[variant]
    if type(wire_bytes) is not int or wire_bytes <= 0:
        raise ProfileError("budget variant %r must be a positive integer byte "
                           "count" % (variant,))
    seconds = (Fraction(wire_bytes * _line_bits(doc, name), _baud(doc, name))
               + Fraction(profile["guard_total_ms"], 1000))
    return {"wire_bytes": wire_bytes, "seconds": seconds,
            "fraction": seconds / Fraction(profile["window_ms"], 1000)}


def rolling_window_max_bytes(doc, name, branch, periods=3):
    """Maximum serialized byte-equivalent occupancy, including partial frames.

    Piecewise-linear occupancy changes slope at frame boundaries or those
    boundaries minus the window duration; testing all those points is exact.
    """
    if type(periods) is not int or periods < 3:
        raise ProfileError("rolling window occupancy must be checked across at "
                           "least 3 periods")
    profile = _profile(doc, name)
    window = profile.get("window_ms")
    if type(window) is not int or window <= 0:
        raise ProfileError("profiles.%s.window_ms must be a positive integer"
                           % name)
    segments = []
    for k in range(periods + 1):
        segments.extend(segment_ms(doc, name, slot, k=k)
                        for slot in branch_segments_slots(doc, name, branch))
    candidates = {Fraction(0)}
    for seg in segments:
        candidates.add(seg["start_ms"])
        candidates.add(seg["end_ms"])
        candidates.add(seg['start_ms'] - window)
        candidates.add(seg['end_ms'] - window)
    best = 0
    for candidate in sorted(candidates):
        if candidate < 0 or candidate > (periods - 1) * window:
            continue
        limit = candidate + window
        total = occupied_bytes(segments, candidate, limit)
        best = max(best, total)
    return best


def occupied_bytes(segments, lower_ms, upper_ms):
    """Exact serial occupancy over [lower, upper), not whole-frame counting."""
    if upper_ms < lower_ms:
        raise ProfileError('rolling interval is reversed')
    total = Fraction(0)
    for seg in segments:
        duration = seg['end_ms'] - seg['start_ms']
        if duration <= 0:
            raise ProfileError('serial segment duration must be positive')
        overlap = max(Fraction(0), min(upper_ms, seg['end_ms']) - max(lower_ms, seg['start_ms']))
        total += Fraction(seg['bytes']) * overlap / duration
    return total


def mode_segments(doc, name, variant, period=0):
    """Exclusive per-mode schedule; PC_DIRECT carries STATE32 and no motion TX."""
    if variant not in BUDGET_VARIANTS:
        raise ProfileError('unknown schedule variant')
    profile = _profile(doc, name)
    segments = []
    for item in doc['mode_variants'][variant]:
        base = segment_ms(doc, name, item['slot'], k=period)
        base.update(frame=item['frame'], bytes=item['bytes'])
        base['direction'] = 'downlink' if item['frame'] in ('CONTROL3D', 'CONFIG', 'GAIN') else 'uplink'
        base['end_ms'] = base['start_ms'] + Fraction(item['bytes'] * _line_bits(doc, name) * 1000, _baud(doc, name))
        segments.append(base)
    return segments


def verify_all_mode_schedules(doc):
    """Exact nominal line proof across all triples of exclusive mode windows.

    Mode switches in a live run still require STOP and BOOT; testing all mixed
    triples is a conservative occupancy stress test, not permission to switch.
    Reserved event/retry slots are charged even if unused. Silence between
    anchored slots remains in the timeline. Actual measured jitter is absent.
    """
    errors = validate_document(doc)
    if errors: raise ProfileError('; '.join(errors))
    result = {'scope': 'software nominal timing only; measured jitter/turnaround not_run', 'profiles': {}}
    for name in PROFILE_NAMES:
        p = _profile(doc, name); window = p['window_ms']; variants = {}
        for variant in BUDGET_VARIANTS:
            segs = mode_segments(doc, name, variant)
            end = Fraction(0)
            for seg in segs:
                if seg['start_ms'] < end: raise ProfileError('overlapping half-duplex slots')
                end = seg['end_ms']
            if window - end < p['guard_total_ms']: raise ProfileError('trailing guard is insufficient')
            total = sum(x['bytes'] for x in segs)
            if total != BUDGET_VARIANT_ANCHORS[variant]: raise ProfileError('mode byte budget differs')
            variants[variant] = dict(wire_bytes=total, last_end_ms=str(end), trailing_margin_ms=str(window-end))
        maximum = Fraction(0); cases = 0
        for triple in itertools.product(BUDGET_VARIANTS, repeat=3):
            segs = [s for k,v in enumerate(triple) for s in mode_segments(doc, name, v, k)]
            boundaries = {Fraction(0), Fraction(2*window)}
            for s in segs:
                boundaries.update([s['start_ms'], s['end_ms'], s['start_ms']-window, s['end_ms']-window])
            for start in boundaries:
                if 0 <= start <= 2*window:
                    maximum = max(maximum, occupied_bytes(segs, start, start+window))
            cases += 1
        if maximum > 214: raise ProfileError('sliding occupancy exceeds the maximal reserved window')
        result['profiles'][name] = dict(variants=variants, mixed_triples_checked=cases,
                                        maximum_sliding_byte_equivalents=str(maximum))
    return result


def branch_segments_slots(doc, name, branch):
    profile = _profile(doc, name)
    branches = profile.get("branches")
    if not isinstance(branches, dict) or branch not in branches:
        raise ProfileError("unknown branch %r" % (branch,))
    return branches[branch]


def ceil_ms(value):
    """Ceiling to whole milliseconds (upper bounds always round up)."""
    if type(value) is int:
        return value
    if isinstance(value, Fraction):
        return -(-value.numerator // value.denominator)
    raise ProfileError("ceil_ms expects an int or Fraction, got %r" % (value,))


def response_deadlines_ms(doc, name):
    """Response deadlines anchored to window/slot offsets, never to ACK
    receipt. Values are exact Fractions of milliseconds."""
    return {
        "retry_decision_ms": Fraction(slot_start_ms(doc, name, "retry_control")),
        "primary_ack_latest_ms": segment_ms(doc, name, "ack_primary")["end_ms"],
        "retry_ack_latest_ms": segment_ms(doc, name, "retry_ack")["end_ms"],
        "config_ack_latest_ms": segment_ms(doc, name, "config_ack")["end_ms"],
    }


def grant_mask_errors(mask):
    """Grant-quality decisions. bit15 main, bit14 config, bit13 retry pre-grant
    (bit13 only together with bit15 and with bit14 clear); no grant, no send."""
    if type(mask) is not int:
        return ["grant mask must be an unsigned integer"]
    if not 0 <= mask <= 0xffff:
        return ["grant mask %r is outside the 16-bit quality word" % (mask,)]
    errors = []
    allowed = ((1 << MAIN_GRANT_BIT) | (1 << CONFIG_GRANT_BIT)
               | (1 << RETRY_GRANT_BIT))
    reserved = mask & ~allowed
    if reserved:
        errors.append("grant mask %#06x sets bits outside the frozen grant "
                      "bits 13-15 (reserved %#06x)" % (mask, reserved))
    main = bool(mask & (1 << MAIN_GRANT_BIT))
    config = bool(mask & (1 << CONFIG_GRANT_BIT))
    retry = bool(mask & (1 << RETRY_GRANT_BIT))
    if retry and not main:
        errors.append("retry pre-grant bit13 requires main grant bit15 (no "
                      "grant means no send)")
    if retry and config:
        errors.append("bit13 and bit14 must not be set together (config and "
                      "retry are mutually exclusive inside one window)")
    return errors


def plan_window(doc, name, grants, first_ack_ok):
    """Bounded software plan for one window.

    Config and retry branches are mutually exclusive; the retry pair is only
    allowed with grants bit15 + bit13 and bit14 clear; the first successful
    ACK suppresses the retry; a lost grant or lost ACK defers to the next full
    window without shifting any slot.
    """
    errors = grant_mask_errors(grants)
    if errors:
        raise ProfileError("; ".join(errors))
    config_grant = bool(grants & (1 << CONFIG_GRANT_BIT))
    main_grant = bool(grants & (1 << MAIN_GRANT_BIT))
    retry_pre = bool(grants & (1 << RETRY_GRANT_BIT))
    transmits = ["event", "telem"]
    advisories = []
    retry_used = False
    retry_suppressed = False
    if main_grant:
        transmits += ["control_primary", "ack_primary"]
    transmits.append("state")
    if config_grant:
        transmits += ["config", "config_ack"]
        advisories.append("config_branch_selected")
    elif main_grant and not first_ack_ok and retry_pre:
        retry_used = True
        transmits += ["retry_control", "retry_ack"]
    elif main_grant and first_ack_ok and retry_pre:
        retry_suppressed = True
        advisories.append("first_ack_success_suppresses_retry")
    elif main_grant:
        advisories.append("defer_next_window")
    else:
        advisories.append("no_grant_no_send")
    branch = "config" if config_grant else ("retry" if retry_used else "normal")
    branch_errors = validate_branch(doc, name, branch)
    if branch_errors:
        raise ProfileError("; ".join(branch_errors))
    return {"transmits": transmits, "retry_used": retry_used,
            "retry_suppressed": retry_suppressed, "advisories": advisories,
            "branch": branch}


def late_candidate_action(doc, name, ready_ms, deadline_ms,
                          slot="control_primary"):
    """A candidate that misses its allocated slot defers to the next full
    window slot or stops; slots are never shifted."""
    if type(ready_ms) is not int and not isinstance(ready_ms, Fraction):
        raise ProfileError("ready_ms must be an integer or Fraction")
    if type(deadline_ms) is not int and not isinstance(deadline_ms, Fraction):
        raise ProfileError("deadline_ms must be an integer or Fraction")
    ready = Fraction(ready_ms)
    deadline = Fraction(deadline_ms)
    if ready < 0:
        raise ProfileError("ready_ms must not be negative")
    start = Fraction(slot_start_ms(doc, name, slot))
    clean = {"slot": slot, "ready_ms": ready, "deadline_ms": deadline}
    if ready <= start:
        action = dict(clean)
        action.update({"action": "send", "start_ms": start})
        return action
    if ready >= deadline:
        action = dict(clean)
        action.update({
            "action": "stop",
            "reason": "deadline reached; the candidate stops and slots are "
                      "never shifted",
        })
        return action
    window = Fraction(_profile(doc, name)["window_ms"])
    offset = ready - start
    periods = -(-offset // window)
    deferred = start + periods * window
    if deferred >= deadline:
        action = dict(clean)
        action.update({
            "action": "stop",
            "deferred_start_ms": deferred,
            "reason": "the next full window slot would arrive at or after the "
                      "deadline",
        })
        return action
    action = dict(clean)
    action.update({"action": "defer", "deferred_start_ms": deferred,
                   "reason": "ready after the allocated slot; defer to the "
                             "next full window without shifting slots"})
    return action


def speed_m_s(doc, name, code):
    """Exact speed for a speed_code inside the profile mapping. The FAST and
    STRESS mappings are never mixed; a code outside 0..20 is rejected."""
    maps = doc.get("speed_mappings")
    entry = maps.get(name) if isinstance(maps, dict) else None
    if not isinstance(entry, dict):
        raise ProfileError("speed_mappings.%s is missing" % name)
    per_code = _rational(entry.get("per_code_m_s"),
                         "speed_mappings.%s.per_code_m_s" % name)
    maximum = _rational(entry.get("max_m_s"), "speed_mappings.%s.max_m_s" % name)
    if per_code <= 0 or maximum <= 0:
        raise ProfileError("speed_mappings.%s must be positive" % name)
    max_code = maximum / per_code
    if max_code.denominator != 1:
        raise ProfileError("speed_mappings.%s max_m_s is not an integer "
                           "multiple of per_code_m_s; the mapping is "
                           "inconsistent" % name)
    if type(code) is not int or type(code) is bool:
        raise ProfileError("speed_code must be an integer")
    if not 0 <= code <= max_code:
        raise ProfileError("speed_code %d is outside 0..%d for %s"
                           % (code, max_code, name))
    return per_code * code


def _name_for_id(table, value, label):
    for name, ident in table.items():
        if ident == value:
            return name
    raise ProfileError("boot mode %s field %r is not a frozen enum value; "
                       "zero or unknown fields are rejected" % (label, value))


def compose_boot_mode(transport, source, topology):
    """boot_mode = transport_profile_id | (source_id << 2) | (topology_id << 5).
    Reserved bit 7 stays zero; zero or unknown fields are rejected."""
    if transport not in TRANSPORT_IDS:
        raise ProfileError("unknown transport profile enum %r" % (transport,))
    if source not in SOURCE_IDS:
        raise ProfileError("unknown source enum %r" % (source,))
    if topology not in TOPOLOGY_IDS:
        raise ProfileError("unknown topology enum %r" % (topology,))
    return TRANSPORT_IDS[transport] | (SOURCE_IDS[source] << 2) \
        | (TOPOLOGY_IDS[topology] << 5)


def parse_boot_mode(mode):
    """Decode one boot mode byte into its frozen enum names."""
    if type(mode) is not int or type(mode) is bool:
        raise ProfileError("boot mode must be an integer byte")
    if not 0 <= mode <= 0xff:
        raise ProfileError("boot mode %r is outside one byte" % (mode,))
    if mode & 0x80:
        raise ProfileError("boot mode sets reserved zero bit 7")
    transport_id = mode & 0b11
    source_id = (mode >> 2) & 0b111
    topology_id = (mode >> 5) & 0b11
    if transport_id == 0:
        raise ProfileError("boot mode transport profile field is zero; zero "
                           "fields are rejected")
    if source_id == 0:
        raise ProfileError("boot mode source field is zero; zero fields are "
                           "rejected")
    if topology_id == 0:
        raise ProfileError("boot mode topology field is zero; zero fields are "
                           "rejected")
    return {
        "mode": mode,
        "transport": _name_for_id(TRANSPORT_IDS, transport_id,
                                  "transport profile"),
        "source": _name_for_id(SOURCE_IDS, source_id, "source"),
        "topology": _name_for_id(TOPOLOGY_IDS, topology_id, "topology"),
    }


def _u32(value, path):
    if type(value) is not int or type(value) is bool or not 0 <= value <= 0xffffffff:
        raise ProfileError("%s must be an unsigned 32-bit integer" % path)
    return value


def _u16(value, path):
    if type(value) is not int or type(value) is bool or not 0 <= value <= 0xffff:
        raise ProfileError("%s must be an unsigned 16-bit integer" % path)
    return value


def boot_payload(doc, session, mode):
    """27-byte BOOT payload: session4, mode1, slot_profile_sha128 16,
    guard_total_ms2, primary_slot_ms2, config_slot_ms2 (little endian)."""
    session = _u32(session, "session")
    parse_boot_mode(mode)
    profile = _profile(doc, parse_boot_mode(mode)["transport"])
    return _pack_boot_payload(session, mode, slot_profile_sha128(doc),
                              profile.get("guard_total_ms"),
                              profile.get("primary_slot_ms"),
                              profile.get("config_slot_ms"))


def _pack_boot_payload(session, mode, sha128, guard, primary, config):
    return _BOOT_PAYLOAD.pack(
        _u32(session, "session"), mode, sha128,
        _u16(guard, "guard_total_ms"), _u16(primary, "primary_slot_ms"),
        _u16(config, "config_slot_ms"))


def parse_boot_payload(payload):
    """Decode a 27-byte BOOT/BOOT_ACK payload; bad mode bytes are rejected."""
    if not isinstance(payload, (bytes, bytearray)):
        raise ProfileError("boot payload must be bytes")
    payload = bytes(payload)
    if len(payload) != BOOT_PAYLOAD_BYTES:
        raise ProfileError("boot payload must be exactly %d bytes, got %d"
                           % (BOOT_PAYLOAD_BYTES, len(payload)))
    session, mode, sha128, guard, primary, config = _BOOT_PAYLOAD.unpack(payload)
    parse_boot_mode(mode)
    return {"session": session, "mode": mode,
            "slot_profile_sha128": sha128.hex(),
            "guard_total_ms": guard, "primary_slot_ms": primary,
            "config_slot_ms": config}


def boot_frame(doc, session, mode, config_epoch=0, sequence=0, tick_ms=0):
    """BOOT frame (type 12, 41 B) over the frozen ABI3 wire encoder."""
    payload = boot_payload(doc, session, mode)
    return wire.encode(wire.Frame(BOOT_TYPE, config_epoch, sequence, tick_ms,
                                  payload))


def boot_ack_frame(doc, session, mode, config_epoch=0, sequence=0, tick_ms=0,
                   guard_override_ms=None, primary_override_ms=None,
                   config_override_ms=None, sha128_override=None):
    """BOOT_ACK echo (type 13, 41 B). Overrides exist so tests can build
    deliberately mismatching acknowledgements; the normal call echoes the
    document exactly."""
    session = _u32(session, "session")
    profile = _profile(doc, parse_boot_mode(mode)["transport"])
    guard = profile.get("guard_total_ms") if guard_override_ms is None \
        else guard_override_ms
    primary = profile.get("primary_slot_ms") if primary_override_ms is None \
        else primary_override_ms
    config = profile.get("config_slot_ms") if config_override_ms is None \
        else config_override_ms
    sha128 = slot_profile_sha128(doc) if sha128_override is None \
        else _as_sha128(sha128_override, "sha128_override")
    payload = _pack_boot_payload(session, mode, sha128, guard, primary, config)
    return wire.encode(wire.Frame(BOOT_ACK_TYPE, config_epoch, sequence,
                                  tick_ms, payload))


def _decode_typed(packet, expected_type, label):
    frame = wire.decode(packet)
    if frame.type_id != expected_type:
        raise ValueError("frame type %d is not %s (%d)"
                         % (frame.type_id, label, expected_type))
    return frame


def parse_boot_frame(packet):
    frame = _decode_typed(packet, BOOT_TYPE, "BOOT")
    parsed = parse_boot_payload(frame.payload)
    parsed["type"] = BOOT_TYPE
    parsed["config_epoch"] = frame.config_epoch
    parsed["sequence"] = frame.sequence
    parsed["tick_ms"] = frame.tick_ms
    return parsed


def parse_boot_ack_frame(packet):
    frame = _decode_typed(packet, BOOT_ACK_TYPE, "BOOT_ACK")
    parsed = parse_boot_payload(frame.payload)
    parsed["type"] = BOOT_ACK_TYPE
    parsed["config_epoch"] = frame.config_epoch
    parsed["sequence"] = frame.sequence
    parsed["tick_ms"] = frame.tick_ms
    return parsed


def verify_boot_ack(req, ack, expected_epoch=None):
    """Exact-equality match of the BOOT_ACK echo against the request. Any
    difference is a mismatch: an inconsistent profile must not ENABLE."""
    try:
        request = parse_boot_frame(req)
        response = parse_boot_ack_frame(ack)
    except (ValueError, ProfileError) as exc:
        return {"ok": False, "mismatches": ["malformed"], "error": str(exc)}
    mismatches = []
    for field in ("session", "mode", "slot_profile_sha128", "guard_total_ms",
                  "primary_slot_ms", "config_slot_ms", "sequence"):
        if request[field] != response[field]:
            mismatches.append(field)
    if expected_epoch is None:
        expected_epoch = request['config_epoch']
    if response["config_epoch"] != expected_epoch:
        mismatches.append("config_epoch")
    return {"ok": not mismatches, "mismatches": mismatches}


def bind_software_documents(doc, prod_root):
    """Bind actual protocol bytes into a candidate BOOT hash; no ENABLE proof.

    The template remains unchanged. Verify these bindings again before using
    the candidate: local hashing establishes byte identity, never hardware
    measurements, process isolation, calibration or peer interoperability.
    """
    errors = validate_document(doc)
    if errors:
        raise ProfileError('; '.join(errors))
    root = Path(prod_root).resolve()
    bound = copy.deepcopy(doc)
    for key, rel in RUNTIME_DIGEST_FILES:
        path = (root / rel).resolve()
        path.relative_to(root)
        bound['digests'][key] = dict(path=rel, mode='locally_bound_software_candidate',
            value=hashlib.sha256(path.read_bytes()).hexdigest())
    interface = load_document(root / 'docs/interface.json')
    layouts = interface['frames']
    if {frame['type'] for frame in layouts.values()} != set(wire.PAYLOAD_LENGTHS):
        raise ProfileError('interface frame set differs from wire implementation')
    for frame in layouts.values():
        if (frame['type'] not in wire.PAYLOAD_LENGTHS
                or wire.PAYLOAD_LENGTHS[frame['type']] != frame['payload_bytes']
                or frame['frame_bytes'] != frame['payload_bytes'] + 14):
            raise ProfileError('interface frame layout differs from wire implementation')
    bound['abi']['frame_layouts_digest'].update(
        mode='locally_bound_software_candidate',
        value=hashlib.sha256(canonical_bytes(layouts)).hexdigest())
    return bound


def verify_software_bindings(doc, prod_root):
    """Return mismatched dependency names; an empty list grants no motion."""
    expected = bind_software_documents(doc, prod_root)
    mismatches = [key for key, _ in RUNTIME_DIGEST_FILES
                  if doc['digests'][key] != expected['digests'][key]]
    if doc['abi']['frame_layouts_digest'] != expected['abi']['frame_layouts_digest']:
        mismatches.append('frame_layouts')
    return mismatches


def runtime_digests(prod_root):
    """Capture the current bytes of the concurrently drafted parent documents.

    Modes stay runtime_loaded_unverified / computed_at_runtime_unverified:
    this candidate never claims a frozen host schema or frame-layout digest.
    """
    root = Path(prod_root)
    digests = {}
    for key, rel in RUNTIME_DIGEST_FILES:
        path = root / rel
        if not path.is_file():
            raise ProfileError("runtime digest capture failed: %s is missing "
                               "under %s" % (rel, root))
        digests[key] = {
            "path": rel,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mode": "runtime_loaded_unverified",
        }
    digests["frame_layouts"] = {
        "mode": "computed_at_runtime_unverified",
        "sha256": None,
        "source": "docs/interface.json frames plus integration/wire.py "
                  "PAYLOAD_LENGTHS",
    }
    return digests
