"""Explicit deadline controls with synthetic clocks; no native/SSH/board."""
import threading,types,unittest
from unittest.mock import patch
from competition.deepeye.integration.host_clock import QpcHostClock
from competition.deepeye.tools.diagnostic import original_source_trace_scan_a as scan, original_chain_receipt_producer_a as prod, original_chain_source_pump_a as pm, functional50_ssh_a as ssh

class Tests(unittest.TestCase):
 def scanner(self,now):
  s=object.__new__(scan.OriginalSourceTraceScan);s._thread=threading.get_ident();s._clock=object.__new__(QpcHostClock);s._source_scan_cycle_v2=True;s._preparing=False;s._prepare_count=0;s._failed=False;s._last_prepared_index=None;s._last_prepared_tick=None
  payload=object();entry={'payload':payload};rec=types.SimpleNamespace(adc_tick_ms=0,em_tick_ms=None);item={'entry':entry,'admission':types.SimpleNamespace(record=rec)};s._admitted=[item];s._functional=types.SimpleNamespace(_retained_samples=[entry]);s._book=types.SimpleNamespace(_samples=[object()],_active=None);s._source=types.SimpleNamespace(_count=1)
  return s,payload
 def selected_end(self,absolute):
  now=[100];s,payload=self.scanner(now);seen=[]
  def check(self):now[0]+=10
  def pump_check(self,pump):now[0]+=20
  def stop(self,pump,end):seen.append(end);raise RuntimeError('checkpoint reached')
  with patch.object(QpcHostClock,'__call__',lambda _:now[0]),patch.object(scan.OriginalSourceTraceScan,'_check',check),patch.object(scan.OriginalSourceTraceScan,'_work_original_pump',pump_check),patch.object(scan.OriginalSourceTraceScan,'_work_pump',stop):
   with self.assertRaisesRegex(RuntimeError,'checkpoint reached'):
    s.prepare_with_pump(payload,facts={},build_binding={},pump=object(),timeout_ns=100,deadline_qpc_ns=absolute)
  return seen,s,now
 def test_absolute_bound_survives_preparation_setup_delay(self):
  seen,s,now=self.selected_end(150);self.assertEqual(seen,[150]);self.assertEqual(now[0],130);self.assertEqual(s._prepare_count,1);self.assertTrue(s._failed)
 def test_optional_absolute_bound_cannot_extend_internal_cap(self):
  seen,s,now=self.selected_end(1000);self.assertEqual(seen,[200]);self.assertTrue(s._failed)
  seen,s,now=self.selected_end(None);self.assertEqual(seen,[200])
  for invalid in (True,-1,1<<63,100):
   s,payload=self.scanner([100])
   with patch.object(QpcHostClock,'__call__',return_value=100):
    with self.assertRaises(ValueError):s.prepare_with_pump(payload,facts={},build_binding={},pump=object(),timeout_ns=100,deadline_qpc_ns=invalid)
   self.assertEqual(s._prepare_count,0)
 def test_producer_captures_one_end_before_copy_and_preserves_unknown(self):
  now=[100];calls=[];p=object.__new__(prod.OriginalChainReceiptProducer);p._clock=object.__new__(QpcHostClock);p._failed=False;p._operation_count=0
  p._chain=types.SimpleNamespace(owner_work_v1=True,sequence=types.SimpleNamespace(ids=set()));p._scanner=object.__new__(scan.OriginalSourceTraceScan)
  payload=object();token=types.SimpleNamespace(_draft=object());item={'entry':{'payload':payload},'token':token,'draft':token._draft,'admission':object()};p._scanner._admitted=[item]
  session=object.__new__(ssh.Session);session._unknown=False;p._session=session
  pump=object.__new__(pm.OriginalChainSourcePump);pump._enabled=True;pump._failed=False;pump._session=session;pump._scanner=p._scanner;pump._clock=p._clock;p._source=object();p._source_pump=pump;session._source_pump=pump
  def qpc(_):calls.append('clock');return now[0]
  def copy_value(value):calls.append('copy');now[0]+=20;return value
  def stop(scanner,payload,**kw):calls.append(('prepare',kw.get('deadline_qpc_ns')));raise RuntimeError('synthetic stop')
  with patch.object(prod.OriginalChainReceiptProducer,'_check',lambda _:None),patch.object(prod.OriginalChainReceiptProducer,'_source_ready',lambda _:None),patch.object(prod.OriginalChainReceiptProducer,'_flush_pump',lambda _:None),patch.object(QpcHostClock,'__call__',qpc),patch.object(prod.copy,'deepcopy',copy_value),patch.object(scan.OriginalSourceTraceScan,'prepare_with_pump',stop),patch.dict(ssh._SESSION_PUMPS,{session:pump}):
   with self.assertRaisesRegex(RuntimeError,'synthetic stop'):p.scan_actual('id',payload,facts={},build_binding={},max_io=1,timeout_ns=100)
  self.assertEqual(calls[0],'clock');self.assertEqual(calls[-1],('prepare',200));self.assertTrue(p._failed);self.assertTrue(session._unknown)
if __name__=='__main__':unittest.main()
