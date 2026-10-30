"""Explicit finite serial raw transport; never inference/BOOT/motion authority.

One complete observed frame is a transport boundary, not an authenticated model
completion or a promise of future pipe quiescence. The production provider must
still verify its original package, invocation identity, semantics and times.
"""
from dataclasses import dataclass, asdict
import hashlib
import re

_KEY = object()
_MAX_NS = (1 << 63)-1
_MAX_OUTPUT = 16*1024*1024


def _uint(value, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('strict finite serial transport integer required')
    return value


def _frame(raw, *, request=False):
    limit = 16384 if request else 16388
    if type(raw) is not bytes or not 5 <= len(raw) <= limit:
        raise ValueError('one bounded nonempty complete frame required')
    size = int.from_bytes(raw[:4], 'little')
    if not 1 <= size <= 16384 or size+4 != len(raw):
        raise ValueError('partial, extra or multiple frames are not a serial boundary')
    return raw


def _settled(row):
    if (type(row) is not dict or row.get('issued') is not True
            or row.get('pending') is not False or row.get('os_result_observed') is not True
            or row.get('cancel_attempted') is not False
            or row.get('unknown_consumption') is not False
            or type(row.get('winerror')) is not int or row['winerror'] != 0):
        raise ValueError('only an uncancelled known successful original IO result may seal')
    bracket = row.get('raw_call_bracket_ns')
    if type(bracket) is not list or len(bracket) != 2:
        raise ValueError('original raw call bracket required')
    a,b = (_uint(x, 0, _MAX_NS) for x in bracket)
    if a > b:
        raise ValueError('original call bracket reversed')
    return a,b


def _raw_frame_from_snapshot(snapshot, request_raw):
    """Pure consistency check. A caller dictionary authenticates nothing."""
    _frame(request_raw, request=True)
    if (type(snapshot) is not dict or type(snapshot.get('schema')) is not int or snapshot['schema'] != 2
            or any(snapshot.get(k) is not False for k in
                ('failed','journal_failed','eof','zero_read_stop','unknown_consumption'))):
        raise ValueError('healthy original raw transcript required')
    dispatch = snapshot.get('dispatch');_,previous = _settled(dispatch)
    if (type(dispatch.get('bytes_written')) is not int
            or dispatch['bytes_written'] != len(request_raw)
            or type(dispatch.get('requested_bytes')) is not int
            or dispatch['requested_bytes'] != len(request_raw)
            or dispatch.get('raw_hex') != request_raw.hex()):
        raise ValueError('exact original fully written request required')
    reads = snapshot.get('reads')
    if type(reads) is not list or not 1 <= len(reads) <= 65536:
        raise ValueError('bounded original read sequence required')
    chunks=[];offset=0
    for row in reads:
        begin,previous_end = _settled(row)
        if begin < previous:
            raise ValueError('original raw call order reversed')
        previous=previous_end
        count = _uint(row.get('returned_bytes'), 1, 8192)
        if (type(row.get('stream_start')) is not int or row['stream_start'] != offset
                or type(row.get('stream_end')) is not int or row['stream_end'] != offset+count
                or type(row.get('raw_hex')) is not str or len(row['raw_hex']) != count*2
                or any(x not in '0123456789abcdef' for x in row['raw_hex'])):
            raise ValueError('original read bytes/offsets disagree')
        offset += count
        if offset > 16388:
            raise ValueError('one frame byte limit exceeded')
        chunks.append(bytes.fromhex(row['raw_hex']))
    if type(snapshot.get('bytes_read')) is not int or snapshot['bytes_read'] != offset:
        raise ValueError('original total output count disagrees')
    return _frame(b''.join(chunks))


@dataclass(frozen=True)
class SerialInvocationLimits:
    """Trusted finite policy chosen before the first request, not a grant."""
    max_invocations: int
    max_total_request_bytes: int
    max_total_output_bytes: int
    max_total_reads: int

    def __post_init__(self):
        _uint(self.max_invocations, 2, 32)
        _uint(self.max_total_request_bytes, 1, 32*16384)
        _uint(self.max_total_output_bytes, 1, _MAX_OUTPUT)
        _uint(self.max_total_reads, 1, 65536)


class _Ticket:
    def __init__(self, identity, request_raw, journal_name, options, stream_start):
        self.identity,self.request_raw,self.journal_name = identity,request_raw,journal_name
        self.options,self.stream_start = options,stream_start
        self.record = self.sealed_frame = None
        self.write_reserved = self.sealing = False
        self.observed_qpc_ns = None


class _SerialLedger:
    """Pure bounded sequencing policy; no native/capability authentication."""
    def __init__(self, limits):
        if type(limits) is not SerialInvocationLimits:
            raise ValueError('exact explicit serial limits required')
        self.limits,self.tickets = limits,[]
        self.request_bytes = self.output_reserved = self.reads_reserved = self.observed_bytes = 0
        self.failed=False

    def _current(self, ticket):
        if self.failed or not self.tickets or self.tickets[-1] is not ticket:
            raise ValueError('current original serial ticket required')

    def reserve(self, identity, *, request_raw, journal_name, max_output_bytes,
                max_reads, read_size, io_deadline_ns):
        from ...integration.cpu_invocation_transcript import InvocationIdentity
        try:
            if self.failed or len(self.tickets) >= self.limits.max_invocations:
                raise ValueError('serial lifetime count exhausted or failed')
            if type(identity) is not InvocationIdentity:
                raise ValueError('exact original invocation labels required')
            _frame(request_raw, request=True)
            _uint(max_output_bytes, 1, _MAX_OUTPUT);_uint(max_reads, 1, 65536)
            _uint(read_size, 1, 8192);_uint(io_deadline_ns, 1, _MAX_NS)
            if (type(journal_name) is not str
                    or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}',journal_name) is None
                    or journal_name.endswith('.') or journal_name.split('.')[0].upper() in
                    {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(10)),*(f'LPT{i}' for i in range(10))}
                    or any(t.journal_name.casefold()==journal_name.casefold() for t in self.tickets)):
                raise ValueError('new original single journal basename required')
            if self.tickets:
                old=self.tickets[-1]
                if old.sealed_frame is None or identity.invocation_id != old.identity.invocation_id+1:
                    raise ValueError('previous complete frame and next original invocation required')
                if any(getattr(identity,k)!=getattr(old.identity,k) for k in
                    ('operation_id','request_hash','tested_commit','package_manifest_sha256',
                     'run_id','actor_instance_id')):
                    raise ValueError('serial operation/package/actor identity changed')
            elif identity.invocation_id != 1:
                raise ValueError('fresh serial operation begins with invocation1')
            if (self.request_bytes+len(request_raw)>self.limits.max_total_request_bytes
                    or self.output_reserved+max_output_bytes>self.limits.max_total_output_bytes
                    or self.reads_reserved+max_reads>self.limits.max_total_reads):
                raise ValueError('aggregate serial budgets exhausted')
            ticket=_Ticket(identity,request_raw,journal_name,dict(max_output_bytes=max_output_bytes,
                max_reads=max_reads,read_size=read_size,io_deadline_ns=io_deadline_ns),self.observed_bytes)
            self.tickets.append(ticket)  # Retained before record/journal/native acquisition.
            self.request_bytes+=len(request_raw);self.output_reserved+=max_output_bytes
            self.reads_reserved+=max_reads
            return ticket
        except BaseException:
            self.failed=True
            raise

    def claim_write(self, ticket):
        self._current(ticket)
        if ticket.write_reserved or ticket.sealed_frame is not None:
            self.failed=True
            raise ValueError('original serial write already reserved; no replay')
        ticket.write_reserved=True

    def seal(self, ticket, raw):
        self._current(ticket);_frame(raw)
        if (not ticket.write_reserved or ticket.sealed_frame is not None
                or len(raw)>ticket.options['max_output_bytes']):
            self.failed=True
            raise ValueError('original written request and bounded new response frame required')
        ticket.sealed_frame=raw
        self.observed_bytes+=len(raw)


class _OriginalSerialSeries:
    def __init__(self, key, owner, limits):
        if key is not _KEY:
            raise ValueError('original actor issue path required')
        self.owner,self.io,self.ledger=owner,owner._pending_io,_SerialLedger(limits)

    def _check(self):
        from .actor_owner import ActorOwner
        from .actor_pipe_io import _ActorPipeIO
        owner=self.owner
        if (type(owner) is not ActorOwner or owner._invocation_series is not self
                or type(self.io) is not _ActorPipeIO or owner._pending_io is not self.io
                or self.io.actor is not owner or not owner._registry._contains(owner)
                or owner._cleanup_attempted or self.io.teardown_started
                or self.io.quarantined or self.io.cleanup_consumed or self.ledger.failed):
            raise ValueError('same healthy original retained serial actor required')
        self.io.continuity()

    def _known_io(self, record):
        if not self.io.all_settled:
            raise ValueError('original pending IO cannot advance serial stream')
        for op in self.io.operations:
            if op.kind=='connect':continue
            if (not op.issued or not op.issue_returned or not op.settled or op.unknown
                    or op.cancel_attempted or op.error!=0 or op.count is None
                    or op.record is None or op.row is None):
                raise ValueError('cancelled, unissued or uncertain original IO cannot advance')
        ops=[op for op in self.io.operations if op.record is record]
        writes=[op for op in ops if op.kind=='write'];reads=[op for op in ops if op.kind=='read']
        if (len(writes)!=1 or writes[0].row is not record.dispatch
                or len(reads)!=len(record.reads)
                or any(op.row is not row for op,row in zip(reads,record.reads))):
            raise ValueError('original transcript rows differ from retained OS operations')

    def reserve(self, identity, **options):
        self._check()
        if self.ledger.tickets:
            old=self.ledger.tickets[-1]
            if (old.record is not self.owner._invocation or old.sealed_frame is None
                    or old.record._failed or not old.record._close_attempted
                    or old.record._close_error is not None):
                raise ValueError('original prior raw frame/journal must be closed')
            self._known_io(old.record)
        return self.ledger.reserve(identity,**options)

    def retain(self, ticket, record):
        self._check();self.ledger._current(ticket)
        if ticket.record is not None or self.owner._invocation is not record or record.owner is not self.owner:
            raise ValueError('one original retained record per ticket required')
        ticket.record=record

    def claim_write(self, record):
        self._check();ticket=self.ledger.tickets[-1]
        if ticket.record is not record or self.owner._invocation is not record:
            raise ValueError('original serial record changed')
        self.ledger.claim_write(ticket)

    def seal_current(self):
        self._check();owner=self.owner;ticket=self.ledger.tickets[-1]
        record=owner._invocation
        if (ticket.record is not record or ticket.sealing or ticket.sealed_frame is not None
                or record._failed or record._journal_failed or record._close_attempted):
            raise ValueError('one open original response frame required')
        self._known_io(record)
        raw=_raw_frame_from_snapshot(record.snapshot(),record.request)
        observed=owner._invocation_check()  # Real observation, never max() of old stamps.
        ticket.sealing=True  # Consumed before journal/flush/close can fail.
        record._append(dict(kind='original_serial_frame_observed',invocation_id=ticket.identity.invocation_id,
            raw_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
            frame_observed_qpc_ns=observed,authenticated=False,completion_verified=False))
        record.close_journal()
        owner._invocation_check()
        self.ledger.seal(ticket,raw);ticket.observed_qpc_ns=observed
        return dict(invocation_id=ticket.identity.invocation_id,raw_frame_hex=raw.hex(),
            payload_hex=raw[4:].hex(),frame_observed_qpc_ns=observed,
            claim='original_raw_transport_frame_only',authenticated=False,completion_verified=False)

    def summary(self):
        return dict(protocol='DEEPEYE-PRIVATE-FRAMES/1',limits=asdict(self.ledger.limits),
            failed=self.ledger.failed,request_bytes_reserved=self.ledger.request_bytes,
            output_bytes_reserved=self.ledger.output_reserved,reads_reserved=self.ledger.reads_reserved,
            output_bytes_observed=self.ledger.observed_bytes,
            invocations=[dict(invocation_id=t.identity.invocation_id,journal_name=t.journal_name,
                record_retained=t.record is not None,write_reserved=t.write_reserved,
                raw_frame_sealed=t.sealed_frame is not None,frame_observed_qpc_ns=t.observed_qpc_ns,
                stream_start=t.stream_start,stream_end=(None if t.sealed_frame is None
                    else t.stream_start+len(t.sealed_frame))) for t in self.ledger.tickets],
            authenticated=False,completion_verified=False)


def _new_original_series(owner, limits):
    from .actor_owner import ActorOwner
    from .actor_pipe_io import _ActorPipeIO
    if (type(owner) is not ActorOwner or type(limits) is not SerialInvocationLimits
            or not owner._registry._contains(owner) or type(owner._pending_io) is not _ActorPipeIO
            or owner._pending_io.actor is not owner or owner._invocation_series is not None
            or owner._invocation_claimed or owner._invocation is not None
            or owner._pending_io.write_reserved
            or any(op.kind in ('read','write') for op in owner._pending_io.operations)):
        raise ValueError('fresh original overlapped actor before first request required')
    return _OriginalSerialSeries(_KEY,owner,limits)


__all__=['SerialInvocationLimits']
