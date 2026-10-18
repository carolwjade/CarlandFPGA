import asyncio
import hashlib
import importlib
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fpga_mesh.protocol import Envelope, MessageKind, SourceKind


THREAD = '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
QUEUE = '01a148bd-d616-7f02-8065-79e541dc6b04'


def message(**changes):
    values = dict(message_id='feishu:oc_team:om_first:1', project_id='fpga-main',
                  sender='ou_human', recipient='A/Astra-A', task_id='task-original',
                  task_version=1, sent_at=datetime(2026, 10, 17, tzinfo=timezone.utc),
                  kind=MessageKind.HUMAN_INSTRUCTION, source=SourceKind.HUMAN,
                  payload={'text': '真人原文，不可进入 CLI argv', 'nested': {'x': [1, 2]}},
                  platform_group_id='oc_team', platform_message_id='om_first',
                  platform_event_id='evt_1', revision=1)
    values.update(changes)
    return Envelope(**values)


class InboxTests(unittest.TestCase):
    def setUp(self):
        try:
            self.api = importlib.import_module('fpga_mesh.desktop_inbox')
        except ModuleNotFoundError:
            self.fail('durable authenticated Desktop relay is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'inbox.sqlite'
        self.binding = self.api.DesktopBinding(project_id='fpga-main', node_id='A',
            group_id='oc_team', thread_id=THREAD, generation=2,
            task_id='DEEPEYE-IMPLEMENTATION-20261014')
        self.inbox = self.api.DesktopInbox(self.path)
        self.addCleanup(lambda: self.inbox.close())

    def accept(self, **changes):
        return self.inbox.accept_trusted_feishu(message(**changes), self.binding)

    def sending(self):
        item = self.accept()
        self.assertIsNotNone(self.inbox.begin_delivery(item['receipt_id'], self.binding))
        return self.inbox.get(item['receipt_id'])

    def claim(self, item, claim_id='turn-claim'):
        return self.inbox.claim(item['receipt_id'], self.binding, claim_id=claim_id,
            expected_envelope_sha256=item['envelope_sha256'])

    def test_complete_original_envelope_survives_mutation_duplicate_and_reopen(self):
        original = message()
        item = self.inbox.accept_trusted_feishu(original, self.binding)
        original.payload['nested']['x'].append(999)
        duplicate = self.accept()
        self.assertEqual(duplicate['receipt_id'], item['receipt_id'])
        self.assertFalse(duplicate['created'])
        self.inbox.close()
        self.inbox = self.api.DesktopInbox(self.path)
        stored = self.inbox.get(item['receipt_id'])
        self.assertEqual(stored['envelope']['payload']['nested'], {'x': [1, 2]})
        self.assertEqual(stored['envelope']['task_id'], 'task-original')
        self.assertEqual(stored['text'], '真人原文，不可进入 CLI argv')
        self.assertTrue(stored['received_at'])
        self.assertEqual(stored['delivery_state'], 'pending')
        self.assertEqual(stored['processing_state'], 'pending')

    def test_same_revision_with_changed_bytes_is_conflict_and_original_preserved(self):
        item = self.accept()
        with self.assertRaises(ValueError):
            self.accept(payload={'text': 'changed without revision'})
        self.assertEqual(self.inbox.get(item['receipt_id'])['text'], '真人原文，不可进入 CLI argv')

    def test_payload_cannot_turn_a_peer_into_a_trusted_human(self):
        for change in [dict(source=SourceKind.ASTRA), dict(recipient='B/Astra-B'),
                       dict(platform_group_id='oc_other'), dict(platform_message_id=None),
                       dict(sender=''), dict(project_id='other')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.accept(**change)
        self.assertEqual(self.inbox.pending(self.binding), [])

    def test_malformed_platform_metadata_and_nonfinite_payload_are_rejected_before_persistence(self):
        for change in [dict(platform_message_id=123), dict(platform_event_id={'event': 'spoof'}),
                       dict(payload={'text': 'x', 'invalid': float('nan')})]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.accept(**change)
        self.assertEqual(self.inbox.pending(self.binding), [])

    def test_inactive_owner_does_not_accept_dispatch_or_claim(self):
        item = self.sending()
        inactive = replace(self.binding, active=False)
        for action in [lambda: self.inbox.accept_trusted_feishu(message(), inactive),
                       lambda: self.inbox.begin_delivery(item['receipt_id'], inactive),
                       lambda: self.inbox.claim(item['receipt_id'], inactive,
                           claim_id='x', expected_envelope_sha256=item['envelope_sha256'])]:
            with self.assertRaises(ValueError):
                action()

    def test_one_delivery_cas_and_binding_serialization_across_connections(self):
        first = self.accept()
        second = self.accept(message_id='evt-other', platform_message_id='om_other')
        other = self.api.DesktopInbox(self.path)
        self.addCleanup(other.close)
        self.assertIsNotNone(self.inbox.begin_delivery(first['receipt_id'], self.binding))
        self.assertIsNone(other.begin_delivery(first['receipt_id'], self.binding))
        self.assertIsNone(other.begin_delivery(second['receipt_id'], self.binding))
        self.inbox.mark_queued(first['receipt_id'], self.binding, QUEUE)
        self.assertIsNotNone(other.begin_delivery(second['receipt_id'], self.binding))

    def test_restart_holds_unknown_delivery_without_automatic_retry(self):
        item = self.sending()
        self.inbox.close()
        self.inbox = self.api.DesktopInbox(self.path, recover_inflight=True)
        self.assertEqual(self.inbox.get(item['receipt_id'])['delivery_state'], 'delivery_unknown')
        self.assertEqual(self.inbox.pending(self.binding), [])
        self.assertIsNone(self.inbox.begin_delivery(item['receipt_id'], self.binding))

    def test_claim_checks_content_owner_and_grants_effects_only_once(self):
        item = self.sending()
        with self.assertRaises(ValueError):
            self.inbox.claim(item['receipt_id'], self.binding, claim_id='wrong-content',
                            expected_envelope_sha256='0' * 64)
        first = self.claim(item)
        self.assertTrue(first['effects_allowed'])
        self.assertFalse(self.claim(item)['effects_allowed'])
        self.assertFalse(self.claim(item, 'another-turn')['effects_allowed'])
        self.inbox.close()
        self.inbox = self.api.DesktopInbox(self.path)
        self.assertFalse(self.claim(item)['effects_allowed'])
        with self.assertRaises(ValueError):
            self.inbox.claim(item['receipt_id'], replace(self.binding, generation=3),
                claim_id='new-owner', expected_envelope_sha256=item['envelope_sha256'])

    def test_pending_is_not_authority_to_execute_and_completion_is_immutable(self):
        pending = self.accept()
        self.assertFalse(self.claim(pending)['effects_allowed'])
        self.inbox.begin_delivery(pending['receipt_id'], self.binding)
        claimed = self.claim(pending)
        result = self.inbox.complete(pending['receipt_id'], self.binding,
            claim_id='turn-claim', result={'text': 'handled', 'outcome': 'done'})
        self.assertEqual(result['processing_state'], 'completed')
        self.assertFalse(self.claim(pending)['effects_allowed'])
        self.assertEqual(self.inbox.complete(pending['receipt_id'], self.binding,
            claim_id='turn-claim', result={'outcome': 'done', 'text': 'handled'})['result'], result['result'])
        with self.assertRaises(ValueError):
            self.inbox.complete(pending['receipt_id'], self.binding,
                claim_id='turn-claim', result={'text': 'different'})
        with self.assertRaises(ValueError):
            self.inbox.complete(pending['receipt_id'], self.binding,
                claim_id='other', result=result['result'])
        self.assertTrue(claimed['effects_allowed'])

    def test_new_revision_stales_prior_but_does_not_release_existing_claim(self):
        old = self.sending()
        self.claim(old)
        new = self.accept(message_id='feishu:oc_team:om_first:2', revision=2,
                          task_version=2, platform_event_id='evt_2', payload={'text': 'amend'})
        stale = self.inbox.get(old['receipt_id'])
        self.assertEqual(stale['processing_state'], 'claimed')
        self.assertEqual(stale['superseded_by'], new['receipt_id'])
        self.assertTrue(stale['needs_attention'])
        self.assertFalse(self.claim(old)['effects_allowed'])
        self.assertEqual([r['receipt_id'] for r in self.inbox.pending(self.binding)], [new['receipt_id']])

    def test_late_old_revision_and_owner_change_are_held_not_replayed(self):
        new = self.accept(message_id='evt2', revision=2, task_version=2,
                          platform_event_id='evt2', payload={'text': 'new'})
        old = self.accept()
        self.assertEqual(old['superseded_by'], new['receipt_id'])
        moved = replace(self.binding, generation=3)
        self.assertEqual(self.inbox.pending(moved), [])
        repeated = self.inbox.accept_trusted_feishu(message(message_id='evt2', revision=2,
            task_version=2, platform_event_id='evt2', payload={'text': 'new'}), moved)
        self.assertEqual(repeated['receipt_id'], new['receipt_id'])
        self.assertEqual(repeated['delivery_state'], 'owner_hold')

    def test_unknown_reconciliation_requires_matching_evidence_and_never_releases_claim(self):
        item = self.sending()
        self.inbox.mark_delivery_unknown(item['receipt_id'], self.binding, reason='timeout')
        evidence = {'outcome': 'confirmed_not_queued', 'envelope_sha256': item['envelope_sha256'],
                    'evidence_sha256': 'a' * 64, 'reference': 'private/verified-probe.json'}
        with self.assertRaises(ValueError):
            self.inbox.reconcile(item['receipt_id'], self.binding,
                expected_envelope_sha256='0' * 64, evidence=evidence)
        reconciled = self.inbox.reconcile(item['receipt_id'], self.binding,
            expected_envelope_sha256=item['envelope_sha256'], evidence=evidence)
        self.assertEqual(reconciled['delivery_state'], 'pending')
        self.inbox.begin_delivery(item['receipt_id'], self.binding)
        self.inbox.mark_delivery_unknown(item['receipt_id'], self.binding, reason='crash')
        self.claim(item)
        with self.assertRaises(ValueError):
            self.inbox.reconcile(item['receipt_id'], self.binding,
                expected_envelope_sha256=item['envelope_sha256'], evidence=evidence)
        queued = dict(evidence, outcome='queued', queue_id=QUEUE)
        self.assertEqual(self.inbox.reconcile(item['receipt_id'], self.binding,
            expected_envelope_sha256=item['envelope_sha256'], evidence=queued)['queue_id'], QUEUE)

    def test_readonly_paginated_list_includes_delivery_holds_and_completed_for_outbox_recovery(self):
        first = self.sending()
        self.inbox.mark_delivery_unknown(first['receipt_id'], self.binding, reason='uncertain')
        second = self.accept(message_id='evt_other', platform_message_id='om_other')
        self.inbox.begin_delivery(second['receipt_id'], self.binding)
        self.claim(second)
        self.inbox.complete(second['receipt_id'], self.binding, claim_id='turn-claim',
                            result={'reply_text': 'recover original reply', 'outcome': 'done'})
        page = self.inbox.list_receipts(self.binding, include_completed=True, limit=1)
        self.assertEqual([r['receipt_id'] for r in page['rows']], [first['receipt_id']])
        self.assertEqual(page['next_cursor'], first['receipt_id'])
        tail = self.inbox.list_receipts(self.binding, include_completed=True,
            limit=1, after_receipt_id=page['next_cursor'])
        self.assertEqual(tail['rows'][0]['result']['reply_text'], 'recover original reply')
        self.assertIsNone(tail['next_cursor'])
        self.assertEqual(len(self.inbox.list_receipts(self.binding)['rows']), 1)
        self.assertEqual(self.inbox.list_receipts(replace(self.binding, generation=3))['rows'], [])
        self.assertEqual(self.inbox.get(first['receipt_id'])['delivery_state'], 'delivery_unknown')
        for limit in [0, True, 1001]:
            with self.assertRaises(ValueError):
                self.inbox.list_receipts(self.binding, limit=limit)
        with self.assertRaises(ValueError):
            self.inbox.list_receipts(replace(self.binding,generation=3), after_receipt_id=first['receipt_id'])


class QueueClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            self.api = importlib.import_module('fpga_mesh.desktop_inbox')
        except ModuleNotFoundError:
            self.fail('durable authenticated Desktop relay is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'codex.exe'
        self.exe.write_bytes(b'pinned executable test fixture')
        self.digest = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        self.binding = self.api.DesktopBinding('fpga-main', 'A', 'oc_team', THREAD, 2,
                                               'DEEPEYE-IMPLEMENTATION-20261014')
        self.inbox = self.api.DesktopInbox(self.root / 'inbox.sqlite')
        self.addCleanup(self.inbox.close)
        self.item = self.inbox.accept_trusted_feishu(message(), self.binding)
        self.calls = []

    def client(self, runner):
        return self.api.CodexQueueClient(executable=self.exe, expected_sha256=self.digest,
            cwd=self.root, codex_home=self.root / 'original-home',
            requests_dir=self.root / 'claims', runner=runner, timeout_seconds=1)

    async def good_runner(self, argv, *, cwd, env, timeout_seconds):
        self.calls.append((argv, cwd, env, timeout_seconds))
        return SimpleNamespace(returncode=0,
            stdout=f'Queued message {QUEUE} for thread {THREAD}.\n'.encode(), stderr=b'')

    async def test_dispatch_pins_binary_home_and_queues_only_receipt_claim_instructions(self):
        result = await self.api.dispatch_one(self.inbox, self.binding, self.client(self.good_runner))
        self.assertEqual(result['delivery_state'], 'queued')
        self.assertEqual(result['queue_id'], QUEUE)
        argv, cwd, env, _ = self.calls[0]
        self.assertEqual(argv[:4], [str(self.exe), 'queue', '--thread', THREAD])
        self.assertEqual(argv[4], '--message')
        self.assertNotIn('真人原文', ' '.join(argv))
        self.assertIn(self.item['receipt_id'], argv[5])
        self.assertIn('desktop_inbox_claim --args-file', argv[5])
        self.assertEqual(cwd, str(self.root))
        self.assertEqual(env['CODEX_HOME'], str(self.root / 'original-home'))
        self.assertEqual(env['CODEX_SQLITE_HOME'], str(self.root / 'original-home'))
        args = json.loads(next((self.root / 'claims').glob('*.json')).read_text(encoding='utf-8'))
        self.assertEqual(args['envelope_sha256'], self.item['envelope_sha256'])
        self.assertEqual(args['thread_id'], THREAD)
        self.assertEqual(args['generation'], 2)
        self.assertFalse(await self.api.dispatch_one(self.inbox, self.binding, self.client(self.good_runner)))
        self.assertEqual(len(self.calls), 1)

    async def test_changed_executable_is_blocked_before_any_process_call(self):
        client = self.client(self.good_runner)
        self.exe.write_bytes(b'replaced binary')
        result = await self.api.dispatch_one(self.inbox, self.binding, client)
        self.assertEqual(result['delivery_state'], 'delivery_unknown')
        self.assertEqual(self.calls, [])

    async def test_nonzero_empty_wrong_thread_and_timeout_hold_unknown_without_resend(self):
        await self.api.dispatch_one(self.inbox, self.binding, self.client(self.good_runner))
        cases = [('nonzero', 1, f'Queued message {QUEUE} for thread {THREAD}.', False),
                 ('empty', 0, '', False), ('wrongthread', 0,
                  f'Queued message {QUEUE} for thread 01a148bb-faea-73c1-b43e-dfd85e77cd88.', False),
                 ('timeout', 0, '', True)]
        for label, code, output, timeout in cases:
            with self.subTest(label=label):
                event = self.inbox.accept_trusted_feishu(message(message_id='evt-'+label,
                    platform_message_id='om_'+label), self.binding)
                async def runner(argv, *, cwd, env, timeout_seconds):
                    if timeout:
                        raise asyncio.TimeoutError()
                    return SimpleNamespace(returncode=code, stdout=output.encode(), stderr=b'do not log')
                result = await self.api.dispatch_one(self.inbox, self.binding, self.client(runner))
                self.assertEqual(result['receipt_id'], event['receipt_id'])
                self.assertEqual(result['delivery_state'], 'delivery_unknown')
                self.assertIsNone(self.inbox.begin_delivery(event['receipt_id'], self.binding))

    async def test_cancelled_delivery_is_persisted_unknown_before_propagating(self):
        async def runner(argv, *, cwd, env, timeout_seconds):
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.api.dispatch_one(self.inbox, self.binding, self.client(runner))
        self.assertEqual(self.inbox.get(self.item['receipt_id'])['delivery_state'], 'delivery_unknown')

    async def test_revision_arriving_during_send_preserves_ack_without_executing_old_input(self):
        async def runner(argv, *, cwd, env, timeout_seconds):
            self.inbox.accept_trusted_feishu(message(message_id='evt2', revision=2,
                task_version=2, platform_event_id='evt2', payload={'text': 'changed'}), self.binding)
            return await self.good_runner(argv, cwd=cwd, env=env, timeout_seconds=timeout_seconds)
        result = await self.api.dispatch_one(self.inbox, self.binding, self.client(runner))
        self.assertEqual(result['delivery_state'], 'superseded')
        self.assertEqual(result['queue_id'], QUEUE)
        claimed = self.inbox.claim(self.item['receipt_id'], self.binding, claim_id='late-old-turn',
            expected_envelope_sha256=self.item['envelope_sha256'])
        self.assertFalse(claimed['effects_allowed'])


if __name__ == '__main__':
    unittest.main()
