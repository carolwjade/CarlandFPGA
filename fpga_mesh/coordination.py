"""Append-only remote ownership claims with receipt-loss reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class RemoteUnavailable(RuntimeError):
    pass


class RemoteReceiptLost(RuntimeError):
    """The remote may have accepted the write, but no receipt arrived."""


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    claim_id: str
    task_id: str
    owner_node: str
    source_message_id: str
    revision: int
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "task_id": self.task_id,
            "owner_node": self.owner_node,
            "source_message_id": self.source_message_id,
            "revision": self.revision,
            "created_at": self.created_at.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }


@dataclass(frozen=True, slots=True)
class ClaimResult:
    effective: bool
    owner_node: str | None
    attempts: int
    pending: bool = False
    already_owner: bool = False


class ClaimRemote(Protocol):
    def append_if_absent(self, record: ClaimRecord) -> tuple[bool, dict]:
        ...

    def get(self, task_id: str) -> dict | None:
        ...


class MemoryClaimStore:
    """Test double that preserves the fast-forward/append-only contract."""

    def __init__(
        self,
        *,
        lose_receipt_once: bool = False,
        available: bool = True,
    ):
        self.records: dict[str, dict] = {}
        self.lose_receipt_once = lose_receipt_once
        self.available = available

    def append_if_absent(self, record: ClaimRecord) -> tuple[bool, dict]:
        if not self.available:
            raise RemoteUnavailable("remote unavailable")
        existing = self.records.get(record.task_id)
        if existing is not None:
            return False, existing
        self.records[record.task_id] = record.to_dict()
        if self.lose_receipt_once:
            self.lose_receipt_once = False
            raise RemoteReceiptLost("receipt lost after append")
        return True, record.to_dict()

    def get(self, task_id: str) -> dict | None:
        if not self.available:
            raise RemoteUnavailable("remote unavailable")
        return self.records.get(task_id)


class OwnershipCoordinator:
    def __init__(self):
        self._pending: dict[str, ClaimRecord] = {}

    def claim(self, record: ClaimRecord, remote: ClaimRemote) -> ClaimResult:
        self._pending[record.task_id] = record
        try:
            accepted, authoritative = remote.append_if_absent(record)
        except RemoteReceiptLost:
            authoritative = remote.get(record.task_id)
            if authoritative is None:
                return ClaimResult(
                    effective=False,
                    owner_node=None,
                    attempts=1,
                    pending=True,
                )
            accepted = authoritative.get("claim_id") == record.claim_id
        except RemoteUnavailable:
            return ClaimResult(
                effective=False,
                owner_node=None,
                attempts=0,
                pending=True,
            )

        owner = authoritative.get("owner_node")
        effective = owner == record.owner_node
        if effective:
            self._pending.pop(record.task_id, None)
        return ClaimResult(
            effective=effective,
            owner_node=owner,
            attempts=1,
            already_owner=accepted and effective,
        )

    def pending(self, task_id: str) -> ClaimRecord | None:
        return self._pending.get(task_id)
