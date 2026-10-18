"""Bounded, durable Feishu history audits, independent of SDK event dedup.

Visible coverage is not proof of inaccessible/deleted history. Recovery creates
review holds; it never executes historical instructions or lifts a human pause.
Only the original resident service owns this store and calls its durable sink.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


class HistoryAPIError(RuntimeError):
    """Fixed category and numeric code only; SDK hints may contain secrets."""
    def __init__(self, category, code=None):
        self.category = category
        self.code = code if type(code) is int else None
        super().__init__(category)


class FeishuHistoryAPI:
    """Use generated 1.4.0 alist/aget, never the single-page SDK helper.

    Official API: /document/server-docs/im-v1/message/list. Thread containers
    do not accept start/end times; the engine filters their fixed upper bound.
    """
    def __init__(self, client, *, expected_app_id=None):
        if expected_app_id is not None and getattr(getattr(client, 'config', None), 'app_id', None) != expected_app_id:
            raise ValueError('history SDK app identity mismatch')
        self.client = client

    @staticmethod
    def _data(response):
        if not response.success():
            raise HistoryAPIError('api_error', getattr(response, 'code', None))
        # Preserve the actual API JSON, including unknown fields, when present.
        content = getattr(getattr(response, 'raw', None), 'content', None)
        if isinstance(content, (str, bytes)):
            body = json.loads(content)
            if body.get('code') != 0 or not isinstance(body.get('data'), dict):
                raise HistoryAPIError('malformed_response')
            return body['data']
        from lark_channel.core.json import JSON
        data = json.loads(JSON.marshal(response.data))
        if not isinstance(data, dict):
            raise HistoryAPIError('malformed_response')
        return data

    async def list_messages(self, *, container_type, container_id, lower_ms,
                            upper_ms, page_token=None, purpose=None):
        from lark_channel.api.im.v1.model.list_message_request import ListMessageRequest
        builder = (ListMessageRequest.builder().container_id_type(container_type)
                   .container_id(container_id).sort_type('ByCreateTimeAsc').page_size(50))
        if container_type == 'chat':
            # Inclusive overlap at second resolution; engine applies ms bound.
            builder.start_time(str(lower_ms // 1000)).end_time(str((upper_ms + 999) // 1000))
        if page_token:
            builder.page_token(page_token)
        try:
            return self._data(await self.client.im.v1.message.alist(builder.build()))
        except HistoryAPIError:
            raise
        except Exception as exc:
            code = getattr(exc, 'code', None)
            raise HistoryAPIError('sdk_error', code) from None

    async def get_message(self, message_id):
        from lark_channel.api.im.v1.model.get_message_request import GetMessageRequest
        request = GetMessageRequest.builder().message_id(message_id).user_id_type('open_id').build()
        try:
            data = self._data(await self.client.im.v1.message.aget(request))
        except HistoryAPIError:
            raise
        except Exception as exc:
            raise HistoryAPIError('sdk_error', getattr(exc, 'code', None)) from None
        items = data.get('items')
        if not isinstance(items, list) or len(items) != 1 or items[0].get('message_id') != message_id:
            raise HistoryAPIError('message_unavailable')
        return items[0]


class FeishuHistoryRecovery:
    def __init__(self, state_path, *, group_id, app_id, api, sink,
                 pending_messages=lambda: (), on_scan_begin=None, on_scan_end=None, allowed_sender_ids=None,
                 initial_lower_ms=0, overlap_ms=60000, max_pages=500,
                 max_seconds=90.0, clock_ms=lambda: int(time.time() * 1000)):
        if (not group_id.startswith('oc_') or not app_id or initial_lower_ms < 0
                or overlap_ms <= 0 or max_pages < 1 or max_seconds <= 0):
            raise ValueError('invalid history recovery bounds or identity')
        self.group_id, self.app_id, self.api, self.sink = group_id, app_id, api, sink
        self.pending_messages = pending_messages
        self.on_scan_begin = on_scan_begin
        self.on_scan_end = on_scan_end
        self.allowed_sender_ids = None if allowed_sender_ids is None else set(allowed_sender_ids)
        self.overlap_ms, self.max_pages, self.max_seconds = overlap_ms, max_pages, max_seconds
        self.clock_ms, self._lock = clock_ms, asyncio.Lock()
        state_path = Path(state_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(state_path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS identity(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                group_id TEXT NOT NULL, app_id TEXT NOT NULL, initial_lower_ms INTEGER NOT NULL,
                checkpoint_ms INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS evidence(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL, kind TEXT NOT NULL, document_json TEXT NOT NULL, sha256 TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS scans(scan_id TEXT PRIMARY KEY, result_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS delivered(evidence_id TEXT PRIMARY KEY, message_id TEXT NOT NULL,
                revision INTEGER, state TEXT NOT NULL, body_sha256 TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS threads(thread_id TEXT PRIMARY KEY, root_id TEXT);
            CREATE TABLE IF NOT EXISTS watches(message_id TEXT PRIMARY KEY);
        ''')
        self.db.execute('INSERT OR IGNORE INTO identity VALUES(1,?,?,?,?)',
                        (group_id, app_id, initial_lower_ms, initial_lower_ms))
        identity = self.db.execute('SELECT * FROM identity').fetchone()
        if (identity['group_id'], identity['app_id']) != (group_id, app_id):
            self.db.close()
            raise ValueError('history state belongs to a different app/group')
        self.initial_lower_ms = identity['initial_lower_ms']
        # Original in-progress evidence survives a killed resident. Record a
        # gap for each orphan instead of pretending its pages reached coverage.
        unfinished = self.db.execute("SELECT scan_id,document_json FROM evidence WHERE kind='begin' "
            'AND scan_id NOT IN (SELECT scan_id FROM scans) ORDER BY sequence').fetchall()
        for row in unfinished:
            original = json.loads(row['document_json'])
            original.update(status='gap', gap=dict(category='runtime_restarted', code=None))
            self._finish(original)
        self.last_result = self._last_result()

    @property
    def checkpoint_ms(self):
        return self.db.execute('SELECT checkpoint_ms FROM identity').fetchone()[0]

    def _last_result(self):
        row = self.db.execute('SELECT result_json FROM scans ORDER BY rowid DESC LIMIT 1').fetchone()
        return json.loads(row[0]) if row else None

    def close(self):
        self.db.close()

    def watch(self, message_id):
        """Persist a failed/rejected live message reference before its recheck."""
        if isinstance(message_id, str) and message_id:
            self.db.execute('INSERT OR IGNORE INTO watches VALUES(?)', (message_id,))

    def _record(self, scan_id, kind, document):
        encoded = _json(document)
        digest = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        self.db.execute('INSERT INTO evidence(scan_id,kind,document_json,sha256) VALUES(?,?,?,?)',
                        (scan_id, kind, encoded, digest))
        return digest

    def audit(self, scan_id):
        row = self.db.execute('SELECT result_json FROM scans WHERE scan_id=?', (scan_id,)).fetchone()
        entries = []
        for item in self.db.execute('SELECT * FROM evidence WHERE scan_id=? ORDER BY sequence', (scan_id,)):
            if hashlib.sha256(item['document_json'].encode('utf-8')).hexdigest() != item['sha256']:
                raise ValueError('history evidence SHA256 mismatch')
            entries.append(dict(kind=item['kind'], sha256=item['sha256'],
                                **json.loads(item['document_json'])))
        return dict(result=json.loads(row[0]) if row else None,
                    pages=[e for e in entries if e['kind'] == 'page'], evidence=entries)

    async def _deliver(self, scan_id, record):
        # Identity includes original raw body, revision and state, but never a
        # scan timestamp: replay after a crash uses the identical durable key.
        evidence_id = 'history-' + _hash(record)
        record = dict(record, evidence_id=evidence_id, scan_id=scan_id)
        self._record(scan_id, 'observation', record)
        if (record['context'] != 'pending_recheck'
                and self.db.execute('SELECT 1 FROM delivered WHERE evidence_id=?', (evidence_id,)).fetchone()):
            return
        if record['revision'] is not None:
            previous = self.db.execute('SELECT * FROM delivered WHERE message_id=? AND revision=? AND state=?',
                (record['message_id'], record['revision'], record['state'])).fetchall()
            if any(r['body_sha256'] != _hash(record['raw_message']) for r in previous):
                raise HistoryAPIError('revision_conflict')
            latest = self.db.execute('SELECT MAX(revision) FROM delivered WHERE message_id=?',
                                     (record['message_id'],)).fetchone()[0]
            if latest is not None and latest > record['revision']:
                if record['context'] == 'pending_recheck':
                    raise HistoryAPIError('revision_regressed')
                return
        try:
            accepted = await self.sink(json.loads(_json(record)))
        except asyncio.CancelledError:
            raise
        except Exception:
            raise HistoryAPIError('sink_failure') from None
        if accepted is not True:
            raise HistoryAPIError('sink_not_durable')
        self.db.execute('INSERT OR IGNORE INTO delivered VALUES(?,?,?,?,?)', (evidence_id, record['message_id'],
            record['revision'], record['state'], _hash(record['raw_message'])))

    def _base(self, message_id, **kw):
        return dict(schema=1, source='feishu_history', group_id=self.group_id,
                    app_id=self.app_id, message_id=message_id, disposition='hold', **kw)

    async def _item(self, scan_id, raw, *, query_group, upper, discover_only=False,
                    expected_id=None, expected_thread=None, expected_sender=None, expected_revision=None):
        if not isinstance(raw, dict) or not isinstance(raw.get('message_id'), str):
            raise HistoryAPIError('malformed_message')
        if expected_id and raw['message_id'] != expected_id:
            raise HistoryAPIError('message_identity_mismatch')
        actual_group = raw.get('chat_id')
        # Missing chat_id is accepted only for an authenticated chat query or
        # a thread whose root was observed in that query, never arbitrary aget.
        if actual_group != self.group_id and (actual_group or query_group != self.group_id):
            if expected_id:
                raise HistoryAPIError('message_group_mismatch')
            return
        try:
            created = int(raw.get('create_time') or 0)
            revision = int(raw.get('update_time') or created)
        except (ValueError, TypeError):
            raise HistoryAPIError('malformed_revision') from None
        if created <= 0 or revision <= 0:
            raise HistoryAPIError('malformed_revision')
        if created > upper:
            if expected_id:
                raise HistoryAPIError('message_after_upper_bound')
            return
        thread = raw.get('thread_id')
        if expected_thread and thread and thread != expected_thread:
            raise HistoryAPIError('message_thread_mismatch')
        if thread:
            self.db.execute('INSERT OR IGNORE INTO threads VALUES(?,?)',
                            (thread, raw.get('root_id') or raw['message_id']))
        if discover_only:
            return
        sender = raw.get('sender') or {}
        if sender.get('sender_type') != 'user' or not sender.get('id'):
            if expected_id:
                raise HistoryAPIError('message_sender_mismatch')
            return
        if expected_sender and sender['id'] != expected_sender:
            raise HistoryAPIError('message_sender_mismatch')
        if expected_revision is not None and revision < int(expected_revision):
            raise HistoryAPIError('revision_regressed')
        if self.allowed_sender_ids is not None and sender['id'] not in self.allowed_sender_ids:
            if expected_id:
                raise HistoryAPIError('message_sender_mismatch')
            return
        if revision > upper:
            raise HistoryAPIError('revision_after_upper_bound')
        if type(raw.get('deleted', False)) is not bool:
            raise HistoryAPIError('malformed_message')
        await self._deliver(scan_id, self._base(raw['message_id'], revision=revision,
            state='deleted' if raw.get('deleted') else 'visible', raw_message=raw,
            query_group_id=query_group, context='pending_recheck' if expected_id else 'history_list'))

    async def _pages(self, scan_id, *, container_type, container_id, lower, upper, purpose, budget):
        token, seen = None, set()
        while True:
            budget[0] += 1
            if budget[0] > self.max_pages:
                raise HistoryAPIError('page_limit')
            request = dict(container_type=container_type, container_id=container_id,
                           lower_ms=lower, upper_ms=upper, page_token=token, purpose=purpose)
            self._record(scan_id, 'request', dict(request=request))
            data = await self.api.list_messages(**request)
            self._record(scan_id, 'page', dict(request=request, response=data))
            if (not isinstance(data, dict) or not isinstance(data.get('items'), list)
                    or type(data.get('has_more')) is not bool):
                raise HistoryAPIError('malformed_page')
            for raw in data['items']:
                await self._item(scan_id, raw, query_group=self.group_id, upper=upper,
                                 discover_only=purpose == 'old_root_discovery',
                                 expected_thread=container_id if container_type == 'thread' else None)
            if not data['has_more']:
                return
            token = data.get('page_token')
            if not isinstance(token, str) or not token or token in seen:
                raise HistoryAPIError('cursor_loop')
            seen.add(token)

    async def scan(self, trigger='retry'):
        async with self._lock:
            upper = int(self.clock_ms())
            previous = self.checkpoint_ms
            lower = max(self.initial_lower_ms, previous - self.overlap_ms)
            scan_id = uuid.uuid4().hex
            result = dict(scan_id=scan_id, trigger=trigger, lower_ms=lower, upper_ms=upper,
                previous_checkpoint_ms=previous, initial_lower_ms=self.initial_lower_ms,
                status='running', limitations=['deleted_or_invisible_not_proven',
                    'historical_instructions_held_for_current_baseline'])
            self._record(scan_id, 'begin', dict(result))
            budget = [0]
            try:
                async with asyncio.timeout(self.max_seconds):
                    if upper < previous or upper < lower:
                        raise HistoryAPIError('clock_regressed')
                    pending = list(self.pending_messages())
                    references = {}
                    for item in pending:
                        if not isinstance(item, dict) or not isinstance(item.get('message_id'), str) or not item['message_id']:
                            raise HistoryAPIError('malformed_pending_reference')
                        references[item['message_id']] = dict(item)
                    for row in self.db.execute('SELECT message_id FROM watches ORDER BY message_id').fetchall():
                        references.setdefault(row[0], dict(message_id=row[0]))
                    if self.on_scan_begin is not None:
                        begin_doc = dict(scan_id=scan_id, upper_ms=upper,
                                         pending_messages=list(references.values()))
                        self._record(scan_id, 'scan_begin', begin_doc)
                        try:
                            accepted = await self.on_scan_begin(json.loads(_json(begin_doc)))
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            raise HistoryAPIError('scan_begin_failed') from None
                        if accepted is not True:
                            raise HistoryAPIError('scan_begin_not_durable')
                    # The overlap finds new group messages. Full older-root
                    # discovery finds replies to roots predating the checkpoint.
                    if lower > 0:
                        await self._pages(scan_id, container_type='chat', container_id=self.group_id,
                            lower=0, upper=lower, purpose='old_root_discovery', budget=budget)
                    await self._pages(scan_id, container_type='chat', container_id=self.group_id,
                        lower=lower, upper=upper, purpose='overlap', budget=budget)
                    for row in self.db.execute('SELECT thread_id FROM threads ORDER BY thread_id').fetchall():
                        await self._pages(scan_id, container_type='thread', container_id=row[0],
                            lower=0, upper=upper, purpose='thread', budget=budget)
                    # Rechecks are authenticated GETs, bypassing SDK stale and
                    # message-ID-only dedup. Absence is an unavailable hold.
                    gaps = []
                    for mid in sorted(references):
                        budget[0] += 1
                        if budget[0] > self.max_pages:
                            raise HistoryAPIError('page_limit')
                        self._record(scan_id, 'get_request', dict(message_id=mid))
                        try:
                            raw = await self.api.get_message(mid)
                            self._record(scan_id, 'get_response', dict(message_id=mid, response=raw))
                            await self._item(scan_id, raw, query_group=None, upper=upper, expected_id=mid,
                                expected_sender=references[mid].get('sender_id'),
                                expected_revision=references[mid].get('revision'))
                            self.db.execute('DELETE FROM watches WHERE message_id=?', (mid,))
                        except HistoryAPIError as exc:
                            if exc.category in {'sink_failure', 'sink_not_durable', 'revision_conflict'}:
                                raise
                            await self._deliver(scan_id, self._base(mid, revision=None, state='unavailable',
                                raw_message=None, api_code=exc.code, reason=exc.category, query_group_id=None,
                                context='pending_recheck'))
                            gaps.append(dict(category=exc.category, code=exc.code, message_id=mid))
                    if gaps:
                        result['gaps'] = gaps
                        raise HistoryAPIError('pending_messages_unavailable')
                result['status'] = 'covered_visible'
            except asyncio.CancelledError:
                result.update(status='gap', gap=dict(category='interrupted', code=None))
                try:
                    await self._end_scan(result)
                finally:
                    self._finish(result)
                raise
            except TimeoutError:
                result.update(status='gap', gap=dict(category='time_limit', code=None))
            except HistoryAPIError as exc:
                result.update(status='gap', gap=dict(category=exc.category, code=exc.code))
            except Exception:
                result.update(status='gap', gap=dict(category='recovery_error', code=None))
            try:
                await self._end_scan(result)
            except asyncio.CancelledError:
                self._finish(result)
                raise
            self._finish(result)
            return json.loads(_json(result))

    async def _end_scan(self, result):
        if self.on_scan_end is None:
            return
        try:
            accepted = await asyncio.wait_for(self.on_scan_end(json.loads(_json(result))),
                                               timeout=min(self.max_seconds, 10.0))
            if accepted is not True:
                raise HistoryAPIError('scan_end_not_durable')
        except asyncio.CancelledError:
            result.update(status='gap', notification_gap=dict(category='scan_end_interrupted', code=None))
            result.setdefault('gap', dict(category='interrupted', code=None))
            raise
        except Exception as exc:
            category = exc.category if isinstance(exc, HistoryAPIError) else 'scan_end_failed'
            result.update(status='gap', notification_gap=dict(category=category, code=None))
            result.setdefault('gap', dict(category=category, code=None))

    def _finish(self, result):
        # All page evidence and successful durable sink writes precede coverage.
        # Atomic terminal record + checkpoint prevent a crash from advancing
        # coverage without its audit. Failed scans leave the old lower bound.
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self._record(result['scan_id'], 'terminal', dict(result))
            self.db.execute('INSERT INTO scans VALUES(?,?)', (result['scan_id'], _json(result)))
            if result['status'] == 'covered_visible':
                self.db.execute('UPDATE identity SET checkpoint_ms=?', (result['upper_ms'],))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.last_result = json.loads(_json(result))
