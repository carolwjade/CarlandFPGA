"""Single-attempt OS BOOT write and original ACK echo diagnostics.

Digest/label equality provides correlation only. No peer, build, BOOT, context,
sample clock or motion authority is authenticated here. See docs/boot_transcript.md.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading

from . import boot_profile as boot
from . import host_clock as clocks
from .live_board_receipts import CaptureIdentity, ReceiptLedger


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(name + ' must be an explicit bounded integer')


def _digest(value, name):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError(name + ' must be a complete lowercase SHA256')


def _detached(value):
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


class BootTranscript:
    """One owner thread, one durable new journal, one OS write, bounded ACK checks.

    Main supplies an already-open descriptor with a separately bounded blocking
    policy and an exclusively owned original ReceiptLedger for that connection.
    This constructor does not establish those ownership or connection claims.
    """
    def __init__(self, fd, ledger, *, identity, profile, profile_sha256,
                 build_manifest, bit_sha256, hwh_sha256, session, mode,
                 config_epoch, sequence, tick_ms, max_ack_checks, journal_path):
        _integer(fd, 'fd', 0, (1 << 31)-1)
        if type(identity) is not CaptureIdentity or type(ledger) is not ReceiptLedger:
            raise ValueError('exact capture identity and original receipt ledger required')
        ledger._owner()
        if ledger.clock_domain is not ledger._bound_domain or ledger._clock is not ledger._bound_clock:
            raise ValueError('original unchanged ledger clock binding required')
        self._clock_domain = clocks._require_binding(ledger.clock_domain)
        self._clock = ledger._clock
        if type(ledger.identity) is not CaptureIdentity or ledger.identity != identity:
            raise ValueError('send and receive correlation identities differ')
        for name, value in [('profile_sha256', profile_sha256),
                            ('bit_sha256', bit_sha256), ('hwh_sha256', hwh_sha256)]:
            _digest(value, name)
        if (type(build_manifest) is not bytes or not 1 <= len(build_manifest) <= 1024*1024 or
                hashlib.sha256(build_manifest).hexdigest() != identity.build_manifest_sha256):
            raise ValueError('original complete build-manifest bytes must match capture digest')
        if type(profile) is not dict:
            raise ValueError('complete profile document required')
        # Freeze the same covered document as the frozen canonical_sha256 helper.
        frozen = json.loads(boot.canonical_bytes(profile))
        if boot.validate_document(frozen):
            raise ValueError('profile fails frozen document contract')
        if boot.canonical_sha256(frozen).hex() != profile_sha256:
            raise ValueError('complete profile SHA256 mismatch')
        _integer(session, 'session', 0, 0xffffffff)
        _integer(mode, 'mode', 0, 255)
        _integer(config_epoch, 'config_epoch', 0, 255)
        _integer(sequence, 'sequence', 0, 65535)
        _integer(tick_ms, 'tick_ms', 0, 0xffffffff)
        _integer(max_ack_checks, 'max_ack_checks', 1, 64)
        request = boot.boot_frame(frozen, session, mode, config_epoch, sequence, tick_ms)
        file_mode = os.fstat(fd).st_mode
        if not (stat.S_ISFIFO(file_mode) or stat.S_ISSOCK(file_mode) or stat.S_ISCHR(file_mode)):
            raise ValueError('connected OS pipe/socket/device required; no replay file')
        self._thread = threading.get_ident()
        self._identity, self._ledger = identity, ledger
        self._request, self._profile = request, frozen
        self._max_ack_checks = max_ack_checks
        self._attempt, self._checks, self._seen = None, [], set()
        self._closed = self._journal_failed = self._clock_failed = False
        self._fd = os.dup(fd)
        try:
            os.set_inheritable(self._fd, False)
            if os.name == 'nt':
                import msvcrt
                msvcrt.setmode(self._fd, os.O_BINARY)
            # Exclusive create deliberately has no resume/recovery/send branch.
            self._journal = Path(journal_path).open('xb')
            try:
                self._prepared = dict(kind='prepared', schema=1, identity=asdict(identity),
                    profile=frozen, profile_sha256=profile_sha256,
                    profile_hash_scope='frozen canonical_sha256; host_inference excluded',
                    build_manifest_hex=build_manifest.hex(), bit_sha256=bit_sha256,
                    hwh_sha256=hwh_sha256, request=boot.parse_boot_frame(request),
                    raw_hex=request.hex(), raw_sha256=hashlib.sha256(request).hexdigest(),
                    max_ack_checks=max_ack_checks,
                    host_clock=clocks._description(self._clock_domain),
                    provenance='main-supplied correlation only; no peer/build/BOOT authentication',
                    authenticated=False, motion_authorized=False)
                self._append(self._prepared)
            except BaseException:
                self._journal.close()
                raise
        except BaseException:
            os.close(self._fd)
            raise

    def _owner(self):
        if threading.get_ident() != self._thread:
            raise ValueError('original BOOT owner thread required')

    def _active(self):
        self._owner()
        if (self._ledger.clock_domain is not self._clock_domain
                or self._ledger._clock is not self._clock):
            self._clock_failed = True
        if self._closed or self._journal_failed or self._clock_failed:
            raise ValueError('BOOT transcript is closed or journal failed')

    @property
    def clock_domain(self):
        return self._clock_domain

    def _append(self, value):
        raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':'),
                          allow_nan=False) + '\n').encode('utf-8')
        try:
            if self._journal.write(raw) != len(raw):
                raise OSError('partial journal write')
            self._journal.flush()
            os.fsync(self._journal.fileno())
        except BaseException:
            self._journal_failed = True
            raise

    def send_once(self):
        """Persist started_unknown, then attempt exactly one actual os.write.

        Short/error/interrupted writes are terminal and never retried. The call
        may block with the original transport policy; no timer or retry is added.
        """
        self._active()
        if self._attempt is not None:
            raise ValueError('original BOOT already attempted; no resume or resend')
        receive = self._ledger.snapshot()
        if (receive['failed'] or receive['closed'] or receive['eof'] or
                receive['identity'] != asdict(self._identity)):
            raise ValueError('original receive ledger is inactive or identity changed')
        self._receive_start = receive['bytes_read']
        self._attempt = dict(kind='write_started', outcome='started_unknown',
            raw_hex=self._request.hex(), raw_sha256=hashlib.sha256(self._request).hexdigest(),
            requested_bytes=len(self._request), bytes_written=None,
            write_call_interval_ns=None, raw_write_call_bracket_ns=None, started_marker_ns=None,
            receive_stream_start=self._receive_start)
        # Reserve before any stamp; failure cannot re-enter a new write attempt.
        try:
            self._attempt['started_marker_ns'] = self._clock()
        except BaseException as exc:
            self._clock_failed = True
            self._attempt.update(outcome='clock_error_no_write',clock_error_type=type(exc).__name__)
            self._append(self._attempt)
            raise
        try:
            self._append(self._attempt)
        except BaseException:
            self._attempt['outcome'] = 'journal_error_no_write'
            raise
        try:
            begin = self._clock()
        except BaseException as exc:
            self._clock_failed = True
            self._attempt.update(outcome='clock_error_no_write',clock_error_type=type(exc).__name__)
            self._append(self._attempt)
            raise
        self._attempt['raw_write_call_bracket_ns'] = [begin,None]
        self._attempt['kind'] = 'write_result'
        error = None
        try:
            count = os.write(self._fd, self._request)
            self._attempt.update(bytes_written=count,
                outcome='written' if count == len(self._request) else 'partial_unknown')
        except BaseException as exc:
            error = exc
            self._attempt.update(outcome='write_error_unknown', error_type=type(exc).__name__,
                errno=getattr(exc, 'errno', None))
        try:
            end = self._clock()
            self._attempt['raw_write_call_bracket_ns'][1] = end
            if self._clock_domain is None:
                self._attempt['write_call_interval_ns'] = [begin,end]
        except BaseException as exc:
            self._clock_failed = True
            self._attempt.update(outcome='clock_error_after_write_unknown',
                                 clock_error_type=type(exc).__name__)
            if error is None: error = exc
        try:
            self._append(self._attempt)
        except BaseException:
            self._attempt['outcome'] = 'journal_error_after_write'
            raise
        if error is not None:
            raise error
        return _detached(self._attempt)

    def check_ack(self, event):
        """Compare an original received ACK with original sent bytes, diagnostically.

        Post-write reads do not prove fresh arrival or authentic BOOT. No received
        packet is re-encoded, no envelope is created, and no send occurs here.
        """
        self._active()
        if self._attempt is None or self._attempt['outcome'] != 'written':
            raise ValueError('one fully returned OS write required for echo comparison')
        if len(self._checks) >= self._max_ack_checks:
            raise ValueError('original ACK-check budget reached')
        self._ledger._owner()
        self._ledger._original(event)  # Exact original object from this ledger only.
        if event.receipt_index in self._seen:
            raise ValueError('original ACK receipt already checked')
        receive = self._ledger.snapshot()
        if receive['failed'] or receive['identity'] != asdict(self._identity):
            raise ValueError('original receive ledger failed or identity changed')
        row = receive['frames'][event.receipt_index]
        spans = row['spans']
        intervals = [receive['reads'][s['read_index']]['raw_read_call_bracket_ns'] for s in spans]
        if (event.stream_start < self._receive_start or
                any(pair[0] < self._attempt['raw_write_call_bracket_ns'][1] for pair in intervals)):
            raise ValueError('ACK includes bytes read before the original write returned')
        self._seen.add(event.receipt_index)
        result = dict(kind='ack_check', receipt_index=event.receipt_index,
            raw_hex=event.raw.hex(), raw_sha256=hashlib.sha256(event.raw).hexdigest(),
            stream_start=event.stream_start, stream_end=event.stream_end, spans=spans,
            read_call_intervals_ns=intervals if self._clock_domain is None else None,
            raw_read_call_brackets_ns=intervals,
            availability_interval_ns=event.availability_interval_ns,
            availability_scope='descriptor queue only; no UART arrival or sample time',
            sample_interval_ns=None, physical_capture_record_sha256=None,
            echo=boot.verify_boot_ack(self._request, event.raw),
            authenticated=False, motion_authorized=False)
        self._checks.append(result)  # A failed journal must not recycle a checked receipt.
        self._append(result)
        return _detached(result)

    def snapshot(self):
        """Detached diagnostic evidence; valid after close or terminal IO failure."""
        self._owner()
        return _detached(dict(schema=1, identity=asdict(self._identity),
            profile=self._profile, prepared=self._prepared, attempt=self._attempt,
            ack_checks=self._checks, closed=self._closed, journal_failed=self._journal_failed,
            clock_failed=self._clock_failed,host_clock=clocks._description(self._clock_domain),
            authenticated=False, motion_authorized=False))

    def close(self):
        """Close only the writer's duplicate and owned journal; never send or retry."""
        self._owner()
        if not self._closed:
            self._closed = True
            try:
                os.close(self._fd)
            finally:
                self._journal.close()


__all__ = ['BootTranscript']
