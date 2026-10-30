"""Private disabled-by-default numerical fixture; never a production authority."""
from dataclasses import dataclass

def _require_unbound(executor):
    """Pure trusted-process check against all retained original Root bindings."""
    from . import _world_loop as world
    for owner in world._RETAINED:
        if type(owner) is world._RootWorldOwner:
            for binding in owner._bindings.values():
                if type(binding) is world._Binding and binding.executor is executor:
                    raise ValueError('Root-custodied executor cannot enter offboard component')

@dataclass(frozen=True, eq=False)
class Command:
    owner: object
    sequence: int
    issue_ns: int
    deadline_ns: int
    profile: str
    speed_code: int
    yaw_q: int
    pitch_q: int

@dataclass(frozen=True, eq=False, init=False)
class Prepared:
    root: object
    path: object
    relative: object
    sweeps: tuple
    solids: tuple
    proof_binding: str

@dataclass(frozen=True, eq=False)
class Fence:
    owner: object
    command_seq: int
    checked_ns: int
    step_end_ns: int
    deadline_ns: int

@dataclass(frozen=True, eq=False)
class Receipt:
    owner: object
    command_seq: int
    pose_revision: int
    start_ns: int
    end_ns: int

class Component:
    """Explicit diagnostic only; caller timestamps are not authenticated QPC."""
    def __init__(self, executor):
        from .motion_executor import OwnedMotionExecutor
        if type(executor) is not OwnedMotionExecutor:
            raise ValueError('exact executor required')
        _require_unbound(executor)
        self._executor=executor
        self._active=False
        self._effect='ready'
        self._receipt=None

    def activate(self):
        _require_unbound(self._executor)
        if self._active: raise ValueError('fixture already active')
        self._executor._offboard_activate(self)
        self._active=True

    def _check(self):
        _require_unbound(self._executor)
        if not self._active: raise ValueError('fixture disabled')
        if self._effect != 'ready': raise ValueError('fixture effect unresolved or unacknowledged')

    def acknowledge(self, receipt):
        _require_unbound(self._executor)
        if (not self._active or self._effect != 'committed'
                or receipt is not self._receipt or type(receipt) is not Receipt):
            raise ValueError('exact retained fixture receipt required')
        self._effect='ready'

    def command(self, *, sequence, issue_ns, deadline_ns, profile, speed_code, yaw_q, pitch_q):
        self._check()
        self._executor._offboard_command(self, Command(self,sequence,issue_ns,deadline_ns,profile,speed_code,yaw_q,pitch_q))

    def prepare(self, expected_pose_revision, dt_ns):
        self._check()
        return self._executor._offboard_prepare(self,expected_pose_revision,dt_ns)

    def commit(self, prepared, *, checked_ns, deadline_ns):
        self._check()
        duration=prepared.relative.duration_ns if type(prepared) is Prepared else 0
        end=checked_ns+duration if type(checked_ns) is int else checked_ns
        fence=Fence(self,prepared.root.command.sequence if type(prepared) is Prepared else -1,checked_ns,end,deadline_ns)
        self._effect='pending'
        try:
            receipt=self._executor._offboard_commit(self,prepared,fence)
            self._receipt=receipt
            self._effect='committed'
            return receipt
        except BaseException:
            self._effect='unknown_or_failed'
            raise
