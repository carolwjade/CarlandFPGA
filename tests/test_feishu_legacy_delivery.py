import sqlite3
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.store import SQLiteStore


class LegacyDeliveryTests(unittest.TestCase):
    def test_upgrade_holds_untracked_pending_without_replaying_or_losing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            db = sqlite3.connect(path)
            db.execute("CREATE TABLE group_outbox (operation_id TEXT PRIMARY KEY, text TEXT NOT NULL, "
                       "role TEXT NOT NULL DEFAULT 'astra', job_id TEXT, created_at TEXT NOT NULL, "
                       "sent_at TEXT, platform_message_id TEXT, cancelled_at TEXT)")
            db.executemany("INSERT INTO group_outbox VALUES (?,?,?,?,?,?,?,?)", [
                ("old-pending", "preserve original text", "astra", None, "2026-10-14T00:00:00Z", None, None, None),
                ("old-sent", "already sent", "astra", None, "2026-10-14T00:00:00Z", "2026-10-14T00:01:00Z", "om_original", None),
                ("old-cancelled", "old cancellation", "astra", None, "2026-10-14T00:00:00Z", None, None, "2026-10-14T00:02:00Z"),
            ])
            db.commit()
            db.close()
            store = SQLiteStore(path)
            try:
                self.assertEqual(store.group_report_delivery("old-pending")["delivery_state"], "delivery_unknown")
                self.assertFalse(store.group_role_ready("astra"))
                self.assertEqual(store.pending_group_reports(), [("old-pending", "preserve original text")])
                self.assertEqual(store.group_report_status("old-sent"), "sent")
                self.assertEqual(store.group_report_status("old-cancelled"), "cancelled")
                store.enqueue_group_report("new", "new original", role="deepseek")
                self.assertTrue(store.group_role_ready("deepseek"))
                store.reconcile_group_report("old-pending", evidence_sha256="a" * 64, confirmed_not_sent=True)
                self.assertTrue(store.group_role_ready("astra"))
            finally:
                store.close()
            reopened = SQLiteStore(path)
            try:
                self.assertTrue(reopened.group_role_ready("astra"))
                self.assertEqual(reopened.group_report_delivery("old-pending")["resolution"], "verified_not_sent")
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
