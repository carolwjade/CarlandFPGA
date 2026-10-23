"""New QPC controls only; private leaf seams are synthetic, OS pipes are real."""
import importlib
import importlib.util
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from . import live_board_receipts as receipts
from . import boot_transcript as transcript
from . import test_live_board_receipts as receipt_fixture
from . import test_boot_transcript as boot_fixture

NAME = __package__+'.host_clock'
clock = importlib.import_module(NAME) if importlib.util.find_spec(NAME) else None


class QpcHostClockTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(clock,'fixed QPC new-run binding is missing')
        self.ledgers=[]

    def tearDown(self):
        destination=os.environ.get('QPC_CONTROL_OUT')
        if destination:
            output=Path(destination)/type(self).__name__/self._testMethodName
            output.mkdir(parents=True,exist_ok=False)
            for index,ledger in enumerate(self.ledgers):
                (output/f'ledger-{index}.json').write_text(
                    json.dumps(ledger.snapshot(),sort_keys=True,indent=2)+'\n',encoding='utf-8')

    def pipe(self,binding=None):
        reader,writer = os.pipe(); os.set_blocking(reader,False)
        self.addCleanup(os.close,reader); self.addCleanup(os.close,writer)
        ledger = receipts.ReceiptLedger(reader,receipts.CaptureIdentity(
            'new-qpc-control','a'*64,'b'*40,'c'*64,1),
            max_bytes=4096,max_reads=8,host_clock=binding)
        self.addCleanup(ledger.close)
        self.ledgers.append(ledger)
        return ledger,writer

    def test_binding_raw_domain_unknown_interval_and_no_callable_constructor(self):
        binding = clock.qpc_clock_for_new_run()
        sample = binding.read_sample()
        self.assertIs(type(binding),clock.QpcHostClock)
        self.assertIs(sample.clock_domain,binding)
        self.assertIsNone(sample.interval_ns)
        self.assertLessEqual(sample.raw_ns,binding())
        self.assertEqual(binding.metadata['implementation'],'QueryPerformanceCounter()')
        self.assertIsNone(binding.metadata['timestamp_uncertainty_ns'])
        with self.assertRaises(TypeError): binding.metadata['resolution_seconds']=0
        with self.assertRaises((TypeError,ValueError)): clock.QpcHostClock(lambda:123)
        with self.assertRaises(TypeError): clock.qpc_clock_for_new_run(now=123)

    def test_bad_leaf_regression_and_foreign_thread_permanently_fail(self):
        for values in ([10,9],[True],[-1],[1<<63]):
            with self.subTest(values=values),patch.object(clock,'_qpc_leaf',side_effect=values):
                binding = clock.qpc_clock_for_new_run()
                if values==[10,9]: self.assertEqual(binding(),10)
                with self.assertRaises(ValueError): binding()
                with self.assertRaises(ValueError): binding()
        binding = clock.qpc_clock_for_new_run(); errors=[]
        def foreign():
            try: binding()
            except ValueError: errors.append(True)
        thread=threading.Thread(target=foreign); thread.start(); thread.join()
        self.assertEqual(errors,[True])
        with self.assertRaises(ValueError): binding()

    def test_wrong_capability_has_no_automatic_fallback(self):
        with patch.object(clock,'_qpc_capability',return_value=dict(
                implementation='GetTickCount64()',monotonic=True,adjustable=False,resolution=1e-7)):
            with self.assertRaises(ValueError): clock.qpc_clock_for_new_run()

    def test_real_pipe_raw_brackets_do_not_fill_unknown_availability(self):
        binding=clock.qpc_clock_for_new_run(); ledger,writer=self.pipe(binding)
        self.assertIs(ledger.clock_domain,binding)
        ledger.read_once(); raw=receipt_fixture.packet(); os.write(writer,raw)
        event,=ledger.read_once(); snapshot=ledger.snapshot()
        self.assertEqual(event.raw,raw)
        self.assertIsNone(event.availability_interval_ns)
        self.assertIsNone(snapshot['reads'][1]['read_call_interval_ns'])
        bracket=snapshot['reads'][1]['raw_read_call_bracket_ns']
        self.assertLessEqual(bracket[0],bracket[1])
        self.assertIsNone(snapshot['host_clock']['timestamp_uncertainty_ns'])
        with self.assertRaises(ValueError):
            ledger.claim_board_response(event,context=receipt_fixture.LiveBoardReceiptTests.context())

    def test_post_read_stamp_failure_preserves_chunk_offsets_budget_and_no_extra_read(self):
        binding=clock.qpc_clock_for_new_run(); ledger,writer=self.pipe(binding)
        raw=receipt_fixture.packet(); os.write(writer,raw)
        with patch.object(clock,'_qpc_leaf',side_effect=[100,OSError('post-read clock')]):
            with self.assertRaises(OSError): ledger.read_once()
        snap=ledger.snapshot()
        self.assertTrue(snap['failed']); self.assertEqual(snap['bytes_read'],len(raw))
        self.assertEqual(snap['reads'][0]['raw_hex'],raw.hex())
        self.assertEqual(snap['reads'][0]['stream_start'],0)
        self.assertEqual(snap['reads'][0]['raw_read_call_bracket_ns'],[100,None])
        self.assertIsNone(snap['reads'][0]['read_call_interval_ns'])
        os.write(writer,b'x')
        with patch.object(receipts.os,'read',side_effect=AssertionError('no second read')):
            with self.assertRaises(ValueError): ledger.read_once()
        with self.assertRaises(ValueError): ledger.claim_board_response(None,context={})

    def test_ledger_rejects_callable_and_legacy_default_stays_monotonic(self):
        reader,writer=os.pipe(); self.addCleanup(os.close,reader); self.addCleanup(os.close,writer)
        identity=receipts.CaptureIdentity('new-legacy','a'*64,'b'*40,'c'*64,1)
        with self.assertRaises(ValueError): receipts.ReceiptLedger(reader,identity,max_bytes=32,
                                                                 max_reads=1,host_clock=lambda:0)
        ledger,writer=self.pipe(); self.assertIsNone(ledger.clock_domain)
        self.assertIs(ledger._clock,receipts.monotonic_ns)
        ledger.read_once(); os.write(writer,receipt_fixture.packet())
        event,=ledger.read_once(); self.assertIsNotNone(event.availability_interval_ns)

    def test_replacing_ledger_domain_or_callable_retires_before_os_read(self):
        for replace_domain in (True,False):
            binding=clock.qpc_clock_for_new_run(); ledger,_=self.pipe(binding)
            if replace_domain: ledger._clock_domain=clock.qpc_clock_for_new_run()
            else: ledger._clock=lambda:0
            with self.subTest(domain=replace_domain),\
                 patch.object(receipts.os,'read',side_effect=AssertionError('mixing must stop before read')):
                with self.assertRaises(ValueError): ledger.read_once()
            self.assertTrue(ledger.snapshot()['failed'])

    def test_post_read_regressed_stamp_preserves_returned_bytes(self):
        binding=clock.qpc_clock_for_new_run(); ledger,writer=self.pipe(binding)
        os.write(writer,b'original')
        with patch.object(clock,'_qpc_leaf',side_effect=[100,99]):
            with self.assertRaises(ValueError): ledger.read_once()
        row=ledger.snapshot()
        self.assertTrue(row['failed']); self.assertEqual(row['bytes_read'],8)
        self.assertEqual(row['reads'][0]['raw_hex'],b'original'.hex())
        self.assertEqual(row['reads'][0]['raw_read_call_bracket_ns'],[100,None])


class QpcBootClockTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(clock,'fixed QPC new-run binding is missing')
        # Fixture construction only, no old TestCase method is executed.
        self.fixture=boot_fixture.BootTranscriptTests()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)

    def tearDown(self):
        destination=os.environ.get('QPC_CONTROL_OUT')
        if destination:
            output=Path(destination)/type(self).__name__/self._testMethodName
            output.mkdir(parents=True,exist_ok=False)
            (output/'ledger.json').write_text(json.dumps(self.fixture.ledger.snapshot(),
                sort_keys=True,indent=2)+'\n',encoding='utf-8')
            for index,sender in enumerate(self.fixture.instances):
                (output/f'sender-{index}.json').write_text(json.dumps(sender.snapshot(),
                    sort_keys=True,indent=2)+'\n',encoding='utf-8')
            for journal in Path(self.fixture.directory.name).glob('*.jsonl'):
                (output/journal.name).write_bytes(journal.read_bytes())

    def make(self):
        binding=clock.qpc_clock_for_new_run()
        self.fixture.ledger.close()
        self.fixture.ledger=receipts.ReceiptLedger(self.fixture.in_reader,self.fixture.identity,
            max_bytes=4096,max_reads=20,host_clock=binding)
        self.addCleanup(self.fixture.ledger.close)
        sender=self.fixture.make()
        return binding,sender

    def test_boot_inherits_exact_ledger_domain_real_write_and_unknown_interval(self):
        binding,sender=self.make()
        self.assertIs(sender.clock_domain,binding); self.assertIs(sender._clock,binding)
        result=sender.send_once()
        self.assertEqual(result['bytes_written'],len(sender._request))
        self.assertEqual(os.read(self.fixture.out_reader,4096),sender._request)
        self.assertIsNone(result['write_call_interval_ns'])
        self.assertLessEqual(*result['raw_write_call_bracket_ns'])
        with self.assertRaises(ValueError): sender.send_once()

    def test_post_write_stamp_failure_keeps_count_started_unknown_and_once_write(self):
        _,sender=self.make()
        with patch.object(clock,'_qpc_leaf',side_effect=[100,101,OSError('post-write clock')]):
            with self.assertRaises(OSError): sender.send_once()
        attempt=sender.snapshot()['attempt']
        self.assertEqual(attempt['bytes_written'],len(sender._request))
        self.assertEqual(attempt['raw_write_call_bracket_ns'],[101,None])
        self.assertIsNone(attempt['write_call_interval_ns'])
        self.assertEqual(os.read(self.fixture.out_reader,4096),sender._request)
        self.assertIn('started_unknown',self.fixture.args['journal_path'].read_text(encoding='utf-8'))
        with patch.object(transcript.os,'write',side_effect=AssertionError('no second write')):
            with self.assertRaises(ValueError): sender.send_once()

    def test_same_domain_ack_raw_order_is_diagnostic_with_unknown_availability(self):
        _,sender=self.make(); sender.send_once()
        os.read(self.fixture.out_reader,4096)
        os.write(self.fixture.in_writer,boot_fixture.ack_for(sender._request))
        event,=self.fixture.ledger.read_once()
        result=sender.check_ack(event)
        self.assertTrue(result['echo']['ok'])
        self.assertIsNone(result['availability_interval_ns'])
        self.assertIsNone(result['read_call_intervals_ns'])
        self.assertFalse(result['authenticated']); self.assertFalse(result['motion_authorized'])

    def test_before_write_stamp_failure_reserves_attempt_without_write(self):
        _,sender=self.make()
        with patch.object(clock,'_qpc_leaf',side_effect=[100,OSError('pre-write clock')]),\
             patch.object(transcript.os,'write',side_effect=AssertionError('must not write')):
            with self.assertRaises(OSError): sender.send_once()
            with self.assertRaises(ValueError): sender.send_once()
        self.assertIsNone(sender.snapshot()['attempt']['bytes_written'])

    def test_initial_marker_stamp_failure_cannot_start_a_later_write(self):
        _,sender=self.make()
        with patch.object(clock,'_qpc_leaf',side_effect=OSError('marker clock')),\
             patch.object(transcript.os,'write',side_effect=AssertionError('must not write')):
            with self.assertRaises(OSError): sender.send_once()
            with self.assertRaises(ValueError): sender.send_once()
        self.assertIsNone(sender.snapshot()['attempt']['bytes_written'])

    def test_second_binding_cannot_replace_original_ledger_clock(self):
        _,sender=self.make(); other=clock.qpc_clock_for_new_run()
        self.fixture.ledger._clock_domain=other
        with self.assertRaises(ValueError): sender.send_once()
