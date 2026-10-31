"""One operation's explicit demo-only source age budget; not authority."""
import threading

_KEY=object()
_SELECTED={}
_MAX_NS=5_000_000_000
_MAX_SELECTIONS=16

class DemoAgeBudget:
 __slots__=('_world','_source','_producer','_chain','_session','_clock','_operation','_domain','_thread','_max','_duration','_origin','_scanner','_ledger','_sealed')
 def __init__(self,key,world,producer,maximum):
  if key is not _KEY:raise ValueError('original demo age factory required')
  chain=producer._chain
  for k,v in dict(_world=world,_source=world.source,_producer=producer,_chain=chain,_session=producer._session,_clock=world.clock,_operation=world.operation_id,_domain=world.clock.metadata['domain_id'],_thread=threading.get_ident(),_max=maximum,_duration=chain.duration,_origin=producer._origin,_scanner=None,_ledger=None,_sealed=True).items():object.__setattr__(self,k,v)
 def __setattr__(self,k,v):raise AttributeError('immutable demo age selection')
 def __reduce__(self):raise TypeError('operation-bound age selection is not serializable')
 @property
 def max_source_age_ns(self):return self._max
 @property
 def operation_id(self):return self._operation
 @property
 def clock_domain_id(self):return self._domain

def _validate_original(world,producer):
 from ..run_causal_functional_chain import FunctionalWorld,FunctionalSource
 from .original_chain_receipt_producer_a import OriginalChainReceiptProducer
 from .functional50_chain_v2_client_a import ChainSessionV2
 from ...integration.host_clock import QpcHostClock
 if type(world) is not FunctionalWorld or type(world.source) is not FunctionalSource or type(producer) is not OriginalChainReceiptProducer or type(producer._chain) is not ChainSessionV2 or type(world.clock) is not QpcHostClock:raise ValueError('exact original world and chain required')
 producer._check();chain=producer._chain;chain._phase_binding()
 if (producer._world is not world or producer._source is not world.source or producer._clock is not world.clock or chain.clock is not world.clock or chain.s is not producer._session or producer._operation!=world.operation_id or producer._scanner is not None or world.source._start_attempted or world.source.source.state!='NEW' or not chain.sequence.initialized or chain.sequence.closed or len(chain.phase_receipts)!=1 or chain.phase_receipts[0].kind!='init' or chain.phase_receipts[0].status!='COMPLETE' or chain.phase_receipts[0].unknown or chain.phase_receipts[0].owner is not chain or not any(refs.get('phase_receipt') is chain.phase_receipts[0] for _,_,refs in producer._history)):raise ValueError('fresh original source and completed original init required')

def select_demo_age_budget(world,producer,*,max_source_age_ns):
 _validate_original(world,producer)
 if type(max_source_age_ns) is not int or not 100_000_000<max_source_age_ns<=_MAX_NS or type(producer._chain.duration) is not int or max_source_age_ns>producer._chain.duration:raise ValueError('finite selected demo age within original session required')
 if producer in _SELECTED:raise ValueError('demo age already selected for operation')
 if len(_SELECTED)>=_MAX_SELECTIONS:raise ValueError('demo age retained selection cap exhausted')
 token=DemoAgeBudget(_KEY,world,producer,max_source_age_ns);_SELECTED[producer]=token;return token

def _verify(token,scanner,*,pending=False):
 if (type(token) is not DemoAgeBudget or _SELECTED.get(token._producer) is not token or threading.get_ident()!=token._thread or token._world.source is not token._source or token._world.clock is not token._clock or token._world.operation_id!=token._operation or token._producer._failed or token._producer._closed or (pending and token._producer._scanner is not None) or (not pending and token._producer._scanner is not scanner) or token._producer._world is not token._world or token._producer._source is not token._source or token._producer._chain is not token._chain or token._producer._clock is not token._clock or token._producer._operation!=token._operation or token._chain.clock is not token._clock or token._chain.duration!=token._duration or token._producer._origin is not token._origin or token._producer._session is not token._session or token._chain.s is not token._session or token._session._unknown or token._session._closed or token._session._dir.name!=token._operation or token._clock.metadata['domain_id']!=token._domain or scanner._functional is not token._source or scanner._clock is not token._clock or token._scanner is not scanner):raise ValueError('original operation-bound demo age selection required')
 if token._chain._phase_binding() is not token._origin:raise ValueError('original session origin changed')
 # Age observations may continue during close intent; request admission remains
 # governed by the protocol sequence, with actual producer/session closure above.
 return token._max

def _bind_scanner(token,scanner):
 from .original_source_trace_scan_a import OriginalSourceTraceScan
 if type(token) is not DemoAgeBudget or type(scanner) is not OriginalSourceTraceScan or token._scanner is not None:raise ValueError('one original scanner binding required')
 object.__setattr__(token,'_scanner',scanner)
 try:_verify(token,scanner,pending=True)
 except BaseException:raise

def _bind_ledger(token,scanner,ledger):
 _verify(token,scanner)
 if token._ledger is not None:raise ValueError('one original ledger required')
 object.__setattr__(token,'_ledger',ledger)

def _ledger_limit(token,scanner,ledger):
 value=_verify(token,scanner)
 if token._ledger is not ledger:raise ValueError('original demo ledger required')
 return value
