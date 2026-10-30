import sys, threading, types, unittest
from unittest.mock import patch

def module(name, **attrs):
    m=types.ModuleType(name);m.__dict__.update(attrs);return m
class Clock: pass
class World: pass
worldmod=module("competition.deepeye.simulation.authority._world_loop",_RootWorldOwner=World,_RETAINED=[])
class Session:
    def _check(self):
        if self._unknown or self._closed or threading.get_ident()!=self._thread: raise ValueError("session")
class Source:
    def _check_thread(self):
        if threading.get_ident()!=self._thread: raise ValueError("thread")
    def poll_sample(self):
        self.calls+=1
        if self.fail: raise RuntimeError("poll failed")
        return self.pair
    def _retained_sample(self,p): return self.entry
    def release_sample(self,p):
        self.releases+=1
        if getattr(self,'release_fail',False): raise RuntimeError("release failed")
class Scanner:
    def _check(self): pass
    def admit(self,p):
        if self.fail: raise RuntimeError("admit failed")
        self._admitted.append(dict(entry=self._functional.entry,token=self._functional.pair[1],draft=self._functional.pair[1]._draft,received=5,admission=self.admission))
        return self.admission
mods={
 'competition.deepeye.simulation.authority._world_loop':worldmod,
 'competition.deepeye.tools.run_causal_functional_chain':module('competition.deepeye.tools.run_causal_functional_chain',FunctionalSource=Source),
 'competition.deepeye.tools.diagnostic.original_source_trace_scan_a':module('competition.deepeye.tools.diagnostic.original_source_trace_scan_a',OriginalSourceTraceScan=Scanner),
 'competition.deepeye.tools.diagnostic.functional50_ssh_a':module('competition.deepeye.tools.diagnostic.functional50_ssh_a',Session=Session),
 'competition.deepeye.integration.host_clock':module('competition.deepeye.integration.host_clock',QpcHostClock=Clock)}
with patch.dict(sys.modules,mods):
 from competition.deepeye.tools.diagnostic.original_chain_source_pump_a import OriginalChainSourcePump

class Tests(unittest.TestCase):
 def fixture(self):
    c=Clock();s=Session();s._clock=c;s._thread=threading.get_ident();s._unknown=s._closed=False;s._protocol='functional50_chain_v2'
    f=Source();f.clock=c;f._thread=s._thread;f.calls=f.releases=0;f.fail=False;f._start_attempted=True
    f.source=types.SimpleNamespace(state='RUNNING',_clock=c);f.book=object();f.owner=World();f.owner._clock=c;f.binding=object();f.owner._binding=f.binding;worldmod._RETAINED.append(f.owner)
    tok=types.SimpleNamespace(_draft={'source_count':1});p=object();f.pair=(p,tok);f.entry={'payload':p,'token':tok,'raw':b'raw','book':f.book}
    a=Scanner();a._functional=f;a._source=f.source;a._book=f.book;a._clock=c;a._thread=s._thread;a._source_scan_cycle_v2=True;a._admitted=[];a.fail=False;a.admission=object()
    return s,f,a,OriginalChainSourcePump(s,f,a)
 def test_disabled_and_success(self):
    s,f,a,p=self.fixture();self.assertIsNone(p.poll_once(s));self.assertEqual(f.calls,0);p.enable();self.assertIs(p.poll_once(s),a.admission);self.assertEqual(f.releases,1);h=p.history[0];self.assertIs(h.payload,f.pair[0]);self.assertIs(h.token,f.pair[1]);self.assertIs(h.draft,f.pair[1]._draft);self.assertIs(h.admission,a.admission);self.assertEqual(h.received_qpc_ns,5);self.assertTrue(h.released)
 def test_failure_no_retry(self):
    s,f,a,p=self.fixture();p.enable();a.fail=True
    with self.assertRaisesRegex(RuntimeError,'admit failed'):p.poll_once(s)
    self.assertIs(p.pending[0],f.pair);self.assertEqual(f.releases,0)
    with self.assertRaises(ValueError):p.poll_once(s)
    self.assertEqual(f.calls,1)
 def test_release_failure_retains_admission(self):
    s,f,a,p=self.fixture();p.enable();f.release_fail=True
    with self.assertRaisesRegex(RuntimeError,'release failed'):p.poll_once(s)
    self.assertFalse(p.history[0].released);self.assertIs(p.history[0].admission,a.admission);self.assertTrue(p.failed)
    with self.assertRaises(ValueError):p.poll_once(s)
    self.assertEqual(f.releases,1)
 def test_identity_and_thread(self):
    s,f,a,p=self.fixture();p.enable();s._clock=Clock()
    with self.assertRaises(ValueError):p.poll_once(s)
    s,f,a,p=self.fixture();p.enable();errors=[]
    def other():
        try:p.poll_once(s)
        except Exception as e:errors.append(e)
    t=threading.Thread(target=other);t.start();t.join();self.assertEqual(len(errors),1);self.assertEqual(f.calls,0)
if __name__=='__main__':unittest.main()
