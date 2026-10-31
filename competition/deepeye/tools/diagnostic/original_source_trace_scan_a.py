"""Root-private original source to B113/B131 bytes; no board authority."""
import hashlib
import json
import sys
import threading
import time

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
    """One original source history; default one scan, explicit v2 at most two."""
    def __init__(self, functional_source, bundle, *, source_scan_cycle_v2=False, defer_start=False):
        _need(type(source_scan_cycle_v2) is bool, 'strict source cycle selection required')
        _need(type(defer_start) is bool and (not defer_start or source_scan_cycle_v2),
              'deferred start requires explicit source cycle v2')
        f = functional_source
        _need(type(f) is FunctionalSource and type(f.book) is root_source_book.RootSourceBook
              and type(f.clock) is host_clock.QpcHostClock and f.book._clock is f.clock
              and f.source._source_book is f.book and f.book._source is f.source
              and f.source._count == 0 and not f.book._samples and not f._retained_samples,
              'fresh original functional source before first sample required')
        if defer_start:
            _need(f.source.state == 'NEW' and f.source._origin is None and f.source._clock is None
                  and f.book._origin is None and f.book._state == 'NEW' and f.book._active is None
                  and f.source._last_tick is None and not f.source._polling
                  and not f._start_attempted and f._pending is None,
                  'fresh prepared original source before start required')
        else:
            _need(f.source.state == 'RUNNING' and f.source._clock is f.clock
                  and f.book._origin == f.source._origin and f.source._origin is not None,
                  'fresh started original functional source required')
        f._check_thread(); f.book._check(); _check_bundle(bundle)
        self._thread = threading.get_ident()
        self._functional, self._book, self._source, self._clock = f, f.book, f.source, f.clock
        self._origin = f.source._origin
        self._domain = f.clock.metadata['domain_id']
        self._bundle = bundle
        self._defer_start = defer_start
        self._activated = not defer_start
        self._activation_attempted = not defer_start
        self._ledger = (None if defer_start else sensor_source.SourceLedger(
            start_tick_ms=0, start_monotonic_ns=self._origin))
        self._admitted = []
        self._failed = self._prepared = False
        self._attempt = self._result = None
        self._source_scan_cycle_v2 = source_scan_cycle_v2
        self._prepare_count = 0
        self._last_prepared_index = None
        self._last_prepared_tick = None
        self._attempts = []
        self._results = []
        self._preparing = False
        self._prepare_job = None
        self._prepared_work = {}

    def activate_started_source(self):
        """Bind the actual once-started origin without rehashing or starting it."""
        already_attempted = self._activation_attempted
        previously_failed = self._failed
        self._activation_attempted = True
        self._failed = True
        f = self._functional
        _need(not already_attempted and not previously_failed and self._defer_start and not self._activated
              and threading.get_ident() == self._thread and f.book is self._book
              and f.source is self._source and f.clock is self._clock
              and f._start_attempted and self._source.state == 'RUNNING'
              and self._source._source_book is self._book and self._book._source is self._source
              and self._source._clock is self._clock and self._book._clock is self._clock
              and type(self._source._origin) is int and 0 <= self._source._origin < (1 << 63)
              and self._book._origin == self._source._origin and self._book._state == 'RUNNING'
              and self._source._count == 0 and self._source._last_tick is None and not self._source._polling
              and not self._book._samples and self._book._active is None
              and not f._retained_samples and f._pending is None
              and not self._admitted and not self._prepared and self._prepare_count == 0
              and self._ledger is None and self._origin is None,
              'fresh once-started original source and Book required')
        self._origin = self._source._origin
        self._ledger = sensor_source.SourceLedger(start_tick_ms=0, start_monotonic_ns=self._origin)
        self._activated = True
        self._failed = False

    def _check(self):
        available = self._source_scan_cycle_v2 or not self._prepared
        _need(threading.get_ident() == self._thread and not self._failed and self._activated
              and self._ledger is not None and available,
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
        _need(not getattr(self, '_preparing', False), 'original preparation already pending')
        self._check()
        if self._source_scan_cycle_v2 and self._prepare_count >= 2:
            self._failed = True
            raise ValueError('source cycle preparation cap exhausted')
        self._prepared = True  # Never reset; default mode remains strictly one-shot.
        self._prepare_count += 1  # Each attempted preparation is consumed, including refusals.
        if self._source_scan_cycle_v2:
            self._failed = True  # No retry or new admission after a refused/unknown attempt.
        _need(len(self._admitted) == len(self._functional._retained_samples),
              'entire original source history must be admitted first')
        if self._source_scan_cycle_v2:
            _need(len(self._book._samples) == len(self._admitted)
                  and self._source._count == len(self._admitted)
                  and self._book._active is None,
                  'entire original Book history must be admitted first')
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
            if self._source_scan_cycle_v2:
                _need(previous['token']._ended is True
                      and previous['draft'].get('status') == 'complete'
                      and previous['draft'].get('source_count') == index+1,
                      'original completed history token changed')
        matches = [item for item in self._admitted if item['entry']['payload'] is payload]
        _need(len(matches) == 1, 'original admitted payload object required')
        item = matches[0]
        if self._source_scan_cycle_v2:
            index = len(self._admitted)-1
            _need(index >= 0 and self._admitted[index] is item,
                  'latest original source sample required')
            _need(self._last_prepared_index is None or index > self._last_prepared_index,
                  'strictly newer original source slot required')
            _need(self._last_prepared_tick is None or item['admission'].record.adc_tick_ms > self._last_prepared_tick,
                  'strictly newer original source tick required')
        _need(self._functional._retained_sample(payload) is item['entry']
              and item['token']._draft is item['draft'] and item['token']._book is self._book
              and _raw(item['draft']) == item['draft_bytes']
              and self._source._handoff_bytes(payload) == item['payload_bytes'],
              'original admitted source or Book bytes changed')
        _check_bundle(self._bundle)
        evaluated = self._clock()
        if self._source_scan_cycle_v2:
            self._ledger._observe_time(evaluated, 'evaluation_monotonic_ns')
            rec = item['admission'].record
            adc_ns = self._origin + rec.adc_tick_ms*1_000_000
            _need(0 <= evaluated-adc_ns <= sensor_source.TIMEOUT_NS,
                  'nominal ADC expired or future at preparation')
            if rec.em_tick_ms is not None:
                em_ns = self._origin + rec.em_tick_ms*1_000_000
                _need(0 <= evaluated-em_ns <= sensor_source.TIMEOUT_NS,
                      'nominal EM expired or future at preparation')
        request, source, companions = _construct_bytes(payload, item['payload_bytes'], item['draft'],
            self._origin, self._domain, item['received'], evaluated, facts, 'NEW_ORIGINAL_LIVE_ROOT',
            clock_metadata=dict(self._clock.metadata))
        self._attempt = (request, source, companions)
        if self._source_scan_cycle_v2:
            _need(all(request != prior[0] and source != prior[1] for prior in self._attempts),
                  'new original request and source bytes required')
            self._attempts.append(self._attempt)
        result = self._bundle.adapter.prepare_bytes(request, source, companions,
                                                    build_binding=build_binding)
        self._result = result
        _need(result.status == 'TRACE94_PLAN_PREPARED' and result.plan is not None,
              'original B113/B131 refused: '+str(result.reason))
        if self._source_scan_cycle_v2:
            self._last_prepared_index = index
            self._last_prepared_tick = item['admission'].record.adc_tick_ms
            self._results.append(result)
            self._failed = False
        return result

    def _work_pump(self, pump, end):
        from .original_chain_source_pump_a import OriginalChainSourcePump
        if self._clock() >= end:raise TimeoutError('original preparation deadline expired')
        OriginalChainSourcePump.poll_once(pump, pump.session)
        if self._clock() >= end:raise TimeoutError('original preparation deadline expired')

    def _work_prefix_check(self, prefix, pump, end):
        """Check current original content on owner, with fixed-pump checkpoints."""
        f=self._functional
        for index, saved in enumerate(prefix):
            self._work_pump(pump,end)
            item,entry,token,draft,payload,draft_bytes,payload_bytes,admission,received=saved
            _need(index<len(self._admitted) and self._admitted[index] is item
                  and index<len(f._retained_samples) and f._retained_samples[index] is entry
                  and index<len(self._book._samples) and self._book._samples[index] is draft
                  and item['entry'] is entry and item['token'] is token and item['draft'] is draft
                  and item['draft_bytes']==draft_bytes and item['payload_bytes']==payload_bytes
                  and item['admission'] is admission and item['received']==received and type(received) is int and entry['book'] is self._book
                  and entry['payload'] is payload and entry['raw']==payload_bytes
                  and type(token) is root_source_book._Sample and token._book is self._book and token._draft is draft and token._ended is True
                  and draft.get('status')=='complete' and draft.get('source_count')==index+1,
                  'original current prefix content or identity changed')
            _need(_raw(draft)==draft_bytes,'original current draft bytes changed')
            self._work_pump(pump,end)
            _need(self._source._handoff_bytes(payload)==payload_bytes,'original current payload bytes changed')
            self._work_pump(pump,end)
        _need(len(self._admitted)==len(f._retained_samples)==len(self._book._samples)==self._source._count
              and self._book._active is None,'original complete ordered history required')

    def _work_fresh(self, adc_tick, em_tick, now):
        adc=self._origin+adc_tick*1_000_000
        _need(0<=now-adc<=sensor_source.TIMEOUT_NS,'nominal ADC expired or future')
        if em_tick is not None:
            em=self._origin+em_tick*1_000_000
            _need(0<=now-em<=sensor_source.TIMEOUT_NS,'nominal EM expired or future')

    def _work_original_pump(self, pump):
        from .original_chain_source_pump_a import OriginalChainSourcePump
        from . import functional50_ssh_a as ssh
        _need(type(pump) is OriginalChainSourcePump and type(pump.session) is ssh.Session
              and pump.scanner is self and pump.source is self._functional and pump.clock is self._clock
              and pump.enabled and not pump.failed and pump.session._clock is self._clock
              and pump.session._thread==self._thread and pump.session._protocol=='functional50_chain_v2'
              and getattr(pump.session,'_source_pump',None) is pump
              and ssh._SESSION_PUMPS.get(pump.session) is pump,'same original enabled v2 pump required')
        pump.session._check()

    def prepare_with_pump(self, payload, *, facts, build_binding, pump, timeout_ns):
        """Explicit v2 one-use fixed-worker preparation while the owner pumps."""
        from . import original_chain_prepare_work_a as work
        self._check();self._work_original_pump(pump)
        _need(self._source_scan_cycle_v2 is True and not getattr(self,'_preparing',False), 'fresh v2 preparation required')
        _need(type(timeout_ns) is int and 0<timeout_ns<=60_000_000_000,'bounded original QPC deadline required')
        end=self._clock()+timeout_ns
        if self._prepare_count>=2:
            self._failed=True;raise ValueError('source cycle preparation cap exhausted')
        self._prepared=True;self._prepare_count+=1;self._preparing=True
        self._prepare_job=None
        try:
            _need(type(facts) is dict and type(build_binding) is dict,'exact root facts and binding required')
            _need(len(self._admitted)==len(self._functional._retained_samples)==len(self._book._samples)==self._source._count
                  and self._book._active is None and 1<=len(self._admitted)<=1001,'bounded complete original history required')
            index=len(self._admitted)-1;item=self._admitted[index]
            _need(item['entry']['payload'] is payload,'latest original sample at reservation required')
            rec=item['admission'].record;adc_tick=rec.adc_tick_ms;em_tick=rec.em_tick_ms
            _need((self._last_prepared_index is None or index>self._last_prepared_index)
                  and (self._last_prepared_tick is None or adc_tick>self._last_prepared_tick),'strictly newer original sample required')
            n=index+1;prefix=[]
            for i in range(n):
                self._work_pump(pump,end)
                previous=self._admitted[i];entry=previous['entry']
                prefix.append((previous,entry,previous['token'],previous['draft'],entry['payload'],previous['draft_bytes'],previous['payload_bytes'],previous['admission'],previous['received']))
                self._work_pump(pump,end)
            prefix=tuple(prefix)
            self._work_prefix_check(prefix,pump,end)
            self._work_pump(pump,end)
            _need(self._functional._retained_sample(payload) is item['entry'],'original selected payload changed')
            self._work_pump(pump,end)
            evaluated=self._clock();_need(evaluated<end,'preparation deadline expired')
            self._ledger._observe_time(evaluated,'evaluation_monotonic_ns');self._work_fresh(adc_tick,em_tick,evaluated)
            self._work_pump(pump,end);facts_bytes=_raw(facts)
            self._work_pump(pump,end);binding_bytes=_raw(build_binding)
            self._work_pump(pump,end);metadata_bytes=_raw(dict(self._clock.metadata));self._work_pump(pump,end)
            _need(len(facts_bytes)<=8192 and len(binding_bytes)<=8192 and len(metadata_bytes)<=8192,'bounded detached context required')
            job=work._PrepareJob(work._KEY,self._bundle,item['payload_bytes'],item['draft_bytes'],facts_bytes,binding_bytes,metadata_bytes,self._origin,self._domain,item['received'],evaluated)
            self._prepare_job=job;job.start(work._KEY)
            while not job.done.is_set() or job.thread.is_alive():
                if self._clock()>=end:raise TimeoutError('original preparation deadline expired')
                self._work_pump(pump,end)
                remaining=end-self._clock()
                if remaining<=0:raise TimeoutError('original preparation deadline expired')
                if not job.done.is_set() or job.thread.is_alive():time.sleep(min(remaining,1_000_000)/1_000_000_000)
            self._attempt=job.attempt
            if job.error is not None:raise job.error
            _need(self._bundle is job._bundle and self._bundle.adapter is job._adapter
                  and self._bundle.reducer is job._reducer,'original B131 bundle changed')
            _need(type(job.attempt) is tuple and len(job.attempt)==3,'actual original attempt required')
            request,source,companions=job.attempt
            _need(all(request!=prior[0] and source!=prior[1] for prior in self._attempts),'new original request and source required')
            self._attempts.append(job.attempt);result=job.result;self._result=result
            _need(type(result) is self._bundle.adapter.Preparation and result.status=='TRACE94_PLAN_PREPARED' and result.plan is not None,'original B113/B131 refused')
            _need(type(request) is bytes and type(source) is bytes and type(companions) is tuple and len(companions)==4
                  and all(type(value) is bytes for value in companions) and result.original.request==request
                  and result.original.source==source and result.original.companions==companions,'original prepared bytes changed')
            self._work_prefix_check(prefix,pump,end)
            self._work_pump(pump,end)
            _need(self._functional._retained_sample(payload) is item['entry'],'original selected payload changed during work')
            self._work_pump(pump,end)
            _need(item['admission'].record is rec and rec.adc_tick_ms==adc_tick and rec.em_tick_ms==em_tick,'original selected timestamps changed')
            self._work_pump(pump,end);_need(_raw(facts)==facts_bytes,'root facts changed')
            self._work_pump(pump,end);_need(_raw(build_binding)==binding_bytes,'root binding changed')
            self._work_pump(pump,end)
            current=self._clock();_need(current<end,'preparation deadline expired');self._ledger._observe_time(current,'evaluation_monotonic_ns');self._work_fresh(adc_tick,em_tick,current)
            self._last_prepared_index=index;self._last_prepared_tick=adc_tick;self._results.append(result)
            if not hasattr(self,'_prepared_work'):self._prepared_work={}
            self._prepared_work[id(result)]=dict(result=result,original=result.original,attempt=job.attempt,job=job,prefix=prefix,item=item,pump=pump,end=end,record=rec,adc_tick=adc_tick,em_tick=em_tick,used=False)
            self._preparing=False
            return result
        except BaseException:
            if self._prepare_job is not None and self._prepare_job.attempt is not None:self._attempt=self._prepare_job.attempt
            self._failed=True;raise

    def _prepared_work_deadline(self, prepared):
        self._check()
        record=getattr(self,'_prepared_work',{}).get(id(prepared))
        _need(record is not None and record['result'] is prepared and type(prepared) is self._bundle.adapter.Preparation,'original prepared work required')
        job=record['job'];_need(self._bundle is job._bundle and self._bundle.adapter is job._adapter and self._bundle.reducer is job._reducer,'original B131 bundle changed')
        self._work_original_pump(record['pump'])
        return record['end']

    def _check_prepared_dispatch(self, prepared):
        self._check()
        record=getattr(self,'_prepared_work',{}).get(id(prepared))
        _need(record is not None and record['result'] is prepared and type(prepared) is self._bundle.adapter.Preparation and not record['used'],'unused original prepared work required')
        record['used']=True
        try:
            pump=record['pump'];self._work_original_pump(pump);self._work_prefix_check(record['prefix'],pump,record['end'])
            job=record['job'];_need(self._bundle is job._bundle and self._bundle.adapter is job._adapter and self._bundle.reducer is job._reducer,'original B131 bundle changed')
            self._work_pump(pump,record['end'])
            _need(self._functional._retained_sample(record['item']['entry']['payload']) is record['item']['entry'],'original selected payload changed before dispatch')
            self._work_pump(pump,record['end'])
            request,source,companions=record['attempt']
            _need(prepared.original is record['original'] and prepared.original.request==request
                  and prepared.original.source==source and prepared.original.companions==companions
                  and record['job'].result is prepared,'original prepared work changed')
            rec=record['item']['admission'].record
            _need(rec is record['record'] and rec.adc_tick_ms==record['adc_tick'] and rec.em_tick_ms==record['em_tick'],'original selected timestamps changed')
            now=self._clock();_need(now<record['end'],'original preparation deadline expired')
            self._ledger._observe_time(now,'evaluation_monotonic_ns');self._work_fresh(record['adc_tick'],record['em_tick'],now)
            return record['end']
        except BaseException:self._failed=True;raise
