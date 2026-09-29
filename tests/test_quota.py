import unittest
from datetime import datetime, timezone

from fpga_mesh.quota import QuotaMonitor


def response(
    used: int,
    *,
    reset: int = 1800000000,
    allowed: bool | None = True,
    spend_control: bool | None = False,
):
    return {
        "accountId": "acct-1",
        "ordinaryUsageAllowed": allowed,
        "rateLimits": {
            "limitId": "codex",
            "limitName": "Codex",
            "primary": {
                "usedPercent": used,
                "windowDurationMins": 300,
                "resetsAt": reset,
            },
            "secondary": None,
            "spendControlReached": spend_control,
        },
        "rateLimitsByLimitId": {
            "codex": {
                "limitId": "codex",
                "limitName": "Codex",
                "primary": {
                    "usedPercent": used,
                    "windowDurationMins": 300,
                    "resetsAt": reset,
                },
                "secondary": None,
                "spendControlReached": spend_control,
            }
        },
    }


class QuotaMonitorTests(unittest.TestCase):
    def setUp(self):
        self.monitor = QuotaMonitor()
        self.now = datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc)

    def test_crossing_twenty_and_ten_emits_each_alert_once(self):
        first = self.monitor.observe(response(80), node_id="A", now=self.now)
        self.assertEqual([alert.threshold for alert in first.alerts], [20])

        duplicate = self.monitor.observe(response(80), node_id="A", now=self.now)
        self.assertEqual(duplicate.alerts, [])

        second = self.monitor.observe(response(91), node_id="A", now=self.now)
        self.assertEqual([alert.threshold for alert in second.alerts], [10])

    def test_unknown_quota_is_not_reported_as_recovered(self):
        state = self.monitor.observe(
            {"accountId": "acct-1", "rateLimits": None},
            node_id="A",
            now=self.now,
        )
        self.assertTrue(state.unknown)
        self.assertFalse(state.blocked)
        self.assertEqual(state.alerts, [])

    def test_backend_false_or_spend_control_blocks_but_none_does_not_claim_recovery(self):
        blocked = self.monitor.observe(
            response(0, allowed=False),
            node_id="A",
            now=self.now,
        )
        self.assertTrue(blocked.blocked)

        unknown = self.monitor.observe(
            response(0, allowed=None),
            node_id="A",
            now=self.now,
        )
        self.assertTrue(unknown.unknown)
        self.assertFalse(unknown.blocked)

        spend = self.monitor.observe(
            response(0, spend_control=True),
            node_id="A",
            now=self.now,
        )
        self.assertTrue(spend.blocked)

    def test_new_reset_window_can_alert_again(self):
        first = self.monitor.observe(
            response(80, reset=1800000000),
            node_id="A",
            now=self.now,
        )
        second = self.monitor.observe(
            response(80, reset=1800003600),
            node_id="A",
            now=self.now,
        )
        self.assertEqual([alert.threshold for alert in first.alerts], [20])
        self.assertEqual([alert.threshold for alert in second.alerts], [20])


if __name__ == "__main__":
    unittest.main()
