"""Owner-thread source servicing for the original chain; no scheduling guarantee."""
from dataclasses import dataclass, replace
import threading
from ...integration.host_clock import QpcHostClock
from ...simulation.authority import _world_loop
from ..run_causal_functional_chain import FunctionalSource
from .functional50_ssh_a import Session
from .original_source_trace_scan_a import OriginalSourceTraceScan

@dataclass(frozen=True)
class PumpRecord:
    payload: object
    token: object
    entry: object
    draft: object
    admission: object
    received_qpc_ns: int
    released: bool

class OriginalChainSourcePump:
    def __init__(self, session, functional_source, scanner):
        if (type(session) is not Session or type(functional_source) is not FunctionalSource
                or type(scanner) is not OriginalSourceTraceScan):
            raise ValueError('exact original session/source/scanner required')
        self._session=session;self._source=functional_source;self._scanner=scanner
        self._clock=functional_source.clock;self._thread=threading.get_ident()
        self._book=functional_source.book;self._causal=functional_source.source
        self._owner=functional_source.owner;self._binding=functional_source.binding
        self._enabled=False;self._failed=False;self._ever_enabled=False
        self._history=[];self._pending=None
        if self._causal.state == 'NEW':
            self._check(False)
            a=self._scanner;f=self._source;b=self._book
            if (a._defer_start is not True or a._activated is not False
                or a._activation_attempted is not False or a._ledger is not None
                or a._origin is not None or a._failed or f._start_attempted
                or self._causal._origin is not None or self._causal._clock is not None
                or self._causal._count != 0 or self._causal._last_tick is not None
                or self._causal._polling is not False or self._causal._source_book is not b
                or b._source is not self._causal or b._clock is not self._clock
                or b._state != 'NEW' or b._origin is not None or b._samples or b._active is not None
                or f._retained_samples or f._pending is not None or a._admitted
                or a._prepared is not False or a._prepare_count != 0):
                raise ValueError('prepared deferred original source required')
        else:
            self._check(True)
    @property
    def session(self): return self._session
    @property
    def source(self): return self._source
    @property
    def scanner(self): return self._scanner
    @property
    def clock(self): return self._clock
    @property
    def enabled(self): return self._enabled and not self._failed
    @property
    def failed(self): return self._failed
    @property
    def history(self): return tuple(self._history)
    @property
    def pending(self): return self._pending
    def _check(self, live, *, _closing=None):
        f=self._source;s=self._session;a=self._scanner
        if (self._failed or threading.get_ident()!=self._thread or s._thread!=self._thread
            or f._thread!=self._thread or a._thread!=self._thread
            or s._protocol != 'functional50_chain_v2'
            or type(self._clock) is not QpcHostClock or s._clock is not self._clock
            or f.clock is not self._clock or f.owner is not self._owner
            or type(self._owner) is not _world_loop._RootWorldOwner
            or not any(self._owner is x for x in _world_loop._RETAINED)
            or f.binding is not self._binding or self._owner._binding is not self._binding
            or self._owner._clock is not self._clock
            or f.source is not self._causal or f.book is not self._book
            or a._functional is not f or a._source is not self._causal
            or a._book is not self._book or a._clock is not self._clock
            or a._source_scan_cycle_v2 is not True):
            raise ValueError('original source/session/clock/thread association required')
        if _closing is None:s._check()
        else:s._check_closing(_closing)
        f._check_thread()
        if live:
            if (not f._start_attempted or self._causal.state!='RUNNING' or self._causal._clock is not self._clock
                or a._activated is not True or a._ledger is None):
                raise ValueError('running original source required')
            a._check()
    def enable(self):
        if self._ever_enabled: raise ValueError('pump enable is one-use')
        self._ever_enabled=True
        try:self._check(True)
        except BaseException:
            self._failed=True;raise
        self._enabled=True
    def poll_once(self, session, *, _closing=None):
        if session is not self._session: raise ValueError('same original session required')
        try:
            if _closing is None:self._check(self._enabled)
            else:self._check(self._enabled,_closing=_closing)
            if not self._enabled:return None
            pair=self._source.poll_sample()
            if pair is None:return None
            self._pending=(pair,None)
            payload,token=pair
            entry=self._source._retained_sample(payload)
            self._pending=(pair,entry)
            admission=self._scanner.admit(payload)
            observed=self._scanner._admitted[-1]
            if observed['entry'] is not entry or observed['token'] is not token or observed['admission'] is not admission:
                raise ValueError('original scanner admission association changed')
            record=PumpRecord(payload,token,entry,observed['draft'],admission,observed['received'],False)
            self._history.append(record)
            self._source.release_sample(payload)
            self._history[-1]=replace(record,released=True)
            self._pending=None
            return admission
        except BaseException:
            self._failed=True;raise
