"""Bounded trusted-Root file transport for presentation only; no process launch.

Correlation is not source authentication. Neither ACK nor native pose feeds the
motion authority, authorizes an action, authenticates BOOT, or proves H12.
"""
import json
import os
from pathlib import Path
import secrets
import time

from ...simulation.authority.renderer_frame import validate_frame

MAX_BYTES = 4096


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('nonfinite JSON constant')


def _read(path):
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
    except FileNotFoundError:
        return None
    if len(raw) > MAX_BYTES:
        raise ValueError('renderer record too large')
    doc = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                     parse_constant=_reject_constant)
    if type(doc) is not dict:
        raise ValueError('renderer record must be an object')
    return doc


def _publish(path, document, limit=MAX_BYTES):
    raw = json.dumps(document, allow_nan=False, ensure_ascii=False,
                     separators=(',', ':')).encode('utf-8')
    if len(raw) > limit:
        raise ValueError('renderer record too large')
    temp = path.with_suffix('.tmp')
    with temp.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    # Atomic no-overwrite publication on the required local hardlink-capable
    # filesystem. Failure is preserved, never replaced/retried by this session.
    os.link(temp, path)
    temp.unlink()


class RendererSession:
    def __init__(self, path, run_id, *, max_messages=16, lifetime_ms=8000):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError('explicit absolute new owned directory required')
        if (type(run_id) is not str or not 1 <= len(run_id) <= 128
                or any(ord(c) < 32 or ord(c) == 127 for c in run_id)):
            raise ValueError('bounded run identifier required')
        if type(max_messages) is not int or not 2 <= max_messages <= 16:
            raise ValueError('message count must be 2..16 including close')
        if type(lifetime_ms) is not int or not 1 <= lifetime_ms <= 8000:
            raise ValueError('lifetime must be 1..8000 ms')
        self.path = path.resolve()
        self.run_id = run_id
        self.nonce = secrets.token_hex(16)
        self.max_messages = max_messages
        self._deadline = time.monotonic() + lifetime_ms / 1000
        self._next = 1
        self._pending = None
        self._failed = False
        self._closing = False
        self.path.mkdir()  # Never adopt, clear, or reuse an earlier directory.
        _publish(self.path / 'bootstrap.json', {'schema': 1, 'run_id': run_id,
                 'nonce': self.nonce, 'max_messages': max_messages,
                 'lifetime_ms': lifetime_ms}, 1024)

    def _active(self):
        if self._failed:
            raise RuntimeError('renderer session retired after unknown/invalid result')
        if time.monotonic() >= self._deadline:
            self._failed = True
            raise TimeoutError('renderer session lifetime expired')

    def _correlated(self, doc):
        if doc.get('nonce') != self.nonce or doc.get('run_id') != self.run_id:
            raise ValueError('foreign renderer session record')

    def _send(self, kind, frame=None):
        self._active()
        if self._closing or self._pending is not None:
            raise RuntimeError('closed or outstanding renderer message')
        if self._next > self.max_messages or (kind == 'frame' and self._next == self.max_messages):
            raise RuntimeError('renderer message budget exhausted; reserve final close')
        sequence = self._next
        doc = {'sequence': sequence, 'nonce': self.nonce,
               'run_id': self.run_id, 'kind': kind}
        if kind == 'frame':
            doc['frame'] = frame
        self._next += 1
        self._pending = (sequence, kind, frame)
        self._closing = kind == 'close'
        try:
            _publish(self.path / f'frame-{sequence:06d}.json', doc)
        except BaseException:
            self._failed = True  # Publication outcome may be unknown; no retry.
            raise
        return sequence

    def publish(self, frame):
        """Publish a copied whitelist frame, normally frame_from_executor(owner).

        Run/revision ordering is additionally enforced by the native renderer;
        structural validation here grants no original-command authority.
        """
        return self._send('frame', validate_frame(frame))

    def close(self):
        return self._send('close')

    def read_ready(self):
        self._active()
        try:
            doc = _read(self.path / 'ready.json')
            if doc is None:
                return None
            if set(doc) != {'nonce', 'run_id', 'asset', 'gates_closed'}:
                raise ValueError('ready whitelist mismatch')
            self._correlated(doc)
            if type(doc['asset']) is not dict or doc['gates_closed'] is not True:
                raise ValueError('renderer readiness/control gates invalid')
            return doc
        except BaseException:
            self._failed = True
            raise

    def read_ack(self):
        self._active()
        if self._pending is None:
            return None
        sequence, kind, frame = self._pending
        try:
            doc = _read(self.path / f'ack-{sequence:06d}.json')
            if doc is None:
                return None
            if set(doc) != {'sequence', 'nonce', 'run_id', 'accepted', 'error', 'native', 'gates_closed'}:
                raise ValueError('ACK whitelist mismatch')
            self._correlated(doc)
            if type(doc['sequence']) is not int or doc['sequence'] != sequence:
                raise ValueError('ACK sequence mismatch')
            if (type(doc['accepted']) is not bool or type(doc['error']) is not str
                    or len(doc['error']) > 128 or doc['gates_closed'] is not True):
                raise ValueError('ACK status/control gates invalid')
            native = doc['native']
            if native != {}:
                native = validate_frame(native)
                if native['run_id'] != self.run_id:
                    raise ValueError('native run mismatch')
            if doc['accepted'] and kind == 'frame':
                if (not native or native['authority_revision'] != frame['authority_revision']
                        or native['pose_revision'] != frame['pose_revision']
                        or native['stopped'] != frame['stopped']):
                    raise ValueError('native ACK revision/status mismatch')
            self._pending = None
            return doc
        except BaseException:
            self._failed = True
            raise

    def read_terminal(self):
        """Bounded terminal observation remains readable after the send deadline."""
        doc = _read(self.path / 'terminal.json')
        if doc is None:
            return None
        if set(doc) != {'nonce', 'run_id', 'status', 'last_sequence', 'native', 'gates_closed'}:
            raise ValueError('terminal whitelist mismatch')
        self._correlated(doc)
        if (doc['status'] not in ('closed', 'timeout', 'message_limit', 'ack_failed', 'gates_open')
                or type(doc['last_sequence']) is not int
                or not 0 <= doc['last_sequence'] <= self.max_messages
                or type(doc['gates_closed']) is not bool):
            raise ValueError('terminal status invalid')
        if doc['native'] != {}:
            native = validate_frame(doc['native'])
            if native['run_id'] != self.run_id:
                raise ValueError('native run mismatch')
        return doc
