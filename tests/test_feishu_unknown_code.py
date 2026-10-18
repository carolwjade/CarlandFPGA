import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lark_channel.channel.errors import FeishuChannelErrorCode, SendError
from lark_channel.channel.types import SendResult
from fpga_mesh.feishu_channel import FeishuNodeService
from fpga_mesh.store import SQLiteStore


class UnknownCodeTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_error_does_not_prove_message_was_not_created(self):
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        store = SQLiteStore(Path(tmp) / "db.sqlite")
        self.addCleanup(store.close)
        store.enqueue_group_report("operation", "one bounded message")
        calls = []
        async def send(*args):
            calls.append(args)
            return SendResult.fail(SendError(
                code=FeishuChannelErrorCode.UNKNOWN, raw_code=50001, retryable=True,
            ))
        service = FeishuNodeService(
            node_id="A", project_id="fpga-main", group_id="oc_team",
            astra_app_id="cli_a", astra_secret_file=Path(tmp) / "unused",
            controller=object(), store=store,
        )
        service.channel = SimpleNamespace(send=send)
        service.connected = True
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(store.group_report_delivery("operation")["delivery_state"], "delivery_unknown")
        self.assertEqual(store.group_report_status("operation"), "pending")
        await service.flush_reports()
        self.assertEqual(len(calls), 1)
