import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore
from fpga_mesh.tasks import TaskRecord, TaskState, VersionConflict


def make_message(
    message_id: str,
    *,
    group_id: str = "group-1",
    platform_message_id: str = "om_123",
    task_version: int = 1,
) -> Envelope:
    return Envelope(
        message_id=message_id,
        project_id="fpga-main",
        sender="human-1",
        recipient="A/Astra-A",
        task_id="task-1",
        task_version=task_version,
        sent_at=datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        kind=MessageKind.HUMAN_INSTRUCTION,
        source=SourceKind.HUMAN,
        payload={"text": "run the test"},
        platform_group_id=group_id,
        platform_message_id=platform_message_id,
    )


class SQLiteStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "state.sqlite"
        self.store = SQLiteStore(self.db_path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_inbound_dedupe_uses_group_and_message_id_not_event_id(self):
        first = make_message("internal-1")
        duplicate = replace(
            first,
            message_id="internal-2",
            platform_event_id="event-2",
        )

        self.assertTrue(self.store.accept_inbound(first))
        self.assertFalse(self.store.accept_inbound(duplicate))
        self.assertEqual(len(self.store.pending_inbound()), 1)

    def test_edited_feishu_message_is_new_revision_but_duplicate_edit_is_not(self):
        first = make_message("first")
        edited = replace(first, message_id="edited", task_version=2, revision=2)
        duplicate_edit = replace(edited, message_id="edited-redelivery")
        self.assertTrue(self.store.accept_inbound(first))
        self.assertTrue(self.store.accept_inbound(edited))
        self.assertFalse(self.store.accept_inbound(duplicate_edit))
        self.assertEqual([m.message.revision for m in self.store.pending_inbound()], [1, 2])

    def test_unprocessed_inbound_survives_reopen(self):
        self.store.accept_inbound(make_message("internal-1"))
        self.store.close()

        reopened = SQLiteStore(self.db_path)
        self.store = reopened
        pending = reopened.pending_inbound()
        self.assertEqual(
            [stored.message.message_id for stored in pending],
            ["internal-1"],
        )

    def test_group_report_outbox_survives_reopen_and_is_idempotent(self):
        self.assertTrue(self.store.enqueue_group_report("op-1", "finished"))
        self.assertFalse(self.store.enqueue_group_report("op-1", "finished"))
        self.store.close()
        self.store = SQLiteStore(self.db_path)
        self.assertEqual(self.store.pending_group_reports(), [("op-1", "finished")])
        self.store.ack_group_report("op-1", "om_sent")
        self.assertEqual(self.store.pending_group_reports(), [])

    def test_group_report_can_retain_shared_deepseek_sender_identity(self):
        self.store.enqueue_group_report("child-op", "child result", role="deepseek")
        self.assertEqual(
            self.store.pending_group_messages(),
            [("child-op", "child result", "deepseek")],
        )

    def test_outbox_retry_and_ack_are_persistent(self):
        message = make_message("internal-1")
        self.store.enqueue_outbound(message, peer_id="B")
        item = self.store.next_outbound()
        self.assertIsNotNone(item)
        self.store.mark_outbound_failed(message.message_id, "offline", retry_at=None)
        self.store.close()

        reopened = SQLiteStore(self.db_path)
        self.store = reopened
        retry = reopened.next_outbound()
        self.assertEqual(retry.message.message_id, "internal-1")
        self.assertEqual(retry.attempts, 2)
        reopened.ack_outbound(message.message_id)
        self.assertEqual(reopened.pending_outbound(), [])

    def test_outbox_rejects_cross_peer_message_id_collision(self):
        first = make_message("shared-op")
        self.assertTrue(self.store.enqueue_outbound(first, peer_id="B"))
        with self.assertRaisesRegex(ValueError, "different peer"):
            self.store.enqueue_outbound(first, peer_id="C")
        self.assertEqual(len(self.store.pending_outbound()), 1)

    def test_task_update_rejects_stale_version(self):
        task = TaskRecord(
            task_id="task-1",
            version=1,
            owner_node="A",
            objective="first",
            state=TaskState.NEW,
        )
        self.store.put_task(task)
        updated = TaskRecord(
            task_id="task-1",
            version=2,
            owner_node="A",
            objective="second",
            state=TaskState.WORKING,
        )
        self.store.put_task(updated, expected_version=1)
        self.assertEqual(self.store.get_task("task-1").version, 2)

        stale = TaskRecord(
            task_id="task-1",
            version=2,
            owner_node="A",
            objective="stale",
            state=TaskState.WAITING_HUMAN,
        )
        with self.assertRaises(VersionConflict):
            self.store.put_task(stale, expected_version=1)


if __name__ == "__main__":
    unittest.main()
