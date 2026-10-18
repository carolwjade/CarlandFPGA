"""Durable history evidence and scoped claim holds; never execute old messages."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _content(raw):
    content = raw.get('body', {}).get('content')
    try:
        return json.loads(content) if isinstance(content, str) else content
    except (ValueError, TypeError):
        return None


def _same_message(observation, row):
    raw, envelope = observation['raw_message'], row['envelope']
    if (observation['state'] != 'visible' or observation['revision'] != row['revision']
            or raw['sender']['id'] != envelope['sender']):
        return False
    previous = envelope['payload'].get('feishu', {})
    original = previous.get('raw_message', {}).get('content')
    if original is not None:
        try:
            old = json.loads(original) if isinstance(original, str) else original
            return old == _content(raw)
        except (ValueError, TypeError):
            return False
    return (raw.get('message_type') == 'text'
            and _content(raw) == {'text': previous.get('body_text')})


def _addressed_elsewhere(raw, node_id):
    content = _content(raw)
    text = content.get('text', '') if isinstance(content, dict) else ''
    match = re.match(r'^\s*(?:/fpga\s+([abc])\b|astra-([abc])\s*[:：])', text, re.I)
    if match:
        return (match.group(1) or match.group(2)).upper() != node_id
    names = {match.group(1).upper() for mention in raw.get('mentions', [])
             if isinstance(mention, dict)
             for match in [re.fullmatch(r'FPGA\s+(?:Astra|DeepSeek)\s+([ABC])',
                                       str(mention.get('name', '')), re.I)] if match}
    return len(names) == 1 and node_id not in names


class DesktopHistory:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS scans(owner TEXT NOT NULL, scan_id TEXT NOT NULL,
                status TEXT NOT NULL, document_json TEXT NOT NULL, PRIMARY KEY(owner,scan_id));
            CREATE TABLE IF NOT EXISTS observations(observation_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL, scan_id TEXT NOT NULL, document_json TEXT NOT NULL,
                actionable INTEGER NOT NULL, received_at TEXT NOT NULL, batch_id TEXT);
            CREATE TABLE IF NOT EXISTS holds(owner TEXT NOT NULL, message_id TEXT NOT NULL,
                scan_id TEXT NOT NULL, through_revision INTEGER NOT NULL, reason TEXT NOT NULL,
                original_revision INTEGER NOT NULL,
                PRIMARY KEY(owner,message_id));
            CREATE TABLE IF NOT EXISTS batches(batch_id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                document_json TEXT NOT NULL, receipt_id TEXT);
            CREATE TABLE IF NOT EXISTS current_scans(owner TEXT PRIMARY KEY, scan_id TEXT NOT NULL);
        ''')
        if 'original_revision' not in {row['name'] for row in self.db.execute('PRAGMA table_info(holds)')}:
            self.db.execute('ALTER TABLE holds ADD COLUMN original_revision INTEGER NOT NULL DEFAULT 0')
            self.db.execute('UPDATE holds SET original_revision=through_revision')
        # The sole resident creates this after the original runtime's stop fence.
        # Preserve evidence from an interrupted scan and its unresolved holds.
        with self.db:
            self.db.execute("UPDATE scans SET status='interrupted' WHERE status='running'")

    @staticmethod
    def _owner(binding):
        return _hash(binding.values())

    def require_recheck(self, binding, receipts):
        """Persist a new gate epoch without claiming a remote scan occurred."""
        owner, gate = self._owner(binding), 'verification-' + uuid.uuid4().hex
        with self.db:
            self.db.execute('INSERT INTO current_scans VALUES(?,?) ON CONFLICT(owner) '
                            'DO UPDATE SET scan_id=excluded.scan_id', (owner, gate))
            for row in receipts:
                self._hold_recheck(owner, gate, row)
        return True

    def _hold_recheck(self, owner, scan, row):
        self.db.execute('''INSERT INTO holds VALUES(?,?,?,?,?,?)
            ON CONFLICT(owner,message_id) DO UPDATE SET scan_id=excluded.scan_id,
            through_revision=MAX(holds.through_revision,excluded.through_revision),
            original_revision=CASE WHEN holds.reason='history_rechecking'
                THEN excluded.original_revision ELSE holds.original_revision END ''',
            (owner, row['platform_message_id'], scan, row['revision'], 'history_rechecking', row['revision']))

    def begin(self, document, binding, receipts):
        binding.require_active()
        scan = document.get('scan_id')
        if (not isinstance(scan, str) or not scan or type(document.get('upper_ms')) is not int
                or not isinstance(document.get('pending_messages'), list)):
            raise ValueError('invalid history scan start')
        owner = self._owner(binding)
        known = {row['platform_message_id']: row for row in receipts}
        with self.db:
            prior = self.db.execute('SELECT status,document_json FROM scans WHERE owner=? AND scan_id=?',
                                    (owner, scan)).fetchone()
            current = self.db.execute('SELECT scan_id FROM current_scans WHERE owner=?', (owner,)).fetchone()
            if prior:
                if (not current or current['scan_id'] != scan or prior['status'] != 'running'
                        or prior['document_json'] != _json(document)):
                    raise ValueError('history scan cannot reclaim a newer verification epoch')
                return True
            self.db.execute('INSERT INTO scans VALUES(?,?,?,?)',
                            (owner, scan, 'running', _json(document)))
            self.db.execute('INSERT INTO current_scans VALUES(?,?) ON CONFLICT(owner) '
                            'DO UPDATE SET scan_id=excluded.scan_id', (owner, scan))
            for reference in document['pending_messages']:
                row = known.get(reference.get('message_id'))
                if row is None:
                    continue  # A live completion may have occurred before this snapshot.
                if reference.get('revision') != row['revision']:
                    continue  # A newer real-time revision is outside this reference.
                self._hold_recheck(owner, scan, row)
        return True

    def block_reason(self, binding, message_id, revision):
        row = self.db.execute('SELECT reason,through_revision FROM holds WHERE owner=? AND message_id=?',
                              (self._owner(binding), message_id)).fetchone()
        return row['reason'] if row and revision <= row['through_revision'] else None

    def observe(self, document, binding, receipts, *, app_id, allowed_sender_ids):
        binding.require_active()
        if (not isinstance(document, dict) or document.get('schema') != 1
                or document.get('source') != 'feishu_history'
                or document.get('app_id') != app_id or not app_id
                or document.get('group_id') != binding.group_id
                or document.get('disposition') != 'hold'
                or document.get('state') not in {'visible', 'deleted', 'unavailable'}
                or not isinstance(document.get('message_id'), str) or not document['message_id']
                or not isinstance(document.get('scan_id'), str) or not document['scan_id']):
            raise ValueError('invalid authenticated history observation')
        raw, revision = document.get('raw_message'), document.get('revision')
        if document['state'] == 'unavailable':
            if raw is not None or revision is not None:
                raise ValueError('unavailable history must not fabricate a body or revision')
        else:
            if not isinstance(raw, dict):
                raise ValueError('visible history requires its actual API message')
            sender = raw.get('sender', {})
            if (raw.get('message_id') != document['message_id']
                    or (raw.get('chat_id') != binding.group_id and (raw.get('chat_id')
                        or document.get('query_group_id') != binding.group_id))
                    or sender.get('sender_type') != 'user' or not sender.get('id')
                    or (allowed_sender_ids is not None and sender['id'] not in allowed_sender_ids)
                    or type(revision) is not int or revision < 1
                    or int(raw.get('update_time') or raw.get('create_time') or 0) != revision
                    or type(raw.get('deleted', False)) is not bool
                    or raw.get('deleted', False) != (document['state'] == 'deleted')):
                raise ValueError('history source, revision or tombstone mismatch')
        owner, scan, message_id = self._owner(binding), document['scan_id'], document['message_id']
        current = [row for row in receipts if row['platform_message_id'] == message_id]
        latest = max(current, key=lambda row: row['revision']) if current else None
        unchanged = latest is not None and _same_message(document, latest)
        older = latest is not None and revision is not None and revision < latest['revision']
        actionable = (not unchanged and not older and (latest is not None or
                      (raw is not None and not _addressed_elsewhere(raw, binding.node_id))))
        identity = {key: value for key, value in document.items()
                    if key not in {'scan_id', 'context', 'evidence_id'}}
        observation_id = 'histobs-' + _hash([owner, identity])
        with self.db:
            if not self.db.execute('SELECT 1 FROM scans WHERE owner=? AND scan_id=?', (owner, scan)).fetchone():
                raise ValueError('history observation scan was not durably begun')
            gate = self.db.execute('SELECT scan_id FROM current_scans WHERE owner=?', (owner,)).fetchone()
            gate_id = gate['scan_id'] if gate else None
            self.db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,NULL)',
                (observation_id, owner, scan, _json(document), int(actionable), _now()))
            if unchanged and document.get('context') == 'pending_recheck' and scan == gate_id:
                self.db.execute("DELETE FROM holds WHERE owner=? AND message_id=? AND scan_id=? "
                    "AND through_revision<=? AND (reason='history_rechecking' OR original_revision<?)",
                    (owner, message_id, scan, latest['revision'], latest['revision']))
            elif latest and actionable:
                reason = 'history_' + (document['state'] if document['state'] != 'visible' else 'changed')
                self.db.execute('''INSERT INTO holds VALUES(?,?,?,?,?,?)
                    ON CONFLICT(owner,message_id) DO UPDATE SET scan_id=excluded.scan_id,
                    through_revision=MAX(holds.through_revision,excluded.through_revision),reason=excluded.reason''',
                    (owner, message_id, gate_id or scan, max(latest['revision'], revision or 0), reason, latest['revision']))
        return True

    def finish(self, document, binding):
        owner, scan = self._owner(binding), document.get('scan_id')
        if not isinstance(scan, str) or not scan:
            raise ValueError('history completion needs scan identity')
        if not self.db.execute('SELECT 1 FROM scans WHERE owner=? AND scan_id=?', (owner,scan)).fetchone():
            raise ValueError('history scan was not durably begun')
        with self.db:
            self.db.execute('UPDATE scans SET status=?,document_json=? WHERE owner=? AND scan_id=?',
                (str(document.get('status') or 'gap'), _json(document), owner, scan))
        return True

    def pending_batches(self, binding):
        owner = self._owner(binding)
        with self.db:
            scans = self.db.execute("SELECT scan_id FROM scans WHERE owner=? AND status<>'running'",
                                    (owner,)).fetchall()
            for scan in scans:
                rows = self.db.execute('SELECT observation_id,received_at FROM observations WHERE '
                    'owner=? AND scan_id=? AND actionable=1 AND batch_id IS NULL ORDER BY rowid',
                    (owner,scan['scan_id'])).fetchall()
                if not rows:
                    continue
                ids = [row['observation_id'] for row in rows]
                batch_id = 'histbatch-' + _hash([owner, ids])
                payload = dict(batch_id=batch_id, scan_id=scan['scan_id'], observation_ids=ids,
                               created_at=rows[0]['received_at'], disposition='review_only')
                self.db.execute('INSERT OR IGNORE INTO batches VALUES(?,?,?,NULL)',
                                (batch_id,owner,_json(payload)))
                self.db.executemany('UPDATE observations SET batch_id=? WHERE observation_id=?',
                                    [(batch_id,item) for item in ids])
        return [json.loads(row['document_json']) for row in self.db.execute(
            'SELECT document_json FROM batches WHERE owner=? AND receipt_id IS NULL ORDER BY rowid', (owner,))]

    def mark_notified(self, batch_id, binding, receipt_id):
        owner = self._owner(binding)
        row = self.db.execute('SELECT receipt_id FROM batches WHERE batch_id=? AND owner=?',
                              (batch_id,owner)).fetchone()
        if row is None or row[0] not in {None, receipt_id}:
            raise ValueError('immutable history batch notification conflict')
        with self.db:
            self.db.execute('UPDATE batches SET receipt_id=? WHERE batch_id=? AND owner=?',
                            (receipt_id,batch_id,owner))

    def inspect_batch(self, batch_id, binding, *, offset=0, limit=100):
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('invalid history evidence page')
        row = self.db.execute('SELECT document_json FROM batches WHERE batch_id=? AND owner=?',
                              (batch_id,self._owner(binding))).fetchone()
        if row is None:
            raise ValueError('history batch does not belong to current owner generation')
        batch = json.loads(row[0])
        ids = batch['observation_ids'][offset:offset + limit]
        records = [json.loads(self.db.execute('SELECT document_json FROM observations WHERE observation_id=?',
                                             (item,)).fetchone()[0]) for item in ids]
        return {'batch': batch, 'rows': records,
                'next_offset': offset + limit if offset + limit < len(batch['observation_ids']) else None}

    def health(self, binding):
        owner = self._owner(binding)
        return {'held_message_count': self.db.execute('SELECT COUNT(*) FROM holds WHERE owner=?', (owner,)).fetchone()[0],
            'scans': [dict(row) for row in self.db.execute('SELECT scan_id,status FROM scans WHERE owner=? ORDER BY rowid DESC LIMIT 5', (owner,))]}

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
