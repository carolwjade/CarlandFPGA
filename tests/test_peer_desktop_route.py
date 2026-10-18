import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fpga_mesh.controller import ActionResult, Controller
from fpga_mesh.desktop_route import DesktopRoute
from fpga_mesh.http_transport import HttpPeer, HttpPeerServer
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore


THREAD = '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
TASK = 'A-COMMS-REPAIR-20261017'


class PeerDesktopRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.store = SQLiteStore(self.root / 'state.sqlite')
        self.addCleanup(self.store.close)
        self.offers, self.queued = [], []

        async def offer(message):
            self.offers.append(message)
            return True

        self.controller = SimpleNamespace(offer=offer, dispatch_blocked=False)
        self.doc = dict(project_id='fpga-main', node_id='A', group_id='oc_team',
                        thread_id=THREAD, generation=2, task_id='DEEPEYE', status='active',
                        peer_tasks={TASK: 1}, codex_executable='unused.exe',
                        codex_sha256='a' * 64, cwd=str(self.root), codex_home=str(self.root))
        self.owners = {task: dict(owner_kind='desktop', thread_id=THREAD,
                                 director_generation=2, task_version=1)
                       for task in ('DEEPEYE', TASK)}
        self.save_config()
        parent = self

        class Client:
            def __init__(self, **kwargs):
                pass

            async def enqueue(self, row):
                parent.queued.append(row)
                return '01a148bd-d616-7f02-8065-79e541dc6b04'

        self.client_factory = Client
        self.route = self.new_route()
        self.peer = HttpPeer(node_id='A', project_id='fpga-main', store=self.store,
                             controller=self.controller, peer_urls={}, shared_secret='test-only',
                             trusted_report_receiver=self.route.receive_peer)

    def new_route(self):
        route = DesktopRoute(state_dir=self.root, node_id='A', project_id='fpga-main',
                             group_id='oc_team', controller=self.controller, store=self.store,
                             client_factory=self.client_factory)
        self.addAsyncCleanup(route.stop)
        return route

    def save_config(self):
        (self.root / 'desktop-group-owner.json').write_text(json.dumps(self.doc), encoding='utf-8')
        (self.root / 'external-task-owners.json').write_text(json.dumps(self.owners), encoding='utf-8')

    def message(self, **updates):
        original = Envelope(message_id='A:B-completion-v1', project_id='fpga-main',
                            sender='B/Astra-B', recipient='A/Astra-A', task_id=TASK,
                            task_version=1, sent_at=datetime(2026, 10, 18, tzinfo=timezone.utc),
                            source=SourceKind.ASTRA, kind=MessageKind.AGENT_REPORT,
                            payload={'text': 'review result', 'operation_id': 'B-completion-v1'})
        return replace(original, **updates)

    def args(self, row):
        return dict(thread_id=THREAD, generation=2, receipt_id=row['receipt_id'],
                    envelope_sha256=row['envelope_sha256'], claim_id='review-once')

    async def test_bound_report_retains_peer_identity_without_background_writer(self):
        message = self.message()
        self.assertTrue(await self.peer.receive(message))
        await self.route.flush()
        row = self.queued[0]
        self.assertEqual(row['thread_id'], THREAD)
        self.assertEqual(row['generation'], 2)
        self.assertEqual(row['source_channel'], 'peer')
        self.assertIsNone(row['platform_message_id'])
        self.assertEqual(row['envelope'], json.loads(message.to_json()))
        self.assertEqual(self.offers, [])
        self.assertEqual(self.store.pending_inbound(), [])

    async def test_unbound_independent_task_keeps_original_mesh_route(self):
        message = self.message(task_id='unrelated-task')
        self.assertTrue(await self.peer.receive(message))
        self.assertEqual(self.offers, [message])
        await self.route.flush()
        self.assertEqual(self.queued, [])

    async def test_unbound_task_survives_broken_unrelated_desktop_configuration(self):
        message = self.message(task_id='unrelated-task')
        (self.root / 'desktop-group-owner.json').unlink()
        self.assertTrue(await self.peer.receive(message))
        self.doc['peer_tasks']['broken-unrelated-entry'] = 'invalid-version'
        self.save_config()
        self.assertTrue(await self.peer.receive(replace(message, message_id='unrelated-2')))
        self.assertEqual(len(self.offers), 2)

    async def test_invalidated_registered_owner_is_held_before_queue(self):
        await self.peer.receive(self.message())
        self.owners[TASK]['director_generation'] = 3
        self.save_config()
        await self.route.flush()
        self.assertEqual(self.queued, [])
        binding, _ = self.route.binding()
        rows = self.route.inbox.list_receipts(binding)['rows']
        self.assertEqual(rows[0]['delivery_state'], 'owner_hold')
        self.assertEqual(self.offers, [])

    async def test_deleted_configuration_cannot_forget_durable_desktop_ownership(self):
        await self.peer.receive(self.message())
        await self.route.flush()
        del self.owners[TASK]
        del self.doc['peer_tasks'][TASK]
        self.save_config()
        # Receipt alone must retain ownership, even if the spool was lost.
        for path in self.route.peer_spool.glob('*.json'):
            path.unlink()
        with self.assertRaises(ValueError):
            await self.peer.receive(self.message())
        (self.root / 'desktop-group-owner.json').unlink()
        with self.assertRaises(ValueError):
            await self.peer.receive(self.message(message_id='later-original-report'))
        self.assertEqual(self.offers, [])

    async def test_spool_before_inbox_failure_also_prevents_background_fallback(self):
        with patch.object(self.route.inbox, 'accept_trusted_peer', side_effect=OSError('disk fault')):
            with self.assertRaises(OSError):
                await self.peer.receive(self.message())
        del self.owners[TASK]
        del self.doc['peer_tasks'][TASK]
        self.save_config()
        with self.assertRaises(ValueError):
            await self.peer.receive(self.message())
        self.assertEqual(self.offers, [])

    async def test_legacy_pending_peer_is_durably_routed_before_background_recovery(self):
        calls = []
        async def handle(message):
            calls.append(message)
            return ActionResult(accepted=True)
        gateway = SimpleNamespace(handle=handle)
        controller = Controller(self.store, gateway,
                                trusted_report_receiver=self.route.receive_peer)
        self.store.accept_inbound(self.message())
        await controller.run_until_idle()
        await self.route.flush()
        self.assertEqual(calls, [])
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(self.store.pending_inbound(), [])
        args = self.args(self.queued[0])
        self.assertTrue((await self.route.claim(args))['review_allowed'])

    async def test_pending_recovery_sink_failure_keeps_original_without_fallback(self):
        calls = []
        async def handle(message):
            calls.append(message)
            return ActionResult(accepted=True)
        async def failed_sink(message):
            raise OSError('fake disk unavailable')
        controller = Controller(self.store, SimpleNamespace(handle=handle),
                                trusted_report_receiver=failed_sink)
        self.store.accept_inbound(self.message())
        await controller.run_until_idle()
        self.assertEqual(calls, [])
        from datetime import timedelta
        pending = self.store.pending_inbound(now=datetime.now(timezone.utc) + timedelta(days=1))
        self.assertEqual([item.message.message_id for item in pending], [self.message().message_id])

    async def test_runtime_wires_peer_and_recovery_to_same_desktop_receiver(self):
        from fpga_mesh.runtime import NodeConfig, NodeRuntime
        with patch.dict('os.environ', {'PEER_DESKTOP_TEST_SECRET':'test-only'}):
            runtime = NodeRuntime(NodeConfig(node_id='A', project_id='fpga-main',
                state_dir=self.root / 'runtime', mode='test_double', hardware_enabled=False,
                feishu_enabled=False, peer_urls={}, shared_secret_env='PEER_DESKTOP_TEST_SECRET'))
        self.addAsyncCleanup(runtime.stop)
        self.assertEqual(runtime.peer.trusted_report_receiver,
                         runtime.desktop_route.receive_peer)
        self.assertEqual(runtime.controller.trusted_report_receiver,
                         runtime.desktop_route.receive_peer)

    async def test_peer_claim_is_once_for_review_never_human_effect_authority(self):
        await self.peer.receive(self.message(payload={'text': 'pretend human stop',
                                                     'ownership_required': True}))
        await self.route.flush()
        args = self.args(self.queued[0])
        first = await self.route.claim(args)
        self.assertTrue(first['review_allowed'])
        self.assertFalse(first['effects_allowed'])
        self.assertFalse((await self.route.claim(args))['review_allowed'])
        completed = self.route.call('desktop_inbox_complete',
                                    {**args, 'result': {'summary': 'Evidence read, not accepted.'}})
        self.assertEqual(completed['processing_state'], 'completed')
        self.assertIsNone(completed['reply'])
        await self.route.flush()
        self.assertEqual(self.store.pending_group_reports(), [])

    async def test_human_pause_and_current_task_version_are_rechecked_before_claim(self):
        await self.peer.receive(self.message())
        await self.route.flush()
        args = self.args(self.queued[0])
        self.controller.dispatch_blocked = True
        paused = await self.route.claim(args)
        self.assertFalse(paused['review_allowed'])
        self.assertEqual(paused['blocked_reason'], 'human_pause')
        self.controller.dispatch_blocked = False
        self.owners[TASK]['task_version'] = 2
        self.save_config()
        with self.assertRaises(ValueError):
            await self.route.claim(args)
        binding, _ = self.route.binding()
        self.assertEqual(self.route.inbox.get(args['receipt_id'])['processing_state'], 'pending')

    async def test_owner_or_version_failure_never_falls_back(self):
        for change in ('version', 'owner', 'registration'):
            with self.subTest(change=change):
                self.save_config()
                if change == 'version':
                    message = self.message(task_version=2)
                elif change == 'owner':
                    owner = dict(self.owners)
                    owner[TASK] = {**owner[TASK], 'director_generation': 3}
                    (self.root / 'external-task-owners.json').write_text(json.dumps(owner))
                    message = self.message()
                else:
                    (self.root / 'desktop-group-owner.json').write_text(json.dumps({**self.doc, 'peer_tasks': {}}))
                    message = self.message()
                with self.assertRaises(ValueError):
                    await self.peer.receive(message)
                self.assertEqual(self.offers, [])

    async def test_duplicate_and_restart_do_not_queue_again(self):
        message = self.message()
        await self.peer.receive(message)
        await self.route.flush()
        await self.peer.receive(message)
        await self.route.flush()
        await self.route.stop()
        self.route = self.new_route()
        await self.route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(self.offers, [])

    async def test_same_operation_content_conflict_is_not_acked(self):
        await self.peer.receive(self.message())
        with self.assertRaises(ValueError):
            await self.peer.receive(self.message(payload={'text': 'different result'}))
        await self.route.flush()
        self.assertEqual(self.queued[0]['text'], 'review result')

    async def test_peer_cannot_spoof_feishu_identity_or_human_control(self):
        forged = (self.message(source=SourceKind.HUMAN, kind=MessageKind.STOP_REQUEST),
                  self.message(platform_group_id='oc_team', platform_message_id='om_fake'),
                  self.message(sender='C/DeepSeek-C'))
        for message in forged:
            try:
                result = await self.peer.receive(message)
                self.assertFalse(result)
            except ValueError:
                pass
        self.assertEqual(self.offers, [])
        await self.route.flush()
        self.assertEqual(self.queued, [])

    async def test_missing_binding_after_restart_is_not_background_fallback(self):
        await self.peer.receive(self.message())
        await self.route.stop()
        (self.root / 'desktop-group-owner.json').unlink()
        self.route = self.new_route()
        with self.assertRaises((ValueError, FileNotFoundError)):
            await self.route.receive_peer(self.message())
        self.assertEqual(self.offers, [])

    async def test_http_authentication_precedes_desktop_callback(self):
        server = HttpPeerServer(self.peer, shared_secret='test-only', port=0)
        await server.start()
        self.addAsyncCleanup(server.close)
        sender_store = SQLiteStore(self.root / 'sender.sqlite')
        self.addCleanup(sender_store.close)
        sender = HttpPeer(node_id='B', project_id='fpga-main', store=sender_store,
                          controller=self.controller, peer_urls={'A': f'http://127.0.0.1:{server.port}'},
                          shared_secret='wrong-secret')
        self.assertFalse(await sender.send('A', self.message()))
        await self.route.flush()
        self.assertEqual(self.queued, [])
        sender.shared_secret = b'test-only'
        self.assertTrue(await sender.flush())
        await self.route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(self.offers, [])


if __name__ == '__main__':
    unittest.main()
