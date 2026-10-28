"""Private original-owner byte pipe and pending-operation lifetime.

Portable structures contain no DLL load or native acquisition at import time.
Only ActorRegistry's explicit fresh route constructs the retained capsule.
Python private objects are trusted-host continuity, not OS authentication.
"""
import ctypes as C
from dataclasses import dataclass
import uuid

from .resource_cleanup import Outcome

_KEY = object()
_DWORD = C.c_uint32


class _Offsets(C.Structure):
    _fields_ = [('Offset', _DWORD), ('OffsetHigh', _DWORD)]


class _Position(C.Union):
    _fields_ = [('offsets', _Offsets), ('Pointer', C.c_void_p)]


class OVERLAPPED(C.Structure):
    _fields_ = [('Internal', C.c_size_t), ('InternalHigh', C.c_size_t),
                ('position', _Position), ('hEvent', C.c_void_p)]


@dataclass
class _StopClaim:
    attempted: bool = False
    returned: bool = False
    result: int | None = None
    error: int | None = None
    terminal: bool = False
    wait_result: int | None = None
    exit_code: int | None = None


class _Operation:
    def __init__(self, owner, endpoint, kind, size, raw, ordinal):
        self.owner, self.endpoint, self.native = owner, endpoint, endpoint.native
        self.kind, self.size, self.ordinal = kind, size, ordinal
        self.buffer = C.create_string_buffer(raw, size) if raw is not None else C.create_string_buffer(max(1, size))
        self.overlapped, self.original_count = OVERLAPPED(), _DWORD()
        self._bound_buffer, self._bound_overlapped, self._bound_count = self.buffer, self.overlapped, self.original_count
        self._bound_native = self.native
        self.event = None
        self._bound_event_native = None
        self.issued = self.issue_returned = self.settled = self.unknown = False
        self.result_bool = self.error = self.count = self.data = None
        self.issue_bool = self.issue_error = None
        self.cancel_attempted = self.cancel_returned = False
        self.cancel_bool = self.cancel_error = None
        self.accounted = False
        self.row = None

    def diagnostic(self):
        return dict(operation_id_local=self.ordinal, kind=self.kind,
            issued=self.issued, issue_returned=self.issue_returned,
            pending=self.issued and not self.settled, os_result_observed=self.settled,
            raw_bool=self.result_bool, winerror=self.error, returned_count=self.count,
            raw_issue_bool=self.issue_bool, raw_issue_error=self.issue_error,
            cancel_attempted=self.cancel_attempted, cancel_returned=self.cancel_returned,
            cancel_bool=self.cancel_bool, cancel_error=self.cancel_error,
            unknown_consumption=self.unknown or (self.issued and self.count is None and self.kind != 'connect'))


def _new(owner):
    from .actor_owner import ActorOwner
    if type(owner) is not ActorOwner or not owner._registry._contains(owner):
        raise ValueError('only retained original registry acquisition creates pipe IO')
    return _ActorPipeIO(_KEY, owner)


class _ActorPipeIO:
    def __init__(self, key, owner):
        if key is not _KEY:
            raise ValueError('original registry factory required')
        self.actor, self.resources, self.api = owner, owner._resources, owner._api
        self.backend = owner._backend
        self._original_api, self._original_backend = self.api, self.backend
        self.clock = owner._registry._clock
        self.clock_binding = owner._registry._clock_binding
        self.operations, self.endpoints = [], {}
        self.acquisitions = []
        self.process_state = 'NOT_ACQUIRED'
        self.process_native = self.thread_native = self.process_reference = None
        self.original_pi = None
        self.stop_claim = _StopClaim()
        self.write_reserved = False
        self.teardown_started = self.cleanup_consumed = self.quarantined = False
        self.teardown_deadline = None
        self.errors = []

    def capture_native(self, label, native, release, keepalive=None):
        # The native return is retained before ledger registration can raise.
        # An unregistered capsule is retained/quarantined, never adopted by PID.
        capsule = dict(label=label, native=getattr(native, 'value', native),
                       release=release, keepalive=keepalive, reference=None)
        self.acquisitions.append(capsule)
        return capsule

    def registered_native(self, capsule, reference):
        if (not any(capsule is item for item in self.acquisitions) or
                not self.resources.owns(reference) or reference.native != capsule['native'] or
                reference.release != capsule['release'] or reference.ambiguous):
            raise ValueError('original acquired native value was not registered exactly')
        capsule['reference'] = reference

    @property
    def acquisitions_registered(self):
        return all(item['reference'] is not None and self.resources.owns(item['reference'])
                   and item['reference'].native == item['native'] and
                   not item['reference'].ambiguous for item in self.acquisitions)

    def private_acquisition_diagnostics(self):
        pi = self.original_pi
        return dict(original_pi=None if pi is None else dict(
            hProcess=getattr(pi, 'hProcess', None), hThread=getattr(pi, 'hThread', None),
            process_id=getattr(pi, 'dwProcessId', None), thread_id=getattr(pi, 'dwThreadId', None)),
            native_returns=[dict(label=item['label'], native=item['native'], release=item['release'],
                registered_resource_id=None if item['reference'] is None else item['reference'].resource_id)
                for item in self.acquisitions])

    def _reference(self, label):
        ref = self.resources.find(label)
        if ref.ambiguous or ref.attempted or ref.release != 'kernel':
            raise ValueError('fresh original endpoint reference required')
        self.endpoints[label] = (ref, ref.native)
        return ref

    def acquire(self):
        logon = self._original_api.logon_sid(owner=self.resources)
        for direction, parent, child in (('outbound', 'input_write', 'input_read'),
                                          ('inbound', 'output_read', 'output_write')):
            name = r'\\.\pipe\LOCAL\DeepEye.Actor.' + uuid.uuid4().hex + '.' + parent
            self._original_api.overlapped_server(name, parent, direction, logon, owner=self.resources)
            endpoint = self._reference(parent)
            self._original_api.synchronous_client(name, child, direction, owner=self.resources)
            self._reference(child)
            op = self.operation(endpoint, 'connect', 0)
            self.issue(op)
            if not op.settled or op.error not in (0, 535):
                raise ValueError('original connect not settled before process creation')
        return tuple(self.endpoints[label][1] for label in
                     ('input_read', 'input_write', 'output_read', 'output_write'))

    def operation(self, endpoint, kind, size, raw=None):
        op = _Operation(self, endpoint, kind, size, raw, len(self.operations) + 1)
        self.operations.append(op)  # Retain storage before native event acquisition.
        native = self._original_api.overlapped_event('io_event_' + str(op.ordinal), owner=self.resources)
        op.event = self.resources.find('io_event_' + str(op.ordinal))
        if op.event.native != native or self._original_api.handle_flags(native) != 0:
            raise ValueError('original non-inheritable operation event required')
        op.overlapped.hEvent = native
        op._bound_event_native = native
        return op

    def continuity(self):
        actor = self.actor
        if (actor._pending_io is not self or actor._resources is not self.resources or
                self.resources._pending_io is not self or actor._backend is not self.backend or
                self.api is not self._original_api or self.backend is not self._original_backend or
                actor._api is not self._original_api or actor._registry._api is not self._original_api or
                actor._registry._clock is not self.clock or
                actor._registry._clock_binding is not self.clock_binding or not self.acquisitions_registered):
            raise ValueError('original IO capsule/clock replaced')
        for label in ('input_write', 'output_read'):
            ref, native = self.endpoints[label]
            if (not self.resources.owns(ref) or self.resources.find(label) is not ref or
                    ref.native != native or ref.attempted or ref.ambiguous):
                raise ValueError('original endpoint continuity lost')
        ref = self.process_reference
        if (ref is None or actor._process is not ref or actor._original_process is not ref or
                actor._original_native != self.process_native or ref.native != self.process_native or
                not self.resources.owns(ref) or ref.attempted or ref.ambiguous):
            raise ValueError('original process continuity lost')

    def _op_continuity(self, op):
        if (op.owner is not self or not any(op is item for item in self.operations) or
                not self.resources.owns(op.endpoint) or op.endpoint.native != op.native or
                op.endpoint.attempted or op.endpoint.ambiguous or op.event is None or
                not self.resources.owns(op.event) or op.event.attempted or op.event.ambiguous or
                op.buffer is not op._bound_buffer or op.overlapped is not op._bound_overlapped or
                op.original_count is not op._bound_count or op.native != op._bound_native or
                op.overlapped.hEvent != op._bound_event_native or op.event.native != op._bound_event_native):
            op.unknown = True
            raise ValueError('original pending operation continuity lost')

    @staticmethod
    def _return(value, size):
        if type(value) is not tuple or len(value) != size:
            raise ValueError('exact raw Win32 return tuple required')
        ok, error = value[:2]
        if (type(ok) not in (bool, int) or not -(1 << 31) <= ok < (1 << 31) or
                type(error) is not int or not 0 <= error <= 0xffffffff or (ok and error != 0)):
            raise ValueError('raw BOOL/error required')
        return value

    def issue(self, op):
        self._op_continuity(op)
        if op.issued: raise ValueError('original operation already issued')
        op.issued = True  # Reserve before native call; unknown never becomes zero.
        try:
            result = getattr(self._original_api, 'pipe_' + op.kind)(op)
            ok, error = self._return(result, 2)
            op.issue_returned, op.result_bool, op.error = True, int(ok), error
            op.issue_bool, op.issue_error = int(ok), error
            if op.kind == 'connect' and (ok or error == 535):
                op.settled = True  # Connect count is undefined, including TRUE.
            elif not ok and op.kind in ('read', 'write') and error in (995, 109):
                # Known completed failure: count is undefined, never zero.
                op.settled = True
            elif not ok and error != 997:
                op.unknown = True
                raise ValueError('original IO issue failed without a settled result')
        except BaseException:
            if not op.issue_returned: op.unknown = True
            raise

    def observe(self, op):
        if op.settled or not op.issued: return
        self._op_continuity(op)
        if op.unknown:
            return  # A zero-initialized OVERLAPPED is not proof an unknown call issued.
        try:
            ok, error, count = self._return(self._original_api.pipe_result(op), 3)
        except BaseException:
            op.unknown = True
            raise
        op.result_bool, op.error = int(ok), error
        if ok:
            if op.kind != 'connect':
                if type(count) is not int or not 0 <= count <= op.size:
                    op.unknown = True
                    raise ValueError('completed count exceeds original operation')
                op.count = count
                if op.kind == 'read': op.data = op.buffer.raw[:count]
            op.settled = True
        elif error == 996:
            return
        elif error in (995, 109):
            op.settled = True
            # Count is not defined by a failed GetOverlappedResult.
        else:
            op.unknown = True
            raise ValueError('original IO result unknown')

    @property
    def all_settled(self):
        return all(not op.issued or op.settled for op in self.operations)

    def before_release(self, ref):
        if (not self.acquisitions_registered or self.process_state == 'STARTED_UNKNOWN' or
                (not self.cleanup_consumed and self.process_state == 'ACQUIRED' and
                 not self.process_pair_registered)):
            raise ValueError('unknown original acquisition retains the whole resource cohort')
        if self.teardown_started and self.process_state == 'ACQUIRED' and not self.stop_claim.terminal:
            raise ValueError('original process terminal barrier precedes every teardown close')
        if not self.all_settled:
            depended = any(op.issued and not op.settled and
                           (ref is op.endpoint or ref is op.event) for op in self.operations)
            if depended or ref.kind == 'process' or ref.recovery or ref.release == 'profile':
                raise ValueError('pending IO retains this original resource before close claim')

    def process_started(self, pi):
        if self.process_state != 'NOT_ACQUIRED':
            raise ValueError('one original process creation only')
        self.original_pi = pi  # Strong retention BEFORE the native call can write it.
        self.process_state = 'STARTED_UNKNOWN'

    def process_returned(self, ok, pi):
        if self.process_state != 'STARTED_UNKNOWN':
            raise ValueError('original creation call was not reserved')
        if pi is not self.original_pi:
            raise ValueError('same preallocated original PI required')
        if ok:
            self.process_native, self.thread_native = pi.hProcess, pi.hThread
            self.process_state = 'ACQUIRED'
        elif not pi.hProcess and not pi.hThread:
            self.process_state = 'NOT_ACQUIRED'
        # False with unexpected returned native values remains unknown.

    def resolve_process(self):
        if self.process_state != 'ACQUIRED': return None
        refs = [ref for ref in self.resources.references if ref.kind == 'process' and
                ref.native == self.process_native and not ref.ambiguous and not ref.attempted]
        if len(refs) != 1: return None
        ref = refs[0]
        if self.process_reference is not None and self.process_reference is not ref:
            return None
        self.process_reference = ref
        return ref

    @property
    def process_pair_registered(self):
        if self.process_state == 'NOT_ACQUIRED': return True
        if self.process_state != 'ACQUIRED' or self.resolve_process() is None: return False
        threads = [ref for ref in self.resources.references if ref.label == 'primary_thread'
                   and ref.native == self.thread_native and not ref.ambiguous and not ref.attempted]
        return len(threads) == 1

    def _stop_target(self):
        ref = self.resolve_process()
        if ref is not None: return self.process_native, ref
        # A successful original CreateProcess can precede failed ledger
        # registration. Its retained original PI is still the stop identity;
        # it never grants generic cleanup or a replacement owned reference.
        if (self.process_reference is None and self.original_pi is not None and
                self.original_pi.hProcess == self.process_native and
                self.original_pi.hThread == self.thread_native and
                type(self.process_native) is int and self.process_native > 0 and
                not any(ref.kind == 'process' or ref.native == self.process_native
                        for ref in self.resources.references)):
            return self.process_native, None
        return None, None

    def cancel_once(self, op):
        if not op.issued or op.settled or op.cancel_attempted: return
        op.cancel_attempted = True
        try:
            self._op_continuity(op)
            ok, error = self._return(self._original_api.pipe_cancel(op), 2)
            op.cancel_returned, op.cancel_bool, op.cancel_error = True, int(ok), error
        except BaseException as error:
            self.errors.append(error)

    def stop_original(self):
        if self.process_state == 'NOT_ACQUIRED': return True
        if self.process_state != 'ACQUIRED': return False
        native, ref = self._stop_target()
        if native is None: return False
        claim = self.stop_claim
        try:
            state = self._original_api.Wait(native, 0)
            claim.wait_result = state if type(state) is int else None
            if type(state) is int and state == 0:
                claim.terminal = True
                if ref is not None: ref.terminal_confirmed = True
        except BaseException as error:
            self.errors.append(error)
        if not claim.terminal and not claim.attempted:
            claim.attempted = True  # Once-only even if native return/logging is lost.
            try:
                result, error_code = self._return(self._original_api.terminate_original(native), 2)
                claim.returned, claim.result, claim.error = True, int(result), error_code
                if not result:
                    try: self._original_api.check(result, 'TerminateProcess original overlapped actor')
                    except BaseException as error: self.errors.append(error)
            except BaseException as error:
                self.errors.append(error)
        # Initial Wait or Terminate failure never suppresses original readback.
        if not claim.terminal:
            try:
                state = self._original_api.Wait(native, 0)
                claim.wait_result = state if type(state) is int else None
                claim.terminal = type(state) is int and state == 0
                if ref is not None: ref.terminal_confirmed = claim.terminal
            except BaseException as error:
                self.errors.append(error)
        if claim.terminal and claim.exit_code is None:
            try:
                code = self._original_api.exit_code(native)
                if type(code) is not int or not 0 <= code <= 0xffffffff:
                    raise ValueError('actual exit code DWORD required')
                claim.exit_code = code
            except BaseException as error: self.errors.append(error)
        return claim.terminal

    def cleanup_terminate(self, resource):
        if resource.identity is not self.process_reference or not self.stop_claim.terminal or not self.all_settled:
            raise ValueError('original stop/quiescence barrier not proven')
        return Outcome.CONFIRMED  # Shared claim consumed; never another terminate.

    def remaining_time_known(self):
        try:
            if (self.actor._registry._clock is not self.clock or
                    self.actor._registry._clock_binding is not self.clock_binding):
                return False
            now = self.clock()
            if type(now) is not int or now < self.actor._registry._high:
                return False
            self.actor._registry._high = now
            return self.teardown_deadline is not None and now < self.teardown_deadline
        except BaseException as error:
            self.errors.append(error)
            return False

    def teardown(self):
        actor = self.actor
        if self.cleanup_consumed or self.quarantined: return actor._cleanup_result
        first = not self.teardown_started
        if first:
            self.teardown_started = True
            self.teardown_deadline = getattr(actor, '_run_deadline', None)
            if actor._invocation is not None:
                actor._invocation._failed = True
                if actor._invocation.deadline is not None:
                    self.teardown_deadline = min(self.teardown_deadline, actor._invocation.deadline)
            # First retirement has the only cancel/stop side effects. Later
            # owner entries observe originals; cleanup never issues them again.
            for op in self.operations: self.cancel_once(op)
        process_terminal = self.stop_original() if first else self.observe_process_only()
        for op in self.operations:
            if op.issued and not op.settled:
                try: self.observe(op)
                except BaseException as error: self.errors.append(error)
            try: self.account(op, journal=False)
            except BaseException as error: self.errors.append(error)
        safe = ((self.process_state == 'NOT_ACQUIRED' or process_terminal) and self.all_settled
                and self.process_pair_registered and self.acquisitions_registered
                and self.resources._pending_io is self)
        if safe:
            self.cleanup_consumed = True
            if actor._invocation is not None:
                try: actor._invocation.close_journal()
                except BaseException as error: actor._evidence_errors.append(error)
            actor._cleanup_result = self.resources.cleanup(self._original_backend, lambda event: actor._report(), actor._primary_error)
        elif (self.process_state == 'STARTED_UNKNOWN' or any(op.unknown for op in self.operations)
              or not self.acquisitions_registered or self.resources._pending_io is not self
              or not self.process_pair_registered
              or not self.remaining_time_known()):
            self.quarantined = True
        return actor._cleanup_result

    def observe_process_only(self):
        if self.process_state == 'NOT_ACQUIRED': return True
        native, ref = self._stop_target()
        if native is None: return False
        try:
            state = self._original_api.Wait(native, 0)
            self.stop_claim.wait_result = state if type(state) is int else None
            self.stop_claim.terminal = type(state) is int and state == 0
            if ref is not None: ref.terminal_confirmed = self.stop_claim.terminal
            if self.stop_claim.terminal and self.stop_claim.exit_code is None:
                code = self._original_api.exit_code(native)
                if type(code) is not int or not 0 <= code <= 0xffffffff:
                    raise ValueError('actual exit code DWORD required')
                self.stop_claim.exit_code = code
        except BaseException as error:
            self.errors.append(error)
        return self.stop_claim.terminal

    def account(self, op, *, journal=True):
        record = self.actor._invocation
        if record is None or op.row is None: return
        row = op.row
        row.update(op.diagnostic())
        if op.kind == 'write': row['bytes_written'] = op.count
        elif op.kind == 'read' and op.settled and not op.accounted:
            op.accounted = True
            row['returned_bytes'] = op.count
            if op.count is not None:
                row['raw_hex'] = op.data.hex()
                record._bytes += op.count
                row['stream_end'] = record._bytes
                if op.count == 0: record._zero_read_stop = True
            elif op.error == 109:
                record._eof = True
        record._unknown_consumption = record._unknown_consumption or op.unknown or (
            op.settled and op.count is None and op.kind != 'connect')
        row['outcome'] = ('result_observed' if op.settled else
                          'original_call_unknown' if op.unknown else
                          'pending' if op.issued else 'started_unknown')
        if journal:
            try: record._append(row)
            except BaseException:
                record._journal_failed = True
                raise


__all__ = []
