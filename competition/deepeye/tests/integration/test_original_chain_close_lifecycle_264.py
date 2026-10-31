"""One synthetic selected-close lifecycle reproduction; no external process."""
import io,json,tempfile,time,unittest
from unittest.mock import patch
from competition.deepeye.tests.integration import test_original_chain_receipt_producer_a as base
from competition.deepeye.tools.diagnostic import functional50_chain_v2_client_a as client,functional50_ssh_a as ssh,original_chain_source_pump_a as pumpmod, original_chain_client_work_a as work
from competition.deepeye.integration.host_clock import QpcHostClock

class SelectedCloseLifecycle(unittest.TestCase):
 def exercise(self,exit_code=0,mode="normal",kind="close"):
  helper=base.Tests();self.addCleanup(helper.doCleanups)
  with tempfile.TemporaryDirectory(dir=OUT) as td:
   world,source,bundle,scanner,s,chain,clock=helper.fixture(td);s._threads=[];s._stderr_overflow=False;del s._check
   state={'exit':None,'response_read':False};s._proc.poll=lambda:state['exit'];s._proc.stdin=io.BytesIO()
   facts=dict(schema='g05_csr_session_v2',kind='close',operation_id='op',policy_sha256='a'*64,deadline_selected_lower_board_monotonic_ns=1,deadline_board_monotonic_ns=1001,phase_io_first=None,phase_io_last=None,identity_words=[1]*13,status=1,fault=0,capture=None,receipts=[dict(index=1,started_raw_hex='01',returned_raw_hex='02')],unresolved_receipts=[],state='CLOSED',authority='not_evaluated')
   raw=(json.dumps(dict(schema='functional50_chain_v2',id='phase-266',operation_id='op',kind=kind,status='COMPLETE',result=facts if kind=='close' else {},error=None,unknown=False),separators=(',',':'))+'\n').encode()
   class Reader:
    def readline(self,n):state['response_read']=True;state['exit']=exit_code;return b'' if mode=='eof' else raw
   s._proc.stdout=Reader();origin=list(ssh._SESSION_ORIGINS[s]);origin[7]=s._proc.stdin;origin[8]=s._proc.stdout;ssh._SESSION_ORIGINS[s]=tuple(origin);old=client._CHAIN_BINDINGS[chain];client._CHAIN_BINDINGS[chain]=(old[0],old[1],old[2],old[3],old[4],ssh._SESSION_ORIGINS[s]);chain.select_owner_work_v1();chain.sequence.initialized=True;chain.sequence.max_commands=2;chain.identity=(1,)*13;chain.deadline=(1,1001);chain.duration=1000;chain.policy_sha='a'*64;chain.receipts=[]
   pump=object.__new__(pumpmod.OriginalChainSourcePump);pump._enabled=True;pump._failed=False;pump._session=s;pump._clock=clock;pump._scanner=scanner;s._source_pump=pump
   def check_original_session(self,live,*,_closing=None):
    if _closing is None:self.session._check()
    else:self.session._check_closing(_closing)
   with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(QpcHostClock,'__call__',lambda _:time.monotonic_ns()),patch.object(pumpmod.OriginalChainSourcePump,'_check',check_original_session),patch.object(pumpmod.OriginalChainSourcePump,'poll_once',lambda *a,**k:None):
    with self.assertRaises(ValueError):s._check_closing(object())
    if mode=='normal' and exit_code==0 and kind=='close':
     out=chain.close('phase-266',stop=False,timeout_ns=1_000_000_000)
     self.assertTrue(state['response_read']);self.assertEqual(state['exit'],0);self.assertIs(out['phase_receipt'],chain.phase_receipts[-1]);self.assertEqual(out['phase_receipt'].response_raw,raw);self.assertTrue((chain.folder/'01-response.bin').exists());self.assertFalse(s._unknown);self.assertIsNone(work._closing_for(s));self.assertIs(out['phase_receipt'].source_pump,pump)
    else:
     with self.assertRaises(Exception):
      if kind=='close':chain.close('phase-266',stop=False,timeout_ns=1_000_000_000)
      else:chain._send('phase-266',kind,{},1_000_000_000)
     self.assertTrue(state['response_read']);self.assertTrue(s._unknown);self.assertEqual(len(chain.phase_receipts),0)
     if kind=='close':self.assertIsNone(work._closing_for(s));self.assertEqual(work._CLOSING[s].raw,b'' if mode=='eof' else raw)
     with self.assertRaises(Exception):chain._send('repeat-266',kind,{'stop':False} if kind=='close' else {},1_000_000_000)
 def test_complete_close_reply_followed_by_process_exit_keeps_original_phase(self):self.exercise()
 def test_nonzero_exit_is_unknown_and_cannot_replay(self):self.exercise(exit_code=5)
 def test_empty_reply_is_unknown_and_cannot_replay(self):self.exercise(mode='eof')
 def test_nonclose_exit_remains_rejected(self):self.exercise(kind='status')
if __name__=='__main__':
 import os
 from pathlib import Path
 OUT=Path(os.environ['A264_EVIDENCE']);ids=['__main__.SelectedCloseLifecycle.test_complete_close_reply_followed_by_process_exit_keeps_original_phase','__main__.SelectedCloseLifecycle.test_nonzero_exit_is_unknown_and_cannot_replay','__main__.SelectedCloseLifecycle.test_empty_reply_is_unknown_and_cannot_replay','__main__.SelectedCloseLifecycle.test_nonclose_exit_remains_rejected'];print('selected_test_ids:',*ids,flush=True);r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(ids));raise SystemExit(not r.wasSuccessful())
