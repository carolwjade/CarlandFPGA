"""NEW software-only claimed-host/world controls; no main, QPC factory or I/O."""
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT),
    'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.local/deepeye-host-deps']
from competition.deepeye.integration import host_clock, private_pl_stream as pl
from competition.deepeye.simulation.authority import _world_loop as loop
from competition.deepeye.simulation.authority import root_world_service as services
from competition.deepeye.simulation.sensors.owned_world_field import OwnedWorldField
from competition.deepeye.tools.diagnostic import causal_pl_exchange as causal
from competition.deepeye.tools.diagnostic import run_private_pl_live as host


CONTEXT = dict(operation_id='new-software-claimed-world', request_hash='a'*64,
    tested_commit='b'*40, build_manifest_sha256='c'*64,
    boot_id='software-fixture-only', session_id='software-fixture-only',
    tag=1, clock_domain_id='d'*32)


class Clock:
    software_fixture_only = True
    def __init__(self): self.now = 1_000_000_000
    def _check(self): pass
    def __call__(self): return self.now


class World:
    software_fixture_only = True
    _known_binding = loop._RootWorldOwner._known_binding
    _known_epoch = loop._RootWorldOwner._known_epoch
    def __init__(self, clock):
        self._test, self._clock, self._thread = True, clock, threading.get_ident()
        self._foreign = threading.Event()
        self._busy, self._vetoed, self._initialized = False, False, True
        self._native = SimpleNamespace(clock_binding=clock,
            _containment_deadline=45_000_000_000, _retired=False, state='AUTHENTICATED')
        scene = SimpleNamespace(scene_id='software-scene', digest='software-digest')
        root = SimpleNamespace(world_invalid=False, phase=SimpleNamespace(
            context=SimpleNamespace(run_id='software-run', epoch=1)))
        self.executor = SimpleNamespace(_scene=scene, _world_binding='software-binding',
                                        authority_snapshot=lambda: root)
        self._epoch = loop._FrozenEpoch(self, 1, 'software-freeze', {}, b'', None, 0)
        self._epochs, self._retired_epochs = {id(self._epoch): self._epoch}, set()
        self._binding = loop._Binding(self, self._epoch,
            SimpleNamespace(scene=scene), self.executor, 0, 1)
        self._bindings = {id(self._binding): self._binding}
        self.events, self.hook = [], None
    def poll(self):
        self.events.append('world')
        if self.hook is not None: self.hook()
        return 'BOUND_STOPPED'


def fixture():
    """Distinct software service; no production/native capability is made."""
    clock = Clock(); world = World(clock)
    field = object.__new__(OwnedWorldField)
    for name, value in dict(_executor=world.executor, _scene=world.executor._scene,
            _scene_id='software-scene', _scene_digest='software-digest',
            _binding='software-binding', _run='software-run', _epoch=1,
            _retired=False).items(): setattr(field, name, value)
    source = causal.CausalSourcePump(field.pose_reader, field.sample_sigma)
    service = services._software_service_for_test(clock, world, source)
    if type(service) is services.RootWorldService:
        raise AssertionError('software fixture must never create production service')
    return SimpleNamespace(software_only=True, clock=clock, world=world,
                           source=source, service=service)


class Transport:
    software_fixture_only = True
    def __init__(self, f, replies=()):
        self.f, self.replies, self.sent = f, list(replies), []
        self.polls = self.closes = self.blocking_calls = 0
    def poll_line(self):
        self.polls += 1; self.f.world.events.append('transport')
        if self.replies:
            value = self.replies.pop(0)
            if callable(value): return value()
            return value, False
        self.f.clock.now += 1_000_000
        return None, False
    def line(self, seconds):
        self.blocking_calls += 1
        raise AssertionError('world mode must not block original world service')
    def send_once(self, raw):
        self.f.world.events.append('send'); self.sent.append(raw)
    def close_input(self): self.closes += 1


class Channel:
    software_fixture_only = True
    def __init__(self, f):
        self.f, self.state, self.requests = f, 'READY', 0
        self._owner = SimpleNamespace(context=CONTEXT, _age=100_000_000)
        self._pending = None; self._start_ns = f.clock.now; self.admitted = []
        self.request_hook = None
    def admit_sample(self, payload): self.admitted.append(payload)
    def _source_ns(self, tick): return self._start_ns+tick*1_000_000
    def next_request(self):
        self.requests += 1; self.f.world.events.append('request')
        if self.request_hook is not None: self.request_hook()
        self.state = 'PENDING'
        raw = pl.encode(dict(original_host_qpc_ns=[self.f.clock.now]*4))
        self._pending = SimpleNamespace(record=SimpleNamespace(adc_tick_ms=0,
            em_tick_ms=0), request_raw=raw)
        return raw
    def accept_capture(self, raw):
        self.state = 'READY'
        return dict(observation_identity=dict(capture_sha256='e'*64))
    def retire(self, reason): self.state = 'RETIRED'


class ClaimedHostWorldTests(unittest.TestCase):
    def call_core(self, f, transport, channel, out, **kwargs):
        # This private seam is explicitly software_only. It does not call the
        # public clock/service admission or manufacture a native-positive run.
        self.assertTrue(f.software_only)
        if f.source.state == 'NEW': f.source.start(f.clock.now, f.clock)
        return causal._exchange_causal_core(channel, transport, f.source,
            clock=f.clock, origin_ns=f.clock.now, scans=1, out=out,
            _world_service=f.service, **kwargs)

    def test_claimed_entry_rejects_software_clock_without_reclaim_or_transport(self):
        run = getattr(host, '_run_claimed', None)
        self.assertTrue(callable(run), 'already-claimed entry is missing')
        f = fixture()
        with tempfile.TemporaryDirectory() as out, \
                patch.object(host, '_claim', side_effect=AssertionError('second claim')), \
                patch.object(host_clock, 'qpc_clock_for_new_run', side_effect=AssertionError('new clock')), \
                patch.object(host, '_Transport', side_effect=AssertionError('SSH')):
            result = run({}, Path(out), {}, {}, f.clock, _causal_source=f.source)
            self.assertEqual(2, result)
            terminal = json.loads((Path(out)/'HOST_TERMINAL.json').read_bytes())
            self.assertEqual('ValueError', terminal['primary_error']['type'])
            self.assertFalse(terminal['SSH_started'])
            self.assertFalse(terminal['movement_authorized'])
            self.assertEqual('RETIRED', f.source.state)
            self.assertEqual(['HOST_TERMINAL.json'], [p.name for p in Path(out).iterdir()])

    def test_public_world_admission_refuses_software_service(self):
        check = getattr(causal, '_require_world_service', None)
        self.assertTrue(callable(check), 'production service admission is missing')
        f = fixture()
        with self.assertRaises(ValueError):
            check(f.service, f.clock, f.source, causal_mode=True)
        self.assertEqual([], f.world.events)

    def test_world_service_never_enables_fixed_mode(self):
        check = getattr(causal, '_require_world_service', None)
        self.assertTrue(callable(check), 'production service admission is missing')
        f = fixture()
        with self.assertRaises(ValueError):
            check(f.service, f.clock, f.source, causal_mode=False)
        self.assertEqual('NEW', f.source.state)

    def test_none_service_keeps_legacy_admission_without_poll(self):
        check = getattr(causal, '_require_world_service', None)
        self.assertTrue(callable(check), 'production service admission is missing')
        f = fixture()
        self.assertIsNone(check(None, f.clock, f.source, causal_mode=True))
        self.assertEqual([], f.world.events)

    def test_ready_wait_services_original_world_without_blocking_line(self):
        wait = getattr(causal, '_wait_world_line', None)
        self.assertTrue(callable(wait), 'cooperative original wait is missing')
        f = fixture(); t = Transport(f, [None, None, b'READY\n'])
        self.assertEqual(b'READY\n', wait(t, f.clock, f.service, 180))
        self.assertEqual(['world','transport']*3, f.world.events)
        self.assertEqual(0, t.blocking_calls)

    def test_wait_cannot_accept_a_line_observed_at_native_deadline(self):
        wait = getattr(causal, '_wait_world_line', None)
        self.assertTrue(callable(wait), 'cooperative original wait is missing')
        f = fixture()
        def late():
            f.clock.now = f.service.deadline_ns
            return b'late\n', False
        t = Transport(f, [late])
        with self.assertRaises(TimeoutError): wait(t, f.clock, f.service, 180)

    def test_wait_uses_original_five_second_phase_cap(self):
        wait = getattr(causal, '_wait_world_line', None)
        self.assertTrue(callable(wait), 'cooperative original wait is missing')
        f = fixture(); start = f.clock.now
        def late():
            f.clock.now = start+5_000_000_000
            return b'late\n', False
        with self.assertRaises(TimeoutError):
            wait(Transport(f, [late]), f.clock, f.service, 5)

    def test_expired_wait_rejects_before_transport_read(self):
        wait = getattr(causal, '_wait_world_line', None)
        self.assertTrue(callable(wait), 'cooperative original wait is missing')
        f = fixture(); f.clock.now = f.service.deadline_ns
        t = Transport(f, [b'late\n'])
        with self.assertRaises(TimeoutError): wait(t, f.clock, f.service, 180)
        self.assertEqual(0, t.polls)

    def test_terminal_wait_only_uses_retired_source_poll(self):
        wait = getattr(causal, '_wait_world_line', None)
        self.assertTrue(callable(wait), 'cooperative original wait is missing')
        f = fixture(); f.source.retire('software terminal')
        t = Transport(f, [b'terminal\n'])
        self.assertEqual(b'terminal\n', wait(t, f.clock, f.service, 5, retired_source=True))
        self.assertFalse(f.service._failed)
        self.assertEqual('RETIRED', f.source.state)
        self.assertEqual(1, t.polls)

    def test_source_failure_before_request_prevents_new_request(self):
        f = fixture(); c = Channel(f); t = Transport(f, [None])
        def sample():
            f.world._vetoed = True
            return dict(adc_tick_ms=0)
        f.source.poll = sample
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError): self.call_core(f, t, c, out)
        self.assertEqual(0, c.requests)
        self.assertEqual([], t.sent)
        self.assertEqual(1, t.closes)

    def test_world_change_after_request_serialization_prevents_send(self):
        f = fixture(); c = Channel(f); t = Transport(f, [None])
        f.source.poll = lambda: dict(adc_tick_ms=0)
        c.request_hook = lambda: setattr(f.world, '_vetoed', True)
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError): self.call_core(f, t, c, out)
        self.assertEqual(1, c.requests)
        self.assertEqual([], t.sent)

    def test_post_consumer_world_veto_blocks_completion_and_new_work(self):
        f = fixture(); c = Channel(f); t = Transport(f, [b'capture\n'])
        called = []
        def consume(candidate):
            called.append(candidate)
            f.world._vetoed = True
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):
                self.call_core(f, t, c, out, on_candidate=consume)
            self.assertFalse((Path(out)/'causal-exchange/HOST_CAUSAL_RESULT.json').exists())
        self.assertEqual(1, len(called))
        self.assertEqual([], t.sent)
        self.assertEqual('RETIRED', f.source.state)
        self.assertEqual(1, t.closes)

    def test_retired_source_terminal_drain_preserves_real_core_result(self):
        f = fixture(); c = Channel(f)
        stopped = pl.encode(dict(schema=1, kind='diagnostic_stopped', context=CONTEXT,
            cleanup=dict(attempted=True, confirmed=True, status=0,
                active_tag=0, secondary_errors=[]), error=None, frames_completed=1,
            movement_authorized=False))
        t = Transport(f, [b'capture\n', stopped])
        with tempfile.TemporaryDirectory() as out:
            result = self.call_core(f, t, c, out)
        self.assertEqual(1, len(result['captures']))
        self.assertFalse(result['movement_authorized'])
        self.assertFalse(result['CPU_completion_created'])
        self.assertEqual('not_run', result['complete_H12'])
        self.assertEqual('RETIRED', f.source.state)
        self.assertFalse(f.service._failed)
        self.assertEqual(1, t.closes)
        self.assertEqual(0, t.blocking_calls)

    def test_wrong_same_source_reference_rejected_before_core_effects(self):
        f = fixture(); c = Channel(f); t = Transport(f)
        another = causal.CausalSourcePump(f.source._pose_reader, f.source._sampler)
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):
                causal._exchange_causal_core(c, t, another, clock=f.clock,
                    origin_ns=f.clock.now, scans=1, out=out, _world_service=f.service)
            self.assertEqual([], list(Path(out).iterdir()))
        self.assertEqual(0, t.polls)

    def test_world_poll_cannot_expire_session_then_invoke_consumer(self):
        f = fixture(); c = Channel(f); t = Transport(f, [b'capture\n'])
        called = []; origin = f.clock.now
        with tempfile.TemporaryDirectory() as out:
            def poll_hook():
                if (Path(out)/'causal-exchange/feedback-00-started.json').exists():
                    f.clock.now = origin+10_000_000_001
            f.world.hook = poll_hook
            with self.assertRaises(TimeoutError):
                self.call_core(f, t, c, out, on_candidate=lambda candidate: called.append(candidate))
            self.assertEqual([], called)
            self.assertTrue((Path(out)/'causal-exchange/feedback-00-not-called.json').exists())

    def test_world_poll_cannot_expire_request_then_send_original_bytes(self):
        f = fixture(); c = Channel(f); t = Transport(f, [None])
        origin = f.clock.now; constructed = []
        f.source.poll = lambda: dict(adc_tick_ms=0)
        c.request_hook = lambda: constructed.append(True)
        def poll_hook():
            if constructed: f.clock.now = origin+100_000_001
        f.world.hook = poll_hook
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(TimeoutError): self.call_core(f, t, c, out)
        self.assertEqual(1, c.requests)
        self.assertEqual([], t.sent)

    def test_claimed_source_recheck_reads_actual_changed_causal_file(self):
        check = getattr(host, '_verify_claimed_sources', None)
        self.assertTrue(callable(check), 'claimed path actual source verification is missing')
        base = Path(host.__file__).parent
        paths = dict(driver=Path(host.__file__), codec=Path(pl.__file__),
            host_clock=Path(host_clock.__file__), agent=base/'private_pl_live_agent.py',
            collector=base/'a_b56_memory_safe_collector.py')
        with tempfile.TemporaryDirectory() as out:
            leaf = Path(out)/'actual-causal-source.py'; leaf.write_bytes(b'original')
            causal_paths = dict(causal.source_paths()); causal_paths['causal_exchange'] = leaf
            stub = SimpleNamespace(source_paths=lambda: causal_paths)
            pins = {name:host.pin(path) for name,path in {**paths, **causal_paths}.items()}
            check(pins, stub)
            leaf.write_bytes(b'changed-after-claim')
            with self.assertRaises(ValueError): check(pins, stub)

    def test_claimed_context_domain_rejected_before_any_effect(self):
        check = getattr(host, '_require_clock_domain', None)
        self.assertTrue(callable(check), 'pre-SSH original domain verification is missing')
        with self.assertRaises(ValueError):
            check(dict(clock_domain_id='a'*32), dict(domain_id='b'*32))
        self.assertIsNone(check(dict(clock_domain_id='a'*32), dict(domain_id='a'*32)))

    def test_world_veto_during_source_work_prevents_admission(self):
        f = fixture(); c = Channel(f); t = Transport(f, [None])
        def sample():
            f.world._vetoed = True
            return dict(adc_tick_ms=0)
        f.source.poll = sample
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError): self.call_core(f, t, c, out)
            self.assertIn(b'"adc_tick_ms":0', (Path(out)/'causal-exchange/source-history.jsonl').read_bytes())
        self.assertEqual([], c.admitted)
        self.assertEqual([], t.sent)

    def test_world_poll_cannot_use_two_second_response_profile_for_source_age(self):
        f = fixture(); c = Channel(f); t = Transport(f, [None, lambda: (None, True)])
        c._owner._age = 2_000_000_000  # Diagnostic response cap, never source100ms.
        origin = f.clock.now; constructed = []
        f.source.poll = lambda: dict(adc_tick_ms=0)
        c.request_hook = lambda: constructed.append(True)
        def poll_hook():
            if constructed: f.clock.now = origin+100_000_001
        f.world.hook = poll_hook
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError): self.call_core(f, t, c, out)
        self.assertEqual([], t.sent)


if __name__ == '__main__': unittest.main(verbosity=2)
