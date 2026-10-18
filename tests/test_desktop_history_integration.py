import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fpga_mesh.desktop_route import DesktopRoute
from fpga_mesh.feishu_history import FeishuHistoryRecovery, HistoryAPIError
from fpga_mesh.protocol import Envelope, MessageKind, SourceKind
from fpga_mesh.store import SQLiteStore


THREAD = '01a13d7e-dcf1-7272-a738-a637dd62ff9d'


class DesktopHistoryIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        owner = dict(owner_kind='desktop',thread_id=THREAD,director_generation=2,task_version=1)
        (self.root/'external-task-owners.json').write_text(json.dumps({'DEEPEYE':owner}))
        (self.root/'desktop-group-owner.json').write_text(json.dumps(dict(project_id='fpga-main',
            node_id='A',group_id='oc_team',thread_id=THREAD,generation=2,task_id='DEEPEYE',status='active',
            codex_executable='fake',codex_sha256='a'*64,cwd=str(self.root),codex_home=str(self.root))))
        self.store = SQLiteStore(self.root/'state.sqlite'); self.addCleanup(self.store.close)
        self.queued = []
        parent = self
        class Client:
            def __init__(self, **kwargs): pass
            async def enqueue(self, row):
                parent.queued.append(row)
                return '01a148bd-d616-7f02-8065-79e541dc6b04'
        async def offer(message):
            raise AssertionError('history must not execute via controller.offer')
        self.controller = SimpleNamespace(dispatch_blocked=False, offer=offer)
        self.route = DesktopRoute(state_dir=self.root,node_id='A',project_id='fpga-main',group_id='oc_team',
            controller=self.controller,store=self.store,client_factory=Client,
            history_app_id='cli_original',history_allowed_user_ids={'ou_human'})
        self.addAsyncCleanup(self.route.stop)

    def live(self, revision=100, text='continue'):
        return Envelope(message_id='feishu:om_live:'+str(revision),project_id='fpga-main',
            sender='ou_human',recipient='A/Astra-A',task_id='original-human-task',task_version=revision,
            sent_at=datetime.fromtimestamp(.1,timezone.utc),kind=MessageKind.HUMAN_INSTRUCTION,
            source=SourceKind.HUMAN,revision=revision,platform_group_id='oc_team',platform_message_id='om_live',
            payload={'text':text,'feishu':{'body_text':text,'message_type':'text'}})

    def raw(self, mid='om_live', revision=100, text='continue'):
        return dict(message_id=mid,chat_id='oc_team',create_time='100',update_time=str(revision),
                    sender={'id':'ou_human','sender_type':'user'},message_type='text',
                    body={'content':json.dumps({'text':text})})

    def args(self, row):
        return dict(thread_id=THREAD,generation=2,receipt_id=row['receipt_id'],claim_id='first',
                    envelope_sha256=row['envelope_sha256'])

    def engine(self, api):
        engine = FeishuHistoryRecovery(self.root/'engine.sqlite',group_id='oc_team',app_id='cli_original',
            api=api,sink=self.route.receive_history,pending_messages=self.route.history_pending,
            on_scan_begin=self.route.history_scan_begin,on_scan_end=self.route.history_scan_end,
            allowed_sender_ids={'ou_human'},clock_ms=lambda:200)
        self.addCleanup(engine.close)
        return engine

    async def restart_route(self):
        factory = self.route.client_factory
        await self.route.stop()
        self.route = DesktopRoute(state_dir=self.root, node_id='A', project_id='fpga-main',
            group_id='oc_team', controller=self.controller, store=self.store, client_factory=factory,
            history_app_id='cli_original', history_allowed_user_ids={'ou_human'})
        self.addAsyncCleanup(self.route.stop)

    async def test_restart_gates_old_receipt_before_remote_connection_or_first_scan(self):
        await self.route.receive(self.live()); await self.route.flush()
        args = self.args(self.queued[0])
        await self.restart_route()
        self.assertFalse((await self.route.claim(args))['effects_allowed'])
        parent = self
        class API:
            async def list_messages(self, **kwargs): return {'items': [], 'has_more': False}
            async def get_message(self, mid): return parent.raw()
        await self.engine(API()).scan('restart')
        self.assertTrue((await self.route.claim(args))['effects_allowed'])

    async def test_startup_gate_covers_durable_spool_before_inbox_write(self):
        with patch.object(self.route.inbox, 'accept_trusted_feishu', side_effect=OSError('disk fault')):
            await self.route.receive(self.live())
        await self.restart_route()
        await self.route.flush()
        self.assertFalse((await self.route.claim(self.args(self.queued[0])))['effects_allowed'])

    async def test_reconnect_gate_is_synchronous_and_new_live_baseline_is_independent(self):
        await self.route.receive(self.live()); await self.route.flush()
        args = self.args(self.queued[0])
        self.assertTrue(self.route.history_recheck())
        self.assertFalse((await self.route.claim(args))['effects_allowed'])
        await self.route.receive(self.live(101, 'new human baseline')); await self.route.flush()
        self.assertTrue((await self.route.claim(self.args(self.queued[-1])))['effects_allowed'])

    async def test_claim_during_api_await_is_blocked_until_exact_current_recheck(self):
        await self.route.receive(self.live()); await self.route.flush()
        args = self.args(self.queued[0]); parent = self
        class API:
            async def list_messages(self, **kwargs):
                claim = await parent.route.claim(args)
                parent.assertFalse(claim['effects_allowed'])
                parent.assertEqual(claim['blocked_reason'],'history_rechecking')
                return {'items':[], 'has_more':False}
            async def get_message(self, mid): return parent.raw()
        result = await self.engine(API()).scan('start')
        self.assertEqual(result['status'],'covered_visible')
        self.assertTrue((await self.route.claim(args))['effects_allowed'])

    async def test_edited_history_invalidates_live_claim_and_emits_one_review_only_batch(self):
        await self.route.receive(self.live()); await self.route.flush()
        old_args=self.args(self.queued[0]); parent=self
        class API:
            async def list_messages(self, **kwargs): return {'items':[], 'has_more':False}
            async def get_message(self, mid): return parent.raw(revision=101,text='changed')
        engine=self.engine(API()); await engine.scan('start'); await self.route.flush()
        old=await self.route.claim(old_args)
        self.assertFalse(old['effects_allowed']); self.assertEqual(old['blocked_reason'],'history_changed')
        notice=self.queued[-1]
        self.assertEqual(notice['source_channel'],'feishu_history')
        self.assertEqual(notice['envelope']['source'],'system')
        self.assertIsNone(notice['platform_message_id'])
        args=self.args(notice); review=await self.route.claim(args)
        self.assertTrue(review['review_allowed']); self.assertFalse(review['effects_allowed'])
        evidence=self.route.call('desktop_history_read',args)
        self.assertEqual(evidence['rows'][0]['message_id'],'om_live')
        self.assertEqual(evidence['rows'][0]['raw_message']['sender']['id'],'ou_human')
        self.route.call('desktop_inbox_complete',{**args,'result':{'summary':'Edited instruction held.'}})
        await self.route.flush(); self.assertEqual(self.store.pending_group_reports(),[])
        await engine.scan('retry'); await self.route.flush()
        self.assertEqual(len(self.queued),2)

    async def test_two_unseen_history_messages_are_one_notification_without_execution(self):
        parent=self
        class API:
            async def list_messages(self, **kwargs):
                return {'items':[parent.raw('om_one'),parent.raw('om_two')], 'has_more':False}
            async def get_message(self, mid): raise AssertionError('no current reference')
        engine=self.engine(API()); await engine.scan('start'); await self.route.flush()
        self.assertEqual(len(self.queued),1)
        row=self.queued[0]
        batch=self.route.call('desktop_history_read',self.args(row))
        self.assertEqual(len(batch['rows']),2)
        await engine.scan('retry'); await self.route.flush()
        self.assertEqual(len(self.queued),1)

    async def test_api_denial_keeps_gate_and_checkpoint_without_fake_empty_coverage(self):
        await self.route.receive(self.live()); await self.route.flush()
        class API:
            async def list_messages(self, **kwargs): raise HistoryAPIError('api_error',21001)
        engine=self.engine(API()); result=await engine.scan('start')
        self.assertEqual(result['status'],'gap'); self.assertEqual(result['gap']['code'],21001)
        self.assertEqual(engine.checkpoint_ms,0)
        self.assertFalse((await self.route.claim(self.args(self.queued[0])))['effects_allowed'])
        self.assertEqual(self.store.pending_group_reports(),[])

    async def test_new_live_revision_requires_matching_current_recheck_to_clear_old_hold(self):
        await self.route.receive(self.live()); await self.route.flush(); parent=self
        class API:
            async def list_messages(self, **kwargs): return {'items':[], 'has_more':False}
            async def get_message(self, mid): return parent.raw(revision=101,text='changed')
        engine=self.engine(API()); await engine.scan('start'); await self.route.flush()
        await self.route.receive(self.live(101,'changed')); await self.route.flush()
        current=next(row for row in self.queued if row['source_channel']=='feishu' and row['revision']==101)
        self.assertFalse((await self.route.claim(self.args(current)))['effects_allowed'])
        await engine.scan('retry')
        self.assertTrue((await self.route.claim(self.args(current)))['effects_allowed'])


if __name__ == '__main__': unittest.main()
