"""Runner behavior checks only; never product/board acceptance.

Set TMP/TEMP to the caller's private evidence directory when running these tests.
"""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/verify_game.py'
if SCRIPT.is_file():
    spec = importlib.util.spec_from_file_location('game_runner_under_test', SCRIPT)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
else:
    runner = None


class RunnerBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(runner, 'RED: unified runner is absent')
        self.temp = tempfile.TemporaryDirectory(prefix='game-runner-test-')
        self.addCleanup(self.temp.cleanup)
        self.evidence = Path(self.temp.name)
        self.sequence = 0

    def cli(self, *args):
        completed = subprocess.run([sys.executable, '-B', str(SCRIPT),
            '--evidence-dir', str(self.evidence), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return completed, json.loads(completed.stdout) if completed.stdout.strip() else None

    def command(self, code, **kwargs):
        self.sequence += 1
        return runner.run_command([sys.executable, '-B', '-c', code],
            cwd=self.evidence, evidence_dir=self.evidence, label='child-' + str(self.sequence),
            timeout_seconds=kwargs.pop('timeout_seconds', 5), **kwargs)

    def test_failed_child_is_not_swallowed_and_raw_bytes_are_hashed(self):
        result = self.command('import sys; sys.stdout.buffer.write(b"out\\x00"); '
                              'sys.stderr.buffer.write(b"bad\\xff"); sys.exit(7)')
        self.assertEqual('failed', result['status'])
        self.assertEqual(7, result['exit_code'])
        for name in ('stdout', 'stderr'):
            item = result[name]
            self.assertEqual(runner.sha256(Path(item['path'])), item['sha256'])
            self.assertTrue(Path(item['path']).is_relative_to(self.evidence))
        self.assertEqual(b'bad\xff', Path(result['stderr']['path']).read_bytes())

    def test_timeout_is_failed_not_dependency_blocked(self):
        result = self.command('import time; print("started", flush=True); time.sleep(30)',
                              timeout_seconds=0.1)
        self.assertEqual('failed', result['status'])
        self.assertTrue(result['timed_out'])
        self.assertIn(b'started', Path(result['stdout']['path']).read_bytes())

    def test_missing_executable_is_blocked(self):
        result = runner.run_command([str(self.evidence / 'absent.exe')],
            cwd=self.evidence, evidence_dir=self.evidence, label='missing', timeout_seconds=1)
        self.assertEqual('blocked', result['status'])
        self.assertIsNone(result['exit_code'])

    def test_zero_exit_without_real_suite_summary_is_failed(self):
        for expectation in ('unittest', 'editor'):
            result = self.command('print("mock PASS")', expectation=expectation)
            self.assertEqual('failed', result['status'])

    def test_zero_test_or_skipped_unittest_cannot_pass(self):
        for output in ('Ran 0 tests in 0.0s\n\nOK',
                       'Ran 2 tests in 0.0s\n\nOK (skipped=2)'):
            result = self.command('print(' + repr(output) + ')', expectation='unittest')
            self.assertEqual('failed', result['status'])

    def test_godot_errors_cannot_hide_behind_pass_marker_and_zero_exit(self):
        result = self.command('print("TESTS checks=672 failures=0\\nRESULT PASS\\nSCRIPT ERROR: bad")',
                              expectation='editor')
        self.assertEqual('failed', result['status'])

    def test_import_errors_cannot_hide_behind_zero_exit(self):
        result = self.command('print("SCRIPT ERROR: parse failure")')
        self.assertEqual('failed', result['status'])

    def test_missing_source_or_empty_command_list_never_passes(self):
        for commands, paths in (([], []),
                ([dict(label='unused', command=[sys.executable, '-V'])],
                 [self.evidence / 'missing-source.py'])):
            result = runner.run_checked(commands, paths, cwd=self.evidence,
                evidence_dir=self.evidence, timeout_seconds=1)
            self.assertEqual('blocked', result['status'])
            self.assertEqual([], result['commands'])

    def test_changed_source_prevents_reference_pass(self):
        source = self.evidence / 'candidate.py'
        source.write_text('before', encoding='utf-8')
        commands = [dict(label='change', command=[sys.executable, '-B', '-c',
            'from pathlib import Path; Path(' + repr(str(source)) + ').write_text("after")'])]
        result = runner.run_checked(commands, [source], cwd=self.evidence,
            evidence_dir=self.evidence, timeout_seconds=5)
        self.assertEqual('failed', result['status'])
        self.assertIn(str(source), result['changed_sources'])
        self.assertNotEqual(result['source_before'], result['source_after'])

    def test_original_tree_additions_are_detected(self):
        simulator = self.evidence / 'simulator'
        simulator.mkdir()
        (simulator / 'original.gd').write_text('original', encoding='utf-8')
        with patch.object(runner, 'PRODUCT', self.evidence):
            before = runner.snapshot(runner.source_paths('editor'))
            added = simulator / 'added.gd'
            added.write_text('new source', encoding='utf-8')
            after = runner.snapshot(runner.source_paths('editor'))
        self.assertIn(str(added), runner.changed_paths(before, after))

    def test_staged_script_tampering_is_detected(self):
        stage = self.evidence / 'staged'
        stage.mkdir()
        script = stage / 'test.gd'
        script.write_text('real suite', encoding='utf-8')
        before = runner.tree_snapshot(stage)
        script.write_text('mock PASS', encoding='utf-8')
        self.assertIn(str(script), runner.changed_paths(before, runner.tree_snapshot(stage)))

    def test_log_label_cannot_escape_evidence(self):
        with self.assertRaises(ValueError):
            runner.run_command([sys.executable, '-V'], cwd=self.evidence,
                evidence_dir=self.evidence, label='../escape', timeout_seconds=1)

    def test_evidence_under_product_is_rejected_before_writes(self):
        completed = subprocess.run([sys.executable, '-B', str(SCRIPT), '--suite', 'timing',
            '--evidence-dir', str(ROOT / 'tools')], capture_output=True, timeout=10)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(b'evidence', completed.stderr.lower())

    def test_all_formal_suites_block_with_specific_gaps(self):
        for suite in ('editor', 'sensors', 'timing', 'assets', 'secrecy', 'motion_authority'):
            with self.subTest(suite=suite):
                completed, result = self.cli('--suite', suite)
                self.assertEqual(2, completed.returncode)
                self.assertEqual('blocked', result['status'])
                self.assertFalse(result['formal_acceptance'])
                self.assertGreater(len(result['missing_evidence']), 0)
                self.assertEqual([], result['commands'])

    def test_unimplemented_action_and_trial_counts_never_silently_pass(self):
        for args in (('--suite', 'editor', '--actions', '200'),
                     ('--suite', 'sensors', '--trials-per-cell', '30')):
            for reference in ((), ('--reference-only',)):
                completed, result = self.cli(*args, *reference)
                self.assertEqual(2, completed.returncode)
                self.assertIn('unsupported', ' '.join(result['missing_evidence']).lower())
                self.assertFalse(result['formal_acceptance'])
                self.assertEqual([], result['commands'])

    def test_unknown_suite_is_rejected(self):
        completed, result = self.cli('--suite', 'imaginary')
        self.assertEqual(2, completed.returncode)
        self.assertIsNone(result)

    def test_no_mock_editor_fallback_and_fake_engine_is_blocked(self):
        completed, result = self.cli('--suite', 'editor', '--reference-only')
        self.assertEqual(2, completed.returncode)
        self.assertEqual('blocked', result['status'])
        fake = self.evidence / 'fake-godot.exe'
        fake.write_bytes(b'mock PASS')
        completed, result = self.cli('--suite', 'editor', '--reference-only', '--godot-exe', str(fake))
        self.assertEqual(2, completed.returncode)
        self.assertEqual('blocked', result['status'])
        self.assertFalse(result['formal_acceptance'])

    def test_reference_sensors_runs_real_tests_but_never_formal_acceptance(self):
        completed, result = self.cli('--suite', 'sensors', '--reference-only')
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual('reference_passed', result['status'])
        self.assertEqual('reference_only', result['evidence_level'])
        self.assertFalse(result['formal_acceptance'])
        self.assertEqual(2, len(result['commands']))
        self.assertTrue(all(step['exit_code'] == 0 for step in result['commands']))
        self.assertEqual(result['source_before'], result['source_after'])
        self.assertTrue(result['missing_evidence'])
        self.assertEqual('c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',
                         result['requirements_sha256'])
        self.assertTrue(Path(result['report_path']).is_relative_to(self.evidence))

    def test_motion_reference_runs_primitives_without_promoting_authority(self):
        completed, result = self.cli('--suite', 'motion_authority', '--reference-only')
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual('reference_passed', result['status'])
        self.assertFalse(result['formal_acceptance'])
        self.assertEqual(1, len(result['commands']))
        self.assertEqual('unittest', result['commands'][0]['expectation'])
        self.assertEqual(0, result['commands'][0]['exit_code'])
        self.assertEqual(result['source_before'], result['source_after'])
        for relative in ('simulation/authority/motion/kinematics.py',
                         'simulation/authority/motion/gate_geometry.py',
                         'simulation/authority/motion/gate_clearance.py',
                         'tests/simulation/test_kinematics.py',
                         'tests/simulation/test_gate_geometry.py',
                         'tests/simulation/test_gate_clearance.py',
                         'integration/motion.py', 'integration/test_motion.py'):
            self.assertIn(str((ROOT / relative).absolute()), result['source_before'])
        self.assertTrue(any('1000' in gap for gap in result['missing_evidence']))

    def test_secrecy_reference_selects_only_policy_when_live_environment_is_set(self):
        live = self.evidence / 'must-not-create-live-runs'
        with patch.dict(os.environ, DEEPEYE_ISOLATION_EVIDENCE_PARENT=str(live)):
            completed, result = self.cli('--suite', 'secrecy', '--reference-only')
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual('reference_passed', result['status'])
        self.assertEqual('reference_only', result['evidence_level'])
        self.assertFalse(result['formal_acceptance'])
        self.assertFalse(live.exists())
        self.assertEqual(1, len(result['commands']))
        stage = Path(result['run_dir']) / 'policy-tests'
        self.assertEqual([sys.executable, '-B', '-m', 'unittest', 'discover',
                          '-s', str(stage), '-p', 'test_policy.py', '-v'],
                         result['commands'][0]['command'])
        self.assertEqual(str(ROOT), result['commands'][0]['cwd'])
        self.assertEqual({'test_policy.py'}, {p.name for p in stage.iterdir()})
        expected = hashlib.sha256((ROOT / 'tests/isolation/test_policy.py').read_bytes()).hexdigest()
        self.assertEqual({str(stage / 'test_policy.py'): expected}, result['staged_source_before'])
        self.assertEqual(result['staged_source_before'], result['staged_source_after'])
        self.assertEqual(result['source_before'], result['source_after'])
        self.assertEqual('P1a policy/parser/helper unit tests only', result['reference_scope'])
        self.assertFalse(result['live_os_probes_run'])
        self.assertFalse(result['historical_windows_evidence_revalidated'])
        self.assertTrue(result['missing_evidence'])

    def test_secrecy_binds_all_p1a_source_and_test_dependencies(self):
        paths = runner.source_paths('secrecy')
        hashes = runner.snapshot(paths)
        for relative in ('simulation/isolation/__init__.py', 'simulation/isolation/policy.py',
                         'simulation/isolation/win32.py', 'simulation/isolation/prototype.py',
                         'simulation/isolation/fixture.py', 'tests/isolation/test_policy.py',
                         'tests/isolation/test_windows_live.py'):
            source = ROOT / relative
            self.assertIn(str(source), hashes)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), hashes[str(source)])

    def test_formal_secrecy_stays_blocked_with_live_environment(self):
        live = self.evidence / 'must-not-create-formal-live-runs'
        with patch.dict(os.environ, DEEPEYE_ISOLATION_EVIDENCE_PARENT=str(live)):
            completed, result = self.cli('--suite', 'secrecy')
        self.assertEqual(2, completed.returncode)
        self.assertEqual('blocked', result['status'])
        self.assertFalse(result['formal_acceptance'])
        self.assertEqual([], result['commands'])
        self.assertFalse(live.exists())
        self.assertFalse((Path(result['run_dir']) / 'policy-tests').exists())


if __name__ == '__main__':
    unittest.main()
