"""Closed trusted composition library; production activation is unavailable.

No real readiness/channel/model provider is installed. The production gate
rejects before registry construction, stage or native acquisition. Private
test seams establish software sequencing only; see docs/actor_composition.md.
"""
from dataclasses import dataclass
from functools import wraps
import threading
from time import monotonic_ns

from ..isolation.actor_owner import ActorPolicy, ActorRegistry
from .motion_executor import OwnedMotionExecutor
from .pc_direct_runtime import (AuthorityDependencies, BootBinding, PcDirectRuntime,
                                VerifiedEnvelope, VerifiedObservation)
from ...integration import host_envelope


class ActivationUnavailable(ValueError):
    """The original authenticated production dependencies do not exist yet."""


class CompositionRejected(ValueError):
    """Sanitized public refusal; private exceptions stay with the owner."""


@dataclass(frozen=True)
class AuthorityConfig:
    """Explicit trusted-main configuration, not a credential or controller input."""
    actor_policy: ActorPolicy
    initial_state: object
    scene: object
    model: object
    budget: object
    heartbeat_timeout_ns: int
    max_slices: int


@dataclass(frozen=True)
class CompositionStatus:
    state: str


@dataclass(frozen=True)
class StepOutcome:
    committed: bool
    pose_revision: int | None


_FACTORY = object()
_RETAINED = []  # Strong recovery ownership before any acquisition; no auto-eviction.


def _production_channels(config):
    # No callable/provider supplied by a caller can bypass this gate.
    raise ActivationUnavailable('original authenticated AI/channel/package unavailable')


def _entry(method):
    @wraps(method)
    def call(self, /, *args, **kwargs):
        if type(self) is not ActorComposition:
            raise CompositionRejected('original composition required')
        if threading.get_ident() != self._thread:
            self._foreign.set()  # No cross-thread native/authority operations.
            raise CompositionRejected('authority owner thread required')
        if self._busy:
            error = CompositionRejected('reentrant composition entry')
            self._remember(error)
            self._retire('reentrant composition entry')
            raise error
        self._busy = True
        terminal = method.__name__ in ('close', 'stop', 'status')
        try:
            if self._foreign.is_set():
                raise CompositionRejected('foreign-thread veto pending')
            epoch = self._veto
            if not terminal:
                self._checkpoint()
            result = method(self, *args, **kwargs)
            if not terminal:
                self._checkpoint(epoch)
            return result
        except BaseException as error:
            self._remember(error)
            self._retire('composition entry rejected')
            if method.__name__ == 'step':
                return StepOutcome(False, None)
            raise CompositionRejected('composition rejected; admission retired') from None
        finally:
            self._busy = False
            if self._retired:
                self._cleanup()
    return call


class _Dependencies(AuthorityDependencies):
    """Fixed actor/executor targets. Channel verifiers cannot supply either."""
    def __init__(self, owner): self._owner = owner

    def verify_boot(self, event):
        owner = self._owner
        owner._checkpoint()
        if (owner._state != 'ACTIVATING' or event is not owner._boot_event or owner._boot_taken):
            raise ValueError('original single-use activation event required')
        owner._boot_taken = True
        return owner._boot

    def _verify(self, name, event, boot, kind):
        owner = self._owner
        owner._active()
        if boot is not owner._boot: raise ValueError('original composition BOOT required')
        epoch = owner._veto
        record = getattr(owner._channels, name)(event, boot)
        owner._checkpoint(epoch)
        if type(record) is not kind or record.boot is not boot or type(record.raw) is not bytes:
            raise ValueError('original verified channel record required')
        return record

    def verify_board(self, event, boot):
        return self._verify('verify_board', event, boot, VerifiedEnvelope)

    def verify_observation(self, event, boot):
        return self._verify('verify_observation', event, boot, VerifiedObservation)

    def verify_command(self, event, boot):
        record = self._verify('verify_command', event, boot, VerifiedEnvelope)
        self._owner._command_record = record
        return record

    def ai_lease(self, boot, now_ns):
        owner = self._owner
        owner._active()
        epoch = owner._veto
        # The only lifetime target: no channel/provider fallback or cached lease.
        result = owner._actor.ai_lease(boot, now_ns)
        owner._checkpoint(epoch)
        return result

    def prepare_step(self, boot, command_raw, expected_pose_revision, dt_ns):
        owner = self._owner
        owner._active(); epoch = owner._veto
        result = owner._executor.prepare_step(boot, command_raw, expected_pose_revision, dt_ns)
        owner._checkpoint(epoch)
        return result

    def commit_step(self, prepared, before_commit):
        self._owner._active()
        # No work is inserted between executor's final callback and its CAS.
        return self._owner._executor.commit_step(prepared, before_commit)


class ActorComposition:
    """One owner thread, one acquisition, one closed activation transaction.

    Only create_authority constructs this library owner. These Python objects
    must remain authority-private; naming/frozen dataclasses are not isolation.
    """
    def __init__(self, key, config, channels):
        if key is not _FACTORY: raise CompositionRejected('trusted factory required')
        self._thread = threading.get_ident()
        self._config, self._channels = config, channels
        self._foreign = threading.Event()
        self._state, self._busy, self._retired = 'STARTING', False, False
        self._veto, self._revoking, self._cleanup_attempted = 0, False, False
        self._registry = self._actor = self._runtime = self._executor = None
        self._runtime_activation = self._executor_activation = None
        self._boot = self._boot_event = self._command_record = None
        self._boot_taken = False
        self._primary_error, self._errors, self._last_step = None, [], None

    def _remember(self, error):
        if self._primary_error is None: self._primary_error = error

    def _checkpoint(self, epoch=None):
        if self._foreign.is_set() or self._retired or (epoch is not None and epoch != self._veto):
            raise CompositionRejected('composition activation vetoed')

    def _active(self):
        self._checkpoint()
        if self._state != 'ACTIVE': raise ValueError('complete activation required')

    def _dispatch_stop(self, reason):
        if self._revoking: return
        self._revoking = True
        try:
            try:
                if (self._runtime_activation is not None and self._runtime is not None and
                        self._runtime._boot is self._runtime_activation):
                    self._runtime.stop(reason)
            except BaseException as error:
                self._errors.append(error)
            finally:
                try:
                    # Check AFTER STOP; its callback can activate a successor.
                    if (self._executor_activation is not None and self._executor is not None and
                            self._executor._root.boot is self._executor_activation):
                        self._executor.revoke(reason)
                except BaseException as error:
                    self._errors.append(error)
        finally:
            self._revoking = False

    def _retire(self, reason):
        self._veto += 1
        self._retired = True  # Gate first, before callbacks or cleanup.
        if self._state not in ('CLOSED', 'QUARANTINED'): self._state = 'RETIRED'
        self._dispatch_stop(reason)

    def _cleanup(self):
        if self._cleanup_attempted: return
        self._cleanup_attempted = True
        # A failed registry.launch can own a process before returning an actor.
        actors = tuple(self._registry._owners) if self._registry is not None else ()
        complete = True
        for actor in actors:
            try:
                actor.close('composition retired')
                if actor.state != 'CLOSED': complete = False
            except BaseException as error:
                self._errors.append(error); complete = False
        self._state = 'CLOSED' if complete and not self._errors else 'QUARANTINED'

    @_entry
    def _start(self):
        config = self._config
        self._registry = ActorRegistry()
        self._checkpoint()
        self._executor = OwnedMotionExecutor(initial_state=config.initial_state, scene=config.scene,
            model=config.model, budget=config.budget, max_slices=config.max_slices)
        self._runtime = PcDirectRuntime(run_id=config.actor_policy.run_id,
            dependencies=_Dependencies(self), clock=monotonic_ns,
            heartbeat_timeout_ns=config.heartbeat_timeout_ns)
        self._checkpoint()
        self._actor = self._registry.launch(config.actor_policy)
        self._checkpoint()
        self._state = 'RUNNING_UNBOUND'

    @_entry
    def accept_boot(self, event):
        if self._state != 'RUNNING_UNBOUND': raise ValueError('activation is single use')
        epoch = self._veto
        proposed = self._channels.verify_boot(event, run_id=self._config.actor_policy.run_id,
                                             instance_id=self._actor.instance_id)
        self._checkpoint(epoch)
        if (type(proposed) is not BootBinding or proposed.run_id != self._config.actor_policy.run_id or
                proposed.ai_instance != self._actor.instance_id):
            raise ValueError('original independently verified binding required')
        self._boot, self._boot_event = proposed, event
        self._state = 'ACTIVATING'
        # Intended original activations are captured before either call; never
        # adopt whatever successor an exceptional callback leaves behind.
        self._runtime_activation = self._executor_activation = proposed
        self._runtime.boot(event)
        self._checkpoint(epoch)
        self._executor.activate_boot(proposed)
        self._checkpoint(epoch)
        self._actor.bind_verified_boot(proposed, runtime=self._runtime, executor=self._executor)
        self._checkpoint(epoch)
        self._channels.checkpoint()
        self._checkpoint(epoch)
        self._actor.poll()
        self._checkpoint(epoch)
        self._state = 'ACTIVE'

    def _channel_health(self):
        epoch = self._veto
        self._channels.checkpoint()
        self._checkpoint(epoch)

    def _runtime_active(self):
        if self._runtime._latched: raise ValueError('runtime stopped')

    @_entry
    def accept_board(self, event):
        self._active(); self._channel_health()
        self._runtime.board(event)
        self._runtime_active()

    @_entry
    def accept_observation(self, event):
        self._active(); self._channel_health()
        self._runtime.observe(event)
        self._runtime_active()

    @_entry
    def accept_command(self, event):
        self._active(); self._channel_health()
        self._command_record = None
        self._runtime.command(event)
        self._checkpoint()
        record = self._command_record
        if record is None: raise ValueError('original command admission missing')
        document = host_envelope._parse_message(record.raw)
        if document['target']['action'] == 0:
            self._retire('broker STOP')
            return
        self._runtime_active()
        self._executor.admit_command(self._boot, record.raw)

    @_entry
    def step(self, *, expected_pose_revision, dt_ns):
        self._active(); self._channel_health()
        result = self._runtime.step(expected_pose_revision=expected_pose_revision, dt_ns=dt_ns)
        self._last_step = result  # Private; raw geometry failure is never public.
        if not result.committed:
            self._retire('runtime step did not commit')
            return StepOutcome(False, None)
        return StepOutcome(True, result.receipt.pose_revision)

    @_entry
    def poll(self):
        self._channel_health()
        self._actor.poll()

    @_entry
    def stop(self, reason):
        if type(reason) is not str or not reason: raise ValueError('explicit reason required')
        self._retire('external STOP')

    @_entry
    def close(self, reason):
        if type(reason) is not str or not reason: raise ValueError('explicit reason required')
        self._retire('composition close')

    @_entry
    def status(self):
        return CompositionStatus(self._state)


def create_authority(config):
    """Production factory: unavailable authentication rejects before acquisition.

    No public dependency/verifier/provider/adoption options. Tests patch only
    module-private factories and the existing fake native boundary.
    """
    if type(config) is not AuthorityConfig or type(config.actor_policy) is not ActorPolicy:
        raise CompositionRejected('explicit trusted authority configuration required')
    channels = _production_channels(config)  # Must precede ActorRegistry construction.
    owner = ActorComposition(_FACTORY, config, channels)
    _RETAINED.append(owner)
    owner._start()
    return owner


__all__ = ['AuthorityConfig', 'CompositionStatus', 'StepOutcome', 'create_authority',
           'ActivationUnavailable', 'CompositionRejected']
