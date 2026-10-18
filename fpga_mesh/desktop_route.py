"""The original resident controller's authenticated Feishu-to-Desktop route."""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .desktop_inbox import DesktopBinding, DesktopInbox, CodexQueueClient, dispatch_one
from .protocol import Envelope, MessageKind, SourceKind


class DesktopRoute:
    def __init__(self, *, state_dir, node_id, project_id, group_id, controller,
                 store, client_factory=CodexQueueClient, on_report=None):
        self.state_dir = Path(state_dir)
        self.binding_path = self.state_dir / 'desktop-group-owner.json'
        # Once configured, a missing/broken binding must never restore the old
        # per-message background writer as an implicit fallback.
        self.enabled = (self.binding_path.exists()
            or (self.state_dir / 'desktop-inbox.sqlite').exists()
            or (self.state_dir / 'desktop-feishu-spool').exists())
        self.node_id, self.project_id, self.group_id = node_id, project_id, group_id
        self.controller, self.store = controller, store
        self.client_factory, self.on_report = client_factory, on_report
        self.spool = self.state_dir / 'desktop-feishu-spool'
        self.inbox = (DesktopInbox(self.state_dir / 'desktop-inbox.sqlite', recover_inflight=True)
                      if self.enabled else None)
        self.error = None
        self.spool_errors = {}
        self._event, self._lock = asyncio.Event(), asyncio.Lock()
        self._task = None
        self._closed = False

    def binding(self):
        doc = json.loads(self.binding_path.read_text(encoding='utf-8'))
        binding = DesktopBinding(project_id=doc['project_id'], node_id=doc['node_id'],
            group_id=doc['group_id'], thread_id=doc['thread_id'], generation=doc['generation'],
            task_id=doc['task_id'], active=doc.get('status') == 'active')
        if (binding.project_id, binding.node_id, binding.group_id) != (self.project_id, self.node_id, self.group_id):
            raise ValueError('Desktop binding does not match this original node and group')
        owner = json.loads((self.state_dir / 'external-task-owners.json').read_text(encoding='utf-8')).get(binding.task_id, {})
        if (owner.get('owner_kind'), owner.get('thread_id'), owner.get('director_generation')) != (
                'desktop', binding.thread_id, binding.generation):
            raise ValueError('Desktop binding conflicts with the existing authoritative owner')
        return binding, doc

    async def receive(self, message):
        """Only called after the Feishu SDK ingress authenticated and filtered it."""
        if not self.enabled:
            return False
        if (message.source != SourceKind.HUMAN or message.project_id != self.project_id
                or message.recipient != f'{self.node_id}/Astra-{self.node_id}'
                or message.platform_group_id != self.group_id or not message.platform_message_id):
            raise ValueError('not a trusted Feishu envelope for this route')
        raw = message.to_json()
        name = hashlib.sha256(message.dedupe_key.encode('utf-8')).hexdigest()
        self.spool.mkdir(parents=True, exist_ok=True)
        path = self.spool / (name + '.json')
        if path.exists():
            prior = json.loads(path.read_text(encoding='utf-8'))
            if prior['envelope_json'] != raw:
                raise ValueError('immutable Feishu spool conflict')
        else:
            record = json.dumps({'envelope_json': raw,
                'received_at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False)
            temporary = self.spool / (name + '.tmp')
            # One resident receiver owns this directory. Preserve incomplete
            # previous writes for diagnosis instead of overwriting their bytes.
            if temporary.exists():
                temporary = self.spool / (name + '.' + os.urandom(8).hex() + '.tmp')
            with temporary.open('x', encoding='utf-8') as stream:
                stream.write(record); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, path)
        try:
            binding, _ = self.binding()
            # Supersession must be visible before acknowledging a new revision,
            # even while the asynchronous queue dispatcher is busy.
            self.inbox.accept_trusted_feishu(message, binding)
        except Exception as exc:
            self.error = 'Desktop routing blocked: ' + type(exc).__name__
        self._event.set()
        if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
            # Apply control to the original controller immediately, independently
            # of when Desktop can consume its copy. Normal instructions never go
            # through that controller's background-model dispatcher.
            await self.controller.offer(message)
        return True

    async def flush(self):
        if not self.enabled or self._closed:
            return
        async with self._lock:
            try:
                binding, doc = self.binding()
                binding.require_active()
                records = []
                self.spool_errors = {}
                for path in self.spool.glob('*.json'):
                    try:
                        saved = json.loads(path.read_text(encoding='utf-8'))
                        records.append((saved['received_at'], path,
                                        Envelope.from_json(saved['envelope_json'])))
                    except Exception as exc:
                        self.spool_errors[path.name] = type(exc).__name__
                for _, path, message in sorted(records, key=lambda pair: pair[0]):
                    try:
                        self.inbox.accept_trusted_feishu(message, binding)
                        if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
                            await self.controller.offer(message)
                    except Exception as exc:
                        self.spool_errors[path.name] = type(exc).__name__
                client = self.client_factory(executable=doc['codex_executable'],
                    expected_sha256=doc['codex_sha256'], cwd=doc['cwd'], codex_home=doc['codex_home'],
                    requests_dir=self.state_dir / 'desktop-inbox-claims')
                while self.inbox.pending(binding):
                    if await dispatch_one(self.inbox, binding, client) is None:
                        break
                self._recover_replies(binding)
                self.error = ('Desktop spool records need review' if self.spool_errors else None)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # Original authenticated envelopes stay in the durable spool.
                # Exception text may contain source data; expose only its type.
                self.error = 'Desktop routing blocked: ' + type(exc).__name__

    def _reply(self, row):
        result = row.get('result')
        if row['processing_state'] != 'completed' or not isinstance(result, dict):
            return None
        text = result.get('reply_text')
        if not isinstance(text, str) or not text.strip() or len(text) > 2800:
            raise ValueError('completed Desktop receipt requires a bounded reply_text')
        operation = 'desktop-result:' + row['receipt_id']
        added = self.store.enqueue_group_report(operation,
            f'Astra-{self.node_id} · 回复 {row["platform_message_id"]}\n{text}')
        if added and self.on_report:
            self.on_report()
        return {'operation_id': operation, 'status': self.store.group_report_status(operation)}

    def _recover_replies(self, binding):
        cursor = None
        while True:
            page = self.inbox.list_receipts(binding, include_completed=True, after_receipt_id=cursor)
            for row in page['rows']:
                self._reply(row)
            cursor = page['next_cursor']
            if cursor is None:
                break

    def _target(self, args):
        if not self.enabled or self._closed:
            raise ValueError('Desktop route is not enabled')
        binding, _ = self.binding()
        if (args.get('thread_id'), args.get('generation')) != (binding.thread_id, binding.generation):
            raise ValueError('caller must name the current Desktop owner generation')
        return binding

    def _claim_block(self, row, *, ownership_verified=False):
        message = row['envelope']
        if (getattr(self.controller, 'dispatch_blocked', False)
                and message['kind'] not in {'stop_request', 'resume_request'}):
            return 'human_pause'
        if message['payload'].get('ownership_required') and not ownership_verified:
            return 'shared_task_ownership_unverified'
        return None

    def _refresh_before_claim(self, binding):
        # Acknowledged spool writes can precede an inbox write (disk/DB error,
        # paused owner, crash). Reapply them synchronously before any claim,
        # including after restart and after an ownership-network await.
        try:
            records = []
            for path in self.spool.glob('*.json'):
                saved = json.loads(path.read_text(encoding='utf-8'))
                records.append((saved['received_at'], Envelope.from_json(saved['envelope_json'])))
            for _, message in sorted(records, key=lambda item:item[0]):
                self.inbox.accept_trusted_feishu(message, binding)
                if message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}:
                    self.controller.recover_control(message)
        except Exception as exc:
            self.error = 'Desktop claim blocked by unapplied spool: ' + type(exc).__name__
            raise ValueError('unapplied Desktop spool requires recovery before execution') from None

    async def claim(self, args):
        binding = self._target(args)
        self._refresh_before_claim(binding)
        row = self.inbox.inspect_receipt(args['receipt_id'], binding, args['envelope_sha256'])
        if self._claim_block(row, ownership_verified=True):
            return {**row, 'effects_allowed':False, 'blocked_reason':'human_pause'}
        verified = False
        if (row['processing_state'] == 'pending' and not row['superseded_by']
                and row['envelope']['payload'].get('ownership_required')):
            owner = getattr(self.controller, 'claim_ownership', None)
            result = owner(Envelope.from_json(json.dumps(row['envelope']))) if owner else None
            result = await result if inspect.isawaitable(result) else result
            verified = result is True
        # Recheck binding, pause and revision after the ownership await.
        return self.call('desktop_inbox_claim', args, ownership_verified=verified)

    def call(self, action, args, *, ownership_verified=False):
        binding = self._target(args)
        if action == 'desktop_inbox_list':
            return self.inbox.list_receipts(binding, include_completed=args.get('include_completed', False),
                limit=args.get('limit', 100), after_receipt_id=args.get('after_receipt_id'))
        receipt = args['receipt_id']
        if action == 'desktop_inbox_claim':
            self._refresh_before_claim(binding)
            row = self.inbox.inspect_receipt(receipt, binding, args['envelope_sha256'])
            block = self._claim_block(row, ownership_verified=ownership_verified)
            if block:
                return {**row, 'effects_allowed':False, 'blocked_reason':block}
            return self.inbox.claim(receipt, binding, claim_id=args['claim_id'],
                expected_envelope_sha256=args['envelope_sha256'])
        if action == 'desktop_inbox_complete':
            result = args['result']
            if (not isinstance(result, dict) or not isinstance(result.get('reply_text'), str)
                    or not result['reply_text'].strip() or len(result['reply_text']) > 2800):
                raise ValueError('completion needs reply_text of 1 to 2800 characters')
            row = self.inbox.complete(receipt, binding, claim_id=args['claim_id'], result=result)
            return {**row, 'reply': self._reply(row)}
        if action == 'desktop_inbox_reconcile':
            row = self.inbox.reconcile(receipt, binding,
                expected_envelope_sha256=args['envelope_sha256'], evidence=args['evidence'])
            self._event.set()
            return row
        raise ValueError('unknown Desktop inbox action')

    def health(self):
        result = {'enabled': self.enabled, 'error': self.error,
                  'spool_errors': dict(self.spool_errors)}
        if self.enabled and not self._closed:
            try:
                binding, _ = self.binding()
                result.update(self.inbox.health(binding))
            except Exception as exc:
                result['error'] = 'Desktop binding blocked: ' + type(exc).__name__
        return result

    async def start(self):
        if self.enabled and self._task is None and not self._closed:
            self._task = asyncio.create_task(self._run(), name='fpga-desktop-inbox')
            self._event.set()

    async def _run(self):
        while True:
            self._event.clear()
            await self.flush()
            try:
                await asyncio.wait_for(self._event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if not self._closed and self.inbox is not None:
            self.inbox.close()
        self._closed = True
