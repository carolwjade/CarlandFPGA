import unittest
from datetime import datetime, timedelta, timezone

from fpga_mesh.feishu import (
    BotIdentity,
    BotRoleKind,
    FeishuMessage,
    HistoryRecovery,
    HumanMessageRouter,
    RoleRegistry,
)
from fpga_mesh.protocol import DelegationScope


def registry() -> RoleRegistry:
    identities = []
    for node in ("A", "B", "C"):
        identities.append(
            BotIdentity(
                node_id=node,
                kind=BotRoleKind.ASTRA,
                app_id=f"cli_astra_{node}",
                app_secret_ref=f"secret://feishu/{node}/astra",
                bot_id=f"bot_astra_{node}",
            )
        )
        identities.append(
            BotIdentity(
                node_id=node,
                kind=BotRoleKind.DEEPSEEK,
                app_id=f"cli_deepseek_{node}",
                app_secret_ref=f"secret://feishu/{node}/deepseek",
                bot_id=f"bot_deepseek_{node}",
            )
        )
    return RoleRegistry(identities)


def human_message(
    message_id: str,
    text: str,
    *,
    mention_app_id: str = "cli_astra_A",
    revision: int = 1,
    event_id: str | None = None,
    sender_type: str = "user",
) -> FeishuMessage:
    return FeishuMessage(
        event_id=event_id or f"event-{message_id}",
        group_id="group-1",
        message_id=message_id,
        sender_id="ou_human_1" if sender_type == "user" else "bot_sender",
        sender_type=sender_type,
        text=text,
        revision=revision,
        mentioned_app_id=mention_app_id,
        created_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
    )


class RoleRegistryTests(unittest.TestCase):
    def test_fixed_six_roles_and_only_astra_apps_subscribe(self):
        reg = registry()
        self.assertEqual(len(reg.identities), 6)
        self.assertEqual(
            [item.app_id for item in reg.subscribed_apps()],
            ["cli_astra_A", "cli_astra_B", "cli_astra_C"],
        )
        self.assertFalse(reg.is_subscribed("cli_deepseek_A"))


class HumanMessageRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = HumanMessageRouter(registry())

    def test_duplicate_event_is_ignored_and_edit_keeps_task_identity(self):
        first = self.router.ingest(human_message("om_123", "work"), local_node="A")
        duplicate = self.router.ingest(human_message("om_123", "work"), local_node="A")
        edited = self.router.ingest(
            human_message("om_123", "work changed", revision=2),
            local_node="A",
        )

        self.assertEqual(first.action, "dispatch")
        self.assertEqual(duplicate.action, "duplicate")
        self.assertEqual(edited.action, "revision")
        self.assertEqual(edited.task_id, first.task_id)
        self.assertEqual(edited.task_version, 2)

    def test_bot_and_attachment_like_messages_are_evidence_not_instructions(self):
        decision = self.router.ingest(
            human_message("om_bot", "assistant output", sender_type="bot"),
            local_node="A",
        )
        self.assertEqual(decision.action, "evidence")
        self.assertIsNone(decision.task_id)

    def test_mentioning_deepseek_routes_to_astra_and_does_not_wake_child(self):
        decision = self.router.ingest(
            human_message("om_deep", "child tasks", mention_app_id="cli_deepseek_B"),
            local_node="A",
        )
        self.assertEqual(decision.action, "dispatch")
        self.assertEqual(decision.target_app_id, "cli_astra_B")
        self.assertEqual(decision.child_wakeups, [])

    def test_child_group_io_requires_an_unexpired_delegation(self):
        grant = self.router.grant(
            parent_astra="A/Astra-A",
            child_instance="deepseek-a-1",
            scopes={DelegationScope.FEISHU_READ},
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        self.assertTrue(
            self.router.can_operate(
                "A/Astra-A",
                "deepseek-a-1",
                DelegationScope.FEISHU_READ,
                grant.delegation_id,
            )
        )
        self.assertFalse(
            self.router.can_operate(
                "A/Astra-A",
                "deepseek-a-1",
                DelegationScope.FEISHU_WRITE,
                grant.delegation_id,
            )
        )
        # The parent can revoke without waking a child.
        self.router.revoke(grant.delegation_id)
        self.assertFalse(
            self.router.can_operate(
                "A/Astra-A",
                "deepseek-a-1",
                DelegationScope.FEISHU_READ,
                grant.delegation_id,
            )
        )

    def test_child_publish_uses_shared_deepseek_identity(self):
        grant = self.router.grant(
            parent_astra="A/Astra-A",
            child_instance="deepseek-a-1",
            scopes={DelegationScope.FEISHU_WRITE},
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        published = self.router.publish(
            parent_astra="A/Astra-A",
            child_instance="deepseek-a-1",
            delegation_id=grant.delegation_id,
            text="child result",
        )
        self.assertEqual(published.sender_app_id, "cli_deepseek_A")
        self.assertEqual(published.instance_id, "deepseek-a-1")


class HistoryRecoveryTests(unittest.TestCase):
    def test_recovery_includes_root_topics_replies_edits_and_reports_permission_gap(self):
        root = human_message("om_root", "old task")
        reply = human_message("om_reply", "new constraint", revision=2)
        pages = [
            {
                "events": [root],
                "next_cursor": "cursor-2",
                "done": False,
                "permission_gap": False,
            },
            {
                "events": [reply],
                "next_cursor": None,
                "done": True,
                "permission_gap": True,
            },
        ]

        def fetch_page(group_id, cursor, start, end):
            return pages.pop(0)

        recovery = HistoryRecovery(fetch_page=fetch_page)
        result = recovery.recover(
            group_id="group-1",
            checkpoint=datetime(2026, 9, 29, tzinfo=timezone.utc),
            upper_bound=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(
            [event.message_id for event in result.events],
            ["om_root", "om_reply"],
        )
        self.assertTrue(result.permission_gap)
        self.assertTrue(result.requires_human_baseline)


if __name__ == "__main__":
    unittest.main()
