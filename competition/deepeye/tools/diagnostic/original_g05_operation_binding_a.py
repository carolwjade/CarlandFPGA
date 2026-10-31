"""Original host-side G05 operation association; no hardware authority."""
from dataclasses import dataclass
import json
import re
import threading
from ..run_causal_functional_chain import FunctionalWorld, FunctionalSource
from ...simulation.authority.actor_composition import AuthorityConfig
from ...simulation.authority.original_world_actor_link import _OriginalWorldActorLink
from ...simulation.authority.root_source_book import RootSourceBook
from ...simulation.authority.source_projection_v1.provider import ProjectionSession
from ...integration.host_clock import QpcHostClock
from .original_chain_receipt_producer_a import OriginalChainReceiptProducer
from .functional50_chain_v2_client_a import ChainSessionV2, OriginalPhaseReceipt
from .functional50_ssh_a import _original_session_origin

def _need(ok, message):
    if not ok: raise ValueError(message)

def _canonical(value):
    _need(type(value) is dict,'exact context required')
    data=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
    _need(len(data)<=8192,'context exceeds bound')
    return data

def _validate_context(legacy, c42):
    _need(set(legacy)=={'session','config_epoch','boot_sha256','transport_profile_id','source_id','topology_id','acquisition_profile_id'},'legacy context fields')
    _need(type(legacy['session']) is int and 0<=legacy['session']<=0xffffffff and type(legacy['config_epoch']) is int and 0<=legacy['config_epoch']<=255,'legacy session/epoch')
    _need(type(legacy['boot_sha256']) is str and re.fullmatch('[0-9a-f]{64}',legacy['boot_sha256']) is not None,'legacy boot digest')
    for k,allowed in (('transport_profile_id',(1,2)),('source_id',(1,2,3,4)),('topology_id',(1,2,3)),('acquisition_profile_id',(1,2,3))):
        _need(type(legacy[k]) is int and legacy[k] in allowed,'legacy context value')
    _need(set(c42)=={'operation_id','request_hash','tested_commit','build_manifest_sha256','boot_id','session_id','tag','clock_domain_id'},'C42 context fields')
    for k,n in (('request_hash',64),('tested_commit',40),('build_manifest_sha256',64),('clock_domain_id',32)):
        _need(type(c42[k]) is str and re.fullmatch('[0-9a-f]{%d}'%n,c42[k]) is not None,'C42 digest')
    for k in ('operation_id','boot_id','session_id'):
        v=c42[k];_need(type(v) is str and 1<=len(v)<=192 and all(32<=ord(ch)<=126 for ch in v),'C42 identity text')
    _need(type(c42['tag']) is int and 1<=c42['tag']<=0xffffffff,'C42 tag')

@dataclass(frozen=True)
class OriginalG05FactoryRefs:
    world: object
    source: object
    link: object
    book: object
    projection: object
    producer: object
    chain: object
    session: object
    init_receipt: object
    clock: object
    legacy_context: object
    c42_context: object
    source_config_attached: bool

class OriginalG05OperationBinding:
    def __init__(self,world,producer,config,init_receipt,*,legacy_context,c42_context):
        _need(type(world) is FunctionalWorld and type(world.source) is FunctionalSource and type(producer) is OriginalChainReceiptProducer and type(config) is AuthorityConfig and type(init_receipt) is OriginalPhaseReceipt,'exact original types required')
        source=world.source;chain=producer._chain;link=source.link;book=source.book;projection=source.session;clock=world.clock
        _need(type(chain) is ChainSessionV2 and type(link) is _OriginalWorldActorLink and type(book) is RootSourceBook and type(projection) is ProjectionSession and type(clock) is QpcHostClock,'exact original association required')
        _validate_context(legacy_context,c42_context)
        self.world=world;self.source=source;self.producer=producer;self.config=config;self.receipt=init_receipt
        self.chain=chain;self.link=link;self.book=book;self.projection=projection;self.clock=clock
        self.session=chain.s;self.origin=_original_session_origin(self.session);self.process=producer._process
        self._thread=threading.get_ident();self._legacy=legacy_context;self._c42=c42_context
        self._legacy_raw=_canonical(legacy_context);self._c42_raw=_canonical(c42_context)
        self._claim_attempted=False;self._attach_attempted=False;self._failed=False;self._source_ref=None;self._config_raw=None;self._stored_config=None;self._stored_fields=None;self._ids=None
        self._check()
        _need(source.source.state in ('NEW','RUNNING'),'original source lifecycle required')
    def _check(self):
        _need(not self._failed and threading.get_ident()==self._thread,'original live owner required')
        w,s,p,c,l,b,v,r=self.world,self.source,self.producer,self.chain,self.link,self.book,self.projection,self.receipt
        _need(_canonical(self._legacy)==self._legacy_raw and _canonical(self._c42)==self._c42_raw,'context mutated')
        p._check();l._registered();v._check()
        _need(w._thread==s._thread==c.thread==self._thread and w.source is s and w.owner is s.owner and w.binding is s.binding and w.clock is s.clock is c.clock is self.clock,'world association changed')
        _need(p._world is w and p._source is s and p._chain is c and p._book is b and p._session is self.session and p._clock is self.clock and p._process is self.process and p._origin is self.origin and _original_session_origin(self.session) is self.origin,'producer/session changed')
        _need(s.link is l and s.book is b and s.session is v and l.book is b and l.owner is w.owner and l.binding is w.binding and s.source is l.source and s.source._source_book is b and v._owner is w.owner and v._link is l and v._book is b,'link/book/projection changed')
        _need(not self.session._unknown and not self.session._closed and self.session._proc is self.process and self.origin[2] is self.clock and self.origin[1] is self.process and self.origin[0].operation_id==w.operation_id==self.session._dir.name and self._c42['operation_id']==w.operation_id and self._c42['clock_domain_id']==self.clock.metadata['domain_id'],'operation/process changed')
        _need(r.owner is c and r.kind=='init' and r.phase_index==1 and r.operation_id==w.operation_id and r.status=='COMPLETE' and r.unknown is False and r.session is self.session and r.process is self.process and r.clock is self.clock and r.session_origin is self.origin and r.stdin is self.origin[7] and r.stdout is self.origin[8] and r.stderr is self.origin[9] and r.spec is self.origin[0] and r.ready_raw is self.origin[3] and type(r.request_raw) is bytes and type(r.response_raw) is bytes and type(r.lower_qpc_ns) is int and type(r.upper_qpc_ns) is int and 0<=r.lower_qpc_ns<=r.upper_qpc_ns,'actual complete init phase required')
        _need(len(c.phase_receipts)>=1 and c.phase_receipts[0] is r and any(refs.get('phase_receipt') is r for event,facts,refs in p._history),'init phase not retained by original producer')
        cfg=self.config;values=w.binding.world_values
        _need(cfg.initial_state is values.initial_state and cfg.scene is values.scene and cfg.model is values.model and cfg.budget is values.budget and cfg.max_slices==l.executor._max_slices and cfg.actor_policy.run_id==l.native.run_id,'original authority configuration mismatch')
    def claim_for_factory(self,config,capability,chain):
        _need(not self._claim_attempted,'factory claim already attempted');self._claim_attempted=True
        try:
            self._check();_need(config is self.config and capability is self.link and chain is self.chain,'original factory inputs required')
            return OriginalG05FactoryRefs(self.world,self.source,self.link,self.book,self.projection,self.producer,self.chain,self.session,self.receipt,self.clock,self._legacy,self._c42,self._source_ref is not None)
        except BaseException:self._failed=True;raise
    def attach_source_config(self,original_config_ref):
        _need(not self._attach_attempted,'source config attachment already attempted');self._attach_attempted=True
        try:
            self._check();s=self.source;proj=self.projection._producer;stored=proj._config
            _need(s.source.state=='RUNNING' and s.source._clock is self.clock and s.source._origin is not None and self.book._origin==s.source._origin,'actual started source required')
            _need(type(stored) is tuple and len(stored)==2 and original_config_ref is not None and stored[0] is original_config_ref and type(stored[1]) is dict,'actual observed source config required')
            fields=stored[1];_need(_canonical(fields.get('context'))==self._c42_raw and type(fields.get('source_start_monotonic_ns')) is int and fields['source_start_monotonic_ns']==s.source._origin and fields.get('source_start_tick_ms')==0 and type(fields.get('source_start_tick_ms')) is int,'actual source origin/context mismatch')
            book_id=proj._id(self.book);binding_id=proj._id(self.link.binding)
            _need(type(book_id) is str and type(binding_id) is str and book_id!=binding_id and proj._id(original_config_ref) is not None,'original C42 identity bindings required')
            for key,val in (('pose_book_id',book_id),('owner_binding_id',binding_id)):
                if key in fields:_need(fields[key] is None or fields[key]==val,'source config binding mismatch')
            self._source_ref=original_config_ref;self._config_raw=_canonical(fields);self._stored_config=stored;self._stored_fields=fields;self._ids=(book_id,binding_id,proj._id(original_config_ref))
        except BaseException:self._failed=True;raise
    def check_source_config(self):
        try:
            self._check();_need(self._source_ref is not None,'source config not attached')
            stored=self.projection._producer._config
            _need(stored is self._stored_config and stored[0] is self._source_ref and stored[1] is self._stored_fields and _canonical(stored[1])==self._config_raw and self.source.source.state=='RUNNING' and self.source.source._origin==self.book._origin==stored[1]['source_start_monotonic_ns'] and self.source.source._clock is self.clock,'source config changed')
            _need((self.projection._producer._id(self.book),self.projection._producer._id(self.link.binding),self.projection._producer._id(self._source_ref))==self._ids,'C42 bindings lost')
            return self._source_ref
        except BaseException:self._failed=True;raise
