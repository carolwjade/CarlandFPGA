"""Optional one-way display updates on Root's existing original world channel.

No acquisition, authority, motion, reply, retry, cleanup or second reader. Queue
only between original operations; Root advances this before blocking work. A
completed Transmission proves transport_written, never presenter/pixel success.
DEEPEYE-HUMAN-LOCK-20261014/revision1 and H01-H15 remain unchanged.
"""
import base64
from dataclasses import dataclass, field
import json
import math
import threading

from ..run_causal_functional_chain import FunctionalWorld, FunctionalSource
from ...integration.host_clock import QpcHostClock
from ...simulation.authority import _world_loop as loop, _owned_godot as native_module
from ...simulation.authority import _world_wire as wire
from ...simulation.authority.original_world_actor_link import _OriginalWorldActorLink

MAX_TRANSPORT_NS = 2_000_000_000  # Transport bound, unrelated to final 100ms metrics.
_RESERVED_TRANSMISSIONS = 16
_STAGES = ('sensor','board_compression','upload_decode','ai_decision','board_readback','motion')
_DATA = frozenset(('raw','encoded','decoded','source_time','reconstruction_error',
                  'compression_ratio','quality_note','board','build','latency','codec_mode','e0_match'))
_KEY = object()
_RETAINED = []  # Original attempts stay available after unknown side effects.


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def encode_demo30h_status(status):
    """Copy only bounded display fields; force the unwired Run readiness false."""
    _need(type(status) is dict and set(status) == {'connection','coordinator_ready','stages','data'},
          'exact display status fields required')
    _need(type(status['connection']) is str and status['connection'] in
          ('disconnected','pending','connected','failed'), 'display connection enum required')
    _need(type(status['coordinator_ready']) is bool, 'strict display readiness bool required')
    stages, data = status['stages'], status['data']
    _need(type(stages) is dict and set(stages) == set(_STAGES) and all(type(v) is str and
          v in ('pending','observed','failed','disconnected') for v in stages.values()),
          'exact bounded display stages required')
    _need(type(data) is dict and set(data) <= _DATA, 'bounded display data keys required')
    for value in data.values():
        _need(type(value) in (str,int,float,bool,type(None)), 'display scalar required')
        if type(value) is str:
            _need(len(value) <= 160 and all(ord(c) >= 32 for c in value), 'bounded display text required')
        if type(value) is float:
            _need(math.isfinite(value), 'finite display number required')
        if type(value) is int:
            _need(-(1<<63) <= value < (1<<63), 'bounded display integer required')
    clean = dict(connection=status['connection'],coordinator_ready=False,stages=dict(stages),data=dict(data))
    try:
        raw = json.dumps(clean,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
    except (UnicodeError,ValueError,TypeError) as error:
        raise ValueError('strict UTF8 display JSON required') from error
    _need(1 <= len(raw) <= wire.MAX_UI_STATUS, 'display JSON bytes over budget')
    return raw


@dataclass(eq=False)
class UiStatusSend:
    world: object
    owner: object
    native: object
    source: object
    binding: object
    epoch: object
    deadline_ns: int
    status: str = 'deferred'
    reason: str | None = None
    transmission: object = None
    message: object = None
    lower_qpc_ns: int | None = None
    upper_qpc_ns: int | None = None
    error: object = None
    _key: object = field(default=None,repr=False)
    _thread: int = field(default_factory=threading.get_ident,repr=False)

    def __post_init__(self):
        _need(self._key is _KEY, 'original UI sender result required')

    def __reduce__(self):
        raise TypeError('original UI transmission cannot be serialized or adopted')

    def snapshot(self):
        tx = self.transmission
        return dict(status=self.status,reason=self.reason,ui_displayed=False,authority='not_evaluated',
            resumable=False,deadline_ns=self.deadline_ns,lower_qpc_ns=self.lower_qpc_ns,
            upper_qpc_ns=self.upper_qpc_ns,operation_id=None if self.message is None else self.message['operation_id'],
            transmission_sequence=None if tx is None else tx.sequence,
            transmission_started=None if tx is None else tx.started,
            transmission_complete=None if tx is None else tx.complete,
            transmission_failed=None if tx is None else tx.failed,
            error_type=None if self.error is None else type(self.error).__name__)


class UiStatusTransportError(ValueError):
    def __init__(self,cause,attempt):
        super().__init__('original UI transport failed; retained original attempt, no replay')
        self.cause,self.attempt = cause,attempt


def _original_graph(world):
    _need(type(world) is FunctionalWorld and type(world.source) is FunctionalSource,
          'exact original functional world/source required')
    f,o,b,c = world.source,world.owner,world.binding,world.clock
    _need(type(o) is loop._RootWorldOwner and type(f.link) is _OriginalWorldActorLink
          and type(c) is QpcHostClock and world._thread == f._thread == o._thread == threading.get_ident(),
          'same original world owner thread/QPC required')
    _need(not world._close_attempted and not o._foreign.is_set() and not o._vetoed
          and o._state in ('FROZEN','BOUND_STOPPED') and o._clock is c and f.clock is c
          and f.owner is o and f.binding is b and o._binding is b
          and f.link.owner is o and f.link.binding is b, 'live original world association required')
    n = o._native
    _need(type(n) is native_module._OwnedGodot and native_module.is_original_owner(n)
          and n is f.link.native and n.clock_binding is c and n._thread == o._thread
          and not n._foreign and not n._retired and n.state == 'AUTHENTICATED'
          and n.hello is not None and n._channel is not None and n._channel._failure is None,
          'healthy original authenticated native channel required')
    c._check()
    _need(o._publication is not None, 'original initial publication required')
    return f,o,b,n


def _busy_reason(f,o,n):
    if o._busy or n._busy or f.source._polling or o._em_scope_active is not None:
        return 'original_owner_busy'
    if o._inflight_frames or o._freeze_request is not None or o._assembly is not None or o._retirement is not None:
        return 'original_operation_pending'
    if not o._publication.resolved or o._publication.state != 'APPLIED' or f._pending is not None:
        return 'original_publication_or_sample_pending'
    return None


def _current_binding(f,o,b):
    o._known_binding(b)
    o._known_epoch(b.epoch)
    f.link._registered()
    _need(b.epoch is o._epoch and str(b.epoch.number) == b.epoch.identity['world_epoch'],
          'same current original frozen epoch required')


def queue_demo30h_status(world,status,*,deadline_ns):
    """Queue once, or return deferred without allocating an operation or frame.

    deadline_ns is an explicit absolute QPC deadline, at most 2s from now; it is
    tightened to original containment. Root should normally allow 250-500ms,
    advance promptly and complete this optional update before board/AI blocking.
    """
    raw = encode_demo30h_status(status)
    _need(type(deadline_ns) is int and 0 < deadline_ns < (1<<63), 'strict transport deadline required')
    f,o,b,n = _original_graph(world)
    now = world.clock()
    _need(0 < deadline_ns-now <= MAX_TRANSPORT_NS, 'short unexpired UI transport deadline required')
    deadline = min(deadline_ns,n._containment_deadline)
    _need(now < deadline, 'original containment already expired')
    result = UiStatusSend(world,o,n,f,b,b.epoch,deadline,_key=_KEY)
    reason = _busy_reason(f,o,n)
    if reason is None and not n.healthy_frame_aligned():
        reason = 'original_frame_pending'
    if reason is None and (len(n._channel._transactions) >= 4096-_RESERVED_TRANSMISSIONS
                           or o._serial >= 8192-_RESERVED_TRANSMISSIONS or len(_RETAINED) >= 1024):
        reason = 'control_transport_budget_reserved'
    if reason is not None:
        result.reason = reason
        return result
    _current_binding(f,o,b)
    # Complete status/message validation precedes send and cannot poison the
    # original channel. The existing allocator owns operation uniqueness.
    result.message = o._message('UI_STATUS',dict(freeze_id=b.epoch.identity['freeze_id'],
                               status_base64=base64.b64encode(raw).decode('ascii')),epoch=b.epoch.number)
    wire.encode_payload(result.message)
    result.lower_qpc_ns = world.clock()
    result.status = 'transport_pending'
    _RETAINED.append(result)  # Before the only fallible original send.
    try:
        result.transmission = n.send(result.message,deadline_ns=deadline)
        _need(type(result.transmission) is wire.Transmission, 'original Transmission required')
        return result
    except BaseException as error:
        pending = n._channel._pending
        if result.transmission is None and type(pending) is wire.Transmission:
            result.transmission = pending
        result.error,result.status = error,'transport_unknown'
        raise UiStatusTransportError(error,result) from error


def advance_demo30h_status(attempt):
    """One original owner.poll, then original complete_tx; no wait/reader/retry."""
    _need(type(attempt) is UiStatusSend and attempt._key is _KEY
          and threading.get_ident() == attempt._thread, 'same original UI transmission owner required')
    if attempt.status == 'transport_written':
        return attempt
    _need(attempt.status == 'transport_pending' and type(attempt.transmission) is wire.Transmission
          and any(item is attempt for item in _RETAINED), 'pending original UI attempt required; no replay')
    try:
        f,o,b,n = _original_graph(attempt.world)
        _need(f is attempt.source and o is attempt.owner and b is attempt.binding
              and n is attempt.native and b.epoch is attempt.epoch, 'original UI association changed')
        reason = _busy_reason(f,o,n)
        if reason is not None:
            attempt.reason = reason
            return attempt
        _current_binding(f,o,b)
        _need(not attempt.transmission.failed and (attempt.transmission.complete
              or n._channel._pending is attempt.transmission), 'original pending UI frame changed')
        o.poll()  # Sole existing reader handles genuine STOP/status/readback.
        if n.complete_tx(attempt.transmission):
            attempt.status,attempt.reason = 'transport_written',None
            attempt.upper_qpc_ns = attempt.world.clock()
        return attempt
    except BaseException as error:
        attempt.error,attempt.status = error,'transport_unknown'
        raise UiStatusTransportError(error,attempt) from error
