"""Synthetic boundary controls only; no native or board operation."""
import json
import sys
import types
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
# Synthetic type identities only; these stubs never operate a native source.
def fake(name, *classes, **values):
 mod=types.ModuleType(name)
 for c in classes:setattr(mod,c,type(c,(),{}))
 mod.__dict__.update(values);return mod
names={
 'competition.deepeye.tools.run_causal_functional_chain':fake('competition.deepeye.tools.run_causal_functional_chain','FunctionalWorld','FunctionalSource'),
 'competition.deepeye.simulation.authority.actor_composition':fake('competition.deepeye.simulation.authority.actor_composition','AuthorityConfig'),
 'competition.deepeye.simulation.authority.original_world_actor_link':fake('competition.deepeye.simulation.authority.original_world_actor_link','_OriginalWorldActorLink'),
 'competition.deepeye.simulation.authority.root_source_book':fake('competition.deepeye.simulation.authority.root_source_book','RootSourceBook'),
 'competition.deepeye.simulation.authority.source_projection_v1.provider':fake('competition.deepeye.simulation.authority.source_projection_v1.provider','ProjectionSession'),
 'competition.deepeye.integration.host_clock':fake('competition.deepeye.integration.host_clock','QpcHostClock'),
 'competition.deepeye.tools.diagnostic.original_chain_receipt_producer_a':fake('competition.deepeye.tools.diagnostic.original_chain_receipt_producer_a','OriginalChainReceiptProducer'),
 'competition.deepeye.tools.diagnostic.functional50_chain_v2_client_a':fake('competition.deepeye.tools.diagnostic.functional50_chain_v2_client_a','ChainSessionV2','OriginalPhaseReceipt'),
 'competition.deepeye.tools.diagnostic.functional50_ssh_a':fake('competition.deepeye.tools.diagnostic.functional50_ssh_a',_original_session_origin=lambda x:None),
}
with patch.dict(sys.modules,names):
 from competition.deepeye.tools.diagnostic import original_g05_operation_binding_a as m

class Tests(unittest.TestCase):
 def setUp(self):
  self.legacy=dict(session=1,config_epoch=2,boot_sha256='a'*64,transport_profile_id=1,source_id=1,topology_id=1,acquisition_profile_id=1)
  self.c42=dict(operation_id='op',request_hash='b'*64,tested_commit='c'*40,build_manifest_sha256='d'*64,boot_id='b',session_id='s',tag=1,clock_domain_id='e'*32)
 def test_distinct_context_shapes_and_strict_values(self):
  m._validate_context(self.legacy,self.c42)
  self.c42['tag']=True
  with self.assertRaises(ValueError):m._validate_context(self.legacy,self.c42)
 def test_synthetic_original_identity_and_one_use_factory(self):
  w=m.FunctionalWorld();s=m.FunctionalSource();p=m.OriginalChainReceiptProducer();c=m.ChainSessionV2();link=m._OriginalWorldActorLink();book=m.RootSourceBook();view=m.ProjectionSession();clock=m.QpcHostClock();cfg=m.AuthorityConfig();r=m.OriginalPhaseReceipt()
  import threading
  tid=threading.get_ident();clock.metadata={'domain_id':self.c42['clock_domain_id']}
  bind=NS(world_values=NS(initial_state=object(),scene=object(),model=object(),budget=object()));owner=object();causal=NS(_source_book=book,state='NEW');native=NS(run_id='run');link._registered=lambda:None;link.book=book;link.owner=owner;link.binding=bind;link.source=causal;link.executor=NS(_max_slices=4);link.native=native
  for key in ('initial_state','scene','model','budget'):setattr(cfg,key,getattr(bind.world_values,key))
  cfg.max_slices=4;cfg.actor_policy=NS(run_id='run')
  sess=NS(_unknown=False,_closed=False,_dir=NS(name='op'));proc=object();sess._proc=proc;spec=NS(operation_id='op');streams=(object(),object(),object());ready=b'ready';origin=(spec,proc,clock,ready,None,0,1,*streams)
  w.source=s;w.owner=owner;w.binding=bind;w.clock=clock;w.operation_id='op';w._thread=tid
  s.owner=owner;s.binding=bind;s.clock=clock;s._thread=tid;s.link=link;s.book=book;s.session=view;s.source=causal
  view._owner=owner;view._link=link;view._book=book;view._check=lambda:None
  c.s=sess;c.clock=clock;c.thread=tid;c.phase_receipts=(r,)
  p._chain=c;p._world=w;p._source=s;p._book=book;p._session=sess;p._clock=clock;p._process=proc;p._origin=origin;p._check=lambda:None;p._history=[(None,None,{'phase_receipt':r})]
  for k,v in dict(owner=c,kind='init',phase_index=1,operation_id='op',status='COMPLETE',unknown=False,session=sess,process=proc,clock=clock,session_origin=origin,stdin=streams[0],stdout=streams[1],stderr=streams[2],spec=spec,ready_raw=ready,request_raw=b'q',response_raw=b'r',lower_qpc_ns=1,upper_qpc_ns=2).items():setattr(r,k,v)
  with patch.object(m,'_original_session_origin',lambda x:origin):
   result=m.OriginalG05OperationBinding(w,p,cfg,r,legacy_context=self.legacy,c42_context=self.c42)
   refs=result.claim_for_factory(cfg,link,c);self.assertIs(refs.init_receipt,r);self.assertFalse(refs.source_config_attached)
   with self.assertRaises(ValueError):result.claim_for_factory(cfg,link,c)
   self.c42['tag']=2
   with self.assertRaises(ValueError):result.check_source_config()
 def test_actual_observed_config_one_use_and_mutation(self):
  p=object.__new__(m.OriginalG05OperationBinding);clock=object();book=NS(_origin=123);binding=object();ref=object();fields=dict(context=self.c42,source_start_monotonic_ns=123,source_start_tick_ms=0)
  refs={id(book):'book',id(binding):'binding',id(ref):'config'}
  proj=NS(_config=(ref,fields),_id=lambda x:refs.get(id(x)))
  p._attach_attempted=False;p._failed=False;p._source_ref=None;p._c42_raw=m._canonical(self.c42);p.clock=clock;p.book=book;p.link=NS(binding=binding);p.source=NS(source=NS(state='RUNNING',_clock=clock,_origin=123));p.projection=NS(_producer=proj)
  with patch.object(m.OriginalG05OperationBinding,'_check',lambda self:None):
   p.attach_source_config(ref);self.assertIs(p.check_source_config(),ref)
   proj._config=(ref,dict(fields))
   with self.assertRaises(ValueError):p.check_source_config()
   self.assertTrue(p._failed)
 def test_refusal_does_not_attach(self):
  p=object.__new__(m.OriginalG05OperationBinding);p._attach_attempted=False;p._failed=False;p._source_ref=None
  p.source=NS(source=NS(state='NEW'));p.projection=NS(_producer=NS(_config=None))
  with patch.object(m.OriginalG05OperationBinding,'_check',lambda self:None):
   with self.assertRaises(ValueError):p.attach_source_config(object())
   self.assertTrue(p._failed);self.assertTrue(p._attach_attempted)
if __name__=='__main__':unittest.main()
