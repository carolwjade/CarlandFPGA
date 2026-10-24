"""Independent packet/timeline review; fixture verifiers are NOT authentication."""
from dataclasses import replace
import binascii
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import unittest

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a/competition/deepeye"
sys.path[:0] = [str(D), str(PRODUCT / "integration"), str(ROOT / ".local/deepeye-host-deps")]
ATTEMPTS = []
READS = set()


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.startfile", "socket.connect",
                 "socket.bind", "socket.sendto", "socket.getaddrinfo"}:
        ATTEMPTS.append(event)
        raise RuntimeError("External action prohibited in independent controls")
    if event == "open" and not isinstance(args[0], int):
        path = Path(args[0]).resolve()
        mode, flags = args[1:3]
        writing = ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
                   (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))))
        if writing and not path.is_relative_to(D):
            ATTEMPTS.append("unowned_write")
            raise RuntimeError("Unowned write")
        if not writing:
            if path.name in {"lease.private.json", "reserve-request.json"}:
                raise RuntimeError("Private file forbidden")
            READS.add(str(path))


sys.addaudithook(audit)
from verify_inputs import verify, save, pin

BEFORE = verify()
save("input-verification.json", BEFORE)
import hil_request_tracker as hil

NS = 1_000_000
TRACES = {}
CURRENT = None
BOOT_CONTEXT = dict(session=23, config_epoch=4, boot_sha256="6"*64,
    transport_profile_id=1, source_id=3, topology_id=1, acquisition_profile_id=1)


def note(event, **fields):
    TRACES.setdefault(CURRENT or "setup", []).append({"event": event, **fields})


def u(number, size):
    return number.to_bytes(size, "little", signed=False)


def s(number, size=2):
    return number.to_bytes(size, "little", signed=True)


def packet(kind, payload, sequence, tick=0, epoch=4):
    # Literal ABI byte construction independent of production Struct/encode.
    body = b"\xa5\x5a" + bytes([3, kind, len(payload), epoch]) + u(sequence, 2) + u(tick, 4) + payload
    return body + u(binascii.crc_hqx(body[2:], 0xffff), 2)


def encode(document):
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode()


def command(ctx, seq=12, obs=70, ttl=2500, tick=0, action=1, yaw=0, pitch=0, speed=8, kind=14):
    if kind == 14:
        payload = u(ctx["session"], 4) + u(seq, 2) + u(action, 1) + s(yaw) + s(pitch) + u(speed, 1) + u(ttl, 2) + u(obs, 2)
    elif kind == 5:
        payload = u(ctx["session"], 4) + bytes([1, 0, 0]) + u(100, 2) + b"\0"
    elif kind == 10:
        payload = u(ctx["session"], 4) + u(seq, 2) + bytes([1, 0]) + u(obs, 2)
    else:
        raise AssertionError("unselected fixture request")
    return packet(kind, payload, seq, tick, ctx["config_epoch"])


def interval(low, high=None):
    return {"lower_ns": low*NS, "upper_ns": (low if high is None else high)*NS}


def observation(ctx, seq=70, sample=100, receipt=100, event=False):
    common = dict(schema_version=1, context=dict(ctx), observed_seq=seq, tick_ms_raw=sample,
        receipt_interval_ns=interval(receipt))
    if event:
        payload = u(1, 2) + bytes([0, 1]) + u(5, 2)
        common.update(kind="event_observation", trigger_sample_interval_ns=interval(sample),
            bitmap=1, channel=0, severity=1, peak_counts=5,
            wire_frame_hex=packet(2, payload, seq, sample, ctx["config_epoch"]).hex())
    else:
        means, spans = [11, 12, 13, 14], [1, 2, 3, 4]
        payload = b"".join(u(x, 2) for x in means + spans + [15])
        common.update(kind="telem_observation", adc_last_interval_ns=interval(sample),
            adc_first_interval_ns=None, native_em_interval_ns=None,
            sample_count=50 if ctx["transport_profile_id"] == 1 else 800,
            mean_counts=means, range_counts=spans, quality_flags=15,
            wire_frame_hex=packet(1, payload, seq, sample, ctx["config_epoch"]).hex())
    return encode(common)


def response(ctx, req=12, seq=200, tick=400, at=400, lo=None, remaining=900,
             kind=15, phase=3, fault=0, capture=30, epoch=None, quality=15,
             yaw=0, pitch=0, speed=8, request_type=14, hashes=False):
    epoch = ctx["config_epoch"] if epoch is None else epoch
    if kind == 15:
        payload = u(ctx["session"], 4) + u(req, 2) + bytes([request_type, phase]) + s(yaw) + s(pitch) + u(speed, 1) + u(remaining, 2) + u(fault, 1) + u(capture, 2) + bytes([epoch, quality])
    elif kind == 16:
        payload = u(ctx["session"], 4) + u(req, 2) + s(yaw) + s(pitch) + bytes([speed, phase]) + u(remaining, 2) + u(fault, 2) + u(capture, 2) + bytes([epoch, quality])
    elif kind == 8:
        payload = u(ctx["session"], 4) + u(req, 2) + s(yaw) + bytes([speed, phase]) + u(remaining, 2) + u(fault, 2) + u(capture, 2) + bytes([epoch, quality])
    else:
        raise AssertionError("unselected fixture response")
    return encode(dict(schema_version=1, context=dict(ctx), kind="board_response",
        receipt_interval_ns=interval(at if lo is None else lo, at),
        wire_frame_hex=packet(kind, payload, seq, tick, ctx["config_epoch"]).hex(),
        timing_record_sha256="7"*64 if hashes else None,
        physical_capture_record_sha256="8"*64 if hashes else None))


class FixtureDependencies(hil.HilDependencies):
    """Closed synthetic associations only; no measured/valid authenticity flag."""
    def __init__(self):
        self.observations = {}
        self.responses = {}
        self.hooks = {}
        self.mods = {}
        self.calls = []
        self.delays = (33*NS, 7*NS, 2*NS)

    def returned(self, name, value):
        self.calls.append(name)
        if name in self.hooks:
            self.hooks[name]()
        return self.mods[name](value) if name in self.mods else value

    def verify_boot(self, event):
        return self.returned("boot", event)

    def verify_observation(self, raw, boot):
        if raw not in self.observations:
            raise ValueError("not a selected synthetic observation")
        return self.returned("observation", hil.ObservationEvidence(boot, raw, self.observations[raw]))

    def verify_timing(self, raw, boot, original):
        if raw not in self.responses:
            raise ValueError("not a selected synthetic response")
        return self.returned("timing", hil.TimingEvidence(boot, original, raw, *self.delays))

    def verify_capture(self, raw, boot, original):
        fields = self.responses[raw]
        return self.returned("capture", hil.CaptureEvidence(boot, original, raw,
            fields["yaw"], fields["pitch"], fields["speed"], fields["capture"], fields["epoch"],
            fields["quality"], ("synthetic-only-batch", fields["capture"])))


class Fixture:
    def __init__(self, profile=1, topology=1, source=...):
        self.ctx = dict(BOOT_CONTEXT, transport_profile_id=profile, topology_id=topology)
        self.deps = FixtureDependencies()
        self.tracker = hil.HilRequestTracker(run_id="independent-synthetic", dependencies=self.deps)
        self.binding = hil.BootBinding("independent-synthetic", 1, encode(self.ctx),
            object() if source is ... else source)
        self.tracker.boot(self.binding, now_ns=0)
        note("boot", context=self.ctx, now_ns=0, synthetic=True)

    def obs(self, seq=70, sample=100, receipt=100, **kw):
        raw = observation(self.ctx, seq, sample, receipt, **kw)
        self.deps.observations[raw] = sample*NS
        note("observation", raw_hex=raw.hex(), now_ns=receipt*NS)
        return self.tracker.observe(raw, now_ns=receipt*NS)

    def send(self, at=120, first=None, **kw):
        raw = command(self.ctx, **kw)
        note("request", raw_hex=raw.hex(), first_send_ns=(at if first is None else first)*NS, now_ns=at*NS)
        result = self.tracker.request(raw, first_send_ns=(at if first is None else first)*NS, now_ns=at*NS)
        note("original_request", key=list(result.key), first_send_ns=result.first_send_ns,
            ttl_ms=result.ttl_ms, sample_lower_ns=result.sample_lower_ns, first_raw_hex=result.first_raw.hex())
        return result

    def arm(self, **kw):
        self.obs()
        return self.send(**kw)

    def raw_response(self, **kw):
        raw = response(self.ctx, **kw)
        self.deps.responses[raw] = {key: kw.get(key, default) for key, default in
            (("yaw", 0), ("pitch", 0), ("speed", 8), ("capture", 30), ("quality", 15))}
        self.deps.responses[raw]["epoch"] = self.ctx["config_epoch"] if kw.get("epoch") is None else kw["epoch"]
        return raw

    def reply(self, now=None, **kw):
        raw = self.raw_response(**kw)
        now = kw.get("at", 400) if now is None else now
        note("response", raw_hex=raw.hex(), now_ns=now*NS)
        result = self.tracker.response(raw, now_ns=now*NS)
        note("association", qualified=result.qualified, deadline_ns=result.deadline_ns,
            status=result.status, request_key=None if result.request is None else list(result.request.key))
        return result


class Controls(unittest.TestCase):
    def setUp(self):
        global CURRENT
        CURRENT = self._testMethodName

    def test_packet_oracle_known_crc_and_literal_layout(self):
        self.assertEqual(binascii.crc_hqx(b"123456789", 0xffff), 0x29b1)
        raw = command(BOOT_CONTEXT)
        # Header 12 bytes plus literal 16-byte CONTROL3D payload plus CRC.
        self.assertEqual(raw[:-2].hex(),
            "a55a030e10040c0000000000170000000c00010000000008c4094600")
        self.assertEqual(len(raw), 30)
        note("literal_packet", hex=raw.hex(), crc_standard_check="123456789 -> 29b1")

    def test_original_ttl_and_late_eight_second_ack(self):
        f = Fixture(profile=2)
        f.deps.delays = (1150*NS, 210*NS, 40*NS)
        original = f.arm(ttl=12000)
        retried = f.send(at=8120, ttl=12000, tick=8120)
        self.assertIs(retried, original)
        self.assertEqual(original.first_send_ns, 120*NS)
        # min(12120, 8120 + 12000 - 1400, 100 + 12000) = 12100.
        got = f.reply(at=8120, remaining=12000, tick=8100)
        self.assertTrue(got.qualified)
        self.assertEqual(got.deadline_ns, 12100*NS)
        self.assertFalse(f.tracker.check(now_ns=12100*NS).qualified)
        self.assertIs(f.send(at=12101, ttl=12000, tick=12101), original)
        self.assertFalse(f.reply(at=12101, seq=201, remaining=12000).qualified)

    def test_receipt_lower_previous_deadline_and_exact_equality(self):
        f = Fixture(); original = f.arm()
        # min(2620, 370 + 900 - 42, 1600) = 1228.
        a = f.reply(lo=370)
        self.assertEqual(a.deadline_ns, 1228*NS)
        self.assertIs(a.request, original)
        b = f.reply(at=600, lo=590, kind=16, seq=201, remaining=1200, capture=31)
        self.assertEqual(b.deadline_ns, 1228*NS)
        self.assertTrue(f.tracker.check(now_ns=1228*NS-1).qualified)
        self.assertFalse(f.tracker.check(now_ns=1228*NS).qualified)
        note("literal_boundary", deadline_ns=1228*NS, one_ns_before=True, equality=False)

    def test_delay_exhaustion_and_original_send_cap(self):
        f = Fixture(); f.arm()
        got = f.reply(lo=370, remaining=41)
        self.assertEqual(got.deadline_ns, 370*NS)
        self.assertFalse(got.qualified)
        f = Fixture(); f.arm(ttl=500)
        got = f.reply(remaining=500)
        self.assertEqual(got.deadline_ns, 620*NS)

    def test_retry_identity_and_nonmotion_type_keys(self):
        f = Fixture(); original = f.arm()
        f.send(at=140, kind=5)
        f.send(at=150, kind=10)
        retry = f.send(at=160, tick=1337)
        self.assertIs(retry, original)
        snap = f.tracker.snapshot()
        self.assertEqual(snap["request_count"], 3)
        self.assertEqual([r["key"][1] for r in snap["requests"]], [14, 5, 10])
        first = snap["requests"][0]
        self.assertNotEqual(first["first_raw_hex"], first["latest_raw_hex"])
        self.assertEqual(first["first_send_ns"], 120*NS)
        self.assertTrue(f.reply().qualified)
        with self.assertRaises(ValueError):
            f.reply(seq=201, at=450, request_type=5)
        self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_same_key_changed_payload_latches_stop(self):
        for kw in ({"ttl":2400}, {"obs":71}, {"yaw":1}, {"speed":9}):
            with self.subTest(change=kw):
                f = Fixture(); f.arm()
                with self.assertRaises(ValueError):
                    f.send(at=130, **kw)
                self.assertTrue(f.tracker.snapshot()["stopped"])
                self.assertFalse(f.reply().qualified)

    def test_superseded_and_expired_requests_never_resurrect(self):
        f = Fixture(); f.arm()
        newer = f.send(at=150, seq=13)
        self.assertFalse(f.reply().qualified)
        self.assertTrue(f.reply(req=13, seq=201, at=450).qualified)
        self.assertIs(f.tracker.check(now_ns=450*NS).request, newer)
        f.tracker.check(now_ns=1600*NS)
        f.obs(seq=71, sample=1600, receipt=1600)
        self.assertFalse(f.reply(req=13, seq=202, at=1601, remaining=2500).qualified)

    def test_unknown_and_evicted_original_observation(self):
        f = Fixture(); original = f.send()
        f.obs(receipt=130)
        self.assertIsNone(original.sample_lower_ns)
        self.assertFalse(f.reply().qualified)
        f = Fixture(); f.arm()
        for seq in range(71, 75):
            f.obs(seq=seq, sample=150, receipt=150)
        self.assertEqual(f.tracker.snapshot()["observation_count"], 4)
        got = f.reply()
        self.assertEqual(got.status, "observation_evicted")
        self.assertFalse(got.qualified)
        with self.assertRaises(ValueError):
            f.obs(seq=70, sample=100, receipt=500)

    def test_event_observation_and_no_receipt_backfill(self):
        f = Fixture(); f.obs(event=True)
        self.assertEqual(f.send().sample_lower_ns, 100*NS)
        self.assertTrue(f.reply().qualified)
        f = Fixture(); f.obs(receipt=130)
        old = f.send(at=140, first=120)
        self.assertIsNone(old.sample_lower_ns)
        self.assertFalse(f.reply().qualified)

    def test_stop_request_and_explicit_stop_cannot_be_undone(self):
        for mode in ("wire", "explicit"):
            with self.subTest(mode=mode):
                f = Fixture(); f.arm(); self.assertTrue(f.reply().qualified)
                if mode == "wire":
                    f.send(seq=13, at=500, action=0, speed=0, ttl=0, obs=65535)
                else:
                    f.tracker.stop("independent STOP")
                self.assertFalse(f.reply(at=550, seq=201).qualified)
                with self.assertRaises(ValueError):
                    f.send(at=560, seq=14)
                self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_current_fault_stop_and_reject_latch(self):
        for field in ({"fault":2}, {"phase":0}, {"phase":4}):
            with self.subTest(field=field):
                f = Fixture(); f.arm(); self.assertTrue(f.reply().qualified)
                got = f.reply(at=450, seq=201, **field)
                self.assertFalse(got.qualified)
                self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_nonmotion_health_response_is_not_a_new_association(self):
        f = Fixture(); f.arm()
        self.assertFalse(f.reply(kind=8, fault=1).qualified)
        self.assertFalse(f.tracker.check(now_ns=400*NS).qualified)
        note("boundary", meaning="STATE8 is diagnostic only; authority independently enforces board health")

    def test_malformed_crc_ttl_curvature_and_epoch(self):
        cases = ({"ttl":0}, {"ttl":3001}, {"yaw":15000}, {"speed":0, "pitch":1},
                 {"action":0, "ttl":1, "speed":0}, {"speed":21})
        for fields in cases:
            with self.subTest(fields=fields):
                f = Fixture(); f.obs()
                with self.assertRaises(ValueError):
                    f.send(**fields)
        f = Fixture(); f.obs()
        bad = bytearray(command(f.ctx)); bad[-1] ^= 1
        with self.assertRaises(ValueError):
            f.tracker.request(bytes(bad), first_send_ns=120*NS, now_ns=120*NS)
        f = Fixture(); f.arm()
        with self.assertRaises(ValueError):
            f.reply(epoch=5)

    def test_capture_phase_quality_codes_and_remaining_ttl(self):
        for fields in ({"phase":1}, {"phase":2}, {"quality":7}, {"yaw":1}, {"pitch":1}, {"speed":7}):
            with self.subTest(fields=fields):
                f = Fixture(); f.arm()
                self.assertFalse(f.reply(**fields).qualified)
        f = Fixture(); f.arm()
        with self.assertRaises(ValueError):
            f.reply(remaining=2501)
        f = Fixture(); f.arm(); f.reply(capture=65535)
        with self.assertRaises(ValueError):
            f.reply(seq=201, at=450, capture=0)

    def test_missing_and_invalid_verifier_results(self):
        for method in ("timing", "capture"):
            for bad in (None, True, "a"*64):
                with self.subTest(method=method, result=repr(bad)):
                    f = Fixture(); f.arm(); f.deps.mods[method] = lambda value, bad=bad: bad
                    try:
                        got = f.reply(hashes=True)
                    except ValueError:
                        self.assertTrue(f.tracker.snapshot()["stopped"])
                    else:
                        self.assertFalse(got.qualified)
        for method, field, value in (
            ("timing", "serial_upper_ns", True), ("timing", "clock_error_upper_ns", -1),
            ("timing", "usb_processing_upper_ns", 0.1), ("timing", "request", object()),
            ("capture", "boot", object()), ("capture", "batch", None),
            ("capture", "capture_seq", 31), ("capture", "quality", 7),
            ("capture", "response_raw", b"{}"), ("capture", "response_raw", bytearray(b"{}"))):
            with self.subTest(method=method, field=field):
                f = Fixture(); f.arm()
                f.deps.mods[method] = lambda proof, field=field, value=value: replace(proof, **{field:value})
                with self.assertRaises(ValueError):
                    f.reply()
                self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_no_default_or_unknown_source_and_no_pc_direct_capture(self):
        tracker = hil.HilRequestTracker(run_id="independent-synthetic")
        with self.assertRaises(ValueError):
            tracker.boot(object(), now_ns=0)
        with self.assertRaises(ValueError):
            Fixture(topology=2)
        f = Fixture(source=None)
        self.assertFalse(f.obs())
        f.send()
        self.assertFalse(f.reply().qualified)

    def test_exact_duplicate_does_not_renew_and_changed_identity_stops(self):
        f = Fixture(); f.arm(); first = f.reply()
        duplicate = f.reply(at=500)
        self.assertFalse(duplicate.qualified)
        self.assertEqual(duplicate.deadline_ns, first.deadline_ns)
        self.assertEqual(f.tracker.check(now_ns=500*NS).deadline_ns, first.deadline_ns)
        with self.assertRaises(ValueError):
            f.reply(at=550, remaining=899)
        self.assertTrue(f.tracker.snapshot()["stopped"])
        f = Fixture(); f.arm(); f.reply()
        with self.assertRaises(ValueError):
            f.reply(at=450, seq=199, kind=16)

    def test_request_and_response_sequence_exhaustion(self):
        for first, next_seq in ((65535, 0), (0, 32768)):
            f = Fixture(); f.obs(); f.send(seq=first)
            with self.assertRaises(ValueError):
                f.send(at=130, seq=next_seq)
            f = Fixture(); f.arm(); f.reply(seq=first)
            with self.assertRaises(ValueError):
                f.reply(at=450, seq=next_seq)
        f = Fixture()
        for seq in range(18):
            f.send(at=120+seq, seq=seq, kind=5)
        self.assertEqual(f.tracker.snapshot()["request_count"], 16)
        with self.assertRaises(ValueError):
            f.send(at=140, seq=0, kind=5)

    def test_evicted_active_command_cannot_be_replayed(self):
        f = Fixture(); f.arm(); self.assertTrue(f.reply().qualified)
        for seq in range(16):
            f.send(at=450+seq, seq=seq, kind=5)
        self.assertIsNone(f.tracker.check(now_ns=470*NS).request)
        with self.assertRaises(ValueError):
            f.send(at=471)

    def test_session_retirement_and_limit(self):
        f = Fixture(); f.arm(); oldraw = f.raw_response()
        for gen in range(2, 65):
            ctx = dict(f.ctx, session=100+gen)
            f.tracker.boot(hil.BootBinding("independent-synthetic", gen, encode(ctx), object()), now_ns=200*NS)
        self.assertEqual(f.tracker.snapshot()["session_count"], 64)
        with self.assertRaises(ValueError):
            f.tracker.boot(hil.BootBinding("independent-synthetic", 65, encode(dict(f.ctx, session=999)), object()), now_ns=200*NS)
        self.assertEqual(f.tracker.snapshot()["session_count"], 64)
        f = Fixture(); f.arm()
        f.tracker.boot(hil.BootBinding("independent-synthetic", 2, encode(dict(f.ctx, session=24)), object()), now_ns=200*NS)
        with self.assertRaises(ValueError):
            f.tracker.response(oldraw, now_ns=400*NS)

    def test_clock_and_public_call_shape_rejections(self):
        for bad in (True, -1, 1.0):
            f = Fixture()
            with self.assertRaises(ValueError):
                f.tracker.check(now_ns=bad)
            self.assertTrue(f.tracker.snapshot()["stopped"])
        f = Fixture(); f.arm(); f.tracker.check(now_ns=200*NS)
        with self.assertRaises(ValueError):
            f.tracker.check(now_ns=199*NS)
        for invoke in (lambda t:t.request(), lambda t:t.check(unknown=1),
                       lambda t:t.snapshot(unknown=1), lambda t:t.stop(unknown=1)):
            f = Fixture()
            with self.assertRaises(ValueError):
                invoke(f.tracker)
            self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_callback_stop_reentry_bad_shape_exception_veto(self):
        for method in ("observation", "timing", "capture"):
            for behavior in ("stop", "reentry", "shape", "exception"):
                with self.subTest(method=method, behavior=behavior):
                    f = Fixture()
                    if method != "observation": f.arm()
                    def hook():
                        if behavior == "stop":
                            f.tracker.stop("provider STOP")
                        elif behavior == "exception":
                            raise RuntimeError("synthetic verifier failure")
                        else:
                            try:
                                if behavior == "reentry": f.tracker.check(now_ns=400*NS)
                                else: f.tracker.snapshot(unknown=True)
                            except ValueError:
                                pass
                    f.deps.hooks[method] = hook
                    with self.assertRaises(ValueError):
                        if method == "observation": f.obs()
                        else: f.reply()
                    self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_boot_callback_veto_retires_proposal(self):
        f = Fixture()
        proposal = hil.BootBinding("independent-synthetic", 2, encode(dict(f.ctx, session=24)), object())
        f.deps.hooks["boot"] = lambda: f.tracker.stop("during verifier")
        with self.assertRaises(ValueError):
            f.tracker.boot(proposal, now_ns=0)
        f.deps.hooks.clear()
        with self.assertRaises(ValueError):
            f.tracker.boot(proposal, now_ns=0)
        self.assertEqual(f.tracker.snapshot()["session_count"], 2)

    def test_foreign_thread_inside_verifier_is_fenced(self):
        f = Fixture(); f.arm(); errors = []
        def foreign():
            try: f.tracker.stop("foreign during callback")
            except ValueError as error: errors.append(str(error))
        def hook():
            worker = threading.Thread(target=foreign)
            worker.start(); worker.join(1)
            self.assertFalse(worker.is_alive())
        f.deps.hooks["capture"] = hook
        with self.assertRaises(ValueError):
            f.reply()
        self.assertEqual(errors, ["constructing serialized owner required"])
        self.assertTrue(f.tracker.snapshot()["stopped"])

    def test_foreign_thread_after_final_fence_cannot_publish_qualified(self):
        """Deterministic scheduling at a real code line, no source/state patch."""
        f = Fixture(); f.arm()
        raw = f.raw_response()
        errors = []
        injected = []
        def foreign():
            try: f.tracker.stop("foreign after final fence")
            except ValueError as error: errors.append(str(error))
        source = str((PRODUCT / "integration/hil_request_tracker.py").resolve())
        # Line 463 is the first statement after final _fence(transition).
        def trace(frame, event, arg):
            if event == "line" and frame.f_code.co_filename == source and frame.f_lineno == 463 and not injected:
                injected.append(463)
                worker = threading.Thread(target=foreign)
                worker.start(); worker.join(1)
                if worker.is_alive(): raise AssertionError("bounded thread did not stop")
            return trace
        sys.settrace(trace)
        try:
            result = f.tracker.response(raw, now_ns=400*NS)
        finally:
            sys.settrace(None)
        # Snapshot on the owner drains pending stop, separately from the stale result.
        snap = f.tracker.snapshot()
        note("publication_race", injection_line=injected, errors=errors,
            returned_qualified=result.qualified, returned_deadline_ns=result.deadline_ns,
            next_owner_snapshot_stopped=snap["stopped"], raw_hex=raw.hex(), now_ns=400*NS)
        self.assertEqual(injected, [463])
        self.assertEqual(errors, ["constructing serialized owner required"])
        self.assertTrue(snap["stopped"])
        self.assertFalse(result.qualified, "foreign STOP occurred before result publication")

    def test_slow_verifier_supplied_time_boundary_is_not_authorization(self):
        f = Fixture(); f.arm(ttl=400)
        # Deterministically advance an EXTERNAL illustrative clock during verification.
        external_clock = {"now_ms":400}
        f.deps.hooks["capture"] = lambda: external_clock.update(now_ms=1000)
        result = f.reply(remaining=300)
        self.assertTrue(result.qualified)
        self.assertEqual(result.deadline_ns, 520*NS)
        self.assertGreater(external_clock["now_ms"]*NS, result.deadline_ns)
        self.assertFalse(f.tracker.check(now_ns=external_clock["now_ms"]*NS).qualified)
        note("boundary", evaluation_now_ns=400*NS, later_caller_now_ns=1000*NS,
            diagnostic_qualified=True, fresh_time_check_qualified=False,
            meaning="Expected supplied-time behavior; no motion/send API exists")


class Results(unittest.TextTestResult):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append({"test":test.id(), "status":"passed"})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.rows.append({"test":test.id(), "status":"failed", "traceback":self._exc_info_to_string(error, test)})

    def addError(self, test, error):
        super().addError(test, error)
        self.rows.append({"test":test.id(), "status":"error", "traceback":self._exc_info_to_string(error, test)})


started = time.monotonic()
result = unittest.TextTestRunner(verbosity=2, resultclass=Results).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
AFTER = verify()
assert AFTER == BEFORE, "read-only inputs changed"
save("controls-results.json", {
    "worker_pid":os.getpid(), "worker_parent_pid":os.getppid(), "executable":sys.executable,
    "argv":sys.argv, "tests_run":result.testsRun, "failures":len(result.failures),
    "errors":len(result.errors), "skipped":len(result.skipped),
    "duration_seconds":time.monotonic()-started, "rows":result.rows,
    "subtest_failures":[{"test":str(test), "traceback":text} for test,text in result.failures],
    "all_inputs_unchanged":AFTER == BEFORE, "prohibited_attempts":ATTEMPTS,
    "synthetic_only":True, "formal_all29_R03_full_H12":"not_run",
})
save("literal-traces.json", TRACES)
modules = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, "__file__", None)
    if name:
        path = Path(name)
        if path.is_file():
            modules[str(path.resolve())] = pin(path)
save("imports-and-reads.json", {"module_file_pins":modules, "read_paths":sorted(READS),
    "no_private_lease_read":True, "product_writes":0, "prohibited_attempts":ATTEMPTS,
    "no_production_encoder_or_author_tests_used":True})
raise SystemExit(0 if result.wasSuccessful() else 1)
