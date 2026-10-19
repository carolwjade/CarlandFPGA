"""Stateful PC_DIRECT executor stop gate; never a motion authorizer.

Consumes raw board_response JSON through host_envelope, then checks STATE8
health/history. Callers authenticate the route and BOOT context independently,
validate actual observations/AI life/commands, and apply physics constraints.
No heartbeat supplies observations, capture, command TTL or permission to move.
See docs/pc_direct_watchdog.md for lifecycle and mandatory caller obligations.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import struct
import sys


def _load_sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_envelope = _load_sibling('deepeye_pc_watchdog_envelope', 'host_envelope.py')
_wire = _load_sibling('deepeye_pc_watchdog_wire', 'wire.py')
_CONTEXT_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / 'docs/host_contract.json').read_bytes())['$defs']['context']
_CONTEXT_VALIDATOR = _envelope.StrictDraft202012Validator(_CONTEXT_SCHEMA)


def _integer(value, name, *, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError('{} must be a strict integer in the permitted range'.format(name))
    return value


def _context_copy(context):
    if type(context) is not dict or next(_CONTEXT_VALIDATOR.iter_errors(context), None) is not None:
        raise ValueError('context must satisfy the strict negotiated host context schema')
    if context['topology_id'] != 2:
        raise ValueError('PC_DIRECT watchdog requires topology_id 2')
    return copy.deepcopy(context)


@dataclass(frozen=True)
class StopGateDecision:
    """Immutable diagnostic snapshot; stop_required=False is only absence of a veto."""
    stop_required: bool
    reason: str
    heartbeat_healthy: bool
    latched: bool
    active_command_seq: int | None
    command_deadline_ns: int | None
    heartbeat_deadline_ns: int | None
    heartbeat_sequence: int | None
    heartbeat_tick_ms: int | None


class PcDirectWatchdog:
    """Single-owner, in-memory veto on an externally authorized PC_DIRECT action.

    All time arguments use one host monotonic clock. No timeout default exists.
    Call check before every physics step, including when no input arrives.
    A thrown exception requires immediate executor STOP, never reuse of an
    earlier decision. Valid fault/rejected STATEs instead return a STOP decision.
    """

    def __init__(self, *, context, heartbeat_timeout_ns, now_ns):
        self._context = _context_copy(context)
        self._heartbeat_timeout_ns = _integer(heartbeat_timeout_ns, 'heartbeat_timeout_ns', minimum=1)
        self._last_now_ns = _integer(now_ns, 'now_ns')
        self._used_sessions = {self._context['session']}
        self._clear_session(now_ns)

    @property
    def context(self):
        return copy.deepcopy(self._context)

    @property
    def heartbeat_timeout_ns(self):
        return self._heartbeat_timeout_ns

    def _clear_session(self, now_ns):
        self._started_ns = now_ns
        self._latched = False
        self._stop_reason = None
        self._idle_reason = 'missing_heartbeat'
        self._heartbeat_deadline_ns = None
        self._heartbeat_sequence = None
        self._heartbeat_tick_ms = None
        self._receipt_lower_ns = None
        self._receipt_upper_ns = None
        self._sequence_span = 0
        self._tick_span = 0
        self._active_command_seq = None
        self._command_deadline_ns = None
        self._last_command_seq = None

    def _trip(self, reason):
        if not self._latched:
            self._stop_reason = reason
        self._latched = True
        self._active_command_seq = None
        self._command_deadline_ns = None

    def _advance(self, now_ns):
        try:
            _integer(now_ns, 'now_ns')
        except ValueError:
            self._trip('invalid_clock')
            raise
        if now_ns < self._last_now_ns:
            self._trip('clock_regression')
            raise ValueError('host monotonic clock regressed')
        self._last_now_ns = now_ns
        if self._latched:
            return
        if self._heartbeat_deadline_ns is not None and now_ns >= self._heartbeat_deadline_ns:
            self._trip('heartbeat_timeout')
        elif self._command_deadline_ns is not None and now_ns >= self._command_deadline_ns:
            self._active_command_seq = None
            self._command_deadline_ns = None
            self._idle_reason = 'command_deadline'

    def _decision(self):
        healthy = not self._latched and self._heartbeat_deadline_ns is not None
        stop = not healthy or self._active_command_seq is None
        reason = (self._stop_reason if self._latched else
                  'missing_heartbeat' if not healthy else
                  self._idle_reason if self._active_command_seq is None else 'no_watchdog_veto')
        return StopGateDecision(stop, reason, healthy, self._latched,
            self._active_command_seq, self._command_deadline_ns, self._heartbeat_deadline_ns,
            self._heartbeat_sequence, self._heartbeat_tick_ms)

    def check(self, *, now_ns):
        """Recheck the clock, heartbeat and immutable command expiration at this instant."""
        self._advance(now_ns)
        return self._decision()

    def ingest_heartbeat(self, raw_bytes, *, producer, consumer, now_ns):
        """Validate raw bytes and advance health only for a new, timely STATE8.

        Route names are mandatory caller assertions, never authenticated here.
        Invalid input latches STOP before ValueError; it never refreshes health.
        """
        self._advance(now_ns)  # An unpolled lapse must trip before any late packet.
        try:
            if self._latched:
                raise ValueError('watchdog is latched; an independently verified new BOOT is required')
            if (type(producer) is not str or producer != 'hardware_bridge'
                    or type(consumer) is not str or consumer != 'world_authority'):
                raise ValueError('heartbeat requires hardware_bridge to world_authority')
            record = _envelope.validate_message(raw_bytes, producer=producer, consumer=consumer,
                                                context=self._context, now_ns=now_ns)
            if record.kind != 'board_response':
                raise ValueError('heartbeat requires a board_response envelope')
            document = record.document
            frame = _wire.decode(bytes.fromhex(document['wire_frame_hex']))
            if frame.type_id != 8:
                raise ValueError('only STATE8 is the PC_DIRECT heartbeat')
            fields = struct.unpack('<IHhBBHHHBB', frame.payload)
            lower = document['receipt_interval_ns']['lower_ns']
            upper = document['receipt_interval_ns']['upper_ns']
            if lower < self._started_ns:
                raise ValueError('receipt predates this watchdog session activation')
            if lower + self._heartbeat_timeout_ns <= now_ns:
                self._trip('stale_heartbeat')
                raise ValueError('heartbeat is already expired at its earliest possible receipt time')
            sequence_span, tick_span = self._sequence_span, self._tick_span
            if self._heartbeat_sequence is not None:
                seq_delta = (frame.sequence - self._heartbeat_sequence) % (1 << 16)
                tick_delta = (frame.tick_ms - self._heartbeat_tick_ms) % (1 << 32)
                if not 0 < seq_delta < (1 << 15) or not 0 < tick_delta < (1 << 31):
                    raise ValueError('heartbeat sequence/tick is old, repeated or half-range ambiguous')
                sequence_span += seq_delta
                tick_span += tick_delta
                if sequence_span >= (1 << 16) or tick_span >= (1 << 31):
                    raise ValueError('ordering horizon exhausted; stop and establish a new BOOT/session')
                if lower <= self._receipt_lower_ns or upper < self._receipt_upper_ns:
                    raise ValueError('heartbeat receipt interval does not advance monotonically')
            if fields[6] != 0:
                self._trip('board_fault')
                return self._decision()
            if fields[4] == 4:
                self._trip('board_rejected')
                return self._decision()
            self._heartbeat_sequence = frame.sequence
            self._heartbeat_tick_ms = frame.tick_ms
            self._sequence_span, self._tick_span = sequence_span, tick_span
            self._receipt_lower_ns, self._receipt_upper_ns = lower, upper
            self._heartbeat_deadline_ns = lower + self._heartbeat_timeout_ns
            if self._idle_reason == 'missing_heartbeat':
                self._idle_reason = 'no_active_command'
            return self._decision()
        except Exception as error:
            self._trip('invalid_heartbeat')
            if isinstance(error, ValueError):
                raise
            raise ValueError('heartbeat validation failed; watchdog stopped') from error

    def track_authority_command(self, *, command_seq, deadline_ns, now_ns):
        """Record only identity/deadline of a command independently verified upstream.

        This method cannot validate authority, observations, AI life, command
        content or physics. Callers must never treat its return as a grant.
        """
        self._advance(now_ns)
        try:
            if self._latched:
                raise ValueError('watchdog is latched')
            _integer(command_seq, 'command_seq', maximum=65535)
            _integer(deadline_ns, 'deadline_ns', minimum=1)
            if deadline_ns <= now_ns:
                raise ValueError('command deadline has already expired')
            if self._heartbeat_deadline_ns is None:
                raise ValueError('cannot track an active action without a healthy heartbeat')
            if self._last_command_seq is not None and command_seq <= self._last_command_seq:
                if command_seq != self._active_command_seq:
                    raise ValueError('command is expired, cancelled, superseded or not increasing')
                self._command_deadline_ns = min(self._command_deadline_ns, deadline_ns)
            else:
                self._last_command_seq = command_seq
                self._active_command_seq = command_seq
                self._command_deadline_ns = deadline_ns
            return self._decision()
        except Exception as error:
            self._trip('invalid_command')
            if isinstance(error, ValueError):
                raise
            raise ValueError('command tracking failed; watchdog stopped') from error

    def cancel(self, *, now_ns):
        """Drop the action without clearing health latches or command replay history."""
        self._advance(now_ns)
        self._active_command_seq = None
        self._command_deadline_ns = None
        self._idle_reason = 'cancelled'
        return self._decision()

    def reset(self, *, context, now_ns):
        """Stopped-state reset after the caller independently verifies a NEW BOOT.

        Requires an unused session for this object; does not verify BOOT itself.
        No old action, heartbeat or command high-water mark crosses the boundary.
        """
        self._advance(now_ns)
        try:
            proposed = _context_copy(context)
            if proposed['session'] in self._used_sessions:
                raise ValueError('reset requires an unused session; same/retired session is forbidden')
            self._used_sessions.add(proposed['session'])
            self._context = proposed
            self._clear_session(now_ns)
            return self._decision()
        except Exception as error:
            self._trip('invalid_reset')
            if isinstance(error, ValueError):
                raise
            raise ValueError('reset failed; watchdog stopped') from error


__all__ = ['PcDirectWatchdog', 'StopGateDecision']
