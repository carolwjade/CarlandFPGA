"""SQLite persistence for events, mailboxes and task versions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .protocol import Envelope
from .tasks import TaskRecord, VersionConflict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


@dataclass(frozen=True, slots=True)
class StoredMessage:
    message: Envelope
    attempts: int = 0
    last_error: str | None = None
    next_attempt_at: datetime | None = None
    processed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OutboxItem:
    message: Envelope
    peer_id: str
    attempts: int
    last_error: str | None = None
    next_attempt_at: datetime | None = None


class SQLiteStore:
    """Small transactional store shared by controller instances."""

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
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()
        self._closed = False

    def _create_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS inbound (
                    message_id TEXT PRIMARY KEY,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    processed_at TEXT,
                    expires_at TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    next_attempt_at TEXT
                );

                CREATE TABLE IF NOT EXISTS outbox (
                    message_id TEXT PRIMARY KEY,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    peer_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    acked_at TEXT,
                    last_error TEXT,
                    next_attempt_at TEXT
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def accept_inbound(self, message: Envelope) -> bool:
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO inbound (
                message_id, dedupe_key, payload, received_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.message_id,
                message.dedupe_key,
                message.to_json(),
                _format_datetime(_utc_now()),
                _format_datetime(message.expires_at),
            ),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def pending_inbound(self, *, now: datetime | None = None) -> list[StoredMessage]:
        current = _format_datetime(now or _utc_now())
        rows = self._connection.execute(
            """
            SELECT * FROM inbound
            WHERE processed_at IS NULL
              AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            ORDER BY received_at, message_id
            """,
            (current,),
        ).fetchall()
        return [self._stored_message(row) for row in rows]

    def mark_inbound_processed(self, message_id: str) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE inbound SET processed_at = ?, next_attempt_at = NULL WHERE message_id = ?",
                (_format_datetime(_utc_now()), message_id),
            )

    def mark_inbound_failed(
        self,
        message_id: str,
        error: str,
        *,
        retry_at: datetime | None = None,
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                UPDATE inbound
                SET attempts = attempts + 1,
                    last_error = ?,
                    next_attempt_at = ?
                WHERE message_id = ?
                """,
                (error, _format_datetime(retry_at), message_id),
            )

    def enqueue_outbound(self, message: Envelope, peer_id: str) -> bool:
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO outbox (
                message_id, dedupe_key, peer_id, payload, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.message_id,
                f"{peer_id}:{message.dedupe_key}",
                peer_id,
                message.to_json(),
                _format_datetime(_utc_now()),
            ),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def next_outbound(self, *, now: datetime | None = None) -> OutboxItem | None:
        current = _format_datetime(now or _utc_now())
        with self._connection:
            row = self._connection.execute(
                """
                SELECT * FROM outbox
                WHERE acked_at IS NULL
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                ORDER BY created_at, message_id
                LIMIT 1
                """,
                (current,),
            ).fetchone()
            if row is None:
                return None
            self._connection.execute(
                "UPDATE outbox SET attempts = attempts + 1 WHERE message_id = ?",
                (row["message_id"],),
            )
            updated = self._connection.execute(
                "SELECT * FROM outbox WHERE message_id = ?",
                (row["message_id"],),
            ).fetchone()
        return self._outbox_item(updated)

    def pending_outbound(self) -> list[OutboxItem]:
        rows = self._connection.execute(
            """
            SELECT * FROM outbox
            WHERE acked_at IS NULL
            ORDER BY created_at, message_id
            """
        ).fetchall()
        return [self._outbox_item(row) for row in rows]

    def mark_outbound_failed(
        self,
        message_id: str,
        error: str,
        *,
        retry_at: datetime | None,
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                UPDATE outbox
                SET last_error = ?, next_attempt_at = ?
                WHERE message_id = ?
                """,
                (error, _format_datetime(retry_at), message_id),
            )

    def ack_outbound(self, message_id: str) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE outbox SET acked_at = ?, next_attempt_at = NULL WHERE message_id = ?",
                (_format_datetime(_utc_now()), message_id),
            )

    def put_task(
        self,
        task: TaskRecord,
        *,
        expected_version: int | None = None,
    ) -> None:
        with self._connection:
            row = self._connection.execute(
                "SELECT version FROM tasks WHERE task_id = ?",
                (task.task_id,),
            ).fetchone()
            current_version = row["version"] if row else None
            if expected_version is not None and current_version != expected_version:
                raise VersionConflict(
                    f"task {task.task_id}: expected {expected_version}, "
                    f"found {current_version}"
                )
            if current_version is not None and task.version <= current_version:
                raise VersionConflict(
                    f"task {task.task_id}: version {task.version} is not newer "
                    f"than {current_version}"
                )
            self._connection.execute(
                """
                INSERT INTO tasks (task_id, version, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    version = excluded.version,
                    payload = excluded.payload
                """,
                (
                    task.task_id,
                    task.version,
                    json.dumps(task.to_dict(), ensure_ascii=False, sort_keys=True),
                ),
            )

    def get_task(self, task_id: str) -> TaskRecord | None:
        row = self._connection.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row["payload"])
        return TaskRecord(
            task_id=data["task_id"],
            version=data["version"],
            owner_node=data["owner_node"],
            objective=data["objective"],
            state=data["state"],
            allowed_operations=set(data.get("allowed_operations", [])),
            dependencies=list(data.get("dependencies", [])),
            current_phase=data.get("current_phase", ""),
            evidence=list(data.get("evidence", [])),
            next_step=data.get("next_step", ""),
            updated_at=_parse_datetime(data["updated_at"]),
        )

    def append_event(
        self,
        event_id: str,
        kind: str,
        payload: dict[str, Any],
    ) -> bool:
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO events (event_id, kind, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                event_id,
                kind,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                _format_datetime(_utc_now()),
            ),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def _stored_message(self, row: sqlite3.Row) -> StoredMessage:
        return StoredMessage(
            message=Envelope.from_json(row["payload"]),
            attempts=row["attempts"],
            last_error=row["last_error"],
            next_attempt_at=_parse_datetime(row["next_attempt_at"]),
            processed_at=_parse_datetime(row["processed_at"]),
        )

    def _outbox_item(self, row: sqlite3.Row) -> OutboxItem:
        return OutboxItem(
            message=Envelope.from_json(row["payload"]),
            peer_id=row["peer_id"],
            attempts=row["attempts"],
            last_error=row["last_error"],
            next_attempt_at=_parse_datetime(row["next_attempt_at"]),
        )
