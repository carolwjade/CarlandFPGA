"""Borrow one original Root world for explicit polling; acquire nothing.

These checks are trusted-process identity conventions, not an OS security
boundary. The software fixture below never produces a RootWorldService.
"""
import threading
from types import MethodType

from ...integration import host_clock as clocks
from ...tools.diagnostic.causal_pl_exchange import CausalSourcePump
from ..sensors.owned_world_field import OwnedWorldField
from . import _owned_godot as native
from . import _world_loop as loop


_PRODUCTION = object()
_SOFTWARE = object()


def _field(source):
    if type(source) is not CausalSourcePump:
        raise ValueError('exact original CausalSourcePump required')
    pose, sampler = source._pose_reader, source._sampler
    if (type(pose) is not MethodType or type(sampler) is not MethodType
            or pose.__func__ is not OwnedWorldField.pose_reader
            or sampler.__func__ is not OwnedWorldField.sample_sigma
            or type(pose.__self__) is not OwnedWorldField
            or sampler.__self__ is not pose.__self__):
        raise ValueError('exact same owned-field methods required')
    return pose.__self__


def _production_inputs(clock, owner):
    if (type(clock) is not clocks.QpcHostClock
            or type(owner) is not loop._RootWorldOwner
            or owner._test is not False
            or not any(owner is retained for retained in loop._RETAINED)
            or not native.is_original_owner(owner._native)):
        raise ValueError('original retained production world and QPC required')
    clocks._require_binding(clock)  # Identity/thread check; no QPC sample.


def _software_inputs(clock, owner):
    # A software seam cannot adopt even a test-key real Root owner, much less an
    # original native acquisition. Its result also has a distinct exact type.
    if (isinstance(owner, loop._RootWorldOwner)
            or getattr(owner, 'software_fixture_only', None) is not True
            or getattr(clock, 'software_fixture_only', None) is not True
            or getattr(owner, '_test', None) is not True
            or native.is_original_owner(getattr(owner, '_native', None))):
        raise ValueError('software-only external owner and clock required')
    clock._check()


class _ServiceCore:
    __slots__ = ('_mode', '_clock', '_owner', '_source', '_native', '_binding',
                 '_field', '_deadline_ns', '_thread', '_failed', '_polling')

    def __init__(self, key, clock, owner, source):
        if hasattr(self, '_mode') or key not in (_PRODUCTION, _SOFTWARE):
            raise ValueError('service is single-use and cannot be rebound')
        if key is _PRODUCTION:
            _production_inputs(clock, owner)
        else:
            _software_inputs(clock, owner)
        self._mode = key
        self._clock, self._owner, self._source = clock, owner, source
        self._native, self._binding = owner._native, owner._binding
        self._field = _field(source)
        self._deadline_ns = self._native._containment_deadline
        self._thread = threading.get_ident()
        self._failed = self._polling = False
        try:
            self._validate(retired_source=False)
        except BaseException:
            self._failed = True
            raise

    @property
    def clock(self):
        """Original raw clock object; reading this never polls or samples."""
        return self._clock

    @property
    def source(self):
        """Original source object, without sampling, starting or rewarming it."""
        return self._source

    @property
    def deadline_ns(self):
        """Original absolute native containment cap, never renewed here."""
        return self._deadline_ns

    def _validate(self, *, retired_source):
        if self._failed:
            raise RuntimeError('world service permanently failed')
        if threading.get_ident() != self._thread:
            raise ValueError('original service owner thread required')
        owner, clock, original = self._owner, self._clock, self._native
        if self._mode is _PRODUCTION:
            if type(self) is not RootWorldService:
                raise ValueError('exact production service required')
            _production_inputs(clock, owner)
        else:
            _software_inputs(clock, owner)
        if (owner._clock is not clock or owner._native is not original
                or original.clock_binding is not clock
                or original._containment_deadline != self._deadline_ns
                or type(self._deadline_ns) is not int or self._deadline_ns <= 0
                or original._retired is not False
                or original.state != 'AUTHENTICATED'
                or owner._thread != self._thread or owner._foreign.is_set()
                or owner._busy is not False or owner._initialized is not True
                or owner._vetoed is not False):
            raise ValueError('original healthy world/clock/containment required')
        # Existing registry checks include the original current, unretired epoch.
        loop._RootWorldOwner._known_binding(owner, self._binding)
        if not retired_source:
            # Every fresh source operation must wait for original numerical
            # commit/publication/getter closure. Terminal drain acquires no
            # observation and must remain possible without fresh-source proof.
            loop._RootWorldOwner.require_source_pose_current(owner)
        source = self._source
        allowed = ('RETIRED',) if retired_source else ('NEW', 'RUNNING')
        if (source.state not in allowed or source._thread != self._thread
                or (source.state == 'RUNNING' and source._clock is not clock)
                or _field(source) is not self._field
                or self._field._executor is not self._binding.executor
                or self._field._scene is not self._binding.world_values.scene):
            raise ValueError('original current world field and source required')
        self._field._check()  # Current committed owner identity, no sampling.

    def _poll(self, *, retired_source):
        if self._failed or self._polling:
            self._failed = True
            raise RuntimeError('world service failed or reentered')
        self._polling = True
        try:
            self._validate(retired_source=retired_source)
            state = self._owner.poll()
            self._validate(retired_source=retired_source)
            return state
        except BaseException:
            self._failed = True
            raise  # Preserve the original owner's/clock's business exception.
        finally:
            self._polling = False

    def poll(self):
        """Explicitly poll the same world once around strict source checks."""
        return self._poll(retired_source=False)

    def poll_retired_source(self):
        """Observe terminal world status only after this source is RETIRED.

        This cannot restore a failed helper or grant fresh work. It performs no
        source polling, request writing, authorization or resource cleanup.
        """
        return self._poll(retired_source=True)


class RootWorldService(_ServiceCore):
    """Borrow only Root's already retained, initialized production world.

    Root supplies its original QpcHostClock and CausalSourcePump. Existing Root
    finally blocks retain source retirement and original world cleanup.
    """
    __slots__ = ()

    def __init__(self, clock, world_owner, source):
        if type(self) is not RootWorldService:
            raise ValueError('exact RootWorldService required')
        super().__init__(_PRODUCTION, clock, world_owner, source)


def _software_service_for_test(clock, world_owner, source):
    """Private software controls only; never return a production capability."""
    return _ServiceCore(_SOFTWARE, clock, world_owner, source)


__all__ = ['RootWorldService']
