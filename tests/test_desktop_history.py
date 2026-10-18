import json
import tempfile
import unittest
from pathlib import Path

from fpga_mesh.desktop_history import DesktopHistory
from fpga_mesh.desktop_inbox import DesktopBinding


THREAD = '01a13d7e-dcf1-7272-a738-a637dd62ff9d'


class DesktopHistoryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.history = DesktopHistory(self.root / 'history.sqlite')
        self.addCleanup(self.history.close)
        self.binding = DesktopBinding('fpga-main', 'A', 'oc_team', THREAD, 2, 'DEEPEYE')
        self.receipt = {'revision': 100, 'platform_message_id': 'om_live',
            'envelope': {'sender': 'ou_human', 'revision': 100, 'payload': {
                'text': 'continue', 'feishu': {'body_text': 'continue', 'message_type': 'text'}}}}

    def observation(self, **changes):
        document = {'schema': 1, 'source': 'feishu_history', 'app_id': 'cli_original',
            'group_id': 'oc_team', 'message_id': 'om_live', 'revision': 100,
            'state': 'visible', 'disposition': 'hold', 'context': 'pending_recheck',
            'scan_id': 'scan-1', 'evidence_id': 'history-original-evidence',
            'query_group_id': 'oc_team', 'raw_message': {
                'message_id': 'om_live', 'chat_id': 'oc_team', 'create_time': '100',
                'update_time': '100', 'message_type': 'text',
                'sender': {'id': 'ou_human', 'sender_type': 'user'},
                'body': {'content': json.dumps({'text': 'continue'})}}}
        return {**document, **changes}

    def begin(self, scan='scan-1'):
        self.history.begin({'scan_id': scan, 'upper_ms': 200,
            'pending_messages': [{'message_id': 'om_live', 'revision': 100, 'sender_id': 'ou_human'}]},
            self.binding, [self.receipt])

    def observe(self, document, receipts=None):
        return self.history.observe(document, self.binding,
            [self.receipt] if receipts is None else receipts,
            app_id='cli_original', allowed_sender_ids={'ou_human'})

    def test_known_pending_is_held_before_query_and_exact_recheck_releases_only_transient_hold(self):
        self.begin()
        self.assertEqual(self.history.block_reason(self.binding, 'om_live', 100), 'history_rechecking')
        self.observe(self.observation(context='history_list'))
        self.assertEqual(self.history.block_reason(self.binding, 'om_live', 100), 'history_rechecking')
        self.observe(self.observation())
        self.assertIsNone(self.history.block_reason(self.binding, 'om_live', 100))
        self.history.finish({'scan_id': 'scan-1', 'status': 'complete'}, self.binding)
        self.assertEqual(self.history.pending_batches(self.binding), [])

    def test_old_scan_cannot_release_new_scan_gate(self):
        self.begin('scan-1'); self.begin('scan-2')
        self.observe(self.observation())
        self.assertEqual(self.history.block_reason(self.binding, 'om_live', 100), 'history_rechecking')
        self.observe(self.observation(scan_id='scan-2'))
        self.assertIsNone(self.history.block_reason(self.binding, 'om_live', 100))

    def test_old_changed_observation_cannot_replace_epoch_or_clear_future_conflict(self):
        self.begin('old')
        raw = self.observation()['raw_message']
        raw['update_time'] = '101'
        raw['body'] = {'content': json.dumps({'text': 'new live'})}
        self.observe(self.observation(scan_id='old', revision=101, raw_message=raw))
        self.receipt['revision'] = 101
        self.receipt['envelope']['payload']['feishu']['body_text'] = 'new live'
        self.history.begin({'scan_id': 'new', 'upper_ms': 300,
            'pending_messages': [{'message_id': 'om_live', 'revision': 101}]}, self.binding, [self.receipt])
        newer = {**raw, 'update_time': '102', 'body': {'content': json.dumps({'text': 'future conflict'})}}
        self.observe(self.observation(scan_id='old', revision=102, raw_message=newer))
        self.observe(self.observation(scan_id='old', revision=101, raw_message=raw))
        self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 101))
        self.observe(self.observation(scan_id='new', revision=101, raw_message=raw))
        self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 101))

    def test_old_scan_start_cannot_reclaim_new_gate_epoch(self):
        self.begin('old'); self.begin('new')
        with self.assertRaises(ValueError):
            self.begin('old')
        self.observe(self.observation(scan_id='old'))
        self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 100))

    def test_edit_deletion_and_unavailable_hold_original_without_executing_history(self):
        for state in ('visible', 'deleted', 'unavailable'):
            with self.subTest(state=state):
                self.begin(state + '-1')
                raw = self.observation()['raw_message']
                raw['update_time'] = '101'
                raw['body'] = {'content': json.dumps({'text': 'changed'})}
                raw['deleted'] = state == 'deleted'
                self.observe(self.observation(scan_id=state + '-1', state=state, revision=101 if state!='unavailable' else None,
                    raw_message=raw if state!='unavailable' else None,
                    evidence_id='history-' + state))
                self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 100))
                self.begin(state + '-2')
                self.observe(self.observation(scan_id=state + '-2'))
                self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 100))

    def test_same_revision_body_conflict_is_held(self):
        self.begin()
        raw = self.observation()['raw_message']
        raw['body'] = {'content': json.dumps({'text': 'different command'})}
        self.observe(self.observation(raw_message=raw))
        self.assertEqual(self.history.block_reason(self.binding, 'om_live', 100), 'history_changed')

    def test_recovered_messages_batch_once_and_do_not_requeue_unchanged_scan(self):
        self.history.begin({'scan_id': 'scan-1', 'upper_ms': 200, 'pending_messages': []}, self.binding, [])
        document = self.observation(context='history_list')
        self.observe(document, receipts=[])
        self.assertEqual(self.history.pending_batches(self.binding), [])
        self.history.finish({'scan_id': 'scan-1', 'status': 'gap', 'error': 'partial page'}, self.binding)
        batch = self.history.pending_batches(self.binding)[0]
        self.assertEqual(len(batch['observation_ids']), 1)
        self.assertEqual(self.history.inspect_batch(batch['batch_id'], self.binding)['rows'][0]['raw_message'], document['raw_message'])
        self.history.mark_notified(batch['batch_id'], self.binding, 'desk-test-receipt')
        self.history.begin({'scan_id': 'scan-2', 'upper_ms': 300, 'pending_messages': []}, self.binding, [])
        self.observe({**document, 'scan_id': 'scan-2'}, receipts=[])
        self.history.finish({'scan_id': 'scan-2', 'status': 'complete'}, self.binding)
        self.assertEqual(self.history.pending_batches(self.binding), [])

    def test_interrupted_scan_keeps_gate_and_surfaces_saved_evidence_on_restart(self):
        self.begin()
        self.observe(self.observation(state='unavailable', revision=None, raw_message=None))
        self.history.close()
        self.history = DesktopHistory(self.root / 'history.sqlite')
        self.addCleanup(self.history.close)
        self.assertIsNotNone(self.history.block_reason(self.binding, 'om_live', 100))
        self.assertEqual(len(self.history.pending_batches(self.binding)), 1)

    def test_wrong_app_group_sender_or_source_never_releases_gate(self):
        self.begin()
        for document in (self.observation(app_id='other'), self.observation(group_id='oc_other'),
                         self.observation(source='peer')):
            with self.assertRaises(ValueError):
                self.observe(document)
        raw = self.observation()['raw_message']
        raw['sender'] = {'sender_type':'app', 'id':'cli_other'}
        with self.assertRaises(ValueError):
            self.observe(self.observation(raw_message=raw))
        self.assertEqual(self.history.block_reason(self.binding, 'om_live', 100), 'history_rechecking')

    def test_newer_live_revision_and_other_node_instruction_are_not_taken_over(self):
        self.begin()
        self.assertIsNone(self.history.block_reason(self.binding, 'om_live', 102))
        raw = self.observation()['raw_message']
        raw['body'] = {'content': json.dumps({'text':'/fpga C run the C task'})}
        self.observe(self.observation(raw_message=raw, context='history_list'), receipts=[])
        self.history.finish({'scan_id':'scan-1','status':'complete'}, self.binding)
        self.assertEqual(self.history.pending_batches(self.binding), [])


if __name__ == '__main__':
    unittest.main()
