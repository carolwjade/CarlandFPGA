import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fpga_mesh.desktop_route import DesktopRoute
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore

THREAD = "01a13d7e-dcf1-7272-a738-a637dd62ff9d"


class DesktopRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.store = SQLiteStore(self.root / "state.sqlite")
        self.addCleanup(self.store.close)
        self.offers = []
        async def offer(message):
            self.offers.append(message)
            return True
        self.controller = SimpleNamespace(offer=offer)
        self.queued = []
        parent = self
        class Client:
            def __init__(self, **kwargs):
                self.settings = kwargs
            async def enqueue(self, receipt):
                parent.queued.append(receipt)
                return "01a148bd-d616-7f02-8065-79e541dc6b04"
        self.client_factory = Client

    def configure(self):
        self.doc = dict(project_id="fpga-main", node_id="A", group_id="oc_team",
            thread_id=THREAD, generation=2, task_id="DEEPEYE-IMPLEMENTATION-20261014",
            status="active", codex_executable="unused.exe", codex_sha256="a" * 64,
            codex_home=str(self.root), cwd=str(self.root))
        (self.root / "desktop-group-owner.json").write_text(json.dumps(self.doc))
        self.owners = {self.doc["task_id"]: dict(owner_kind="desktop", thread_id=THREAD, director_generation=2)}
        (self.root / "external-task-owners.json").write_text(json.dumps(self.owners))

    def route(self):
        obj = DesktopRoute(state_dir=self.root, node_id="A", project_id="fpga-main",
            group_id="oc_team", controller=self.controller, store=self.store,
            client_factory=self.client_factory)
        self.addAsyncCleanup(obj.stop)
        return obj

    def message(self, kind=MessageKind.HUMAN_INSTRUCTION):
        return Envelope(message_id="feishu:oc_team:om_human:12", project_id="fpga-main",
            sender="ou_human", recipient="A/Astra-A", task_id="task-original", task_version=12,
            sent_at=datetime(2026,10,17,tzinfo=timezone.utc), kind=kind, source=SourceKind.HUMAN,
            payload={"text":"请继续已授权任务"}, revision=12,
            platform_group_id="oc_team", platform_message_id="om_human")

    async def test_configured_ingress_is_durable_and_never_background_dispatches(self):
        self.configure(); route = self.route()
        self.assertTrue(await route.receive(self.message()))
        await route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(self.offers, [])
        self.assertTrue(await route.receive(self.message()))
        await route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(route.inbox.get(self.queued[0]["receipt_id"])["delivery_state"], "queued")

    async def test_broken_owner_is_spooled_and_can_recover_without_background_fallback(self):
        self.configure(); route = self.route()
        (self.root / "external-task-owners.json").write_text("{")
        self.assertTrue(await route.receive(self.message()))
        await route.flush()
        self.assertEqual(len(self.queued), 0)
        self.assertEqual(self.offers, [])
        self.assertTrue(route.health()["error"])
        (self.root / "external-task-owners.json").write_text(json.dumps(self.owners))
        await route.flush()
        self.assertEqual(len(self.queued), 1)

    async def test_control_is_applied_to_original_controller_and_also_reaches_desktop(self):
        self.configure(); route = self.route()
        await route.receive(self.message(MessageKind.STOP_REQUEST))
        self.assertEqual([m.kind for m in self.offers], [MessageKind.STOP_REQUEST])
        await route.flush()
        self.assertEqual(len(self.queued), 1)

    async def test_unconfigured_node_keeps_original_ingress(self):
        route = self.route()
        self.assertFalse(await route.receive(self.message()))
        self.assertEqual(route.health()["enabled"], False)

    async def test_restart_reuses_receipt_and_does_not_resend_queue(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.flush(); await route.stop()
        replacement = self.route(); await replacement.flush()
        self.assertEqual(len(self.queued), 1)

    async def test_restart_without_binding_cannot_fall_back_to_background(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.stop()
        (self.root / 'desktop-group-owner.json').unlink()
        replacement = self.route()
        self.assertTrue(await replacement.receive(self.message()))
        await replacement.flush()
        self.assertTrue(replacement.health()['error'])
        self.assertEqual(self.offers, [])

    async def test_bad_spool_record_is_visible_but_does_not_hide_other_human_messages(self):
        self.configure(); route = self.route()
        await route.receive(self.message())
        (route.spool / 'damaged.json').write_text('{')
        await route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertTrue(route.health()['error'])
        self.assertEqual((route.spool / 'damaged.json').read_text(), '{')

    async def test_claim_complete_and_reply_recovery_are_idempotent(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.flush()
        row = self.queued[0]
        args = dict(thread_id=THREAD, generation=2, receipt_id=row['receipt_id'],
                    claim_id='one', envelope_sha256=row['envelope_sha256'])
        first = route.call('desktop_inbox_claim', args)
        self.assertTrue(first['effects_allowed'])
        self.assertFalse(route.call('desktop_inbox_claim', args)['effects_allowed'])
        binding, _ = route.binding()
        # Model completion persisted, then process exits before outbox enqueue.
        route.inbox.complete(row['receipt_id'], binding, claim_id='one', result={'reply_text':'已读取。'})
        await route.stop()
        replacement = self.route(); await replacement.flush(); await replacement.flush()
        reports = self.store.pending_group_reports()
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0][0], 'desktop-result:' + row['receipt_id'])
        self.assertIn('om_human', reports[0][1])
        self.assertIn('已读取。', reports[0][1])
        self.assertEqual(len(self.queued), 1)

    async def test_edit_invalidates_old_claim_before_queue_flush(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.flush()
        row = self.queued[0]
        await route.receive(replace(self.message(), message_id='feishu:oc_team:om_human:13',
            task_version=13, revision=13, payload={'text':'改为新指令'}))
        result = route.call('desktop_inbox_claim', dict(thread_id=THREAD, generation=2,
            receipt_id=row['receipt_id'], claim_id='old', envelope_sha256=row['envelope_sha256']))
        self.assertFalse(result['effects_allowed'])

    async def test_controller_pause_blocks_normal_claim(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.flush()
        row = self.queued[0]
        self.controller.dispatch_blocked = True
        result = route.call('desktop_inbox_claim', dict(thread_id=THREAD, generation=2,
            receipt_id=row['receipt_id'], claim_id='paused', envelope_sha256=row['envelope_sha256']))
        self.assertFalse(result['effects_allowed'])
        self.assertEqual(result['processing_state'], 'pending')

    async def test_shared_instruction_requires_original_ownership_claim(self):
        self.configure(); route = self.route()
        await route.receive(replace(self.message(), payload={'text':'shared', 'ownership_required':True}))
        await route.flush(); row = self.queued[0]
        args = dict(thread_id=THREAD, generation=2, receipt_id=row['receipt_id'],
                    claim_id='owned', envelope_sha256=row['envelope_sha256'])
        self.assertFalse(route.call('desktop_inbox_claim', args)['effects_allowed'])
        checks = []
        async def other_owner(message):
            checks.append(message); return False
        self.controller.claim_ownership = other_owner
        self.assertFalse((await route.claim(args))['effects_allowed'])
        self.assertEqual(len(checks), 1)
        async def our_owner(message):
            return True
        self.controller.claim_ownership = our_owner
        self.assertTrue((await route.claim(args))['effects_allowed'])

    async def test_spooled_edit_after_accept_failure_cannot_authorize_old_claim(self):
        self.configure(); route = self.route()
        await route.receive(self.message()); await route.flush(); row=self.queued[0]
        newer = replace(self.message(), message_id='feishu:oc_team:om_human:13',
            task_version=13, revision=13, payload={'text':'更正旧指令'})
        with patch.object(route.inbox, 'accept_trusted_feishu', side_effect=OSError('temporary')):
            self.assertTrue(await route.receive(newer))
        await route.stop(); route = self.route()
        result = route.call('desktop_inbox_claim', dict(thread_id=THREAD, generation=2,
            receipt_id=row['receipt_id'], claim_id='old', envelope_sha256=row['envelope_sha256']))
        self.assertFalse(result['effects_allowed'])
