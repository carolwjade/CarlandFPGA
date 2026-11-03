"""Opt-in, original-owner G05 CSR admission. No UART BOOT/STATE is invented.

The public configuration and parsed facts below are not credentials. Production
selection claims a genuine OriginalG05OperationBinding, and every admitted event
is consumed from its original producer. Raw four-lane E4 captures remain E4.
"""
from dataclasses import dataclass, field
import copy
import hashlib
import json
import re
import threading

from ...integration import host_envelope

_KEY = object()
_SELECTED = {}  # Keep failed/consumed selection identities, never evict or retry.
_OBSERVATIONS = {}
_COMMANDS = {}
_MAX_NS = (1 << 63) - 1


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _uint(value, low=0, high=_MAX_NS):
    _need(type(value) is int and low <= value <= high, 'strict bounded integer required')
    return value


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _json(raw, limit=1048576):
    _need(type(raw) is bytes and 0 < len(raw) <= limit, 'bounded original bytes required')
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw.decode('utf8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


@dataclass(frozen=True)
class G05CsrPolicy:
    """Explicit main-selected demo budgets; no endpoint or authority evidence."""
    max_source_age_ns: int
    health_timeout_ns: int
    usb_upper_ns: int
    packing_upper_ns: int
    demo_ai_profile: object = None

    def check(self):
        _need(type(self) is G05CsrPolicy, 'exact G05 CSR policy required')
        from .demo30h_ai_em3_profile_v2 import DemoEM3AIProfile,NAV_ENTRY_C0_V1,NAV_ENTRY_C0_12S_V3
        entry_demo=(type(self.demo_ai_profile) is DemoEM3AIProfile and self.demo_ai_profile.navigation_profile==NAV_ENTRY_C0_V1)
        entry12=(type(self.demo_ai_profile) is DemoEM3AIProfile and self.demo_ai_profile.navigation_profile is NAV_ENTRY_C0_12S_V3)
        age_cap=12_000_000_000 if entry12 else 8_000_000_000 if entry_demo else 5_000_000_000
        _uint(self.max_source_age_ns, 1, age_cap)
        _uint(self.health_timeout_ns, 1, age_cap)
        _uint(self.usb_upper_ns, 0, 5_000_000_000)
        _uint(self.packing_upper_ns, 0, 5_000_000_000)
        if self.demo_ai_profile is not None:
            from .demo30h_ai_em3_profile_v2 import DemoEM3AIProfile, selected_profile as selected_em3_profile
            if type(self.demo_ai_profile) is DemoEM3AIProfile:
                selected = selected_em3_profile(self.max_source_age_ns,navigation_profile=self.demo_ai_profile.navigation_profile)
                _need(self.demo_ai_profile.projection is selected.projection and type(self.demo_ai_profile.verifier) is type(selected.verifier) and self.demo_ai_profile.verifier==selected.verifier, 'fixed EM3 projection/verifier identities required')
            else:
                from .demo30h_ai_profile_v1 import selected_profile
                selected = selected_profile(self.max_source_age_ns)
            _need(self.demo_ai_profile == selected, 'fixed explicit demo AI profile required')


def select_original_g05(config, binding):
    """Retain the exact pre-source binding before the fixed factory is called.

    This is a trusted-main callsite, not IPC, JSON restoration or a provider hook.
    It performs no I/O and creates no BOOT/observation/command record.
    """
    from .actor_composition import AuthorityConfig
    from ...tools.diagnostic.original_g05_operation_binding_a import OriginalG05OperationBinding
    _need(type(config) is AuthorityConfig and type(binding) is OriginalG05OperationBinding,
          'original configuration and G05 operation binding required')
    _need(type(config.g05_csr_v1) is G05CsrPolicy, 'explicit default-off G05 profile required')
    config.g05_csr_v1.check()
    from .g05_board_output_v1 import check_mode_selection
    check_mode_selection(config.g05_board_output_v1,config.pc_direct_window_v2,config.g05_csr_v1)
    _need(config.g05_csr_v1.demo_ai_profile is not None, 'fixed new G05 demo AI profile required')
    binding._check()
    if config.g05_csr_v1.max_source_age_ns>100_000_000:
        from ...tools.diagnostic.demo30h_age_budget_a import _verify
        scanner=binding.producer._scanner
        _need(scanner is not None and _verify(scanner._demo_age_budget,scanner)==config.g05_csr_v1.max_source_age_ns,
              'same original operation-bound scanner demo age selection required')
    _need(binding.config is config and binding.source.source.state == 'NEW'
          and binding.source.composition is None, 'same untouched pre-source configuration required')
    ident = id(config)
    _need(ident not in _SELECTED and not any(row[1] is binding for row in _SELECTED.values()),
          'original G05 profile selection already consumed')
    _SELECTED[ident] = [config, binding, False, None]


def _create_channels(config, capability, host_clock):
    selected = _SELECTED.get(id(config))
    _need(selected is not None and selected[0] is config and not selected[2],
          'original selected G05 binding required')
    selected[2] = True  # A failed factory attempt is consumed as well.
    binding = selected[1]
    refs = binding.claim_for_factory(config, capability, binding.chain)
    _need(refs.clock is host_clock and capability is refs.link, 'same original factory clock/link required')
    result = G05CsrChannels(_KEY, config, binding, refs)
    selected[3] = result
    return result


def channels_for(config):
    """Return only the already-created original channel; never activates it."""
    row = _SELECTED.get(id(config))
    _need(row is not None and row[0] is config and type(row[3]) is G05CsrChannels,
          'original factory has not installed G05 channels')
    return row[3]


def validate_csr_facts(facts, *, identity_words, operation_id, previous=(),demo_cycle_profile=None):
    """Pure byte-level CSR consistency check; successful parsing grants nothing."""
    from ...tools.diagnostic import functional50_chain_v2_client_a as client
    from ...tools.diagnostic import functional50_g05_a as g05
    g05._identity(identity_words)
    _need(type(facts) is dict and facts.get('kind') in ('init', 'status', 'apply'),
          'live G05 CSR phase required')
    kind = facts['kind']
    deadline = client._facts(facts, kind, operation_id, identity_words, None,demo_cycle_profile)
    g05._status_check(facts['status'], facts['fault'], 'bound')
    rows = facts['receipts']
    _need(tuple(rows[:len(previous)]) == tuple(previous), 'cumulative original CSR prefix changed')
    parsed, last, pid = [], None, None
    for index, row in enumerate(rows, 1):
        a = _json(bytes.fromhex(row['started_raw_hex']), 4096)
        z = _json(bytes.fromhex(row['returned_raw_hex']), 4096)
        _need(set(a) == {'request_id','io','kind','offset','value','pid','monotonic_ns'}
              and set(z) == {'request_id','io','kind','value','monotonic_ns'},
              'original CSR raw schema mismatch')
        _need(a['io'] == z['io'] == index and a['request_id'] == z['request_id']
              and a['kind'] == z['kind'] and a['kind'] in ('read','write'),
              'original CSR raw identity/order mismatch')
        _uint(a['pid'], 1); _uint(a['offset'], 0, 0x37c)
        if pid is None:pid=a['pid']
        _need(a['pid']==pid, 'CSR evidence mixed board processes')
        _need(a['offset'] % 4 == 0, 'unaligned CSR receipt')
        lo, hi = _uint(a['monotonic_ns']), _uint(z['monotonic_ns'])
        _need(lo <= hi and (last is None or last <= lo), 'CSR raw time reversed')
        last = hi
        if a['kind'] == 'read':
            _need(a['value'] is None and a['offset'] in g05._READ, 'unselected read receipt')
            _uint(z['value'], 0, 0xffffffff)
        else:
            _need(a['offset']==12 or a['offset'] in range(0x100,0x134,4)
                  or a['offset'] in range(0x200,0x21c,4), 'unselected write receipt')
            _uint(a['value'], 0, 0xffffffff)
            _need(z['value'] is None, 'write receipt has invented readback')
        parsed.append((a, z))
    first, end = facts['phase_io_first'], facts['phase_io_last']
    _need(first is not None and end == len(rows) and first > len(previous), 'new complete CSR phase required')
    phase = parsed[first-1:end]
    _need(all(deadline[0]<=a['monotonic_ns']<=z['monotonic_ns']<deadline[1]
              for a,z in phase), 'actual CSR phase outside its fixed board deadline')
    reads = [(a['offset'], z['value']) for a,z in phase if a['kind'] == 'read']
    expected = [(0x100+4*i, word) for i,word in enumerate(identity_words)]
    _need(any(reads[i:i+13] == expected for i in range(max(0, len(reads)-12))),
          'actual full13 identity readback missing')
    _need(reads[-2:] == [(8, facts['status']), (16, facts['fault'])] or kind == 'apply',
          'actual final status/fault readback mismatch')
    if kind == 'init':
        factory_reads=[(a['offset'],z['value']) for a,z in parsed[:first-1] if a['kind']=='read']
        _need(factory_reads==[(0,0x47303550),(4,2),(8,0),(16,0)],
              'actual same-load G05P/layout2/unbound factory reads missing')
        writes = [(a['offset'],a['value']) for a,z in phase if a['kind']=='write']
        _need(writes[:13] == expected and (12,1) in writes[13:], 'actual identity stage/BEGIN missing')
    if kind == 'apply':
        capture=facts['capture']; words=capture['words32']
        snapshots=[(a['offset'],z['value']) for a,z in phase
                   if a['kind']=='read' and 0x300<=a['offset']<=0x37c]
        expected_snapshot=[(0x300+4*i,word) for i,word in enumerate(words)]
        held=capture.get('capture_kind')=='g05_held_bank_v2'
        if held:
            expected_snapshot=[(0x300,capture['held_before_seq'])]+expected_snapshot+[(0x300,capture['held_after_seq'])]
        _need(snapshots==expected_snapshot,
              'original complete32-word snapshot missing or torn')
        seqs=[z['value'] for a,z in phase if a['kind']=='read' and a['offset']==0x1c]
        _need(len(seqs)==2 and ((seqs==[capture['latest_before_seq'],capture['latest_after_seq']]
              and 0<words[0]==capture['held_before_seq']==capture['held_after_seq']==capture['result_seq']<=seqs[0]<=seqs[1])
              if held else seqs[0]==seqs[1]==capture['result_seq']==words[0])
              and words[30]==identity_words[12] and words[31]==0x47303550,
              'actual latched snapshot identity mismatch')
    return dict(deadline_board_ns=deadline, receipts=tuple(copy.deepcopy(rows)),
                kind=kind, status=facts['status'], fault=facts['fault'])


def validate_raw4_observation(raw, *, context, now_ns):
    """New host-only shape, with no fabricated public wire TELEM/EVENT frame."""
    doc = _json(raw, 16384)
    _need(type(doc) is dict and set(doc) == {'schema_version','kind','context','observed_seq',
          'adc_interval_ns','native_em_interval_ns','receipt_interval_ns','capture_sha256',
          'quality','channel_counts','wire_format','wire_hex','target100ms_met'}, 'raw4 shape')
    _need(type(doc['schema_version']) is int and doc['schema_version'] == 1 and doc['kind'] == 'g05_raw4_observation_v1'
          and doc['context'] == context and doc['wire_format'] == 'ABI3_E4_PAYLOAD_REV2',
          'explicit raw4 namespace/format required')
    _uint(doc['observed_seq'], 1, 65535); _uint(doc['quality'], 0, 8191)
    _need(type(doc['channel_counts']) is list and len(doc['channel_counts']) == 4,
          'four returned channel counts required')
    for i, value in enumerate(doc['channel_counts']):
        _need((value is not None) == bool(doc['quality'] & (1 << i)), 'returned validity mismatch')
        if value is not None: _uint(value, 0, 4095)
    for name in ('adc_interval_ns','native_em_interval_ns','receipt_interval_ns'):
        span = doc[name]
        if span is None:
            _need(name == 'native_em_interval_ns', 'missing ADC/receipt interval')
            continue
        _need(type(span) is dict and set(span) == {'lower_ns','upper_ns'}, 'explicit QPC interval required')
        _need(_uint(span['lower_ns']) <= _uint(span['upper_ns']) <= _uint(now_ns), 'future/reversed interval')
    _need(type(doc['capture_sha256']) is str and re.fullmatch('[0-9a-f]{64}',doc['capture_sha256']) is not None,
          'original capture digest required')
    _need(type(doc['wire_hex']) is str and 0 < len(doc['wire_hex']) <= 504
          and len(doc['wire_hex'])%2==0 and re.fullmatch('[0-9a-f]+',doc['wire_hex']) is not None,
          'bounded complete four-frame wire required')
    bytes.fromhex(doc['wire_hex'])
    _need(type(doc['target100ms_met']) is bool, 'actual quality flag required')
    return doc


class _ObservationEvent:
    __slots__ = ()
    def __new__(cls,key):
        _need(key is _KEY, 'original validated G05 capture required')
        return super().__new__(cls)
    def __reduce__(self): raise TypeError('original observation is not serializable')


class _CommandEvent(_ObservationEvent):
    pass


@dataclass(eq=False)
class _Mapping:
    channels: object
    event: object
    facts: dict
    refs: dict
    candidate: dict
    raw: bytes
    sample_lower_ns: int
    capture_ref: object
    current_read: object = None
    registry_ref: object = None
    registry_hold: object = None
    retained_bytes: bytes = b''
    used: bool = False
    def __reduce__(self): raise TypeError('original mapping is not serializable')


def _fresh_action_previous(previous,current,old,*,profile,source_origin):
    """Decision only, after original mapping/proof verification by the caller.

    JSON names, GPIO capture sequence and numerical counts alone grant nothing.
    Same sample/held EM always retains the old action's minimum deadline.
    """
    from ...tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
    if previous is None or not demo.is_navigation(profile):return previous
    if type(current) is not _Mapping or type(old) is not _Mapping or current.channels is not old.channels:return previous
    try:
        n,o=current.refs,old.refs;nt,ot=n['token'],o['token'];nd,od=n['draft'],o['draft']
        ne=nd['held_em_association']['original_em'];oe=od['held_em_association']['original_em']
        numbers=(nd['source_count'],od['source_count'],nd['tick_ms'],od['tick_ms'],
                 ne['tick_ms'],oe['tick_ms'],ne['source_count'],oe['source_count'],
                 n['phase_receipt'].phase_index,o['phase_receipt'].phase_index,source_origin)
        if not all(type(x) is int and x>=0 for x in numbers):return previous
        fresh=(nt is not ot and nd is not od and ne is not oe
            and nt._draft is nd and ot._draft is od and nt._ended is True and ot._ended is True
            and nd['status']==od['status']=='complete'
            and ne['kind']==oe['kind']=='original_scoped_em_call_v1'
            and ne['source_origin_qpc_ns']==oe['source_origin_qpc_ns']==source_origin
            and nd['held_em_association']['held'] is False
            and nd['source_count']>od['source_count'] and ne['source_count']==nd['source_count']
            and ne['tick_ms']==nd['tick_ms']>oe['tick_ms']
            and current.candidate['source_time']['adc_tick_ms']==current.candidate['source_time']['em_tick_ms']==ne['tick_ms']
            and current.candidate['quality']&7==7
            and n['phase_receipt'].phase_index>o['phase_receipt'].phase_index
            and current.sample_lower_ns>old.sample_lower_ns)
        return None if fresh else previous
    except (KeyError,AttributeError,TypeError):return previous


class G05CsrChannels:
    def __init__(self,key,config,binding,refs):
        _need(key is _KEY, 'fixed original factory required')
        self.config, self.binding, self.refs = config,binding,refs
        self.policy = config.g05_csr_v1; self.policy.check()
        self.thread = threading.get_ident(); self.owner = None; self.boot = None
        self.retired = False; self._boot_attempted = False
        self._csr_receipts = (); self._health_deadline = None; self._global_deadline = None
        self._last_now = refs.clock(); self._events = []; self._mappings = []
        self._admissions = []; self._command_seq = 0; self._command_pending = None
        self._observation_events = set()
        self.command_quality_reports = []
        self._nav_new_actions = []  # Strong original refs; no progress/clock reset.
        self._source_attached = False
        self._board_pending = None
        self._board_outputs = []  # Strong original APPLY -> command associations.
        self._board_last_sequence = self._board_last_result = 0

    def _binding_checkpoint(self):
        """Validate real channel custody without entering an excluded source.

        Original BOOT/COMMAND reserve their transition before channel admission;
        original STEP additionally owns a retained pre/post-CAS commit slot. A
        source/ProjectionSession check is deliberately forbidden in these states.
        This branch verifies those exact original objects; it never polls source.
        """
        from ._actor_source_custody import _Transition
        from . import _world_loop as world
        from ...tools.diagnostic.original_g05_operation_binding_a import _canonical
        link=self.refs.link; book=self.refs.book; custody=book._actor_custody
        transition=custody.pending
        if transition is None:
            self.binding._check()
            return
        owner=self.owner; producer=self.refs.producer
        _need(type(transition) is _Transition and transition.custody is custody
              and transition.composition is owner and not transition.closed
              and transition.kind in ('BOOT','COMMAND','STEP') and owner is not None
              and owner._busy and not owner._retired and not owner._foreign.is_set()
              and owner._config is self.config and owner._host_clock is self.refs.clock
              and owner._thread==self.thread and self.refs.source.composition is owner
              and owner._world_action_link is link and link.composition is owner
              and link.claimed and book._root is transition.before,
              'exact pending original actor transition required')
        if transition.kind=='STEP':
            slot=link.slot
            _need(type(slot) is world._Commit and slot.book_transition is transition
                  and any(slot is x for x in link.owner._commits) and slot.binding is link.binding
                  and slot.original_witness.link is link and slot.original_witness.composition is owner
                  and slot.pre_root is transition.before and not slot.closed and slot.uncertainty is None,
                  'exact original STEP commit custody required')
            if slot.committed:
                _need(slot.receipt is not None and slot.post_root is link.executor._root,
                      'actual original committed Root required')
                link._registered(_pending_slot=slot)
            else:
                _need(owner._runtime._stepping and link.executor._root is transition.before
                      and link.executor._original_world_witness is slot.original_witness,
                      'exact original pre-CAS final fence required')
                link._registered()
        else:
            link._registered()
        producer._binding_check()
        _need(not producer._failed and not producer._closed and not self.binding._failed
              and self.binding.config is self.config and self.binding.link is link
              and self.binding.book is book and self.binding.world is self.refs.world
              and self.binding.projection is self.refs.projection
              and self.binding.source is self.refs.source and self.binding.clock is self.refs.clock
              and _canonical(self.binding._legacy)==self.binding._legacy_raw
              and _canonical(self.binding._c42)==self.binding._c42_raw,
              'original pending channel operation/context changed')
        projection=self.refs.projection; stored=projection._producer
        _need(projection._owner is link.owner and projection._link is link
              and projection._book is book and stored._owner is link.owner
              and stored._link is link and stored._book is book and not stored._failed,
              'original pending projection association changed')
        if self._source_attached:
            actual=stored._config
            _need(actual is self.binding._stored_config and actual[0] is self.binding._source_ref
                  and actual[1] is self.binding._stored_fields
                  and _canonical(actual[1])==self.binding._config_raw,
                  'original pending source configuration changed')

    def _attach_composition(self, owner):
        from .actor_composition import ActorComposition
        _need(type(owner) is ActorComposition and self.owner is None and owner._channels is self
              and owner._config is self.config and owner._world_action_link is self.refs.link,
              'same original composition factory required')
        self.owner = owner

    def checkpoint(self):
        _need(not self.retired and threading.get_ident() == self.thread, 'original live CSR owner required')
        self._binding_checkpoint(); self.refs.session._check()
        now = self.refs.clock(); _uint(now)
        _need(now >= self._last_now, 'original QPC regressed'); self._last_now = now
        if self.boot is not None:
            _need(now < self._global_deadline and now < self._health_deadline,
                  'actual CSR session/health deadline expired')
        return now

    def _consume(self,event):
        from ...tools.diagnostic.original_chain_receipt_producer_a import consume_original_receipt
        self.checkpoint()
        facts,refs = consume_original_receipt(event)
        _need(refs['world'] is self.refs.world and refs['functional_source'] is self.refs.source
              and refs['chain'] is self.refs.chain and refs['session'] is self.refs.session
              and refs['clock'] is self.refs.clock and refs['book'] is self.refs.book,
              'original event owner/world/clock changed')
        _need(len(self._events) < 1050, 'finite original CSR event cap exhausted')
        self._events.append((event,facts,refs))
        return facts,refs

    def _cycle_profile(self):
        """Use only the bound original chain/source/book/invocation selection."""
        from ...tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
        selected=demo.validate_profile(self.refs.chain.sequence.demo_cycle_profile)
        navigation=selected if demo.is_navigation(selected) else None
        source=self.refs.source.source;book=self.refs.book
        _need(self.refs.source.book is book and book._source is source
              and source._source_book is book
              and getattr(source,'_navigation_profile',None) is navigation
              and getattr(book,'_navigation_profile',None) is navigation
              and getattr(getattr(self.config,'owned_invocation_v1',None),'navigation_profile',None) is navigation,
              'same original source/book/invocation cycle profile required')
        return selected

    def _health(self,facts,refs):
        from ...tools.diagnostic.functional50_chain_v2_client_a import OriginalPhaseReceipt
        phase=refs['phase_receipt']
        _need(type(phase) is OriginalPhaseReceipt and phase.owner is self.refs.chain
              and phase.response_raw == facts['raw_response'] and phase.clock is self.refs.clock
              and phase.lower_qpc_ns == facts['lower_qpc_ns'] and phase.upper_qpc_ns == facts['upper_qpc_ns']
              and phase.status == 'COMPLETE' and phase.unknown is False, 'actual complete CSR phase required')
        parsed=validate_csr_facts(facts['response']['result'],identity_words=self.refs.chain.identity,
                                  operation_id=self.refs.world.operation_id,previous=self._csr_receipts,
                                  demo_cycle_profile=self._cycle_profile())
        self._csr_receipts=parsed['receipts']
        duration=parsed['deadline_board_ns'][1]-parsed['deadline_board_ns'][0]
        if self._global_deadline is None:
            _need(phase.kind=='init' and phase is self.refs.init_receipt, 'actual init anchors deadline')
            # Host lower + board duration is conservative; clocks are not equated.
            self._global_deadline=_uint(phase.lower_qpc_ns+duration)
        self._health_deadline=min(self._global_deadline,
                                  _uint(phase.lower_qpc_ns+self.policy.health_timeout_ns))
        _need(self.refs.clock()<self._health_deadline, 'actual CSR health already stale')

    def verify_boot(self,event,*,run_id,instance_id):
        from .pc_direct_runtime import BootBinding
        _need(not self._boot_attempted and self.owner is not None, 'single original CSR init binding required')
        self._boot_attempted=True
        matches=[row for row in self.refs.producer._history if row[0] is event]
        _need(len(matches)==1 and matches[0][2].get('phase_receipt') is self.refs.init_receipt,
              'actual original init event required')
        facts,refs=self._consume(event)
        _need(facts['kind']=='init' and run_id==self.config.actor_policy.run_id
              and instance_id==self.owner._actor.instance_id, 'actual CSR init/actor binding required')
        self._health(facts,refs)
        self.boot=BootBinding(run_id,1,_raw(self.refs.legacy_context),instance_id)
        return self.boot  # Local G05_CSR_INIT binding, never UART BOOT_ACK.

    def mailbox_activation_for_boot(self,boot):
        from .candidate_owner import _MailboxActivation
        _need(boot is self.boot, 'original CSR binding required'); self.checkpoint()
        return _MailboxActivation(boot,self,self.refs.clock,self.refs.init_receipt.lower_qpc_ns,
                                  self.policy.usb_upper_ns,self.policy.packing_upper_ns)

    def make_health_guard(self,boot,*,now_ns):
        _need(boot is self.boot, 'original CSR binding required')
        return _CsrHealthGuard(_KEY,self,now_ns)

    def attach_started_source(self):
        """One actual started-origin/config attachment; no old counter invention."""
        self.checkpoint(); s=self.refs.source
        _need(self.boot is not None and not self._source_attached and s.source.state=='RUNNING',
              'original source must have actually started')
        fields=dict(context=dict(self.refs.c42_context),generation=self.boot.generation,
                    source_start_monotonic_ns=s.source._origin,source_start_tick_ms=0,
                    profile='G05_CSR_RAW4_V1',legacy_context=dict(self.refs.legacy_context))
        s.observe_config(self.binding,fields)
        self.binding.attach_source_config(self.binding); self._source_attached=True

    def attach_latest_transition(self):
        """Call after BOOT/COMMAND/STEP returns, before the next source poll."""
        self.checkpoint(); s=self.refs.source; custody=self.refs.book._actor_custody
        _need(custody.pending is None and custody.transitions, 'actual finished original transition required')
        transition=custody.transitions[-1]
        if s._last_transition is transition: return
        slot=self.refs.link.slot if transition.kind=='STEP' else None
        s.observe_finished_transition(transition,successor_root=self.refs.book._root,slot=slot,fields={})

    def accept_source_event(self,event):
        facts,refs=self._consume(event)
        _need(facts['kind']=='source_admission' and self._source_attached,
              'actual ordered source admission required')
        item=refs['admitted']; token=refs['token']
        _need(any(item is x for x in self.refs.producer._scanner._admitted)
              and item['token'] is token and token._book is self.refs.book
              and token._draft is refs['draft'] and token._ended is True
              and any(token._draft is x for x in self.refs.book._samples), 'original completed source sample required')
        _need(item['payload_bytes']==facts['payload_bytes'], 'original source admission bytes changed')
        self._admissions.append((event,facts,refs))
        return dict(kind='source_admission', sequence=facts['sequence'], authority='not_evaluated')

    def verify_board(self,event,boot):
        # Explicit typed health, not a synthetic board_response or STATE8.
        from .pc_direct_runtime import VerifiedG05Health
        _need(boot is self.boot, 'original CSR binding required')
        facts,refs=self._consume(event)
        _need(facts['kind'] in ('status','apply'), 'actual CSR health phase required')
        self._health(facts,refs)
        return VerifiedG05Health(boot,facts['raw_response'],self,self._health_deadline)

    def prepare_observation(self,event):
        """Validate actual E4 return and retain original getter/registry outside entry."""
        from .g05_csr_projection_v1 import _map_original_trace
        facts,refs=self._consume(event)
        _need(facts['kind']=='trace_scan' and self.boot is not None and self._source_attached,
              'actual same-run TRACE scan required')
        self.binding.check_source_config()
        mapping=_map_original_trace(self,event,facts,refs)
        capture=mapping.capture_ref
        self.refs.source.capture(capture,refs['payload'],candidate=mapping.candidate,
                                 fields=dict(request_raw=refs['request'].decode('utf8'),
                                             capture_raw=facts['raw_response'].decode('utf8'),
                                             format='G05_CSR_E4_RAW4_V1'))
        current,view,hold=self.refs.source.read_current_with_registry()
        self.refs.source.attach_registry(view,self.refs.c42_context,self.boot.generation,
                                        as_of_qpc_ns=current['at_qpc_ns'],observation_ref=hold)
        mapping.current_read,mapping.registry_ref,mapping.registry_hold=current,view,hold
        mapping.retained_bytes=_raw(mapping.candidate)
        result=_ObservationEvent(_KEY); _OBSERVATIONS[result]=mapping
        self._observation_events.add(result)
        self._mappings.append(mapping)
        return result

    def _previous_for_observation(self,m,previous):
        from ...tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
        selected=self._cycle_profile()
        if previous is None or not demo.is_navigation(selected):return previous
        from .g05_csr_projection_v1 import _original_mapping
        from .candidate_owner import _CompletedInference
        from ...integration.cpu_invocation_transcript import _ActorRecord
        _original_mapping(m)  # Original token/book/scoped source/E4 CRC/B131/phase chain.
        current=self.owner._candidates._current
        _need(type(current) is tuple and len(current)==2 and current[0]==previous.request_raw,
              'original committed command/progress association required')
        proof=current[1]
        _need(type(proof) is _CompletedInference and proof.boot is self.boot and proof.source is self
              and proof.clock_domain is self.refs.clock and proof.candidate_raw==previous.candidate_raw
              and proof.invocation_id==previous.invocation_id
              and proof.observed_interval_v2 is previous.observed_interval_v2,
              'original committed inference/progress identity required')
        adapter=self.owner._owned_invocations
        _need(not adapter.failed and adapter.pending is None and adapter.ready is None
              and len(adapter.records)==len(adapter.associations),'original settled invocation association required')
        pairs=[(r,a) for r,a in zip(adapter.records,adapter.associations)
               if r.identity.invocation_id==proof.invocation_id]
        _need(len(pairs)==1,'unique original committed invocation required')
        record,association=pairs[0];old=association.g05_mapping
        _need(type(record) is _ActorRecord and record.owner is self.owner._actor
              and record._close_attempted and record._close_error is None
              and type(old) is _Mapping and old.channels is self
              and _OBSERVATIONS.get(association.event) is old and old.used
              and association.source is self and association.clock is self.refs.clock and association.boot is self.boot
              and association.sample_ref is old.refs['draft'] and association.source_bound_receipt is old.refs['token']
              and association.record.raw==old.raw==association.observation_bytes
              and json.loads(association.observation_key)==host_envelope._parse_message(proof.candidate_raw)['observation'],
              'original private old sample/mapping/invocation binding required')
        _original_mapping(old)
        chosen=_fresh_action_previous(previous,m,old,profile=selected,source_origin=self.refs.source.source._origin)
        if chosen is None:
            _need(len(self._nav_new_actions)<selected.max_commands,'finite new navigation action evidence budget')
            self._nav_new_actions.append((m,old,previous,proof,record))
        return chosen

    def verify_observation(self,event,boot):
        from .pc_direct_runtime import VerifiedObservation
        from .owned_invocation_v1.adapter import _retain_original_association
        self.checkpoint(); m=_OBSERVATIONS.get(event)
        _need(boot is self.boot and type(m) is _Mapping and m.channels is self and not m.used,
              'unused original G05 observation required')
        _need(_raw(m.candidate)==m.retained_bytes, 'retained raw4 mapping changed')
        m.used=True
        record=VerifiedObservation(boot,m.raw,m.sample_lower_ns)
        deadline=min(m.sample_lower_ns+self.policy.max_source_age_ns,self._global_deadline)
        dispatch=min(deadline,self.owner._actor._run_deadline)
        previous=self._previous_for_observation(m,self.owner._progress.bound)
        _retain_original_association(self.owner,event,record,session=self.refs.projection,
            capture_ref=m.capture_ref,sample_ref=m.refs['draft'],current_read=m.current_read,
            registry_ref=m.registry_ref,history_refs=tuple(x.capture_ref for x in self._mappings if x is not m),
            mapping_receipt=m,source_bound_receipt=m.refs['token'],dispatch_bound_receipt=m.refs['phase_receipt'],
            source_deadline_ns=deadline,dispatch_deadline_ns=dispatch,
            previous_action=previous,previous_deadline_ns=None if previous is None else previous.deadline_ns,
            g05_mapping=m)
        return record

    def broker_next(self):
        """Pack only an actual offered owned-AI completion in its original slot."""
        if self.config.g05_board_output_v1 is not None:
            return self._broker_board_output()
        from .candidate_owner import _CompletedInference
        now=self.checkpoint(); o=self.owner
        _need(o is not None and not o._busy and o._state=='ACTIVE', 'original idle authority required')
        proof=o._candidates._pending
        if proof is None: return None
        _need(type(proof) is _CompletedInference and proof.boot is self.boot and proof.source is self,
              'original completed AI proposal required')
        mailbox=o._candidates._mailbox
        _need(mailbox._pc_direct_window_v2 is not None, 'explicit PC_DIRECT consume window required')
        relative=now-mailbox._origin-mailbox._window_first
        if relative<0: return None
        window=relative//mailbox._window_period
        if window<=mailbox._last_slot:return None
        start=mailbox._origin+mailbox._window_first+window*mailbox._window_period
        if not start<=now<start+mailbox._pc_direct_window_v2.consume_window_ns: return None
        ready=proof.completion_upper_ns+self.policy.usb_upper_ns+self.policy.packing_upper_ns
        if ready>start: return None
        candidate=_json(proof.candidate_raw,16384)
        _need(candidate['target']['action']!=0, 'STOP is not movement')
        self._command_seq+=1; _uint(self._command_seq,1,65535)
        quality_rows=[x for x in o._owned_invocations.quality_reports
                      if x['invocation_id']==proof.invocation_id]
        _need(len(quality_rows)==1, 'actual completion quality record required')
        quality=self.policy.demo_ai_profile.verifier.quality_report(
            quality_rows[0]['public_input'],observed_now_qpc_ns=now)
        self.command_quality_reports.append(dict(command_seq=self._command_seq,
            invocation_id=proof.invocation_id,broker_issue_qpc_ns=now,age_quality=dict(quality)))
        doc=dict(schema_version=1,kind='motion_request',context=dict(self.refs.legacy_context),
                 command_seq=self._command_seq,candidate_id=candidate['candidate_id'],
                 observation=candidate['observation'],target=candidate['target'],host_issue_monotonic_ns=now)
        raw=_raw(doc)
        host_envelope.validate_message(raw,producer='control_broker',consumer='world_authority',
                                       context=self.refs.legacy_context,now_ns=now)
        event=_CommandEvent(_KEY);_COMMANDS[event]=(self,raw,proof,window,start,now)
        self._command_pending=event
        return event

    def prepare_board_output(self,event):
        """Consume actual producer APPLY after AI completion, before broker issue.

        Root first consumes any preceding source-admission events emitted while
        APPLY was in flight. No status-only event or reconstructed JSON grants
        this association. TTL begins at the original pre-APPLY host lower bound.
        """
        from .candidate_owner import _CompletedInference
        from .g05_board_output_v1 import G05BoardOutputPolicyV1, decode_board_output, MODE
        now=self.checkpoint();o=self.owner
        _need(type(self.config.g05_board_output_v1) is G05BoardOutputPolicyV1
              and o is not None and not o._busy and o._state=='ACTIVE'
              and self._board_pending is None,'exclusive idle board-output admission required')
        proof=o._candidates._pending
        _need(type(proof) is _CompletedInference and proof.boot is self.boot and proof.source is self,
              'original completed AI proposal required before APPLY')
        facts,refs=self._consume(event)
        _need(facts['kind']=='apply','actual original APPLY output required')
        self._health(facts,refs)  # Full13, full32, original phase, cumulative receipts.
        phase=refs['phase_receipt'];request=_json(phase.request_raw)
        _need(phase.kind=='apply' and request['kind']=='apply'
              and proof.completion_upper_ns<=phase.lower_qpc_ns<=phase.upper_qpc_ns,
              'actual APPLY must follow original AI completion')
        command=tuple(request['payload']['command_words'])
        words=_json(phase.response_raw,4194304)['result']['capture']['words32']
        target=decode_board_output(words,command,session=self.refs.chain.identity[12])
        _need(command[2]==self.refs.legacy_context['transport_profile_id']
              and command[5]>self._board_last_sequence and words[0]>self._board_last_result,
              'fresh original board output and fixed profile required')
        candidate=_json(proof.candidate_raw,16384)
        _need(target==candidate['target'],'measured FPGA output differs from original AI target')
        deadline=min(_uint(phase.lower_qpc_ns+target['duration_ms']*1_000_000),
                     self._health_deadline,self._global_deadline)
        _need(self.checkpoint()<deadline,'original APPLY TTL expired before admission')
        self._board_last_sequence,self._board_last_result=command[5],words[0]
        self._board_pending=(event,phase,proof,deadline,_raw(target))
        return dict(mode=MODE,genuine_PC_DIRECT=False,command_seq=command[5],tag=command[6],
                    result_seq=words[0],target=dict(target),deadline_qpc_ns=deadline,
                    apply_lower_qpc_ns=phase.lower_qpc_ns,apply_upper_qpc_ns=phase.upper_qpc_ns,
                    capture_sha256=_sha(_raw(words)),pwm_period_words=list(words[12:15]),
                    pwm_high_words=list(words[15:18]),submitted_echo_words=list(words[3:6]),
                    submitted_echo_role='echo_only',host_context_encoding='topology2_compatibility_only')

    def _broker_board_output(self):
        from .g05_board_output_v1 import MODE
        now=self.checkpoint();o=self.owner
        _need(o is not None and not o._busy and o._state=='ACTIVE','original idle authority required')
        output=self._board_pending
        if output is None:return None
        proof=output[2]
        _need(o._candidates._pending is proof and now<output[3],
              'original pending AI/APPLY association expired or displaced')
        mailbox=o._candidates._mailbox;policy=mailbox._g05_board_output_v1
        _need(policy is self.config.g05_board_output_v1 and mailbox._pc_direct_window_v2 is None,
              'exclusive original board-output window required')
        relative=now-mailbox._origin-mailbox._window_first
        if relative<0:return None
        window=relative//mailbox._window_period
        if window<=mailbox._last_slot:return None
        start=mailbox._origin+mailbox._window_first+window*mailbox._window_period
        if not start<=now<min(start+policy.consume_window_ns,output[3]):return None
        if proof.completion_upper_ns+self.policy.usb_upper_ns+self.policy.packing_upper_ns>start:return None
        candidate=_json(proof.candidate_raw,16384)
        # Construct the motion target from retained actual measured output.
        target=_json(output[4],4096)
        self._command_seq+=1;_uint(self._command_seq,1,65535)
        doc=dict(schema_version=1,kind='motion_request',context=dict(self.refs.legacy_context),
                 command_seq=self._command_seq,candidate_id=candidate['candidate_id'],
                 observation=candidate['observation'],target=target,host_issue_monotonic_ns=now)
        raw=_raw(doc)
        host_envelope.validate_message(raw,producer='control_broker',consumer='world_authority',
                                       context=self.refs.legacy_context,now_ns=now)
        event=_CommandEvent(_KEY);_COMMANDS[event]=(self,raw,proof,window,start,now)
        self._board_outputs.append((raw,output,event));self._board_pending=None
        self._command_pending=event
        self.command_quality_reports.append(dict(command_seq=self._command_seq,
            invocation_id=proof.invocation_id,broker_issue_qpc_ns=now,mode=MODE,genuine_PC_DIRECT=False,
            apply_lower_qpc_ns=output[1].lower_qpc_ns,board_deadline_qpc_ns=output[3]))
        return event

    def verify_board_output(self,event,boot,raw,proof,*,now_ns):
        """Exact original APPLY and one emitted command; no parsed-proof adoption."""
        _need(boot is self.boot,'original board-output boot required')
        rows=[row for row in self._board_outputs if row[0]==raw and row[2] is event]
        _need(len(rows)==1 and rows[0][1][2] is proof,'original board-output command association required')
        return self.board_deadline_for(raw,now_ns=now_ns)

    def board_deadline_for(self,raw,*,now_ns):
        from .g05_board_output_v1 import decode_board_output
        self.checkpoint();rows=[row for row in self._board_outputs if row[0]==raw]
        _need(len(rows)==1,'original command-bound APPLY required')
        output=rows[0][1];phase=output[1]
        request=_json(phase.request_raw);words=_json(phase.response_raw,4194304)['result']['capture']['words32']
        target=decode_board_output(words,tuple(request['payload']['command_words']),session=self.refs.chain.identity[12])
        _need(_raw(target)==output[4] and _json(raw)['target']==target
              and _json(output[2].candidate_raw)['target']==target
              and _uint(now_ns)<output[3],'original measured output/TTL changed or expired')
        return output[3]

    def latest_quality(self):
        """Detached real observed-time diagnostics; never renews any deadline."""
        self.checkpoint()
        adapter=None if self.owner is None else self.owner._owned_invocations
        return dict(completions=[] if adapter is None else copy.deepcopy(adapter.quality_reports),
                    commands=copy.deepcopy(self.command_quality_reports))

    def verify_command(self,event,boot):
        from .pc_direct_runtime import VerifiedEnvelope
        row=_COMMANDS.get(event);self.checkpoint()
        _need(boot is self.boot and row is not None and row[0] is self and self._command_pending is event
              and self.owner._candidates._pending is row[2], 'original broker/candidate command required')
        return VerifiedEnvelope(boot,row[1])

    def verify_slot(self,event,boot):
        from .candidate_owner import _VerifiedSlot
        row=_COMMANDS.get(event);now=self.checkpoint()
        _need(boot is self.boot and row is not None and row[0] is self and self._command_pending is event,
              'original broker slot event required')
        policy=(self.config.pc_direct_window_v2 if self.config.g05_board_output_v1 is None
                else self.config.g05_board_output_v1)
        _need(row[4]<=now<row[4]+policy.consume_window_ns,
              'original actual consume window closed')
        self._command_pending=None
        return _VerifiedSlot(boot,self,self.refs.clock,row[3])


class _CsrHealthGuard:
    """Same watchdog interface, backed exclusively by genuine CSR health facts."""
    def __init__(self,key,channels,now):
        _need(key is _KEY and type(channels) is G05CsrChannels, 'original CSR channel required')
        self.channels=channels;self.context=dict(channels.refs.legacy_context)
        self.now=_uint(now);self.latched=False;self.reason='no_command'
        self.command=None;self.deadline=None;self.last=None

    def _trip(self,reason):
        self.latched=True;self.reason=reason;self.command=self.deadline=None

    def check(self,*,now_ns):
        from ...integration.pc_direct_watchdog import StopGateDecision
        now=_uint(now_ns)
        if now<self.now:self._trip('CSR_clock_regression')
        self.now=now
        try:self.channels.checkpoint()
        except Exception:self._trip('CSR_health_or_session_expired')
        health=self.channels._health_deadline
        if health is None or now>=health:self._trip('CSR_health_timeout')
        if self.deadline is not None and now>=self.deadline:
            self.command=self.deadline=None;self.reason='command_deadline'
        healthy=not self.latched and health is not None
        return StopGateDecision(not healthy or self.command is None,self.reason,healthy,self.latched,
                                self.command,self.deadline,health,None,None)

    def track_authority_command(self,*,command_seq,deadline_ns,now_ns):
        decision=self.check(now_ns=now_ns)
        _need(not decision.latched and decision.heartbeat_healthy, 'actual CSR health required')
        seq=_uint(command_seq,0,65535);end=_uint(deadline_ns,1)
        _need(end>now_ns and (self.last is None or seq>self.last), 'original increasing command required')
        self.command=self.last=seq;self.deadline=end;self.reason='no_CSR_watchdog_veto'
        return self.check(now_ns=now_ns)

    def cancel(self,*,now_ns):
        self.check(now_ns=now_ns);self.command=self.deadline=None;self.reason='cancelled'
        return self.check(now_ns=now_ns)
