import unittest
from competition.deepeye.tools.diagnostic import functional50_g05_transaction_a as t

class Controls(unittest.TestCase):
 def test_bounds(self):
  x=t.Limits(max_commands=2,max_polls=10,duration_ns=1000);self.assertEqual(x.max_commands,2)
  for kw in (dict(max_commands=17,max_polls=1,duration_ns=1),dict(max_commands=True,max_polls=1,duration_ns=1),dict(max_commands=1,max_polls=0,duration_ns=1),dict(max_commands=1,max_polls=1,duration_ns=0)):
   with self.assertRaises(ValueError):t.Limits(**kw)
 def test_forged_ports_refused(self):
  with self.assertRaises(ValueError):t.TransactionIssuer({}, {}, t.Limits(1,1,1))
 def test_deadline_once(self):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  from competition.deepeye.tools.diagnostic import functional50_g05_a as g
  p=object.__new__(g.G05Port);p._check=lambda:None;p._deadline_ns=None;p._failed=False
  with tempfile.TemporaryDirectory() as d, patch.object(g.time,'monotonic_ns',side_effect=[1,2]):
   p._dir=Path(d);p._bind_deadline(g._DEADLINE_KEY,100)
   with self.assertRaises(ValueError):p._bind_deadline(g._DEADLINE_KEY,200)
 def test_started_crosses_deadline_no_mmio(self):
  import tempfile,os
  from pathlib import Path
  from unittest.mock import patch
  from types import SimpleNamespace
  from competition.deepeye.tools.diagnostic import functional50_g05_a as g
  p=object.__new__(g.G05Port);p._check=lambda:None;p._deadline_ns=100;p._count=0;p._failed=False;p._pid=os.getpid();p._policy={'limits':{'total_io':2}}
  class M:
   def read(self,*args):raise AssertionError('expired call reached MMIO')
  p._mmio=M()
  with tempfile.TemporaryDirectory() as d, patch.object(g.time,'monotonic_ns',side_effect=[99,100]):
   p._dir=Path(d)
   with self.assertRaises(TimeoutError):p._io('read',0,None,'op')
   self.assertTrue(p._failed);self.assertTrue((Path(d)/'g05-00001-not-attempted.json').exists());self.assertFalse((Path(d)/'g05-00001-returned.json').exists())
 def test_normal_synthetic_original_ports(self):
  import tempfile,os,threading
  from pathlib import Path
  from types import SimpleNamespace
  from unittest.mock import patch
  from competition.deepeye.tools.diagnostic import functional50_board_a as b
  from competition.deepeye.tools.diagnostic import functional50_g05_a as g
  class MMIO:
   def __init__(self,device):self.device=device;self.status=0;self.reg={};self.commands=[]
   def read(self,off):
    if off==8:return self.status
    if off==0x10:return 0
    if off==0x1c:return 1
    if off==0x300:return 1
    if off==0x304:return 1
    if off==0x308:return 7
    if off==0x30c:return 9876
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
  device=object();trace=object.__new__(b._TracePort);trace._pid=os.getpid();trace._boot='testboot';trace._failed=False;trace._mmio=SimpleNamespace(device=device)
  reg=(device,None,None,(('operation_id','op207'),),None,None,os.getpid(),trace._mmio,threading.get_ident())
  b._G05_LOADS[trace]=reg;b._G05_CLAIMED.add(trace)
  self.addCleanup(b._G05_LOADS.pop,trace,None);self.addCleanup(b._G05_CLAIMED.discard,trace);self.addCleanup(b._G05_PORTS.pop,trace,None)
  with tempfile.TemporaryDirectory() as tmp,patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'testboot')):
   mmio=MMIO(device);p=g.G05Port(g._KEY,trace,reg,mmio,Path(tmp),dict(binding={},policy_sha256='a'*64,limits=dict(begin=1,commit=1,stop=1,latch=1,release=1,total_io=512)))
   b._G05_PORTS[trace]=p;issuer=t.TransactionIssuer(trace,p,t.Limits(1,3,10_000_000_000));self.addCleanup(t._ISSUERS.pop,p,None)
   facts=issuer.run((1,0,0,0,0,0,0,0,2,0,0,0,7),((0,0,1,1,100,1,7),),stop=True)
   self.assertEqual(facts.identity_words[12],7);self.assertEqual(facts.captures[0].words32[3],9876)
   self.assertEqual(facts.stop_status,2);self.assertEqual(mmio.commands,[1,2,4,5,3]);self.assertTrue(facts.receipts)
   self.assertEqual(facts.authority,'not_evaluated')
   with self.assertRaises(ValueError):issuer.run((1,)*13,((0,0,1,1,100,1,7),))
 def test_default_does_not_send_stop(self):
  import tempfile
  from pathlib import Path
  from types import SimpleNamespace
  from unittest.mock import patch
  ident=(1,0,0,0,0,0,0,0,2,0,0,0,7);calls=[]
  x=object.__new__(t.TransactionIssuer);x._check=lambda:None;x._issued=False;x.operation_id='op';x.policy_sha256='a'*64;x._receipts=[];x.limits=t.Limits(1,2,1_000_000_000)
  x.port=SimpleNamespace(_policy={'limits':dict(begin=1,commit=1,stop=0,latch=1,release=1)},_count=0,_bind_deadline=lambda *a:None)
  def step(name,*args):
   calls.append(name)
   if name=='read32':
    off=args[0]
    if 0x100<=off<=0x130:return ident[(off-0x100)//4]
    return 0x11 if off==8 else 0
   if name=='read_snapshot':
    words=[0]*32;words[1]=1;words[2]=7
    return dict(words=tuple(words),status_before=0x21,status_after=0x21,result_seq=1)
  x._step=step
  with tempfile.TemporaryDirectory() as d:
   x.directory=Path(d);facts=x.run(ident,((0,0,1,1,100,1,7),))
  self.assertNotIn('stop',calls);self.assertIsNone(facts.stop_status);self.assertIsNone(facts.stop_fault)
 def test_immutable_and_no_authority(self):
  import dataclasses
  self.assertTrue(dataclasses.is_dataclass(t.TransactionFacts))
  self.assertTrue(t.TransactionFacts.__dataclass_params__.frozen)
if __name__=='__main__':unittest.main()
