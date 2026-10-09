import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fpga_mesh.setup_gates import (
    assess_setup, child_smoke_verified, human_roundtrip_verified,
    render_next_steps,
)


class SetupGateTests(unittest.TestCase):
    def test_child_smoke_receipt_must_match_revision_and_actual_result(self):
        result = {
            "revision": "abc", "parent_accepted": True,
            "parent_text": "CHILD_OK", "parent_effort": "low",
            "child_jobs": [{"status": "completed", "result_text": "CHILD_OK"}],
            "pool_efforts": ["max"],
        }
        self.assertTrue(child_smoke_verified(result, "abc"))
        self.assertFalse(child_smoke_verified(result, "def"))
        self.assertFalse(child_smoke_verified({**result, "pool_efforts": ["high"]}, "abc"))

    def test_human_roundtrip_requires_processed_inbound_and_sent_report(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "state.sqlite"
            with closing(sqlite3.connect(db)) as conn:
                conn.executescript("""
                    CREATE TABLE inbound (message_id TEXT, processed_at TEXT);
                    CREATE TABLE group_outbox (operation_id TEXT, sent_at TEXT);
                """)
                conn.execute("INSERT INTO inbound VALUES (?, ?)",
                             ("feishu:oc_team:om_one:1", "now"))
                conn.execute("INSERT INTO group_outbox VALUES (?, NULL)",
                             ("result:feishu:oc_team:om_one:1:1",))
                conn.commit()
            self.assertFalse(human_roundtrip_verified(db))
            with closing(sqlite3.connect(db)) as conn:
                conn.execute("UPDATE group_outbox SET sent_at = 'now'")
                conn.commit()
            self.assertTrue(human_roundtrip_verified(db))

    def complete_facts(self):
        return {
            "node": "B", "source_read": True, "github_auth": True,
            "upstream_write": True, "fork_ready": True,
            "codex_auth": True, "deepseek_key": True,
            "tailscale_ip": "100.64.0.2", "shared_secret": True,
            "peer_urls": {"A": "http://100.64.0.1:8787",
                          "C": "http://100.64.0.3:8787"},
            "peer_health": {"A": True, "C": True},
            "astra_app_id": "cli_astra_b", "astra_verified": True,
            "deepseek_app_id": "cli_deepseek_b", "deepseek_verified": True,
            "service_running": True, "human_roundtrip": True,
            "child_route": True,
        }

    def test_full_readiness_requires_real_peer_and_bot_evidence(self):
        report = assess_setup(self.complete_facts())
        self.assertTrue(report["ready"])
        self.assertEqual(report["gates"], [])
        facts = self.complete_facts()
        facts["peer_health"]["C"] = False
        facts["deepseek_verified"] = False
        facts["human_roundtrip"] = False
        report = assess_setup(facts)
        self.assertFalse(report["ready"])
        self.assertIn("peer_C", [item["code"] for item in report["gates"]])
        self.assertIn("deepseek_selftest", [item["code"] for item in report["gates"]])
        self.assertIn("human_roundtrip", [item["code"] for item in report["gates"]])

    def test_public_clone_and_fork_do_not_grant_shared_claim_write(self):
        facts = self.complete_facts()
        facts["upstream_write"] = False
        report = assess_setup(facts)
        self.assertFalse(report["ready"])
        self.assertIn("upstream_write", [item["code"] for item in report["gates"]])
        text = render_next_steps(report)
        self.assertIn("collaborator", text)
        self.assertIn("fork/PR", text)

    def test_missing_feishu_registration_provides_personal_steps(self):
        facts = self.complete_facts()
        facts["astra_app_id"] = ""
        facts["astra_verified"] = False
        facts["deepseek_verified"] = False
        report = assess_setup(facts)
        text = render_next_steps(report)
        self.assertIn("飞书", text)
        self.assertIn("实名认证", text)
        self.assertIn("FPGA/AI/DEV", text)
        self.assertIn("https://open.feishu.cn/", text)
        self.assertNotIn("secret", text.lower())


if __name__ == "__main__":
    unittest.main()
