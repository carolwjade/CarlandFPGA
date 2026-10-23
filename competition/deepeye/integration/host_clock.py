"""Fixed raw QPC source for a fresh run; never timing or endpoint authentication."""
from dataclasses import dataclass
import math
import threading
import time
from types import MappingProxyType
import uuid

_FACTORY = object()
_MAX_NS = (1 << 63)-1


def _qpc_leaf():
    return time.perf_counter_ns()


def _qpc_capability():
    info = time.get_clock_info('perf_counter')
    return dict(implementation=info.implementation, monotonic=info.monotonic,
                adjustable=info.adjustable, resolution=info.resolution)


@dataclass(frozen=True)
class _RawClockSample:
    raw_ns: int
    clock_domain: object
    interval_ns: None = None


class QpcHostClock:
    """Stable callable/domain identity, fixed leaf, one thread and high-water.

    Exact type/private construction are trusted-process conventions, not an OS
    security boundary. Advertised resolution never supplies timestamp uncertainty.
    """
    __slots__ = ('_key','_thread','_high','_failed','_metadata')

    def __init__(self, key, metadata=None):
        if key is not _FACTORY:
            raise ValueError('use the fixed fresh-run QPC factory')
        object.__setattr__(self,'_key',key)
        object.__setattr__(self,'_thread',threading.get_ident())
        object.__setattr__(self,'_high',0)
        object.__setattr__(self,'_failed',False)
        object.__setattr__(self,'_metadata',MappingProxyType(metadata))

    def __setattr__(self,name,value):
        raise AttributeError('fixed QPC binding is read-only')

    @property
    def metadata(self):
        return self._metadata

    def _check(self):
        if self._key is not _FACTORY or self._failed:
            raise ValueError('QPC binding permanently failed')
        if threading.get_ident() != self._thread:
            object.__setattr__(self,'_failed',True)
            raise ValueError('original QPC owner thread required')

    def __call__(self):
        self._check()
        try:
            raw = _qpc_leaf()
            if type(raw) is not int or not 0 <= raw <= _MAX_NS or raw < self._high:
                raise ValueError('strict bounded nonregressing raw QPC value required')
            object.__setattr__(self,'_high',raw)
            return raw
        except BaseException:
            object.__setattr__(self,'_failed',True)
            raise

    def read_sample(self):
        return _RawClockSample(self(),self)


def qpc_clock_for_new_run():
    """No caller leaf, now, mode or authenticated flag; no automatic fallback."""
    info = _qpc_capability()
    resolution = info.get('resolution')
    if (info.get('implementation') != 'QueryPerformanceCounter()'
            or info.get('monotonic') is not True or info.get('adjustable') is not False
            or type(resolution) not in (int,float) or not math.isfinite(resolution)
            or resolution <= 0):
        raise ValueError('fixed nonadjustable monotonic QPC capability required')
    return QpcHostClock(_FACTORY,dict(kind='qpc_raw_v1',domain_id=uuid.uuid4().hex,
        implementation=info['implementation'],resolution_seconds=resolution,
        monotonic=True,adjustable=False,timestamp_uncertainty_ns=None,
        authenticated=False,measured_timing=False))


def _require_binding(binding):
    if binding is not None:
        if type(binding) is not QpcHostClock:
            raise ValueError('exact fixed fresh-run QPC binding required')
        binding._check()
    return binding


def _description(binding):
    return (dict(kind='legacy_monotonic',timestamp_uncertainty_ns=None,
                 authenticated=False,measured_timing=False) if binding is None
            else dict(binding.metadata))


__all__ = ['QpcHostClock','qpc_clock_for_new_run']
