import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lark_channel.channel.types import SendResult
from fpga_mesh.feishu_channel import FeishuIngress, FeishuNodeService
from fpga_mesh.store import SQLiteStore


class RoleProgressTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp)
        self.store = SQLiteStore(self.root / "state.sqlite")
        self.addCleanup(self.store.close)

    def service(self, astra, child):
        service = FeishuNodeService(
            node_id="A", project_id="offline-roles", group_id="oc_fake",
            astra_app_id="cli_fake", astra_secret_file=self.root / "unused",
            controller=object(), store=self.store, deepseek_sender=SimpleNamespace(send=child),
        )
        service.channel = SimpleNamespace(send=astra)
        service.connected = True
        return service

    async def test_stalled_astra_allows_child_fifo_and_later_notification_progress(self):
        began = asyncio.Event()
        delivered = asyncio.Event()
        children = []
        async def astra(*args):
            began.set()
            await asyncio.Future()
        async def child(group, text, operation):
            children.append(operation)
            delivered.set()
            return "om_" + operation
        service = self.service(astra, child)
        self.store.enqueue_group_report("a-1", "astra")
        self.store.enqueue_group_report("d-1", "first", role="deepseek")
        task = asyncio.create_task(service._run_outbox())
        try:
            await asyncio.wait_for(began.wait(), 1)
            await asyncio.wait_for(delivered.wait(), 0.2)
            delivered.clear()
            self.store.enqueue_group_report("d-2", "second", role="deepseek")
            service.notify_report()
            await asyncio.wait_for(delivered.wait(), 0.2)
            self.assertEqual(children, ["d-1", "d-2"])
            self.assertEqual(self.store.group_report_status("d-2"), "sent")
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(self.store.group_report_delivery("a-1")["last_error"],
                         "delivery_unknown:cancelled_attempt")

    async def test_concurrent_flush_keeps_one_active_send_per_role_and_fifo(self):
        began = asyncio.Event()
        release = asyncio.Event()
        active = 0
        maximum = 0
        order = []
        async def astra(to, message, opts):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            order.append(message["text"])
            began.set()
            await release.wait()
            active -= 1
            return SendResult.ok("om_" + message["text"])
        async def child(*args):
            return "om_child"
        service = self.service(astra, child)
        self.store.enqueue_group_report("a-1", "first")
        self.store.enqueue_group_report("a-2", "second")
        first = asyncio.create_task(service.flush_reports())
        await asyncio.wait_for(began.wait(), 1)
        second = asyncio.create_task(service.flush_reports())
        release.set()
        await asyncio.wait_for(asyncio.gather(first, second), 1)
        self.assertEqual(maximum, 1)
        self.assertEqual(order, ["first", "second"])

    async def test_other_role_reconciliation_does_not_wait_for_stalled_send(self):
        began = asyncio.Event()
        async def astra(*args):
            began.set()
            await asyncio.Future()
        async def child(*args):
            return "om_child"
        service = self.service(astra, child)
        self.store.enqueue_group_report("d-1", "unknown child", role="deepseek")
        self.store.attempt_group_report("d-1")
        self.store.fail_group_report("d-1", "TimeoutError", 30, delivery_unknown=True)
        self.store.enqueue_group_report("a-1", "astra")
        task = asyncio.create_task(service.flush_reports())
        await asyncio.wait_for(began.wait(), 1)
        try:
            await asyncio.wait_for(service.reconcile_report(
                "d-1", evidence_sha256="a" * 64, platform_message_id="om_reviewed"), 0.2)
            self.assertEqual(self.store.group_report_status("d-1"), "sent")
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    async def test_stalled_child_allows_new_astra_reports_and_cancel_holds_child(self):
        began = asyncio.Event()
        delivered = asyncio.Event()
        astra_texts = []
        async def astra(to, message, opts):
            astra_texts.append(message["text"])
            delivered.set()
            return SendResult.ok("om_" + message["text"])
        async def child(*args):
            began.set()
            await asyncio.Future()
        service = self.service(astra, child)
        self.store.enqueue_group_report("d-1", "child", role="deepseek")
        task = asyncio.create_task(service._run_outbox())
        try:
            await asyncio.wait_for(began.wait(), 1)
            self.store.enqueue_group_report("a-1", "first")
            service.notify_report()
            await asyncio.wait_for(delivered.wait(), 0.2)
            delivered.clear()
            self.store.enqueue_group_report("a-2", "second")
            service.notify_report()
            await asyncio.wait_for(delivered.wait(), 0.2)
            self.assertEqual(astra_texts, ["first", "second"])
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(self.store.group_report_delivery("d-1")["last_error"],
                         "delivery_unknown:cancelled_attempt")

    async def test_cancelling_flush_waits_for_both_roles_to_persist_unknown(self):
        astra_began = asyncio.Event()
        child_began = asyncio.Event()
        async def astra(*args):
            astra_began.set()
            await asyncio.Future()
        async def child(*args):
            child_began.set()
            await asyncio.Future()
        service = self.service(astra, child)
        self.store.enqueue_group_report("a-1", "astra")
        self.store.enqueue_group_report("d-1", "child", role="deepseek")
        task = asyncio.create_task(service.flush_reports())
        try:
            await asyncio.wait_for(asyncio.gather(astra_began.wait(), child_began.wait()), 1)
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        for operation in ("a-1", "d-1"):
            self.assertEqual(self.store.group_report_delivery(operation)["last_error"],
                             "delivery_unknown:cancelled_attempt")


class TrustedReceiverTests(unittest.IsolatedAsyncioTestCase):
    def message(self, **kwargs):
        values = dict(chat_id="oc_fake", chat_type="group", sender_type="user",
                      sender_id="ou_human", body_text="/fpga A inspect",
                      message_id="om_human", create_time=1780000000000,
                      raw={}, mentions=[], mentioned_bot=False)
        values.update(kwargs)
        return SimpleNamespace(**values)

    def ingress(self, callback):
        self.offered = []
        async def offer(envelope):
            self.offered.append(envelope)
            return True
        return FeishuIngress(node_id="A", project_id="offline-ingress", group_id="oc_fake",
                             app_id="cli_fake", controller=SimpleNamespace(offer=offer),
                             allowed_sender_ids={"ou_human"}, trusted_receiver=callback)

    async def test_true_callback_receives_validated_envelope_and_consumes_revision(self):
        received = []
        async def callback(envelope):
            received.append(envelope)
            return True
        ingress = self.ingress(callback)
        message = self.message(raw={"update_time": "1780000001000", "event_id": "ev_fake"})
        self.assertTrue(await ingress.ingest(message))
        self.assertFalse(await ingress.ingest(message))
        self.assertEqual(self.offered, [])
        self.assertEqual(len(received), 1)
        envelope = received[0]
        self.assertEqual(envelope.platform_group_id, "oc_fake")
        self.assertEqual(envelope.platform_message_id, "om_human")
        self.assertEqual(envelope.sender, "ou_human")
        self.assertEqual(envelope.recipient, "A/Astra-A")
        self.assertEqual(envelope.revision, 1780000001000)
        self.assertEqual(envelope.platform_event_id, "ev_fake")
        edited = self.message(raw={"update_time": "1780000002000"}, body_text="revised")
        self.assertTrue(await ingress.ingest(edited))
        self.assertFalse(await ingress.ingest(message))
        self.assertEqual([item.revision for item in received], [1780000001000, 1780000002000])
        self.assertEqual(received[0].task_id, received[1].task_id)

    async def test_false_callback_preserves_legacy_offer(self):
        received = []
        async def callback(envelope):
            received.append(envelope)
            return False
        self.assertTrue(await self.ingress(callback).ingest(self.message()))
        self.assertEqual(self.offered, received)
        self.assertEqual(len(self.offered), 1)

    async def test_rejected_source_group_target_never_reaches_callback(self):
        received = []
        async def callback(envelope):
            received.append(envelope)
            return True
        ingress = self.ingress(callback)
        for message in (self.message(chat_id="oc_other"), self.message(chat_type="p2p"),
                        self.message(sender_type="app"), self.message(sender_id="ou_unknown"),
                        self.message(body_text="/fpga B inspect"), self.message(message_id="")):
            self.assertFalse(await ingress.ingest(message))
        self.assertEqual(received, [])
        self.assertEqual(self.offered, [])

    async def test_callback_failure_never_falls_back_and_revision_can_retry(self):
        fail = True
        async def callback(envelope):
            if fail:
                raise RuntimeError("receiver failed")
            return True
        ingress = self.ingress(callback)
        with self.assertRaises(RuntimeError):
            await ingress.ingest(self.message())
        self.assertEqual(self.offered, [])
        fail = False
        self.assertTrue(await ingress.ingest(self.message()))

    async def test_node_service_passes_optional_receiver_to_ingress(self):
        received = []
        async def callback(envelope):
            received.append(envelope)
            return True
        service = FeishuNodeService(
            node_id="A", project_id="offline-ingress", group_id="oc_fake",
            astra_app_id="cli_fake", astra_secret_file=Path("unused"),
            controller=object(), trusted_receiver=callback,
        )
        self.assertTrue(await service.ingress.ingest(self.message()))
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
