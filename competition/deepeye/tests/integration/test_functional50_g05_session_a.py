import os,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from competition.deepeye.tools.diagnostic import functional50_board_a as b
from competition.deepeye.tools.diagnostic import functional50_g05_a as g
from competition.deepeye.tools.diagnostic import functional50_g05_transaction_a as t
from competition.deepeye.tools.diagnostic import functional50_g05_session_a as s

IDENTITY=(1,0,0,0,0,0,0,0,2,0,0,0,7)
class MemoryMMIO:
 def __init__(self,device):self.device=device;self.status=0;self.reg={};self.commands=[]
 def read(self,off):
  if off==8:return self.status
  if off==0x10:return 0
  if off in (0x1c,0x300,0x304):return self.reg.get(0x214,0)
  if off==0x308:return self.reg.get(0x218,0)
  if off==0x30c:return 123456
  if off==0x378:return 7
  if off==0x37c:return 0x47303550
  return self.reg.get(off,0)
 def write(self,off,val):
  self.reg[off]=val
  if off==0x00c:
   self.commands.append(val)
   if val==1:self.status=1
   elif val==2:self.reg[0x14]=self.reg[0x214];self.status=0x11
   elif val==4:self.status=0x21
   elif val==5:self.status=1
   elif val==3:self.status=2

class Controls(unittest.TestCase):
 def fixture(self,polls=64):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);path=Path(tmp.name)
  device=object();trace=object.__new__(b._TracePort);trace._pid=os.getpid();trace._boot='boot';trace._failed=False;trace._mmio=SimpleNamespace(device=device)
  reg=(device,None,None,(('operation_id','op216'),),None,None,os.getpid(),trace._mmio,threading.get_ident())
  b._G05_LOADS[trace]=reg;b._G05_CLAIMED.add(trace);self.addCleanup(b._G05_LOADS.pop,trace,None);self.addCleanup(b._G05_CLAIMED.discard,trace);self.addCleanup(b._G05_PORTS.pop,trace,None)
  mmio=MemoryMMIO(device);port=g.G05Port(g._KEY,trace,reg,mmio,path,dict(binding={},policy_sha256='a'*64,limits=dict(begin=1,commit=2,stop=1,latch=2,release=2,total_io=512)));b._G05_PORTS[trace]=port
  issuer=t.TransactionIssuer(trace,port,t.Limits(2,polls,10_000_000_000));self.addCleanup(t._ISSUERS.pop,port,None)
  return issuer,mmio
 def test_init_then_two_real_boundary_steps(self):
  with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
   issuer,mmio=self.fixture();session=s.G05SessionV2(issuer);self.addCleanup(s._SESSIONS.pop,issuer,None)
   start=session.init(IDENTITY);self.assertEqual(start.kind,'init');self.assertEqual(start.identity_words,IDENTITY);self.assertEqual(mmio.commands,[1])
   first=session.apply_one((0,0,1,1,100,1,7));self.assertEqual(first.capture.words32[3],123456);self.assertEqual(first.kind,'apply')
   with self.assertRaises(ValueError):session.apply_one((0,0,1,1,100,1,7))
   second=session.apply_one((0,0,1,1,100,2,8));self.assertEqual(second.capture.words32[1:3],(2,8))
   status=session.observe_status();self.assertEqual(status.identity_words,IDENTITY);end=session.close();self.assertEqual(end.kind,'close');self.assertNotIn(3,mmio.commands)
   self.assertEqual((start.deadline_board_monotonic_ns,first.deadline_board_monotonic_ns,second.deadline_board_monotonic_ns),(issuer._deadline,)*3)
   self.assertTrue(all(r.started_raw and r.returned_raw for r in second.receipts))
 def test_explicit_stop_once(self):
  with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
   issuer,mmio=self.fixture();session=s.G05SessionV2(issuer);self.addCleanup(s._SESSIONS.pop,issuer,None);session.init(IDENTITY)
   result=session.close(stop=True);self.assertEqual((result.status,result.fault),(2,0));self.assertEqual(mmio.commands,[1,3])
   with self.assertRaises(ValueError):session.close(stop=True)
 def test_status_budget_rejects_before_command(self):
  with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
   issuer,mmio=self.fixture(polls=4);session=s.G05SessionV2(issuer);self.addCleanup(s._SESSIONS.pop,issuer,None);session.init(IDENTITY)
   with self.assertRaises(ValueError):session.apply_one((0,0,1,1,100,1,7))
   self.assertEqual(mmio.commands,[1]);self.assertEqual(session.close().state,'CLOSED')
 def test_partial_io_retained_after_unknown(self):
  with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
   issuer,mmio=self.fixture();session=s.G05SessionV2(issuer);self.addCleanup(s._SESSIONS.pop,issuer,None);session.init(IDENTITY)
   def unknown_read(off):raise OSError('synthetic unknown')
   mmio.read=unknown_read
   with self.assertRaises(OSError):session.observe_status()
   with self.assertRaises(ValueError):session.close(stop=True)
   facts=session.close();self.assertEqual(facts.state,'CLOSED_AFTER_FAILURE');self.assertTrue(facts.unresolved_receipts)
   last=facts.unresolved_receipts[-1];self.assertIsNotNone(last.started_raw);self.assertIsNone(last.returned_raw);self.assertNotIn(3,mmio.commands)
 def test_expired_no_replay_or_stop(self):
  with patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'boot')):
   issuer,mmio=self.fixture();session=s.G05SessionV2(issuer);self.addCleanup(s._SESSIONS.pop,issuer,None);session.init(IDENTITY)
   with patch.object(s.time,'monotonic_ns',return_value=issuer._deadline):
    with self.assertRaises((ValueError,TimeoutError)):session.apply_one((0,0,1,1,100,1,7))
    with self.assertRaises(ValueError):session.close(stop=True)
   self.assertEqual(mmio.commands,[1])
if __name__=='__main__':unittest.main()
