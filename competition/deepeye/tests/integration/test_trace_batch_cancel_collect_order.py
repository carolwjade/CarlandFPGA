"""Two SYNTHETIC_TEST lifecycle controls; no source/authority/PYNQ/SSH load."""
import binascii
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from competition.deepeye.tools.diagnostic import functional50_board_trace_batch_a as batch
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader


class SyntheticPort:
    """94/74-style completion/cancel/FIFO state boundary, not a hardware model."""
    def __init__(self, path, frames, *, unknown_cancel=False):
        self._dir, self._count, self._failed = path, 0, False
        self.frames, self.fifo = frames, b""
        self.state = self.push = self.assoc = self.tag = self.pos = 0
        self.current = -1
        self.unknown_cancel = unknown_cancel
        self.calls = []
        self.cancel_fifo = None

    def _call(self, kind, offset, value, request_id):
        self._count += 1
        event = dict(kind=kind, offset=offset, value=value, state=self.state, fifo_bytes=len(self.fifo)-self.pos)
        self.calls.append(event)
        (self._dir / f"io-{self._count:05d}-started.json").write_text("{}")
        out = None
        if kind == "write":
            if offset == 0x100:
                self.tag = value
            elif offset == 0x80:
                if value == 1:
                    self.state = 3
                elif value == 2:
                    self.push += 1
                    if self.push == 4:
                        self.state = 4
                elif value == 3:
                    self.current += 1
                    self.fifo += self.frames[self.current]
                    self.state = 7
                elif value == 4:
                    self.assoc += 1
                    self.state = 9 if self.assoc == 4 else 4
                elif value == 5:
                    self.cancel_fifo = self.fifo[self.pos:]
                    if self.unknown_cancel:
                        self._failed = True
                        event["outcome"] = "unknown"
                        raise OSError("SYNTHETIC_TEST CANCEL effect unknown")
                    self.state = 0
                elif value == 8:
                    self.pos += 1
                else:
                    raise AssertionError("unselected command: " + str(value))
        else:
            identity = {0: 0x54353046, 4: 1, 8: 4, 12: 50000000, 16: 1000000, 20: 4096}
            if offset in identity:
                out = identity[offset]
            elif 0x60 <= offset <= 0x6c:
                out = (int("c" * 32, 16) >> (32 * ((offset-0x60)//4))) & 0xffffffff
            elif offset == 0x18:
                out = self.state
            elif offset == 0x20:
                # COMPLETE9 is still armed: quiet becomes true only after CANCEL.
                out = 0x10 if self.state == 7 else ((2 | (0x20 if len(self.fifo) == self.pos else 0)) if self.state == 0 else 0)
            elif offset in (0x1c, 0x44, 0x4c):
                out = 0
            elif offset == 0x34:
                out = len(self.fifo)
            elif offset == 0x2c:
                out = self.tag
            elif offset == 0x24:
                out = self.push
            elif offset == 0x28:
                out = self.assoc
            elif offset == 0x40:
                out = self.current + 1
            elif offset == 0x48:
                out = len(self.frames[self.current])
            elif offset == 0x50:
                out = sum(map(len, self.frames[:self.current]))
            elif offset == 0x7c:
                out = len(self.fifo)
            elif offset == 0x30:
                out = len(self.fifo) - self.pos
            elif offset == 0x38:
                out = self.pos
            elif offset == 0x70:
                out = 0x100 + self.fifo[self.pos]
            else:
                raise AssertionError(hex(offset))
        event["returned"] = out
        (self._dir / f"io-{self._count:05d}-returned.json").write_text("{}")
        return out


def synthetic_packet(bundle):
    source = b"SYNTHETIC_TEST lifecycle source"
    companions = tuple(f"SYNTHETIC_TEST companion {i}".encode() for i in range(4))
    lanes = [dict(channel=i, raw_sample_uint16=i, root_quality_uint16=0,
                  mapped_flags=dict(valid=True, saturated=False, held=False, source_fault=False),
                  staged_quality_uint4=1, acquisition_qpc_ns=1000, acquisition_tick_us=1,
                  acquisition_remainder_ns=0, source_qpc_ns=1000, source_tick_us=1,
                  source_remainder_ns=0, session=1, index=i, view=1, frame_seq=i+1) for i in range(4)]
    request = dict(schema="B113_EXTERNAL_ORIGINAL_SCAN_REQUEST_V1",
        task=dict(task_id="DEEPEYE-IMPLEMENTATION-20261014", task_version=1, work_id="A368-SYNTHETIC_TEST",
                  requirements_sha256="c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"),
        source_provenance={"class": "SYNTHETIC_TEST", "declared_by": "A368-control", "source_note": "software lifecycle only",
                           "mapping_state": "B_NEUTRAL_AWAITING_A_MAPPING"},
        source_payload=dict(format_label="SYNTHETIC_TEST", bytes=len(source), sha256=batch.digest(source)),
        scan=dict(scan_id_uint63=1, origin_qpc_ns=0, acquisition_qpc_ns=1000, clock_domain_id="synthetic", lanes=lanes),
        lineage=dict(operation_id="op", request_id="req", request_hash="a"*64, tested_commit="b"*40,
                     build_id_hex128="c"*32, boot_id="synthetic", session_id=1, tag=1, trigger_id=1,
                     generation=1, request_seq=1, capture_seq=1),
        association=dict(profile_id="TRACE-PAYLOAD-1US-PRIVATE-v2", binding_receipt_id="synthetic", e=0,
                         source_context_sha256="d"*64, timestamp_record_sha256="e"*64, quality_record_sha256="f"*64,
                         receiver_qpc_ns=1000, evaluation_now_qpc_ns=1000, evaluation_clock_id="synthetic",
                         receiver_clock_id="synthetic", freshness_limit_ns=100000000),
        companions=[dict(channel=i, format_label="SYNTHETIC_TEST", bytes=len(v), sha256=batch.digest(v)) for i, v in enumerate(companions)])
    request_bytes = batch.raw(request)
    binding = dict(canonical_build_id_full_sha256="c"*64, source_closure_file_sha256="d"*64,
                   operation_id="op", request_hash="a"*64)
    prepared = bundle.adapter.prepare_bytes(request_bytes, source, companions, build_binding=binding)
    if prepared.status != "TRACE94_PLAN_PREPARED":
        raise AssertionError(prepared.reason)
    frames = []
    for lane in lanes:
        point = dict(index=lane["index"], tick_ms=1, source_tick_ms=1, value=lane["raw_sample_uint16"], **lane["mapped_flags"])
        frame = bytearray(bundle.adapter.codec.encode_frame([point], dict(session=1, config_epoch=1, e=0), lane["channel"], lane["frame_seq"]))
        frame[3], frame[12] = 0xe4, 2
        frame[-2:] = struct.pack("<H", binascii.crc_hqx(frame[2:-2], 0xffff))
        frames.append(bytes(frame))
    packet = dict(schema="trace_batch_v1", id="req", operation_id="op", request_hex=request_bytes.hex(),
                  source_hex=source.hex(), companions_hex=[v.hex() for v in companions], build_binding=binding)
    return prepared, companions, frames, batch.raw(packet)+b"\n"


class CancelCollectOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = loader.load_selected(Path.cwd())
        cls.prepared, cls.companions, cls.frames, cls.line = synthetic_packet(cls.bundle)

    def run_synthetic(self, *, unknown_cancel):
        phases = []
        drive = batch._drive
        def observe_drive(port, reducer, phase, origin, directory, used):
            phases.append((phase, origin))
            return drive(port, reducer, phase, origin, directory, used)
        with tempfile.TemporaryDirectory() as tmp:
            port = SyntheticPort(Path(tmp), self.frames, unknown_cancel=unknown_cancel)
            with patch.object(batch, "_drive", observe_drive):
                response = batch.run_batch(port, self.bundle, self.line, SimpleNamespace(_TracePort=SyntheticPort),
                                           dict(operation_id="op", build_id="c"*32))
            records = [json.loads(p.read_bytes()[:1024].split(b"\n", 1)[0])
                       for p in sorted((port._dir / "trace-batch").glob("intent-*.bin"))]
            terminal_file = port._dir / "trace-batch/reducer-terminal.json"
            terminal = json.loads(terminal_file.read_text()) if terminal_file.exists() else None
        return json.loads(response), port, phases, records, terminal

    def test_complete_ack_cancel_then_collect_preserves_wire_and_work_origin(self):
        doc, port, phases, records, terminal = self.run_synthetic(unknown_cancel=False)
        self.assertEqual(doc["status"], "COMPLETE", doc)
        self.assertTrue(doc["wire_complete"])
        self.assertEqual(doc["terminal"], "QUIESCENT")
        self.assertEqual(bytes.fromhex(doc["raw_wire_hex"]), b"".join(self.frames))
        self.assertEqual(len(doc["results"]), 4)
        commands = [c["value"] for c in port.calls if c["kind"] == "write" and c["offset"] == 0x80]
        self.assertEqual((commands.count(1), commands.count(4), commands.count(5)), (1, 4, 1))
        self.assertNotIn(6, commands)
        cancel = next(c for c in port.calls if c["kind"] == "write" and c["offset"] == 0x80 and c["value"] == 5)
        self.assertEqual(cancel["state"], 9)
        self.assertEqual(cancel["fifo_bytes"], len(b"".join(self.frames)))
        self.assertEqual(port.cancel_fifo, b"".join(self.frames))
        self.assertEqual([p[0] for p in phases], ["work", "cleanup", "work"])
        self.assertEqual(phases[0][1], phases[2][1])
        collected = [r for r in records if r["label"] in ("FIFO count", "POP", "POP staging", "POP count", "POP ID", "peek")]
        self.assertTrue(collected)
        self.assertTrue(all(r["phase"] == "work" and r["phase_deadline_ns"] == 10000000000 for r in collected))
        self.assertFalse(terminal["failed"])
        correlated = self.bundle.adapter.correlate_collected(self.prepared.plan, bytes.fromhex(doc["raw_wire_hex"]),
                                                            self.companions, doc["results"])
        self.assertEqual(correlated["status"], "FOUR_FRAME_CORRELATION_CONSISTENT", correlated.get("reason"))
        print(json.dumps(dict(control="SYNTHETIC_TEST complete-cancel-collect", status=doc["status"],
                              phases=[p[0] for p in phases], same_work_origin=True, commands=commands,
                              results=doc["results"], raw_wire_hex=doc["raw_wire_hex"], hardware_authority=False)))

    def test_cancel_unknown_stops_before_collect_without_replay(self):
        doc, port, phases, records, terminal = self.run_synthetic(unknown_cancel=True)
        self.assertEqual(doc["status"], "UNKNOWN")
        self.assertTrue(doc["unknown"])
        self.assertFalse(doc["wire_complete"])
        self.assertFalse(doc["cleanup_observed"])
        self.assertEqual(len(doc["results"]), 4)
        commands = [c["value"] for c in port.calls if c["kind"] == "write" and c["offset"] == 0x80]
        self.assertEqual((commands.count(1), commands.count(4), commands.count(5)), (1, 4, 1))
        self.assertNotIn(6, commands)
        self.assertNotIn(8, commands)
        self.assertEqual([p[0] for p in phases], ["work", "cleanup"])
        self.assertFalse(any(r["label"] in ("FIFO count", "peek", "POP") for r in records))
        self.assertEqual(port.pos, 0)
        self.assertEqual(port.cancel_fifo, b"".join(self.frames))
        self.assertIsNone(terminal)
        print(json.dumps(dict(control="SYNTHETIC_TEST cancel-unknown", status=doc["status"],
                              phases=[p[0] for p in phases], commands=commands,
                              results=doc["results"], pop_count=port.pos, hardware_authority=False)))


if __name__ == "__main__":
    unittest.main()
