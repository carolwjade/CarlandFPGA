"""Candidate authority -> hardware_bridge admission boundary; stdlib, no I/O.

Only the actual ForwardProfile.to_payload shape is accepted. No calibration,
transport authentication, physical sampling or G03/G09 acceptance is implied.
The caller supplies a trusted receiver monotonic clock/origin, never a clock
from the untrusted record. See docs/sensor_source_boundary.md before adoption.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Optional


FIELDS = frozenset((
    'profile_id', 'profile_status', 'profile_note', 'source_mode', 'adc_tick_ms',
    'em_tick_ms', 'channel_values', 'channel_counts', 'quality',
))
METADATA = (
    ('profile_id', 'deepeye_forward_profile_candidate_v1'),
    ('profile_status', 'candidate_only'),
    ('profile_note', 'not_calibrated;not_em_surrogate_v2;not_formally_frozen'),
    ('source_mode', 'twin_fixture'),
)
# Independently pinned consumer bounds for the existing candidate; importing
# producer internals here would silently change the boundary when it drifts.
LIMITS = ((math.log10(0.2), math.log10(2000.0)), (-2.0, 2.0),
          (-2.0, 2.0), (0.0, 2.0))
MAX_TICK_MS = (1 << 31) - 1
NS_PER_MS = 1_000_000
TIMEOUT_NS = 100 * NS_PER_MS


def _integer(value, name, low=0, high=None):
    if type(value) is not int or value < low or (high is not None and value > high):
        raise ValueError(name + ' must be an in-range integer, never bool')
    return value


def _tick(value, name, period):
    value = _integer(value, name, high=MAX_TICK_MS)
    if value % period:
        raise ValueError(name + ' is off-grid')
    return value


@dataclass(frozen=True)
class SourceRecord:
    profile_id: str
    profile_status: str
    profile_note: str
    source_mode: str
    adc_tick_ms: int
    em_tick_ms: Optional[int]
    channel_values: tuple
    channel_counts: tuple
    quality: int


def validate_record(payload):
    """Return a detached immutable record, or ValueError; never coerce input."""
    if type(payload) is not dict or set(payload) != FIELDS:
        raise ValueError('record must contain exactly the nine source fields')
    for key, expected in METADATA:
        if type(payload[key]) is not str or payload[key] != expected:
            raise ValueError('unsupported candidate metadata: ' + key)
    adc = _tick(payload['adc_tick_ms'], 'adc_tick_ms', 10)
    quality = _integer(payload['quality'], 'quality', high=0x1FFF)
    values, counts = payload['channel_values'], payload['channel_counts']
    if type(values) is not list or type(counts) is not list or len(values) != 4 or len(counts) != 4:
        raise ValueError('values/counts must be four-element JSON arrays')
    em_valid = quality & 7
    if em_valid not in (0, 7):
        raise ValueError('EM validity must be all-or-none')
    fault = bool(quality & 0x1000)
    if fault != (em_valid == 0):
        raise ValueError('source_fault must match invalid EM')
    if quality & 0x800:
        raise ValueError('vibration RMS is not a held EM channel')
    em = payload['em_tick_ms']
    if em_valid:
        em = _tick(em, 'em_tick_ms', 50)
        if not 0 <= adc - em <= 100:
            raise ValueError('EM time is future or stale')
        expected_hold = 0x700 if em < adc else 0
        if quality & 0x700 != expected_hold:
            raise ValueError('held EM must preserve its original time')
    elif em is not None:
        raise ValueError('invalid EM must have null original time')
    detached = []
    for channel, (value, count, (low, high)) in enumerate(zip(values, counts, LIMITS)):
        valid = bool(quality & (1 << channel))
        saturated = bool(quality & (1 << (4 + channel)))
        held = bool(quality & (1 << (8 + channel)))
        if not valid:
            if value is not None or count is not None or saturated or held:
                raise ValueError('invalid channel must be null with saturation/hold cleared')
            detached.append(None)
            continue
        if type(value) not in (int, float):
            raise ValueError('channel value must be a finite JSON number, never bool')
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or not low <= value <= high:
            raise ValueError('channel value is non-finite or outside candidate range')
        _integer(count, 'channel_counts', high=4095)
        expected_count = round((value - low) / (high - low) * 4095)
        if count != expected_count:
            raise ValueError('normalized proxy count disagrees with channel value')
        if channel < 3 and saturated and value not in (low, high):
            raise ValueError('saturated EM must be clipped to a range endpoint')
        if channel == 3 and (adc < 90 or (saturated and value < math.sqrt(0.4))):
            raise ValueError('vibration RMS cannot have this startup/saturation state')
        detached.append(value)
    return SourceRecord(*(payload[key] for key, _ in METADATA), adc, em,
                        tuple(detached), tuple(counts), quality)


def _decode(raw):
    if type(raw) not in (str, bytes) or len(raw) > 4096:
        raise ValueError('source JSON must be a bounded UTF-8 record')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON field')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('non-finite JSON number')

    try:
        text = raw.decode('utf-8') if type(raw) is bytes else raw
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError('invalid source JSON') from exc


def validate_json(raw):
    """Strict wire parser: duplicate keys and non-finite JSON fail closed."""
    return validate_record(_decode(raw))


@dataclass(frozen=True)
class LedgerSnapshot:
    accepted_records: int = 0
    native_em_acquisitions: int = 0
    last_record: Optional[SourceRecord] = None
    last_received_ns: Optional[int] = None
    last_healthy_received_ns: Optional[int] = None
    last_em_tick_ms: Optional[int] = None
    consecutive_adc_samples: int = 0


@dataclass(frozen=True)
class Admission:
    record: SourceRecord
    new_em_sample: bool
    adc_gap_ms: Optional[int]


class SourceLedger:
    """Single-writer, in-memory per-run admission ledger; not a transport.

    Start with the producer's full ADC history from start_tick_ms, not a live
    midstream attach. Clock anchors are trusted caller inputs in one receiver
    monotonic domain. Do not recreate this ledger to hide faults or replay.
    """

    def __init__(self, *, start_tick_ms, start_monotonic_ns):
        self._start_tick = _tick(start_tick_ms, 'start_tick_ms', 10)
        self._start_ns = _integer(start_monotonic_ns, 'start_monotonic_ns')
        self._clock_high_water_ns = self._start_ns
        self._snapshot = LedgerSnapshot()

    @property
    def snapshot(self):
        return self._snapshot

    @property
    def clock_high_water_ns(self):
        """Trusted clock observation, separate from admitted sample/heartbeat state."""
        return self._clock_high_water_ns

    def _observe_time(self, value, name):
        now = _integer(value, name)
        if now < self._clock_high_water_ns:
            raise ValueError('receiver monotonic clock reversed below an observed time')
        # Observe before parsing/validating untrusted payloads. A later payload
        # failure cannot erase a trusted clock fact or permit time travel.
        self._clock_high_water_ns = now
        return now

    def _time_ns(self, tick):
        return self._start_ns + (tick - self._start_tick) * NS_PER_MS

    def accept_json(self, raw, *, received_monotonic_ns):
        now = self._observe_time(received_monotonic_ns, 'received_monotonic_ns')
        return self.accept(_decode(raw), received_monotonic_ns=now)

    def accept(self, payload, *, received_monotonic_ns):
        """Observe time first; rejection changes no sample/heartbeat snapshot."""
        now = self._observe_time(received_monotonic_ns, 'received_monotonic_ns')
        rec = validate_record(payload)
        state = self._snapshot
        if rec.adc_tick_ms < self._start_tick:
            raise ValueError('record predates run origin')
        lag = now - self._time_ns(rec.adc_tick_ms)
        if not 0 <= lag <= TIMEOUT_NS:
            raise ValueError('ADC record is future or older than source timeout')
        previous = state.last_record
        if previous is None:
            if rec.adc_tick_ms != self._start_tick:
                raise ValueError('full ADC stream required from run origin')
            gap = None
            consecutive = 1
        else:
            gap = rec.adc_tick_ms - previous.adc_tick_ms
            if gap <= 0:
                raise ValueError('ADC duplicate, reversal or backfill')
            consecutive = min(10, state.consecutive_adc_samples + 1) if gap == 10 else 1
        if bool(rec.quality & 8) != (consecutive == 10):
            raise ValueError('vibration validity disagrees with observed contiguous ADC window')
        new_em = rec.em_tick_ms is not None and rec.em_tick_ms != state.last_em_tick_ms
        if rec.em_tick_ms is not None:
            if new_em:
                if (state.last_em_tick_ms is not None and rec.em_tick_ms <= state.last_em_tick_ms
                        or rec.em_tick_ms != rec.adc_tick_ms):
                    raise ValueError('new EM must first appear in its own ADC slot; no backfill')
            else:
                if previous is None or previous.em_tick_ms != rec.em_tick_ms:
                    raise ValueError('invalidated EM cannot revive as held data')
                if (rec.channel_values[:3] != previous.channel_values[:3]
                        or rec.channel_counts[:3] != previous.channel_counts[:3]
                        or rec.quality & 0x70 != previous.quality & 0x70):
                    raise ValueError('held EM value/count/saturation changed')
        healthy_received = state.last_healthy_received_ns
        if rec.em_tick_ms is not None:
            # Delayed delivery cannot turn an expired EM timestamp fresh.
            if now - self._time_ns(rec.em_tick_ms) > TIMEOUT_NS:
                raise ValueError('EM already expired at receiver')
            healthy_received = now
        self._snapshot = LedgerSnapshot(
            state.accepted_records + 1, state.native_em_acquisitions + int(new_em),
            rec, now, healthy_received,
            rec.em_tick_ms if new_em else state.last_em_tick_ms, consecutive,
        )
        return Admission(rec, new_em, gap)

    def healthy(self, *, now_monotonic_ns):
        """Observe time, then read source health without mutating its records."""
        now = self._observe_time(now_monotonic_ns, 'now_monotonic_ns')
        state = self._snapshot
        rec = state.last_record
        return bool(rec is not None and rec.em_tick_ms is not None
                    and now - state.last_received_ns <= TIMEOUT_NS
                    and now - self._time_ns(rec.em_tick_ms) <= TIMEOUT_NS)
