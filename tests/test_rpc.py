import asyncio
import json
import unittest

from fpga_mesh.rpc import InMemoryTransport, JsonRpcError, JsonRpcSession


class JsonRpcSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_request_matches_response_even_when_replies_arrive_out_of_order(self):
        transport = InMemoryTransport()
        session = JsonRpcSession(transport)
        first = asyncio.create_task(session.request("model/list", {"limit": 1}))
        second = asyncio.create_task(session.request("account/read", {}))
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        first_id = json.loads(await transport.next_client_message())["id"]
        second_id = json.loads(await transport.next_client_message())["id"]
        await transport.inject_server_message(
            json.dumps({"jsonrpc": "2.0", "id": second_id, "result": {"ok": 2}})
        )
        await transport.inject_server_message(
            json.dumps({"jsonrpc": "2.0", "id": first_id, "result": {"ok": 1}})
        )

        self.assertEqual(await first, {"ok": 1})
        self.assertEqual(await second, {"ok": 2})

    async def test_notifications_are_queued_without_blocking_requests(self):
        transport = InMemoryTransport()
        session = JsonRpcSession(transport)
        await transport.inject_server_message(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "account/rateLimits/updated",
                    "params": {"usedPercent": 10},
                }
            )
        )
        await asyncio.sleep(0)

        notification = await session.next_notification()
        self.assertEqual(notification.method, "account/rateLimits/updated")
        self.assertEqual(notification.params["usedPercent"], 10)

    async def test_server_error_raises_with_method_context(self):
        transport = InMemoryTransport()
        session = JsonRpcSession(transport)
        pending = asyncio.create_task(session.request("thread/start", {}))
        await asyncio.sleep(0)
        request = json.loads(await transport.next_client_message())
        await transport.inject_server_message(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {"code": -32602, "message": "invalid params"},
                }
            )
        )
        with self.assertRaises(JsonRpcError):
            await pending


if __name__ == "__main__":
    unittest.main()
