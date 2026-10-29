"""NEW component fixtures only: no real QPC, agent main, SSH, board or model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[4]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load('functional_codec_fixture', 'competition/deepeye/integration/private_pl_stream.py')
A = load('functional_agent_fixture', 'competition/deepeye/tools/diagnostic/private_pl_live_agent.py')
H = load('functional_host_fixture', 'competition/deepeye/tools/diagnostic/run_private_pl_live.py')
PROFILE = {'name': 'functional_chain_v1', 'max_age_ns': 2000000000, 'idle_timeout_ms': 2000}
CTX = dict(operation_id='NEW-FUNCTIONAL-COMPONENT', request_hash='a' * 64,
           tested_commit='b' * 40, build_manifest_sha256='c' * 64, boot_id='fixture-boot',
           session_id='new-fixture-session', tag=123, clock_domain_id='d' * 32)


class Clock:
    def __init__(self): self.value = 1000000000
    def __call__(self):
        value = self.value
        self.value += 1
        return value


def request():
    return {'functional_timing_profile': dict(PROFILE), 'idle_timeout_ms': 2000,
            'total_seconds': 10, 'poll_seconds': 2, 'max_scans': 16}


def activation():
    return {'functional_timing_profile': dict(PROFILE), 'max_age_ns': 2000000000}


def ready():
    return C.encode(C.record('diagnostic_ready', CTX, generation=1, trigger_id=0,
                             baseline_counters=[0, 0, 0]))


def capture(raw):
    q = json.loads(raw)
    lanes = []
    for ch, ticks in enumerate(q['original_host_qpc_ns']):
        lanes.append({'channel': ch, 'raw_words': [q['values'][ch], ch | (q['qualities'][ch] << 8),
                      ticks & 0xffffffff, ticks >> 32, 0, 3, 123, 1, 1, 987],
                      'pipeline_counters': [4, 1, ch + 1], 'ack_returned': True})
    return C.record('diagnostic_capture', CTX, request_seq=1,
                    request_sha256=hashlib.sha256(raw).hexdigest(), generation=1,
                    trigger_id=1, captures=lanes, final_counters=[4, 1, 4])


class FunctionalTimingTests(unittest.TestCase):
    def policy(self):
        self.assertTrue(callable(getattr(C, 'request_timing', None)),
                        'NEW timing schema/selection is absent (expected RED)')
        return C.request_timing

    def owner(self, functional=True):
        if functional: self.policy()
        clock = Clock()
        kw = {'functional_timing_profile': dict(PROFILE), 'max_age_ns': 2000000000} if functional else {}
        owner = C._HostOwner(CTX, clock, **kw)
        owner.accept_ready(ready())
        raw = owner.next_request([17, 4095, 32769, 65280], [2, 17, 128, 254])
        return owner, clock, raw

    def test_request_activation_must_match_exact_fixed_profile(self):
        select = self.policy()
        selected = select(request(), activation())
        self.assertEqual((selected['max_age_ns'], selected['idle_timeout_ms']), (2000000000, 2000))
        cases = []
        for side in ('request', 'activation'):
            for bad in (None, True, 'functional_chain_v1', {}, {**PROFILE, 'extra': 1},
                        {**PROFILE, 'name': 'x' * 193}, {**PROFILE, 'max_age_ns': True},
                        {**PROFILE, 'max_age_ns': float('nan')}, {**PROFILE, 'max_age_ns': 2000000001},
                        {**PROFILE, 'idle_timeout_ms': 2001}, {**PROFILE, 'idle_timeout_ms': 2000.0}):
                q, a = request(), activation()
                (q if side == 'request' else a)['functional_timing_profile'] = bad
                cases.append((q, a))
        q, a = request(), activation(); del a['functional_timing_profile']; cases.append((q, a))
        q, a = request(), activation(); del q['functional_timing_profile']; cases.append((q, a))
        q, a = request(), activation(); a['max_age_ns'] = 100000000; cases.append((q, a))
        q, a = request(), activation(); q['idle_timeout_ms'] = 100; cases.append((q, a))
        for q, a in cases:
            with self.subTest(q=q, a=a), self.assertRaises(ValueError): select(q, a)

    def test_legacy_age_and_wire_shape_remain_100ms(self):
        owner, clock, raw = self.owner(False)
        self.assertEqual(set(json.loads(raw)), {'schema', 'kind', 'context', 'request_seq', 'source_id',
                         'source', 'values', 'qualities', 'original_host_qpc_ns'})
        clock.value = json.loads(raw)['original_host_qpc_ns'][0] + 150000000
        with self.assertRaises(ValueError): owner.accept(C.encode(capture(raw)))
        self.assertEqual(owner.state, 'FAILED')
        with self.assertRaises(ValueError): C._HostOwner(CTX, Clock(), max_age_ns=2000000000)

    def test_explicit_profile_accepts_150ms_but_does_not_pass_target(self):
        owner, clock, raw = self.owner()
        original = capture(raw)
        clock.value = json.loads(raw)['original_host_qpc_ns'][0] + 150000000
        self.assertEqual(owner.accept(C.encode(original)), original)
        self.assertEqual(owner.last_response_timing['response_latency_ns'], 150000000)
        self.assertIs(owner.last_response_timing['target100ms_met'], False)
        self.assertEqual(owner.last_response_timing['formal_100ms_acceptance'], 'not_run')
        self.assertEqual(owner.response_timeout_seconds, 2.0)

    def test_inclusive_age_boundary_is_not_source_renewal(self):
        for latency, accepted in ((2000000000, True), (2000000001, False)):
            owner, clock, raw = self.owner()
            clock.value = json.loads(raw)['original_host_qpc_ns'][0] + latency
            with self.subTest(latency=latency):
                if accepted: owner.accept(C.encode(capture(raw)))
                else:
                    with self.assertRaises(ValueError): owner.accept(C.encode(capture(raw)))
                    self.assertEqual(owner.state, 'FAILED')

    def test_profile_preserves_identity_sequence_ack_and_unknown_fences(self):
        for key in ('request_seq', 'generation', 'context', 'ack'):
            owner, clock, raw = self.owner(); obj = capture(raw)
            if key == 'context': obj[key] = {**CTX, 'session_id': 'wrong'}
            elif key == 'ack': obj['captures'][0]['ack_returned'] = False
            else: obj[key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError): owner.accept(C.encode(obj))
            with self.assertRaises(ValueError): owner.next_request([1] * 4, [0] * 4)
        owner, clock, raw = self.owner()
        q = json.loads(raw); q['source_id'] = 1
        with self.assertRaises(ValueError): C.decode_request(C.encode(q), CTX, 1)
        with self.assertRaises(ValueError): owner.next_request([1] * 4, [0] * 4)

    def test_agent_timing_selects_bounded_idle_without_runtime(self):
        self.policy()
        self.assertTrue(callable(getattr(A, '_validated_session_timing', None)), 'NEW agent timing preflight absent')
        selected = A._validated_session_timing(request(), C)
        self.assertEqual(selected['idle_timeout_ms'], 2000)
        for field, bad in (('idle_timeout_ms', 2001), ('max_scans', 17), ('total_seconds', 11),
                           ('poll_seconds', float('nan'))):
            q = request(); q[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError): A._validated_session_timing(q, C)
        q = request(); del q['functional_timing_profile']
        with self.assertRaises(ValueError): A._validated_session_timing(q, C)

    def test_exchange_uses_profile_wait_and_keeps_separate_timing_report(self):
        self.policy()
        clock = Clock()
        owner = C._HostOwner(CTX, clock, max_age_ns=2000000000, functional_timing_profile=dict(PROFILE))
        owner.host_clock = types.SimpleNamespace(metadata={'fixture_only': True})
        class Transport:
            def __init__(self): self.waits = []; self.raw = None; self.closed = False
            def send_once(self, raw): self.raw = raw
            def close_input(self): self.closed = True
            def line(self, seconds):
                self.waits.append(seconds)
                if len(self.waits) == 1: return ready()
                if len(self.waits) == 2:
                    clock.value = json.loads(self.raw)['original_host_qpc_ns'][0] + 150000000
                    return C.encode(capture(self.raw))
                return C.encode(C.record('diagnostic_stopped', CTX, cleanup={'attempted': True,
                    'confirmed': True, 'status': 0, 'active_tag': 0, 'secondary_errors': []},
                    error=None, frames_completed=1, movement_authorized=False))
        transport = Transport()
        with tempfile.TemporaryDirectory() as tmp:
            H._exchange(owner, transport, C, [17, 4095, 32769, 65280], [2, 17, 128, 254], 1, Path(tmp))
            result = json.loads((Path(tmp) / 'HOST_RESULT.json').read_bytes())
        self.assertEqual(transport.waits, [180, 2.0, 5])
        self.assertTrue(transport.closed)
        self.assertEqual(result['response_timing'][0]['response_latency_ns'], 150000000)
        self.assertIs(result['response_timing'][0]['target100ms_met'], False)
        self.assertEqual(result['formal_100ms_acceptance'], 'not_run')
        self.assertIs(result['movement_authorized'], False)


if __name__ == '__main__': unittest.main(verbosity=2)
