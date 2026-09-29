"""Task state and version helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class TaskState(StrEnum):
    NEW = "new"
    CLAIMED = "claimed"
    WORKING = "working"
    WAITING_PEER = "waiting_peer"
    WAITING_SUBAGENT = "waiting_subagent"
    WAITING_HUMAN = "waiting_human"
    WAITING_HARDWARE = "waiting_hardware"
    QUOTA_BLOCKED = "quota_blocked"
    AUTH_REQUIRED = "auth_required"
    HUMAN_PAUSED = "human_paused"
    RECOVERING = "recovering"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_TASK_STATES = {
    TaskState.COMPLETE,
    TaskState.FAILED,
    TaskState.CANCELLED,
}


class VersionConflict(RuntimeError):
    """Raised when an optimistic task update is based on stale state."""


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    version: int
    owner_node: str
    objective: str
    state: TaskState
    allowed_operations: set[str] = field(default_factory=set)
    dependencies: list[str] = field(default_factory=list)
    current_phase: str = ""
    evidence: list[str] = field(default_factory=list)
    next_step: str = ""
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if self.version < 1:
            raise ValueError("version must be positive")
        if self.owner_node not in {"A", "B", "C"}:
            raise ValueError("owner_node must be A, B, or C")
        self.state = TaskState(self.state)
        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")

    def transition(
        self,
        state: TaskState,
        *,
        next_step: str | None = None,
        evidence: str | None = None,
    ) -> "TaskRecord":
        if self.state in TERMINAL_TASK_STATES:
            raise ValueError(f"cannot transition terminal task from {self.state}")
        self.state = TaskState(state)
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        if next_step is not None:
            self.next_step = next_step
        if evidence is not None:
            self.evidence.append(evidence)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "version": self.version,
            "owner_node": self.owner_node,
            "objective": self.objective,
            "state": self.state.value,
            "allowed_operations": sorted(self.allowed_operations),
            "dependencies": list(self.dependencies),
            "current_phase": self.current_phase,
            "evidence": list(self.evidence),
            "next_step": self.next_step,
            "updated_at": self.updated_at.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
