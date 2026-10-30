"""Private identity association; not a source, channel, or motion grant."""
import threading
from . import _world_loop as world
from . import root_world_service as service_module
from . import _owned_godot as native
from .pc_direct_runtime import StepFence, CommitReceipt

_KEY = object()

class _OriginalWorldActorLink:
    def __init__(self, key, owner, service):
        if key is not _KEY:
            raise world.WorldRejected('fixed issue path required')
        self.owner, self.service = owner, service
        self.binding, self.source, self.field = service._binding, service._source, service._field
        self.clock, self.native = service._clock, service._native
        self.executor = self.binding.executor
        if type(self.executor) is not world.motion.OwnedMotionExecutor:
            raise world.WorldRejected('exact original executor required')
        self.pose_reader, self.sampler, self.profile = self.source._pose_reader, self.source._sampler, self.source._profile
        self.freeze_identity = dict(self.binding.epoch.identity)
        self.epoch = self.binding.epoch
        self.thread = threading.get_ident()
        self.claimed = False
        self.composition = None
        self.slot = None
        self.getter_admitted = False
        self.generation = owner._veto_generation
        self.deadline = service._deadline_ns

    def _registered(self):
        o = self.owner
        if (type(self) is not _OriginalWorldActorLink or type(o) is not world._RootWorldOwner
                or not any(o is x for x in world._RETAINED)
                or o._actor_links.get(id(self)) is not self
                or o._actor_link is not self or self.thread != threading.get_ident()
                or o._thread != self.thread or o._foreign.is_set()
                or o._clock is not self.clock or o._native is not self.native
                or o._binding is not self.binding or self.binding.executor is not self.executor
                or self.binding.epoch is not self.epoch or o._epoch is not self.epoch
                or o._bindings.get(id(self.binding)) is not self.binding
                or o._epochs.get(id(self.epoch)) is not self.epoch
                or self.epoch.number in o._retired_epochs
                or o._vetoed or o._veto_generation != self.generation
                or self.native._retired or self.native.state != 'AUTHENTICATED'
                or self.native.clock_binding is not self.clock
                or self.native._containment_deadline != self.deadline
                or o._em_scope_active is not None or not o._initialized
                or o._native_observation is None or o._native_observation.alive is not True
                or o._status is None or o._status['identity'] != self.freeze_identity
                or o._status['state'] not in ('FROZEN', 'BOUND_STOPPED')
                or self.service._failed or self.service._owner is not o
                or self.service._source is not self.source or self.service._field is not self.field
                or self.field._executor is not self.executor
                or self.field._scene is not self.binding.world_values.scene
                or self.binding.epoch.identity != self.freeze_identity
                or self.source._pose_reader is not self.pose_reader
                or self.source._sampler is not self.sampler or self.source._profile is not self.profile
                or self.source._polling
                or self.source._thread != self.thread
                or self.source.state not in ('NEW', 'RUNNING')
                or (self.source.state == 'RUNNING' and self.source._clock is not self.clock)
                or o._publication is None or not o._publication.resolved
                or o._publication.state != 'APPLIED'):
            raise world.WorldRejected('original world action association changed')
        return o

    def _claim(self, config, clock):
        self._registered()
        b = self.binding
        if (self.claimed or clock is not self.clock
                or config.initial_state is not b.world_values.initial_state
                or config.scene is not b.world_values.scene
                or config.model is not b.world_values.model
                or config.budget is not b.world_values.budget
                or config.actor_policy.run_id != self.native.run_id
                or config.max_slices != self.executor._max_slices):
            raise world.WorldRejected('original unconsumed configuration required')
        self.claimed = True

    def _ready(self, composition):
        o = self._registered()
        if (not self.claimed or self.composition is not composition
                or composition._executor is not self.executor
                or self.source.state != 'RUNNING' or self.source._clock is not self.clock
                or o._busy or o._native_observation is None
                or o._native_observation.alive is not True
                or o._status is None or o._status['identity'] != self.epoch.identity
                or o._status['state'] not in ('FROZEN', 'BOUND_STOPPED')
                or (self.slot is not None and (self.slot.committed or self.slot.uncertainty is not None))):
            raise world.WorldRejected('original running source/action slot required')


def _issue(owner, service):
    if (type(owner) is not world._RootWorldOwner
            or not any(owner is retained for retained in world._RETAINED)
            or owner._test is not False
            or type(service) is not service_module.RootWorldService
            or service._owner is not owner or not native.is_original_owner(owner._native)):
        raise world.WorldRejected('retained original world/service required')
    service._validate(retired_source=False)
    if owner._em_scope_active is not None or owner._actor_link is not None:
        raise world.WorldRejected('world action association already used or EM active')
    link = _OriginalWorldActorLink(_KEY, owner, service)
    owner._actor_links[id(link)] = link
    owner._actor_link = link
    link._registered()
    return link



def _commit_once(link, composition, prepared, before_commit):
    """Reserve before CAS; retain the original receipt before runtime resumes."""
    link._ready(composition)
    o, executor = link.owner, link.executor
    root = executor._root
    command = root.command
    runtime_command = composition._runtime._command
    if (command is None or runtime_command is None or command.raw != runtime_command.raw
            or command.sequence != runtime_command.sequence or prepared.root is not root):
        raise world.WorldRejected('original prepared command/root required')
    link.service.poll()  # Explicit native world service before executor critical section.
    link._ready(composition)
    if (executor._root is not root or composition._runtime._command is not runtime_command
            or root.command is not command):
        raise world.WorldRejected('original command/root changed during world poll')
    slot = world._Commit(link.binding, command.raw, command.issue_ns,
                         min(command.deadline_ns, link.deadline))
    slot.dt_ns = prepared.relative.duration_ns
    slot.pre_root = root
    slot.publication_attempted = False
    link.slot = slot
    o._commits.append(slot)  # Reserved before the executor critical section and CAS.
    generation, actor_generation = o._veto_generation, composition._veto
    try:
        def pure_check():
            if (o._actor_links.get(id(link)) is not link or o._actor_link is not link
                    or o._binding is not link.binding or o._epoch is not link.epoch
                    or o._bindings.get(id(link.binding)) is not link.binding
                    or o._epochs.get(id(link.epoch)) is not link.epoch
                    or link.epoch.number in o._retired_epochs
                    or o._foreign.is_set() or o._vetoed or o._veto_generation != generation
                    or composition._foreign.is_set() or composition._retired
                    or composition._veto != actor_generation
                    or link.slot is not slot or executor._root is not root
                    or link.source.state != 'RUNNING' or link.source._clock is not link.clock
                    or link.source._polling or link.source._pose_reader is not link.pose_reader
                    or link.source._sampler is not link.sampler or link.source._profile is not link.profile
                    or link.epoch.identity != link.freeze_identity
                    or link.field._executor is not executor or o._em_scope_active is not None
                    or link.native._retired or link.native.state != 'AUTHENTICATED'
                    or link.native._containment_deadline != link.deadline
                    or o._publication is None or not o._publication.resolved
                    or o._publication.state != 'APPLIED'
                    or o._native_observation is None or o._native_observation.alive is not True
                    or o._status is None or o._status['identity'] != link.epoch.identity
                    or o._status['state'] not in ('FROZEN', 'BOUND_STOPPED')):
                raise world.WorldRejected('original world/source/action changed at final fence')
        def final():
            if slot.fence_used:
                raise world.WorldRejected('original final fence already consumed')
            slot.fence_used = True
            pure_check()
            fence = before_commit()
            pure_check()
            return _check_final(link, command, slot, fence)
        receipt = executor.commit_step(prepared, final)
        slot.receipt = receipt  # Preserve the exact return before any subsequent check.
        slot.post_root = executor._root
        if type(receipt) is not CommitReceipt:
            slot.uncertainty = 'unexpected original executor receipt type'
            raise world.WorldRejected('original CommitReceipt required')
        slot.committed = True
        slot.frame = slot.post_root.frame
        slot.view = world.motion.RendererView(slot.post_root.pose, slot.post_root.pose_revision)
        slot.deadline_ns = min(slot.deadline_ns, slot.frame.fence.deadline_ns)
        return receipt
    except BaseException:
        if not slot.committed and executor._root is not root:
            slot.uncertainty = 'root changed without returned receipt'
        raise


def _publish_once(owner, link):
    if (type(link) is not _OriginalWorldActorLink or link.owner is not owner
            or owner._actor_links.get(id(link)) is not link or owner._actor_link is not link
            or link.slot is None or not link.slot.committed or link.slot.receipt is None
            or link.slot.publication_attempted or link.slot.publication is not None
            or owner._binding is not link.binding or owner._epoch is not link.epoch
            or link.epoch.identity != link.freeze_identity
            or link.composition is None or link.composition._world_action_link is not link
            or link.composition._busy or link.composition._runtime._stepping
            or link.slot.view is None
            or link.executor._root.pose is not link.slot.post_root.pose
            or link.executor._root.pose_revision != link.slot.post_root.pose_revision):
        raise world.WorldRejected('one retained original numerical commit required')
    slot = link.slot
    slot.publication_attempted = True  # Consumed before hashing or native send.
    receipt = slot.receipt
    digest = world._hash(world._raw(dict(
        kind='original-actor-commit-v1', run_id=receipt.boot.run_id,
        generation=receipt.boot.generation, context_sha256=world._hash(receipt.boot.context_json),
        command_sha256=world._hash(slot.command_raw), command_seq=receipt.command_seq,
        pose_revision=receipt.pose_revision, start_ns=receipt.start_ns, end_ns=receipt.end_ns,
        deadline_ns=slot.deadline_ns, freeze_id=link.epoch.identity['freeze_id'])))
    slot.publication = owner._publish(link.binding, 'PUBLISH_VIEW', slot.view, receipt_digest=digest)
    return slot.publication



# These distinct exact fixture records and backend are software-only. They do
# not construct BOOT, verify a channel, run geometry or operate a native owner.
from dataclasses import dataclass
from types import SimpleNamespace

@dataclass(frozen=True)
class _FixtureFence:
    boot: object
    command_seq: int
    checked_ns: int
    step_end_ns: int
    deadline_ns: int

@dataclass(frozen=True)
class _FixtureReceipt:
    command_seq: int
    pose_revision: int
    start_ns: int
    end_ns: int


def _check_final(link, command, slot, fence):
    if type(link) is _OriginalWorldActorLink:
        required = StepFence
    elif type(link) is _SoftwareWorldActorLink:
        required = _FixtureFence
    else:
        raise world.WorldRejected('exact fixed link mode required')
    if (type(fence) is not required or fence.boot is not command.boot
            or type(fence.command_seq) is not int or fence.command_seq != command.sequence
            or type(fence.checked_ns) is not int or type(fence.step_end_ns) is not int
            or type(fence.deadline_ns) is not int
            or fence.step_end_ns-fence.checked_ns != slot.dt_ns
            or fence.deadline_ns > slot.deadline_ns or fence.step_end_ns >= slot.deadline_ns):
        raise world.WorldRejected('original final fence identity/interval/cap rejected')
    return fence


class _SoftwareOwner:
    software_fixture_only = True
    def __init__(self):
        self._native = None
        self._link = None


class _SoftwareBackend:
    software_fixture_only = True
    def __init__(self, owner, *, fail_send=False, stop_before_fence=False):
        if type(owner) is not _SoftwareOwner:
            raise ValueError('distinct software owner required')
        self.owner, self.fail_send, self.stop_before_fence = owner, fail_send, stop_before_fence
        self.events, self.revision = [], 0

    def poll(self):
        self.poll_observed_slot = self.owner._link.slot
        self.events.append('poll')

    def commit(self, link, final):
        self.events.append('commit-enter')
        if self.stop_before_fence:
            link.vetoed = True
        fence = final()
        self.events.append('cas')
        self.revision += 1
        receipt = _FixtureReceipt(fence.command_seq, self.revision, fence.checked_ns, fence.step_end_ns)
        self.events.append('commit-return')
        return receipt

    def send(self):
        self.events.append('send')
        if self.fail_send:
            raise RuntimeError('software unknown send effect')
        return 'software send returned'


class _SoftwareWorldActorLink:
    software_fixture_only = True
    def __init__(self, key, owner, backend):
        if key is not _SOFTWARE_KEY:
            raise ValueError('fixed software factory required')
        self.owner, self.backend = owner, backend
        self.slot, self.vetoed, self.getter_admitted = None, False, False

    def _check_software(self):
        if (type(self.owner) is not _SoftwareOwner or type(self.backend) is not _SoftwareBackend
                or self.backend.owner is not self.owner or self.owner._link is not self
                or native.is_original_owner(self.owner._native)):
            raise ValueError('software fixture custody changed')

    def step(self, sequence, dt_ns, *, fail_after_return=False):
        self._check_software()
        if (self.vetoed or self.slot is not None or type(sequence) is not int or sequence < 1
                or type(dt_ns) is not int or not 1 <= dt_ns <= 10_000_000):
            raise ValueError('fresh fixture action required')
        command = SimpleNamespace(boot=object(), sequence=sequence)
        self.backend.poll()
        slot = SimpleNamespace(dt_ns=dt_ns, deadline_ns=100_000_000, fence_used=False,
                               committed=False, receipt=None, publication_attempted=False)
        self.slot = slot
        def final():
            if slot.fence_used or self.vetoed:
                raise ValueError('fixture veto or repeated fence')
            slot.fence_used = True
            self.backend.events.append('final-fence')
            fence = _FixtureFence(command.boot, sequence, 1_000_000, 1_000_000+dt_ns, 100_000_000)
            return _check_final(self, command, slot, fence)
        receipt = self.backend.commit(self, final)
        if type(receipt) is not _FixtureReceipt:
            raise ValueError('exact fixture receipt required')
        slot.receipt, slot.committed = receipt, True
        if fail_after_return:
            raise RuntimeError('fixture post-return failure')
        return receipt

    def publish_once(self):
        self._check_software()
        if self.slot is None or not self.slot.committed or self.slot.publication_attempted:
            raise ValueError('one fixture publication attempt required')
        self.slot.publication_attempted = True
        return self.backend.send()


_SOFTWARE_KEY = object()

def _software_link_for_test(owner, backend):
    if (isinstance(owner, world._RootWorldOwner) or native.is_original_owner(owner)
            or type(owner) is not _SoftwareOwner or type(backend) is not _SoftwareBackend
            or backend.owner is not owner or owner._link is not None
            or native.is_original_owner(owner._native)):
        raise ValueError('distinct software owner/backend only')
    link = _SoftwareWorldActorLink(_SOFTWARE_KEY, owner, backend)
    owner._link = link
    return link
