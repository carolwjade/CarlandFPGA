"""NEW component controls only; no board, QPC, CPU actor or motion execution."""
import hashlib
import importlib
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from competition.deepeye.integration import private_pl_stream as pl

ORIGIN = 1_000_000_000
PROFILE = {'name': 'functional_chain_v1', 'max_age_ns': 2_000_000_000,
           'idle_timeout_ms': 2000}
CTX = dict(operation_id='NEW-CAUSAL-CHANNEL-COMPONENT', request_hash='a'*64,
           tested_commit='b'*40, build_manifest_sha256='c'*64,
           boot_id='component-label-not-BOOT-proof', session_id='new-component',
           tag=123, clock_domain_id='d'*32)


class Clock:
    def __init__(self): self.value = ORIGIN
    def __call__(self):
        now = self.value
        self.value += 1
        return now
    def tick(self, tick): self.value = ORIGIN + tick*1_000_000 + 100


def sample(tick=0, *, fault=False, saturated=False):
    em = tick//50*50
    values = [math.log10(.2), 0., 2., None]
    counts = [0, 2048, 4095, None]
    quality = 7 | (0x700 if tick != em else 0) | (0x40 if saturated else 0)
    if fault:
        values, counts, quality, em = [None]*4, [None]*4, 0x1000, None
    return dict(profile_id='deepeye_forward_profile_candidate_v1',
        profile_status='candidate_only',
        profile_note='not_calibrated;not_em_surrogate_v2;not_formally_frozen',
        source_mode='twin_fixture', adc_tick_ms=tick, em_tick_ms=em,
        channel_values=values, channel_counts=counts, quality=quality)


def ready():
    return pl.encode(pl.record('diagnostic_ready', dict(CTX), generation=1,
                               trigger_id=0, baseline_counters=[0, 0, 0]))


def capture(raw):
    request = pl.decode(raw)
    seq = request['request_seq']
    lanes = []
    for ch, ticks in enumerate(request['original_host_qpc_ns']):
        lanes.append(dict(channel=ch,
            raw_words=[request['values'][ch], ch | request['qualities'][ch]<<8,
                       ticks & 0xffffffff, ticks >> 32, 4*(seq-1), 4*seq-1,
                       CTX['tag'], seq, 1, 12345+ch],
            pipeline_counters=[4*seq, seq, 4*(seq-1)+ch+1], ack_returned=True))
    return pl.record('diagnostic_capture', dict(CTX), request_seq=seq,
        request_sha256=hashlib.sha256(raw).hexdigest(), generation=1,
        trigger_id=seq, captures=lanes, final_counters=[4*seq, seq, 4*seq])


class CandidateChannelTests(unittest.TestCase):
    def module(self):
        self.assertTrue((ROOT/'competition/deepeye/simulation/authority/live_chain_channels.py').exists(),
                        'NEW causal channel missing: expected RED')
        return importlib.import_module('competition.deepeye.simulation.authority.live_chain_channels')

    def channel(self, *, max_scans=16):
        module = self.module()
        clock = Clock()
        owner = pl._HostOwner(dict(CTX), clock, max_age_ns=2_000_000_000,
                              functional_timing_profile=dict(PROFILE))
        channel = module._CandidateChannel(owner, clock=clock, start_tick_ms=0,
            start_monotonic_ns=ORIGIN, max_scans=max_scans)
        channel.accept_ready(ready())
        return channel, clock

    def test_quality_mapping_preserves_each_global_bit_and_all_8192_words(self):
        module = self.module()
        for bit in range(13):
            expected = [0]*4
            if bit == 12: expected = [8]*4
            else: expected[bit % 4] = 1 << (bit//4)
            self.assertEqual(module.pack_candidate_quality(1 << bit), tuple(expected))
        for word in range(8192):
            self.assertEqual(module.unpack_candidate_quality(module.pack_candidate_quality(word)), word)

    def test_quality_rejects_bool_reserved_bits_and_disagreeing_fault_copies(self):
        module = self.module()
        for bad in (True, -1, 8192, 65535, 1.0, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.pack_candidate_quality(bad)
        for bad in ((8, 0, 8, 8), (16, 0, 0, 0), (True, 0, 0, 0), (0,)*3):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.unpack_candidate_quality(bad)

    def test_returned_counts_and_quality_keep_candidate_identity_without_floats(self):
        channel, clock = self.channel()
        channel.admit_sample(sample(saturated=True))
        request = channel.next_request()
        self.assertEqual(pl.decode(request)['qualities'], [1, 1, 3, 0])
        raw = pl.encode(capture(request))
        result = channel.accept_capture(raw)
        self.assertEqual(result['channel_counts'], [0, 2048, 4095, None])
        self.assertEqual(result['quality'], 0x47)
        self.assertEqual(result['observation_identity']['capture_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['transport_source'], 'software_fixture')
        self.assertEqual(result['source_mode'], 'twin_fixture')
        self.assertNotIn('channel_values', result)
        self.assertFalse(result['diagnostic_flags']['movement_authorized'])
        self.assertFalse(result['diagnostic_flags']['BOOT_authenticated'])
        self.assertFalse(result['diagnostic_flags']['compression_verified'])

    def test_invalid_transport_placeholders_decode_to_null_never_valid_zero(self):
        channel, clock = self.channel()
        channel.admit_sample(sample(fault=True))
        request = channel.next_request()
        self.assertEqual(pl.decode(request)['values'], [0]*4)
        self.assertEqual(pl.decode(request)['qualities'], [8]*4)
        result = channel.accept_capture(pl.encode(capture(request)))
        self.assertEqual(result['channel_counts'], [None]*4)
        self.assertEqual(result['quality'], 0x1000)
        self.assertFalse(result['diagnostic_flags']['source_fresh_at_capture'])

    def test_two_distinct_source_samples_keep_their_own_request_and_original_time(self):
        channel, clock = self.channel()
        channel.admit_sample(sample())
        first = channel.accept_capture(pl.encode(capture(channel.next_request())))
        clock.tick(10)
        channel.admit_sample(sample(10))
        second = channel.accept_capture(pl.encode(capture(channel.next_request())))
        self.assertEqual([first['observation_identity']['request_seq'], second['observation_identity']['request_seq']], [1, 2])
        self.assertEqual(second['source_time']['adc_tick_ms'], 10)
        self.assertEqual(second['source_time']['em_tick_ms'], 0)
        self.assertEqual(second['quality'], 0x707)
        self.assertNotEqual(first['observation_identity']['request_sha256'], second['observation_identity']['request_sha256'])

    def test_newer_source_cannot_refresh_the_pending_source_age(self):
        channel, clock = self.channel()
        channel.admit_sample(sample())
        request = channel.next_request()
        clock.tick(150)
        channel.admit_sample(sample(150))
        result = channel.accept_capture(pl.encode(capture(request)))
        self.assertEqual(result['source_time']['adc_tick_ms'], 0)
        self.assertEqual(result['source_time']['em_tick_ms'], 0)
        self.assertGreaterEqual(result['source_time']['em_source_age_ns'], 150_000_000)
        self.assertFalse(result['diagnostic_flags']['source_fresh_at_capture'])
        self.assertFalse(result['diagnostic_flags']['target100ms_met'])
        self.assertEqual(result['diagnostic_flags']['formal_H12'], 'not_run')

    def test_source_payload_is_detached_and_never_falls_back_to_changed_input(self):
        channel, clock = self.channel()
        original = sample()
        channel.admit_sample(original)
        original['channel_counts'][0] = 123
        original['channel_values'][0] = 100
        result = channel.accept_capture(pl.encode(capture(channel.next_request())))
        self.assertEqual(result['channel_counts'][0], 0)

    def test_source_relabel_extra_truth_or_counts_mismatch_fail_closed(self):
        for change in ({'source_mode': 'sim_em_v2'}, {'obstacle_xyz': [1, 2, 3]},
                       {'channel_counts': [1, 2048, 4095, None]}):
            channel, clock = self.channel()
            payload = sample(); payload.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): channel.admit_sample(payload)
            self.assertEqual(channel.state, 'FAILED')

    def test_no_source_midstream_attach_or_duplicate_source_is_accepted(self):
        channel, clock = self.channel()
        clock.tick(10)
        with self.assertRaises(ValueError): channel.admit_sample(sample(10))
        self.assertEqual(channel.state, 'FAILED')
        channel, clock = self.channel()
        channel.admit_sample(sample())
        with self.assertRaises(ValueError): channel.admit_sample(sample())
        self.assertEqual(channel.state, 'FAILED')

    def test_pending_request_cannot_be_replaced_or_same_source_resent(self):
        channel, clock = self.channel(); channel.admit_sample(sample())
        channel.next_request()
        with self.assertRaises(ValueError): channel.next_request()
        self.assertEqual(channel.state, 'FAILED')
        channel, clock = self.channel(); channel.admit_sample(sample())
        channel.accept_capture(pl.encode(capture(channel.next_request())))
        with self.assertRaises(ValueError): channel.next_request()

    def test_altered_returned_lane_counter_or_missing_ack_cannot_emit_candidate(self):
        for field in ('count', 'quality', 'counter', 'ack'):
            channel, clock = self.channel(); channel.admit_sample(sample())
            doc = capture(channel.next_request())
            if field == 'count': doc['captures'][0]['raw_words'][0] = 1
            elif field == 'quality': doc['captures'][0]['raw_words'][1] |= 0x1000
            elif field == 'counter': doc['final_counters'][2] += 1
            else: doc['captures'][0]['ack_returned'] = False
            with self.subTest(field=field), self.assertRaises(ValueError): channel.accept_capture(pl.encode(doc))
            self.assertEqual(channel.state, 'FAILED')

    def test_consumed_capture_or_capture_without_pending_rejected(self):
        channel, clock = self.channel(); channel.admit_sample(sample())
        raw = pl.encode(capture(channel.next_request()))
        channel.accept_capture(raw)
        with self.assertRaises(ValueError): channel.accept_capture(raw)
        self.assertEqual(channel.state, 'FAILED')

    def test_fixed_scan_cap_and_expired_response_are_irreversible(self):
        channel, clock = self.channel(max_scans=1); channel.admit_sample(sample())
        channel.accept_capture(pl.encode(capture(channel.next_request())))
        clock.tick(10); channel.admit_sample(sample(10))
        with self.assertRaises(ValueError): channel.next_request()
        channel, clock = self.channel(); channel.admit_sample(sample())
        request = channel.next_request()
        clock.value += 2_000_000_001
        with self.assertRaises(ValueError): channel.accept_capture(pl.encode(capture(request)))
        self.assertEqual(channel.state, 'FAILED')

    def test_production_wrapper_does_not_accept_a_component_clock(self):
        module = self.module()
        with self.assertRaises(ValueError):
            module.LiveFourChannelChannel(dict(CTX), Clock(), start_tick_ms=0,
                start_monotonic_ns=ORIGIN, functional_timing_profile=dict(PROFILE))


if __name__ == '__main__': unittest.main(verbosity=2)
