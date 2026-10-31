"""A Root's one-use original pre-source preparation, never authority activation.

Validate now; call prepare only when the reviewed C49 attachment and the whole
immediate cycle are ready. Real init starts a NON-RENEWABLE board-monotonic
deadline of at most ten seconds. Neither this object graph nor its observation
snapshot can be adopted/restored later. No retry, STOP, source start or cleanup
is implicit: Root retains ownership of all original objects after any failure.

DEEPEYE-HUMAN-LOCK-20261014/revision1, H01-H15 unchanged. Final default source
freshness remains 100 ms; a larger demo budget requires explicit selection.
"""
from dataclasses import dataclass, field
import hashlib
import threading

from ..run_causal_functional_chain import FunctionalWorld, FunctionalSource
from ...integration.host_clock import QpcHostClock
from ...simulation.authority.actor_composition import AuthorityConfig, PcDirectWindowV2
from ...simulation.isolation.actor_owner import ActorPolicy
from ...simulation.authority.original_world_actor_link import _OriginalWorldActorLink
from ...simulation.authority.root_source_book import RootSourceBook
from ...simulation.authority.source_projection_v1.provider import ProjectionSession
from . import functional50_ssh_a as ssh
from . import functional50_g05_a as g05
from . import demo30h_age_budget_a as age_module
from . import original_chain_receipt_producer_a as receipt_module
from .functional50_chain_v2_client_a import ChainSessionV2, OriginalPhaseReceipt
from .original_chain_receipt_producer_a import OriginalChainReceiptProducer
from .original_g05_operation_binding_a import OriginalG05OperationBinding, _canonical, _validate_context
from .original_source_trace_scan_a import OriginalSourceTraceScan, _check_bundle
from .original_chain_source_pump_a import OriginalChainSourcePump
from .demo30h_age_budget_a import select_demo_age_budget

REQUIREMENTS_SHA256 = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
_PLAN_KEY = object()
_ATTEMPTS = {}  # Strong original recovery ownership, including failed attempts.
_MAX_NS = (1 << 63) - 1


def _need(value, message):
    if not value:
        raise ValueError(message)


def _integer(value, low, high, name):
    _need(type(value) is int and low <= value <= high, 'strict bounded ' + name + ' required')


@dataclass(frozen=True)
class ValidatedPlan:
    world: object
    authority_config: object
    legacy_context: dict
    c42_context: dict
    g05_policy_raw: bytes
    ident: str
    identity_words: tuple
    max_commands: int
    max_polls: int
    duration_ns: int
    max_io: int
    timeout_ns: int
    max_source_age_ns: int | None
    select_owner_work_v1: bool
    _key: object = field(repr=False)
    _thread: int = field(repr=False)
    _legacy_raw: bytes = field(repr=False)
    _c42_raw: bytes = field(repr=False)
    _refs: tuple = field(repr=False)

    def __post_init__(self):
        _need(self._key is _PLAN_KEY, 'use validate_pre_source_plan')

    def __reduce__(self):
        raise TypeError('original pre-source plan cannot be serialized or adopted')


def _validate_world_config(world, config):
    _need(type(world) is FunctionalWorld and type(world.source) is FunctionalSource
          and type(config) is AuthorityConfig and type(config.actor_policy) is ActorPolicy,
          'exact original world/source/authority configuration required')
    f, clock = world.source, world.clock
    _need(type(clock) is QpcHostClock and f.clock is clock
          and world._thread == f._thread == threading.get_ident(), 'same original owner/QPC required')
    clock._check()
    _need(not world._close_attempted and world.owner is f.owner and world.binding is f.binding
          and not f._activation_attempted and not f._start_attempted and f.composition is None,
          'fresh unclosed original world required')
    b, s, l, v = f.book, f.source, f.link, f.session
    _need(type(b) is RootSourceBook and type(l) is _OriginalWorldActorLink
          and type(v) is ProjectionSession, 'original link/book/projection required')
    l._registered(); b._check(); v._check()
    _need(l.owner is world.owner and l.binding is world.binding and l.source is s and l.book is b
          and v._owner is world.owner and v._link is l and v._book is b
          and not l.claimed and l.composition is None, 'unclaimed original world association required')
    _need(s.state == 'NEW' and s._origin is None and s._clock is None and s._count == 0
          and s._last_tick is None and s._polling is False and s._source_book is b
          and b._source is s and b._clock is clock and b._state == 'NEW' and b._origin is None
          and not b._samples and b._active is None and not f._retained_samples and f._pending is None,
          'untouched deferred original source required')
    values = world.binding.world_values
    _need(all(getattr(config, name) is getattr(values, name)
              for name in ('initial_state', 'scene', 'model', 'budget'))
          and config.max_slices == l.executor._max_slices
          and config.actor_policy.run_id == l.native.run_id, 'original authority configuration mismatch')
    for name in ('heartbeat_timeout_ns', 'progress_max_age_ns', 'max_slices'):
        _integer(getattr(config, name), 1, _MAX_NS, name)
    _need(type(config.enable_completion_interval_v2) is bool, 'strict completion interval selection required')
    _need(type(config.ai_model_sha256) is str and len(config.ai_model_sha256) == 64
          and all(x in '0123456789abcdef' for x in config.ai_model_sha256), 'approved AI model SHA256 required')
    if config.pc_direct_window_v2 is not None:
        _need(type(config.pc_direct_window_v2) is PcDirectWindowV2, 'original PC direct policy required')
        _integer(config.pc_direct_window_v2.consume_window_ns, 1, _MAX_NS, 'consume window')
    config.actor_policy._validate()  # Read-only original path/package/budget checks.
    if config.owned_invocation_v1 is not None:
        from ...simulation.authority.owned_invocation_v1.adapter import _validate_config
        _validate_config(config, clock)
    return (f, clock, world.owner, world.binding, l, b, v, l.executor, l.native,
            values.initial_state, values.scene, values.model, values.budget)


def _validate_inputs(*, world, authority_config, legacy_context, c42_context,
                     g05_policy_raw, ident, identity_words, max_commands, max_polls,
                     duration_ns, max_io, timeout_ns, max_source_age_ns, select_owner_work_v1):
    # Refuse all cheap protocol/configuration errors before preparation can init.
    from .functional50_chain_v2_board_a import ID
    _need(type(ident) is str and ID.fullmatch(ident) is not None, 'bounded protocol request ID required')
    g05._identity(identity_words)
    for value, low, high, name in ((max_commands,1,2,'commands'), (max_polls,4,64,'polls'),
            (duration_ns,1,10_000_000_000,'duration'), (max_io,1,450,'I/O cap'),
            (timeout_ns,1,60_000_000_000,'timeout')):
        _integer(value, low, high, name)
    _need(type(select_owner_work_v1) is bool, 'strict owner work selection required')
    if max_source_age_ns is not None:
        _integer(max_source_age_ns, 100_000_001, 5_000_000_000, 'explicit demo age')
        _need(max_source_age_ns <= duration_ns, 'demo age must fit fixed board duration')
    _need(type(legacy_context) is dict and type(c42_context) is dict, 'exact original context dictionaries required')
    _validate_context(legacy_context, c42_context)
    legacy_raw, c42_raw = _canonical(legacy_context), _canonical(c42_context)
    refs = _validate_world_config(world, authority_config)
    _need(c42_context['operation_id'] == world.operation_id
          and c42_context['clock_domain_id'] == world.clock.metadata['domain_id'], 'same operation and QPC domain required')
    _need(type(g05_policy_raw) is bytes and 0 < len(g05_policy_raw) <= 131072, 'actual bounded G05 policy bytes required')
    document = g05.board._json(g05_policy_raw)
    _need(type(document) is dict and type(document.get('binding')) is dict, 'actual G05 policy binding required')
    binding = document['binding']
    _need(set(binding) == {'operation_id','request_sha256','boot_id','source_commit','build_id'}
          and binding['operation_id'] == world.operation_id
          and binding['request_sha256'] == c42_context['request_hash']
          and binding['boot_id'] == c42_context['boot_id']
          and binding['source_commit'] == c42_context['tested_commit']
          and type(binding['build_id']) is str and 0 < len(binding['build_id']) <= 192,
          'actual same-operation G05 policy/context required')
    policy = g05._policy(g05_policy_raw, binding)
    limits = policy['limits']
    _need(102 + 76*max_commands + 2*max_polls <= limits['total_io'] <= max_io
          and limits['begin'] >= 1 and all(limits[k] >= max_commands for k in ('commit','latch','release')),
          'actual G05 policy cannot cover selected session or exceeds budget')
    return refs, legacy_raw, c42_raw, policy


def validate_pre_source_plan(*, world, authority_config, legacy_context, c42_context,
        g05_policy_raw, ident, identity_words, max_commands, max_polls, duration_ns,
        max_io, timeout_ns, max_source_age_ns=None, select_owner_work_v1=False):
    """Validate/freeze trusted original refs without init, source start or acquisition.

    Contexts retain their original identity; their canonical bytes detect later
    mutation. Policy bytes must be the actual file later attested by SSH ready.
    Validation is not board authentication or a readiness/authority grant.
    """
    inputs = dict(world=world, authority_config=authority_config, legacy_context=legacy_context,
        c42_context=c42_context, g05_policy_raw=g05_policy_raw, ident=ident, identity_words=identity_words,
        max_commands=max_commands,max_polls=max_polls,duration_ns=duration_ns,max_io=max_io,
        timeout_ns=timeout_ns,max_source_age_ns=max_source_age_ns,select_owner_work_v1=select_owner_work_v1)
    refs, legacy_raw, c42_raw, _ = _validate_inputs(**inputs)
    return ValidatedPlan(**inputs, _key=_PLAN_KEY, _thread=threading.get_ident(),
                         _legacy_raw=legacy_raw, _c42_raw=c42_raw, _refs=refs)


@dataclass(eq=False)
class PreparedCycle:
    """Retained recovery objects; only a completed preparation is returned normally."""
    plan: ValidatedPlan
    chain: object
    stage: str = 'preflight'
    status: str = 'IN_PROGRESS'
    producer: object = None
    init_event: object = None
    init_receipt: object = None
    demo_age_budget: object = None
    binding: object = None
    scanner: object = None
    pump: object = None
    phase_receipts: tuple = ()
    lower_qpc_ns: int | None = None
    upper_qpc_ns: int | None = None
    error: object = None
    evidence_errors: list = field(default_factory=list)

    def __reduce__(self):
        raise TypeError('prepared original cycle cannot be serialized or adopted')

    def snapshot(self):
        """JSON-safe historical observations; never executable/restorable state."""
        return dict(schema='demo30h_pre_source_observation_v1', requirements_sha256=REQUIREMENTS_SHA256,
            operation_id=self.plan.world.operation_id, stage=self.stage, status=self.status,
            authority='not_evaluated', resumable=False, snapshot_is_execution_permission=False,
            deadline_note='init starts fixed board-monotonic deadline <=10s; no renewal or clock-domain conversion',
            duration_ns=self.plan.duration_ns, max_source_age_ns=self.plan.max_source_age_ns,
            source_state=self.plan.world.source.source.state,
            pump_enabled=None if self.pump is None else self.pump.enabled,
            session_unknown=self.chain.s._unknown, lower_qpc_ns=self.lower_qpc_ns,
            upper_qpc_ns=self.upper_qpc_ns, error_type=None if self.error is None else type(self.error).__name__,
            evidence_errors=list(self.evidence_errors), phases=[dict(kind=p.kind,status=p.status,unknown=p.unknown,
                lower_qpc_ns=p.lower_qpc_ns,upper_qpc_ns=p.upper_qpc_ns,
                request_sha256=hashlib.sha256(p.request_raw).hexdigest(),
                response_sha256=hashlib.sha256(p.response_raw).hexdigest()) for p in self.phase_receipts])


class PreSourcePreparationError(ValueError):
    """Keep original state for Root cleanup; no replay/reset/STOP is attempted."""
    def __init__(self, cause, cycle):
        super().__init__('original pre-source preparation failed at ' + cycle.stage)
        self.cause, self.cycle = cause, cycle


def _capture_phases(cycle):
    try:
        cycle.phase_receipts = cycle.chain.phase_receipts
    except BaseException as error:
        cycle.evidence_errors.append('phase_capture:' + type(error).__name__)


def prepare_pre_source_cycle(plan, chain):
    """Execute one real init->binding->deferred scanner->disabled pump sequence.

    Caller supplies already-acquired original world/SSH chain. This immediately
    consumes the attempt, including failures; call only just before the reviewed
    integrated activation. Inspect exception.cycle for original cleanup custody.
    """
    _need(type(plan) is ValidatedPlan and plan._key is _PLAN_KEY and type(chain) is ChainSessionV2,
          'original validated plan and chain required')
    _need(threading.get_ident() == plan._thread == chain.thread, 'same original preparation owner required')
    _need(chain not in _ATTEMPTS and not any(c.plan.world is plan.world or c.chain.s is chain.s
                                           or c.plan._refs[0] is plan._refs[0] for c in _ATTEMPTS.values()),
          'pre-source attempt already consumed for original world/source/session')
    cycle = PreparedCycle(plan, chain)
    _ATTEMPTS[chain] = cycle
    try:
        inputs = {name:getattr(plan,name) for name in (
            'world','authority_config','legacy_context','c42_context','g05_policy_raw','ident','identity_words',
            'max_commands','max_polls','duration_ns','max_io','timeout_ns','max_source_age_ns','select_owner_work_v1')}
        refs, legacy_raw, c42_raw, policy = _validate_inputs(**inputs)
        _need(all(a is b for a,b in zip(refs,plan._refs)) and len(refs) == len(plan._refs)
              and legacy_raw == plan._legacy_raw and c42_raw == plan._c42_raw, 'validated original plan changed')
        origin = chain._phase_binding()
        _need(type(chain.s) is ssh.Session and chain.clock is plan.world.clock
              and origin is ssh._original_session_origin(chain.s) and origin[2] is chain.clock
              and origin[0].operation_id == plan.world.operation_id == chain.s._dir.name
              and not chain.s._unknown and not chain.s._closed, 'same original live session/clock required')
        chain.s._check()
        _need(not chain.sequence.initialized and not chain.sequence.ids and not chain.sequence.closed
              and not chain.phase_receipts and chain.s not in receipt_module._OWNERS
              and plan.world.source not in receipt_module._SOURCES
              and getattr(chain.s,'_source_pump',None) is None and chain.s not in ssh._SESSION_PUMPS,
              'fresh unclaimed original chain/source/pump required')
        _check_bundle(chain.bundle)
        ready, binding = origin[4], policy['binding']
        _need(ready['policy_file_sha256'] == hashlib.sha256(plan.g05_policy_raw).hexdigest()
              and ready['load_request_hash'] == binding['request_sha256']
              and ready['source_commit'] == binding['source_commit'] and ready['build_id'] == binding['build_id'],
              'actual original ready/policy/build mismatch')
        if plan.max_source_age_ns is not None:
            _need(len(age_module._SELECTED) < age_module._MAX_SELECTIONS, 'demo age retained selection cap exhausted')
        selected = chain.owner_work_v1
        _need(plan.select_owner_work_v1 or not selected, 'undeclared owner work selection')
        cycle.lower_qpc_ns = plan.world.clock()
        cycle.stage = 'select_owner_work_v1'
        if plan.select_owner_work_v1 and not selected:
            chain.select_owner_work_v1()
        cycle.stage = 'producer'
        cycle.producer = OriginalChainReceiptProducer(plan.world, chain, scanner=None)
        cycle.stage = 'init'
        cycle.init_event = cycle.producer.init(plan.ident,plan.identity_words,
            max_commands=plan.max_commands,max_polls=plan.max_polls,duration_ns=plan.duration_ns,
            max_io=plan.max_io,timeout_ns=plan.timeout_ns)
        _capture_phases(cycle)
        _need(len(cycle.phase_receipts) == 1, 'exactly one original init phase required')
        phase = cycle.phase_receipts[0]
        cycle.init_receipt = phase
        _need(type(phase) is OriginalPhaseReceipt and phase.owner is chain and phase.kind == 'init'
              and phase.phase_index == 1 and phase.status == 'COMPLETE' and phase.unknown is False
              and any(event is cycle.init_event and refs.get('phase_receipt') is phase
                      for event,_,refs in cycle.producer._history), 'actual complete original init event/phase required')
        cycle.stage = 'demo_age'
        if plan.max_source_age_ns is not None:
            cycle.demo_age_budget = select_demo_age_budget(plan.world,cycle.producer,
                                                          max_source_age_ns=plan.max_source_age_ns)
        cycle.stage = 'operation_binding'
        cycle.binding = OriginalG05OperationBinding(plan.world,cycle.producer,plan.authority_config,phase,
                            legacy_context=plan.legacy_context,c42_context=plan.c42_context)
        cycle.stage = 'scanner'
        cycle.scanner = OriginalSourceTraceScan(plan.world.source,chain.bundle,source_scan_cycle_v2=True,
                                               defer_start=True,demo_age_budget=cycle.demo_age_budget)
        cycle.stage = 'bind_scanner'
        cycle.producer.bind_scanner(cycle.scanner)
        cycle.stage = 'pump'
        cycle.pump = OriginalChainSourcePump(chain.s,plan.world.source,cycle.scanner)
        cycle.stage = 'bind_pump'
        cycle.producer.bind_pump(cycle.pump)
        _need(plan.world.source.source.state == 'NEW' and not plan.world.source._start_attempted
              and cycle.scanner._defer_start is True and cycle.scanner._activated is False
              and cycle.scanner._activation_attempted is False and not cycle.pump.enabled,
              'pre-source preparation must remain NEW/deferred/disabled')
        cycle.upper_qpc_ns = plan.world.clock()
        cycle.stage, cycle.status = 'prepared', 'PREPARED'
        return cycle
    except BaseException as error:
        cycle.error, cycle.status = error, 'FAILED'
        _capture_phases(cycle)
        raise PreSourcePreparationError(error, cycle) from error
