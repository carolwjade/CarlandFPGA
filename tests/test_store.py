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
