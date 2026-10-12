"""Local integration evidence; no provider, Feishu or resident service is contacted."""
import asyncio
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from fpga_mesh.app_server import AppServerClient
from fpga_mesh.controller import ActionResult, Controller
from fpga_mesh.feishu_channel import FeishuIngress
from fpga_mesh.gateway import AppServerGateway, GatewayConfig
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.rpc import JsonRpcNotification
from fpga_mesh.runtime import NodeConfig, NodeRuntime
from test_feishu_channel import FakeMessage, RecordingController
from test_sessions import Wire


def message(identity, text="work", **changes):
    return replace(Envelope(
        message_id=identity, task_id=identity, task_version=1,
        project_id="fpga-main", sender="human", recipient="A/Astra-A",
        sent_at=datetime.now(timezone.utc), kind=MessageKind.HUMAN_INSTRUCTION,
        source=SourceKind.HUMAN, payload={"text": text},
    ), **changes)


class BlockedWire(Wire):
    def __init__(self):
        super().__init__()
        self.started = asyncio.Event()
        self.turn = None

    async def request(self, method, params=None):
        if method == "turn/start":
            self.requests.append((method, params))
            self.turn = params
            self.started.set()
            return {"turn": {"id": "held-turn"}}
        return await super().request(method, params)

    async def finish(self):
        if self.turn:
            await self.queue.put(JsonRpcNotification(method="turn/completed", params={
                "threadId": self.turn["threadId"], "turn": {
                    "id": "held-turn", "status": "completed",
                    "items": [{"type": "agentMessage", "phase": "final_answer", "text": "DONE"}],
                },
            }))


class ProgressQueryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = NodeRuntime(NodeConfig(
            node_id="A", project_id="fpga-main", state_dir=Path(self.tmp.name),
            mode="test_double", hardware_enabled=False, peer_urls={},
            shared_secret_env="UNUSED_PROGRESS_TEST_SECRET",
        ))
        self.controller = self.runtime.controller

    async def asyncTearDown(self):
        await self.runtime.stop()
        self.tmp.cleanup()

    async def test_original_query_does_not_cancel_real_app_gateway_and_work_completes(self):
        wire = BlockedWire()
        gateway = AppServerGateway(GatewayConfig(
            node_id="A", role="astra", model="gpt-6-astra", provider="openai",
            reasoning_effort="ultra", cwd=str(Path.cwd()), codex_home=self.tmp.name,
        ), client_factory=lambda: AppServerClient(wire, client_version="test"),
            session_router=self.runtime.main_sessions)
        self.runtime.astra_gateway = self.controller.gateway = gateway
        work = message("original")
        await self.controller.offer(work)
        worker = asyncio.create_task(self.controller.run_until_idle())
        try:
            await asyncio.wait_for(wire.started.wait(), 2)
            active = self.controller._active_dispatch
            before = list(wire.requests)
            ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                                   app_id="test", controller=self.controller)
            query = FakeMessage(body_text="当前工作进度")
            self.assertTrue(await ingress.ingest(query))
            self.assertFalse(await ingress.ingest(query))
            await self.controller.offer(message("query-version", "当前工作进度",
                                                task_id="original", task_version=99))
            self.assertEqual(self.runtime.store.latest_human_task_version("original"), 1)
            self.assertEqual(self.runtime.main_sessions.session("original")["task_version"], 1)
            self.assertEqual(active.cancelling(), 0, "pure query cancelled the original task")
            self.assertEqual(self.runtime.progress_snapshot()["main"]["counts"]["running"], 1)
            self.assertIn("running=1", self.runtime.store.pending_group_reports()[0][1])
            self.assertEqual(wire.requests, before)
            self.assertIsNone(self.runtime.main_sessions.result("query"))
            await wire.finish()
            await asyncio.wait_for(worker, 2)
            self.assertEqual(self.runtime.main_sessions.result("original")["status"], "completed")
            self.assertEqual(sum(m == "turn/start" for m, _ in wire.requests), 1)
        finally:
            await wire.finish()
            if not worker.done():
                worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    async def test_query_bypasses_task_version_callback_and_model(self):
        calls = []
        self.controller.on_human_instruction = lambda msg: calls.append(msg.message_id)
        await self.controller.offer(message("query", "/fpga status"))
        self.assertEqual(calls, [])
        self.assertIsNone(self.runtime.store.latest_human_task_version("query"))
        await self.controller.run_until_idle()
        self.assertEqual(self.runtime.astra_gateway.calls, [])

    async def test_ingress_classifies_query_without_claim(self):
        recorder = RecordingController()
        ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                               app_id="test", controller=recorder)
        await ingress.ingest(FakeMessage(body_text="当前工作进度"))
        self.assertEqual(recorder.messages[0].kind.value, "status_query")
        self.assertFalse(recorder.messages[0].payload["ownership_required"])

    async def test_status_is_durable_once_and_reports_snapshot_without_model(self):
        query = message("query", "当前工作进度", platform_group_id="oc_team",
                        platform_message_id="query-platform")
        self.assertTrue(await self.controller.offer(query))
        first = self.runtime.store.pending_group_reports()
        self.assertEqual(len(first), 1, "status needs an immediate durable reply")
        self.assertIn("snapshot_at=", first[0][1])
        self.assertIn("running=0", first[0][1])
        self.assertIn("completion_percent=unknown", first[0][1])
        self.assertFalse(await self.controller.offer(replace(query, message_id="duplicate")))
        self.assertEqual(self.runtime.store.pending_group_reports(), first)
        self.assertEqual(self.runtime.astra_gateway.calls, [])
        self.assertEqual(self.runtime.store.pending_inbound(), [])

    async def test_cli_status_is_read_only_and_does_not_open_gateway(self):
        calls = []
        async def forbidden():
            calls.append("client")
            raise AssertionError("status must not open a client")
        self.runtime.astra_gateway._ensure_client = forbidden
        before = self.runtime.store._connection.total_changes
        snapshot = await self.runtime.project_actions.call("progress_status", {})
        self.assertEqual(snapshot["active_dispatch"]["state"], "idle")
        self.assertFalse(snapshot["paused"])
        self.assertEqual(calls, [])
        self.assertEqual(before, self.runtime.store._connection.total_changes)
        self.assertEqual(self.runtime.store.pending_group_reports(), [])

    async def test_paused_query_is_answered_and_does_not_release_pause_or_claim(self):
        claims = []
        self.controller.claim_ownership = lambda msg: claims.append(msg.message_id)
        await self.controller.offer(message("pause", "/fpga pause", kind=MessageKind.STOP_REQUEST))
        await self.controller.offer(message("queued"))
        await self.controller.offer(message("query", "当前工作进度",
                                            payload={"text": "当前工作进度", "ownership_required": True}))
        self.assertEqual(len(self.runtime.store.pending_group_reports()), 1)
        await self.controller.run_until_idle()
        snap = await self.runtime.project_actions.call("progress_status", {})
        self.assertTrue(snap["paused"])
        self.assertEqual(snap["main"]["counts"]["queued"], 1)
        self.assertEqual(claims, [])
        self.assertEqual(self.runtime.astra_gateway.calls, [])
        restored = Controller(self.runtime.store, self.runtime.astra_gateway)
        self.assertTrue(restored.dispatch_blocked)

    async def test_compounds_and_new_work_and_pause_still_interrupt(self):
        for text in ("当前工作进度，然后停止", "/fpga status\n取消任务", "change task", "/fpga pause"):
            with self.subTest(text=text):
                entered = asyncio.Event()
                cancelled = asyncio.Event()
                class Gate:
                    async def handle(self, msg):
                        if not msg.message_id.startswith("work-"):
                            return ActionResult(accepted=True)
                        entered.set()
                        try:
                            await asyncio.Event().wait()
                        except asyncio.CancelledError:
                            cancelled.set()
                            raise
                self.controller.gateway = Gate()
                # Each iteration uses a fresh inbox identity; old evidence is not replayed.
                work = message("work-" + text, source=SourceKind.ASTRA, kind=MessageKind.AGENT_REPORT)
                await self.controller.offer(work)
                worker = asyncio.create_task(self.controller.run_until_idle())
                try:
                    await asyncio.wait_for(entered.wait(), 1)
                    urgent = message("urgent-" + text, text, kind=(MessageKind.STOP_REQUEST
                                     if text == "/fpga pause" else MessageKind.HUMAN_INSTRUCTION))
                    await self.controller.offer(urgent)
                    await asyncio.wait_for(cancelled.wait(), 1)
                    await asyncio.wait_for(worker, 1)
                    self.assertEqual(self.controller.dispatch_blocked, text == "/fpga pause")
                finally:
                    if not worker.done():
                        worker.cancel()
                    await asyncio.gather(worker, return_exceptions=True)
                    self.runtime.store.mark_inbound_processed(work.message_id)
                    self.runtime.store.mark_inbound_processed("urgent-" + text)

    async def test_full_match_grammar_and_routing(self):
        from fpga_mesh.protocol import is_progress_query
        accepted = ("当前工作进度", " /fpga status ", "/fpga A status",
                    "/fpga A 当前工作进度", "Astra-A: 当前工作进度",
                    "Astra-A：/fpga status", "@FPGA Astra A 当前工作进度",
                    "@FPGA Astra A @FPGA DeepSeek B /fpga status")
        for text in accepted:
            with self.subTest(text=text):
                self.assertTrue(is_progress_query(text))
        for text in ("进度", "当前工作进度?", "当前工作进度，停止", "查询后停止",
                     "/fpga status cancel", "/fpga status\nstop", "解释当前工作进度",
                     "当前工作进度并修改任务", "@someone 当前工作进度"):
            with self.subTest(text=text):
                self.assertFalse(is_progress_query(text))
        for text in ("/fpga B 当前工作进度", "Astra-B: /fpga status"):
            recorder = RecordingController()
            ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                                   app_id="test", controller=recorder)
            self.assertFalse(await ingress.ingest(FakeMessage(body_text=text)))
            self.assertEqual(recorder.messages, [])

    async def test_platform_mentions_only_strip_known_prefix_and_preserve_compound(self):
        recorder = RecordingController()
        ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                               app_id="test", controller=recorder)
        mention = SimpleNamespace(key="@_user_1", name="FPGA Astra A", is_bot=True)
        for i, (text, kind) in enumerate((
                ("@_user_1 当前工作进度", "status_query"),
                ("@_user_1 当前工作进度，然后停止", "human_instruction"),
                ("@_user_9 当前工作进度", "human_instruction"))):
            await ingress.ingest(FakeMessage(message_id=str(i), body_text=text, mentions=[mention]))
            self.assertEqual(recorder.messages[-1].kind.value, kind)

    async def test_multiple_placeholder_mentions_are_independent_of_metadata_order(self):
        recorder = RecordingController()
        ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                               app_id="test", controller=recorder)
        a = SimpleNamespace(key="@_user_1", name="FPGA Astra A", is_bot=True, open_id="a")
        b = SimpleNamespace(key="@_user_2", name="FPGA Astra B", is_bot=True, open_id="b")
        await ingress.ingest(FakeMessage(body_text="@_user_1 @_user_2 当前工作进度", mentions=[b, a]))
        self.assertEqual(recorder.messages[0].kind.value, "status_query")

    async def test_display_mention_query_is_only_answered_by_addressed_node(self):
        recorder = RecordingController()
        ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                               app_id="test", controller=recorder)
        self.assertFalse(await ingress.ingest(FakeMessage(body_text="@FPGA Astra B 当前工作进度")))
        self.assertEqual(recorder.messages, [])

    async def test_failed_and_interrupted_ledgers_are_not_replayed_by_query_or_drain(self):
        wire = Wire()
        gateway = AppServerGateway(GatewayConfig(
            node_id="A", role="astra", model="gpt-6-astra", provider="openai",
            reasoning_effort="ultra", cwd=str(Path.cwd()), codex_home=self.tmp.name,
        ), client_factory=lambda: AppServerClient(wire, client_version="test"),
            session_router=self.runtime.main_sessions)
        self.runtime.astra_gateway = self.controller.gateway = gateway
        for state in ("failed", "interrupted"):
            work = message(state)
            self.runtime.main_sessions.record(state, state, state, error="original error")
            await self.controller.offer(work)
        before = self.runtime.main_sessions.run_summaries()
        await self.controller.offer(message("query", "/fpga status"))
        await self.controller.run_until_idle()
        self.assertEqual(self.runtime.main_sessions.run_summaries(), before)
        self.assertEqual(wire.requests, [])

    async def test_duplicate_after_controller_restart_keeps_original_reply(self):
        query = message("query", "/fpga status")
        await self.controller.offer(query)
        reports = self.runtime.store.pending_group_reports()
        restored = Controller(self.runtime.store, self.runtime.astra_gateway,
                              on_status_query=self.runtime._on_status_query)
        self.assertFalse(await restored.offer(query))
        await restored.run_until_idle()
        self.assertEqual(self.runtime.store.pending_group_reports(), reports)
        self.assertIsNone(self.runtime.store.latest_human_task_version(query.task_id))

    async def test_actual_gateway_pause_interrupts_then_status_preserves_interrupted_state(self):
        wire = BlockedWire()
        gateway = AppServerGateway(GatewayConfig(
            node_id="A", role="astra", model="gpt-6-astra", provider="openai",
            reasoning_effort="ultra", cwd=str(Path.cwd()), codex_home=self.tmp.name,
        ), client_factory=lambda: AppServerClient(wire, client_version="test"),
            session_router=self.runtime.main_sessions)
        self.runtime.astra_gateway = self.controller.gateway = gateway
        await self.controller.offer(message("original"))
        worker = asyncio.create_task(self.controller.run_until_idle())
        try:
            await asyncio.wait_for(wire.started.wait(), 2)
            ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                                   app_id="test", controller=self.controller)
            await ingress.ingest(FakeMessage(body_text="/fpga pause"))
            self.assertTrue(self.controller.dispatch_blocked)
            self.assertEqual(self.controller._active_dispatch.cancelling(), 1)
            await asyncio.wait_for(worker, 2)
            before = list(wire.requests)
            await self.controller.offer(message("query", "当前工作进度"))
            await self.controller.run_until_idle()
            self.assertEqual(wire.requests, before)
            snap = self.runtime.progress_snapshot()
            self.assertTrue(snap["paused"])
            self.assertEqual(snap["main"]["counts"]["interrupted"], 1)
            self.assertEqual(self.runtime.main_sessions.result("original")["status"], "interrupted")
            self.assertIn("turn/interrupt", [m for m, _ in wire.requests])
        finally:
            if not worker.done():
                worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    async def test_protocol_router_uses_same_query_classification(self):
        from fpga_mesh.feishu import HumanMessageRouter
        from test_feishu import registry, human_message
        router = HumanMessageRouter(registry())
        self.assertEqual(router.ingest(human_message("q", "当前工作进度"), local_node="A").envelope.kind,
                         MessageKind.STATUS_QUERY)
        self.assertEqual(router.ingest(human_message("stop", "当前工作进度，然后停止"), local_node="A").envelope.kind,
                         MessageKind.HUMAN_INSTRUCTION)

    async def test_child_ledger_failure_is_unknown_and_expired_queue_is_not_running(self):
        self.runtime.children.status = lambda: (_ for _ in ()).throw(RuntimeError("secret"))
        await self.controller.offer(message("expired", expires_at=datetime.now(timezone.utc)-timedelta(hours=1)))
        before = self.runtime.store._connection.total_changes
        snap = self.runtime.progress_snapshot()
        self.assertEqual(snap["children"]["counts"], "unknown")
        self.assertEqual(snap["main"]["counts"]["unknown"], 1)
        self.assertEqual(snap["main"]["counts"]["queued"], 0)
        self.assertNotIn("secret", str(snap))
        self.assertEqual(before, self.runtime.store._connection.total_changes)

    async def test_nonhuman_and_attachments_are_not_queries(self):
        called = []
        self.controller.on_status_query = lambda msg: called.append(msg.message_id)
        await self.controller.offer(message("peer", "/fpga status", source=SourceKind.ASTRA,
                                            kind=MessageKind.AGENT_REPORT))
        await self.controller.offer(message("attachment", payload={
            "text": "当前工作进度", "attachment_refs": ["file-task"]}))
        await self.controller.run_until_idle()
        self.assertEqual(called, [])
        self.assertEqual(len(self.runtime.astra_gateway.calls), 2)

    async def test_real_sdk_resources_and_full_content_cannot_be_hidden_by_body_text(self):
        recorder = RecordingController()
        ingress = FeishuIngress(node_id="A", project_id="fpga-main", group_id="oc_team",
                               app_id="test", controller=recorder)
        for i, extra in enumerate(({"resources": [object()]},
                                  {"content_text": "当前工作进度，然后取消任务"})):
            msg = SimpleNamespace(**{**vars(FakeMessage(body_text="当前工作进度")),
                                     "message_id": str(i), **extra})
            await ingress.ingest(msg)
            self.assertEqual(recorder.messages[-1].kind, MessageKind.HUMAN_INSTRUCTION)
            # The Controller fallback must not override the conservative ingress decision.
            calls = []
            self.controller.on_human_instruction = lambda message: calls.append(message.message_id)
            await self.controller.offer(recorder.messages[-1])
            self.assertEqual(calls, [recorder.messages[-1].message_id])

    async def test_snapshot_distinguishes_terminal_unknown_and_delayed_queue(self):
        ledger = self.runtime.main_sessions
        for status in ("failed", "interrupted", "completed", "running", "unexpected", "queued"):
            ledger.record(status, status, status, error="PRIVATE_ERROR_DO_NOT_PUBLISH")
        later = message("delayed")
        await self.controller.offer(later)
        self.runtime.store.mark_inbound_failed("delayed", "private",
            retry_at=datetime.now(timezone.utc) + timedelta(hours=1))
        await self.controller.offer(message("waiting"))
        snap = self.runtime.progress_snapshot()
        counts = snap["main"]["counts"]
        self.assertEqual(counts, {"running": 0, "queued": 1, "failed": 2,
                                 "interrupted": 1, "completed": 1, "unknown": 3})
        self.assertEqual(snap["pending_inbound"], 2)
        self.assertTrue(datetime.fromisoformat(snap["snapshot_at"]).tzinfo)
        self.assertNotIn("PRIVATE_ERROR", str(snap))
        self.assertEqual(ledger.result("running")["status"], "running")
        await self.controller.offer(message("query", "当前工作进度"))
        report = self.runtime.store.pending_group_reports()[0][1]
        for value in ("running=0", "failed=2", "interrupted=1", "unknown=3", "queued=1"):
            self.assertIn(value, report)

    async def test_failed_snapshot_source_is_unknown_without_mutating_work(self):
        self.runtime.main_sessions.run_summaries = lambda: (_ for _ in ()).throw(RuntimeError("private"))
        snap = self.runtime.progress_snapshot()
        self.assertEqual(snap["main"]["counts"], "unknown")
        self.assertNotIn("private", str(snap))
        await self.controller.offer(message("query", "当前工作进度"))
        self.assertEqual(len(self.runtime.store.pending_group_reports()), 1)

    async def test_query_callback_failure_is_recoverable_while_paused_without_inference(self):
        def fail(msg):
            raise RuntimeError("report unavailable")
        self.controller.on_status_query = fail
        await self.controller.offer(message("query", "当前工作进度"))
        self.runtime.store.mark_inbound_failed("query", "delivery only", retry_at=datetime.now(timezone.utc))
        await self.controller.offer(message("pause", kind=MessageKind.STOP_REQUEST))
        restored = Controller(self.runtime.store, self.runtime.astra_gateway,
                             on_status_query=self.runtime._on_status_query)
        await restored.run_until_idle()
        self.assertTrue(restored.dispatch_blocked)
        self.assertEqual(len(self.runtime.store.pending_group_reports()), 1)
        self.assertEqual(self.runtime.astra_gateway.calls, [])

    async def test_persisted_query_is_answered_before_older_work_dispatch_on_recovery(self):
        observations = []
        self.runtime.store.accept_inbound(message("older-work"))
        self.runtime.store.accept_inbound(message("saved-query", "/fpga status", kind=MessageKind.STATUS_QUERY))
        restored = Controller(self.runtime.store, self.runtime.astra_gateway,
            on_status_query=lambda msg: observations.append(len(self.runtime.astra_gateway.calls)))
        await restored.run_until_idle()
        self.assertEqual(observations, [0])

    async def test_missing_callback_retains_query_for_delivery_recovery(self):
        controller = Controller(self.runtime.store, self.runtime.astra_gateway)
        await controller.offer(message("undelivered", "当前工作进度"))
        rows = self.runtime.store.inbound_progress()
        self.assertEqual(len(rows), 1)
        self.assertIn("status callback", rows[0].last_error)
        self.assertEqual(self.runtime.astra_gateway.calls, [])

    async def test_snapshot_counts_all_pending_kinds_and_renders_retry_eligibility(self):
        from fpga_mesh.progress import format_progress
        for identity, kind in (("query", MessageKind.STATUS_QUERY), ("pause", MessageKind.STOP_REQUEST),
                               ("resume", MessageKind.RESUME_REQUEST), ("work", MessageKind.HUMAN_INSTRUCTION)):
            self.runtime.store.accept_inbound(message(identity, kind=kind))
        retry = datetime.now(timezone.utc)+timedelta(hours=1)
        self.runtime.store.mark_inbound_failed("work", "error", retry_at=retry)
        snap = self.runtime.progress_snapshot()
        self.assertEqual(snap["pending_inbound"], 4)
        self.assertEqual(snap["pending_work"], 1)
        self.assertEqual(snap["pending_queries"], 1)
        self.assertEqual(snap["pending_controls"], 2)
        self.assertIn("retry_at="+retry.isoformat(), format_progress(snap))

    async def test_legacy_status_action_still_reaches_child_control(self):
        from unittest.mock import patch, AsyncMock
        legacy = {"pool": {"standby": 0}, "jobs": []}
        with patch("fpga_mesh.project_control.LocalControlFileClient") as client:
            client.return_value.call = AsyncMock(return_value=legacy)
            self.assertEqual(await self.runtime.project_actions.call("status", {}), legacy)
            client.return_value.call.assert_awaited_once_with("status", {})
