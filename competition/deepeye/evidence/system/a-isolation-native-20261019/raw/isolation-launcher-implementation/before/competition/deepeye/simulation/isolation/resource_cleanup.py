"""One-shot cleanup of an explicit trusted-owner plan, with no OS backend.

All identities and provenance are assertions supplied by the future launcher.
This module cannot discover resources, attest ownership, or grant permission.
"""
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Callable, Protocol


class Outcome(Enum):
    CONFIRMED = 'confirmed'
    FAILED = 'failed'  # Backend definitively observed failure, not success.
    UNKNOWN = 'unknown'  # Effect may have happened: never automatically replay.


class CleanupRejected(RuntimeError):
    """This coordinator is running or has already attempted cleanup."""


@dataclass(frozen=True)
class Provenance:
    task_id: str
    work_id: str
    owner_id: str
    source_hashes: tuple[tuple[str, str], ...]

    def __post_init__(self):
        bindings = tuple(tuple(pair) for pair in self.source_hashes)
        if not all(isinstance(v, str) and v for v in (self.task_id, self.work_id, self.owner_id)):
            raise ValueError('task, work and owner identities must be nonempty strings')
        if not bindings or any(len(pair) != 2 or not isinstance(pair[0], str) or not pair[0]
                               or not isinstance(pair[1], str) or len(pair[1]) != 64
                               or any(c not in '0123456789abcdef' for c in pair[1]) for pair in bindings):
            raise ValueError('source bindings require named lowercase SHA256 digests')
        if len({pair[0] for pair in bindings}) != len(bindings):
            raise ValueError('duplicate source binding')
        object.__setattr__(self, 'source_hashes', bindings)


@dataclass(frozen=True)
class Resource:
    resource_id: str
    owner_id: str
    kind: str  # process, handle, thread, socket, profile
    identity: object  # Exact already-owned backend reference; never a guessed PID/path.
    profile_id: str | None = None
    recovery_for: tuple[str, ...] = ()  # Process identities whose recovery needs this resource.

    def __post_init__(self):
        object.__setattr__(self, 'recovery_for', tuple(self.recovery_for))


@dataclass(frozen=True)
class ErrorInfo:
    stage: str
    resource_id: str | None
    type_name: str
    message: str


@dataclass(frozen=True)
class Operation:
    action: str
    outcome: Outcome
    error: ErrorInfo | None = None


@dataclass(frozen=True)
class ResourceResult:
    resource: Resource
    closed: bool
    terminal_confirmed: bool
    operations: tuple[Operation, ...]
    blocked_reason: str | None


@dataclass(frozen=True)
class CleanupResult:
    provenance: Provenance
    primary_error: ErrorInfo | None
    resources: tuple[ResourceResult, ...]
    cleanup_errors: tuple[ErrorInfo, ...]
    audit_errors: tuple[ErrorInfo, ...]
    resources_complete: bool
    evidence_complete: bool
    success: bool

    @property
    def unresolved(self) -> tuple[str, ...]:
        return tuple(row.resource.resource_id for row in self.resources if not row.closed)


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    provenance: Provenance
    phase: str
    action: str
    resource_id: str | None = None
    operation: Operation | None = None
    primary_error: ErrorInfo | None = None
    result: CleanupResult | None = None


class Backend(Protocol):
    """Implement bounded calls on exact owned identities; exceptions mean UNKNOWN.

    CONFIRMED close/remove means independently confirmed closed/removed, not just
    a request acknowledgement. wait_terminal performs an actual terminal readback
    on the held process identity and returns the literal bool True only if proven.
    """
    def terminate(self, resource: Resource) -> Outcome: ...
    def wait_terminal(self, resource: Resource) -> bool | None: ...
    def close(self, resource: Resource) -> Outcome: ...
    def remove_profile(self, resource: Resource) -> Outcome: ...


def _error(stage, resource_id, error):
    try:
        message = str(error)
    except BaseException:
        message = '<exception text unavailable>'
    return ErrorInfo(stage, resource_id, type(error).__name__, message)


class CleanupCoordinator:
    """Synchronous, single-attempt coordinator. No automatic recovery/retry API.

    Backend and sink must be supplied explicitly. A sink return acknowledges its
    serialization/flush/durability contract; any exception is evidence incomplete.
    Logging never prevents a safe cleanup callback. Lock only guards local reentry;
    it does not lock OS resources or coordinate separate coordinator instances.
    """
    def __init__(self, provenance: Provenance, resources: tuple[Resource, ...],
                 backend: Backend, report_sink: Callable[[AuditEvent], None]):
        plan = tuple(resources)
        if not isinstance(provenance, Provenance) or backend is None or not callable(report_sink):
            raise ValueError('explicit provenance, backend and report sink required')
        if any(not callable(getattr(backend, name, None)) for name in
               ('terminate', 'wait_terminal', 'close', 'remove_profile')):
            raise ValueError('incomplete backend')
        if any(not isinstance(r, Resource) or not isinstance(r.resource_id, str) or not r.resource_id
               or r.owner_id != provenance.owner_id or r.identity is None
               or r.kind not in ('process', 'handle', 'thread', 'socket', 'profile') for r in plan):
            raise ValueError('invalid resource identity, kind or owner')
        by_id = {r.resource_id: r for r in plan}
        if len(by_id) != len(plan):
            raise ValueError('duplicate resource identity')
        if len({id(r.identity) for r in plan}) != len(plan):
            raise ValueError('same exact owned reference registered twice')
        for r in plan:
            if r.profile_id is not None and (r.kind == 'profile' or r.profile_id not in by_id
                                            or by_id[r.profile_id].kind != 'profile'):
                raise ValueError('invalid profile dependency')
            if r.recovery_for and (r.kind in ('process', 'profile') or any(
                    p not in by_id or by_id[p].kind != 'process' for p in r.recovery_for)):
                raise ValueError('invalid recovery dependency')
        self._provenance, self._plan = provenance, plan
        self._backend, self._sink = backend, report_sink
        self._lock = Lock()
        self._attempted = False

    def cleanup(self, primary_error: BaseException | None = None) -> CleanupResult:
        if not self._lock.acquire(blocking=False):
            raise CleanupRejected('cleanup already running')
        try:
            if self._attempted:
                raise CleanupRejected('cleanup already attempted; reconcile retained ownership explicitly')
            self._attempted = True
            # Freeze the original error before the first sink or backend callback.
            primary = None if primary_error is None else _error('primary', None, primary_error)
            cleanup_errors, audit_errors = [], []
            closed, terminal, operations, blocked = {}, {}, {}, {}
            for resource in self._plan:
                name = resource.resource_id
                closed[name], terminal[name], operations[name] = False, False, []
            sequence = 0

            def emit(phase, action, resource_id=None, operation=None, result=None):
                nonlocal sequence
                sequence += 1
                event = AuditEvent(sequence, self._provenance, phase, action, resource_id,
                                   operation, primary, result)
                try:
                    self._sink(event)
                except BaseException as exc:
                    audit_errors.append(_error('audit:' + phase + ':' + action, resource_id, exc))

            def step(action, resource):
                name = resource.resource_id
                emit('before', action, name)
                error = None
                try:
                    value = getattr(self._backend, action)(resource)
                    if action == 'wait_terminal':
                        if value is True:
                            outcome = Outcome.CONFIRMED
                        elif value is False:
                            outcome = Outcome.FAILED
                        else:
                            outcome = Outcome.UNKNOWN
                    else:
                        outcome = value if type(value) is Outcome else Outcome.UNKNOWN
                    if outcome is not Outcome.CONFIRMED:
                        error = ErrorInfo(action, name, 'UnconfirmedOutcome', outcome.value)
                except BaseException as exc:
                    outcome, error = Outcome.UNKNOWN, _error(action, name, exc)
                if error is not None:
                    cleanup_errors.append(error)
                operation = Operation(action, outcome, error)
                operations[name].append(operation)
                emit('after', action, name, operation)
                return outcome is Outcome.CONFIRMED

            def retain(resource, reason):
                blocked[resource.resource_id] = reason
                emit('blocked', reason, resource.resource_id)

            def snapshot():
                rows = tuple(ResourceResult(r, closed[r.resource_id], terminal[r.resource_id],
                                            tuple(operations[r.resource_id]), blocked.get(r.resource_id))
                             for r in self._plan)
                resources_complete = all(row.closed for row in rows)
                evidence_complete = not audit_errors
                success = resources_complete and evidence_complete and primary is None and not cleanup_errors
                return CleanupResult(self._provenance, primary, rows, tuple(cleanup_errors),
                                     tuple(audit_errors), resources_complete, evidence_complete, success)

            emit('start', 'cleanup')
            for resource in self._plan:
                if resource.kind != 'process':
                    continue
                # A failed/unknown termination must not suppress independent readback.
                step('terminate', resource)
                terminal[resource.resource_id] = step('wait_terminal', resource)
                if terminal[resource.resource_id]:
                    closed[resource.resource_id] = step('close', resource)
                else:
                    retain(resource, 'terminal_unconfirmed')
            for resource in self._plan:
                if resource.kind in ('process', 'profile'):
                    continue
                if any(not terminal[p] for p in resource.recovery_for):
                    retain(resource, 'recovery_control_required')
                else:
                    closed[resource.resource_id] = step('close', resource)
            for resource in self._plan:
                if resource.kind != 'profile':
                    continue
                if any(not closed[r.resource_id] for r in self._plan if r.profile_id == resource.resource_id):
                    retain(resource, 'profile_dependents_unresolved')
                else:
                    closed[resource.resource_id] = step('remove_profile', resource)
            emit('finish', 'cleanup', result=snapshot())
            # The final sink can fail too: return a fresh snapshot including that error.
            return snapshot()
        finally:
            self._lock.release()
