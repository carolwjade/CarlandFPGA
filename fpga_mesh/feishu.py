"""Feishu six-role mapping, human-message routing and delegated group I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable

from .protocol import (
    Delegation,
    DelegationScope,
    Envelope,
    MessageKind,
    SourceKind,
    task_id_from_message,
)


class BotRoleKind(StrEnum):
    ASTRA = "astra"
    DEEPSEEK = "deepseek"


@dataclass(frozen=True, slots=True)
class BotIdentity:
    node_id: str
    kind: BotRoleKind
    app_id: str
    app_secret_ref: str
    bot_id: str


class RoleRegistry:
    def __init__(self, identities: list[BotIdentity]):
        if len(identities) != 6:
            raise ValueError("exactly six Feishu roles are required")
        keys = {(item.node_id, item.kind) for item in identities}
        expected = {
            (node, kind)
            for node in ("A", "B", "C")
            for kind in (BotRoleKind.ASTRA, BotRoleKind.DEEPSEEK)
        }
        if keys != expected:
            raise ValueError("Feishu roles must cover A/B/C Astra and DeepSeek")
        app_ids = [item.app_id for item in identities]
        if len(set(app_ids)) != 6:
            raise ValueError("Feishu app IDs must be unique")
        self.identities = sorted(
            identities,
            key=lambda item: (item.node_id, item.kind.value),
        )
        self._by_key = {(item.node_id, item.kind): item for item in identities}
        self._by_app_id = {item.app_id: item for item in identities}

    def get(self, node_id: str, kind: BotRoleKind) -> BotIdentity:
        return self._by_key[(node_id, BotRoleKind(kind))]

    def by_app_id(self, app_id: str) -> BotIdentity | None:
        return self._by_app_id.get(app_id)

    def subscribed_apps(self) -> list[BotIdentity]:
        return [
            item
            for item in self.identities
            if item.kind == BotRoleKind.ASTRA
        ]

    def is_subscribed(self, app_id: str) -> bool:
        item = self._by_app_id.get(app_id)
        return bool(item and item.kind == BotRoleKind.ASTRA)


@dataclass(frozen=True, slots=True)
class FeishuMessage:
    event_id: str
    group_id: str
    message_id: str
    sender_id: str
    sender_type: str
    text: str
    revision: int
    mentioned_app_id: str | None
    created_at: datetime
    deleted: bool = False
    attachment_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouteDecision:
    action: str
    target_app_id: str | None = None
    task_id: str | None = None
    task_version: int = 0
    envelope: Envelope | None = None
    child_wakeups: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PublishedMessage:
    sender_app_id: str
    instance_id: str
    message_id: str
    text: str
    task_id: str


class HumanMessageRouter:
    def __init__(self, roles: RoleRegistry):
        self.roles = roles
        self._seen_events: dict[str, int] = {}
        self._message_revisions: dict[tuple[str, str], int] = {}
        self._grants: dict[str, Delegation] = {}

    def ingest(self, message: FeishuMessage, *, local_node: str) -> RouteDecision:
        if local_node not in {"A", "B", "C"}:
            raise ValueError("local_node must be A, B, or C")
        previous_revision = self._seen_events.get(message.event_id, 0)
        if message.revision <= previous_revision:
            return RouteDecision(action="duplicate")
        self._seen_events[message.event_id] = message.revision

        if message.sender_type != "user":
            return RouteDecision(action="evidence")
        if message.deleted:
            return RouteDecision(action="deleted")
        if not message.text.strip():
            return RouteDecision(action="evidence")

        target = self._target_identity(message, local_node=local_node)
        message_key = (message.group_id, message.message_id)
        previous_message_revision = self._message_revisions.get(message_key, 0)
        task_id = task_id_from_message(message.group_id, message.message_id)
        action = "dispatch" if previous_message_revision == 0 else "revision"
        self._message_revisions[message_key] = message.revision
        envelope = Envelope(
            message_id=message.event_id,
            project_id="fpga-main",
            sender=message.sender_id,
            recipient=target.app_id,
            task_id=task_id,
            task_version=message.revision,
            sent_at=message.created_at.astimezone(timezone.utc),
            kind=MessageKind.HUMAN_INSTRUCTION,
            source=SourceKind.HUMAN,
            payload={
                "text": message.text,
                "attachment_refs": list(message.attachment_refs),
            },
            platform_group_id=message.group_id,
            platform_message_id=message.message_id,
            platform_event_id=message.event_id,
        )
        return RouteDecision(
            action=action,
            target_app_id=target.app_id,
            task_id=task_id,
            task_version=message.revision,
            envelope=envelope,
            child_wakeups=[],
        )

    def grant(
        self,
        *,
        parent_astra: str,
        child_instance: str,
        scopes: set[DelegationScope],
        expires_at: datetime,
    ) -> Delegation:
        delegation_id = f"deleg-{len(self._grants) + 1}"
        grant = Delegation(
            delegation_id=delegation_id,
            parent_astra=parent_astra,
            child_instance=child_instance,
            scopes=scopes,
            expires_at=expires_at,
        )
        self._grants[delegation_id] = grant
        return grant

    def revoke(self, delegation_id: str) -> None:
        self._grants[delegation_id].revoke()

    def can_operate(
        self,
        parent_astra: str,
        child_instance: str,
        scope: DelegationScope,
        delegation_id: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        grant = self._grants.get(delegation_id)
        if grant is None:
            return False
        return grant.allows(parent_astra, child_instance, scope, now=now)

    def publish(
        self,
        *,
        parent_astra: str,
        child_instance: str,
        delegation_id: str,
        text: str,
        task_id: str = "",
    ) -> PublishedMessage:
        if not self.can_operate(
            parent_astra,
            child_instance,
            DelegationScope.FEISHU_WRITE,
            delegation_id,
        ):
            raise PermissionError("child has no active Feishu write delegation")
        node_id = child_instance.split("-")[1].upper()
        identity = self.roles.get(node_id, BotRoleKind.DEEPSEEK)
        return PublishedMessage(
            sender_app_id=identity.app_id,
            instance_id=child_instance,
            message_id=f"out-{len(self._seen_events) + 1}",
            text=text,
            task_id=task_id,
        )

    def _target_identity(
        self,
        message: FeishuMessage,
        *,
        local_node: str,
    ) -> BotIdentity:
        mentioned = (
            self.roles.by_app_id(message.mentioned_app_id)
            if message.mentioned_app_id
            else None
        )
        if mentioned is None:
            return self.roles.get(local_node, BotRoleKind.ASTRA)
        if mentioned.kind == BotRoleKind.DEEPSEEK:
            return self.roles.get(mentioned.node_id, BotRoleKind.ASTRA)
        return mentioned


@dataclass(frozen=True, slots=True)
class HistoryPage:
    events: list[FeishuMessage]
    next_cursor: str | None
    done: bool
    permission_gap: bool = False


@dataclass(slots=True)
class RecoveryResult:
    events: list[FeishuMessage]
    permission_gap: bool
    requires_human_baseline: bool


class HistoryRecovery:
    def __init__(
        self,
        *,
        fetch_page: Callable[[str, str | None, datetime, datetime], dict],
    ):
        self.fetch_page = fetch_page

    def recover(
        self,
        *,
        group_id: str,
        checkpoint: datetime,
        upper_bound: datetime,
    ) -> RecoveryResult:
        cursor: str | None = None
        events: list[FeishuMessage] = []
        permission_gap = False
        done = False
        for _ in range(1000):
            page = self.fetch_page(group_id, cursor, checkpoint, upper_bound)
            events.extend(page.get("events", []))
            permission_gap = permission_gap or bool(page.get("permission_gap"))
            cursor = page.get("next_cursor")
            if page.get("done"):
                done = True
                break
        return RecoveryResult(
            events=events,
            permission_gap=permission_gap,
            requires_human_baseline=permission_gap or not done,
        )
