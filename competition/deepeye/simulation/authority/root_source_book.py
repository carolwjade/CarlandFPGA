"""Root-private original source/pose time observations; no admission authority.

Exact types/registries are trusted-process conventions, not an OS boundary.
The software seam returns a different type and never adopts native owners.
"""
from dataclasses import asdict
from functools import wraps
import hashlib
import json
import threading
from types import MethodType

from ...integration import host_clock as clocks
from ...integration import sensor_source
from ..sensors import forward_profile as forward
from ..sensors.owned_world_field import OwnedWorldField
from . import _owned_godot as native
from . import _world_loop as loop
from . import motion_executor as motion
from .motion import solid_clearance as geometry

_PRODUCTION, _SOFTWARE, _TOKEN = object(), object(), object()
_MAX_NS = (1 << 63)-1


def _integer(value):
    if type(value) is not int or not 0 <= value <= _MAX_NS:
        raise ValueError('bounded original integer required')
    return value


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _operation(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        if threading.get_ident() != self._thread:
            self.fail('foreign book call')
            raise RuntimeError('original book thread required')
        if self._fault.is_set() or self._state == 'FAILED' or self._busy:
            self.fail('book failed or reentered')
            raise RuntimeError('book failed or reentered')
        if self._state == 'RETIRED':
            self.fail('retired book use')
            raise RuntimeError('book has retired')
        self._busy = True
        try:
            return method(self, *args, **kwargs)
        except BaseException as error:
            self.fail(type(error).__name__)
            raise
        finally:
            self._busy = False
    return call


class _Sample:
    __slots__ = ('_book', '_draft', '_ended', '_handle')

    def __init__(self, key, book, draft):
        if key is not _TOKEN:
            raise ValueError('private original sample token required')
        self._book, self._draft = book, draft
        self._ended, self._handle = False, None


class _ADC:
    __slots__ = ('_sample', '_begin', '_previous', '_used')

    def __init__(self, key, sample, begin, previous):
        if key is not _TOKEN:
            raise ValueError('private original ADC handle required')
        self._sample, self._begin, self._previous = sample, begin, previous
        self._used = False


class _SourceBookCore:
    def __init__(self, key, owner, binding, field, source):
        from ...tools.diagnostic.causal_pl_exchange import CausalSourcePump
        if hasattr(self, '_mode') or key not in (_PRODUCTION, _SOFTWARE):
            raise ValueError('book cannot be rebound')
        if key is _PRODUCTION:
            if (type(self) is not RootSourceBook or type(owner) is not loop._RootWorldOwner
                    or owner._test is not False
                    or not any(owner is retained for retained in loop._RETAINED)
                    or not native.is_original_owner(owner._native)
                    or type(owner._clock) is not clocks.QpcHostClock):
                raise ValueError('original retained production Root/native/QPC required')
        elif (isinstance(owner, loop._RootWorldOwner)
                or getattr(owner, 'software_fixture_only', None) is not True
                or getattr(owner._clock, 'software_fixture_only', None) is not True
                or native.is_original_owner(owner._native)):
            raise ValueError('software book cannot adopt actual Root/native')
        if type(field) is not OwnedWorldField or type(source) is not CausalSourcePump:
            raise ValueError('exact original field and source required')
        self._mode, self._owner, self._binding = key, owner, binding
        self._field, self._source = field, source
        self._clock, self._native = owner._clock, owner._native
        self._profile = source._profile
        self._pose_reader, self._sampler = source._pose_reader, source._sampler
        self._scope = source._em_scope_factory
        self._scene, self._pieces = field._scene, field._pieces
        self._policy = field._background, field._epsilon
        self._deadline = self._native._containment_deadline
        self._freeze = _raw(binding.epoch.identity)
        self._thread = threading.get_ident()
        self._fault = threading.Event()
        self._state, self._busy = 'NEW', False
        self._failure_reason = self._retire_reason = None
        self._origin = self._start_observed = None
        self._high = self._last_tick = self._last_count = 0
        self._last_tick = -1
        self._active = None
        self._samples, self._partials = [], []
        self._root = self._baseline = self._base_pose = self._pose_values = None
        self._veto_generation = None
        self._span_from = self._span_through = None
        try:
            if (source.state != 'NEW' or source._count != 0
                    or source._last_tick is not None or source._polling
                    or source._origin is not None or source._clock is not None
                    or self._profile._last_adc_tick is not None
                    or self._profile._last_em_tick is not None):
                raise ValueError('fresh unsampled source required')
            self._poll()
            root = field._check()
            begin = self._time()
            pose = self._pose_reader()
            end = self._time()
            self._poll()
            if field._check() is not root:
                raise ValueError('baseline committed root changed while read')
            self._root, self._veto_generation = root, owner._veto_generation
            self._base_pose = root.pose
            self._pose_values = (tuple(root.pose.position_m), tuple(root.pose.orientation_xyzw))
            self._baseline = dict(begin_qpc_ns=begin, end_qpc_ns=end,
                pose=self._pose_doc(pose), root_revision=root.revision,
                pose_revision=root.pose_revision, revoke_generation=root.revoke_generation)
            self._check()
            # begin was read after custody/root check; the post-read check proves
            # the same immutable root survived this initial bracket.
            self._span_from, self._span_through = begin, end
        except BaseException as error:
            self.fail(type(error).__name__)
            raise

    @property
    def source(self):
        return self._source

    @property
    def clock(self):
        return self._clock

    @staticmethod
    def _pose_doc(pose):
        if type(pose) is not forward.Pose:
            raise ValueError('original validated forward Pose required')
        return dict(position_m=list(pose.position_m),
                    orientation_xyzw=list(pose.orientation_xyzw))

    def _check(self):
        if self._fault.is_set():
            raise RuntimeError('book permanently failed')
        if threading.get_ident() != self._thread:
            raise ValueError('original book thread required')
        owner, source, field = self._owner, self._source, self._field
        if self._mode is _PRODUCTION:
            if (type(self) is not RootSourceBook or type(owner) is not loop._RootWorldOwner
                    or owner._test is not False
                    or not any(owner is retained for retained in loop._RETAINED)
                    or not native.is_original_owner(self._native)
                    or type(self._clock) is not clocks.QpcHostClock):
                raise ValueError('original production book custody lost')
            clocks._require_binding(self._clock)
        else:
            if (isinstance(owner, loop._RootWorldOwner)
                    or getattr(owner, 'software_fixture_only', None) is not True
                    or getattr(self._clock, 'software_fixture_only', None) is not True
                    or native.is_original_owner(owner._native)):
                raise ValueError('software book custody lost')
            self._clock._check()
        if (owner._clock is not self._clock or owner._native is not self._native
                or owner._thread != self._thread or owner._busy
                or owner._foreign.is_set() or owner._vetoed or not owner._initialized
                or self._native._retired or self._native.state != 'AUTHENTICATED'
                or self._native.clock_binding is not self._clock
                or self._native._containment_deadline != self._deadline
                or owner._native_observation is None
                or owner._native_observation.alive is not True
                or (owner._publication is not None and not owner._publication.resolved)):
            raise ValueError('original initialized healthy world required')
        loop._RootWorldOwner._known_binding(owner, self._binding)
        if self._mode is _PRODUCTION:
            # Fixed original owner API; no caller-supplied gate or callback.
            loop._RootWorldOwner.require_source_pose_current(owner)
        elif hasattr(type(owner), 'require_source_pose_current'):
            # Optional explicit software-fixture API only. Legacy software
            # fixture absence never weakens the mandatory production check.
            type(owner).require_source_pose_current(owner)
        if _raw(self._binding.epoch.identity) != self._freeze:
            raise ValueError('original epoch/freeze changed')
        if (source._thread != self._thread or source.state not in ('NEW', 'RUNNING')
                or source._profile is not self._profile
                or type(self._profile) is not forward.ForwardProfile
                or source._pose_reader is not self._pose_reader
                or source._sampler is not self._sampler
                or type(self._pose_reader) is not MethodType
                or self._pose_reader.__func__ is not OwnedWorldField.pose_reader
                or self._pose_reader.__self__ is not field
                or type(self._sampler) is not MethodType
                or self._sampler.__func__ is not OwnedWorldField.sample_sigma
                or self._sampler.__self__ is not field
                or field._executor is not self._binding.executor
                or field._scene is not self._scene
                or self._binding.world_values.scene is not self._scene
                or field._pieces is not self._pieces
                or (field._background, field._epsilon) != self._policy
                or source._em_scope_factory is not self._scope
                or field._em_scope_factory is not self._scope):
            raise ValueError('original field/source/profile/method association required')
        if self._scope is not None:
            if (type(self._scope) is not loop._OriginalEmScopeFactory
                    or self._scope._owner is not owner
                    or self._scope._binding is not self._binding
                    or self._scope._field is not field or self._scope._source is not source
                    or self._scope._profile is not self._profile
                    or self._scope._clock is not self._clock
                    or self._scope._native is not self._native
                    or self._scope._fault.is_set()):
                raise ValueError('original registered EM scope association required')
        root = field._check()
        view = self._binding.executor.renderer_view()
        if (type(root) is not motion._Root or view.pose is not root.pose
                or view.pose_revision != root.pose_revision
                or self._binding.executor._busy
                or geometry._digest(self._scene) != field._scene_digest
                or self._scene.digest != field._scene_digest):
            raise ValueError('original committed root/pose/scene required')
        if self._root is not None and (root is not self._root
                or root.pose is not self._base_pose
                or (tuple(root.pose.position_m), tuple(root.pose.orientation_xyzw)) != self._pose_values
                or root.revision != self._baseline['root_revision']
                or root.pose_revision != self._baseline['pose_revision']
                or root.revoke_generation != self._baseline['revoke_generation']
                or owner._veto_generation != self._veto_generation):
            raise ValueError('fixed baseline revision changed; actions unavailable')
        if source.state == 'RUNNING':
            if source._clock is not self._clock:
                raise ValueError('original source clock required')
            if self._origin is not None and source._origin != self._origin:
                raise ValueError('original source origin changed')
        return root

    def _time(self):
        now = _integer(self._clock())
        if now < self._high or now >= self._deadline:
            raise ValueError('original clock regressed or containment expired')
        if self._origin is not None and not 0 <= now-self._origin <= 10_000_000_000:
            raise ValueError('original source session expired')
        self._high = now
        return now

    def _poll(self):
        self._check()
        self._owner.poll()  # Explicit; never inside clock() or owner._busy.
        self._check()

    def _span(self, through):
        """Advance only after a real clock sample and a successful custody check."""
        self._check()
        if (self._span_from is None or through < self._span_through
                or through > self._high):
            raise ValueError('invalid fixed root interval checkpoint')
        self._span_through = through
        return dict(from_qpc_ns=self._span_from, through_qpc_ns=through,
                    root_revision=self._root.revision,
                    pose_revision=self._root.pose_revision)

    @_operation
    def current_pose_interval(self):
        """Read the actual fixed numerical pose; never a native/board receipt."""
        if self._state not in ('NEW', 'RUNNING') or self._active is not None:
            raise ValueError('idle original book required')
        self._poll()
        begin = self._time()
        pose = self._pose_reader()
        end = self._time()
        self._poll()
        span = self._span(end)
        return dict(pose=self._pose_doc(pose),
                    pose_revision=self._root.pose_revision,
                    at_qpc_ns=end,
                    pose_read=dict(begin_qpc_ns=begin, end_qpc_ns=end),
                    valid_span=span,
                    claim='numerical_immutable_committed_root_only',
                    native_interval_atomic=False)

    def _sample(self, token):
        if (type(token) is not _Sample or token._book is not self
                or token is not self._active or token._ended):
            raise ValueError('original active one-use sample token required')
        if (self._state != 'RUNNING' or self._source.state != 'RUNNING'
                or self._source._polling is not True
                or self._source._last_tick != token._draft['tick_ms']
                or self._source._count != token._draft['source_count']
                or self._source._high != token._draft['observed_source_qpc_ns']):
            raise ValueError('original consumed source slot changed')
        return token._draft

    @_operation
    def start(self):
        if (self._state != 'NEW' or self._source.state != 'RUNNING'
                or self._source._polling or self._source._count != 0
                or self._source._last_tick is not None):
            raise ValueError('once-only original source start required')
        self._poll()
        origin = _integer(self._source._origin)
        now = self._time()
        if (not self._baseline['end_qpc_ns'] <= origin <= now
                or now-origin > 10_000_000_000
                or self._source._high != origin):
            raise ValueError('original origin must follow actual baseline read')
        self._origin, self._start_observed = origin, now
        self._state = 'RUNNING'
        self._poll()

    @_operation
    def open_sample(self, tick_ms, observed_qpc_ns):
        tick, observed = _integer(tick_ms), _integer(observed_qpc_ns)
        if (self._state != 'RUNNING' or self._active is not None
                or tick % 10 or tick <= self._last_tick
                or self._source.state != 'RUNNING' or self._source._polling is not True
                or self._source._last_tick != tick
                or type(self._source._count) is not int
                or self._source._count != self._last_count+1
                or not 1 <= self._source._count <= 1001
                or self._source._high != observed):
            raise ValueError('fresh original consumed source prefix slot required')
        nominal = self._origin+tick*1_000_000
        if not nominal <= observed < nominal+10_000_000:
            raise ValueError('original observation must be in its real10ms bin')
        self._poll()
        opened = self._time()
        if opened < observed:
            raise ValueError('source observation is in the future')
        self._last_tick, self._last_count = tick, self._source._count
        token = _Sample(_TOKEN, self, dict(tick_ms=tick, source_count=self._last_count,
            nominal_qpc_ns=nominal, observed_source_qpc_ns=observed,
            opened_qpc_ns=opened, pose_reads={}, adc=None, status='open'))
        self._active = token
        self._poll()
        return token

    @_operation
    def read_pose(self, token, kind='em'):
        draft = self._sample(token)
        reads = draft['pose_reads']
        if (type(kind) is not str or kind not in ('em', 'adc') or kind in reads
                or token._handle is not None
                or (kind == 'em' and (draft['tick_ms'] % 50 or 'adc' in reads))
                or (kind == 'adc' and (draft['tick_ms'] % 50 == 0 and 'em' not in reads))
                or (kind == 'adc' and self._owner._em_scope_active is not None)):
            raise ValueError('original ordered EM/ADC pose read required')
        self._poll()
        begin = self._time()
        pose = self._pose_reader()
        end = self._time()
        root = self._root
        reads[kind] = dict(begin_qpc_ns=begin, end_qpc_ns=end,
            pose=self._pose_doc(pose), root_revision=root.revision,
            pose_revision=root.pose_revision, revoke_generation=root.revoke_generation,
            postcheck_complete=False)
        self._poll()
        reads[kind]['postcheck_complete'] = True
        return pose

    @_operation
    def begin_adc(self, token):
        draft = self._sample(token)
        if ('adc' not in draft['pose_reads'] or token._handle is not None
                or self._owner._em_scope_active is not None):
            raise ValueError('one ADC bracket after its actual pose read required')
        self._poll()
        previous = self._profile._last_adc_tick
        if previous is not None and previous >= draft['tick_ms']:
            raise ValueError('original ADC profile slot is not fresh')
        handle = _ADC(_TOKEN, token, self._time(), previous)
        token._handle = handle
        draft['adc'] = dict(begin_qpc_ns=handle._begin, end_qpc_ns=None,
            previous_adc_tick_ms=previous, profile_tick_observed=False)
        return handle

    @_operation
    def end_adc(self, token, handle):
        draft = self._sample(token)
        end = self._time()
        if draft['adc'] is not None:
            draft['adc']['end_attempt_qpc_ns'] = end
        if (type(handle) is not _ADC or token._handle is not handle
                or handle._sample is not token or handle._used
                or self._profile._last_adc_tick != draft['tick_ms']):
            raise ValueError('original ADC handle/profile progression required')
        handle._used = True
        draft['adc'].update(end_qpc_ns=end, profile_tick_observed=True,
                            postcheck_complete=False)
        self._poll()
        draft['adc']['postcheck_complete'] = True

    @_operation
    def finish_sample(self, token, payload):
        draft = self._sample(token)
        if (token._handle is None or not token._handle._used
                or draft['adc']['end_qpc_ns'] is None
                or 'adc' not in draft['pose_reads']
                or (draft['tick_ms'] % 50 == 0 and 'em' not in draft['pose_reads'])
                or self._profile._last_adc_tick != draft['tick_ms']):
            raise ValueError('complete original pose/ADC brackets required')
        self._poll()
        record = sensor_source.validate_record(payload)
        if record.adc_tick_ms != draft['tick_ms']:
            raise ValueError('payload must belong to this original tick')
        raw = _raw(asdict(record))
        if len(raw) > 4096:
            raise ValueError('bounded original canonical source record required')
        detached = json.loads(raw)
        sensor_source.validate_record(detached)
        draft.update(payload=detached, canonical_source_hex=raw.hex(),
            source_sha256=hashlib.sha256(raw).hexdigest())
        self._poll()
        end = self._time()
        self._check()
        span = self._span(end)
        points = [draft['nominal_qpc_ns'], draft['adc']['begin_qpc_ns'],
                  draft['adc']['end_qpc_ns']]
        for read in draft['pose_reads'].values():
            points.extend((read['begin_qpc_ns'], read['end_qpc_ns']))
        covered = all(span['from_qpc_ns'] <= t <= span['through_qpc_ns']
                      for t in points)
        draft.update(status='complete',
            numerical_pose_span=span if covered else None,
            numerical_pose_span_status=('available;fixed_numerical_root_only' if covered
                else 'unavailable;nominal_or_actual_outside_fixed_root_span'),
            held_em_association='unavailable;original_native_em_association_not_implemented',
            finish_qpc_ns=end, actual_adc_end_minus_nominal_ns=(
                draft['adc']['end_qpc_ns']-draft['nominal_qpc_ns']),
            baseline_span=dict(begin_qpc_ns=self._baseline['begin_qpc_ns'],
                end_qpc_ns=end, root_revision=self._root.revision,
                pose_revision=self._root.pose_revision,
                observation='same committed Root value at checks; not atomic native pose'))
        token._ended = True
        self._samples.append(draft)
        self._active = None

    def fail(self, reason):
        """Pure, non-throwing failure notice; never mask the caller's exception."""
        self._fault.set()
        if threading.get_ident() != self._thread:
            return  # Only contamination; original thread owns state retirement.
        if self._failure_reason is None:
            self._failure_reason = reason[:256] if type(reason) is str and reason else 'book failure'
        self._state = 'FAILED'
        self._source.state = 'FAILED'
        if self._active is not None:
            token = self._active
            token._ended = True
            token._draft.update(status='failed', failure_reason=self._failure_reason)
            self._partials.append(token._draft)
            self._active = None

    def retire(self, reason):
        """Retire only this book; Root retains source/world/resource cleanup."""
        if threading.get_ident() != self._thread:
            self.fail('foreign retirement')
            return
        if self._busy or self._fault.is_set() or self._active is not None:
            self.fail('book retired with failure or incomplete sample')
        else:
            self._state = 'RETIRED'
        self._retire_reason = reason[:256] if type(reason) is str and reason else 'book retired'

    def evidence(self):
        """Detached Root-private observations, with no I/O or authority claim."""
        if threading.get_ident() != self._thread:
            self.fail('foreign evidence read')
            raise RuntimeError('original evidence owner thread required')
        return json.loads(_raw(dict(schema=1,
            state='FAILED' if self._fault.is_set() else self._state,
            source_state=self._source.state, failure_reason=self._failure_reason,
            retire_reason=self._retire_reason, source_origin_qpc_ns=self._origin,
            start_observed_qpc_ns=self._start_observed, baseline=self._baseline,
            samples=self._samples, partial_samples=self._partials,
            active_sample=self._active._draft if self._active is not None else None,
            fixed_root_interval=(None if self._span_from is None else dict(
                from_qpc_ns=self._span_from, through_qpc_ns=self._span_through,
                root_revision=self._baseline['root_revision'],
                pose_revision=self._baseline['pose_revision'],
                claim='numerical_immutable_committed_root_only')),
            action_association='unavailable;fixed_revision_only',
            native_interval_atomic=False, source_scope='Root private candidate observations',
            adc_call_evidence='trusted caller bracket and retained profile tick progression')))


class RootSourceBook(_SourceBookCore):
    def __init__(self, owner, binding, field, source):
        if type(self) is not RootSourceBook:
            raise ValueError('exact production RootSourceBook required')
        super().__init__(_PRODUCTION, owner, binding, field, source)


def _software_source_book_for_test(owner, binding, field, source):
    """Different exact software core; cannot satisfy production book checks."""
    return _SourceBookCore(_SOFTWARE, owner, binding, field, source)


__all__ = ['RootSourceBook']
