import io,unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from competition.deepeye.tools.diagnostic import functional50_ssh_a as m

class Tests(unittest.TestCase):
 def test_fixed_board_environment(self):
  s=SimpleNamespace(remote_python='/usr/local/share/pynq-venv/bin/python3',remote_script='/tmp/a.py',remote_plan='/tmp/a.json')
  self.assertEqual(m._remote_command(s),"/usr/bin/sudo -S -p '' /usr/bin/env BOARD=Pynq-Z2 XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python3 -I -B /tmp/a.py /tmp/a.json")
 def test_write_once_exact_and_unknown(self):
  class Pipe:
   def __init__(self,answer):self.answer=answer;self.writes=0;self.flushes=0
   def write(self,raw):self.writes+=1;return self.answer
   def flush(self):self.flushes+=1
  for answer in (None,0,2,True):
   p=Pipe(answer)
   with self.assertRaises(OSError):m._write_once(p,b'abc')
   self.assertEqual(p.writes,1);self.assertEqual(p.flushes,0)
  p=Pipe(3);m._write_once(p,b'abc');self.assertEqual((p.writes,p.flushes),(1,1))
 def test_short_write_latches_without_read_or_replay(self):
  class Sink:
   calls=0
   def write(self,raw):self.calls+=1;return 1
   def flush(self):raise AssertionError('short write must not flush')
  class Reader:
   def read(self,n):return b''
   def readline(self,n):raise AssertionError('short write must not read')
  p=SimpleNamespace(stdin=Sink(),stdout=Reader(),stderr=Reader(),poll=lambda:None)
  s=m.Session(m._SESSION_KEY,p,None,None)
  with self.assertRaises(OSError):s._call(b'abc',1_000_000_000)
  with self.assertRaises(ValueError):s._check()
  self.assertEqual(p.stdin.calls,1)
 def test_original_unknown_local_cleanup(self):
  class Handle:
   def __init__(self):self.closed=False
   def Close(self):self.closed=True
  class Proc:
   def __init__(self):self.stdin=io.BytesIO();self.stdout=io.BytesIO();self.stderr=io.BytesIO();self._handle=Handle();self.pid=123;self.returncode=None;self.kills=0
   def poll(self):return self.returncode
   def kill(self):self.kills+=1;self.returncode=1
   def wait(self,timeout):return self.returncode
  p=Proc();tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);s=m.Session(m._SESSION_KEY,p,None,Path(tmp.name));s._unknown=True
  r=s.cleanup_local(kill=True,timeout_seconds=1)
  self.assertTrue(r['wait_confirmed']);self.assertTrue(r['threads_stopped']);self.assertTrue(r['handle_closed']);self.assertFalse(r['remote_stopped']);self.assertEqual(p.kills,1)
  with self.assertRaises(ValueError):s._check()
  with self.assertRaises(ValueError):s.cleanup_local(kill=True,timeout_seconds=1)
if __name__=='__main__':unittest.main()
