"""New software-only prestart producer binding control."""
import json,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.run_causal_functional_chain import FunctionalWorld,FunctionalSource
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh,functional50_b131_loader as loader,functional50_chain_v2_client_a as chain_mod,functional50_chain_v2_board_a as protocol,original_source_trace_scan_a as scan_mod,original_chain_source_pump_a as pump_mod,original_chain_receipt_producer_a as prod

class Tests(unittest.TestCase):
 def test_deferred_scanner_and_pump_bind_without_start_or_admission(self):
  with tempfile.TemporaryDirectory() as tmp:
   clock=object.__new__(QpcHostClock);world=object.__new__(FunctionalWorld);source=object.__new__(FunctionalSource)
   world.clock=clock;world._thread=threading.get_ident();world.operation_id='op';world.source=source;world.owner=object();world.binding=object()
   book=types.SimpleNamespace(_samples=[],_origin=None,_active=None);pump_source=types.SimpleNamespace(state='NEW',_count=0,_origin=None,_source_book=book);book._source=pump_source
   source.clock=clock;source.owner=world.owner;source.binding=world.binding;source._thread=threading.get_ident();source.book=book;source.source=pump_source;source._retained_samples=[];source._start_attempted=False
   bundle=object.__new__(loader._Bundle);scanner=object.__new__(scan_mod.OriginalSourceTraceScan)
   for name,value in dict(_functional=source,_clock=clock,_bundle=bundle,_source=pump_source,_book=book,_thread=threading.get_ident(),_source_scan_cycle_v2=True,_defer_start=True,_activated=False,_activation_attempted=False,_origin=None,_ledger=None,_admitted=[],_prepared=False,_failed=False,_prepare_count=0).items():setattr(scanner,name,value)
   s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._clock=clock;s._proc=types.SimpleNamespace(stdin=object(),stdout=object(),stderr=object());s._dir=Path(tmp)/'op';s._unknown=False;s._closed=False;s._thread=threading.get_ident();s._check=lambda:None
   chain=object.__new__(chain_mod.ChainSessionV2);chain.s=s;chain.clock=clock;chain.bundle=bundle;chain.thread=threading.get_ident();chain.sequence=protocol.Sequence()
   spec=ssh.SessionSpec((),'/python','/script','/plan','C:/script','a'*64,tmp,'op','functional50_chain_v2','/manifest','b'*64,'/policy');ready=dict(schema='chain_board_v2',state='ready',operation_id='op',manifest_sha256='b'*64);origin=(spec,s._proc,clock,(json.dumps(ready)+'\n').encode(),ready,1,2,s._proc.stdin,s._proc.stdout,s._proc.stderr)
   pmp=object.__new__(pump_mod.OriginalChainSourcePump);pmp._session=s;pmp._source=source;pmp._scanner=scanner;pmp._clock=clock;pmp._enabled=False;pmp._failed=False
   with patch.dict(ssh._SESSION_ORIGINS,{s:origin}),patch.dict(ssh._SESSION_PUMPS,{}):
    p=prod.OriginalChainReceiptProducer(world,chain);p.bind_scanner(scanner);p.bind_pump(pmp)
    self.assertEqual(pump_source.state,'NEW');self.assertIsNone(pump_source._origin);self.assertIsNone(scanner._ledger);self.assertFalse(scanner._activated);self.assertFalse(pmp.enabled)
    with patch.object(scan_mod.OriginalSourceTraceScan,'admit') as admit:
     with self.assertRaises(ValueError):p.admit_source(object())
     admit.assert_not_called()
    with self.assertRaises(ValueError):p.enable_pump()
    source._start_attempted=True;pump_source.state='RUNNING';pump_source._origin=100;book._origin=100
    scanner._activated=True;scanner._activation_attempted=True;scanner._origin=100;scanner._ledger=object()
    with patch.object(pump_mod.OriginalChainSourcePump,'enable',lambda self:setattr(self,'_enabled',True)):
     p.enable_pump()
    self.assertTrue(pmp.enabled);self.assertEqual(pump_source._origin,100)
if __name__=='__main__':unittest.main()
