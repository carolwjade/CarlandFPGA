import unittest
from datetime import datetime, timedelta, timezone

from fpga_mesh.protocol import (
    ChildInstance,
    DelegationScope,
    Envelope,
    HardwareOperation,
    HardwareOperationState,
    MessageKind,
    OwnershipClaim,
    ProtocolError,
    SourceKind,
    task_id_from_message,
)


class MessageProtocolTests(unittest.TestCase):
    def test_envelope_round_trip_keeps_revision_and_recipient(self):
        message = Envelope(
            message_id="msg-1",
            project_id="fpga-main",
            sender="A/Astra-A",
            recipient="B/Astra-B",
            task_id="task-1",
            task_version=4,
            sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
            kind=MessageKind.AGENT_REPORT,
            source=SourceKind.ASTRA,
            payload={"summary": "ready"},
        )

        restored = Envelope.from_json(message.to_json())

        self.assertEqual(restored.message_id, "msg-1")
        self.assertEqual(restored.recipient, "B/Astra-B")
        self.assertEqual(restored.task_version, 4)
        self.assertEqual(restored.payload, {"summary": "ready"})

    def test_task_id_is_stable_for_message_edits_but_tracks_revision(self):
        first = task_id_from_message("group-1", "om_123")
        duplicate = task_id_from_message("group-1", "om_123")
        self.assertEqual(first, duplicate)
        self.assertNotEqual(first, task_id_from_message("group-1", "om_124"))

    def test_envelope_requires_positive_task_version(self):
        with self.assertRaises(ProtocolError):
            Envelope(
                message_id="msg-1",
                project_id="fpga-main",
                sender="A/Astra-A",
                recipient="B/Astra-B",
                task_id="task-1",
                task_version=0,
                sent_at=datetime.now(timezone.utc),
                kind=MessageKind.AGENT_REPORT,
                source=SourceKind.ASTRA,
                payload={},
            )

    def test_deepseek_child_instance_must_use_max_reasoning(self):
        with self.assertRaises(ProtocolError):
            ChildInstance(
                instance_id="deepseek-a-1",
                node_id="A",
                model="deepseek-flash",
                reasoning_effort="high",
            )

    def test_deepseek_child_instance_rejects_other_models(self):
        with self.assertRaises(ProtocolError):
            ChildInstance(
                instance_id="deepseek-a-1",
                node_id="A",
                model="deepseek-v4-pro",
                reasoning_effort="max",
            )

    def test_delegation_only_allows_parent_and_scoped_actions(self):
        delegation = OwnershipClaim(
            claim_id="claim-1",
            task_id="task-1",
            owner_node="B",
            source_message_id="om_123",
            revision=1,
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(delegation.owner_node, "B")

        from fpga_mesh.protocol import Delegation

        grant = Delegation(
            delegation_id="deleg-1",
            parent_astra="B/Astra-B",
            child_instance="deepseek-b-1",
            scopes={DelegationScope.FEISHU_READ, DelegationScope.HARDWARE_SUBMIT},
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.assertTrue(grant.allows("B/Astra-B", "deepseek-b-1", DelegationScope.FEISHU_READ))
        self.assertTrue(grant.allows("B/Astra-B", "deepseek-b-1", DelegationScope.HARDWARE_SUBMIT))
        self.assertFalse(grant.allows("B/Astra-B", "deepseek-b-1", DelegationScope.GIT_WRITE))
        self.assertFalse(grant.allows("A/Astra-A", "deepseek-b-1", DelegationScope.FEISHU_READ))

    def test_hardware_operation_can_transition_to_unknown_but_not_retry_silently(self):
        operation = HardwareOperation(
            operation_id="op-1",
            task_id="task-1",
            task_version=1,
            requester="B/Astra-B",
        )
        operation.mark_unknown("service restart")
        self.assertEqual(operation.state, HardwareOperationState.UNKNOWN)
        with self.assertRaises(ProtocolError):
            operation.start()


if __name__ == "__main__":
    unittest.main()
