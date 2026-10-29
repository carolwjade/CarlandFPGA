"""NEW causal exchange controls; synthetic board, no SSH/board/model execution."""
import copy
import importlib
import json
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_live_chain_candidate_channel import CTX, PROFILE, ORIGIN, ready, sample, capture, pl
from competition.deepeye.tools.diagnostic import run_private_pl_live as host
from competition.deepeye.simulation.authority import live_chain_channels as channels


class Clock:
    def __init__(self, step=1_000_000): self.value, self.step = ORIGIN, step
    def __call__(self):
        now = self.value; self.value += self.step; return now


class Pump:
    def __init__(self, clock, *, fail=False, quiet=False):
        self.clock, self.fail, self.quiet = clock, fail, quiet
        self.last = None; self.count = 0; self.state = 'RUNNING'; self.consecutive = 0
    def poll(self):
        if self.quiet: return None
        tick = (self.clock.value-ORIGIN)//10_000_000*10
        if tick == self.last: return None
        self.consecutive = self.consecutive+1 if self.last is not None and tick-self.last == 10 else 1
        self.last = tick; self.count += 1
        payload = sample(tick)
        if tick >= 50:
            payload['channel_values'][1] = 1.
            payload['channel_counts'][1] = 3071
        if self.consecutive >= 10:
            payload['channel_values'][3] = 0.
            payload['channel_counts'][3] = 0
            payload['quality'] |= 8
        if self.fail and self.count == 3: payload['quality'] = True
        return payload
    def retire(self, reason): self.state = 'RETIRED'


class Transport:
    def __init__(self, scans=2, *, bad=False, eof=False):
        self.scans, self.bad, self.eof = scans, bad, eof
        self.sent = []; self.pending = None; self.polls = 0; self.closes = 0
        self.last_returned = None
    def send_once(self, raw):
        if self.pending is not None: raise AssertionError('second pending write')
        self.sent.append(raw); self.pending = raw; self.polls = 0
    def poll_line(self):
        if self.pending is None: return None, False
        if self.eof: return None, True
        self.polls += 1
        if self.polls < 30: return None, False
        doc = capture(self.pending); self.pending = None
        if self.bad: doc['captures'][0]['ack_returned'] = False
        self.last_returned = pl.encode(doc)
        return self.last_returned, False
    def close_input(self): self.closes += 1
    def line(self, seconds):
        return pl.encode(pl.record('diagnostic_stopped', dict(CTX),
            cleanup=dict(attempted=True, confirmed=True, status=0, active_tag=0,
                         secondary_errors=[]), error=None,
            frames_completed=len(self.sent), movement_authorized=False))


class CausalExchangeTests(unittest.TestCase):
    def module(self):
        self.assertTrue((ROOT/'competition/deepeye/tools/diagnostic/causal_pl_exchange.py').exists(),
                        'NEW causal exchange missing: expected RED')
        return importlib.import_module('competition.deepeye.tools.diagnostic.causal_pl_exchange')
    def core(self, directory, *, bad=False, eof=False, fail_source=False, quiet=False):
        clock = Clock(step=100_000_000 if quiet else 1_000_000)
        owner = pl._HostOwner(dict(CTX), clock, max_age_ns=2_000_000_000,
                              functional_timing_profile=dict(PROFILE))
        channel = channels._CandidateChannel(owner, clock=clock,
            start_tick_ms=0, start_monotonic_ns=ORIGIN)
        channel.accept_ready(ready())
        transport = Transport(bad=bad, eof=eof)
        source = Pump(clock, fail=fail_source, quiet=quiet)
        return channel, transport, source, clock

    def test_profile_is_explicit_in_all_three_hash_bound_root_records(self):
        module = self.module()
        source = module.CausalSourcePump(lambda: None, lambda x, y, z: 1.)
        profile = copy.deepcopy(module.SOURCE_PROFILE)
        records = [dict(candidate_source_profile=copy.deepcopy(profile)) for _ in range(3)]
        self.assertTrue(module.select_source_mode(*records, source))
        self.assertFalse(module.select_source_mode({}, {}, {}, None))
        for index in range(3):
            bad = copy.deepcopy(records); bad[index].pop('candidate_source_profile')
            with self.subTest(index=index), self.assertRaises(ValueError): module.select_source_mode(*bad, source)
        for replacement in (None, {**profile, 'source_age_cap_ns': 100_000_001},
                            {**profile, 'session_max_ns': float(profile['session_max_ns'])}):
            bad = copy.deepcopy(records); bad[2]['candidate_source_profile'] = replacement
            with self.assertRaises(ValueError): module.select_source_mode(*bad, source)
        with self.assertRaises(ValueError): module.select_source_mode(*records, None)
        bad = copy.deepcopy(records); bad[2]['values'] = [1]*4
        with self.assertRaises(ValueError): module.select_source_mode(*bad, source)

    def test_new_samples_are_pumped_during_pending_and_replace_fixed_activation_values(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            channel, transport, source, clock = self.core(directory)
            result = module._exchange_causal_core(channel, transport, source,
                clock=clock, origin_ns=ORIGIN, scans=2, out=Path(directory))
            requests = [pl.decode(raw) for raw in transport.sent]
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[0]['values'][1], 2048)
            self.assertEqual(requests[1]['values'][1], 3071)
            self.assertGreater(source.count, 2)
            self.assertEqual([r['observation_identity']['request_seq'] for r in result['captures']], [1, 2])
            self.assertFalse(result['movement_authorized'])
            self.assertEqual(transport.closes, 1)
            self.assertEqual(source.state, 'RETIRED')

    def test_bad_capture_raw_is_saved_before_rejection_and_no_request_replayed(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            channel, transport, source, clock = self.core(directory, bad=True)
            with self.assertRaises(ValueError):
                module._exchange_causal_core(channel, transport, source,
                    clock=clock, origin_ns=ORIGIN, scans=2, out=Path(directory))
            self.assertEqual((Path(directory)/'causal-exchange/response-00.bin').read_bytes(), transport.last_returned)
            self.assertEqual(len(transport.sent), 1)
            self.assertEqual(channel._pending.request_raw, transport.sent[0])
            self.assertEqual(transport.closes, 1)

    def test_eof_or_bad_new_source_while_pending_stops_without_second_write(self):
        module = self.module()
        for mode in ('eof', 'source'):
            with tempfile.TemporaryDirectory() as directory:
                channel, transport, source, clock = self.core(directory,
                    eof=mode=='eof', fail_source=mode=='source')
                with self.assertRaises(ValueError):
                    module._exchange_causal_core(channel, transport, source,
                        clock=clock, origin_ns=ORIGIN, scans=2, out=Path(directory))
                self.assertEqual(len(transport.sent), 1)
                self.assertEqual(transport.closes, 1)
                self.assertEqual(source.state, 'RETIRED')
                self.assertIsNotNone(channel._pending)

    def test_no_source_has_a_finite_session_stop_and_does_not_send_constants(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            channel, transport, source, clock = self.core(directory, quiet=True)
            with self.assertRaises(TimeoutError):
                module._exchange_causal_core(channel, transport, source,
                    clock=clock, origin_ns=ORIGIN, scans=2, out=Path(directory))
            self.assertEqual(transport.sent, [])
            self.assertEqual(transport.closes, 1)

    def test_source_pump_never_backfills_missed_em_or_adc_slots(self):
        module = self.module()
        class Profile:
            def __init__(self): self.em = []; self.adc = []
            def acquire_em(self, tick, pose, **kw): self.em.append(tick)
            def sample_adc(self, tick, **kw):
                self.adc.append(tick)
                return types.SimpleNamespace(to_payload=lambda: {'tick': tick})
        profile = Profile(); clock = Clock(step=0)
        source = module._CausalSourcePump(profile, lambda: 'own-pose', lambda x, y, z: 1.)
        source.start(ORIGIN, clock)
        self.assertEqual(source.poll(), {'tick': 0})
        clock.value = ORIGIN+70_000_000
        self.assertEqual(source.poll(), {'tick': 70})
        self.assertIsNone(source.poll())
        clock.value = ORIGIN+100_000_000; source.poll()
        self.assertEqual(profile.em, [0, 100])
        self.assertEqual(profile.adc, [0, 70, 100])
        with self.assertRaises(ValueError): source.start(ORIGIN, clock)

    def test_history_close_failure_never_replaces_original_capture_rejection(self):
        module = self.module()
        real_open = Path.open
        class CloseFailure:
            def __init__(self, stream): self.stream = stream
            def write(self, raw): return self.stream.write(raw)
            def flush(self): return self.stream.flush()
            def fileno(self): return self.stream.fileno()
            def close(self):
                self.stream.close()
                raise OSError('NEW source history close failure')
        def open_with_close_failure(path, *args, **kwargs):
            stream = real_open(path, *args, **kwargs)
            return CloseFailure(stream) if path.name == 'source-history.jsonl' else stream
        with tempfile.TemporaryDirectory() as directory:
            channel, transport, source, clock = self.core(directory, bad=True)
            caught = None
            with patch.object(Path, 'open', open_with_close_failure):
                try:
                    module._exchange_causal_core(channel, transport, source,
                        clock=clock, origin_ns=ORIGIN, scans=2, out=Path(directory))
                except BaseException as error: caught = error
            self.assertIsInstance(caught, ValueError, 'close failure masked original rejection')
            self.assertIn('lane mismatch', str(caught))
            self.assertIn('history_close', str(caught._causal_exchange_secondary_errors))

    def test_actual_candidate_kernel_reads_current_root_pose_and_exports_only_signals(self):
        module = self.module()
        from competition.deepeye.simulation.sensors import forward_profile as forward
        poses = [forward.Pose((0., 0., 0.), (0., 0., 0., 1.)) for _ in range(2)]
        clocks = [Clock(step=0), Clock(step=0)]
        pumps = []
        for index in range(2):
            pump = module.CausalSourcePump(lambda index=index: poses[index],
                lambda x, y, z: 1. if z >= 5. else .01)
            # Equal seeded source noise is a counterfactual control only, never AI input.
            pump._profile = forward.ForwardProfile(em_rng=random.Random(17),
                                                   vibration_rng=random.Random(18))
            pump.prepare(); pump.start(ORIGIN, clocks[index]); pumps.append(pump)
        first = [pump.poll() for pump in pumps]
        self.assertEqual(first[0]['channel_counts'], first[1]['channel_counts'])
        poses[0] = forward.Pose((0., 0., 8.), (0., 0., 0., 1.))
        for clock in clocks: clock.value = ORIGIN+50_000_000
        second = [pump.poll() for pump in pumps]
        self.assertGreater(abs(second[0]['channel_counts'][0]-second[1]['channel_counts'][0]), 100)
        for payload in second:
            self.assertEqual(payload['em_tick_ms'], 50)
            self.assertEqual(payload['profile_status'], 'candidate_only')
            self.assertEqual(set(payload), {'profile_id','profile_status','profile_note','source_mode',
                'adc_tick_ms','em_tick_ms','channel_values','channel_counts','quality'})
        for pump in pumps: pump.retire('new kernel control completed')

    def test_startup_disk_sync_delay_precedes_real_source_origin_and_first_sample(self):
        module = self.module()
        clock = Clock(step=0)
        class Profile:
            def __init__(self): self.em = None
            def acquire_em(self, tick, pose, **kwargs): self.em = tick
            def sample_adc(self, tick, **kwargs):
                payload = sample(tick)
                if self.em is None:
                    payload = sample(tick, fault=True)
                else:
                    payload['em_tick_ms'] = self.em
                    payload['quality'] = 7 | (0x700 if self.em < tick else 0)
                return types.SimpleNamespace(to_payload=lambda: payload)
        class StartupTransport(Transport):
            def __init__(self): super().__init__(scans=1); self.ready_read = False
            def line(self, seconds):
                if not self.ready_read: self.ready_read = True; return ready()
                return super().line(seconds)
        source = module.CausalSourcePump(lambda: None, lambda x, y, z: 1.)
        source._profile = Profile()
        source.prepare()
        def fixture_channel(ctx, bound_clock, **kwargs):
            owner = pl._HostOwner(ctx, bound_clock, max_age_ns=2_000_000_000,
                                  functional_timing_profile=dict(PROFILE))
            return channels._CandidateChannel(owner, clock=bound_clock,
                start_tick_ms=0, start_monotonic_ns=kwargs['start_monotonic_ns'])
        def delayed_sync(fd): clock.value += 20_000_000
        with tempfile.TemporaryDirectory() as directory:
            # Component seams only; no claim that this clock/board is native.
            with patch.object(module.clocks, '_require_binding', lambda value: value), \
                    patch.object(module.clocks, 'QpcHostClock', Clock), \
                    patch.object(module.channels, 'LiveFourChannelChannel', fixture_channel), \
                    patch.object(module.os, 'fsync', delayed_sync):
                result = module.exchange_causal(dict(CTX), clock, StartupTransport(), source,
                    scans=1, out=Path(directory), functional_timing_profile=dict(PROFILE))
            rows = [json.loads(line) for line in
                    (Path(directory)/'causal-exchange/source-history.jsonl').read_text().splitlines()]
            self.assertEqual(rows[0]['adc_tick_ms'], 0)
            self.assertEqual(rows[0]['em_tick_ms'], 0)
            self.assertGreaterEqual(result['source_origin_ns'], ORIGIN+20_000_000)

    def test_public_exchange_refuses_component_clock_before_any_transport_or_source_start(self):
        module = self.module()
        source = module.CausalSourcePump(lambda: None, lambda x, y, z: 1.)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            module.exchange_causal(dict(CTX), Clock(), Transport(), source,
                scans=2, out=Path(directory), functional_timing_profile=dict(PROFILE))

    def test_nonblocking_poll_reads_real_original_pipe_then_distinguishes_actual_eof(self):
        self.assertTrue(callable(getattr(host._Transport, 'poll_line', None)),
                        'NEW nonblocking original pipe poll missing: expected RED')
        self.assertEqual(os.name, 'nt', 'this NEW native pipe control requires Windows')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            process = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c',
                "import time;time.sleep(.03);print('fresh',flush=True)"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW)
            transport = object.__new__(host._Transport)
            transport.clock = lambda: 0; transport.process = process
            transport.buffer = bytearray(); transport.stdout_count = transport.stderr_count = 0
            transport.stdout_log = (out/'stdout.bin').open('xb')
            transport.stderr_log = (out/'stderr.bin').open('xb')
            try:
                first = transport.poll_line()
                self.assertIn(first, ((None, False), (b'fresh\r\n', False), (b'fresh\n', False)))
                process.wait(timeout=3)
                result = first if first[0] is not None else transport.poll_line()
                self.assertIn(result[0], (b'fresh\r\n', b'fresh\n'))
                self.assertFalse(result[1])
                self.assertEqual(transport.poll_line(), (None, True))
                self.assertEqual(process.returncode, 0)
            finally:
                if process.poll() is None: process.kill(); process.wait(timeout=3)
                for stream in (process.stdout, process.stderr): stream.close()
                process._handle.Close()
                transport.stdout_log.close(); transport.stderr_log.close()


if __name__ == '__main__': unittest.main(verbosity=2)
