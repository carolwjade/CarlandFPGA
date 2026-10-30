import unittest
from competition.deepeye.tools.diagnostic import functional50_ssh_a as m

class Controls(unittest.TestCase):
 def test_response_exact(self):
  self.assertEqual(m._parse_response(b'{"id":"x","returned":0}\n','x','read'),0)
  self.assertIsNone(m._parse_response(b'{"id":"x","returned":null}\n','x','write'))
  for raw in (b'{"id":"y","returned":0}\n',b'{"id":"x","id":"x","returned":0}\n',b'{"id":"x","returned":true}\n',b'{"id":"x","returned":0}\nextra',b'{}\n'):
   with self.assertRaises(ValueError):m._parse_response(raw,'x','read')
 def test_remote_paths(self):
  self.assertEqual(m._remote_path('/opt/pynq/a-b.py'),'/opt/pynq/a-b.py')
  for bad in ('relative','/a/../b','/a x','/a;bad','/a\nb','//a'):
   with self.assertRaises(ValueError):m._remote_path(bad)
 def test_quota_and_identity(self):
  c=m._Quota();c.check('x','write',128,1)
  with self.assertRaises(ValueError):c.check('x','read',0,None)
  with self.assertRaises(ValueError):c.check('y','write',128,1)
  with self.assertRaises(ValueError):c.check('z','write',0,0)
 def test_timeout_latches_unknown(self):
  import threading,io
  class Output:
   def __init__(self):self.gate=threading.Event()
   def readline(self,n):self.gate.wait();return b''
  class Proc:
   def __init__(self):self.stdin=io.BytesIO();self.stdout=Output();self.stderr=io.BytesIO()
   def poll(self):return None
  p=Proc();s=m.Session(m._SESSION_KEY,p,None,None)
  with self.assertRaises(TimeoutError):s._call(b'{}\n',1_000_000)
  with self.assertRaises(ValueError):s._check()
  p.stdout.gate.set()
 def test_spec_is_frozen(self):
  import dataclasses
  self.assertTrue(m.SessionSpec.__dataclass_params__.frozen)
  with self.assertRaises(ValueError):m._parse_response(b'{"state":"ready","pid":true}\n',None,'ready')
if __name__=='__main__':unittest.main()
