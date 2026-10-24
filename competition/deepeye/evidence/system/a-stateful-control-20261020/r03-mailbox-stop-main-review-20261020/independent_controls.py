"""Self-authored bounded controls using production schema, wire codec and BOOT.

No author tests, mock validator, model, transport or authorization is used.
The expected policy comes from fixed taskbook epochs and strict age/deadline.
"""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import unittest

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / ".local/deepeye-implementation-a/competition/deepeye"
MODE, LABEL = sys.argv[1:]
assert (MODE, LABEL) in {("all", "suite-01"), ("stop", "stop-callshape-01")}
OUT = D / LABEL
ATTEMPTS = []

def owned(path):
    return Path(path).resolve().is_relative_to(D)

def audit(event, args):
    denied = event in {"subprocess.Popen", "os.system", "os.startfile", "os.startfile/2",
                       "socket.connect", "socket.bind", "os.remove", "os.rmdir",
                       "os.rename", "os.link", "os.symlink", "os.chdir"}
    if event == "open" and not isinstance(args[0], int):
        path, mode, flags = args[:3]
        denied |= "lease.private" in str(path).lower()
        writing = isinstance(mode, str) and any(c in mode for c in "wax+")
        writing |= isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        denied |= writing and not owned(path)
    if event == "os.mkdir":
        denied |= not owned(args[0])
    if denied:
        ATTEMPTS.append(event)
        raise RuntimeError("review prohibited effect: " + event)

sys.addaudithook(audit)
sys.path[:0] = [str(D), str(PRODUCT / "integration"), str(ROOT / ".local/deepeye-host-deps")]
import boot_profile as boot
import candidate_mailbox as mailbox
import host_envelope as envelope
import wire

NS = 1_000_000
DOCUMENT = boot.load_document(PRODUCT / "docs/boot_profiles.json")
DIGEST = boot.canonical_sha256(DOCUMENT).hex()
TRACES = []

def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()

def interval(n):
    return {"lower_ns": n, "upper_ns": n}

class Fixture:
    def __init__(self, mode=1, profile=1, origin=0, source=True, clock=True, bounds=True):
        self.source = object() if source else None
        self.clock = object() if clock else None
        self.context = dict(session=100, config_epoch=2, boot_sha256=DIGEST,
                            transport_profile_id=profile, source_id=3,
                            topology_id=mode, acquisition_profile_id=1)
        self.owner = mailbox.LatestCompletedMailbox(DOCUMENT)
        self.origin = origin
        self.owner.activate(encode(self.context), generation=1, slot_origin_ns=origin,
                            source=self.source, clock_domain=self.clock,
                            bounds=mailbox.TransferBounds(10*NS, 5*NS) if bounds else None, now_ns=origin)

    def raw_observation(self, seq=1, sample=None, receipt=None, kind="telem"):
        sample = self.origin if sample is None else sample
        receipt = self.origin if receipt is None else receipt
        common = dict(schema_version=1, context=self.context, observed_seq=seq,
                      tick_ms_raw=seq, receipt_interval_ns=interval(receipt))
        if kind == "telem":
            mean, ranges, quality = [1, 2, 3, 4], [5, 6, 7, 8], 3
            payload = struct.pack("<4H4HH", *(mean + ranges + [quality]))
            common.update(kind="telem_observation", adc_last_interval_ns=interval(sample),
                          adc_first_interval_ns=None, native_em_interval_ns=None,
                          sample_count=50 if self.context["transport_profile_id"] == 1 else 800,
                          mean_counts=mean, range_counts=ranges, quality_flags=quality,
                          wire_frame_hex=wire.encode(wire.Frame(1, 2, seq, seq, payload)).hex())
        else:
            payload = struct.pack("<HBBH", 1, 2, 3, 99)
            common.update(kind="event_observation", trigger_sample_interval_ns=interval(sample),
                          bitmap=1, channel=2, severity=3, peak_counts=99,
                          wire_frame_hex=wire.encode(wire.Frame(2, 2, seq, seq, payload)).hex())
        return encode(common)

    def observe(self, seq=1, sample=None, receipt=None, now=None, kind="telem", unknown=False):
        sample = self.origin if sample is None else sample
        receipt = self.origin if receipt is None else receipt
        now = receipt if now is None else now
        raw = self.raw_observation(seq, sample, receipt, kind)
        self.owner.observe(raw, sample_lower_ns=None if unknown else sample, now_ns=now)
        return raw

    def completion(self, seq=1, candidate=1, invocation=None, completed=None, dispatch=None,
                   deadline=None, generation=1):
        completed = self.origin + 150*NS if completed is None else completed
        dispatch = self.origin if dispatch is None else dispatch
        deadline = self.origin + 2000*NS if deadline is None else deadline
        raw = encode(dict(schema_version=1, context=self.context, kind="model_candidate",
                          candidate_id=candidate, model_sha256="b"*64,
                          observation={"context": self.context, "observed_seq": seq},
                          completed_monotonic_ns=completed,
                          target=dict(action=1, yaw_q=0, pitch_q=0, speed_code=5, duration_ms=1000)))
        return mailbox.Completion(generation, self.source, self.clock, raw,
                                  candidate if invocation is None else invocation,
                                  dispatch, completed, completed, deadline)

    def pending(self, **kw):
        self.observe()
        record = self.completion(**kw)
        assert self.owner.complete(record, now_ns=record.completion_upper_ns)
        return record

class IndependentControls(unittest.TestCase):
    def test_contract_vectors_independent_integer_formula(self):
        data = json.loads((PRODUCT / "tests/vectors/r03_mailbox_lifecycle.json").read_text(encoding="utf-8"))
        rows = []
        for row in data["timelines"]:
            first, window, cap = (210, 500, 1500) if row["profile"] == 1 else (2050, 8000, 12000)
            profile = "fast_9600" if row["profile"] == 1 else "stress_300"
            self.assertEqual(boot.slot_start_ms(DOCUMENT, profile, "control_primary"), first)
            self.assertEqual(DOCUMENT["profiles"][profile]["window_ms"], window)
            earliest = max(row["now_ms"], row["completed_ms"] + 15)
            # Mathematical ceiling, independently of mailbox or helper output.
            index = max(0, (earliest - first + window - 1) // window)
            slot = first + index * window
            expected = slot if (slot < min(row["deadline_ms"], row["sample_ms"] + cap)
                                and row["grant_window"] == index) else None
            self.assertEqual(expected, row["expected_slot_ms"], row["name"])
            rows.append({"name": row["name"], "independently_calculated_slot_ms": expected})
        TRACES.append({"literal_vector_arithmetic": rows})

    def test_ns_edges_fixed_origin_and_both_modes(self):
        cases = [
            (1, 20*NS, 20*NS, 210*NS-1, 0, None),
            (1, 20*NS, 20*NS, 210*NS, 0, None),
            (1, 20*NS, 20*NS, 210*NS+1, 0, 210*NS),
            (1, 195*NS, 195*NS, 1500*NS, 0, 210*NS),
            (1, 195*NS+1, 195*NS+1, 1500*NS, 1, 710*NS),
            (1, 150*NS, 210*NS+1, 1500*NS, 1, 710*NS),
            (1, 250*NS, 1210*NS+1, 3000*NS, 3, None),
            (2, 20*NS, 20*NS, 2050*NS, 0, None),
            (2, 20*NS, 20*NS, 2050*NS+1, 0, 2050*NS),
            (2, 2035*NS, 2035*NS, 12000*NS, 0, 2050*NS),
            (2, 2035*NS+1, 2035*NS+1, 12000*NS, 1, 10050*NS),
            (2, 250*NS, 10050*NS+1, 15000*NS, 2, None),
        ]
        for mode in (1, 2):
            for profile, completed, now, deadline, window, expected in cases:
                with self.subTest(mode=mode, case=(profile, completed, now, deadline)):
                    origin = 37*NS + 11
                    f = Fixture(mode, profile, origin=origin)
                    f.pending(completed=origin+completed, deadline=origin+deadline)
                    selected = f.owner.plan(origin+now, grant=mailbox.SlotGrant(1, window))
                    self.assertEqual(None if selected is None else selected.slot_start_ns,
                                     None if expected is None else origin+expected)
                    if selected:
                        self.assertEqual(selected.mode, "HIL_PC_FPGA" if mode == 1 else "PC_DIRECT")
                        self.assertEqual(selected.ready_ns, origin+completed+15*NS)

    def test_plan_exact_consume_and_grant_replay(self):
        for mode in (1, 2):
            f = Fixture(mode)
            original = f.pending()
            grant = mailbox.SlotGrant(1, 0)
            for _ in range(3):
                self.assertIsNotNone(f.owner.plan(150*NS, grant=grant))
                self.assertIsNone(f.owner.consume(150*NS, grant=grant))
            self.assertIsNone(f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 1)))
            selected = f.owner.consume(210*NS, grant=grant)
            self.assertEqual(selected.candidate_raw, original.candidate_raw)
            self.assertEqual(selected.deadline_ns, 1500*NS)
            self.assertIsNone(f.owner.consume(210*NS, grant=grant))
            self.assertFalse(f.owner.complete(original, now_ns=210*NS))
            self.assertIsNone(f.owner.consume(210*NS, grant=grant))
            newer = f.completion(candidate=2, completed=195*NS)
            self.assertTrue(f.owner.complete(newer, now_ns=210*NS))
            self.assertIsNone(f.owner.consume(210*NS, grant=grant))
            self.assertIsNotNone(f.owner.consume(710*NS, grant=mailbox.SlotGrant(1, 1)))

    def test_reordered_completion_cannot_replace_newer_observation(self):
        for mode in (1, 2):
            f = Fixture(mode)
            f.observe(1)
            f.observe(2)
            newer = f.completion(seq=2, candidate=20, invocation=20)
            f.owner.complete(newer, now_ns=150*NS)
            older = f.completion(seq=1, candidate=21, invocation=21, completed=180*NS)
            self.assertFalse(f.owner.complete(older, now_ns=180*NS))
            selected = f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0))
            self.assertEqual(selected.candidate_id, 20)
            self.assertFalse(f.owner.complete(older, now_ns=210*NS))
            self.assertIsNone(f.owner.plan(710*NS, grant=mailbox.SlotGrant(1, 1)))

    def test_conflicting_completion_repeat_stops_without_deadline_extension(self):
        f = Fixture()
        original = f.pending(deadline=700*NS)
        with self.assertRaises(ValueError):
            f.owner.complete(replace(original, deadline_ns=2000*NS), now_ns=151*NS)
        self.assertTrue(f.owner.snapshot()["stopped"])
        self.assertIsNone(f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0)))

    def test_retained_old_observation_and_eviction(self):
        for mode in (1, 2):
            for evict in (False, True):
                f = Fixture(mode)
                for seq in range(1, 5):
                    f.observe(seq)
                f.owner.complete(f.completion(seq=1), now_ns=150*NS)
                if evict:
                    f.observe(5, receipt=160*NS, now=160*NS)
                selected = f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0))
                self.assertEqual(selected is None, evict)
                self.assertEqual(f.owner.snapshot()["observation_count"], 4)
        f = Fixture()
        for seq in range(1, 6):
            f.observe(seq)
        with self.assertRaises(ValueError):
            f.owner.complete(f.completion(seq=1), now_ns=150*NS)
        self.assertTrue(f.owner.snapshot()["stopped"])

    def test_original_age_and_duplicate_observation_never_renew(self):
        f = Fixture()
        raw = f.observe()
        rec = f.completion()
        f.owner.complete(rec, now_ns=150*NS)
        self.assertFalse(f.owner.observe(raw, sample_lower_ns=0, now_ns=1400*NS))
        self.assertFalse(f.owner.complete(rec, now_ns=1400*NS))
        self.assertIsNone(f.owner.plan(1400*NS, grant=mailbox.SlotGrant(1, 3)))
        # Receipt substitution under the same immutable observation key must stop.
        doc = json.loads(raw)
        doc["receipt_interval_ns"] = interval(1400*NS)
        with self.assertRaises(ValueError):
            f.owner.observe(encode(doc), sample_lower_ns=0, now_ns=1400*NS)
        self.assertTrue(f.owner.snapshot()["stopped"])

    def test_missing_provenance_or_grant_never_selects(self):
        for field in ("source", "clock", "bounds", "sample"):
            for mode in (1, 2):
                f = Fixture(mode, **{field: False} if field != "sample" else {})
                f.observe(unknown=field == "sample")
                f.owner.complete(f.completion(), now_ns=150*NS)
                self.assertIsNone(f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0)))
        for grant in (None, mailbox.SlotGrant(2, 0), mailbox.SlotGrant(1, 1)):
            f = Fixture()
            f.pending()
            self.assertIsNone(f.owner.consume(210*NS, grant=grant))

    def test_event_observation_uses_real_schema_and_original_lower(self):
        for mode in (1, 2):
            f = Fixture(mode)
            f.observe(kind="event")
            f.owner.complete(f.completion(), now_ns=150*NS)
            selected = f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0))
            self.assertEqual(selected.sample_lower_ns, 0)
            self.assertEqual(selected.deadline_ns, 1500*NS)

    def test_causal_and_strict_numeric_rejections_stop(self):
        for field, value in (("dispatch_lower_ns", -1), ("completion_lower_ns", True),
                             ("completion_upper_ns", 149*NS), ("deadline_ns", 150*NS),
                             ("invocation_id", 0), ("generation", True),
                             ("source", object()), ("clock_domain", object())):
            with self.subTest(field=field):
                f = Fixture()
                f.observe()
                with self.assertRaises(ValueError):
                    f.owner.complete(replace(f.completion(), **{field: value}), now_ns=150*NS)
                self.assertTrue(f.owner.snapshot()["stopped"])
        f = Fixture()
        f.observe(receipt=10*NS, now=10*NS)
        with self.assertRaises(ValueError):
            f.owner.complete(f.completion(dispatch=9*NS), now_ns=150*NS)
        self.assertTrue(f.owner.snapshot()["stopped"])

    def test_observation_crc_context_and_bad_mapping_rejections(self):
        for change in ("crc", "context", "younger_lower", "future", "bool"):
            f = Fixture()
            raw = f.raw_observation()
            doc = json.loads(raw)
            supplied, now = 0, 10*NS
            if change == "crc":
                doc["wire_frame_hex"] = doc["wire_frame_hex"][:-2] + "00"
                self.assertNotEqual(encode(doc), raw)
            elif change == "context":
                doc["context"]["session"] += 1
            elif change == "younger_lower":
                supplied = 1
            elif change == "future":
                supplied = 11*NS
            else:
                supplied = False
            with self.assertRaises(ValueError, msg=change):
                f.owner.observe(encode(doc), sample_lower_ns=supplied, now_ns=now)
            self.assertTrue(f.owner.snapshot()["stopped"])

    def test_stop_and_new_activation_retire_old_identity(self):
        for mode in (1, 2):
            f = Fixture(mode)
            rec = f.pending()
            f.owner.stop("independent explicit STOP")
            self.assertTrue(f.owner.snapshot()["stopped"])
            self.assertIsNone(f.owner.plan(210*NS, grant=mailbox.SlotGrant(1, 0)))
            with self.assertRaises(ValueError):
                f.owner.activate(encode(f.context), generation=2, slot_origin_ns=0,
                                 source=f.source, clock_domain=f.clock,
                                 bounds=mailbox.TransferBounds(10*NS, 5*NS), now_ns=210*NS)
            fresh = dict(f.context, session=101, topology_id=3-mode)
            f.owner.activate(encode(fresh), generation=2, slot_origin_ns=210*NS,
                             source=f.source, clock_domain=f.clock,
                             bounds=mailbox.TransferBounds(10*NS, 5*NS), now_ns=210*NS)
            with self.assertRaises(ValueError):
                f.owner.complete(rec, now_ns=210*NS)
            self.assertTrue(f.owner.snapshot()["stopped"])

    def test_malformed_time_taking_calls_latch_stop(self):
        calls = [
            lambda owner: owner.observe(),
            lambda owner: owner.complete(),
            lambda owner: owner.activate(),
            lambda owner: owner.plan(150*NS, unexpected=True),
            lambda owner: owner.consume(150*NS, unexpected=True),
        ]
        for call in calls:
            f = Fixture()
            f.pending()
            with self.assertRaises(ValueError):
                call(f.owner)
            self.assertTrue(f.owner.snapshot()["stopped"])
            self.assertIsNone(f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0)))

    def test_malformed_stop_call_must_latch_stop(self):
        """Contract-level counterexample: argument binding must not bypass STOP."""
        for mode in (1, 2):
            with self.subTest(mode=mode):
                f = Fixture(mode)
                f.pending()
                caught = None
                try:
                    f.owner.stop(reason="emergency", unexpected=True)
                except (TypeError, ValueError) as error:
                    caught = type(error).__name__
                before_consume = f.owner.snapshot()
                selected = f.owner.consume(210*NS, grant=mailbox.SlotGrant(1, 0))
                TRACES.append({
                    "case": "malformed_stop", "mode": mode, "exception": caught,
                    "after_invalid_call": before_consume,
                    "subsequent_consume_candidate_id": None if selected is None else selected.candidate_id,
                    "subsequent_consume_mode": None if selected is None else selected.mode,
                    "expected": "invalid public call latches STOP; consume returns None",
                    "authority": "Selection is non-authorizing; no real motion or send",
                })
                self.assertTrue(before_consume["stopped"], "Malformed STOP left the activation live")
                self.assertIsNone(selected)

    def test_finite_history_wrap_and_clock_fences(self):
        f = Fixture()
        for seq in range(1, 65):
            f.observe(seq)
        self.assertEqual(f.owner.snapshot()["observation_sequences"], [61, 62, 63, 64])
        for pair in ((1, 32769), (65535, 0), (10, 9)):
            f = Fixture()
            f.observe(pair[0])
            with self.assertRaises(ValueError):
                f.observe(pair[1])
            self.assertTrue(f.owner.snapshot()["stopped"])
        for bad in (149*NS, True, -1, float("nan")):
            f = Fixture()
            f.pending()
            with self.assertRaises(ValueError):
                f.owner.plan(bad)
            self.assertTrue(f.owner.snapshot()["stopped"])
        f = Fixture()
        for generation in range(2, 65):
            context = dict(f.context, session=100+generation)
            f.owner.activate(encode(context), generation=generation, slot_origin_ns=0,
                             source=f.source, clock_domain=f.clock,
                             bounds=mailbox.TransferBounds(0, 0), now_ns=0)
        self.assertEqual(f.owner.snapshot()["retired_session_count"], 64)
        with self.assertRaises(ValueError):
            f.owner.activate(encode(dict(f.context, session=1000)), generation=65, slot_origin_ns=0,
                             source=f.source, clock_domain=f.clock, bounds=None, now_ns=0)
        self.assertTrue(f.owner.snapshot()["stopped"])
        self.assertEqual(f.owner.snapshot()["retired_session_count"], 64)

    def test_retained_deadline_negative_control_is_preserved(self):
        author = D.parent / "r03-mailbox-implementation-20261020"
        record = json.loads((author / "deadline-negative-control/execution.json").read_text(encoding="utf-8"))
        self.assertEqual(record["exit"], 1)
        source = (PRODUCT / "integration/candidate_mailbox.py").read_text(encoding="utf-8")
        self.assertIn("if start_ns >= deadline or start_ns < max(now, ready):", source)
        # The real helper's early return is deliberately not used as an oracle.
        self.assertEqual(boot.late_candidate_action(DOCUMENT, "fast_9600", 35, 100)["action"], "send")
        f = Fixture()
        f.pending(completed=20*NS, deadline=100*NS)
        self.assertIsNone(f.owner.plan(20*NS, grant=mailbox.SlotGrant(1, 0)))

if __name__ == "__main__":
    suite = (unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls) if MODE == "all"
             else unittest.TestSuite([
                 IndependentControls("test_malformed_stop_call_must_latch_stop"),
                 IndependentControls("test_stop_and_new_activation_retire_old_identity"),
                 IndependentControls("test_malformed_time_taking_calls_latch_stop"),
             ]))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    module_files = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name and Path(name).is_file():
            path = Path(name).resolve()
            module_files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {
        "tests_run": result.testsRun, "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
        "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
        "skipped": result.skipped, "traces": TRACES, "prohibited_attempts": ATTEMPTS,
        "module_file_hashes": module_files, "worker_pid": os.getpid(),
        "scope": "bounded schema-backed software only; all29/R03 not_run",
    }
    with (OUT / "checks.json").open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"tests_run": result.testsRun, "failure_count": len(result.failures), "error_count": len(result.errors), "prohibited_attempts": ATTEMPTS}))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
