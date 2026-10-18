import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lark_channel.channel.config import OutboundConfig, RetryConfig
from lark_channel.channel.outbound.sender import OutboundSender, SendDriver
from lark_channel.channel.types import OutboundText

from fpga_mesh.feishu_channel import FeishuNodeService
from fpga_mesh.store import SQLiteStore


class SDKChannel:
    """Use installed SDK materialization/aggregation with an offline driver."""
    def __init__(self, responses, *, limit=3500, mode="newline"):
        self.responses = iter(responses)
        self.calls = []
        self.results = []
        config = OutboundConfig(text_chunk_limit=limit, chunk_mode=mode,
                                retry=RetryConfig(max_attempts=1))
        self.config = SimpleNamespace(outbound=config)
        def create(**kwargs):
            self.calls.append(kwargs)
            return next(self.responses)
        self.sender = OutboundSender(SendDriver(create_message=create, reply_message=create), config)

    async def send(self, to, message, opts):
        result = await self.sender.send(OutboundText(text=message["text"]),
                                        receive_id=to, uuid_=opts["uuid"])
        self.results.append(result)
        return result


def ok(message_id):
    return {"code": 0, "data": {"message_id": message_id}}


class ChunkEvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(self.tmp) / "state.sqlite"
        self.store = SQLiteStore(self.path)
        self.addCleanup(self.store.close)

    def service(self, channel):
        service = FeishuNodeService(
            node_id="A", project_id="offline-chunks", group_id="oc_fake",
            astra_app_id="cli_fake", astra_secret_file=Path(self.tmp) / "unused",
            controller=object(), store=self.store,
        )
        service.channel = channel
        service.connected = True
        return service

    async def test_sdk_missing_first_chunk_id_holds_whole_report(self):
        channel = SDKChannel([ok(None), ok("om_second")])
        service = self.service(channel)
        self.store.enqueue_group_report("operation", "x" * 3501)
        try:
            await service.flush_reports()
        except RuntimeError:
            pass
        # Characterize the actual SDK bug: a later ID masks an earlier absent ID.
        result = channel.results[0]
        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "om_second")
        self.assertIsNone(result.chunk_ids)
        self.assertEqual(self.store.group_report_delivery("operation")["delivery_state"],
                         "delivery_unknown")
        await service.flush_reports()
        self.assertEqual(len(channel.calls), 2)

    async def test_sdk_subset_chunk_ids_cannot_ack_three_chunk_report(self):
        channel = SDKChannel([ok("om_first"), ok(None), ok("om_third")])
        service = self.service(channel)
        self.store.enqueue_group_report("operation", "x" * 7001)
        try:
            await service.flush_reports()
        except RuntimeError:
            pass
        self.assertEqual(channel.results[0].chunk_ids, ["om_first", "om_third"])
        self.assertEqual(self.store.group_report_status("operation"), "pending")
        self.assertEqual(self.store.group_outbox_health()["held"], 1)

    async def test_all_chunk_ids_are_persisted_before_original_ack(self):
        channel = SDKChannel([ok("om_first"), ok("om_second"), ok("om_third")], limit=3)
        service = self.service(channel)
        self.store.enqueue_group_report("operation", "abcdefg")
        original_ack = self.store.ack_group_report
        before_ack = []
        def ack(operation_id, message_id):
            with closing(sqlite3.connect(self.path)) as db:
                before_ack.extend(db.execute("SELECT payload FROM events WHERE kind = ?",
                                              ("feishu_report_acknowledgements",)))
            original_ack(operation_id, message_id)
        with patch.object(self.store, "ack_group_report", side_effect=ack):
            await service.flush_reports()
        self.assertEqual(len(before_ack), 1)
        self.assertEqual(self.store.group_report_status("operation"), "sent")
        with closing(sqlite3.connect(self.path)) as db:
            rows = list(db.execute("SELECT payload FROM events WHERE kind = ?",
                                   ("feishu_report_acknowledgements",)))
        self.assertEqual(len(rows), 1)
        evidence = json.loads(rows[0][0])
        self.assertEqual(evidence["operation_id"], "operation")
        self.assertEqual(evidence["expected_chunks"], 3)
        self.assertEqual(evidence["message_ids"], ["om_first", "om_second", "om_third"])
        self.assertTrue(evidence["complete"])
        self.assertNotIn("abcdefg", rows[0][0])

    async def test_newline_chunk_boundaries_use_actual_sdk_count(self):
        channel = SDKChannel([ok("om_first"), ok("om_second"), ok("om_third")], limit=5)
        self.store.enqueue_group_report("operation", "abcd\nefgh\nij")
        await self.service(channel).flush_reports()
        self.assertEqual([json.loads(call["content"])["text"] for call in channel.calls],
                         ["abcd", "efgh", "ij"])
        self.assertEqual(self.store.group_report_status("operation"), "sent")

    async def test_duplicate_chunk_ids_do_not_prove_distinct_acknowledgements(self):
        channel = SDKChannel([ok("om_same"), ok("om_same")])
        self.store.enqueue_group_report("operation", "x" * 3501)
        try:
            await self.service(channel).flush_reports()
        except RuntimeError:
            pass
        self.assertEqual(self.store.group_report_delivery("operation")["delivery_state"],
                         "delivery_unknown")

    async def test_configuration_change_after_send_cannot_hide_missing_chunk_id(self):
        class ChangedConfigChannel(SDKChannel):
            async def send(self, *args):
                result = await super().send(*args)
                self.config.outbound.text_chunk_limit = 100
                return result
        channel = ChangedConfigChannel([ok(None), ok("om_second")], limit=4)
        self.store.enqueue_group_report("operation", "abcdefg")
        try:
            await self.service(channel).flush_reports()
        except RuntimeError:
            pass
        self.assertEqual(self.store.group_report_delivery("operation")["delivery_state"],
                         "delivery_unknown")


if __name__ == "__main__":
    unittest.main()
