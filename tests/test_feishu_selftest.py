import json
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.feishu_selftest import run_self_test


class FakeAPI:
    def __init__(self):
        self.sent = []
        self.reads = 0
        self.visible = True

    def access_token(self, app_id, secret):
        assert app_id == "cli_astra_a"
        assert secret == "local-only-secret"
        return "test-token"

    def send(self, token, group_id, message, uuid):
        self.sent.append((token, group_id, message, uuid))
        return "om_selftest_1"

    def recent_messages(self, token, group_id):
        self.reads += 1
        if not self.visible:
            return []
        return [{
            "message_id": "om_selftest_1",
            "chat_id": group_id,
            "msg_type": "text",
            "body": {"content": json.dumps({"text": self.sent[0][2]})},
        }]


class FeishuSelfTestTests(unittest.TestCase):
    def test_sends_once_and_reads_back_exact_message_before_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = root / "secret.txt"
            secret.write_text("local-only-secret", encoding="utf-8")
            state = root / "selftest.json"
            api = FakeAPI()
            result = run_self_test(
                node="A", role="astra", app_id="cli_astra_a",
                secret_file=secret, group_id="oc_team", state_file=state,
                api=api, delays=(),
            )
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["message_id"], "om_selftest_1")
            self.assertEqual(len(api.sent), 1)
            self.assertEqual(api.reads, 1)
            self.assertNotIn("local-only-secret", state.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(state.read_text(encoding="utf-8"))["verified"])
            again = run_self_test(
                node="A", role="astra", app_id="cli_astra_a",
                secret_file=secret, group_id="oc_team", state_file=state,
                api=api, delays=(),
            )
            self.assertTrue(again["reused"])
            self.assertEqual(len(api.sent), 1)
            self.assertEqual(api.reads, 1)

    def test_failed_read_keeps_send_receipt_and_retry_does_not_post_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = root / "secret.txt"
            secret.write_text("local-only-secret", encoding="utf-8")
            state = root / "selftest.json"
            api = FakeAPI()
            api.visible = False
            args = dict(node="A", role="astra", app_id="cli_astra_a",
                        secret_file=secret, group_id="oc_team", state_file=state,
                        api=api, delays=())
            with self.assertRaisesRegex(RuntimeError, "read-back"):
                run_self_test(**args)
            self.assertEqual(len(api.sent), 1)
            self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["message_id"],
                             "om_selftest_1")
            api.visible = True
            result = run_self_test(**args)
            self.assertEqual(result["status"], "verified")
            self.assertEqual(len(api.sent), 1)
            self.assertEqual(api.reads, 2)

    def test_deepseek_registration_allows_one_time_read_without_subscription(self):
        from fpga_mesh.feishu_registration import registration_addons

        child = registration_addons("deepseek")
        self.assertNotIn("events", child)
        self.assertEqual(set(child["scopes"]["tenant"]), {
            "im:message:send_as_bot", "im:message:readonly", "im:message.group_msg",
        })


if __name__ == "__main__":
    unittest.main()
