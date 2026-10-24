"""Typed native pipe observations; no actor, authority, model or providers."""
from dataclasses import FrozenInstanceError
import importlib
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

try:
    pr=importlib.import_module('competition.deepeye.simulation.isolation.pipe_read')
except ModuleNotFoundError as error:
    if error.name!='competition.deepeye.simulation.isolation.pipe_read':raise
    pr=None

NATIVE_EVIDENCE=[]

def failure(code):
    error=OSError('controlled native error');error.winerror=code;return error

class PipeReadTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(pr,'typed pipe-read component is absent')

    def native_stub(self,available=5,result=b'abc',peek_error=None,read_error=None):
        from competition.deepeye.simulation.isolation import win32 as w
        def peek(*args):
            if peek_error is not None:w.C.set_last_error(peek_error);return 0
            w.C.cast(args[4],w.C.POINTER(w.W.DWORD))[0]=available;return 1
        return SimpleNamespace(C=w.C,W=w.W,PeekNamedPipe=Mock(side_effect=peek),
            read=Mock(side_effect=read_error) if read_error else Mock(return_value=result))

    def test_invalid_arguments_reject_before_any_native_access(self):
        class Integer(int):pass
        too_big=1<<(8*struct.calcsize('P'))
        with patch.object(pr,'_native',side_effect=AssertionError('native reached')) as native:
            for handle in [True,False,0,-1,None,'1',1.,Integer(1),too_big]:
                with self.subTest(handle=handle),self.assertRaises(ValueError):pr.poll_output(handle)
            for maximum in [True,False,0,-1,8193,None,'3',3.,Integer(3)]:
                with self.subTest(maximum=maximum),self.assertRaises(ValueError):pr.poll_output(1,maximum)
        self.assertEqual(native.call_count,0)

    def test_open_empty_has_one_peek_and_no_read(self):
        w=self.native_stub(available=0)
        with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1)
        self.assertEqual((result.state,result.data),('empty',b''))
        self.assertEqual(w.PeekNamedPipe.call_count,1);self.assertEqual(w.read.call_count,0)

    def test_data_reads_once_with_caller_cap(self):
        w=self.native_stub(available=20)
        with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1,3)
        self.assertEqual((result.state,result.data),('data',b'abc'))
        w.read.assert_called_once_with(1,3);self.assertEqual(w.PeekNamedPipe.call_count,1)

    def test_default_8192_and_available_count_both_bound_read(self):
        for available,maximum,expected in [(10000,8192,8192),(2,8192,2),(3,8192,3)]:
            with self.subTest(available=available):
                w=self.native_stub(available=available,result=b'x'*expected)
                with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1,maximum)
                self.assertEqual(len(result.data),expected);w.read.assert_called_once_with(1,expected)
                self.assertEqual(w.PeekNamedPipe.call_count,1)

    def test_peek_broken_pipe_is_eof_without_read(self):
        w=self.native_stub(peek_error=109)
        with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1)
        self.assertEqual((result.state,result.data),('eof',b''));self.assertEqual(w.read.call_count,0)
        self.assertEqual(w.PeekNamedPipe.call_count,1)

    def test_read_broken_pipe_race_is_eof(self):
        w=self.native_stub(read_error=failure(109))
        with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1)
        self.assertEqual((result.state,result.data),('eof',b''))
        w.read.assert_called_once_with(1,5);self.assertEqual(w.PeekNamedPipe.call_count,1)

    def test_other_peek_errors_and_other_read_errors_propagate(self):
        for code in [5,6,232]:
            with self.subTest(operation='peek',code=code):
                w=self.native_stub(peek_error=code)
                with patch.object(pr,'_native',return_value=w),self.assertRaises(OSError) as caught:pr.poll_output(1)
                self.assertEqual(caught.exception.winerror,code);self.assertEqual(w.read.call_count,0)
            with self.subTest(operation='read',code=code):
                original=failure(code);w=self.native_stub(read_error=original)
                with patch.object(pr,'_native',return_value=w),self.assertRaises(OSError) as caught:pr.poll_output(1)
                self.assertIs(caught.exception,original);w.read.assert_called_once_with(1,5)
        original=OSError(109,'errno alone is not Win32 broken-pipe evidence')
        w=self.native_stub(read_error=original)
        with patch.object(pr,'_native',return_value=w),self.assertRaises(OSError) as caught:pr.poll_output(1)
        self.assertIs(caught.exception,original)

    def test_zero_oversized_and_type_invalid_read_refuse(self):
        class Bytes(bytes):pass
        for raw in [b'',b'abcd',None,'abc',bytearray(b'abc'),Bytes(b'abc')]:
            with self.subTest(raw=repr(raw)):
                w=self.native_stub(result=raw)
                with patch.object(pr,'_native',return_value=w),self.assertRaises(ValueError):pr.poll_output(1,3)
                w.read.assert_called_once_with(1,3);self.assertEqual(w.PeekNamedPipe.call_count,1)

    def test_result_is_plain_immutable_diagnostic(self):
        w=self.native_stub()
        with patch.object(pr,'_native',return_value=w):result=pr.poll_output(1)
        self.assertEqual(set(result.__dict__),{'state','data'})
        with self.assertRaises(FrozenInstanceError):result.state='eof'

    def open_pipe(self):
        from competition.deepeye.simulation.isolation import win32 as w
        event={'test':self.id(),'events':[]};NATIVE_EVIDENCE.append(event)
        live={}
        def own_pair(*records):
            for label,handle,_ in records:
                value=handle.value if isinstance(handle,w.W.HANDLE) else handle
                self.assertIs(type(value),int)
                live[label]=value;event['events'].append({'created':label,'original_handle':value})
        owner=SimpleNamespace(own_pair=own_pair)
        reader,writer=w.pipe(owner=owner,read_label='read',write_label='write')
        def close(label):
            handle=live.pop(label) # One attempt only, before native action.
            okay=bool(w.CloseHandle(handle));event['events'].append({'closed':label,'original_handle':handle,'success':okay})
            if not okay:raise w.C.WinError(w.C.get_last_error(),'CloseHandle')
        def cleanup():
            failures=[]
            for label in tuple(live):
                try:close(label)
                except OSError as error:failures.append(error)
            event['cleanup_complete']=not live and not failures
            if failures:raise failures[0]
        self.addCleanup(cleanup)
        return w,reader,writer,close,event

    def test_real_pipe_empty_exact_partial_data_then_last_writer_close_eof(self):
        w,reader,writer,close,event=self.open_pipe()
        def poll():
            with patch.object(w,'PeekNamedPipe',wraps=w.PeekNamedPipe) as peek,patch.object(w,'ReadFile',wraps=w.ReadFile) as read:
                result=pr.poll_output(reader,3)
            event['events'].append({'state':result.state,'data_hex':result.data.hex(),'peek_calls':peek.call_count,'read_calls':read.call_count})
            self.assertEqual(peek.call_count,1);self.assertLessEqual(read.call_count,1)
            return result
        self.assertEqual(poll().state,'empty')
        payload=b'abcdefghij' # 10 bytes, below the requested 16384-byte capacity.
        w.write(writer,payload);event['events'].append({'write_bytes':len(payload),'payload_hex':payload.hex()})
        parts=[poll() for _ in range(4)]
        self.assertEqual([r.state for r in parts],['data']*4)
        self.assertEqual([r.data for r in parts],[b'abc',b'def',b'ghi',b'j'])
        self.assertEqual(poll().state,'empty')
        close('write')
        self.assertEqual(poll().state,'eof')

    def test_real_pipe_buffered_data_precedes_eof_after_writer_close(self):
        w,reader,writer,close,event=self.open_pipe()
        w.write(writer,b'xy');event['events'].append({'write_bytes':2,'payload_hex':'7879'})
        close('write')
        first=pr.poll_output(reader);last=pr.poll_output(reader)
        event['events'] += [{'state':first.state,'data_hex':first.data.hex()},{'state':last.state,'data_hex':last.data.hex()}]
        self.assertEqual((first.state,first.data),('data',b'xy'))
        self.assertEqual((last.state,last.data),('eof',b''))

    def test_real_closed_read_handle_is_error6_without_handle_reuse(self):
        w,reader,writer,close,event=self.open_pipe()
        close('read')
        # No intervening kernel handle creation or lookup before this call.
        with self.assertRaises(OSError) as caught:pr.poll_output(reader)
        event['events'].append({'closed_read_error':caught.exception.winerror,'no_intervening_handle_creation':True})
        self.assertEqual(caught.exception.winerror,6)

if __name__=='__main__':unittest.main()
