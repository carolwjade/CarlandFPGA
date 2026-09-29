import unittest

from fpga_mesh.deepseek import DeepSeekBalanceClient


class DeepSeekBalanceClientTests(unittest.TestCase):
    def test_balance_query_uses_user_balance_endpoint_and_bearer_header(self):
        calls = []

        def fake_request(method, url, headers):
            calls.append((method, url, headers))
            return {
                "is_available": True,
                "balance_infos": [
                    {
                        "currency": "CNY",
                        "total_balance": "110.00",
                        "granted_balance": "10.00",
                        "topped_up_balance": "100.00",
                    }
                ],
            }

        client = DeepSeekBalanceClient(
            api_key="test-key",
            request_json=fake_request,
        )
        result = client.query()

        self.assertTrue(result["is_available"])
        self.assertEqual(calls[0][0], "GET")
        self.assertTrue(calls[0][1].endswith("/user/balance"))
        self.assertEqual(calls[0][2]["Authorization"], "Bearer test-key")

    def test_safe_summary_does_not_include_balances(self):
        client = DeepSeekBalanceClient(
            api_key="test-key",
            request_json=lambda method, url, headers: {
                "is_available": True,
                "balance_infos": [
                    {"currency": "CNY", "total_balance": "110.00"}
                ],
            },
        )
        summary = client.safe_summary()
        self.assertEqual(summary["currencies"], ["CNY"])
        self.assertNotIn("110.00", str(summary))


if __name__ == "__main__":
    unittest.main()
