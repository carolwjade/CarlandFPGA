import unittest
from datetime import datetime, timezone

from fpga_mesh.coordination import (
    ClaimRecord,
    MemoryClaimStore,
    OwnershipCoordinator,
    RemoteReceiptLost,
    RemoteUnavailable,
)


def claim(owner: str, claim_id: str = "claim-1") -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        task_id="task-1",
        owner_node=owner,
        source_message_id="om_123",
        revision=1,
        created_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
    )


class OwnershipCoordinatorTests(unittest.TestCase):
    def test_first_remote_claim_wins_and_later_conflict_does_not_execute(self):
        remote = MemoryClaimStore()
        coordinator_a = OwnershipCoordinator()
        coordinator_b = OwnershipCoordinator()

        first = coordinator_a.claim(claim("A", "claim-a"), remote)
        second = coordinator_b.claim(claim("B", "claim-b"), remote)

        self.assertTrue(first.effective)
        self.assertEqual(first.owner_node, "A")
        self.assertFalse(second.effective)
        self.assertEqual(second.owner_node, "A")
        self.assertEqual(len(remote.records), 1)

    def test_receipt_loss_queries_remote_before_claiming_failure(self):
        remote = MemoryClaimStore(lose_receipt_once=True)
        coordinator = OwnershipCoordinator()

        result = coordinator.claim(claim("B"), remote)

        self.assertTrue(result.effective)
        self.assertEqual(result.owner_node, "B")
        self.assertEqual(result.attempts, 1)

    def test_remote_unavailable_leaves_claim_pending_and_retryable(self):
        remote = MemoryClaimStore()
        remote.available = False
        coordinator = OwnershipCoordinator()
        pending = coordinator.claim(claim("C"), remote)
        self.assertFalse(pending.effective)
        self.assertTrue(pending.pending)

        remote.available = True
        retried = coordinator.claim(claim("C"), remote)
        self.assertTrue(retried.effective)
        self.assertEqual(retried.owner_node, "C")

    def test_receipt_loss_with_other_owner_is_authoritative(self):
        remote = MemoryClaimStore()
        remote.records["task-1"] = claim("A", "claim-a").to_dict()
        remote.lose_receipt_once = True
        result = OwnershipCoordinator().claim(claim("B", "claim-b"), remote)
        self.assertFalse(result.effective)
        self.assertEqual(result.owner_node, "A")


if __name__ == "__main__":
    unittest.main()
