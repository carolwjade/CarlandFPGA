"""Exclusive FPGA experiment queue with idempotent operation IDs."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class HardwareConflict(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class HardwareRequest:
    operation_id: str
    task_id: str
    task_version: int
    requester: str
    code_commit: str
    test_steps: list[str]
    expected_result: str

    @property
    def request_hash(self) -> str:
        payload = {
            "operation_id": self.operation_id,
            "task_id": self.task_id,
            "task_version": self.task_version,
            "requester": self.requester,
            "code_commit": self.code_commit,
            "test_steps": self.test_steps,
            "expected_result": self.expected_result,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class HardwareResult:
    operation_id: str
    state: str
    result: dict[str, Any] = field(default_factory=dict)


class HardwareAdapter(Protocol):
    async def execute(
        self,
        operation: HardwareRequest,
        stop_event: asyncio.Event,
    ) -> HardwareResult:
        ...


class FakeHardwareAdapter:
    def __init__(self, delay: float = 0.0):
        self.delay = delay
        self.active = 0
        self.max_active = 0
        self.stop_seen = False

    async def execute(
        self,
        operation: HardwareRequest,
        stop_event: asyncio.Event,
    ) -> HardwareResult:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            remaining = self.delay
            while remaining > 0:
                if stop_event.is_set():
                    self.stop_seen = True
                    return HardwareResult(
                        operation_id=operation.operation_id,
                        state="cancelled",
                        result={"reason": "stop requested"},
                    )
                step = min(0.01, remaining)
                await asyncio.sleep(step)
                remaining -= step
            return HardwareResult(
                operation_id=operation.operation_id,
                state="succeeded",
                result={"expected": operation.expected_result},
            )
        finally:
            self.active -= 1


class HardwareService:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            str(self.path),
            timeout=30,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hardware_operations (
                operation_id TEXT PRIMARY KEY,
                request_hash TEXT NOT NULL,
                payload TEXT NOT NULL,
                state TEXT NOT NULL,
                result TEXT
            )
            """
        )
        self._connection.commit()
        self._run_lock = asyncio.Lock()
        self._stop_events: dict[str, asyncio.Event] = {}
        self._closed = False

    def submit(self, request: HardwareRequest) -> HardwareRequest:
        row = self._connection.execute(
            "SELECT request_hash, payload FROM hardware_operations WHERE operation_id = ?",
            (request.operation_id,),
        ).fetchone()
        if row is not None:
            if row["request_hash"] != request.request_hash:
                raise HardwareConflict(
                    f"operation_id {request.operation_id} already has different input"
                )
            return request
        self._connection.execute(
            """
            INSERT INTO hardware_operations
            (operation_id, request_hash, payload, state, result)
            VALUES (?, ?, ?, 'queued', NULL)
            """,
            (
                request.operation_id,
                request.request_hash,
                json.dumps(asdict(request), ensure_ascii=False, sort_keys=True),
            ),
        )
        self._connection.commit()
        return request

    def queue(self) -> list[HardwareRequest]:
        rows = self._connection.execute(
            "SELECT payload FROM hardware_operations WHERE state = 'queued' ORDER BY rowid"
        ).fetchall()
        return [HardwareRequest(**json.loads(row["payload"])) for row in rows]

    async def run_next(self, adapter: HardwareAdapter) -> HardwareResult | None:
        async with self._run_lock:
            row = self._connection.execute(
                "SELECT * FROM hardware_operations WHERE state = 'queued' ORDER BY rowid LIMIT 1"
            ).fetchone()
            if row is None:
                if self._connection.execute(
                    "SELECT 1 FROM hardware_operations WHERE state = 'unknown' LIMIT 1"
                ).fetchone():
                    raise HardwareConflict(
                        "hardware state is unknown; reconcile before retrying"
                    )
                return None
            request = HardwareRequest(**json.loads(row["payload"]))
            self._set_state(request.operation_id, "running")
            stop_event = asyncio.Event()
            self._stop_events[request.operation_id] = stop_event
            try:
                result = await adapter.execute(request, stop_event)
                self._set_state(
                    request.operation_id,
                    result.state,
                    result.result,
                )
                return result
            finally:
                self._stop_events.pop(request.operation_id, None)

    def request_stop(self, operation_id: str) -> bool:
        row = self._connection.execute(
            "SELECT state FROM hardware_operations WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        if row is None or row["state"] in {"succeeded", "failed", "cancelled", "unknown"}:
            return False
        event = self._stop_events.get(operation_id)
        if event is not None:
            event.set()
        else:
            self._set_state(operation_id, "cancelled", {"reason": "not started"})
        return True

    def recover_unknown(self) -> list[str]:
        rows = self._connection.execute(
            "SELECT operation_id FROM hardware_operations WHERE state = 'running'"
        ).fetchall()
        ids = [row["operation_id"] for row in rows]
        for operation_id in ids:
            self._set_state(operation_id, "unknown", {"reason": "restart"})
        return ids

    def state(self, operation_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT state FROM hardware_operations WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        return row["state"] if row else None

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def _set_state(
        self,
        operation_id: str,
        state: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        self._connection.execute(
            """
            UPDATE hardware_operations
            SET state = ?, result = ?
            WHERE operation_id = ?
            """,
            (
                state,
                json.dumps(result, ensure_ascii=False, sort_keys=True)
                if result is not None
                else None,
                operation_id,
            ),
        )
        self._connection.commit()

    def _mark_running_for_test(self, operation_id: str) -> None:
        self._set_state(operation_id, "running")
