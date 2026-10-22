"""New software fixtures only; no board or external instrument operations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'integration/input_calibrate.py'


def fixture():
    channels = []
    for c in range(4):
        points = []
        for i in range(8):
            code = 100 + 200 * i
            points.append(dict(level_id=f'l{i}', target_v=0.1 + 0.001 * code,
                               reference_kind='software_fixture',
                               reference_v=0.1 + 0.001 * code,
                               reference_uncertainty_v=0.0001,
                               samples=[dict(sample_id=f'{c}/{i}/0', raw_word=code,
                                             analog_saturation=False)]))
        channels.append(dict(channel_id=f'A{c}', signal_chain_id=f'fixture-{c}',
                             gain=1, nominal_adc_bits=12, container_bits=16,
                             packing='right_aligned', range_v=[0.0, 3.3],
                             reference_instrument='software fixture, no instrument', levels=points))
    return dict(schema=1, source_mode='software_fixture', operation_id='software-fixture-01',
                request_hash='a' * 64, tested_commit='b' * 40,
                captured_at_utc='2026-10-22T00:00:00Z', channels=channels)


class IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SCRIPT.exists():
            spec = importlib.util.spec_from_file_location('input_calibrate', SCRIPT)
            cls.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.mod)

    def run_record(self, doc):
        self.assertTrue(SCRIPT.exists(), 'new calibration command is missing')
        return self.mod.analyze(json.dumps(doc).encode(), 8)

    def test_affine_fit_and_no_physical_or_enob_promotion(self):
        r = self.run_record(fixture())
        self.assertEqual(r['status'], 'computed')
        for c in r['channels']:
            self.assertAlmostEqual(c['fit']['offset_v'], 0.1, places=12)
            self.assertAlmostEqual(c['fit']['volts_per_code'], 0.001, places=12)
            self.assertLess(c['fit']['max_abs_residual_v'], 1e-12)
            self.assertEqual(c['level_count'], 8)
        self.assertEqual(r['evidence_level'], 'software_fixture')
        self.assertEqual(r['physical_verification'], 'not_run')
        self.assertEqual(r['enob']['status'], 'not_run')
        self.assertEqual(r['r02_acceptance'], 'not_run')

    def test_replicates_are_one_level_and_do_not_reweight_fit(self):
        d = fixture(); p = d['channels'][0]['levels'][0]
        p['reference_v'] += 0.01
        first = self.run_record(d)['channels'][0]['fit']
        for j in range(1, 20):
            p['samples'].append(dict(p['samples'][0], sample_id=f'0/0/{j}'))
        r = self.run_record(d)
        self.assertEqual(first, r['channels'][0]['fit'])
        self.assertEqual(r['channels'][0]['sample_count'], 27)

    def test_explicit_left_packing_and_invalid_padding(self):
        d = fixture()
        for c in d['channels']:
            c['packing'] = 'left_aligned'
            for p in c['levels']:
                p['samples'][0]['raw_word'] <<= 4
        self.assertEqual(self.run_record(d)['status'], 'computed')
        d['channels'][0]['levels'][0]['samples'][0]['raw_word'] |= 1
        self.assertEqual(self.run_record(d)['status'], 'invalid')

    def test_incomplete_and_ambiguous_levels_are_not_fitted(self):
        for mutation in ('seven', 'target', 'reference'):
            with self.subTest(mutation=mutation):
                d = fixture(); p = d['channels'][0]['levels']
                if mutation == 'seven': p.pop()
                elif mutation == 'target': p[1]['target_v'] = p[0]['target_v']
                else: p[1]['reference_v'] = p[0]['reference_v'] + 0.00001
                r = self.run_record(d)
                self.assertNotEqual(r['status'], 'computed')
                self.assertIsNone(r['channels'][0]['fit'])

    def test_quality_flags_block_entire_channel_without_dropping_samples(self):
        for mutation in ('low_rail', 'high_rail', 'saturated', 'unknown', 'range'):
            with self.subTest(mutation=mutation):
                d = fixture(); p = d['channels'][0]['levels'][0]; s = p['samples'][0]
                if mutation == 'low_rail': s['raw_word'] = 0
                elif mutation == 'high_rail': s['raw_word'] = 4095
                elif mutation == 'saturated': s['analog_saturation'] = True
                elif mutation == 'unknown': s['analog_saturation'] = None
                else: p['reference_v'] = 3.4
                r = self.run_record(d)
                self.assertEqual(r['status'], 'incomplete')
                self.assertIsNone(r['channels'][0]['fit'])
                self.assertEqual(r['channels'][0]['sample_count'], 8)
                self.assertEqual(r['channels'][1]['status'], 'computed')

    def test_structural_corruption_cannot_compute(self):
        for mutation in ('sample_id', 'level_id', 'channel_id', 'word_bool', 'word_overflow',
                         'nominal_bits', 'source', 'setpoint_reference', 'commit', 'nan'):
            with self.subTest(mutation=mutation):
                d = fixture(); c = d['channels'][0]; p = c['levels'][0]
                if mutation == 'sample_id': p['samples'].append(copy.deepcopy(p['samples'][0]))
                elif mutation == 'level_id': c['levels'][1]['level_id'] = p['level_id']
                elif mutation == 'channel_id': d['channels'][1]['channel_id'] = 'A0'
                elif mutation == 'word_bool': p['samples'][0]['raw_word'] = True
                elif mutation == 'word_overflow': p['samples'][0]['raw_word'] = 65536
                elif mutation == 'nominal_bits': c['nominal_adc_bits'] = 16
                elif mutation == 'source': d['source_mode'] = 'geo_replay'
                elif mutation == 'setpoint_reference': p['reference_kind'] = 'dac_setpoint'
                elif mutation == 'commit': d['tested_commit'] = 'short'
                else: p['reference_v'] = float('nan')
                self.assertEqual(self.run_record(d)['status'], 'invalid')

    def test_constant_or_reversed_adc_is_not_a_calibration(self):
        for reverse in (False, True):
            d = fixture()
            for i, p in enumerate(d['channels'][0]['levels']):
                p['samples'][0]['raw_word'] = 1500 - 200 * i if reverse else 1000
            r = self.run_record(d)
            self.assertEqual(r['status'], 'incomplete')
            self.assertIsNone(r['channels'][0]['fit'])

    def test_raw_identity_and_physical_declarations_remain_unverified(self):
        d = fixture(); d['source_mode'] = 'twin_fixture'
        for c in d['channels']:
            for p in c['levels']: p['reference_kind'] = 'independent_measurement'
        self.assertTrue(SCRIPT.exists(), 'new calibration command is missing')
        raw = json.dumps(d, indent=2).encode()
        r = self.mod.analyze(raw)
        self.assertEqual(r['input_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(r['declared_provenance']['tested_commit'], 'b' * 40)
        self.assertEqual(r['evidence_level'], 'offline_computation_on_declared_measurements')
        self.assertEqual(r['physical_verification'], 'not_run')

    def test_cli_missing_input_and_exclusive_output(self):
        self.assertTrue(SCRIPT.exists(), 'new calibration command is missing')
        q = subprocess.run([sys.executable, '-B', str(SCRIPT), '--levels', '8'],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(q.returncode, 3)
        self.assertEqual(json.loads(q.stdout)['status'], 'not_run')
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'record.json'; out = Path(td) / 'report.json'
            raw = json.dumps(fixture()).encode(); src.write_bytes(raw)
            cmd = [sys.executable, '-B', str(SCRIPT), '--input', str(src), '--output', str(out)]
            q = subprocess.run(cmd, capture_output=True, timeout=10)
            self.assertEqual(q.returncode, 0, q.stderr)
            saved = out.read_bytes()
            q = subprocess.run(cmd, capture_output=True, timeout=10)
            self.assertEqual(q.returncode, 2)
            self.assertEqual(saved, out.read_bytes())
            self.assertEqual(raw, src.read_bytes())

    def test_cli_oversize_does_not_claim_a_prefix_hash_as_file_identity(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'oversize.json'
            src.write_bytes(b' ' * (4 * 1024 * 1024 + 25))
            q = subprocess.run([sys.executable, '-B', str(SCRIPT), '--input', str(src)],
                               capture_output=True, text=True, timeout=10)
            self.assertEqual(q.returncode, 2)
            report = json.loads(q.stdout)
            self.assertIsNone(report['input_sha256'], 'unread suffix cannot have a complete-file identity')

    def test_cli_output_error_keeps_read_input_identity(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'record.json'; out = Path(td) / 'exists.json'
            raw = json.dumps(fixture()).encode(); src.write_bytes(raw); out.write_bytes(b'preserve')
            q = subprocess.run([sys.executable, '-B', str(SCRIPT), '--input', str(src),
                                '--output', str(out)], capture_output=True, text=True, timeout=10)
            self.assertEqual(q.returncode, 2)
            report = json.loads(q.stdout)
            self.assertEqual(report['input_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertFalse(any('input_missing' in x for x in report['errors']))
            self.assertEqual(out.read_bytes(), b'preserve')


if __name__ == '__main__':
    unittest.main()
