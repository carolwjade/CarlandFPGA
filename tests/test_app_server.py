import unittest

from fpga_mesh.app_server import AppServerClient


class FakeSession:
    def __init__(self):
        self.requests = []

    async def request(self, method, params=None):
        self.requests.append((method, params or {}))
        return {"ok": method}

    async def notify(self, method, params=None):
        self.requests.append((method, params or {}))

    async def close(self):
        self.requests.append(("close", {}))


class AppServerClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = FakeSession()
        self.client = AppServerClient(self.session, client_version="0.159.0")

    async def test_initialize_declares_client_and_experimental_capability(self):
        await self.client.initialize()
        method, params = self.session.requests[0]
        self.assertEqual(method, "initialize")
        self.assertEqual(params["clientInfo"]["name"], "fpga-mesh")
        self.assertEqual(params["clientInfo"]["version"], "0.159.0")
        self.assertTrue(params["capabilities"]["experimentalApi"])

    async def test_thread_and_turn_keep_model_provider_and_max_effort(self):
        await self.client.thread_start(
            cwd="C:/workspace",
            model="deepseek-flash",
            model_provider="deepseek",
        )
        await self.client.turn_start(
            thread_id="thread-1",
            text="inspect",
            model="deepseek-flash",
            effort="max",
        )

        start_method, start_params = self.session.requests[0]
        turn_method, turn_params = self.session.requests[1]
        self.assertEqual(start_method, "thread/start")
        self.assertEqual(start_params["model"], "deepseek-flash")
        self.assertEqual(start_params["modelProvider"], "deepseek")
        self.assertEqual(turn_method, "turn/start")
        self.assertEqual(turn_params["model"], "deepseek-flash")
        self.assertEqual(turn_params["effort"], "max")
        self.assertEqual(turn_params["input"], [{"type": "text", "text": "inspect"}])

    async def test_rate_limit_read_uses_the_official_method_and_empty_params(self):
        await self.client.account_rate_limits()
        self.assertEqual(
            self.session.requests[0],
            ("account/rateLimits/read", {}),
        )


if __name__ == "__main__":
    unittest.main()
