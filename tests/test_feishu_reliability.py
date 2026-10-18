import asyncio
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lark_channel.channel.errors import FeishuChannelErrorCode, SendError
from lark_channel.channel.config import OutboundConfig
from lark_channel.channel.types import SendResult
from lark_channel.core.exception import ObtainAccessTokenException

from fpga_mesh.feishu_channel import FeishuAppSender, FeishuNodeService
from fpga_mesh.runtime import NodeConfig, NodeRuntime
from fpga_mesh.store import SQLiteStore


class Channel:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def send(self, to, message, opts=None):
        self.calls.append((to, message, opts))
        return self.result


def token_denial():
    # SDK _create catches ObtainAccessTokenException and returns this shape.
    return SendResult.fail(SendError(
        code=FeishuChannelErrorCode.UNKNOWN, retryable=True,
        hint="obtain self tenant access token failed, code: 21001, msg: SECRET payload",
    ))


class FeishuReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = SQLiteStore(self.root / "state.sqlite")
        self.addCleanup(lambda: self.store.close())
        self.now = datetime(2026, 10, 17, tzinfo=timezone.utc)
        self.clock = patch("fpga_mesh.store._utc_now", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def service(self, channel, **kwargs):
        service = FeishuNodeService(
            node_id="A", project_id="fpga-main", group_id="oc_team",
            astra_app_id="cli_astra_a", astra_secret_file=self.root / "unused.txt",
            controller=object(), store=self.store, retry_seconds=30, **kwargs,
        )
        service.channel = channel
        service.connected = True
        return service

    async def test_token_denial_stops_role_but_delivers_other_role(self):
        child = SimpleNamespace(send=None)
        async def send(group_id, text, operation_id):
            return "om_child"
        child.send = send
        channel = Channel(token_denial())
        service = self.service(channel, deepseek_sender=child)
        self.store.enqueue_group_report("a-1", "first")
        self.store.enqueue_group_report("a-2", "second")
        self.store.enqueue_group_report("d-1", "child", role="deepseek")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(len(channel.calls), 1)
        self.assertEqual(self.store.group_report_status("d-1"), "sent")
        state = self.store.group_report_delivery("a-1")
        self.assertEqual(state["attempts"], 1)
        self.assertEqual(state["last_error"], "access_token_error:21001")
        self.assertEqual(state["last_attempt_at"], "2026-10-17T00:00:00Z")
        self.assertEqual(state["next_attempt_at"], "2026-10-17T00:00:30Z")
        self.assertEqual(self.store.group_report_delivery("a-2")["attempts"], 0)
        self.assertNotIn("SECRET", json.dumps(self.store.group_outbox_health()))

    async def test_restart_and_new_notification_cannot_bypass_role_backoff(self):
        channel = Channel(token_denial())
        self.store.enqueue_group_report("a-1", "first")
        with self.assertRaises(RuntimeError):
            await self.service(channel).flush_reports()
        self.store.close()
        self.store = SQLiteStore(self.root / "state.sqlite")
        self.store.enqueue_group_report("a-2", "new arrival")
        service = self.service(channel)
        task = asyncio.create_task(service._run_outbox())
        try:
            service.notify_report()
            await asyncio.sleep(0.01)
            service.notify_report()
            await asyncio.sleep(0.01)
            self.assertEqual(len(channel.calls), 1)
            self.assertEqual(service.last_error, "access_token_error:21001")
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    async def test_retry_success_clears_error_and_keeps_original_uuid_and_order(self):
        channel = Channel(token_denial())
        service = self.service(channel)
        self.store.enqueue_group_report("a-1", "first")
        self.store.enqueue_group_report("a-2", "second")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.now += timedelta(seconds=30)
        channel.result = SendResult.ok("om_sent")
        await service.flush_reports()
        self.assertEqual([call[1]["text"] for call in channel.calls],
                         ["first", "first", "second"])
        self.assertEqual(channel.calls[0][2], channel.calls[1][2])
        state = self.store.group_report_delivery("a-1")
        self.assertEqual(state["attempts"], 2)
        self.assertIsNone(state["last_error"])
        self.assertIsNone(state["next_attempt_at"])
        self.assertIsNone(service.last_error)
        self.assertEqual(self.store.group_outbox_health()["pending"], 0)

    async def test_successful_manual_flush_clears_background_failure_health(self):
        channel = Channel(token_denial())
        service = self.service(channel)
        self.store.enqueue_group_report("a-1", "first")
        task = asyncio.create_task(service._run_outbox())
        try:
            await asyncio.sleep(0.01)
            self.assertEqual(service.last_error, "access_token_error:21001")
            self.now += timedelta(seconds=30)
            channel.result = SendResult.ok("om_sent")
            await service.flush_reports()
            self.assertIsNone(service.last_error)
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    async def test_empty_astra_id_never_acknowledges_or_advances_same_role(self):
        service = self.service(Channel(SendResult.ok(None)))
        self.store.enqueue_group_report("a-1", "first")
        self.store.enqueue_group_report("a-2", "second")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(self.store.group_report_status("a-1"), "pending")
        self.assertEqual(self.store.group_report_delivery("a-1")["last_error"],
                         "delivery_unknown:missing_message_id")
        self.assertEqual(self.store.group_report_delivery("a-2")["attempts"], 0)

    async def test_empty_child_id_never_acknowledges(self):
        async def send(*args):
            return "   "
        service = self.service(Channel(SendResult.ok("om_astra")),
                               deepseek_sender=SimpleNamespace(send=send))
        self.store.enqueue_group_report("d-1", "child", role="deepseek")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(self.store.group_report_status("d-1"), "pending")

    async def test_missing_id_holds_role_across_restart_until_evidenced_reconcile(self):
        channel = Channel(SendResult.ok(None))
        self.store.enqueue_group_report("a-1", "first")
        with self.assertRaises(RuntimeError):
            await self.service(channel).flush_reports()
        state = self.store.group_report_delivery("a-1")
        self.assertEqual(state["delivery_state"], "delivery_unknown")
        self.assertEqual(state["last_error"], "delivery_unknown:missing_message_id")
        self.assertIsNone(state["next_attempt_at"])
        self.store.close()
        self.store = SQLiteStore(self.root / "state.sqlite")
        self.now += timedelta(days=2)
        self.store.enqueue_group_report("a-2", "new arrival")
        service = self.service(channel)
        await service.flush_reports()
        self.assertEqual(len(channel.calls), 1)
        self.assertEqual(self.store.group_outbox_health()["held"], 1)
        with self.assertRaises(ValueError):
            self.store.ack_group_report("a-1", "om_unverified")
        await service.reconcile_report("a-1", evidence_sha256="a" * 64,
                                       platform_message_id="om_verified")
        self.assertEqual(self.store.group_report_status("a-1"), "sent")
        self.assertEqual(self.store.group_report_delivery("a-1")["reconciliation_sha256"],
                         "a" * 64)

    async def test_transport_exception_holds_without_replaying_and_other_role_runs(self):
        class UncertainChannel(Channel):
            async def send(self, *args):
                self.calls.append(args)
                raise TimeoutError("SECRET request may already be delivered")
        channel = UncertainChannel(None)
        async def child_send(*args):
            return "om_child"
        self.store.enqueue_group_report("a-1", "first")
        self.store.enqueue_group_report("d-1", "child", role="deepseek")
        service = self.service(channel, deepseek_sender=SimpleNamespace(send=child_send))
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.now += timedelta(days=2)
        await service.flush_reports()
        self.assertEqual(len(channel.calls), 1)
        self.assertEqual(self.store.group_report_status("d-1"), "sent")
        self.assertEqual(service.last_error, "delivery_unknown:TimeoutError")

    async def test_interrupted_inflight_becomes_durable_hold_after_reopen(self):
        self.store.enqueue_group_report("a-1", "first")
        self.store.attempt_group_report("a-1")
        self.assertEqual(self.store.group_report_delivery("a-1")["delivery_state"], "inflight")
        self.store.close()
        self.store = SQLiteStore(self.root / "state.sqlite")
        channel = Channel(SendResult.ok("om_sent"))
        await self.service(channel).flush_reports()
        self.assertEqual(channel.calls, [])
        state = self.store.group_report_delivery("a-1")
        self.assertEqual(state["delivery_state"], "delivery_unknown")
        self.assertEqual(state["last_error"], "delivery_unknown:interrupted_attempt")

    async def test_reconcile_release_requires_evidence_and_explicit_not_sent(self):
        self.store.enqueue_group_report("a-1", "first")
        service = self.service(Channel(SendResult.ok(None)))
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        for kwargs in ({"evidence_sha256": ""},
                       {"evidence_sha256": "a" * 64},
                       {"evidence_sha256": "a" * 64, "confirmed_not_sent": True,
                        "platform_message_id": "om_conflict"}):
            with self.assertRaises(ValueError):
                await service.reconcile_report("a-1", **kwargs)
        await service.reconcile_report("a-1", evidence_sha256="b" * 64,
                                       confirmed_not_sent=True)
        service.channel.result = SendResult.ok("om_sent")
        await service.flush_reports()
        self.assertEqual(self.store.group_report_status("a-1"), "sent")
        self.assertEqual(self.store.group_report_delivery("a-1")["attempts"], 2)

    async def test_long_report_api_failure_cannot_prove_prior_chunks_unsent(self):
        result = SendResult.fail(SendError(
            code=FeishuChannelErrorCode.PERMISSION_DENIED, retryable=False, raw_code=230003))
        channel = Channel(result)
        self.store.enqueue_group_report("a-1", "x" * 3501)
        service = self.service(channel)
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.now += timedelta(days=2)
        await service.flush_reports()
        self.assertEqual(len(channel.calls), 1)
        self.assertEqual(service.last_error, "delivery_unknown:permission_denied:230003")

    async def test_unstructured_sdk_hint_is_never_treated_as_proof_of_rejection(self):
        result = SendResult.fail(SendError(
            code=FeishuChannelErrorCode.UNKNOWN, retryable=True,
            hint="SECRET unrelated 21001 may have been sent"))
        channel = Channel(result)
        self.store.enqueue_group_report("a-1", "first")
        service = self.service(channel)
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.now += timedelta(days=2)
        await service.flush_reports()
        self.assertEqual(len(channel.calls), 1)
        self.assertEqual(service.last_error, "delivery_unknown:unknown")

    async def test_default_sdk_channel_disables_internal_retries(self):
        class StartupChannel:
            def on(self, *args):
                pass
            async def connect_until_ready(self, **kwargs):
                pass
            async def disconnect(self):
                pass
        secret = self.root / "astra.txt"
        secret.write_text("test-secret", encoding="utf-8")
        configs = []
        def channel_factory(**kwargs):
            configs.append(kwargs.get("outbound", OutboundConfig()))
            return StartupChannel()
        service = FeishuNodeService(
            node_id="A", project_id="fpga-main", group_id="oc_team",
            astra_app_id="cli_astra_a", astra_secret_file=secret, controller=object(),
        )
        with patch("lark_channel.FeishuChannel", side_effect=channel_factory):
            await service.start()
        try:
            self.assertEqual(configs[0].retry.max_attempts, 1)
        finally:
            await service.stop()

    async def test_attempt_is_durable_before_external_send_begins(self):
        store = self.store
        class InspectingChannel(Channel):
            async def send(self, *args):
                state = store.group_report_delivery("a-1")
                self_observed.append((state["attempts"], state["delivery_state"]))
                return SendResult.ok("om_sent")
        self_observed = []
        self.store.enqueue_group_report("a-1", "first")
        await self.service(InspectingChannel(None)).flush_reports()
        self.assertEqual(self_observed, [(1, "inflight")])

    async def test_child_api_denial_retries_after_backoff_without_blocking_astra(self):
        secret = self.root / "child.txt"
        secret.write_text("test-secret", encoding="utf-8")
        rejected = True
        def create(request):
            return SimpleNamespace(success=lambda: not rejected, code=21001,
                                   data=SimpleNamespace(message_id="om_child"))
        client = SimpleNamespace(im=SimpleNamespace(
            v1=SimpleNamespace(message=SimpleNamespace(create=create))))
        sender = FeishuAppSender(app_id="cli_child", secret_file=secret,
                                 client_factory=lambda *args: client)
        self.store.enqueue_group_report("d-1", "first child", role="deepseek")
        self.store.enqueue_group_report("d-2", "second child", role="deepseek")
        self.store.enqueue_group_report("a-1", "astra")
        service = self.service(Channel(SendResult.ok("om_astra")), deepseek_sender=sender)
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(self.store.group_report_delivery("d-1")["last_error"], "access_policy:21001")
        self.assertEqual(self.store.group_report_delivery("d-2")["attempts"], 0)
        self.assertEqual(self.store.group_report_status("a-1"), "sent")
        await service.flush_reports()
        self.assertEqual(self.store.group_report_delivery("d-1")["attempts"], 1)
        rejected = False
        self.now += timedelta(seconds=30)
        await service.flush_reports()
        self.assertEqual(self.store.group_report_status("d-1"), "sent")
        self.assertEqual(self.store.group_report_status("d-2"), "sent")

    async def test_cancelled_send_remains_held_before_and_after_restart(self):
        began = asyncio.Event()
        class WaitingChannel(Channel):
            async def send(self, *args):
                began.set()
                await asyncio.Future()
        self.store.enqueue_group_report("a-1", "first")
        service = self.service(WaitingChannel(None))
        task = asyncio.create_task(service.flush_reports())
        await began.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(service.last_error, "delivery_unknown:cancelled_attempt")
        channel = Channel(SendResult.ok("om_sent"))
        service.channel = channel
        await service.flush_reports()
        self.assertEqual(channel.calls, [])
        self.store.close()
        self.store = SQLiteStore(self.root / "state.sqlite")
        await self.service(channel).flush_reports()
        self.assertEqual(channel.calls, [])
        self.assertEqual(self.store.group_outbox_health()["held"], 1)

    async def test_child_lookup_error_cannot_release_existing_unknown_hold(self):
        async def send(*args):
            raise TimeoutError("uncertain")
        lookup_failed = False
        def lookup(job_id):
            if lookup_failed:
                raise RuntimeError("temporary lookup error")
            return {"status": "completed", "stale": False}
        service = self.service(Channel(SendResult.ok("om_astra")),
                               deepseek_sender=SimpleNamespace(send=send), job_lookup=lookup)
        self.store.enqueue_group_report("d-1", "child", role="deepseek", job_id="child-1")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        lookup_failed = True
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        self.assertEqual(self.store.group_report_delivery("d-1")["delivery_state"],
                         "delivery_unknown")
        self.assertEqual(service.last_error, "delivery_unknown:TimeoutError")
        with self.assertRaises(ValueError):
            self.store.attempt_group_report("d-1")

    async def test_raw_code_is_preserved_but_hint_and_raw_response_are_not(self):
        result = SendResult.fail(SendError(
            code=FeishuChannelErrorCode.PERMISSION_DENIED, retryable=False,
            raw_code=230003, hint="SECRET"), raw={"app_secret": "SECRET"})
        service = self.service(Channel(result))
        self.store.enqueue_group_report("a-1", "sensitive message")
        with self.assertRaises(RuntimeError) as raised:
            await service.flush_reports()
        self.assertEqual(str(raised.exception), "permission_denied:230003")
        health = self.store.group_outbox_health()
        self.assertEqual(health["last_error"], "permission_denied:230003")
        self.assertNotIn("SECRET", json.dumps(health))
        self.assertNotIn("sensitive message", json.dumps(health))

    async def test_runtime_health_exposes_pending_error_even_after_restart(self):
        service = self.service(Channel(token_denial()))
        self.store.enqueue_group_report("a-1", "first")
        with self.assertRaises(RuntimeError):
            await service.flush_reports()
        config = NodeConfig(node_id="A", project_id="fpga-main",
                            state_dir=self.root / "runtime", mode="test_double",
                            hardware_enabled=False, peer_urls={},
                            shared_secret_env="UNUSED_TEST_SECRET")
        runtime = NodeRuntime(config)
        original_store = runtime.store
        runtime.store = self.store
        runtime.feishu = self.service(Channel(SendResult.ok("om_sent")))
        try:
            health = runtime.snapshot()
            self.assertTrue(health["feishu_connected"])
            self.assertEqual(health["feishu_error"], "access_token_error:21001")
            self.assertEqual(health["feishu_outbox"]["pending"], 1)
            self.assertEqual(health["feishu_outbox"]["roles"]["astra"]["attempts"], 1)
        finally:
            runtime.store = original_store
            runtime.feishu = None
            await runtime.stop()

    async def test_send_only_sdk_token_exception_retains_only_code(self):
        secret = self.root / "child.txt"
        secret.write_text("test-secret", encoding="utf-8")
        def create(request):
            raise ObtainAccessTokenException(
                "obtain self tenant access token failed", 21001, "SECRET")
        client = SimpleNamespace(im=SimpleNamespace(
            v1=SimpleNamespace(message=SimpleNamespace(create=create))))
        sender = FeishuAppSender(app_id="cli_child", secret_file=secret,
                                 client_factory=lambda *args: client)
        with self.assertRaises(Exception) as raised:
            await sender.send("oc_team", "child", "d-1")
        self.assertEqual(str(raised.exception), "access_token_error:21001")

    def test_store_rejects_ack_without_real_id(self):
        self.store.enqueue_group_report("a-1", "first")
        for value in ("", "   ", None):
            with self.assertRaises(ValueError):
                self.store.ack_group_report("a-1", value)
        self.assertEqual(self.store.group_report_status("a-1"), "pending")

    def test_legacy_group_outbox_migrates_without_losing_rows(self):
        path = self.root / "legacy.sqlite"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE group_outbox (operation_id TEXT PRIMARY KEY, "
                       "text TEXT NOT NULL, created_at TEXT NOT NULL, sent_at TEXT, "
                       "platform_message_id TEXT)")
            db.execute("INSERT INTO group_outbox VALUES ('old', 'original', "
                       "'2026-10-16T00:00:00Z', NULL, NULL)")
        db.close()
        store = SQLiteStore(path)
        try:
            self.assertEqual(store.pending_group_messages(), [("old", "original", "astra")])
            state = store.group_report_delivery("old")
            self.assertEqual(state["attempts"], 0)
            self.assertEqual(state["last_error"], "delivery_unknown:legacy_delivery_untracked")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
