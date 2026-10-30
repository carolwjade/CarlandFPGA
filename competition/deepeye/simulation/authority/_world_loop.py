"""Private original-world diagnostic loop, never a genuine channel provider.

The fixed factory acquires its own original native owner on this same thread.
Values, IDs, hashes and BootBinding records alone convey no owner capability.
The separate test factory rejects actual native owners and labels all outcomes
software-only. Production create_authority and motion CAS remain unchanged.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction as F
from functools import wraps
import hashlib
import json
import math
import struct
import threading

from ...integration import host_clock as clocks
from . import _owned_godot as native
from . import _world_values as values
from . import _world_wire as wire
from . import motion_executor as motion
from .pc_direct_runtime import StepFence
from .motion.kinematics import RigidState
from .motion import solid_clearance as solids

_FACTORY = object()
_TEST_FACTORY = object()
_RETAINED = []
_MAX_NS = (1 << 63) - 1
COMMAND_NS = 100_000_000
STEP_NS = 10_000_000
VIEW_NS = 5_000_000_000
CONSTRUCT_NS = 120_000_000_000
FREEZE_NS = 120_000_000_000


class WorldRejected(ValueError):
    pass


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= _MAX_NS:
        raise WorldRejected('bounded strict integer required')
    return value


def _raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _identity(snapshot):
    return {key: str(value) if type(value) is int else value
            for key, value in asdict(snapshot.freeze_identity).items()}


def _f64(value):
    if not math.isfinite(float(value)):
        raise WorldRejected('finite desired pose required')
    return struct.pack('>d', float(value)).hex()


def _desired(view):
    pose = view.pose
    rotation = solids._rotation(tuple(map(F, pose.orientation_xyzw)))
    transform = dict(basis_columns=[[_f64(rotation[row][column]) for row in range(3)]
                                    for column in range(3)],
                     origin=[_f64(value) for value in pose.position_m])
    return dict(position_m=[_f64(x) for x in pose.position_m],
                orientation_xyzw=[_f64(x) for x in pose.orientation_xyzw],
                speed_m_s=_f64(pose.speed_m_s)), transform


def _getter_differences(expected, actual, width):
    """Exact differences are observations, not a manufactured engine error bound."""
    def scalar(token, bits):
        if type(token) is not str or len(token) != bits // 4:
            raise WorldRejected('actual getter scalar width mismatch')
        number = struct.unpack('>f' if bits == 32 else '>d', bytes.fromhex(token))[0]
        if not math.isfinite(number):
            raise WorldRejected('nonfinite actual getter')
        return F(number)
    result = []
    for key in ('basis_columns', 'origin'):
        desired = expected[key]
        observed = actual[key]
        if key == 'basis_columns':
            desired = [x for column in desired for x in column]
            observed = [x for column in observed for x in column]
        if len(desired) != len(observed):
            raise WorldRejected('incomplete actual getter')
        for wanted, got in zip(desired, observed):
            difference = scalar(got, width) - scalar(wanted, 64)
            result.append((difference.numerator, difference.denominator))
    return tuple(result)


@dataclass(frozen=True, eq=False)
class _FrozenEpoch:
    owner: object
    number: int
    freeze_operation: str
    identity: object
    snapshot_raw: bytes
    snapshot: object
    completed_ns: int


@dataclass(frozen=True, eq=False)
class _Binding:
    owner: object
    epoch: _FrozenEpoch
    world_values: object
    executor: object
    constructor_entry_ns: int
    constructor_exit_ns: int


@dataclass(eq=False)
class _Publication:
    kind: str
    operation_id: str
    epoch: _FrozenEpoch
    revision: int
    message: dict
    payload: bytes
    digest: str
    deadline_ns: int
    tx: object = None
    send_attempted: bool = False
    state: str = 'RESERVED'
    readback: object = None
    readback_ns: int | None = None
    differences: object = None
    getter_admitted: bool = False
    query_attempted: bool = False
    query_tx: object = None
    resolved: bool = False


@dataclass(eq=False)
class _Commit:
    binding: _Binding
    command_raw: bytes
    issue_ns: int
    deadline_ns: int
    prepared: object = None
    fence_used: bool = False
    receipt: object = None
    frame: object = None
    view: object = None
    publication: object = None
    committed: bool = False
    uncertainty: str | None = None


def _entry(method):
    @wraps(method)
    def call(self, /, *args, **kwargs):
        self._check_thread()
        if self._busy:
            self._veto('reentrant_world_owner')
            raise WorldRejected('reentrant world owner')
        self._busy = True
        try:
            return method(self, *args, **kwargs)
        except BaseException:
            self._veto('world_call_failed')
            raise
        finally:
            self._busy = False
    return call


class _RootWorldOwner:
    def __init__(self, key, clock):
        if key not in (_FACTORY, _TEST_FACTORY):
            raise WorldRejected('fixed original owner factory required')
        self._test = key is _TEST_FACTORY
        self._clock = clock
        self._thread = threading.get_ident()
        self._foreign = threading.Event()
        self._busy = False
        self._em_scope_active = None
        self._native = None
        self._high = 0
        self._number = 0
        self._serial = 0
        self._epochs = {}
        self._bindings = {}
        self._actor_links = {}
        self._actor_link = None
        self._epoch = None
        self._binding = None
        self._hello = None
        self._editable = None
        self._freeze_request = None
        self._assembly = None
        self._status = None
        self._native_observation = None
        self._publication = None
        self._publications = []
        self._commits = []
        self._diagnostic_used = False
        self._initialized = False
        self._renderer_revision = 0
        self._vetoed = False
        self._veto_generation = 0
        self._reason = None
        self._stop_notice_attempted = False
        self._stop_tx = None
        self._stop_transactions = []
        self._retirement = None
        self._retired_epochs = set()
        self._state = 'ACQUIRING'
        self._errors = []
        self._retired_status_frames = 0
        self._close_result = None
        self._inflight_frames = ()
        self._time()

    def _check_thread(self):
        if threading.get_ident() != self._thread:
            self._foreign.set()
            raise WorldRejected('original owner thread required')

    def _time(self):
        now = _integer(self._clock())
        if now < self._high:
            self._veto('clock_regressed')
            raise WorldRejected('original clock regressed')
        self._high = now
        return now

    def _veto(self, reason, *, world=False):
        # Pure synchronous veto, usable during the numerical final callback.
        # No I/O, logging, serialization or transport effect is performed here.
        self._veto_generation += 1
        self._vetoed = True
        if self._reason is None:
            self._reason = reason
        link = self._actor_link
        if link is not None and self._actor_links.get(id(link)) is link:
            actor = link.composition
            if actor is not None and actor._world_action_link is link and not actor._retired:
                actor._veto += 1
                actor._retired = True
                if actor._state not in ('CLOSED', 'QUARANTINED'):
                    actor._state = 'RETIRED'
                if actor._progress is not None:
                    actor._progress.generation += 1
                    actor._progress.revoked = True
                actor._world_pending_stop = True
        if self._binding is not None:
            if world:
                self._binding.executor.invalidate_world(reason)
            else:
                self._binding.executor.revoke(reason)

    def _operation(self, name):
        self._serial += 1
        return f'{self._native.run_id}:{name}:{self._serial}'

    def _phase_deadline(self, duration_ns):
        """Tighten a phase to this original native owner's absolute cap."""
        now = self._time()
        cap = _integer(self._native._containment_deadline)
        deadline = min(now+_integer(duration_ns, 1), cap)
        if deadline <= now:
            raise WorldRejected('original native containment already expired')
        return deadline

    def _message(self, name, body, *, epoch=None, operation=None):
        return dict(type=name, run_id=self._native.run_id,
                    world_epoch=str(self._number if epoch is None else epoch),
                    operation_id=operation or self._operation(name), body=body)

    def _known_epoch(self, epoch):
        if (type(epoch) is not _FrozenEpoch or epoch.owner is not self or
                self._epochs.get(id(epoch)) is not epoch or self._epoch is not epoch or
                epoch.number in self._retired_epochs):
            raise WorldRejected('original current frozen epoch required')
        return epoch

    def _known_binding(self, binding):
        if (type(binding) is not _Binding or binding.owner is not self or
                self._bindings.get(id(binding)) is not binding or self._binding is not binding):
            raise WorldRejected('original registered binding required')
        self._known_epoch(binding.epoch)
        return binding

    def _audit_identity(self, body):
        epoch = self._known_epoch(self._epoch)
        if body['freeze_identity'] != epoch.identity:
            raise WorldRejected('original freeze identity changed')
        if body.get('geometry_audit_digest', epoch.identity['geometry_state_sha256']) != epoch.identity['geometry_state_sha256']:
            raise WorldRejected('static geometry audit changed')
        return epoch

    def _accept_frame(self, frame):
        if not any(frame is original for original in self._inflight_frames):
            raise WorldRejected('frame did not come from original poll')
        document = frame.as_dict()
        if document['run_id'] != self._native.run_id:
            raise WorldRejected('world run changed')
        name, body = document['type'], document['body']
        if name == 'HELLO':
            if self._hello is not None or self._native.hello is None:
                raise WorldRejected('unexpected original HELLO')
            self._hello = frame  # Secret challenge remains trusted memory only.
            self._editable = dict(document_generation=body['document_generation'],
                geometry_generation=body['geometry_generation'], raw_layout_sha256=body['raw_layout_sha256'])
            self._state = 'EDITABLE'
            return
        if name == 'EDITABLE':
            if self._retirement is None or body['retired_freeze_id'] != self._retirement['freeze_id']:
                raise WorldRejected('unsolicited editable generation')
            self._editable = body
            self._state = 'EDITABLE'
            return
        incoming_epoch = int(document['world_epoch'])
        if incoming_epoch in self._retired_epochs and name in ('WORLD_STATUS','STOPPED','VIEW_READBACK'):
            # Authenticated old status may already be queued before UNLOCK.
            # It cannot update the new epoch, resolve a new operation or move.
            self._retired_status_frames += 1
            return
        if incoming_epoch != self._number:
            raise WorldRejected('stale world message')
        if name.startswith('SNAPSHOT_'):
            request = self._freeze_request
            if request is None or document['operation_id'] != request['operation_id']:
                raise WorldRejected('snapshot not bound to outstanding freeze')
            if self._time() >= request['deadline_ns']:
                raise WorldRejected('original freeze deadline expired before snapshot handling')
            if name == 'SNAPSHOT_BEGIN':
                if self._assembly is not None:
                    raise WorldRejected('duplicate snapshot begin')
                ident = body['freeze_identity']
                hello = self._hello.as_dict()['body']
                if (ident['source_bundle_sha256'] != hello['source_bundle_sha256'] or
                        ident['document_generation'] != request['body']['expected_document_generation'] or
                        body['raw_layout_sha256'] != request['body']['expected_raw_sha256'] or
                        any(ident[key] != hello[key] for key in ('main_instance_id',
                            'document_instance_id', 'workspace_instance_id', 'drill_root_instance_id'))):
                    raise WorldRejected('snapshot source/generation/original references changed')
                self._assembly = wire._SnapshotAssembly(frame)
            elif name == 'SNAPSHOT_CHUNK':
                if self._assembly is None:
                    raise WorldRejected('snapshot chunk before begin')
                self._assembly.add(frame)
            else:
                if self._assembly is None:
                    raise WorldRejected('snapshot end before begin')
                raw = self._assembly.finish(frame)
                snapshot = values.snapshot_from_wire(raw)
                identity = _identity(snapshot)
                if (identity != body['freeze_identity'] or
                        snapshot.canonical_companion.raw_sha256 != request['body']['expected_raw_sha256']):
                    raise WorldRejected('complete snapshot identity differs')
                if self._time() >= request['deadline_ns']:
                    raise WorldRejected('original freeze deadline expired during complete conversion')
                epoch = _FrozenEpoch(self, self._number, request['operation_id'], identity,
                                     raw, snapshot, self._time())
                if self._epoch is not None:
                    if self._epoch.number not in self._retired_epochs:
                        raise WorldRejected('previous original epoch not retired')
                    self._binding = None
                    self._publication = None
                    self._initialized = False
                    self._vetoed = False  # New independently frozen trial only.
                    self._reason = None
                    self._veto_generation += 1
                    self._stop_notice_attempted = False
                    self._stop_tx = None
                self._epochs[id(epoch)] = epoch
                self._epoch = epoch
                self._renderer_revision = 0
                self._freeze_request = None
                self._assembly = None
                self._status = dict(identity=identity, state='FROZEN', revision=0,
                                    received_ns=self._high)
                self._state = 'FROZEN'
            return
        if name in ('EDIT_REQUEST', 'STOP_NOTICE', 'REFUSAL'):
            self._veto(name.lower(), world=name == 'EDIT_REQUEST')
            self._state = 'STOPPED'
            return
        if name == 'WORLD_STATUS':
            self._audit_identity(body)
            revision = int(body['pose_revision'])
            pending = self._publication
            allowed = {self._renderer_revision}
            if pending is not None:
                allowed.add(pending.revision)
            if revision not in allowed:
                raise WorldRejected('unauthorized actual revision')
            self._renderer_revision = revision
            self._status = dict(identity=body['freeze_identity'], state=body['state'],
                                revision=revision, received_ns=self._time())
            if body['state'] == 'INVALIDATED':
                self._veto('engine_world_invalidated', world=True)
            return
        if name == 'VIEW_READBACK':
            self._audit_identity(body)
            pending = self._publication
            if (pending is None or body['publication_operation_id'] != pending.operation_id or
                    body['payload_digest'] != pending.digest or
                    body['drill_root_instance_id'] != pending.epoch.identity['drill_root_instance_id']):
                raise WorldRejected('readback not for original publication')
            if body['state'] == 'APPLIED' and int(body['pose_revision']) != pending.revision:
                raise WorldRejected('APPLIED revision differs')
            if body['state'] == 'NOT_SEEN' and int(body['pose_revision']) != self._renderer_revision:
                raise WorldRejected('NOT_SEEN actual renderer revision differs')
            width = self._hello.as_dict()['body']['scalar_width']
            expected = pending.message['body']['desired_transform']
            pending.differences = dict(local=_getter_differences(expected, body['local_transform'], width),
                                      global_transform=_getter_differences(expected, body['global_transform'], width))
            pending.readback = frame
            pending.readback_ns = self._time()
            pending.state = body['state']
            pending.resolved = body['state'] in ('APPLIED', 'NOT_SEEN')
            if body['state'] == 'APPLIED':
                self._renderer_revision = pending.revision
            if pending.readback_ns >= pending.deadline_ns:
                self._veto('late_view_readback')
            if pending.kind == 'INITIAL_VIEW' and body['state'] == 'APPLIED':
                if self._time() < pending.deadline_ns and not self._vetoed:
                    self._initialized = True
                    self._state = 'BOUND_STOPPED'
            return
        if name == 'STOPPED':
            self._audit_identity(body)
            self._veto('engine_stopped')
            self._state = 'STOPPED'
            return
        raise WorldRejected('unexpected original-world message')

    def _poll_once(self):
        now = self._time()
        if self._foreign.is_set():
            self._veto('foreign_thread_call', world=True)
        observation = self._native.native_liveness()
        self._native_observation = observation
        if not observation.alive:
            self._veto('original_engine_not_alive', world=True)
        frames = self._native.poll()
        self._inflight_frames = frames
        try:
            for frame in frames:
                self._accept_frame(frame)
        finally:
            self._inflight_frames = ()
        now = self._time()  # Account for actual time consumed by receive/handling.
        pending = self._publication
        if pending is not None and not pending.resolved and now >= pending.deadline_ns:
            pending.state = 'COMMIT_PUBLICATION_UNKNOWN' if pending.kind == 'PUBLISH_VIEW' else 'INITIAL_PUBLICATION_UNKNOWN'
            self._veto('publication_deadline')
        if self._freeze_request is not None and now >= self._freeze_request['deadline_ns']:
            self._veto('freeze_deadline', world=True)
            raise WorldRejected('original freeze deadline expired')
        if (self._commits and self._commits[-1].binding.epoch is self._epoch and
                now >= self._commits[-1].deadline_ns):
            self._veto('original_command_expired')
        self._try_stop_notice()
        return self._state

    def _try_stop_notice(self):
        if (not self._vetoed or self._stop_notice_attempted or self._epoch is None or
                self._epoch.number in self._retired_epochs or self._epoch.number != self._number or
                self._state in ('UNLOCKING','EDITABLE','FREEZING') or
                not self._native.healthy_frame_aligned()):
            return
        self._stop_notice_attempted = True
        revision = self._renderer_revision
        message = self._message('STOP', dict(freeze_id=self._epoch.identity['freeze_id'],
            reason_code=self._reason or 'stopped', expected_pose_revision=str(revision)))
        self._stop_tx = self._native.send(message, deadline_ns=self._phase_deadline(VIEW_NS))
        self._stop_transactions.append(self._stop_tx)

    @_entry
    def poll(self):
        return self._poll_once()

    @_entry
    def request_freeze(self, *, snapshot_limits_sha256, model_policy_sha256):
        if (self._state != 'EDITABLE' or self._editable is None or self._freeze_request is not None or
                (self._epoch is not None and self._epoch.number not in self._retired_epochs)):
            raise WorldRejected('original editable document required')
        self._number += 1  # Consumed even if sending the request fails.
        operation = self._operation('freeze')
        body = dict(expected_document_generation=self._editable['document_generation'],
            expected_raw_sha256=self._editable['raw_layout_sha256'],
            snapshot_limits_sha256=snapshot_limits_sha256, model_policy_sha256=model_policy_sha256)
        message = self._message('FREEZE_REQUEST', body, operation=operation)
        self._freeze_request = dict(operation_id=operation, body=body,
                                    deadline_ns=self._phase_deadline(FREEZE_NS), tx=None)
        self._state = 'FREEZING'
        self._freeze_request['tx'] = self._native.send(message, deadline_ns=self._freeze_request['deadline_ns'])
        return operation

    @_entry
    def frozen_epoch(self):
        return self._known_epoch(self._epoch)

    @_entry
    def construct_and_bind(self, epoch, policy, *, initial_pose):
        self._known_epoch(epoch)
        if self._state != 'FROZEN' or type(policy) is not values.ValuePolicy or policy.run_id != self._native.run_id:
            raise WorldRejected('reviewed actual-run value policy required')
        if type(initial_pose) is not RigidState or initial_pose.speed_m_s != 0:
            raise WorldRejected('explicit zero-speed Root initial pose required')
        entered = self._time()
        result = values._construct_values(epoch.snapshot, policy,
            initial_pose, initial_monotonic_ns=entered)
        finished = self._time()
        if finished-entered > CONSTRUCT_NS or finished-result.initial_state.monotonic_ns > VIEW_NS:
            raise WorldRejected('constructor or original initial-state age exceeded')
        executor = motion.OwnedMotionExecutor(initial_state=result.initial_state, scene=result.scene,
            model=result.model, budget=result.budget)
        binding = _Binding(self, epoch, result, executor, entered, finished)
        self._bindings[id(binding)] = binding
        self._binding = binding
        return binding

    def _publish(self, binding, kind, view, *, receipt_digest=None):
        epoch = self._known_epoch(binding.epoch)
        if self._publication is not None and not self._publication.resolved:
            raise WorldRejected('original publication unresolved')
        desired, transform = _desired(view)
        body = dict(freeze_id=epoch.identity['freeze_id'], geometry_identity=binding.world_values.geometry_identity,
                    pose_revision=str(view.pose_revision), desired_pose=desired, desired_transform=transform)
        if kind == 'PUBLISH_VIEW':
            body.update(expected_previous_revision=str(view.pose_revision-1), numerical_receipt_digest=receipt_digest)
        operation = self._operation(kind)
        message = self._message(kind, body, operation=operation)
        payload = wire.encode_payload(message)
        deadline = self._phase_deadline(VIEW_NS)
        if kind == 'PUBLISH_VIEW':
            if not self._commits or self._commits[-1].binding is not binding:
                raise WorldRejected('original numerical commit record missing')
            deadline = min(deadline,self._commits[-1].deadline_ns)
        pending = _Publication(kind, operation, epoch, view.pose_revision, message, payload,
                               _hash(payload), deadline)
        self._publications.append(pending)
        self._publication = pending  # Retained before any transport effect.
        pending.send_attempted = True
        try:
            pending.tx = self._native.send(message, deadline_ns=pending.deadline_ns)
            if pending.tx.payload != payload or pending.tx.payload_digest != pending.digest:
                raise WorldRejected('original transmission request changed')
            pending.state = 'SENDING'
        except BaseException:
            pending.state = 'COMMIT_PUBLICATION_UNKNOWN' if kind == 'PUBLISH_VIEW' else 'INITIAL_PUBLICATION_UNKNOWN'
            self._veto('publication_send_failed')
            raise
        return pending

    @_entry
    def initialize_view(self, binding):
        self._known_binding(binding)
        if self._vetoed or self._initialized or binding.executor.renderer_view().pose_revision != 0:
            raise WorldRejected('fresh stopped binding required')
        if self._time()-binding.world_values.initial_state.monotonic_ns > VIEW_NS:
            raise WorldRejected('original initializer stale before publication')
        return self._publish(binding, 'INITIAL_VIEW', binding.executor.renderer_view())

    def require_source_pose_current(self):
        """Gate every original source acquisition after any numerical action.

        Initial stopped diagnostics remain available. APPLIED alone is not
        getter admission; no tolerance or admission is installed here.
        """
        self._check_thread()
        link = self._actor_link
        slot = None if link is None else link.slot
        if slot is not None and not slot.committed:
            raise WorldRejected('original numeric action is pending or uncertain')
        if any(item.uncertainty is not None for item in self._commits):
            raise WorldRejected('original numeric effect remains uncertain')
        if not any(item.committed for item in self._commits):
            return
        publication = self._publication
        binding = self._binding
        if (binding is None or publication is None or publication.kind != 'PUBLISH_VIEW'
                or not publication.resolved or publication.state != 'APPLIED'
                or publication.getter_admitted is not True
                or publication.revision != self._renderer_revision
                or binding.executor._root.pose_revision != self._renderer_revision):
            raise WorldRejected('actual published getter pose has not been admitted')

    def actor_link(self, service):
        from .original_world_actor_link import _issue
        return _issue(self, service)

    @_entry
    def publish_actor_commit_once(self, capability):
        from .original_world_actor_link import _publish_once
        return _publish_once(self, capability)

    def diagnostic_step_once(self, binding):
        """Disabled before any owner/BOOT/command/executor effect."""
        raise WorldRejected('synthetic diagnostic actions are disabled in current world integration')

    @_entry
    def query_publication_once(self):
        pending = self._publication
        if pending is None or pending.query_attempted or pending.resolved:
            raise WorldRejected('no unresolved once-query publication')
        pending.query_attempted = True
        self._veto('readonly_publication_query')
        if (pending.tx is None or not self._native.complete_tx(pending.tx) or
                not self._native.healthy_frame_aligned()):
            raise WorldRejected('partial/lost original stream cannot query')
        message = self._message('QUERY_VIEW', dict(freeze_id=pending.epoch.identity['freeze_id'],
            publication_operation_id=pending.operation_id,payload_digest=pending.digest,
            expected_pose_revision=str(pending.revision)))
        pending.query_tx = self._native.send(message, deadline_ns=self._phase_deadline(VIEW_NS))
        return pending.query_tx

    @_entry
    def retire_for_edit(self):
        epoch = self._known_epoch(self._epoch)
        self._veto('edit_retirement', world=True)
        pending = self._publication
        if pending is not None and not pending.resolved:
            raise WorldRejected('unresolved old effect holds epoch; query once or close original engine')
        if self._retirement is not None and self._retirement['epoch'] == epoch.number:
            raise WorldRejected('retirement already attempted')
        if not self._native.healthy_frame_aligned():
            raise WorldRejected('original stream not frame-aligned')
        revision = self._renderer_revision
        record = dict(freeze_id=epoch.identity['freeze_id'],epoch=epoch.number,revision=revision,
                      generation=self._veto_generation)
        self._retirement = record  # Retain before effect, never retry UNLOCK.
        self._retired_epochs.add(epoch.number)
        message = self._message('UNLOCK_FOR_EDIT',dict(retired_freeze_id=record['freeze_id'],
            retired_epoch=str(epoch.number),expected_pose_revision=str(revision),retirement_record_digest=_hash(_raw(record))))
        record['tx'] = self._native.send(message, deadline_ns=self._phase_deadline(VIEW_NS))
        self._initialized = False
        self._state = 'UNLOCKING'
        return record

    def stop(self, reason='root_stop'):
        self._check_thread()
        self._veto(reason)

    @_entry
    def controller_view(self):
        return motion.ControllerView(True,False) if self._binding is None else self._binding.executor.controller_view()

    @_entry
    def close(self, reason='root_close'):
        self._veto(reason, world=True)
        self._close_result = self._native.close(reason)
        self._state = self._close_result.get('state','QUARANTINED')
        return self._close_result

    @_entry
    def evidence(self):
        # Private trusted evidence only; never serialize HELLO/challenge/key.
        return dict(mode='DIAGNOSTIC_COMPONENT',native_original=not self._test,
            state=self._state,reason=self._reason,epoch=self._number,
            retired_status_frames=self._retired_status_frames,
            initialized=self._initialized,vetoed=self._vetoed,diagnostic_slot_consumed=self._diagnostic_used,
            actual_renderer_revision=self._renderer_revision,
            commits=[dict(committed=x.committed,uncertainty=x.uncertainty,
                pose_revision=None if x.view is None else x.view.pose_revision,
                fence_used=x.fence_used,issue_ns=x.issue_ns,deadline_ns=x.deadline_ns) for x in self._commits],
            publications=[dict(kind=x.kind,operation_id=x.operation_id,payload_digest=x.digest,
                revision=x.revision,state=x.state,resolved=x.resolved,query_attempted=x.query_attempted,
                readback_ns=x.readback_ns,deadline_ns=x.deadline_ns,
                actual_getter_differences=x.differences,getter_admitted=x.getter_admitted) for x in self._publications],
            native=self._native.diagnostics(),close_result=self._close_result,
            genuine_PC_DIRECT=False,board=False,AI_provider=False,GPU_frame=False)


def _acquire_root_world(spec, original_host_clock_binding):
    clocks._require_binding(original_host_clock_binding)
    if type(original_host_clock_binding) is not clocks.QpcHostClock:
        raise WorldRejected('original QPC binding required')
    owner = _RootWorldOwner(_FACTORY, original_host_clock_binding)
    _RETAINED.append(owner)  # Before any fallible native acquisition.
    try:
        owner._native = native._acquire_owned_godot(spec, original_host_clock_binding)
        if not native.is_original_owner(owner._native) or owner._native.clock_binding is not original_host_clock_binding:
            raise WorldRejected('native factory did not retain original owner')
        owner._state = 'WAIT_HELLO'
        return owner
    except native.AcquisitionFailure as error:
        owner._native = error.owner
        owner._state = 'QUARANTINED'
        owner._errors.append(error.cause)
        raise


def _owner_for_test(boundary, clock):
    """Software-only seam. Never adopts an actual native owner."""
    if native.is_original_owner(boundary) or getattr(boundary,'software_fixture_only',False) is not True:
        raise WorldRejected('test seam refuses actual native owners')
    owner = _RootWorldOwner(_TEST_FACTORY,clock)
    owner._native = boundary
    owner._state = 'WAIT_HELLO'
    _RETAINED.append(owner)
    return owner


# One synchronous EM interval; no owner/native acquisition or lifecycle.
_EM_SCOPE_PRODUCTION = object()
_EM_SCOPE_SOFTWARE = object()


class _EmScopeFactoryCore:
    def __init__(self, key, owner, binding, field, source):
        from types import MethodType
        from ..sensors.owned_world_field import OwnedWorldField
        from ...tools.diagnostic.causal_pl_exchange import CausalSourcePump
        if hasattr(self, '_key') or key not in (_EM_SCOPE_PRODUCTION, _EM_SCOPE_SOFTWARE):
            raise WorldRejected('private original acquisition factory required')
        if key is _EM_SCOPE_PRODUCTION:
            if (type(self) is not _OriginalEmScopeFactory
                    or type(owner) is not _RootWorldOwner or owner._test is not False
                    or not any(owner is original for original in _RETAINED)
                    or not native.is_original_owner(owner._native)
                    or type(owner._clock) is not clocks.QpcHostClock):
                raise WorldRejected('retained production Root/native/QPC required')
        elif (isinstance(owner, _RootWorldOwner)
                or getattr(owner, 'software_fixture_only', None) is not True
                or getattr(owner._clock, 'software_fixture_only', None) is not True
                or native.is_original_owner(owner._native)):
            raise WorldRejected('software factory cannot adopt real Root/native')
        if (type(field) is not OwnedWorldField or type(source) is not CausalSourcePump
                or type(source._pose_reader) is not MethodType
                or type(source._sampler) is not MethodType
                or source._pose_reader.__func__ is not OwnedWorldField.pose_reader
                or source._sampler.__func__ is not OwnedWorldField.sample_sigma
                or source._pose_reader.__self__ is not field
                or source._sampler.__self__ is not field
                or field._em_scope_factory is not None):
            raise WorldRejected('fresh exact field/source association required')
        self._key, self._owner, self._binding = key, owner, binding
        self._field, self._source = field, source
        self._clock, self._native = owner._clock, owner._native
        self._profile = source._profile
        self._scene, self._pieces = field._scene, field._pieces
        self._background, self._epsilon = field._background, field._epsilon
        self._deadline = self._native._containment_deadline
        self._freeze = _raw(binding.epoch.identity)
        self._thread = threading.get_ident()
        self._fault = threading.Event()
        self._active = None
        self._last_tick = -1
        self._high = 0
        self._check(None)
        if owner._em_scope_active is not None:
            owner._em_scope_active._factory._fail()
            raise WorldRejected('one original owner acquisition at a time')
        field._em_scope_factory = self

    def _fail(self):
        self._fault.set()
        # Foreign calls only contaminate. Original-thread exit performs retirement.
        if threading.get_ident() == self._thread:
            self._field._retired = True
            self._source.state = 'FAILED'

    def _check(self, tick):
        from types import MethodType
        from ..sensors.owned_world_field import OwnedWorldField
        from ...tools.diagnostic.causal_pl_exchange import CausalSourcePump
        if self._fault.is_set():
            raise RuntimeError('acquisition association permanently failed')
        if threading.get_ident() != self._thread:
            raise WorldRejected('original acquisition thread required')
        owner, source, field = self._owner, self._source, self._field
        if self._key is _EM_SCOPE_PRODUCTION:
            if (type(self) is not _OriginalEmScopeFactory
                    or type(owner) is not _RootWorldOwner or owner._test is not False
                    or not any(owner is original for original in _RETAINED)
                    or not native.is_original_owner(self._native)
                    or type(self._clock) is not clocks.QpcHostClock):
                raise WorldRejected('original production factory custody lost')
            clocks._require_binding(self._clock)
        else:
            if (isinstance(owner, _RootWorldOwner)
                    or getattr(owner, 'software_fixture_only', None) is not True
                    or getattr(self._clock, 'software_fixture_only', None) is not True
                    or native.is_original_owner(owner._native)):
                raise WorldRejected('software fixture custody lost')
            self._clock._check()
        if (owner._clock is not self._clock or owner._native is not self._native
                or owner._thread != self._thread or owner._busy is not False
                or owner._foreign.is_set() or owner._initialized is not True
                or owner._vetoed is not False or self._native._retired is not False
                or self._native.state != 'AUTHENTICATED'
                or self._native.clock_binding is not self._clock
                or self._native._containment_deadline != self._deadline
                or owner._native_observation is None
                or owner._native_observation.alive is not True
                or (owner._publication is not None and not owner._publication.resolved)):
            raise WorldRejected('healthy original world/native/containment required')
        _RootWorldOwner._known_binding(owner, self._binding)
        if (_raw(self._binding.epoch.identity) != self._freeze
                or owner._status is None
                or owner._status['identity'] != self._binding.epoch.identity
                or owner._status['state'] not in ('FROZEN', 'BOUND_STOPPED')):
            raise WorldRejected('original frozen world status required')
        if (type(source) is not CausalSourcePump or source._profile is not self._profile
                or source._thread != self._thread
                or source.state not in (('NEW', 'RUNNING') if tick is None else ('RUNNING',))
                or type(source._pose_reader) is not MethodType
                or type(source._sampler) is not MethodType
                or source._pose_reader.__func__ is not OwnedWorldField.pose_reader
                or source._sampler.__func__ is not OwnedWorldField.sample_sigma
                or source._pose_reader.__self__ is not field
                or source._sampler.__self__ is not field
                or field._executor is not self._binding.executor
                or field._scene is not self._scene
                or self._binding.world_values.scene is not self._scene
                or field._pieces is not self._pieces
                or field._background != self._background or field._epsilon != self._epsilon
                or (field._em_scope_factory is not None and field._em_scope_factory is not self)):
            raise WorldRejected('original complete field/profile/source required')
        root = field._check()
        view = self._binding.executor.renderer_view()
        if (type(root) is not motion._Root or view.pose is not root.pose
                or view.pose_revision != root.pose_revision
                or self._binding.executor._busy
                or solids._digest(self._scene) != field._scene_digest
                or self._scene.digest != field._scene_digest):
            raise WorldRejected('current root/pose and actual scene digest required')
        now = _integer(self._clock())
        if now < self._high or now >= self._deadline:
            raise WorldRejected('original acquisition clock/containment expired')
        self._high = now
        if source.state == 'RUNNING':
            if (source._clock is not self._clock or now < source._origin
                    or now < source._high or now-source._origin > 10_000_000_000):
                raise WorldRejected('original source clock/session required')
        if tick is not None:
            if (source._last_tick != tick or type(source._count) is not int
                    or not 1 <= source._count <= 1001):
                raise WorldRejected('already consumed current source slot required')
        return (root, root.pose, root.revision, root.revoke_generation,
                root.pose_revision, owner._veto_generation,
                _raw(self._binding.epoch.identity), source._origin,
                source._last_tick, source._count, source._high)

    def _boundary(self, tick):
        self._check(tick)
        self._owner.poll()  # Explicit, never inside the clock or owner._busy.
        return self._check(tick)

    def begin(self, tick_ms):
        try:
            if self._fault.is_set():
                raise RuntimeError('acquisition association permanently failed')
            if threading.get_ident() != self._thread:
                raise WorldRejected('original acquisition thread required')
            if self._active is not None or self._owner._em_scope_active is not None:
                raise RuntimeError('nested original acquisition refused')
            if (type(tick_ms) is not int or tick_ms < 0 or tick_ms % 50
                    or tick_ms <= self._last_tick):
                raise WorldRejected('fresh already consumed EM tick required')
            self._last_tick = tick_ms  # Reservation is never rolled back.
            self._check(tick_ms)
            scope = _EmAcquisitionScope(self, tick_ms)
            self._active = self._owner._em_scope_active = scope
            return scope
        except BaseException:
            self._fail()
            raise


class _OriginalEmScopeFactory(_EmScopeFactoryCore):
    def __init__(self, key, owner, binding, field, source):
        if key is not _EM_SCOPE_PRODUCTION or type(self) is not _OriginalEmScopeFactory:
            raise WorldRejected('exact original acquisition factory required')
        super().__init__(key, owner, binding, field, source)


class _EmAcquisitionScope:
    def __init__(self, factory, tick):
        self._factory, self._tick = factory, tick
        self._entered = self._ended = self._active = self._sampling = False
        self._snapshot = None
        self._secondary = []

    @property
    def sampler(self):
        return self._sample_sigma

    @property
    def secondary_errors(self):
        return tuple(self._secondary)

    def __enter__(self):
        factory = self._factory
        if threading.get_ident() != factory._thread:
            factory._fail()
            raise RuntimeError('foreign scope entry refused')
        try:
            if (self._entered or self._ended or factory._active is not self
                    or factory._owner._em_scope_active is not self):
                raise RuntimeError('one-shot original acquisition scope required')
            self._entered = True
            self._snapshot = factory._boundary(self._tick)
            self._active = True
            return self
        except BaseException:
            factory._fail()
            self._ended = True
            self._snapshot = None
            if factory._active is self:
                factory._active = None
            if factory._owner._em_scope_active is self:
                factory._owner._em_scope_active = None
            raise

    def _sample_sigma(self, x, y, z):
        factory = self._factory
        sampling = False
        try:
            if (not self._active or self._ended or self._sampling
                    or threading.get_ident() != factory._thread
                    or factory._fault.is_set()):
                raise RuntimeError('inactive, foreign or reentered scoped sampler')
            if (factory._field._retired
                    or factory._field._pieces is not factory._pieces
                    or factory._field._background != factory._background
                    or factory._field._epsilon != factory._epsilon):
                raise WorldRejected('original scoped field/policy required')
            self._sampling = True
            sampling = True
            return factory._field._sample_sigma_pure(x, y, z)
        except BaseException:
            factory._fail()
            raise
        finally:
            if sampling:
                self._sampling = False

    def __exit__(self, exc_type, exc, traceback):
        factory = self._factory
        if threading.get_ident() != factory._thread:
            factory._fail()
            raise RuntimeError('foreign scope exit refused')
        self._active = False  # Never usable during post-poll or afterward.
        secondary = None
        try:
            if not self._entered or self._ended or self._snapshot is None:
                raise RuntimeError('one-shot active scope exit required')
            current = factory._boundary(self._tick)
            previous = self._snapshot
            if (current[0] is not previous[0] or current[1] is not previous[1]
                    or current[2:] != previous[2:]):
                raise WorldRejected('original acquisition root/generations changed')
        except BaseException as error:
            secondary = error
            factory._fail()
        finally:
            self._ended = True
            self._snapshot = None  # No root/pose cache survives an acquisition.
            if factory._active is self:
                factory._active = None
            if factory._owner._em_scope_active is self:
                factory._owner._em_scope_active = None
        if exc is not None:
            factory._fail()
            if secondary is not None and len(self._secondary) < 2:
                self._secondary.append(secondary)
            return False  # Original body exception remains primary.
        if secondary is not None:
            raise secondary
        return False


def _make_original_em_scope_factory(owner, binding, field, source):
    return _OriginalEmScopeFactory(_EM_SCOPE_PRODUCTION, owner, binding, field, source)


def _make_software_em_scope_factory_for_test(owner, binding, field, source):
    """Software-only controls; a distinct exact type, never a native capability."""
    return _EmScopeFactoryCore(_EM_SCOPE_SOFTWARE, owner, binding, field, source)


__all__ = []
