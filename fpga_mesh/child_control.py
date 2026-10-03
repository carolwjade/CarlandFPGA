"""Durable, event-driven delegation from one Astra to its local child pool."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .pool import InstancePool
from .protocol import Envelope, MessageKind, SourceKind


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ChildCoordinator:
    """The parent chooses assignments; the program waits and records results."""

    TERMINAL = frozenset({"completed", "failed", "cancelled", "interrupted"})

    def __init__(
        self, *, node_id: str, project_id: str, pool: InstancePool,
        state_path: str | Path,
    ):
        self.node_id = node_id
        self.project_id = project_id
        self.pool = pool
        path = Path(state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS child_jobs (
                job_id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_version INTEGER NOT NULL,
                instructions TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_versions (
                task_id TEXT PRIMARY KEY,
                version INTEGER NOT NULL
            );
            """
        )
        # An earlier process may have died while a tool or board operation ran.
        # Never replay such work without a fresh decision from Astra.
        self._db.execute(
            "UPDATE child_jobs SET status='interrupted', updated_at=? "
            "WHERE status IN ('queued', 'running')", (_now(),),
        )
        self._db.commit()
        self._running: dict[str, asyncio.Task[None]] = {}
        self._changed = asyncio.Event()
        self._allocation_lock = asyncio.Lock()

    async def delegate(
        self, *, task_id: str, task_version: int, text: str,
        instance_id: str | None = None, auto_expand: bool = False,
    ) -> dict:
        async with self._allocation_lock:
            return await self._delegate_locked(
                task_id=task_id, task_version=task_version, text=text,
                instance_id=instance_id, auto_expand=auto_expand,
            )

    async def _delegate_locked(
        self, *, task_id: str, task_version: int, text: str,
        instance_id: str | None, auto_expand: bool,
    ) -> dict:
        if not task_id.strip() or not text.strip() or task_version < 1:
            raise ValueError("task_id, positive task_version, and text are required")
        latest = self._db.execute(
            "SELECT version FROM task_versions WHERE task_id=?", (task_id,),
        ).fetchone()
        if latest is not None and task_version < latest["version"]:
            raise ValueError("stale child assignment task_version")
        if instance_id is None:
            standby = [item for item in self.pool.snapshot()["instances"]
                       if item["state"] == "standby"]
            if not standby and auto_expand:
                await self.pool.ensure_standby(
                    len(self.pool.snapshot()["instances"]) + 1,
                )
                standby = [item for item in self.pool.snapshot()["instances"]
                           if item["state"] == "standby"]
            if not standby:
                raise RuntimeError("no standby child; Astra may scale the pool")
            instance_id = standby[0]["instance_id"]
        else:
            matching = [item for item in self.pool.snapshot()["instances"]
                        if item["instance_id"] == instance_id]
            if not matching or matching[0]["state"] != "standby":
                raise RuntimeError("selected child is not standby")

        self.update_task_version(task_id, task_version)
        job_id = f"child-{uuid4().hex}"
        created_at = _now()
        # Claim the instance before yielding control so concurrent dispatches
        # cannot both select the same standby worker.
        await self.pool.reserve(instance_id)
        try:
            latest_after_claim = self._db.execute(
                "SELECT version FROM task_versions WHERE task_id=?", (task_id,),
            ).fetchone()
            if (latest_after_claim is not None and
                    latest_after_claim["version"] > task_version):
                raise ValueError("stale child assignment task_version")
            with self._db:
                self._db.execute(
                    "INSERT INTO child_jobs VALUES (?, ?, ?, ?, ?, 'queued', NULL, NULL, ?, ?)",
                    (job_id, instance_id, task_id, task_version, text,
                     created_at, created_at),
                )
        except Exception:
            await self.pool.return_to_standby(instance_id)
            raise
        self._running[job_id] = asyncio.create_task(
            self._run(job_id, instance_id, task_id, task_version, text),
            name=job_id,
        )
        return self.job(job_id)

    async def scale(self, count: int) -> dict:
        async with self._allocation_lock:
            await self.pool.scale_to(count)
            return self.pool.snapshot()

    def update_task_version(self, task_id: str, version: int) -> None:
        if version < 1:
            raise ValueError("version must be positive")
        with self._db:
            self._db.execute(
                "INSERT INTO task_versions(task_id, version) VALUES (?, ?) "
                "ON CONFLICT(task_id) DO UPDATE SET version=max(version, excluded.version)",
                (task_id, version),
            )
        self._changed.set()

    def job(self, job_id: str) -> dict:
        row = self._db.execute(
            "SELECT j.*, v.version AS latest_version FROM child_jobs j "
            "LEFT JOIN task_versions v ON v.task_id=j.task_id WHERE j.job_id=?",
            (job_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown child job: {job_id}")
        return {
            "job_id": row["job_id"],
            "instance_id": row["instance_id"],
            "task_id": row["task_id"],
            "task_version": row["task_version"],
            "status": row["status"],
            "terminal": row["status"] in self.TERMINAL,
            "stale": bool(row["latest_version"] and
                          row["latest_version"] > row["task_version"]),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def status(self) -> dict:
        rows = self._db.execute(
            "SELECT job_id FROM child_jobs ORDER BY created_at, job_id"
        ).fetchall()
        return {"pool": self.pool.snapshot(),
                "jobs": [self.job(row["job_id"]) for row in rows]}

    async def wait(self, job_ids: list[str]) -> list[dict]:
        if not job_ids:
            raise ValueError("at least one job_id is required")
        while True:
            results = [self.job(job_id) for job_id in job_ids]
            if all(item["terminal"] for item in results):
                return results
            self._changed.clear()
            # The event and data are in the same process; check again after
            # clearing to avoid a completion between the check and wait.
            if all(self.job(job_id)["terminal"] for job_id in job_ids):
                continue
            await self._changed.wait()

    async def cancel(self, job_id: str) -> dict:
        job = self.job(job_id)
        task = self._running.get(job_id)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self.job(job_id)

    async def cancel_all(self) -> list[dict]:
        return [await self.cancel(job_id) for job_id in list(self._running)]

    async def close(self) -> None:
        await self.cancel_all()
        self._db.close()

    async def _run(
        self, job_id: str, instance_id: str, task_id: str,
        task_version: int, text: str,
    ) -> None:
        self._record(job_id, "running")
        message = Envelope(
            message_id=job_id,
            project_id=self.project_id,
            sender=f"{self.node_id}/Astra-{self.node_id}",
            recipient=f"{self.node_id}/DeepSeek-{self.node_id}",
            task_id=task_id,
            task_version=task_version,
            sent_at=datetime.now(timezone.utc),
            kind=MessageKind.DELEGATION,
            source=SourceKind.ASTRA,
            payload={"text": text},
            correlation_id=job_id,
        )
        try:
            result = await self.pool.wake(instance_id, message)
            self._record(job_id, "completed" if result.accepted else "failed",
                         result=result.output)
        except asyncio.CancelledError:
            self._record(job_id, "cancelled")
            raise
        except Exception as exc:  # noqa: BLE001 - persisted for parent review
            self._record(job_id, "failed", error=f"{type(exc).__name__}: {exc}")
        finally:
            await self.pool.return_to_standby(instance_id)
            self._running.pop(job_id, None)
            self._changed.set()

    def _record(
        self, job_id: str, status: str, *, result: dict | None = None,
        error: str | None = None,
    ) -> None:
        with self._db:
            self._db.execute(
                "UPDATE child_jobs SET status=?, result_json=?, error=?, "
                "updated_at=? WHERE job_id=?",
                (status, json.dumps(result, ensure_ascii=False) if result is not None
                 else None, error, _now(), job_id),
            )
        self._changed.set()


class LocalControlServer:
    """Authenticated loopback socket owned by the node process."""

    def __init__(
        self, coordinator: ChildCoordinator, *, token: str,
        discovery_path: str | Path | None = None,
    ):
        if not token:
            raise ValueError("a private control token is required")
        self.coordinator = coordinator
        self.token = token
        self.discovery_path = Path(discovery_path) if discovery_path else None
        self._server: asyncio.AbstractServer | None = None
        self.port: int | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle, host="127.0.0.1", port=0, limit=1 << 20,
        )
        self.port = self._server.sockets[0].getsockname()[1]
        if self.discovery_path is not None:
            self.discovery_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.discovery_path.with_suffix(".tmp")
            temporary.write_text(json.dumps({
                "host": "127.0.0.1", "port": self.port,
                "token": self.token, "pid": os.getpid(),
            }), encoding="utf-8")
            os.replace(temporary, self.discovery_path)

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self.discovery_path is not None and self.discovery_path.exists():
            try:
                current = json.loads(self.discovery_path.read_text(encoding="utf-8"))
                if current.get("token") == self.token:
                    self.discovery_path.unlink()
            except (OSError, ValueError):
                pass

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request = json.loads(await reader.readline())
            if not secrets.compare_digest(str(request.get("token", "")), self.token):
                raise PermissionError("invalid local control token")
            action = request.get("action")
            args = request.get("arguments", {})
            if not isinstance(args, dict):
                raise ValueError("arguments must be an object")
            if action == "status":
                result = self.coordinator.status()
            elif action == "scale":
                result = await self.coordinator.scale(int(args["count"]))
            elif action == "delegate":
                result = await self.coordinator.delegate(
                    task_id=str(args["task_id"]),
                    task_version=int(args["task_version"]),
                    text=str(args["text"]),
                    instance_id=args.get("instance_id"),
                    auto_expand=bool(args.get("auto_expand", False)),
                )
            elif action == "wait":
                result = await self.coordinator.wait(list(args["job_ids"]))
            elif action == "cancel":
                result = await self.coordinator.cancel(str(args["job_id"]))
            elif action == "task_version":
                self.coordinator.update_task_version(
                    str(args["task_id"]), int(args["version"]),
                )
                result = {"updated": True}
            else:
                raise ValueError("unknown local control action")
            response = {"result": result}
        except Exception as exc:  # noqa: BLE001 - return a bounded protocol error
            response = {"error": {"type": type(exc).__name__,
                                  "message": str(exc)[:300]}}
        try:
            writer.write((json.dumps(response, ensure_ascii=False) + "\n").encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


class LocalControlClient:
    def __init__(self, *, host: str, port: int, token: str):
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("control client may only connect to loopback")
        self.host = host
        self.port = port
        self.token = token

    @classmethod
    def from_discovery_file(cls, path: str | Path) -> "LocalControlClient":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(host=str(data["host"]), port=int(data["port"]),
                   token=str(data["token"]))

    async def call(self, action: str, arguments: dict) -> object:
        reader, writer = await asyncio.open_connection(
            self.host, self.port, limit=1 << 20,
        )
        try:
            payload = {"token": self.token, "action": action,
                       "arguments": arguments}
            writer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode())
            await writer.drain()
            line = await reader.readline()
            if not line:
                raise ConnectionError("local control connection closed")
            response = json.loads(line)
            if "error" in response:
                error = response["error"]
                if error["type"] == "PermissionError":
                    raise PermissionError(error["message"])
                if error["type"] == "KeyError":
                    raise KeyError(error["message"])
                raise RuntimeError(error["message"])
            return response["result"]
        finally:
            writer.close()
            await writer.wait_closed()


class LocalControlFileClient:
    """Resolve the latest loopback endpoint at call time across restarts."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    async def call(self, action: str, arguments: dict) -> object:
        return await LocalControlClient.from_discovery_file(self.path).call(
            action, arguments,
        )
