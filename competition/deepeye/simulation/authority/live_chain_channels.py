"""Candidate source -> private PL -> returned-count channel segment.

This is diagnostic data plumbing, not the missing authenticated production
ActorComposition provider. No BOOT, CPU completion, compression or movement
authority is created here. Public inputs contain returned counts/quality and
causal identity only, never pre-board floating values or world truth.
"""
from dataclasses import dataclass
import hashlib
import json
import threading

from ...integration import private_pl_stream as pl
from ...integration import sensor_source as source

QUALITY_ENCODING = 'candidate_four_channel_quality_v1'
CHANNEL_NAMES = ('log10_rho_apparent', 'yaw_log10_rho_difference',
                 'pitch_log10_rho_difference', 'near_bit_vibration_rms_g')
# At most the complete 100Hz input history of one existing <=10s diagnostic.
MAX_SOURCE_RECORDS = 1001


def pack_candidate_quality(quality):
    """Private lane bits0 valid,1 saturated,2 held,3 shared source_fault."""
    if type(quality) is not int or not 0 <= quality <= 0x1fff:
        raise ValueError('strict candidate13bit quality word required')
    fault = (quality >> 12) & 1
    return tuple(((quality >> ch) & 1) | (((quality >> (4+ch)) & 1) << 1)
                 | (((quality >> (8+ch)) & 1) << 2) | (fault << 3)
                 for ch in range(4))


def unpack_candidate_quality(lanes):
    """Invert the versioned private mapping; reject reserved/disagreed bits."""
    if (type(lanes) not in (tuple, list) or len(lanes) != 4 or
            any(type(value) is not int or not 0 <= value < 16 for value in lanes)):
        raise ValueError('four strict candidate quality nibbles required')
    faults = tuple((value >> 3) & 1 for value in lanes)
    if len(set(faults)) != 1:
        raise ValueError('shared source_fault copies disagree')
    quality = faults[0] << 12
    for ch, value in enumerate(lanes):
        quality |= ((value & 1) << ch) | (((value >> 1) & 1) << (4+ch))
        quality |= ((value >> 2) & 1) << (8+ch)
    return quality


@dataclass(frozen=True)
class _PendingSample:
    record: source.SourceRecord
    admission_index: int
    received_ns: int
    request_raw: bytes


class _CandidateChannel:
    """Single-thread component core; constructor arguments grant no authority.

    Tests use the established private PL component owner/clock seam. The public
    wrapper below constructs a real HostOwner with its fixed QPC binding.
    All actual admissions are retained up to a fixed bound; gaps are recorded,
    never backfilled or presented as a complete lossless100Hz acquisition.
    """
    def __init__(self, owner, *, clock, start_tick_ms, start_monotonic_ns,
                 max_scans=16):
        if type(max_scans) is not int or not 1 <= max_scans <= 16:
            raise ValueError('strict diagnostic scan cap1..16 required')
        self._ledger = source.SourceLedger(start_tick_ms=start_tick_ms,
                                          start_monotonic_ns=start_monotonic_ns)
        self._owner, self._clock = owner, clock
        self._start_tick, self._start_ns = start_tick_ms, start_monotonic_ns
        self._thread = threading.get_ident()
        self._high = start_monotonic_ns
        self._history = []
        self._pending = None
        self._last_requested_tick = None
        self._scans, self._max_scans = 0, max_scans
        self.state = 'AWAITING_READY'

    def _fail(self):
        self.state = 'FAILED'  # Latch before returning to any external transport.
        self._owner.retire()
        # Original pending bytes, history and source failure facts stay retained.

    def _active(self, *states):
        if threading.get_ident() != self._thread or self.state not in states:
            raise ValueError('original active channel owner/state required')

    def _now(self):
        now = self._clock()
        pl.uint(now, 63)
        if now < self._high:
            raise ValueError('original channel clock regressed')
        self._high = now
        return now

    def _source_ns(self, tick):
        return self._start_ns + (tick-self._start_tick)*source.NS_PER_MS

    def accept_ready(self, raw):
        try:
            self._active('AWAITING_READY')
            result = self._owner.accept_ready(raw)
            self._now()
            self.state = 'READY'
            # Do not export HostOwner's shared baseline_counters list.
            return json.loads(json.dumps(result))
        except BaseException:
            self._fail()
            raise

    def admit_sample(self, payload):
        """Feed every actual source admission, including during a pending scan."""
        try:
            self._active('READY', 'PENDING')
            if len(self._history) >= MAX_SOURCE_RECORDS:
                raise ValueError('bounded source admission history exhausted')
            now = self._now()
            admitted = self._ledger.accept(payload, received_monotonic_ns=now)
            self._history.append((admitted, now))
            return admitted  # Detached immutable SourceLedger record, no truth.
        except BaseException:
            self._fail()
            raise

    def next_request(self):
        """Reserve once before the caller's sole external write; never resend."""
        try:
            self._active('READY')
            if not self._history or self._scans >= self._max_scans:
                raise ValueError('new source admission and remaining scan budget required')
            admitted, received = self._history[-1]
            record = admitted.record
            now = self._now()
            em_expired = (record.em_tick_ms is not None and
                          not 0 <= now-self._source_ns(record.em_tick_ms) <= source.TIMEOUT_NS)
            if (record.adc_tick_ms == self._last_requested_tick or
                    not 0 <= now-self._source_ns(record.adc_tick_ms) <= source.TIMEOUT_NS or
                    em_expired):
                raise ValueError('source already requested, future or expired before injection')
            # Invalid channels use an explicit transport placeholder, never valid0.
            # New lists are not shared with callers or the immutable source record.
            values = [0 if count is None else count for count in record.channel_counts]
            qualities = list(pack_candidate_quality(record.quality))
            self._scans += 1  # Consumed before HostOwner may reserve request state.
            self._pending = _PendingSample(record, len(self._history)-1, received, b'')
            raw = self._owner.next_request(values, qualities)
            self._pending = _PendingSample(record, len(self._history)-1, received, raw)
            self._last_requested_tick = record.adc_tick_ms
            self.state = 'PENDING'
            return raw
        except BaseException:
            self._fail()
            raise

    def accept_capture(self, raw):
        """Translate only original pending HostOwner-validated returned lanes."""
        try:
            self._active('PENDING')
            pending = self._pending
            if pending is None or not pending.request_raw:
                raise ValueError('original pending source/request association required')
            accepted = self._owner.accept(raw)
            now = self._now()  # Conservative receiver upper bound after validation.
            request = pl.decode(pending.request_raw)
            lane_quality = [lane['raw_words'][1] >> 8 for lane in accepted['captures']]
            quality = unpack_candidate_quality(lane_quality)
            if quality != pending.record.quality:
                raise ValueError('returned source quality changed')
            counts = []
            for ch, lane in enumerate(accepted['captures']):
                value = lane['raw_words'][0]  # Never use pre-board sample floats/counts.
                if quality & (1 << ch):
                    if type(value) is not int or not 0 <= value <= 4095:
                        raise ValueError('returned candidate count outside12bit range')
                    counts.append(value)
                else:
                    if type(value) is not int or value != 0:
                        raise ValueError('invalid returned channel lacks zero placeholder')
                    counts.append(None)
            record = pending.record
            adc_age = now-self._source_ns(record.adc_tick_ms)
            em_age = None if record.em_tick_ms is None else now-self._source_ns(record.em_tick_ms)
            if adc_age < 0 or (em_age is not None and em_age < 0):
                raise ValueError('original source schedule is future at capture')
            fresh = (adc_age <= source.TIMEOUT_NS and em_age is not None and
                     em_age <= source.TIMEOUT_NS and not quality & 0x1000)
            latency_upper = now-request['original_host_qpc_ns'][0]
            if latency_upper < 0:
                raise ValueError('receiver precedes original injection')
            measured = self._owner.last_response_timing
            result = dict(schema=1, kind='candidate_four_channel_input',
                profile_id=record.profile_id, profile_status=record.profile_status,
                profile_note=record.profile_note, source_mode=record.source_mode,
                quality_encoding=QUALITY_ENCODING, source_id=4,
                transport_source='software_fixture', channel_names=list(CHANNEL_NAMES),
                channel_counts=counts, quality=quality,
                source_time=dict(adc_tick_ms=record.adc_tick_ms, em_tick_ms=record.em_tick_ms,
                    source_start_tick_ms=self._start_tick, source_start_monotonic_ns=self._start_ns,
                    admission_received_monotonic_ns=pending.received_ns,
                    adc_source_age_ns=adc_age, em_source_age_ns=em_age,
                    time_basis='trusted_root_source_schedule_not_physical_sample_authentication'),
                observation_identity=dict(context=dict(accepted['context']),
                    request_seq=accepted['request_seq'], request_sha256=accepted['request_sha256'],
                    capture_sha256=hashlib.sha256(raw).hexdigest(),
                    generation=accepted['generation'], trigger_id=accepted['trigger_id'],
                    source_admission_index=pending.admission_index,
                    original_host_injection_qpc_ns=list(request['original_host_qpc_ns']),
                    receiver_upper_qpc_ns=now),
                diagnostic_flags=dict(source_fresh_at_capture=bool(fresh),
                    all_channels_valid=(quality & 15) == 15,
                    injection_to_receiver_upper_ns=latency_upper,
                    target100ms_met=(latency_upper <= pl.TARGET_AGE_NS if measured is None
                                     else measured['target100ms_met']),
                    target100ms_scope=('conservative_receiver_upper_bound' if measured is None
                                       else 'private_HostOwner_request_to_receive'),
                    formal_100ms_acceptance='not_run', formal_H12='not_run',
                    transport_authenticated=False, BOOT_authenticated=False,
                    physical_sample_authenticated=False, compression_verified=False,
                    CPU_completion_created=False, movement_authorized=False))
            self._pending = None  # This accepted scan is consumed, never reusable.
            self.state = 'READY'
            return result
        except BaseException:
            self._fail()
            raise

    def source_history(self):
        """Detached bounded evidence of all actual admissions; gaps stay gaps."""
        self._active('READY', 'PENDING', 'FAILED', 'RETIRED')
        return tuple(dict(adc_tick_ms=admission.record.adc_tick_ms,
                          em_tick_ms=admission.record.em_tick_ms,
                          quality=admission.record.quality,
                          received_monotonic_ns=received,
                          new_em_sample=admission.new_em_sample,
                          adc_gap_ms=admission.adc_gap_ms)
                     for admission, received in self._history)

    def retire(self, reason):
        if type(reason) is not str or not reason:
            raise ValueError('explicit retirement reason required')
        self._active('AWAITING_READY', 'READY', 'PENDING', 'FAILED', 'RETIRED')
        self._owner.retire()
        self.state = 'RETIRED'


class LiveFourChannelChannel(_CandidateChannel):
    """Root-owned diagnostic wrapper; actual fixed QPC type, no provider injection."""
    def __init__(self, context, host_clock, *, start_tick_ms, start_monotonic_ns,
                 max_scans=16, functional_timing_profile=None):
        profile = (None if functional_timing_profile is None else
                   pl.validate_functional_timing_profile(functional_timing_profile))
        age = pl.TARGET_AGE_NS if profile is None else pl.FUNCTIONAL_AGE_NS
        # Freeze nested caller state before handing it to the original PL owner.
        ctx = json.loads(pl.encode(pl.context(context)))
        owner = pl.HostOwner(ctx, host_clock, max_age_ns=age,
                             functional_timing_profile=profile)
        super().__init__(owner, clock=host_clock, start_tick_ms=start_tick_ms,
                         start_monotonic_ns=start_monotonic_ns, max_scans=max_scans)


__all__ = ['LiveFourChannelChannel', 'pack_candidate_quality',
           'unpack_candidate_quality', 'QUALITY_ENCODING']
