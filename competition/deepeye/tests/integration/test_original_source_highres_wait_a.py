"""New pump wait controls using synthetic streams and QPC; no board/source."""
import io,threading,types,unittest
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.diagnostic import functional50_ssh_a as ssh, original_chain_source_pump_a as pm

class Tests(unittest.TestCase):
 def fixture(self):
  unblock=threading.Event();entered=threading.Event()
  class Reader:
   def readline(self,n):entered.set();unblock.wait(2);return b'reply\n'
  s=object.__new__(ssh.Session);s._protocol='functional50_chain_v2';s._thread=threading.get_ident();s._clock=object.__new__(QpcHostClock);s._proc=types.SimpleNamespace(stdin=io.BytesIO(),stdout=Reader());s._threads=[];s._unknown=False
  pump=object.__new__(pm.OriginalChainSourcePump);pump._session=s;pump._clock=s._clock;pump._enabled=True;pump._failed=False;s._source_pump=pump
  return s,pump,unblock,entered
 def test_fixed_qpc_deadline_and_original_owner_poll(self):
  s,pump,unblock,entered=self.fixture();now=[0];polls=[];sleeps=[];owner=threading.get_ident()
  def poll(p,session):
   polls.append(threading.get_ident());unblock.set()
  def sleep(seconds):
   sleeps.append(seconds);now[0]+=500_000;entered.wait(1);threading.Event().wait(.001)
  with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(QpcHostClock,'__call__',lambda _:now[0]),patch.object(pm.OriginalChainSourcePump,'poll_once',poll),patch.object(ssh.time,'sleep',sleep):
   self.assertEqual(s._call(b'one\n',5_000_000),b'reply\n')
  self.assertTrue(polls);self.assertTrue(all(x==owner for x in polls));self.assertTrue(all(0<x<=.001 for x in sleeps));self.assertEqual(s._proc.stdin.getvalue(),b'one\n')
 def test_timeout_is_not_renewed_and_retains_pending_thread(self):
  s,pump,unblock,entered=self.fixture();now=[0];polls=[];sleeps=[]
  def poll(p,session):polls.append(now[0])
  def sleep(seconds):sleeps.append(seconds);entered.wait(1);now[0]+=750_000
  try:
   with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(QpcHostClock,'__call__',lambda _:now[0]),patch.object(pm.OriginalChainSourcePump,'poll_once',poll),patch.object(ssh.time,'sleep',sleep):
    with self.assertRaises(TimeoutError):s._call(b'once\n',2_000_000)
   self.assertTrue(s._unknown);self.assertEqual(s._proc.stdin.getvalue(),b'once\n');self.assertEqual(len(s._threads),1);self.assertTrue(s._threads[0].is_alive());self.assertEqual(polls,[0,750_000,1_500_000]);self.assertEqual(sleeps,[.001,.001,.0005])
  finally:unblock.set();s._threads[0].join(1)
 def test_default_path_does_not_use_pump_or_qpc_sleep(self):
  s,pump,unblock,entered=self.fixture();del s._source_pump;unblock.set()
  with patch.object(QpcHostClock,'__call__',side_effect=AssertionError('QPC pump path')),patch.object(ssh.time,'sleep',side_effect=AssertionError('sleep pump path')):
   self.assertEqual(s._call(b'legacy\n',1_000_000_000),b'reply\n')
 def test_source_error_keeps_original_pending_io_and_stops(self):
  s,pump,unblock,entered=self.fixture();now=[0]
  def fail(p,session):entered.wait(1);raise RuntimeError('synthetic source error')
  try:
   with patch.dict(ssh._SESSION_PUMPS,{s:pump}),patch.object(QpcHostClock,'__call__',lambda _:now[0]),patch.object(pm.OriginalChainSourcePump,'poll_once',fail):
    with self.assertRaisesRegex(RuntimeError,'synthetic source error'):s._call(b'only\n',2_000_000)
   self.assertTrue(s._unknown);self.assertEqual(s._proc.stdin.getvalue(),b'only\n');self.assertEqual(len(s._threads),1);self.assertTrue(s._threads[0].is_alive())
  finally:unblock.set();s._threads[0].join(1)
if __name__=='__main__':unittest.main()
