"""Bounded HIL original-request association; never send or motion permission.

Trusted upstream verifiers must authenticate actual BOOT/source/timing/capture.
Frozen records and hashes are evidence containers, not credentials. None means
unknown. No default measurement provider, mailbox dependency, transport, model,
process, board or product activation is supplied. See the assigned API note.
"""
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
import struct
import threading

if __package__:
    from . import host_envelope as envelope, wire, motion, clock_bounds
else:
    import host_envelope as envelope
    import wire
    import motion
    import clock_bounds

MAX_TIME = (1 << 63) - 1
MAX_SESSIONS = 64
MAX_HISTORY = 16
MAX_OBSERVATIONS = 4
SUPPORTED_REQUESTS = frozenset((5, 10, 14))
NS_PER_MS = 1_000_000


def _integer(value, label, low=0, high=MAX_TIME):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(label + ' must be a strict bounded integer')
    return value


def _entry(method):
    @wraps(method)
    def call(self, /, *args, **kwargs):
        self._owner_call()
        if self._busy:
            self._halt('reentrant_' + method.__name__)
            raise ValueError('reentrant tracker transition')
        self._busy = True
        try:
            return method(self, *args, **kwargs)
        except BaseException as error:
            self._halt('failed_' + method.__name__)
            raise ValueError(str(error)) from error
        finally:
            self._busy = False
    return call


def _side_entry(method):
    """STOP/read remain callable in a verifier; malformed shapes still veto."""
    @wraps(method)
    def call(self, /, *args, **kwargs):
        self._owner_call()
        try:
            return method(self, *args, **kwargs)
        except BaseException as error:
            self._halt('failed_' + method.__name__)
            raise ValueError(str(error)) from error
    return call


@dataclass(frozen=True)
class BootBinding:
    run_id: str
    generation: int
    context_raw: bytes
    source: object


@dataclass(frozen=True)
class ObservationEvidence:
    boot: BootBinding
    raw: bytes
    sample_lower_ns: int | None


@dataclass(frozen=True)
class OriginalRequest:
    boot: BootBinding
    key: tuple
    first_raw: bytes
    payload: bytes
    first_send_ns: int
    ttl_ms: int | None
    observed_seq: int | None
    sample_lower_ns: int | None
    target: tuple | None


@dataclass(frozen=True)
class TimingEvidence:
    boot: BootBinding
    request: OriginalRequest
    response_raw: bytes
    serial_upper_ns: int
    usb_processing_upper_ns: int
    clock_error_upper_ns: int


@dataclass(frozen=True)
class CaptureEvidence:
    boot: BootBinding
    request: OriginalRequest
    response_raw: bytes
    yaw_q: int
    pitch_q: int
    speed_code: int
    capture_seq: int
    control_epoch: int
    quality: int
    batch: object


@dataclass(frozen=True)
class Association:
    """Diagnostic only; qualified is never a motion/send authorization."""
    request: OriginalRequest | None
    qualified: bool
    deadline_ns: int | None
    status: str


class HilDependencies(ABC):
    @abstractmethod
    def verify_boot(self, event) -> BootBinding: ...

    @abstractmethod
    def verify_observation(self, raw, boot) -> ObservationEvidence | None: ...

    @abstractmethod
    def verify_timing(self, raw, boot, original_request) -> TimingEvidence | None: ...

    @abstractmethod
    def verify_capture(self, raw, boot, original_request) -> CaptureEvidence | None: ...


@dataclass
class _Entry:
    original: OriginalRequest
    latest_raw: bytes
    deadline_ns: int | None
    state: str
    qualified: bool = False


@dataclass(frozen=True)
class _Observation:
    raw: bytes
    sample_lower_ns: int
    receipt_upper_ns: int


class HilRequestTracker:
    """Serialized owner; bounded session/request/observation/replay histories.

    Providers must be synchronous and must not hide verification failure or
    fabricate evidence. Global/restart BOOT uniqueness remains their obligation.
    Foreign-thread input requests a pending STOP; owner drains before publishing.
    """
    def __init__(self, *, run_id, dependencies=None):
        if type(run_id) is not str or not 0 < len(run_id) <= 256:
            raise ValueError('bounded run_id required')
        if dependencies is not None and not isinstance(dependencies, HilDependencies):
            raise ValueError('explicit verifier dependencies required')
        self._run, self._deps = run_id, dependencies
        self._thread = threading.get_ident()
        self._pending_stop = threading.Event()
        self._busy = False
        self._veto = 0
        self._time_high = 0
        self._stopped, self._reason = True, 'not_booted'
        self._sessions = set()
        self._generation = 0
        self._boot = None
        self._entries = OrderedDict()
        self._observations = OrderedDict()
        self._high_waters = {}
        self._active_key = None
        self._last_observation = None
        self._last_response = None
        self._last_capture = None

    def _owner_call(self):
        if threading.get_ident() != self._thread:
            self._pending_stop.set()
            raise ValueError('constructing serialized owner required')
        if self._pending_stop.is_set():
            self._pending_stop.clear()
            self._halt('foreign_thread_stop')

    def _halt(self, reason):
        self._veto += 1
        self._stopped, self._reason = True, reason
        self._observations.clear()
        current = self._entries.get(self._active_key)
        if current is not None:
            current.state, current.qualified = 'stopped', False

    def _time(self, now):
        _integer(now, 'now_ns')
        if now < self._time_high:
            raise ValueError('host clock regressed')
        self._time_high = now
        return now

    def _fence(self, epoch):
        self._owner_call()
        if self._veto != epoch:
            raise ValueError('verification transition was vetoed')

    def _callback(self, method, *args):
        epoch = self._veto
        result = getattr(self._deps, method)(*args)
        self._fence(epoch)
        return result

    def _active(self):
        if self._stopped or self._boot is None:
            raise ValueError('stopped HIL activation')

    def _association(self, entry=None, status=None, qualified=None):
        return Association(None if entry is None else entry.original,
            False if entry is None else (entry.qualified if qualified is None else qualified),
            None if entry is None else entry.deadline_ns,
            status or ('unknown_request' if entry is None else entry.state))

    def _current(self):
        return self._entries.get(self._active_key)

    def _refresh(self, entry, now):
        if entry.state in ('superseded', 'stopped', 'expired', 'observation_evicted', 'evicted'):
            entry.qualified = False
            return False
        if entry.deadline_ns is not None and now >= entry.deadline_ns:
            entry.state, entry.qualified = 'expired', False
            return False
        original = entry.original
        if original.key[1] == 14 and original.ttl_ms:
            if original.sample_lower_ns is None:
                entry.state, entry.qualified = 'unknown_observation', False
                return False
            old = self._observations.get(original.observed_seq)
            if old is None or old.sample_lower_ns != original.sample_lower_ns:
                entry.state, entry.qualified = 'observation_evicted', False
                return False
        return True

    @_entry
    def boot(self, event, *, now_ns):
        self._halt('boot_replaced')
        now = self._time(now_ns)
        if self._deps is None:
            raise ValueError('BOOT verifier unavailable')
        epoch = self._veto
        proposed = self._deps.verify_boot(event)
        if (type(proposed) is not BootBinding or proposed.run_id != self._run
                or type(proposed.context_raw) is not bytes):
            raise ValueError('original verified run/BOOT binding required')
        _integer(proposed.generation, 'BOOT generation', 1)
        context = envelope._parse_message(proposed.context_raw)
        envelope._check_context_argument(context, envelope._validators()[1])
        if (proposed.generation <= self._generation or context['session'] in self._sessions
                or len(self._sessions) >= MAX_SESSIONS):
            raise ValueError('fresh generation and unused session required')
        # A valid verifier proposal cannot be replayed after caught STOP/reentry.
        self._sessions.add(context['session'])
        self._generation = proposed.generation
        if context['topology_id'] != 1:
            raise ValueError('HIL only; PC_DIRECT cannot acquire board capture')
        self._fence(epoch)
        self._boot, self._context, self._started = proposed, context, now
        self._profile = 'fast_9600' if context['transport_profile_id'] == 1 else 'stress_300'
        self._ttl_cap = 3000 if context['transport_profile_id'] == 1 else 12000
        self._age_cap = (clock_bounds.FAST_OBSERVATION_AGE_CAP_NS if context['transport_profile_id'] == 1
                         else clock_bounds.STRESS_OBSERVATION_AGE_CAP_NS)
        self._entries.clear(); self._observations.clear(); self._high_waters.clear()
        self._active_key = self._last_observation = self._last_response = self._last_capture = None
        self._stopped, self._reason = False, 'active_no_request'

    @_entry
    def observe(self, raw, *, now_ns):
        now = self._time(now_ns); self._active()
        if type(raw) is not bytes:
            raise ValueError('immutable observation bytes required')
        parsed = envelope.validate_message(raw, producer='hardware_bridge',
            consumer='world_authority', context=self._context, now_ns=now)
        if parsed.kind not in ('telem_observation', 'event_observation'):
            raise ValueError('TELEM/EVENT source observation required')
        proof = self._callback('verify_observation', raw, self._boot)
        if proof is None or self._boot.source is None:
            return False
        if type(proof) is not ObservationEvidence or proof.boot is not self._boot or proof.raw != raw:
            raise ValueError('original source/BOOT observation association required')
        if proof.sample_lower_ns is None:
            return False
        sample = _integer(proof.sample_lower_ns, 'sample lower')
        doc = parsed.document
        mapped = doc['adc_last_interval_ns'] if parsed.kind == 'telem_observation' else doc['trigger_sample_interval_ns']
        native = doc.get('native_em_interval_ns')
        receipt = doc['receipt_interval_ns']
        if (mapped is None or sample > mapped['lower_ns'] or sample > now
                or (native is not None and sample > native['lower_ns'])
                or receipt['lower_ns'] < self._started or receipt['upper_ns'] > now):
            raise ValueError('unknown/nonconservative sample or receipt timing')
        seq = doc['observed_seq']; item = _Observation(raw, sample, receipt['upper_ns'])
        if seq in self._observations:
            if self._observations[seq] != item:
                raise ValueError('changed duplicate observation')
            return False
        if self._last_observation is not None and not 0 < seq - self._last_observation < 32768:
            raise ValueError('observation reordered, half-range or wrapped')
        self._observations[seq] = item; self._last_observation = seq
        if len(self._observations) > MAX_OBSERVATIONS:
            self._observations.popitem(last=False)
        return True

    @_entry
    def request(self, packet, *, first_send_ns, now_ns):
        now = self._time(now_ns); self._active()
        first = _integer(first_send_ns, 'first_send_ns')
        if not self._started <= first <= now or type(packet) is not bytes:
            raise ValueError('original immutable request/send time required')
        frame = wire.decode(packet)
        if (frame.type_id not in SUPPORTED_REQUESTS or frame.config_epoch != self._context['config_epoch']
                or struct.unpack_from('<I', frame.payload)[0] != self._context['session']):
            raise ValueError('unsupported request or wrong session/config epoch')
        key = (self._context['session'], frame.type_id, frame.sequence)
        existing = self._entries.get(key)
        if existing is not None:
            if existing.original.payload != frame.payload:
                raise ValueError('same request key changed semantic payload')
            existing.latest_raw = packet
            self._refresh(existing, now)
            return existing.original
        high = self._high_waters.get(frame.type_id)
        if high is not None and not 0 < frame.sequence - high < 32768:
            raise ValueError('evicted, half-range or wrapped request identity')
        ttl = observed = sample = target = None
        action = None
        if frame.type_id == 14:
            session, cmd, action, yaw, pitch, speed, ttl, observed = struct.unpack('<IHBhhBHH', frame.payload)
            if cmd != frame.sequence or action not in (0, 1):
                raise ValueError('CONTROL3D id/action mismatch')
            if action == 0:
                if any((yaw, pitch, speed, ttl)):
                    raise ValueError('STOP requires zero target/TTL')
            else:
                if not 0 < ttl <= self._ttl_cap:
                    raise ValueError('TTL outside active profile')
                motion.validate(self._profile, speed, yaw, pitch)
                obs = self._observations.get(observed)
                if obs is not None and obs.receipt_upper_ns <= first:
                    sample = obs.sample_lower_ns
            target = (yaw, pitch, speed)
        original = OriginalRequest(self._boot, key, packet, bytes(frame.payload), first,
            ttl, observed, sample, target)
        deadline = None if ttl is None else first + ttl * NS_PER_MS
        if sample is not None:
            deadline = min(deadline, sample + self._age_cap)
        state = 'non_motion' if frame.type_id != 14 else ('pending' if sample is not None else 'unknown_observation')
        entry = _Entry(original, packet, deadline, state)
        if frame.type_id == 14:
            old = self._current()
            if old is not None:
                old.state, old.qualified = ('stopped' if action == 0 else 'superseded'), False
            self._active_key = key
        self._entries[key] = entry; self._high_waters[frame.type_id] = frame.sequence
        if len(self._entries) > MAX_HISTORY:
            evicted_key, evicted = self._entries.popitem(last=False)
            if evicted_key == self._active_key:
                evicted.state, evicted.qualified = 'evicted', False
                self._active_key = None
        if action == 0:
            self._halt('STOP_request')
        else:
            self._refresh(entry, now)
        return original

    def _decode_response(self, frame):
        if frame.type_id == 15:
            a = struct.unpack('<IHBBhhBHBHBB', frame.payload)
            return a[1], a[3], (a[4], a[5], a[6]), a[7], a[8], a[9], a[10], a[11]
        a = struct.unpack('<IHhhBBHHHBB', frame.payload)
        return a[1], a[5], (a[2], a[3], a[4]), a[6], a[7], a[8], a[9], a[10]

    def _evidence(self, proof, expected_type, raw, original):
        if (type(proof) is not expected_type or proof.boot is not self._boot
                or proof.request is not original or type(proof.response_raw) is not bytes
                or proof.response_raw != raw):
            raise ValueError('original BOOT/request/response verifier association required')

    @_entry
    def response(self, raw, *, now_ns):
        now = self._time(now_ns)
        if self._stopped:
            return self._association(self._current(), 'stopped', False)
        if type(raw) is not bytes:
            raise ValueError('immutable response envelope required')
        parsed = envelope.validate_message(raw, producer='hardware_bridge',
            consumer='world_authority', context=self._context, now_ns=now)
        if parsed.kind != 'board_response':
            raise ValueError('board response required')
        doc = parsed.document; packet = bytes.fromhex(doc['wire_frame_hex']); frame = wire.decode(packet)
        receipt = doc['receipt_interval_ns']
        if receipt['lower_ns'] < self._started or receipt['upper_ns'] > now:
            raise ValueError('response receipt outside activation/current time')
        if frame.type_id not in (15, 16):
            return self._association(None, 'non_motion_response', False)
        seq, phase, target, remaining, fault, capture_seq, epoch, quality = self._decode_response(frame)
        key = (self._context['session'], 14, seq); entry = self._entries.get(key)
        if entry is None:
            return self._association(None)
        if not self._refresh(entry, now) or key != self._active_key:
            return self._association(entry, qualified=False)
        previous = self._last_response
        if previous is not None:
            if frame.sequence == previous[0]:
                if packet != previous[1]:
                    raise ValueError('changed duplicate response identity')
                return self._association(entry, 'duplicate_response', False)
            if not 0 < frame.sequence - previous[0] < 32768:
                raise ValueError('response reordered, half-range or wrapped')
        self._last_response = (frame.sequence, packet)
        entry.qualified = False
        if fault or phase in (0, 4):
            self._halt('board_fault_or_stop')
            return self._association(entry, qualified=False)
        if phase != 3 or quality != 15 or target != entry.original.target:
            return self._association(entry, 'not_current_capture', False)
        if remaining > entry.original.ttl_ms:
            raise ValueError('remaining TTL exceeds original request')
        original = entry.original
        if receipt['upper_ns'] < original.first_send_ns or self._boot.source is None:
            return self._association(entry, 'unknown_source_or_time', False)
        transition = self._veto
        timing = self._callback('verify_timing', raw, self._boot, original)
        if timing is None:
            return self._association(entry, 'unknown_timing', False)
        self._evidence(timing, TimingEvidence, raw, original)
        delays = sum(_integer(getattr(timing, name), name) for name in
            ('serial_upper_ns', 'usb_processing_upper_ns', 'clock_error_upper_ns'))
        capture = self._callback('verify_capture', raw, self._boot, original)
        if capture is None:
            return self._association(entry, 'unknown_capture', False)
        self._evidence(capture, CaptureEvidence, raw, original)
        values = tuple(_integer(getattr(capture, name), name, -15000 if name in ('yaw_q','pitch_q') else 0)
            for name in ('yaw_q','pitch_q','speed_code','capture_seq','control_epoch','quality'))
        if values != (*target, capture_seq, epoch, quality) or capture.batch is None:
            raise ValueError('independent capture batch/codes/epoch mismatch')
        if self._last_capture is not None and capture_seq < self._last_capture:
            raise ValueError('capture sequence wrapped or regressed')
        deadline = min(original.first_send_ns + original.ttl_ms * NS_PER_MS,
            receipt['lower_ns'] + max(0, remaining * NS_PER_MS - delays),
            original.sample_lower_ns + self._age_cap, entry.deadline_ns)
        self._fence(transition)
        entry.deadline_ns = deadline
        self._last_capture = capture_seq
        entry.qualified = now < deadline
        entry.state = 'associated' if entry.qualified else 'expired'
        return self._association(entry)

    @_entry
    def check(self, *, now_ns):
        now = self._time(now_ns); current = self._current()
        if self._stopped:
            return self._association(current, 'stopped', False)
        if current is not None:
            self._refresh(current, now)
        return self._association(current)

    @_side_entry
    def stop(self, reason='stop'):
        self._halt(reason[:256] if type(reason) is str else 'stop')

    @_side_entry
    def snapshot(self):
        return {'stopped':self._stopped, 'reason':self._reason, 'generation':self._generation,
            'session_count':len(self._sessions), 'request_count':len(self._entries),
            'observation_count':len(self._observations), 'request_high_waters':dict(self._high_waters),
            'host_time_high_water_ns':self._time_high,
            'requests':[{'key':list(e.original.key),'state':e.state,'qualified':e.qualified,
                'deadline_ns':e.deadline_ns,'first_send_ns':e.original.first_send_ns,
                'ttl_ms':e.original.ttl_ms,'first_raw_hex':e.original.first_raw.hex(),
                'latest_raw_hex':e.latest_raw.hex()} for e in self._entries.values()]}
