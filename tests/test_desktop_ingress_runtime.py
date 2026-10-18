"""Authenticated ingress to the same Desktop owner and original reply outbox."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fpga_mesh.runtime import NodeConfig, NodeRuntime
from tests.test_desktop_route import DesktopRouteTests, THREAD


class DesktopRuntimeTests(DesktopRouteTests):
    async def test_filtered_ingress_reaches_desktop_and_completion_uses_original_outbox(self):
        self.configure()
        config = NodeConfig(node_id='A', project_id='fpga-main', state_dir=self.root,
            mode='test_double', hardware_enabled=False, peer_urls={}, shared_secret_env='COMMS_TEST_UNUSED',
            feishu_enabled=True, feishu_group_id='oc_team', feishu_astra_app_id='cli_test',
            feishu_astra_secret_file=self.root / 'test-secret', feishu_allowed_user_ids=('ou_human',))
        runtime = NodeRuntime(config)
        self.addAsyncCleanup(runtime.stop)
        async def own_shared(message):
            return True
        runtime.controller.claim_ownership = own_shared
        runtime.desktop_route.client_factory = self.client_factory
        msg = SimpleNamespace(chat_id='oc_team', chat_type='group', sender_type='user',
            sender_id='ou_human', body_text='继续已授权通信修复', message_id='om_runtime',
            raw={}, create_time=1792200000000, mentions=(), mentioned_bot=False)
        self.assertTrue(await runtime.feishu.ingress.ingest(msg))
        self.assertFalse(await runtime.feishu.ingress.ingest(msg))
        await runtime.desktop_route.flush()
        self.assertEqual(len(self.queued), 1)
        self.assertEqual(runtime.store.pending_inbound(), [])
        self.assertEqual(runtime.snapshot()['idle_model_calls'], 0)
        target = dict(thread_id=THREAD, generation=2)
        listed = await runtime.project_actions.call('desktop_inbox_list', target)
        receipt = listed['rows'][0]
        args = dict(**target, receipt_id=receipt['receipt_id'], claim_id='main-test',
                    envelope_sha256=receipt['envelope_sha256'])
        claimed = await runtime.project_actions.call('desktop_inbox_claim', args)
        self.assertTrue(claimed['effects_allowed'])
        self.assertEqual(claimed['envelope']['platform_message_id'], 'om_runtime')
        completed = await runtime.project_actions.call('desktop_inbox_complete',
            dict(**args, result={'reply_text':'已读取，继续修复。'}))
        self.assertEqual(completed['reply']['status'], 'pending')
        self.assertEqual(len(runtime.store.pending_group_reports()), 1)
        wrong = SimpleNamespace(**{**vars(msg), 'message_id':'om_other', 'sender_id':'ou_other'})
        self.assertFalse(await runtime.feishu.ingress.ingest(wrong))
        self.assertEqual(len(runtime.desktop_route.inbox.list_receipts(runtime.desktop_route.binding()[0],
            include_completed=True)['rows']), 1)

