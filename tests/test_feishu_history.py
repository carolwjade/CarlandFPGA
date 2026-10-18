import copy
import json
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.feishu_history import FeishuHistoryRecovery, HistoryAPIError


def message(mid='om_1', revision=1000, **kw):
    return dict(message_id=mid, chat_id='oc_team', create_time='1000',
                update_time=str(revision), deleted=False, msg_type='text',
                sender={'id': 'ou_human', 'id_type': 'open_id', 'sender_type': 'user'},
                body={'content': '{"text":"instruction"}'}, **kw)


def page(items=(), more=False, token=None):
    return dict(items=list(items), has_more=more, page_token=token)


class API:
    def __init__(self):
        self.pages = {('chat', None): page([message()])}
        self.messages = {}
        self.calls = []

    async def list_messages(self, **kw):
        self.calls.append(kw)
        value = self.pages.get((kw['container_type'], kw['page_token']), page())
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)

    async def get_message(self, mid):
        self.calls.append({'get': mid})
        value = self.messages.get(mid, message(mid))
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)


class RecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'history.sqlite'
        self.api, self.received, self.pending = API(), [], []
        self.fail_sink = False
        self.now = 10000
        self.engine = self.make_engine()

    def make_engine(self, **kw):
        return FeishuHistoryRecovery(self.path, group_id='oc_team', app_id='cli_a',
            api=self.api, sink=self.sink, pending_messages=lambda: self.pending,
            clock_ms=lambda: self.now, overlap_ms=1000, **kw)

    async def sink(self, record):
        if self.fail_sink:
            raise OSError('private exception text must not enter health')
        self.received.append(copy.deepcopy(record))
        return True

    async def asyncTearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    async def test_paginated_success_has_fixed_upper_and_immutable_page_evidence(self):
        self.api.pages[('chat', None)] = page([message()], True, 'next')
        self.api.pages[('chat', 'next')] = page([message('om_2')])
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'covered_visible')
        self.assertEqual(self.engine.checkpoint_ms, 10000)
        self.assertEqual(len(self.received), 2)
        self.assertTrue(all(x['upper_ms'] == 10000 for x in self.api.calls))
        audit = self.engine.audit(result['scan_id'])
        self.assertEqual(audit['pages'][0]['response']['page_token'], 'next')
        self.assertEqual(audit['pages'][1]['request']['page_token'], 'next')
        audit['pages'][0]['response']['items'].clear()
        self.assertEqual(len(self.engine.audit(result['scan_id'])['pages'][0]['response']['items']), 1)
        self.assertEqual(self.received[0]['disposition'], 'hold')
        self.assertEqual(self.received[0]['raw_message'], message())

    async def test_page_failure_does_not_advance_checkpoint_then_restart_replays_from_lower(self):
        self.api.pages[('chat', None)] = page([message()], True, 'next')
        self.api.pages[('chat', 'next')] = HistoryAPIError('api_error', 21001)
        result = await self.engine.scan('reconnected')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.engine.checkpoint_ms, 0)
        self.assertEqual(result['gap']['code'], 21001)
        old_audit = self.engine.audit(result['scan_id'])
        self.engine.close()
        self.engine = self.make_engine()
        self.api.pages[('chat', 'next')] = page([message('om_2')])
        result2 = await self.engine.scan('retry')
        self.assertEqual(result2['lower_ms'], 0)
        self.assertEqual(result2['status'], 'covered_visible')
        self.assertEqual(len(self.received), 2)
        self.assertEqual(self.engine.audit(result['scan_id']), old_audit)

    async def test_sink_failure_is_gap_and_message_retried(self):
        self.fail_sink = True
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(result['gap']['category'], 'sink_failure')
        self.assertNotIn('private exception', json.dumps(result))
        self.assertEqual(self.engine.checkpoint_ms, 0)
        self.fail_sink = False
        self.assertEqual((await self.engine.scan('retry'))['status'], 'covered_visible')
        self.assertEqual(len(self.received), 1)

    async def test_duplicate_revision_retraction_and_recheck_of_old_pending(self):
        await self.engine.scan('start')
        self.pending = [{'message_id': 'om_1'}]
        self.api.messages['om_1'] = message(revision=5000)
        await self.engine.scan('retry')
        self.assertEqual([r['revision'] for r in self.received], [1000, 5000])
        self.api.messages['om_1'] = dict(message(revision=6000), deleted=True)
        await self.engine.scan('retry')
        self.assertEqual(self.received[-1]['state'], 'deleted')
        self.assertEqual(self.received[-1]['revision'], 6000)
        self.assertEqual(len(self.received), 3)

    async def test_invisible_pending_is_hold_not_fabricated_delete(self):
        self.pending = [{'message_id': 'om_old'}]
        self.api.messages['om_old'] = HistoryAPIError('api_error', 230073)
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'gap')
        held = next(x for x in self.received if x['message_id'] == 'om_old')
        self.assertEqual(held['state'], 'unavailable')
        self.assertIsNone(held['revision'])
        self.assertIsNone(held['raw_message'])

    async def test_source_filtering_and_missing_group_requires_query_provenance(self):
        foreign = dict(message('om_foreign'), chat_id='oc_other')
        bot = dict(message('om_bot'), sender={'id': 'cli_bot', 'sender_type': 'app'})
        outsider = dict(message('om_out'), sender={'id': 'ou_out', 'sender_type': 'user'})
        self.api.pages[('chat', None)] = page([foreign, bot, outsider, message()])
        self.engine.close()
        self.engine = self.make_engine(allowed_sender_ids={'ou_human'})
        await self.engine.scan('start')
        self.assertEqual([x['message_id'] for x in self.received], ['om_1'])

    async def test_old_roots_enumerated_and_thread_pagination_has_no_time_request(self):
        self.api.pages[('chat', None)] = page([message('om_root', thread_id='omt_old')])
        self.api.pages[('thread', None)] = page([message('om_reply', thread_id='omt_old')], True, 'reply2')
        self.api.pages[('thread', 'reply2')] = page([message('om_reply2', thread_id='omt_old')])
        await self.engine.scan('start')
        self.assertIn('om_reply2', [x['message_id'] for x in self.received])
        self.now = 20000
        self.api.calls.clear()
        await self.engine.scan('reconnected')
        self.assertTrue(any(x.get('purpose') == 'old_root_discovery' for x in self.api.calls))
        self.assertTrue(any(x['container_type'] == 'thread' for x in self.api.calls))

    async def test_page_loop_and_page_limit_do_not_claim_coverage(self):
        self.api.pages[('chat', None)] = page([], True, 'loop')
        self.api.pages[('chat', 'loop')] = page([], True, 'loop')
        result = await self.engine.scan('start')
        self.assertEqual(result['gap']['category'], 'cursor_loop')
        self.assertEqual(self.engine.checkpoint_ms, 0)
        self.engine.close()
        self.engine = self.make_engine(max_pages=1)
        self.assertEqual((await self.engine.scan('retry'))['gap']['category'], 'page_limit')

    async def test_future_thread_item_not_ingested_and_observed_edit_after_bound_blocks_checkpoint(self):
        self.api.pages[('chat', None)] = page([dict(message(), update_time='20000')])
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.received, [])

    async def test_same_revision_conflicting_body_is_explicit_gap(self):
        await self.engine.scan('start')
        self.api.pages[('chat', None)] = page([dict(message(), body={'content':'changed'})])
        result = await self.engine.scan('retry')
        self.assertEqual(result['gap']['category'], 'revision_conflict')
        self.assertEqual(len(self.received), 1)

    async def test_initial_lower_is_persistent_and_empty_page_scope_is_visible_only(self):
        self.engine.close()
        self.path.unlink()
        self.engine = self.make_engine(initial_lower_ms=500)
        self.api.pages[('chat', None)] = page()
        result = await self.engine.scan('start')
        self.assertEqual(result['lower_ms'], 500)
        self.assertIn('deleted_or_invisible_not_proven', result['limitations'])
        self.engine.close()
        self.engine = self.make_engine(initial_lower_ms=999)
        self.assertEqual(self.engine.initial_lower_ms, 500)

    async def test_timeout_is_bounded_and_checkpoint_unchanged(self):
        import asyncio
        async def hang(**_):
            await asyncio.Event().wait()
        self.api.list_messages = hang
        self.engine.close()
        self.engine = self.make_engine(max_seconds=0.02)
        result = await self.engine.scan('start')
        self.assertEqual(result['gap']['category'], 'time_limit')
        self.assertEqual(self.engine.checkpoint_ms, 0)

    async def test_begin_is_durable_before_remote_query_and_same_revision_rechecked_every_scan(self):
        self.pending = [{'message_id':'om_1', 'revision':1000, 'sender_id':'ou_human'}]
        begins = []
        async def begin(doc):
            self.assertEqual(len(self.api.calls), 0)
            begins.append(doc)
            return True
        self.engine.on_scan_begin = begin
        result = await self.engine.scan('start')
        self.assertEqual(begins[0]['scan_id'], result['scan_id'])
        self.api.calls.clear()
        await self.engine.scan('retry')
        rechecks = [r for r in self.received if r['context'] == 'pending_recheck']
        self.assertEqual(len(rechecks), 2)
        self.assertNotEqual(rechecks[0]['scan_id'], rechecks[1]['scan_id'])
        self.assertEqual(rechecks[0]['evidence_id'], rechecks[1]['evidence_id'])

    async def test_begin_refusal_aborts_without_remote_queries(self):
        async def begin(_):
            return False
        self.engine.on_scan_begin = begin
        result = await self.engine.scan('start')
        self.assertEqual(result['gap']['category'], 'scan_begin_not_durable')
        self.assertEqual(self.api.calls, [])

    async def test_pending_revision_regression_holds_and_blocks_checkpoint(self):
        self.api.pages[('chat', None)] = page([message(revision=6000)])
        await self.engine.scan('start')
        self.pending = [{'message_id':'om_1', 'revision':6000}]
        self.api.messages['om_1'] = message(revision=5000)
        result = await self.engine.scan('retry')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.received[-1]['state'], 'unavailable')
        self.assertEqual(self.received[-1]['reason'], 'revision_regressed')

    async def test_pending_sender_mismatch_is_held(self):
        self.pending = [{'message_id':'om_1', 'sender_id':'ou_original'}]
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.received[-1]['reason'], 'message_sender_mismatch')

    async def test_thread_response_cannot_claim_unrelated_thread_provenance(self):
        self.api.pages[('chat', None)] = page([message(thread_id='omt_original')])
        foreign = message('om_reply', thread_id='omt_foreign')
        foreign.pop('chat_id')
        self.api.pages[('thread', None)] = page([foreign])
        result = await self.engine.scan('start')
        self.assertEqual(result['gap']['category'], 'message_thread_mismatch')
        self.assertNotIn('om_reply', [r['message_id'] for r in self.received])

    async def test_empty_success_after_denied_pending_recheck_cannot_prove_delete(self):
        self.pending = [{'message_id':'om_old'}]
        self.api.messages['om_old'] = HistoryAPIError('message_unavailable')
        self.api.pages[('chat', None)] = page()
        result = await self.engine.scan('start')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.received[0]['state'], 'unavailable')

    async def test_restarted_unfinished_scan_remains_auditable_gap(self):
        self.engine._record('interrupted-scan', 'begin', dict(scan_id='interrupted-scan',
            lower_ms=0, upper_ms=9000, previous_checkpoint_ms=0, status='running'))
        self.engine.close()
        self.engine = self.make_engine()
        audit = self.engine.audit('interrupted-scan')
        self.assertEqual(audit['result']['status'], 'gap')
        self.assertEqual(audit['result']['gap']['category'], 'runtime_restarted')
        self.assertEqual(self.engine.checkpoint_ms, 0)

    async def test_audit_detects_mutated_page_bytes(self):
        result = await self.engine.scan('start')
        self.engine.db.execute("UPDATE evidence SET document_json='{}' WHERE kind='page'")
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            self.engine.audit(result['scan_id'])

    async def test_scan_end_called_once_and_failed_notification_keeps_checkpoint(self):
        calls = []
        async def end(result):
            calls.append(copy.deepcopy(result))
            raise OSError('private notification error')
        self.engine.on_scan_end = end
        result = await self.engine.scan('start')
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(result['notification_gap']['category'], 'scan_end_failed')
        self.assertEqual(self.engine.checkpoint_ms, 0)
        self.assertNotIn('private notification', json.dumps(result))

    async def test_cancelled_scan_has_terminal_audit_and_one_scan_end(self):
        import asyncio
        calls, querying = [], asyncio.Event()
        async def end(result):
            calls.append(copy.deepcopy(result))
            return True
        async def hang(**_):
            querying.set()
            await asyncio.Event().wait()
        self.engine.on_scan_end, self.api.list_messages = end, hang
        task = asyncio.create_task(self.engine.scan('start'))
        await querying.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.engine.last_result['gap']['category'], 'interrupted')
        self.assertEqual(self.engine.checkpoint_ms, 0)

    async def test_cancellation_during_scan_end_still_persists_terminal_gap(self):
        import asyncio
        notifying = asyncio.Event()
        async def end(_):
            notifying.set()
            await asyncio.Event().wait()
        self.engine.on_scan_end = end
        task = asyncio.create_task(self.engine.scan('start'))
        await notifying.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertIsNotNone(self.engine.last_result)
        self.assertEqual(self.engine.last_result['status'], 'gap')

    async def test_missing_chat_id_accepted_for_authenticated_group_page_only(self):
        raw = message()
        raw.pop('chat_id')
        self.api.pages[('chat', None)] = page([raw])
        await self.engine.scan('start')
        self.assertEqual(self.received[0]['query_group_id'], 'oc_team')
        self.assertNotIn('chat_id', self.received[0]['raw_message'])
        self.pending = [{'message_id':'om_1'}]
        self.api.messages['om_1'] = raw
        result = await self.engine.scan('retry')
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(self.received[-1]['reason'], 'message_group_mismatch')


if __name__ == '__main__':
    unittest.main()
