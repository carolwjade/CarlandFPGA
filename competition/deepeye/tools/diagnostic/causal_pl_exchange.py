"""Root-owned candidate sensing/PL exchange; no BOOT or movement authority.

World callbacks belong only to the trusted authority. Candidate/controller
outputs contain accepted board counts, never callbacks, layout or source floats.
The same original transport remains owned and cleaned by run_private_pl_live.
"""
import hashlib
import json
import os
from pathlib import Path
import threading
import time

from ...integration import host_clock as clocks, private_pl_stream as pl
from ...integration import sensor_source
from ...simulation.sensors import forward_profile as forward
from ...simulation.authority import live_chain_channels as channels


def _source_profile():
    return dict(name='candidate_causal_source_v1',
        signal_profile='deepeye_forward_profile_candidate_v1',
        quality_encoding='candidate_four_channel_quality_v1',
        source_age_cap_ns=100_000_000, session_max_ns=10_000_000_000,
        max_source_records=1001)


SOURCE_PROFILE = _source_profile()  # Exported copy cannot change validation policy.


def _feedback_profile():
    return dict(name='root_causal_feedback_v1', max_calls=16,
                movement_authority=False, CPU_completion_created=False)


FEEDBACK_PROFILE = _feedback_profile()


def select_em_scope_profile(plan):
    """Exact opt-in local source profile, covered by the Root plan hash."""
    if type(plan) is not dict:
        raise ValueError('Root plan object required')
    if 'source_acquisition_profile' not in plan:
        return False
    profile = plan['source_acquisition_profile']
    if (type(profile) is not dict or set(profile) != {'name'}
            or type(profile['name']) is not str
            or profile['name'] != 'root_original_em_scope_v1'):
        raise ValueError('exact root_original_em_scope_v1 profile required')
    return True


def select_source_book_profile(plan):
    """Exact opt-in for original nominal/actual source timing observations."""
    if type(plan) is not dict:
        raise ValueError('Root plan object required')
    if 'source_book_profile' not in plan:
        return False
    profile = plan['source_book_profile']
    if (type(profile) is not dict or set(profile) != {'name'}
            or type(profile['name']) is not str
            or profile['name'] != 'root_original_source_time_book_v1'):
        raise ValueError('exact root_original_source_time_book_v1 profile required')
    return True


def select_jit_kernel_profile(plan):
    if type(plan) is not dict:
        raise ValueError('Root plan object required')
    if 'source_kernel_profile' not in plan:
        return False
    profile = plan['source_kernel_profile']
    if (type(profile) is not dict or set(profile) != {'name'}
            or type(profile['name']) is not str
            or profile['name'] != 'root_strict_jit_ordered_kernel_v1'):
        raise ValueError('exact Root JIT kernel profile required')
    return True


def select_feedback_mode(template, request, activation, callback, *, causal_mode):
    """Select reviewed Root code only; correlation/profile is not authentication."""
    records = (template, request, activation)
    if any(type(record) is not dict for record in records):
        raise ValueError('Root template/request/activation objects required')
    declared = ['candidate_feedback_profile' in record for record in records]
    if callback is None and not any(declared): return None
    if causal_mode is not True or not callable(callback) or not all(declared):
        raise ValueError('explicit causal source and Root feedback in all records required')
    expected = _feedback_profile()
    for record in records:
        value = record['candidate_feedback_profile']
        if (type(value) is not dict or value.keys() != expected.keys() or
                any(type(value[key]) is not type(wanted) or value[key] != wanted
                    for key, wanted in expected.items())):
            raise ValueError('only exact root_causal_feedback_v1 policy allowed')
    return callback


def select_source_mode(template, request, activation, source):
    records = (template, request, activation)
    if any(type(record) is not dict for record in records):
        raise ValueError('Root template/request/activation objects required')
    declared = ['candidate_source_profile' in record for record in records]
    if source is None:
        if any(declared): raise ValueError('explicit Root-owned causal source missing')
        return False
    if (type(source) is not CausalSourcePump or source.state != 'NEW' or
            source._thread != threading.get_ident() or not all(declared)):
        raise ValueError('one fresh Root source and all three profile declarations required')
    expected = _source_profile()
    for record in records:
        value = record['candidate_source_profile']
        if (type(value) is not dict or value.keys() != expected.keys() or
                any(type(value[key]) is not type(wanted) or value[key] != wanted
                    for key, wanted in expected.items())):
            raise ValueError('only exact candidate_causal_source_v1 policy allowed')
    if 'values' in activation or 'qualities' in activation:
        raise ValueError('causal source mode cannot also declare fixed activation inputs')
    return True


def source_paths(jit_enabled=False, dependency_config=None):
    from ...simulation.authority import root_source_book
    paths = dict(causal_exchange=Path(__file__),
                candidate_channel=Path(channels.__file__),
                sensor_source=Path(sensor_source.__file__),
                forward_profile=Path(forward.__file__),
                original_source_book=Path(root_source_book.__file__))
    if jit_enabled:
        if (type(dependency_config) is not dict or
                set(dependency_config) != {'dependency_path','dependency_files','numpy_path','numpy_files'}):
            raise ValueError('verified dependency manifest required')
        paths.update(root_jit_kernel=Path(forward.__file__).parent.parent / 'authority' / '_root_jit_kernel.py',
                     ordered_jit_kernel=Path(forward.__file__).with_name('_jit_ordered_kernel.py'))
        for area, records, prefix in ((dependency_config['dependency_path'], dependency_config['dependency_files'], 'jitdep:'),
                                      (dependency_config['numpy_path'], dependency_config['numpy_files'], 'numpydep:')):
            for name, _digest in records:
                paths[prefix+name] = Path(area) / name
    return paths


class _CausalSourcePump:
    """Single-use schedule core. Missed native slots are never backfilled."""
    def __init__(self, profile, pose_reader, sampler, *, contact_reader=None,
                 medium_context='formation'):
        if not callable(pose_reader) or not callable(sampler):
            raise ValueError('trusted world pose/conductivity readers required')
        if contact_reader is not None and not callable(contact_reader):
            raise ValueError('already-occurred contact reader must be callable')
        self._profile, self._pose_reader, self._sampler = profile, pose_reader, sampler
        self._contact_reader, self._medium = contact_reader, medium_context
        self._thread = threading.get_ident()
        self._origin = self._clock = self._high = self._last_tick = None
        self._count = 0
        self._em_scope_factory = None
        self._jit_backend = None
        self._source_book = None
        self._polling = False
        self.state = 'NEW'

    def _bind_software_source_book_for_test(self, book):
        """Marked software stub only; never binds the public candidate source."""
        try:
            if (type(self) is not _CausalSourcePump or self.state != 'NEW'
                    or threading.get_ident() != self._thread
                    or self._source_book is not None
                    or getattr(book, 'software_fixture_only', None) is not True
                    or book.source is not self):
                raise ValueError('fresh software-only pump/book required')
            self._source_book = book
        except BaseException:
            self.state = 'FAILED'
            raise

    def _book_failed(self, primary):
        if self._source_book is not None:
            try:
                self._source_book.fail('original source acquisition failed')
            except BaseException as secondary:
                # Keep the original instrument/source error and finite evidence.
                # The production fail() is pure/nonthrowing; this also covers
                # the distinct software stub and unexpected secondary failures.
                try:
                    previous = getattr(primary, '_causal_exchange_secondary_errors', ())
                    primary._causal_exchange_secondary_errors = (previous+(
                        dict(stage='source_book_fail', type=type(secondary).__name__,
                             message=str(secondary)[:256]),))[-8:]
                except BaseException:
                    # Reporting a secondary failure cannot replace the first.
                    pass

    def _bind_software_em_scope_for_test(self, factory):
        """Distinct software pump core only; cannot bind the public source."""
        try:
            if (type(self) is not _CausalSourcePump or self.state != 'NEW'
                    or threading.get_ident() != self._thread
                    or self._em_scope_factory is not None
                    or getattr(factory, 'software_fixture_only', None) is not True
                    or getattr(factory, '_source', None) is not self):
                raise ValueError('fresh software-only pump/factory required')
            self._em_scope_factory = factory
        except BaseException:
            self.state = 'FAILED'
            raise

    def start(self, origin_ns, clock):
        if self.state != 'NEW' or threading.get_ident() != self._thread or not callable(clock):
            raise ValueError('fresh original source owner required; no restart')
        pl.uint(origin_ns, 63)
        self._origin, self._high, self._clock = origin_ns, origin_ns, clock
        self.state = 'RUNNING'
        if self._source_book is not None:
            try:
                self._source_book.start()
            except BaseException as primary:
                self.state = 'FAILED'
                self._book_failed(primary)
                raise

    def poll(self):
        entered = False
        try:
            if self._polling:
                raise ValueError('reentrant source acquisition refused')
            self._polling = True
            entered = True
            if self.state != 'RUNNING' or threading.get_ident() != self._thread:
                raise ValueError('original running source owner required')
            if self._em_scope_factory is not None and self._contact_reader is not None:
                raise ValueError('EM-only scope profile does not admit contact callbacks')
            now = self._clock(); pl.uint(now, 63)
            if now < self._high or now < self._origin:
                raise ValueError('original source clock regressed')
            self._high = now
            if now-self._origin > _source_profile()['session_max_ns']:
                raise TimeoutError('source session expired')
            tick = (now-self._origin)//10_000_000*10
            if tick == self._last_tick: return None
            if self._count >= 1001: raise ValueError('source record cap exhausted')
            self._last_tick = tick  # Consume before callbacks; no failed-slot replay.
            self._count += 1
            book = self._source_book
            token = None if book is None else book.open_sample(tick, now)
            if self.state != 'RUNNING':
                raise ValueError('source book invalidated active acquisition')
            if tick % 50 == 0:
                if self._em_scope_factory is None:
                    pose = self._pose_reader() if book is None else book.read_pose(token, kind='em')
                    if self.state != 'RUNNING':
                        raise ValueError('pose read invalidated active acquisition')
                    self._profile.acquire_em(tick, pose,
                        context=self._medium, sampler=self._sampler)
                else:
                    with self._em_scope_factory.begin(tick) as scope:
                        pose = self._pose_reader() if book is None else book.read_pose(token, kind='em')
                        if self.state != 'RUNNING':
                            raise ValueError('pose read invalidated active acquisition')
                        if self._jit_backend is None:
                            self._profile.acquire_em(tick, pose,
                                context=self._medium, sampler=scope.sampler)
                        else:
                            from ...simulation.authority import _root_jit_kernel as root_jit
                            if not root_jit._valid_backend_association(self, self._jit_backend):
                                raise ValueError('original JIT backend association lost')
                            self._jit_backend.acquire(tick, pose, self._medium, scope)
            if self.state != 'RUNNING':
                raise ValueError('source callback invalidated active acquisition')
            contact = None if self._contact_reader is None else self._contact_reader(tick)
            if book is None:
                payload = self._profile.sample_adc(tick, contact_accel_g=contact).to_payload()
            else:
                book.read_pose(token, kind='adc')
                if self.state != 'RUNNING':
                    raise ValueError('ADC pose read invalidated active acquisition')
                handle = book.begin_adc(token)
                if self.state != 'RUNNING':
                    raise ValueError('ADC intent invalidated active acquisition')
                sample = self._profile.sample_adc(tick, contact_accel_g=contact)
                book.end_adc(token, handle)
                payload = sample.to_payload()
            if self.state != 'RUNNING':
                raise ValueError('source callback invalidated active acquisition')
            if book is not None:
                book.finish_sample(token, payload)
                if self.state != 'RUNNING':
                    raise ValueError('source book invalidated completed acquisition')
            return payload
        except BaseException as primary:
            self.state = 'FAILED'
            self._book_failed(primary)
            raise
        finally:
            if entered:
                self._polling = False

    def retire(self, reason):
        if type(reason) is not str or not reason: raise ValueError('source retirement reason required')
        self.state = 'RETIRED'
        if self._source_book is not None:
            self._source_book.retire(reason)


class CausalSourcePump(_CausalSourcePump):
    """Fresh real candidate ForwardProfile; callbacks stay in the Root authority."""
    def __init__(self, pose_reader, sampler, *, contact_reader=None,
                 medium_context='formation'):
        if medium_context not in forward.KNOWN_CONTEXTS:
            raise ValueError('explicit supported candidate medium context required')
        super().__init__(forward.ForwardProfile(), pose_reader, sampler,
            contact_reader=contact_reader, medium_context=medium_context)
        self.prepared = False

    def bind_original_source_book(self, book):
        """One exact original-owner book; no caller callback/provider seam."""
        from ...simulation.authority.root_source_book import RootSourceBook
        try:
            if (type(self) is not CausalSourcePump or self.state != 'NEW'
                    or threading.get_ident() != self._thread
                    or self._source_book is not None
                    or type(book) is not RootSourceBook or book.source is not self
                    or type(self._profile) is not forward.ForwardProfile):
                raise ValueError('fresh exact original source/book required')
            self._source_book = book
        except BaseException:
            self.state = 'FAILED'
            raise

    def bind_original_em_scope(self, factory):
        """Bind one already registered original-world factory before starting."""
        from ...simulation.authority import _world_loop as world
        try:
            if (type(self) is not CausalSourcePump or self.state != 'NEW'
                    or threading.get_ident() != self._thread
                    or self._em_scope_factory is not None
                    or self._contact_reader is not None
                    or type(self._profile) is not forward.ForwardProfile
                    or type(factory) is not world._OriginalEmScopeFactory
                    or factory._source is not self):
                raise ValueError('fresh original source/scope factory required')
            factory._check(None)
            self._em_scope_factory = factory
        except BaseException:
            self.state = 'FAILED'
            raise

    def bind_original_jit_backend(self, backend):
        from ...simulation.authority import _root_jit_kernel as root_jit
        try:
            if (type(self) is not CausalSourcePump or self.state != 'NEW'
                    or threading.get_ident() != self._thread
                    or self._jit_backend is not None
                    or type(backend) is not root_jit._OriginalBackend
                    or backend._source is not self
                    or backend._factory is not self._em_scope_factory):
                raise ValueError('fresh exact original JIT association required')
            self._jit_backend = backend
        except BaseException:
            self.state = 'FAILED'
            raise

    def prepare(self):
        if self.state != 'NEW' or threading.get_ident() != self._thread:
            raise ValueError('cannot rewarm/restart or transfer a source run')
        # Warm geometry only, not a signal, scene lookup or precomputed observation.
        if not self.prepared:
            try:forward._weight_table()
            except BaseException:
                self.state = 'FAILED'
                raise
            self.prepared = True


def _raw(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def _terminal(raw, context, scans):
    doc = pl.decode(raw)
    if (set(doc) != {'schema','kind','context','cleanup','error','frames_completed','movement_authorized'} or
            type(doc['schema']) is not int or doc['schema'] != 1 or
            doc['kind'] != 'diagnostic_stopped' or pl.context(doc['context']) != context or
            doc['movement_authorized'] is not False or type(doc['frames_completed']) is not int or
            doc['frames_completed'] != scans or doc['error'] is not None):
        raise ValueError('original causal terminal identity/error mismatch')
    cleanup = doc['cleanup']
    if (type(cleanup) is not dict or cleanup.get('attempted') is not True or
            cleanup.get('confirmed') is not True or type(cleanup.get('status')) is not int or
            cleanup['status'] != 0 or type(cleanup.get('active_tag')) is not int or
            cleanup['active_tag'] != 0 or type(cleanup.get('secondary_errors')) is not list or
            cleanup['secondary_errors']):
        raise ValueError('original causal raw STOP not confirmed')
    return doc


def _require_world_service(service, clock, source, *, causal_mode):
    if service is None:
        return None
    # Lazy import: the service module itself imports CausalSourcePump.
    from ...simulation.authority.root_world_service import RootWorldService
    if (causal_mode is not True or type(service) is not RootWorldService
            or type(clock) is not clocks.QpcHostClock
            or service.clock is not clock or service.source is not source):
        raise ValueError('exact causal original-world service/clock/source required')
    clocks._require_binding(clock)
    return service


def _wait_world_line(transport, clock, service, seconds, *, retired_source=False):
    """One original nonblocking wait, tightened to the original native cap."""
    if service.clock is not clock or type(seconds) is not int or not 1 <= seconds <= 180:
        raise ValueError('original world clock and bounded wait required')
    started = clock(); pl.uint(started, 63)
    cap = service.deadline_ns; pl.uint(cap, 63)
    deadline = min(started+seconds*1_000_000_000, cap)
    high = started
    while True:
        now = clock(); pl.uint(now, 63)
        if now < high: raise ValueError('original world wait clock regressed')
        high = now
        if now >= deadline: raise TimeoutError('original world wait expired')
        if retired_source: service.poll_retired_source()
        else: service.poll()
        now = clock(); pl.uint(now, 63)
        if now < high: raise ValueError('original world wait clock regressed')
        high = now
        if now >= deadline: raise TimeoutError('original world wait expired')
        raw, eof = transport.poll_line()
        now = clock(); pl.uint(now, 63)
        if now < high: raise ValueError('original world wait clock regressed')
        high = now
        if now >= deadline: raise TimeoutError('original world wait expired')
        if raw is not None: return raw
        if eof: return None
        time.sleep(.001)


def _require_pending_source_fresh(channel, request, now):
    """Recheck original pending ADC/EM times, never the response-profile cap."""
    pending = channel._pending
    if channel.state != 'PENDING' or pending is None or pending.request_raw != request:
        raise ValueError('original pending source/request association required before send')
    record = pending.record
    for tick in (record.adc_tick_ms, record.em_tick_ms):
        if tick is not None and not 0 <= now-channel._source_ns(tick) <= sensor_source.TIMEOUT_NS:
            raise ValueError('original pending source expired before send')


def _exchange_causal_core(channel, transport, source, *, clock, origin_ns, scans, out,
                          _start=None, context=None, on_candidate=None,
                          _world_service=None):
    if type(scans) is not int or not 1 <= scans <= 16:
        raise ValueError('finite causal scan count1..16 required')
    if on_candidate is not None and not callable(on_candidate):
        raise ValueError('trusted Root consumer must be callable')
    # Public admission is exact-type above. This private core also supports the
    # distinct, explicitly software-only service used by bounded controls.
    if (_world_service is not None and
            (_world_service.clock is not clock or _world_service.source is not source)):
        raise ValueError('same original service clock/source required')
    root = Path(out)/'causal-exchange'
    history = None; closed = False; total = 0; records = []; high = origin_ns
    feedback_calls = []
    primary_error = None
    latest = False; request_deadline = None
    def budget(raw):
        nonlocal total
        if type(raw) is not bytes or total+len(raw) > 8*1024*1024:
            raise ValueError('bounded causal evidence exhausted')
        total += len(raw)
    def write(name, raw):
        budget(raw)
        with (root/name).open('xb') as stream:
            if stream.write(raw) != len(raw): raise OSError('short causal evidence write')
            stream.flush();os.fsync(stream.fileno())
    def close_input():
        nonlocal closed
        if not closed:
            closed = True  # Never repeat a failed/unknown close operation.
            transport.close_input()
    def admit_payload(payload):
        nonlocal latest
        raw = _raw(payload)
        if len(raw) > 4096: raise ValueError('bounded causal source record required')
        budget(raw)
        if history.write(raw) != len(raw): raise OSError('short causal source evidence')
        history.flush()
        if _world_service is not None: _world_service.poll()
        channel.admit_sample(payload)
        latest = True
    try:
        if _world_service is not None: _world_service.poll()
        root.mkdir(exist_ok=False)
        history = (root/'source-history.jsonl').open('xb')
        write('intent.json', _raw(dict(source_profile=_source_profile(), scans=scans,
            feedback_profile=None if on_candidate is None else _feedback_profile(),
            context=channel._owner.context if channel is not None else pl.context(context),
            origin_ns=origin_ns, source_started=_start is None,
            movement_authorized=False, production_authentication_created=False)))
        if _start is not None:
            # All directory/open/intent sync work precedes the actual run origin.
            # First sample is taken immediately at that origin, never backfilled.
            if _world_service is not None: _world_service.poll()
            channel, origin_ns, first = _start()
            high = origin_ns
            if first is None: raise ValueError('first actual source record absent')
            admit_payload(first)
            write('source-origin.json', _raw(dict(origin_ns=origin_ns,
                first_actual_adc_tick_ms=first['adc_tick_ms'])))
        for _ in range(10001):
            if _world_service is not None: _world_service.poll()
            now = clock(); pl.uint(now, 63)
            if now < high: raise ValueError('exchange owner clock regressed')
            high = now
            returned, eof = transport.poll_line()
            if returned is not None:
                # Preserve original stale/malformed bytes before ANY admission.
                write('response-%02d.bin' % len(records), returned)
                if _world_service is not None: _world_service.poll()
                candidate = channel.accept_capture(returned)
                records.append(candidate)
                candidate_raw = _raw(candidate)
                index = len(records)-1
                write('candidate-%02d.json' % index, candidate_raw)
                request_deadline = None
                if on_candidate is not None:
                    begin = clock(); pl.uint(begin, 63)
                    if begin < high: raise ValueError('feedback owner clock regressed')
                    if begin-origin_ns > _source_profile()['session_max_ns']:
                        raise TimeoutError('source session expired before Root consumer')
                    evidence = dict(invocation_index=index,
                        candidate_sha256=hashlib.sha256(candidate_raw).hexdigest(),
                        capture_sha256=candidate['observation_identity']['capture_sha256'],
                        begin_qpc_ns=begin, CPU_completion_created=False,
                        movement_authorized=False)
                    write('feedback-%02d-started.json' % index, _raw(dict(evidence,
                        state='started_unknown_before_root_consumer')))
                    if _world_service is not None: _world_service.poll()
                    dispatch = clock(); pl.uint(dispatch, 63)
                    if dispatch < begin: raise ValueError('feedback owner clock regressed')
                    if dispatch-origin_ns > _source_profile()['session_max_ns']:
                        write('feedback-%02d-not-called.json' % index, _raw(dict(evidence,
                            state='not_called_expired_before_consumer', checked_qpc_ns=dispatch)))
                        raise TimeoutError('source session expired during consumer intent publication')
                    # A detached candidate contains only board-returned input.
                    # Root package review must bind this trusted code/closure;
                    # its return never becomes completion or movement evidence.
                    try:
                        result = on_candidate(json.loads(candidate_raw))
                    except BaseException as primary:
                        if _world_service is not None:
                            try: _world_service.poll()
                            except BaseException as secondary:
                                primary._causal_exchange_secondary_errors = (
                                    getattr(primary, '_causal_exchange_secondary_errors', ())+
                                    (dict(stage='world_after_consumer', type=type(secondary).__name__,
                                          message=str(secondary)[:256]),))
                        raise
                    if _world_service is not None: _world_service.poll()
                    if result is not None:
                        raise ValueError('Root consumer returns None; no authority claims accepted')
                    end = clock(); pl.uint(end, 63)
                    if end < dispatch: raise ValueError('feedback owner clock regressed')
                    high = now = end
                    completed = dict(evidence, dispatch_qpc_ns=dispatch,
                                     end_qpc_ns=end, state='returned')
                    write('feedback-%02d-returned.json' % index, _raw(completed))
                    feedback_calls.append(completed)
            if now-origin_ns > _source_profile()['session_max_ns']:
                raise TimeoutError('bounded causal host session expired')
            if len(records) == scans: break
            if eof: raise ValueError('original transport ended before all causal responses')
            if _world_service is not None: _world_service.poll()
            payload = source.poll()
            if payload is not None:
                admit_payload(payload)
            if channel.state == 'READY' and latest:
                if _world_service is not None: _world_service.poll()
                request = channel.next_request()
                write('request-%02d.json' % len(records), _raw(dict(
                    raw_hex=request.hex(), raw_sha256=hashlib.sha256(request).hexdigest(),
                    state='started_unknown_before_original_write')))
                request_deadline = pl.decode(request)['original_host_qpc_ns'][0]+channel._owner._age
                latest = False
                history.flush();os.fsync(history.fileno())
                if _world_service is not None:
                    _world_service.poll()
                    checked = clock(); pl.uint(checked, 63)
                    if checked < high: raise ValueError('exchange owner clock regressed')
                    high = checked
                    if checked > request_deadline:
                        raise TimeoutError('original pending capture expired before send; no retry')
                    _require_pending_source_fresh(channel, request, checked)
                transport.send_once(request)
            if request_deadline is not None and clock() > request_deadline:
                raise TimeoutError('original pending capture expired; no retry')
            time.sleep(.001)
        else:
            raise TimeoutError('finite causal polling budget exhausted')
        source.retire('causal scans completed')
        close_input()
        stopped = (transport.line(5) if _world_service is None else
                   _wait_world_line(transport, clock, _world_service, 5, retired_source=True))
        if stopped is None: raise ValueError('original causal terminal absent')
        write('terminal.raw', stopped)
        terminal = _terminal(stopped, channel._owner.context, scans)
        result = dict(context=channel._owner.context, captures=records,
            original_terminal=terminal, source_profile=_source_profile(),
            source_origin_ns=origin_ns,
            root_feedback_calls=feedback_calls, CPU_completion_created=False,
            movement_authorized=False, formal_acceptance='not_run',
            complete_H12='not_run', compression_verified=False)
        write('HOST_CAUSAL_RESULT.json', _raw(result))
        return result
    except BaseException as primary:
        primary_error = primary
        secondary = []
        for action in (lambda: channel.retire('causal exchange failed') if channel is not None else None,
                       lambda: source.retire('causal exchange failed'), close_input):
            try: action()
            except BaseException as error:
                secondary.append(dict(type=type(error).__name__, message=str(error)[:256]))
        if secondary:
            primary._causal_exchange_secondary_errors = (
                getattr(primary, '_causal_exchange_secondary_errors', ())+tuple(secondary))
        raise
    finally:
        if history is not None:
            failures = []
            for stage, action in (('history_flush', history.flush),
                    ('history_fsync', lambda: os.fsync(history.fileno())),
                    ('history_close', history.close)):
                try: action()
                except BaseException as error:
                    failures.append((error, dict(stage=stage,
                        type=type(error).__name__, message=str(error)[:256])))
            if failures:
                if primary_error is not None:
                    old = getattr(primary_error, '_causal_exchange_secondary_errors', ())
                    primary_error._causal_exchange_secondary_errors = old+tuple(row for _,row in failures)
                else:
                    first = failures[0][0]
                    first._causal_exchange_secondary_errors = tuple(row for _,row in failures[1:])
                    raise first


def exchange_causal(context, host_clock, transport, source, *, scans, out,
                    functional_timing_profile=None, on_candidate=None,
                    _world_service=None):
    """Run inside the original activated Root host; never create/adopt SSH here."""
    binding = clocks._require_binding(host_clock)
    if type(host_clock) is not clocks.QpcHostClock or type(source) is not CausalSourcePump:
        raise ValueError('original QPC and fresh Root candidate source required')
    if not source.prepared or source.state != 'NEW':
        raise ValueError('source geometry must be prepared before original SSH acquisition')
    _require_world_service(_world_service, host_clock, source, causal_mode=True)
    ready = (transport.line(180) if _world_service is None else
             _wait_world_line(transport, binding, _world_service, 180))
    if ready is None: raise ValueError('original causal READY absent')
    def start():
        origin = binding()
        source.start(origin, binding)
        first = source.poll()  # No file work or channel construction before it.
        if _world_service is not None: _world_service.poll()
        channel = channels.LiveFourChannelChannel(context, binding,
            start_tick_ms=0, start_monotonic_ns=origin, max_scans=scans,
            functional_timing_profile=functional_timing_profile)
        channel.accept_ready(ready)
        return channel, origin, first
    return _exchange_causal_core(None, transport, source, clock=binding,
        origin_ns=None, scans=scans, out=out, _start=start, context=context,
        on_candidate=on_candidate, _world_service=_world_service)


__all__ = ['CausalSourcePump', 'exchange_causal', 'select_source_mode', 'SOURCE_PROFILE',
           'select_feedback_mode', 'FEEDBACK_PROFILE']
