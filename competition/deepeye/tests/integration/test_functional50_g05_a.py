import hashlib,json,unittest
from competition.deepeye.tools.diagnostic import functional50_g05_a as g

class Tests(unittest.TestCase):
 def test_exact_mapper_bounds(self):
  self.assertEqual(g._command((0,0,1,1,100,1,7),0,None),(0,0,1,1,100,1,7))
  self.assertEqual(g._command((0,0,1,0,100,1,7),0,None)[3],0)
  for words in ((15000,0,1,1,100,1,7),(1,0,1,0,100,1,7),(0,0,1,1,0,1,7),(0,0,1,1,100,0,7),(True,0,1,1,100,1,7)):
   with self.assertRaises(ValueError):g._command(words,0,None)
  with self.assertRaises(ValueError):g._command((0,0,1,1,100,1,7),1,1)
 def test_policy_binding(self):
  binding=dict(operation_id='op',request_sha256='a'*64,boot_id='boot',source_commit='b'*40,build_id='c'*32)
  p=dict(binding=binding,limits=dict(begin=1,commit=16,stop=1,latch=16,release=16,total_io=1000))
  p['policy_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  self.assertEqual(g._policy(json.dumps(p).encode(),binding)['limits']['commit'],16)
  p['limits']['begin']=2
  with self.assertRaises(ValueError):g._policy(json.dumps(p).encode(),binding)
 def test_scoped_software_state_machine(self):
  import tempfile,os
  from pathlib import Path
  from types import SimpleNamespace
  from unittest.mock import patch
  from competition.deepeye.tools.diagnostic import functional50_board_a as b
  class MockMMIO:
   def __init__(self,device):self.device=device;self.status=0;self.reg={};self.commands=[]
   def read(self,off):
    if off==8:return self.status
    if off==0x10:return 0
    if off==0x1c:return 1
    if off==0x300:return 1
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
  mmio=MockMMIO(device);reg=(device,None,None,None,None,None,os.getpid(),trace._mmio);b._G05_LOADS[trace]=reg;b._G05_CLAIMED.add(trace)
  self.addCleanup(b._G05_LOADS.pop,trace,None);self.addCleanup(b._G05_CLAIMED.discard,trace)
  with tempfile.TemporaryDirectory() as tmp, patch.object(g,'Path',return_value=SimpleNamespace(read_text=lambda:'testboot')):
   port=g.G05Port(g._KEY,trace,reg,mmio,Path(tmp),dict(binding={},policy_sha256='x',limits=dict(begin=1,commit=1,stop=1,latch=1,release=1,total_io=128)))
   port.stage_identity((1,0,0,0,0,0,0,0,2,0,0,0,7),'identity');port.begin('begin')
   port.stage_command((0,0,1,1,100,1,7),'stage');port.commit('commit');port.latch('latch')
   snap=port.read_snapshot('snapshot');self.assertEqual(snap['words'][30],7);self.assertFalse(snap['native_atomic_interval'])
   port.release('release');port.stop('stop');self.assertEqual(mmio.commands,[1,2,4,5,3])
   with self.assertRaises(ValueError):port.stop('newstop')
   self.assertTrue((Path(tmp)/'g05-00001-started.json').is_file())
   bad=MockMMIO(device)
   def failed_read(off):raise OSError('synthetic unknown')
   bad.read=failed_read
   second=Path(tmp)/'unknown';second.mkdir()
   q=g.G05Port(g._KEY,trace,reg,bad,second,dict(binding={},policy_sha256='y',limits=dict(begin=1,commit=1,stop=1,latch=1,release=1,total_io=128)))
   with self.assertRaises(OSError):q.read32(0,'once')
   with self.assertRaises(ValueError):q.stop('no-replay')
   self.assertTrue((second/'g05-00001-started.json').exists());self.assertFalse((second/'g05-00001-returned.json').exists())
 def test_no_forged_port(self):
  with self.assertRaises(ValueError):g.open_g05({},'not-a-policy')
 def test_status_bits(self):
  g._status_check(0,0,'new');g._status_check(1,0,'bound');g._status_check(0x21,0,'latched')
  for status,fault,mode in ((2,0,'new'),(1,1,'bound'),(1,0,'latched'),(0x80,0,'bound')):
   with self.assertRaises(ValueError):g._status_check(status,fault,mode)
if __name__=='__main__':unittest.main()
