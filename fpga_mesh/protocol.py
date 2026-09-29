"""Versioned protocol objects shared by all three nodes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class ProtocolError(ValueError):
    """Raised when a protocol object violates a cross-node invariant."""


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{name} must be a non-empty string")


def _require_aware(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ProtocolError(f"{name} must be timezone-aware")


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    _require_aware(value, "datetime")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    _require_aware(parsed, "datetime")
    return parsed.astimezone(timezone.utc)


class MessageKind(StrEnum):
    HUMAN_INSTRUCTION = "human_instruction"
    AGENT_REPORT = "agent_report"
    TASK_CLAIM = "task_claim"
    STATUS = "status"
    DELEGATION = "delegation"
    HARDWARE_REQUEST = "hardware_request"
    HARDWARE_RESULT = "hardware_result"
    STOP_REQUEST = "stop_request"
    RESUME_REQUEST = "resume_request"


class SourceKind(StrEnum):
    HUMAN = "human"
    ASTRA = "astra"
    DEEPSEEK_POOL = "deepseek_pool"
    SYSTEM = "system"


class DelegationScope(StrEnum):
    FEISHU_READ = "feishu_read"
    FEISHU_WRITE = "feishu_write"
    HARDWARE_SUBMIT = "hardware_submit"
    GIT_READ = "git_read"
    GIT_WRITE = "git_write"
    TASK_CREATE = "task_create"


class HardwareOperationState(StrEnum):
    NEW = "new"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Envelope:
    message_id: str
    project_id: str
    sender: str
    recipient: str
    task_id: str
    task_version: int
    sent_at: datetime
    kind: MessageKind
    source: SourceKind
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    expires_at: datetime | None = None
    revision: int = 1
    platform_group_id: str | None = None
    platform_message_id: str | None = None
    platform_event_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "message_id",
            "project_id",
            "sender",
            "recipient",
            "task_id",
        ):
            _require_text(getattr(self, name), name)
        if not isinstance(self.task_version, int) or self.task_version < 1:
            raise ProtocolError("task_version must be a positive integer")
        if not isinstance(self.revision, int) or self.revision < 1:
            raise ProtocolError("revision must be a positive integer")
        _require_aware(self.sent_at, "sent_at")
        if self.expires_at is not None:
            _require_aware(self.expires_at, "expires_at")
        if not isinstance(self.kind, MessageKind):
            raise ProtocolError("kind must be a MessageKind")
        if not isinstance(self.source, SourceKind):
            raise ProtocolError("source must be a SourceKind")
        if not isinstance(self.payload, dict):
            raise ProtocolError("payload must be an object")

    @property
    def dedupe_key(self) -> str:
        if self.platform_group_id and self.platform_message_id:
            return f"feishu:{self.platform_group_id}:{self.platform_message_id}"
        return f"internal:{self.message_id}"

    def to_json(self) -> str:
        data = {
            "message_id": self.message_id,
            "project_id": self.project_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "task_id": self.task_id,
            "task_version": self.task_version,
            "sent_at": _format_datetime(self.sent_at),
            "kind": self.kind.value,
            "source": self.source.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "expires_at": _format_datetime(self.expires_at),
            "revision": self.revision,
            "platform_group_id": self.platform_group_id,
            "platform_message_id": self.platform_message_id,
            "platform_event_id": self.platform_event_id,
        }
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str) -> "Envelope":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProtocolError("invalid envelope JSON") from exc
        try:
            return cls(
                message_id=data["message_id"],
                project_id=data["project_id"],
                sender=data["sender"],
                recipient=data["recipient"],
                task_id=data["task_id"],
                task_version=data["task_version"],
                sent_at=_parse_datetime(data["sent_at"]),
                kind=MessageKind(data["kind"]),
                source=SourceKind(data["source"]),
                payload=data.get("payload", {}),
                correlation_id=data.get("correlation_id"),
                expires_at=_parse_datetime(data.get("expires_at")),
                revision=data.get("revision", 1),
                platform_group_id=data.get("platform_group_id"),
                platform_message_id=data.get("platform_message_id"),
                platform_event_id=data.get("platform_event_id"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ProtocolError):
                raise
            raise ProtocolError("invalid envelope fields") from exc


def task_id_from_message(group_id: str, message_id: str) -> str:
    """Derive one stable task identity from the human message source."""

    _require_text(group_id, "group_id")
    _require_text(message_id, "message_id")
    digest = hashlib.sha256(f"{group_id}\x1f{message_id}".encode("utf-8")).hexdigest()
    return f"task-{digest[:24]}"


@dataclass(frozen=True, slots=True)
class OwnershipClaim:
    claim_id: str
    task_id: str
    owner_node: str
    source_message_id: str
    revision: int
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("claim_id", "task_id", "source_message_id"):
            _require_text(getattr(self, name), name)
        if self.owner_node not in {"A", "B", "C"}:
            raise ProtocolError("owner_node must be A, B, or C")
        if not isinstance(self.revision, int) or self.revision < 1:
            raise ProtocolError("revision must be a positive integer")
        _require_aware(self.created_at, "created_at")


@dataclass(slots=True)
class Delegation:
    delegation_id: str
    parent_astra: str
    child_instance: str
    scopes: set[DelegationScope]
    expires_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("delegation_id", "parent_astra", "child_instance"):
            _require_text(getattr(self, name), name)
        if not self.scopes:
            raise ProtocolError("delegation must grant at least one scope")
        self.scopes = {DelegationScope(scope) for scope in self.scopes}
        _require_aware(self.expires_at, "expires_at")
        if self.revoked_at is not None:
            _require_aware(self.revoked_at, "revoked_at")

    def allows(
        self,
        parent_astra: str,
        child_instance: str,
        scope: DelegationScope,
        *,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(timezone.utc)
        _require_aware(current, "now")
        if self.revoked_at is not None or current >= self.expires_at:
            return False
        return (
            parent_astra == self.parent_astra
            and child_instance == self.child_instance
            and DelegationScope(scope) in self.scopes
        )

    def revoke(self, *, now: datetime | None = None) -> None:
        self.revoked_at = now or datetime.now(timezone.utc)
        _require_aware(self.revoked_at, "revoked_at")


@dataclass(slots=True)
class ChildInstance:
    instance_id: str
    node_id: str
    model: str = "deepseek-flash"
    reasoning_effort: str = "max"
    state: str = "standby"
    generation: int = 1

    def __post_init__(self) -> None:
        _require_text(self.instance_id, "instance_id")
        if self.node_id not in {"A", "B", "C"}:
            raise ProtocolError("node_id must be A, B, or C")
        if self.model != "deepseek-flash":
            raise ProtocolError("child model must be deepseek-flash")
        if self.reasoning_effort != "max":
            raise ProtocolError("child reasoning effort must be max")
        if not isinstance(self.generation, int) or self.generation < 1:
            raise ProtocolError("generation must be a positive integer")


@dataclass(slots=True)
class HardwareOperation:
    operation_id: str
    task_id: str
    task_version: int
    requester: str
    state: HardwareOperationState = HardwareOperationState.NEW
    result: dict[str, Any] | None = None
    unknown_reason: str | None = None

    def __post_init__(self) -> None:
        for name in ("operation_id", "task_id", "requester"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.task_version, int) or self.task_version < 1:
            raise ProtocolError("task_version must be a positive integer")
        self.state = HardwareOperationState(self.state)

    def queue(self) -> None:
        if self.state != HardwareOperationState.NEW:
            raise ProtocolError(f"cannot queue operation from {self.state}")
        self.state = HardwareOperationState.QUEUED

    def start(self) -> None:
        if self.state not in {
            HardwareOperationState.NEW,
            HardwareOperationState.QUEUED,
        }:
            raise ProtocolError(f"cannot start operation from {self.state}")
        self.state = HardwareOperationState.RUNNING

    def complete(self, result: dict[str, Any]) -> None:
        if self.state != HardwareOperationState.RUNNING:
            raise ProtocolError(f"cannot complete operation from {self.state}")
        self.result = dict(result)
        self.state = HardwareOperationState.SUCCEEDED

    def cancel(self, reason: str) -> None:
        if self.state in {
            HardwareOperationState.SUCCEEDED,
            HardwareOperationState.FAILED,
            HardwareOperationState.CANCELLED,
            HardwareOperationState.UNKNOWN,
        }:
            raise ProtocolError(f"cannot cancel operation from {self.state}")
        self.result = {"reason": reason}
        self.state = HardwareOperationState.CANCELLED

    def mark_unknown(self, reason: str) -> None:
        if self.state in {
            HardwareOperationState.SUCCEEDED,
            HardwareOperationState.FAILED,
            HardwareOperationState.CANCELLED,
        }:
            raise ProtocolError(f"cannot mark operation unknown from {self.state}")
        self.unknown_reason = reason
        self.state = HardwareOperationState.UNKNOWN
