"""Bounded original OS-read evidence, not authentication or source timing.

The authority-owned opener supplies one connected descriptor. This ledger reads
the OS itself; it accepts no fed bytes, verified flags, sample clocks or physical
capture claims. An empty nonblocking read bounds availability at this descriptor,
not UART/USB arrival or FPGA acquisition. See docs/live_board_receipts.md.
"""
from collections import deque
from dataclasses import asdict, dataclass
import hashlib
import json
import os
import re
import stat
import threading
from time import monotonic_ns

from . import wire, host_clock as clocks


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(name + ' must be an explicit bounded integer')
    return value


@dataclass(frozen=True)
class CaptureIdentity:
    """Main-supplied correlation labels; their shape proves no provenance."""
    operation_id: str
    request_hash: str
    tested_commit: str
    build_manifest_sha256: str
    connection_generation: int

    def __post_init__(self):
        if (type(self.operation_id) is not str or
                re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}', self.operation_id) is None):
            raise ValueError('explicit bounded operation identity required')
        for name, size in [('request_hash', 64), ('tested_commit', 40),
                           ('build_manifest_sha256', 64)]:
            value = getattr(self, name)
            if type(value) is not str or re.fullmatch('[0-9a-f]{%d}' % size, value) is None:
                raise ValueError(name + ' must be a complete lowercase digest')
        _integer(self.connection_generation, 'connection_generation', 1, (1 << 63)-1)


@dataclass(frozen=True)
class FrameReceipt:
    receipt_index: int
    raw: bytes
    stream_start: int
    stream_end: int
    availability_interval_ns: tuple | None


class ReceiptLedger:
    """One owner, one duplicated descriptor, finite reads/bytes, original frames.

    read_once can block according to the supplied descriptor. Main must provide
    nonblocking IO or a separately bounded transport supervisor before runtime
    adoption. A duplicate protects the caller's descriptor lifetime; it does not
    establish sole-reader ownership or peer identity.
    """
    def __init__(self, fd, identity, *, max_bytes, max_reads, read_size=wire.MAX_FEED,
                 host_clock=None):
        self._clock_domain = clocks._require_binding(host_clock)
        self._clock = monotonic_ns if host_clock is None else host_clock
        self._bound_domain, self._bound_clock = self._clock_domain, self._clock
        _integer(fd, 'fd', 0, (1 << 31)-1)
        if type(identity) is not CaptureIdentity:
            raise ValueError('explicit capture identity required')
        _integer(max_bytes, 'max_bytes', 1, 16 * 1024 * 1024)
        _integer(max_reads, 'max_reads', 1, 65536)
        _integer(read_size, 'read_size', 1, wire.MAX_FEED)
        mode = os.fstat(fd).st_mode
        if not (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode) or stat.S_ISCHR(mode)):
            raise ValueError('connected OS pipe/socket/device required; no replay file')
        self.identity = identity
        self._thread = threading.get_ident()
        self._fd = os.dup(fd)
        try:
            os.set_inheritable(self._fd, False)
            if os.name == 'nt':
                import msvcrt
                msvcrt.setmode(self._fd, os.O_BINARY)
        except BaseException:
            os.close(self._fd)
            raise
        self._max_bytes, self._max_reads, self._read_size = max_bytes, max_reads, read_size
        self._closed = self._eof = self._failed = False
        self._bytes = 0
        self._reads, self._frames, self._spans = [], [], []
        self._claimed = set()
        self._decoder = wire.FrameDecoder()
        self._tail = deque(maxlen=wire.MAX_FRAME)
        self._empty_lower = None
        self._last_frame_end = 0

    def _owner(self):
        if threading.get_ident() != self._thread:
            raise ValueError('original receiving owner thread required')

    @property
    def clock_domain(self):
        return self._clock_domain

    def _active(self):
        self._owner()
        if self._clock_domain is not self._bound_domain or self._clock is not self._bound_clock:
            self._failed = True
        if self._closed or self._failed:
            raise ValueError('capture is closed or failed')

    def read_once(self):
        """Perform one actual OS read, retaining all bytes including noise/CRC failures."""
        self._active()
        if self._eof or self._bytes >= self._max_bytes or len(self._reads) >= self._max_reads:
            raise ValueError('EOF or original capture budget reached; no extra read')
        try:
            begin = self._clock()
        except BaseException:
            self._failed = True
            raise
        index = len(self._reads)
        start = self._bytes
        # Reserve the attempt and close reentry before the side-effect boundary.
        # An interrupted read may have consumed bytes without returning them.
        self._failed = True
        row = dict(kind='started_unknown', raw_hex=None, returned_bytes=None, stream_start=start,
            raw_read_call_bracket_ns=[begin,None], read_call_interval_ns=None,
            preceding_empty_lower_ns=self._empty_lower)
        self._reads.append(row)
        try:
            error = None
            try:
                raw = os.read(self._fd, min(self._read_size, self._max_bytes-self._bytes))
            except BlockingIOError:
                raw, kind = b'', 'empty'
            except OSError as exc:
                raw, kind, error = b'', 'error', exc
            else:
                kind = 'data' if raw else 'eof'
            row.update(kind=kind, raw_hex=raw.hex(), returned_bytes=len(raw))
            if error is not None: row['errno'] = error.errno
            self._bytes += len(raw)  # Persist returned bytes before post-read stamping.
            if kind == 'eof':
                self._eof = True
            try:
                end = self._clock()
            except BaseException as exc:
                row['clock_error_type'] = type(exc).__name__
                raise
            row['raw_read_call_bracket_ns'][1] = end
            if self._clock_domain is None:
                row['read_call_interval_ns'] = [begin,end]  # Legacy diagnostic semantics only.
            if error is not None:
                raise error
            if kind == 'empty':
                self._empty_lower = begin if self._clock_domain is None else None
                events = ()
            else:
                events = self._scan(raw, index, start) if raw else ()
        except BaseException as exc:
            self._empty_lower = None
            row['failure_type'] = type(exc).__name__
            raise
        self._failed = False  # Only a completely recorded read can reopen the next entry.
        return events

    def _locate(self, frame):
        """Locate the earliest original recovered packet after the prior receipt.

        Decoder recovery can emit an embedded packet several bytes after that
        packet ended. Its original end is not necessarily the current tail end.
        """
        count = wire.HEADER.size + len(frame.payload) + 2
        tail = list(self._tail)
        for start in range(len(tail)-count+1):
            if tail[start][1] < self._last_frame_end:
                continue
            original = tail[start:start+count]
            packet = bytes(item[0] for item in original)
            try:
                decoded = wire.decode(packet)
            except ValueError:
                continue
            if decoded == frame:
                return original, packet
        raise ValueError('original recovered packet provenance mismatch')

    def _scan(self, raw, index, start):
        events = []
        for offset, byte in enumerate(raw):
            self._tail.append((byte, start+offset, index, offset))
            for frame in self._decoder.feed(bytes((byte,))):
                original, packet = self._locate(frame)
                # Delayed recovery cannot borrow a later read's empty-queue anchor.
                last_read = self._reads[original[-1][2]]
                lower = last_read['preceding_empty_lower_ns']
                interval = (None if lower is None or last_read['read_call_interval_ns'] is None else
                            (lower, last_read['read_call_interval_ns'][1]))
                event = FrameReceipt(len(self._frames), packet, original[0][1],
                                     original[-1][1]+1, interval)
                spans = []
                for _, _, read_index, read_offset in original:
                    if (spans and spans[-1]['read_index'] == read_index and
                            spans[-1]['offset'] + spans[-1]['length'] == read_offset):
                        spans[-1]['length'] += 1
                    else:
                        spans.append({'read_index': read_index, 'offset': read_offset, 'length': 1})
                self._frames.append(event)
                self._spans.append(spans)
                self._last_frame_end = event.stream_end
                events.append(event)
        return tuple(events)

    def _original(self, event):
        if (type(event) is not FrameReceipt or type(event.receipt_index) is not int or
                not 0 <= event.receipt_index < len(self._frames) or
                self._frames[event.receipt_index] is not event):
            raise ValueError('original local receipt required; copied/loaded records cannot be claimed')

    def claim_board_response(self, event, *, context):
        """Single-use schema translation, never an authenticated provider result.

        The caller must separately establish peer/BOOT/context authenticity and
        the timing meaning of this descriptor's availability bounds. TELEM/EVENT
        are not board heartbeats; this API cannot manufacture sample intervals.
        """
        self._active()
        self._original(event)
        if event.receipt_index in self._claimed:
            raise ValueError('original receipt already claimed')
        if event.availability_interval_ns is None:
            raise ValueError('descriptor availability unknown; read-call interval is insufficient')
        self._claimed.add(event.receipt_index)  # Failed validation cannot recycle an event.
        from . import host_envelope
        lower, upper = event.availability_interval_ns
        document = dict(schema_version=1, kind='board_response', context=context,
            receipt_interval_ns=dict(lower_ns=lower, upper_ns=upper),
            wire_frame_hex=event.raw.hex(), timing_record_sha256=None,
            physical_capture_record_sha256=None)
        raw = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        host_envelope.validate_message(raw, producer='hardware_bridge',
            consumer='world_authority', context=context, now_ns=self._clock())
        return raw

    def snapshot(self):
        """Detached diagnostic export, including rejected bytes and unknown timing."""
        self._owner()
        frames = []
        for event, spans in zip(self._frames, self._spans):
            frames.append(dict(receipt_index=event.receipt_index, raw_hex=event.raw.hex(),
                raw_sha256=hashlib.sha256(event.raw).hexdigest(), stream_start=event.stream_start,
                stream_end=event.stream_end, availability_interval_ns=event.availability_interval_ns,
                sample_interval_ns=None, physical_capture_record_sha256=None,
                claimed=event.receipt_index in self._claimed, spans=spans))
        value = dict(schema=1, identity=asdict(self.identity), transport='os_descriptor',
            host_clock=clocks._description(self._bound_domain),
            clock_binding_continuity=(self._clock_domain is self._bound_domain
                                      and self._clock is self._bound_clock),
            provenance='main-supplied correlation labels; peer and BOOT not authenticated here',
            availability_scope='descriptor queue only; not UART/USB arrival or FPGA sample time',
            closed=self._closed, eof=self._eof, failed=self._failed,
            budgets=dict(max_bytes=self._max_bytes, max_reads=self._max_reads, read_size=self._read_size),
            bytes_read=self._bytes, reads=self._reads, frames=frames,
            decoder=dict(buffered_bytes=self._decoder.buffered_bytes,
                rejected_candidates=self._decoder.rejected_candidates,
                discarded_bytes=self._decoder.discarded_bytes))
        return json.loads(json.dumps(value, ensure_ascii=False))

    def close(self):
        """Close the owned duplicate once; retain evidence for explicit export."""
        self._owner()
        if not self._closed:
            self._closed = True
            os.close(self._fd)


__all__ = ['CaptureIdentity', 'FrameReceipt', 'ReceiptLedger']
