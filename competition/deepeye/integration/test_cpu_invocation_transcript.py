"""New raw invocation controls; local OS pipes/journals, scripted clock seams.

No actual clock/capability query, CPU model, native actor or old TestCase runs.
"""
import importlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

NAME=__package__+'.cpu_invocation_transcript'
module=importlib.import_module(NAME) if importlib.util.find_spec(NAME) else None


class ScriptedClock:
    def __init__(self): self.value=100; self.actions=[]
    def __call__(self):
        if self.actions:
            value=self.actions.pop(0)
            if isinstance(value,BaseException): raise value
            self.value=value+1
            return value
        value=self.value; self.value+=1; return value


class HiddenInterrupt(BaseException): pass


class InvocationTranscriptTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(module,'bounded raw invocation transcript is absent')
        self.directory=tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name); self.instances=[]; self.witnesses={}
        self.input_reader,self.input_writer=os.pipe()
        self.output_reader,self.output_writer=os.pipe()
        for fd in (self.input_reader,self.output_reader): os.set_blocking(fd,False)
        for fd in (self.input_reader,self.input_writer,self.output_reader,self.output_writer):
            self.addCleanup(self.safe_close,fd)
        self.clock=ScriptedClock()
        seam=patch.object(module,'monotonic_ns',self.clock)
        seam.start(); self.addCleanup(seam.stop)
        self.identity=module.InvocationIdentity('new-cpu-raw','a'*64,'b'*40,'c'*64,
                                                 'new-run',1,'original-actor-label')

    @staticmethod
    def safe_close(fd):
        try: os.close(fd)
        except OSError: pass

    def make(self,**options):
        args=dict(request_raw=b'opaque\x00request',journal_path=self.root/f'invocation-{len(self.instances)}.jsonl',
                  max_output_bytes=32,max_reads=8,read_size=8)
        args.update(options)
        value=module.InvocationTranscript(self.input_writer,self.output_reader,self.identity,**args)
        self.instances.append((value,args['journal_path']))
        self.addCleanup(value.close)
        return value

    def tearDown(self):
        destination=os.environ.get('CPU_TRANSCRIPT_CONTROL_OUT')
        if destination:
            output=Path(destination)/self._testMethodName
            output.mkdir(parents=True,exist_ok=False)
            for index,(value,journal) in enumerate(self.instances):
                (output/f'snapshot-{index}.json').write_text(json.dumps(value.snapshot(),
                    sort_keys=True,indent=2)+'\n',encoding='utf-8')
                (output/journal.name).write_bytes(journal.read_bytes())
            for journal in self.root.glob('*.jsonl'):
                if not (output/journal.name).exists():
                    (output/journal.name).write_bytes(journal.read_bytes())
            (output/'test-seam-witnesses.json').write_text(json.dumps(self.witnesses,
                sort_keys=True,indent=2)+'\n',encoding='utf-8')

    def test_original_request_durable_marker_precedes_sole_write_and_raw_output_offsets(self):
        value=self.make(); original_write=os.write
        self.assertIsNone(value.snapshot()['host_time_high_water_ns'])
        def write(fd,raw):
            rows=[json.loads(line) for line in self.instances[0][1].read_bytes().splitlines()]
            self.assertEqual(rows[-1]['outcome'],'started_unknown')
            self.assertEqual(raw,b'opaque\x00request')
            return original_write(fd,raw)
        with patch.object(module.os,'write',side_effect=write): result=value.dispatch_once()
        self.assertEqual(result['bytes_written'],14)
        self.assertEqual(os.read(self.input_reader,32),b'opaque\x00request')
        os.write(self.output_writer,b'abc'); first=value.read_once()
        os.write(self.output_writer,b'def'); second=value.read_once()
        self.assertEqual((first['raw_hex'],second['raw_hex']),('616263','646566'))
        self.assertEqual((first['stream_start'],second['stream_start']),(0,3))
        self.assertEqual((first['read_index'],second['read_index']),(0,1))
        self.assertEqual(value.snapshot()['bytes_read'],6)
        with self.assertRaises(ValueError): value.dispatch_once()

    def test_partial_write_retires_without_remainder_or_output_read(self):
        value=self.make(); original=os.write
        with patch.object(module.os,'write',side_effect=lambda fd,raw:original(fd,raw[:2])):
            with self.assertRaises(OSError): value.dispatch_once()
        self.assertEqual(value.snapshot()['dispatch']['bytes_written'],2)
        self.assertEqual(os.read(self.input_reader,32),b'op')
        self.assertTrue(value.snapshot()['failed'])
        with self.assertRaises(ValueError): value.read_once()
        with self.assertRaises(ValueError): value.dispatch_once()

    def test_post_write_stamp_failure_preserves_actual_count_and_unknown_end(self):
        value=self.make(); self.clock.actions=[100,101,OSError('post-write stamp')]
        with self.assertRaises(OSError): value.dispatch_once()
        row=value.snapshot()['dispatch']
        self.assertEqual(row['bytes_written'],14)
        self.assertEqual(row['raw_write_call_bracket_ns'],[101,None])
        self.assertIsNone(row['write_call_interval_ns'])
        self.assertEqual(os.read(self.input_reader,32),b'opaque\x00request')
        with self.assertRaises(ValueError): value.read_once()
        with self.assertRaises(ValueError): value.dispatch_once()

    def test_write_interruption_after_hidden_bytes_keeps_count_null_and_never_repeats(self):
        value=self.make(); original=os.write
        def interrupted(fd,raw):
            count=original(fd,raw[:2]); self.witnesses['hidden_write_count_known_only_to_seam']=count
            raise HiddenInterrupt()
        with patch.object(module.os,'write',side_effect=interrupted):
            with self.assertRaises(HiddenInterrupt): value.dispatch_once()
        row=value.snapshot()['dispatch']
        self.assertIsNone(row['bytes_written']); self.assertTrue(row['write_attempted'])
        self.assertEqual(os.read(self.input_reader,32),b'op')
        with self.assertRaises(ValueError): value.dispatch_once()
        with self.assertRaises(ValueError): value.read_once()

    def test_read_interruption_after_hidden_consumption_preserves_unknown_attempt(self):
        value=self.make(); value.dispatch_once(); os.write(self.output_writer,b'abcdef')
        original=os.read
        def interrupted(fd,count):
            raw=original(fd,count); self.witnesses['hidden_consumed_hex_known_only_to_seam']=raw.hex()
            raise HiddenInterrupt()
        with patch.object(module.os,'read',side_effect=interrupted):
            with self.assertRaises(HiddenInterrupt): value.read_once()
        snapshot=value.snapshot(); row=snapshot['reads'][0]
        self.assertTrue(snapshot['failed']); self.assertEqual(snapshot['bytes_read'],0)
        self.assertIsNone(row['raw_hex']); self.assertIsNone(row['returned_bytes'])
        self.assertEqual(row['stream_start'],0)
        with patch.object(module.os,'read',side_effect=AssertionError('no second read')):
            with self.assertRaises(ValueError): value.read_once()

    def test_post_read_stamp_failure_or_regression_retains_returned_chunk(self):
        for bad in (OSError('post-read stamp'),99):
            with self.subTest(bad=repr(bad)):
                value=self.make(); value.dispatch_once(); os.write(self.output_writer,b'abc')
                self.clock.actions=[self.clock.value,bad]
                with self.assertRaises((OSError,ValueError)): value.read_once()
                row=value.snapshot()['reads'][0]
                self.assertEqual(row['raw_hex'],'616263'); self.assertEqual(row['returned_bytes'],3)
                self.assertEqual(value.snapshot()['bytes_read'],3)
                self.assertIsNone(row['raw_read_call_bracket_ns'][1])
                self.assertIsNone(row['availability_interval_ns'])
                with self.assertRaises(ValueError): value.read_once()

    def test_empty_eof_and_budgets_are_distinct_and_bound_actual_os_read(self):
        value=self.make(max_output_bytes=5,max_reads=2,read_size=3); value.dispatch_once()
        os.write(self.output_writer,b'abcdef')
        self.assertEqual(value.read_once()['returned_bytes'],3)
        self.assertEqual(value.read_once()['returned_bytes'],2)
        with self.assertRaises(ValueError): value.read_once()
        self.assertEqual(os.read(self.output_reader,8),b'f')
        value=self.make(max_reads=2); value.dispatch_once()
        self.assertEqual(value.read_once()['kind'],'empty')
        os.close(self.output_writer)
        self.assertEqual(value.read_once()['kind'],'eof')
        self.assertTrue(value.snapshot()['eof'])
        self.assertFalse(value.snapshot()['failed'])
        with self.assertRaises(ValueError): value.read_once()

    def test_prequeued_output_remains_raw_unknown_and_snapshot_is_detached(self):
        os.write(self.output_writer,b'READY old model_candidate')
        value=self.make(read_size=32); value.dispatch_once(); row=value.read_once()
        self.assertEqual(bytes.fromhex(row['raw_hex']),b'READY old model_candidate')
        snapshot=value.snapshot()
        for name in ('availability_interval_ns','sample_interval_ns','completion_interval_ns'):
            self.assertIsNone(snapshot[name]); self.assertIsNone(row[name])
        self.assertFalse(snapshot['authenticated']); self.assertFalse(snapshot['completion_verified'])
        snapshot['reads'][0]['raw_hex']='00'
        self.assertEqual(bytes.fromhex(value.snapshot()['reads'][0]['raw_hex']),b'READY old model_candidate')

    def test_marker_or_prewrite_stamp_and_journal_failure_allow_no_write_retry(self):
        for actions in ([OSError('marker')],[100,OSError('pre-write')]):
            with self.subTest(actions=repr(actions)):
                value=self.make(); self.clock.actions=actions
                with patch.object(module.os,'write',side_effect=AssertionError('no write')):
                    with self.assertRaises(OSError): value.dispatch_once()
                    with self.assertRaises(ValueError): value.dispatch_once()
                self.assertIsNone(value.snapshot()['dispatch']['bytes_written'])
        value=self.make()
        with patch.object(module.os,'fsync',side_effect=OSError('journal sync')),\
             patch.object(module.os,'write',side_effect=AssertionError('no write')):
            with self.assertRaises(OSError): value.dispatch_once()
        self.assertTrue(value.snapshot()['journal_failed'])
        with self.assertRaises(ValueError): value.read_once()

    def test_original_clock_domain_or_callable_cannot_be_replaced(self):
        from . import host_clock as clocks
        info=dict(implementation='QueryPerformanceCounter()',monotonic=True,adjustable=False,resolution=1e-7)
        with patch.object(clocks,'_qpc_capability',return_value=info),\
             patch.object(clocks,'_qpc_leaf',side_effect=self.clock):
            binding=clocks.qpc_clock_for_new_run(); value=self.make(host_clock=binding)
            self.assertIs(value.clock_domain,binding)
            value._clock_domain=clocks.qpc_clock_for_new_run()
            with self.assertRaises(ValueError): value.dispatch_once()
        value=self.make(); value._clock=lambda:0
        with self.assertRaises(ValueError): value.dispatch_once()
        with self.assertRaises(ValueError): self.make(host_clock=lambda:0)

    def test_foreign_and_caught_reentrant_calls_cannot_reopen_outer_io(self):
        value=self.make(); errors=[]
        def foreign():
            try: value.dispatch_once()
            except ValueError: errors.append(True)
        thread=threading.Thread(target=foreign); thread.start(); thread.join()
        self.assertEqual(errors,[True])
        with self.assertRaises(ValueError): value.dispatch_once()
        value=self.make(); value.dispatch_once(); os.write(self.output_writer,b'x'); original=os.read
        def reentrant(fd,count):
            try: value.read_once()
            except ValueError: pass
            return original(fd,count)
        with patch.object(module.os,'read',side_effect=reentrant):
            with self.assertRaises(ValueError): value.read_once()
        self.assertTrue(value.snapshot()['failed'])
        with self.assertRaises(ValueError): value.read_once()

    def test_replay_files_invalid_shapes_read_before_dispatch_and_close_duplicates_only(self):
        with tempfile.TemporaryFile() as stream:
            with self.assertRaises(ValueError):
                module.InvocationTranscript(stream.fileno(),self.output_reader,self.identity,
                    request_raw=b'x',journal_path=self.root/'bad.jsonl',max_output_bytes=3,max_reads=1,read_size=1)
        for options in (dict(request_raw=b''),dict(request_raw=bytearray(b'x')),
                        dict(max_output_bytes=True),dict(max_reads=0),dict(read_size=8193)):
            with self.subTest(options=repr(options)),self.assertRaises(ValueError): self.make(**options)
        with self.assertRaises(ValueError):
            module.InvocationIdentity('op','a'*64,'b'*40,'c'*64,'run',True,'actor')
        value=self.make()
        with self.assertRaises(ValueError): value.read_once()
        value.close(); value.close()
        os.write(self.input_writer,b'caller fd remains open')
        self.assertEqual(os.read(self.input_reader,32),b'caller fd remains open')
        self.assertTrue(value.snapshot()['closed'])
        with self.assertRaises(ValueError): value.dispatch_once()

    def test_existing_journal_is_never_reopened_and_constructor_attempts_each_owned_close_once(self):
        journal=self.root/'existing.jsonl'; journal.write_bytes(b'original journal\n')
        original_dup,original_close=os.dup,os.close
        duplicates=[]; closed=[]; captured=None
        def duplicate(fd):
            value=original_dup(fd); duplicates.append(value); return value
        def close(fd):
            closed.append(fd); original_close(fd)
            if len(closed)==1: raise OSError('first duplicate release outcome reported unknown')
        with patch.object(module.os,'dup',side_effect=duplicate),patch.object(module.os,'close',side_effect=close):
            try: self.make(journal_path=journal)
            except BaseException as error: captured=error
        for fd in duplicates:
            if fd not in closed: original_close(fd)
        self.assertIsInstance(captured,FileExistsError)
        self.assertEqual(closed,duplicates)
        self.assertEqual(journal.read_bytes(),b'original journal\n')

    def test_foreign_veto_after_final_checkpoint_never_reopens_next_io(self):
        value=self.make(); original=value._checkpoint; calls=[]
        def checkpoint(epoch):
            original(epoch); calls.append(True)
            if len(calls)==4:  # Explicit private seam immediately after the final dispatch check.
                def foreign():
                    try: value.snapshot()
                    except ValueError: pass
                thread=threading.Thread(target=foreign); thread.start(); thread.join()
        with patch.object(value,'_checkpoint',side_effect=checkpoint): value.dispatch_once()
        self.assertTrue(value.snapshot()['failed'])
        os.write(self.output_writer,b'x')
        with patch.object(module.os,'read',side_effect=AssertionError('permanent veto must reject before read')):
            with self.assertRaises(ValueError): value.read_once()
