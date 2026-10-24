"""One additional main-requested ordering control; reuses saved literal bytes."""
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
P = ROOT / ".local/deepeye-implementation-a/competition/deepeye"
sys.path[:0] = [str(D), str(P / "integration"), str(ROOT / ".local/deepeye-host-deps")]
blocked_attempts = []


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.startfile", "socket.connect",
                 "socket.bind", "socket.sendto", "socket.getaddrinfo"}:
        blocked_attempts.append(event)
        raise RuntimeError("External action forbidden")
    if event == "open" and not isinstance(args[0], int):
        path = Path(args[0]).resolve()
        if path.name == "lease.private.json":
            raise RuntimeError("Private lease forbidden")
        mode, flags = args[1:3]
        writing = ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
            (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))))
        if writing and not path.is_relative_to(D):
            blocked_attempts.append("unowned_write")
            raise RuntimeError("Unowned write forbidden")


sys.addaudithook(audit)
from verify_inputs import verify, pin, save
before = verify()
assert before == json.loads((D / "input-verification.json").read_bytes())
import hil_request_tracker as hil

started = time.monotonic()
source = json.loads((D / "literal-traces.json").read_bytes())
trace = source["test_foreign_thread_after_final_fence_cannot_publish_qualified"]
context = next(x["context"] for x in trace if x["event"] == "boot")
obs_raw = bytes.fromhex(next(x["raw_hex"] for x in trace if x["event"] == "observation"))
req_raw = bytes.fromhex(next(x["raw_hex"] for x in trace if x["event"] == "request"))
reply_raw = bytes.fromhex(next(x["raw_hex"] for x in trace if x["event"] == "publication_race"))
events = []


class Dependencies(hil.HilDependencies):
    def verify_boot(self, event):
        return event

    def verify_observation(self, raw, boot):
        assert raw == obs_raw
        return hil.ObservationEvidence(boot, raw, 100_000_000)

    def verify_timing(self, raw, boot, original):
        assert raw == reply_raw
        return hil.TimingEvidence(boot, original, raw, 33_000_000, 7_000_000, 2_000_000)

    def verify_capture(self, raw, boot, original):
        assert raw == reply_raw
        return hil.CaptureEvidence(boot, original, raw, 0, 0, 8, 30, 4, 15,
            ("synthetic-only-batch", 30))


tracker = hil.HilRequestTracker(run_id="prequeued-independent", dependencies=Dependencies())
boot = hil.BootBinding("prequeued-independent", 1,
    json.dumps(context, sort_keys=True, separators=(",", ":")).encode(), object())
tracker.boot(boot, now_ns=0)
assert tracker.observe(obs_raw, now_ns=100_000_000)
tracker.request(req_raw, first_send_ns=120_000_000, now_ns=120_000_000)
baseline = tracker.response(reply_raw, now_ns=400_000_000)
assert baseline.qualified and baseline.deadline_ns == 1_258_000_000
events.append({"event":"baseline_response", "qualified":True, "deadline_ns":baseline.deadline_ns})
errors = []


def foreign():
    events.append({"event":"foreign_stop_called", "thread_id":threading.get_ident()})
    try:
        tracker.stop("queued before owner entry")
    except ValueError as error:
        errors.append(str(error))
        events.append({"event":"foreign_stop_rejected", "error":str(error)})


worker = threading.Thread(target=foreign)
worker.start()
worker.join(1)
assert not worker.is_alive()
assert errors == ["constructing serialized owner required"]
events.append({"event":"foreign_thread_joined_before_owner_call"})
# No owner call intervenes between the foreign request and this response.
result = tracker.response(reply_raw, now_ns=400_000_000)
events.append({"event":"owner_response_after_prequeued_stop",
    "qualified":result.qualified, "status":result.status, "deadline_ns":result.deadline_ns})
assert result.qualified is False and result.status == "stopped"
assert tracker.check(now_ns=400_000_000).qualified is False
snapshot = tracker.snapshot()
assert snapshot["stopped"] is True
assert verify() == before and not blocked_attempts
modules = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, "__file__", None)
    if name and Path(name).is_file():
        modules[str(Path(name).resolve())] = pin(Path(name))
save("pending-before-entry-result.json", {"status":"passed", "assertions":"all passed",
    "worker_pid":os.getpid(), "worker_parent_pid":os.getppid(), "events":events,
    "literal_source":pin(D / "literal-traces.json"), "original_source":pin(P / "integration/hil_request_tracker.py"),
    "source_packets":{"observation_hex":obs_raw.hex(), "request_hex":req_raw.hex(), "response_hex":reply_raw.hex()},
    "snapshot_stopped":snapshot["stopped"], "all_input_pins_unchanged":True,
    "blocked_attempts":blocked_attempts, "elapsed_seconds":time.monotonic()-started,
    "scope":"one prequeued foreign STOP control; no prior26/author37/full245 replay",
    "module_file_pins":modules, "synthetic_only":True,
    "formal_all29_R03_G05_full_H12":"not_run"})
print(json.dumps({"status":"passed", "prequeued_stop":"owner entry drained before response",
    "worker_pid":os.getpid()}))
