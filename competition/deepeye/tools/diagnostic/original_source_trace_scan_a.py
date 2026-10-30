"""Root-private original source to B113/B131 bytes; no board authority."""
import hashlib
import json
import sys
import threading

from ...integration import host_clock, sensor_source
from ...simulation.authority import root_source_book
from ...simulation.authority.live_chain_channels import pack_candidate_quality
from ..run_causal_functional_chain import FunctionalSource
from . import functional50_exchange_a as exchange


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _construct_bytes(payload, payload_bytes, draft, origin, domain, received, evaluated,
                     facts, provenance, clock_metadata=None):
    """Pure encoding seam; production obtains all source values from original custody."""
    _need(type(payload_bytes) is bytes and _raw(payload) == payload_bytes,
          'original source payload bytes changed')
    record = sensor_source.validate_record(payload)
    _need(type(draft) is dict and draft.get('status') == 'complete'
          and draft.get('tick_ms') == record.adc_tick_ms, 'complete original sample required')
    _need(type(origin) is int and 0 <= origin < (1 << 63) and type(domain) is str,
          'original source origin/domain required')
    _need(type(received) is int and type(evaluated) is int and origin <= received <= evaluated < (1 << 63),
          'original receiver/evaluation order required')
    _need(type(facts) is dict and set(facts) == {'work_id','declared_by','scan_id_uint63',
          'view','frame_seq_start','sample_index','binding_receipt_id','lineage'},
          'exact external physical-callsite facts required')
    lineage = facts['lineage']
    _need(type(lineage) is dict and set(lineage) == {'operation_id','request_id','request_hash',
          'tested_commit','build_id_hex128','boot_id','session_id','tag','trigger_id',
          'generation','request_seq','capture_seq'}, 'exact external lineage required')
    start = facts['frame_seq_start']
    _need(type(start) is int and 0 <= start <= 65532, 'four nonwrapping frame numbers required')
    nominal_adc = origin + record.adc_tick_ms * 1_000_000
    _need(nominal_adc <= received and nominal_adc < (1 << 63), 'nominal ADC is future/overflow')
    quality = record.quality
    mapped = pack_candidate_quality(quality)
    times = [None if record.em_tick_ms is None else origin+record.em_tick_ms*1_000_000]*3 + [nominal_adc]
    lanes = []
    for channel, staged in enumerate(mapped):
        valid = bool(staged & 1)
        source_ns = times[channel] if valid else None
        _need(not valid or (type(source_ns) is int and origin <= source_ns <= nominal_adc),
              'invalid nominal source time')
        delta = None if source_ns is None else source_ns-origin
        lane = dict(channel=channel, raw_sample_uint16=record.channel_counts[channel],
            root_quality_uint16=quality,
            mapped_flags=dict(valid=valid, saturated=bool(staged&2), held=bool(staged&4),
                              source_fault=bool(staged&8)), staged_quality_uint4=staged,
            acquisition_qpc_ns=nominal_adc, acquisition_tick_us=(nominal_adc-origin)//1000,
            acquisition_remainder_ns=(nominal_adc-origin)%1000, source_qpc_ns=source_ns,
            source_tick_us=None if delta is None else delta//1000,
            source_remainder_ns=None if delta is None else delta%1000,
            session=lineage['session_id'], index=facts['sample_index'], view=facts['view'],
            frame_seq=start+channel)
        lanes.append(lane)
    source_context = dict(schema='original-source-trace-context-v1', lineage=lineage,
        source_origin_qpc_ns=origin, clock_domain_id=domain, profile_id=record.profile_id,
        profile_status=record.profile_status, profile_note=record.profile_note,
        source_mode=record.source_mode, clock_metadata=clock_metadata)
    timestamp_record = dict(schema='original-source-trace-timing-v1',
        time_basis='nominal_source_grid_not_exact_adc_or_em_acquisition',
        source_origin_qpc_ns=origin, nominal_adc_qpc_ns=nominal_adc,
        nominal_em_qpc_ns=times[0], original_book_draft=draft,
        ledger_receiver_qpc_ns=received, evaluation_qpc_ns=evaluated,
        clock_domain_id=domain)
    quality_record = dict(schema='original-source-trace-quality-v1',
        mapping='candidate_four_channel_quality_v1', quality_uint16=quality,
        channel_counts=list(record.channel_counts), staged_quality_uint4=list(mapped),
        lane_flags=[lane['mapped_flags'] for lane in lanes])
    companions = tuple(_raw(dict(schema='original-source-trace-companion-v1', channel=i,
        payload_utf8_hex=payload_bytes.hex(), book_draft=draft, source_context=source_context,
        timestamp_record=timestamp_record, quality_record=quality_record)) for i in range(4))
    association = dict(profile_id='TRACE-PAYLOAD-1US-PRIVATE-v2',
        binding_receipt_id=facts['binding_receipt_id'], e=0,
        source_context_sha256=_sha(_raw(source_context)),
        timestamp_record_sha256=_sha(_raw(timestamp_record)),
        quality_record_sha256=_sha(_raw(quality_record)), receiver_qpc_ns=received,
        evaluation_now_qpc_ns=evaluated, evaluation_clock_id=domain,
        receiver_clock_id=domain, freshness_limit_ns=100_000_000)
    request = dict(schema='B113_EXTERNAL_ORIGINAL_SCAN_REQUEST_V1',
        task=dict(task_id='DEEPEYE-IMPLEMENTATION-20261014', task_version=1,
                  work_id=facts['work_id'], requirements_sha256=
                  'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'),
        source_provenance={'class':provenance,'declared_by':facts['declared_by'],
            'source_note':'nominal ADC/EM source grid; actual call brackets in full companions; no physical authority',
            'mapping_state':'B_NEUTRAL_AWAITING_A_MAPPING'},
        source_payload=dict(format_label='original-forward-payload-json-v1',
                            bytes=len(payload_bytes),sha256=_sha(payload_bytes)),
        scan=dict(scan_id_uint63=facts['scan_id_uint63'],origin_qpc_ns=origin,
                  acquisition_qpc_ns=nominal_adc,clock_domain_id=domain,lanes=lanes),
        lineage=lineage,association=association,
        companions=[dict(channel=i,format_label='original-source-trace-companion-v1',
                         bytes=len(body),sha256=_sha(body)) for i,body in enumerate(companions)])
    return _raw(request), payload_bytes, companions


def _check_bundle(bundle):
    _need(type(bundle) is exchange._Bundle and sys.modules.get('adapter128') is bundle.adapter
          and sys.modules.get('reducer128') is bundle.reducer, 'original fixed B131 bundle required')
    root = exchange.Path(bundle.adapter.__file__).resolve().parents[5]
    base = root/'competition/deepeye/tools/diagnostic/functional50_adapter128'
    for name, digest in exchange._PINS.items():
        _need(exchange._sha(base/name) == digest, 'B131 source pin changed')
    for name, digest in exchange._DEPS.items():
        _need(exchange._sha(root/name) == digest, 'B113/codec source pin changed')
    _need(exchange.Path(bundle.adapter.__file__).resolve() == (base/'adapter128.py').resolve(),
          'original fixed adapter path required')


class OriginalSourceTraceScan:
    """One original source history and at most one frozen B113/B131 scan."""
    def __init__(self, functional_source, bundle):
        f = functional_source
        _need(type(f) is FunctionalSource and type(f.book) is root_source_book.RootSourceBook
              and type(f.clock) is host_clock.QpcHostClock and f.source.state == 'RUNNING'
              and f.source._clock is f.clock and f.book._clock is f.clock
              and f.source._source_book is f.book and f.book._source is f.source
              and f.book._origin == f.source._origin and f.source._origin is not None
              and f.source._count == 0 and not f.book._samples and not f._retained_samples,
              'fresh started original functional source before first sample required')
        f._check_thread(); f.book._check(); _check_bundle(bundle)
        self._thread = threading.get_ident()
        self._functional, self._book, self._source, self._clock = f, f.book, f.source, f.clock
        self._origin = f.source._origin
        self._domain = f.clock.metadata['domain_id']
        self._bundle = bundle
        self._ledger = sensor_source.SourceLedger(start_tick_ms=0, start_monotonic_ns=self._origin)
        self._admitted = []
        self._failed = self._prepared = False
        self._attempt = self._result = None

    def _check(self):
        _need(threading.get_ident() == self._thread and not self._failed and not self._prepared,
              'one live original producer on its original thread required')
        f = self._functional
        _need(f.book is self._book and f.source is self._source and f.clock is self._clock
              and self._source.state == 'RUNNING' and self._source._source_book is self._book
              and self._source._clock is self._clock and self._source._origin == self._origin
              and self._book._origin == self._origin and self._clock.metadata['domain_id'] == self._domain,
              'original source/book/clock association changed')
        self._book._check()

    def admit(self, payload):
        self._check()
        self._failed = True  # Receiver time and ledger attempts are never replayed.
        f = self._functional
        entry = f._retained_sample(payload)
        index = len(self._admitted)
        _need(index < len(f._retained_samples) and f._retained_samples[index] is entry,
              'all original source records in order required')
        token = entry['token']
        _need(type(token) is root_source_book._Sample and token._book is self._book
              and token._ended is True and index < len(self._book._samples)
              and self._book._samples[index] is token._draft
              and token._draft.get('source_count') == index+1
              and token._draft.get('status') == 'complete', 'original completed token/book required')
        draft_bytes = _raw(token._draft)
        _need(bytes.fromhex(token._draft['canonical_source_hex']) == entry['raw']
              and token._draft['source_sha256'] == _sha(entry['raw']),
              'Book and original returned payload differ')
        received = self._clock()
        _need(received >= token._draft['finish_qpc_ns'], 'receiver precedes completion')
        admission = self._ledger.accept(payload, received_monotonic_ns=received)
        self._admitted.append(dict(entry=entry, token=token, draft=token._draft,
            draft_bytes=draft_bytes, payload_bytes=entry['raw'], received=received,
            admission=admission))
        self._failed = False
        return admission

    def prepare(self, payload, *, facts, build_binding):
        self._check()
        self._prepared = True  # One attempt, including all refused inputs.
        _need(len(self._admitted) == len(self._functional._retained_samples),
              'entire original source history must be admitted first')
        for index, previous in enumerate(self._admitted):
            _need(self._functional._retained_samples[index] is previous['entry']
                  and self._book._samples[index] is previous['draft']
                  and previous['token']._draft is previous['draft']
                  and previous['token']._book is self._book
                  and _raw(previous['draft']) == previous['draft_bytes']
                  and previous['entry']['book'] is self._book
                  and self._source._handoff_bytes(previous['entry']['payload']) == previous['payload_bytes']
                  and previous['entry']['raw'] == previous['payload_bytes'],
                  'previous original source history changed')
        matches = [item for item in self._admitted if item['entry']['payload'] is payload]
        _need(len(matches) == 1, 'original admitted payload object required')
        item = matches[0]
        _need(self._functional._retained_sample(payload) is item['entry']
              and item['token']._draft is item['draft'] and item['token']._book is self._book
              and _raw(item['draft']) == item['draft_bytes']
              and self._source._handoff_bytes(payload) == item['payload_bytes'],
              'original admitted source or Book bytes changed')
        _check_bundle(self._bundle)
        evaluated = self._clock()
        request, source, companions = _construct_bytes(payload, item['payload_bytes'], item['draft'],
            self._origin, self._domain, item['received'], evaluated, facts, 'NEW_ORIGINAL_LIVE_ROOT',
            clock_metadata=dict(self._clock.metadata))
        self._attempt = (request, source, companions)
        result = self._bundle.adapter.prepare_bytes(request, source, companions,
                                                    build_binding=build_binding)
        self._result = result
        _need(result.status == 'TRACE94_PLAN_PREPARED' and result.plan is not None,
              'original B113/B131 refused: '+str(result.reason))
        return result
