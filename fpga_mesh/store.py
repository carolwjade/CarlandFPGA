"""SQLite persistence for events, mailboxes and task versions."""

from __future__ import annotations

import json
import re
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

                CREATE TABLE IF NOT EXISTS group_outbox (
                    operation_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'astra',
                    job_id TEXT,
                    created_at TEXT NOT NULL,
                    sent_at TEXT,
                    platform_message_id TEXT,
                    cancelled_at TEXT
                );

                CREATE TABLE IF NOT EXISTS human_task_versions (
                    task_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS controller_state (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                """
            )
            columns = {
                str(row["name"]) for row in self._connection.execute(
                    "PRAGMA table_info(group_outbox)"
                )
            }
            if "role" not in columns:
                self._connection.execute(
                    "ALTER TABLE group_outbox ADD COLUMN role TEXT NOT NULL DEFAULT 'astra'"
                )
            if "job_id" not in columns:
                self._connection.execute("ALTER TABLE group_outbox ADD COLUMN job_id TEXT")
            if "cancelled_at" not in columns:
                self._connection.execute("ALTER TABLE group_outbox ADD COLUMN cancelled_at TEXT")
            for name, declaration in (
                ("attempts", "INTEGER NOT NULL DEFAULT 0"),
                ("last_attempt_at", "TEXT"),
                ("last_error", "TEXT"),
                ("next_attempt_at", "TEXT"),
                ("delivery_state", "TEXT NOT NULL DEFAULT 'ready'"),
                ("reconciliation_sha256", "TEXT"),
                ("reconciled_at", "TEXT"),
                ("resolution", "TEXT"),
            ):
                if name not in columns:
                    self._connection.execute(
                        f"ALTER TABLE group_outbox ADD COLUMN {name} {declaration}"
                    )
            if "delivery_state" not in columns:
                # Old rows contain no attempt outcome. A pending row may have
                # reached Feishu before an acknowledgement was lost; migration
                # alone is not evidence that replay is safe.
                self._connection.execute(
                    "UPDATE group_outbox SET delivery_state = 'delivery_unknown', "
                    "last_error = 'delivery_unknown:legacy_delivery_untracked' "
                    "WHERE sent_at IS NULL AND cancelled_at IS NULL"
                )
            # Only the original single sender opens this runtime store. An
            # interrupted attempt cannot be assumed unsent on its next startup.
            self._connection.execute(
                "UPDATE group_outbox SET delivery_state = 'delivery_unknown', "
                "last_error = 'delivery_unknown:interrupted_attempt', next_attempt_at = NULL "
                "WHERE delivery_state = 'inflight' AND sent_at IS NULL AND cancelled_at IS NULL"
            )
            # Rebuild the revision index for databases created before this table
            # existed; a processed newer edit must still supersede an older retry.
            for row in self._connection.execute("SELECT payload FROM inbound"):
                message = Envelope.from_json(row["payload"])
                if message.source.value == "human" and message.kind.value == "human_instruction":
                    self._connection.execute(
                        "INSERT INTO human_task_versions (task_id, version) VALUES (?, ?) "
                        "ON CONFLICT(task_id) DO UPDATE SET version = MAX(version, excluded.version)",
                        (message.task_id, message.task_version),
                    )

    def enqueue_group_report(
        self, operation_id: str, text: str, *, role: str = "astra",
        job_id: str | None = None,
    ) -> bool:
        if not operation_id or not text.strip():
            raise ValueError("group report needs operation_id and nonempty text")
        if role not in {"astra", "deepseek"}:
            raise ValueError("unknown group sender role")
        with self._connection:
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO group_outbox "
                "(operation_id, text, role, job_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (operation_id, text, role, job_id, _format_datetime(_utc_now())),
            )
        return cursor.rowcount == 1

    def pending_group_reports(self) -> list[tuple[str, str]]:
        rows = self._connection.execute(
            "SELECT operation_id, text FROM group_outbox "
            "WHERE sent_at IS NULL AND cancelled_at IS NULL "
            "ORDER BY created_at, rowid"
        ).fetchall()
        return [(str(row["operation_id"]), str(row["text"])) for row in rows]

    def pending_group_messages(self) -> list[tuple[str, str, str]]:
        rows = self._connection.execute(
            "SELECT operation_id, text, role FROM group_outbox "
            "WHERE sent_at IS NULL AND cancelled_at IS NULL "
            "ORDER BY created_at, rowid"
        ).fetchall()
        return [
            (str(row["operation_id"]), str(row["text"]), str(row["role"]))
            for row in rows
        ]

    def ack_group_report(self, operation_id: str, platform_message_id: str) -> None:
        if not isinstance(platform_message_id, str) or not platform_message_id.strip():
            raise ValueError("group acknowledgement requires a platform message ID")
        with self._connection:
            state = self.group_report_delivery(operation_id)
            if state and state["delivery_state"] == "delivery_unknown":
                raise ValueError("unknown delivery requires evidenced reconciliation")
            self._connection.execute(
                "UPDATE group_outbox SET sent_at = ?, platform_message_id = ?, "
                "last_error = NULL, next_attempt_at = NULL, delivery_state = 'sent' "
                "WHERE operation_id = ? AND sent_at IS NULL AND cancelled_at IS NULL",
                (_format_datetime(_utc_now()), platform_message_id, operation_id),
            )

    def group_report_delivery(self, operation_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT attempts, last_attempt_at, last_error, next_attempt_at, delivery_state, "
            "reconciliation_sha256, reconciled_at, resolution "
            "FROM group_outbox WHERE operation_id = ?", (operation_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def group_role_ready(self, role: str) -> bool:
        row = self._connection.execute(
            "SELECT MAX(next_attempt_at) AS retry_at, "
            "MAX(delivery_state IN ('inflight', 'delivery_unknown')) AS held FROM group_outbox "
            "WHERE role = ? AND sent_at IS NULL AND cancelled_at IS NULL", (role,),
        ).fetchone()
        retry_at = _parse_datetime(row["retry_at"])
        return not row["held"] and (retry_at is None or retry_at <= _utc_now())

    def attempt_group_report(self, operation_id: str) -> None:
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE group_outbox SET attempts = attempts + 1, last_attempt_at = ?, "
                "delivery_state = 'inflight' "
                "WHERE operation_id = ? AND sent_at IS NULL AND cancelled_at IS NULL "
                "AND delivery_state = 'ready'",
                (_format_datetime(_utc_now()), operation_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("report is not ready for a send attempt")

    def fail_group_report(
        self, operation_id: str, error: str, retry_seconds: float, *,
        delivery_unknown: bool = False,
    ) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE group_outbox SET last_error = ?, next_attempt_at = ?, delivery_state = ? "
                "WHERE operation_id = ? AND sent_at IS NULL AND cancelled_at IS NULL "
                "AND delivery_state IN ('ready', 'inflight')",
                ("delivery_unknown:" + error if delivery_unknown else error,
                 None if delivery_unknown else _format_datetime(
                     _utc_now() + timedelta(seconds=retry_seconds)),
                 "delivery_unknown" if delivery_unknown else "ready", operation_id),
            )

    def reconcile_group_report(
        self, operation_id: str, *, evidence_sha256: str,
        platform_message_id: str | None = None, confirmed_not_sent: bool = False,
    ) -> None:
        """Resolve a held original only with a reference to reviewed evidence.

        The owner must first check platform history/ID and retain the evidence
        whose SHA256 is supplied here. No timeout or UUID alone releases a hold.
        This method performs no platform request and cannot verify that evidence.
        """
        if not isinstance(evidence_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", evidence_sha256):
            raise ValueError("reconciliation requires a reviewed evidence SHA256")
        delivered = isinstance(platform_message_id, str) and bool(platform_message_id.strip())
        if (platform_message_id is not None and not delivered
                or type(confirmed_not_sent) is not bool
                or delivered == confirmed_not_sent):
            raise ValueError("choose a verified message ID or explicitly confirmed not sent")
        with self._connection:
            state = self.group_report_delivery(operation_id)
            if not state or state["delivery_state"] != "delivery_unknown":
                raise ValueError("only unknown delivery can be reconciled")
            cursor = self._connection.execute(
                "UPDATE group_outbox SET delivery_state = ?, last_error = NULL, "
                "next_attempt_at = NULL, reconciliation_sha256 = ?, reconciled_at = ?, "
                "resolution = ?, platform_message_id = ?, sent_at = ? "
                "WHERE operation_id = ? AND delivery_state = 'delivery_unknown' "
                "AND sent_at IS NULL AND cancelled_at IS NULL",
                ("sent" if delivered else "ready", evidence_sha256, _format_datetime(_utc_now()),
                 "verified_sent" if delivered else "verified_not_sent", platform_message_id,
                 _format_datetime(_utc_now()) if delivered else None, operation_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("report is no longer pending reconciliation")

    def group_outbox_health(self) -> dict[str, Any]:
        rows = self._connection.execute(
            "SELECT role, attempts, last_attempt_at, last_error, next_attempt_at, delivery_state "
            "FROM group_outbox WHERE sent_at IS NULL AND cancelled_at IS NULL "
            "ORDER BY last_attempt_at, rowid"
        ).fetchall()
        roles: dict[str, dict[str, Any]] = {}
        last_error = None
        for row in rows:
            state = roles.setdefault(row["role"], {
                "pending": 0, "attempts": 0, "last_attempt_at": None,
                "last_error": None, "next_attempt_at": None,
                "held": 0,
            })
            state["pending"] += 1
            state["attempts"] += row["attempts"]
            state["held"] += row["delivery_state"] in {"inflight", "delivery_unknown"}
            if row["last_attempt_at"]:
                state["last_attempt_at"] = row["last_attempt_at"]
            if row["last_error"]:
                state["last_error"] = last_error = row["last_error"]
            if row["next_attempt_at"]:
                state["next_attempt_at"] = max(
                    state["next_attempt_at"] or "", row["next_attempt_at"],
                )
        return {"pending": len(rows), "last_error": last_error, "roles": roles,
                "held": sum(state["held"] for state in roles.values())}

    def group_report_job(self, operation_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT job_id FROM group_outbox WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        return str(row["job_id"]) if row and row["job_id"] else None

    def cancel_group_report(self, operation_id: str) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE group_outbox SET cancelled_at = ? "
                "WHERE operation_id = ? AND sent_at IS NULL",
                (_format_datetime(_utc_now()), operation_id),
            )

    def group_report_status(self, operation_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT sent_at, cancelled_at FROM group_outbox WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        return "cancelled" if row["cancelled_at"] else "sent" if row["sent_at"] else "pending"

    def accept_inbound(self, message: Envelope) -> bool:
        with self._connection:
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
            if cursor.rowcount == 1 and message.source.value == "human" and message.kind.value == "human_instruction":
                self._connection.execute(
                    "INSERT INTO human_task_versions (task_id, version) VALUES (?, ?) "
                    "ON CONFLICT(task_id) DO UPDATE SET version = MAX(version, excluded.version)",
                    (message.task_id, message.task_version),
                )
        return cursor.rowcount == 1

    def latest_human_task_version(self, task_id: str) -> int | None:
        row = self._connection.execute(
            "SELECT version FROM human_task_versions WHERE task_id = ?", (task_id,),
        ).fetchone()
        return int(row["version"]) if row else None

    def load_control_state(self) -> tuple[datetime | None, datetime | None, str | None]:
        row = self._connection.execute(
            "SELECT payload FROM controller_state WHERE key = 'human_pause'"
        ).fetchone()
        if row is None:
            return None, None, None
        data = json.loads(row["payload"])
        return (
            _parse_datetime(data.get("last_control_at")),
            _parse_datetime(data.get("paused_at")),
            data.get("scope"),
        )

    def save_control_state(
        self, last_control_at: datetime, paused_at: datetime | None,
        scope: str | None,
    ) -> None:
        payload = json.dumps({
            "last_control_at": _format_datetime(last_control_at),
            "paused_at": _format_datetime(paused_at), "scope": scope,
        }, sort_keys=True)
        with self._connection:
            self._connection.execute(
                "INSERT INTO controller_state (key, payload) VALUES ('human_pause', ?) "
                "ON CONFLICT(key) DO UPDATE SET payload = excluded.payload",
                (payload,),
            )

    def pending_inbound(self, *, now: datetime | None = None) -> list[StoredMessage]:
        current = _format_datetime(now or _utc_now())
        rows = self._connection.execute(
            """
            SELECT * FROM inbound
            WHERE processed_at IS NULL
              AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            ORDER BY received_at, rowid
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
        inserted, _ = self._persist_outbound(message, peer_id)
        return inserted

    def prepare_outbound_operation(
        self, message: Envelope, peer_id: str,
    ) -> tuple[Envelope, bool, bool]:
        """Reuse the original tool operation, ignoring only generated sent_at.

        Return the canonical envelope, whether it was inserted, and whether
        transport delivery was already acknowledged. Never reset its status.
        """
        inserted, row = self._persist_outbound(
            message, peer_id, ignore_generated_sent_at=True,
        )
        assert row is not None
        return Envelope.from_json(row["payload"]), inserted, bool(row["acked_at"])

    def _persist_outbound(
        self, message: Envelope, peer_id: str,
        *, ignore_generated_sent_at: bool = False,
    ) -> tuple[bool, sqlite3.Row | None]:
        payload = message.to_json()
        with self._connection:
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
                    payload,
                    _format_datetime(_utc_now()),
                ),
            )
            existing = self._connection.execute(
                "SELECT * FROM outbox WHERE message_id = ?",
                (message.message_id,),
            ).fetchone()
            if existing is None:
                if ignore_generated_sent_at:
                    raise ValueError("outbound dedupe key belongs to another message")
                return False, None
            if cursor.rowcount == 0:
                if existing["peer_id"] != peer_id:
                    raise ValueError("outbound message ID already belongs to a different peer")
                before, after = existing["payload"], payload
                if ignore_generated_sent_at:
                    before, after = json.loads(before), json.loads(after)
                    before.pop("sent_at", None)
                    after.pop("sent_at", None)
                if before != after:
                    raise ValueError("outbound message ID already has different content")
        return cursor.rowcount == 1, existing

    def next_outbound(
        self, *, now: datetime | None = None,
        exclude_peer_ids: set[str] | None = None,
    ) -> OutboxItem | None:
        current = _format_datetime(now or _utc_now())
        excluded = sorted(exclude_peer_ids or ())
        exclusion = (
            f" AND peer_id NOT IN ({','.join('?' for _ in excluded)})"
            if excluded else ""
        )
        with self._connection:
            row = self._connection.execute(
                f"""
                SELECT * FROM outbox
                WHERE acked_at IS NULL
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                  {exclusion}
                ORDER BY created_at, message_id
                LIMIT 1
                """,
                (current, *excluded),
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
