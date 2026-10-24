"""Opt-in OS tests: create only fresh task profiles, ACLs and fixture processes.

Set DEEPEYE_ISOLATION_EVIDENCE_PARENT to an existing dedicated evidence folder.
These tests never discard run receipts, including expected timeout failures.
"""
import os
from pathlib import Path
import unittest


@unittest.skipUnless(os.name == 'nt' and os.environ.get('DEEPEYE_ISOLATION_EVIDENCE_PARENT'),
                     'requires explicit dedicated AppContainer evidence directory')
class WindowsLiveTests(unittest.TestCase):
    def test_real_boundary_and_profile_cleanup(self):
        from simulation.isolation.prototype import run
        receipt, evidence = run(Path(os.environ['DEEPEYE_ISOLATION_EVIDENCE_PARENT']))
        self.assertTrue(receipt.is_file())
        self.assertTrue(evidence['verdict']['passed'], evidence)
        self.assertTrue(evidence['lifecycle']['terminal'])
        self.assertTrue(evidence['lifecycle']['profile_deleted'])
        self.assertEqual(evidence['trusted']['job_limits']['ui_restrictions'], 255)
        self.assertTrue(evidence['inheritance']['excluded_canary_inheritable'])
        self.assertEqual(evidence.ownership.unresolved, ())
        self.assertTrue(evidence['cleanup']['resources_complete'])
        self.assertTrue(evidence['cleanup']['evidence_complete'])

    def test_timeout_is_failed_and_own_process_profile_are_cleaned(self):
        # A fixed sleeping replacement exercises launcher timeout without
        # loosening sandbox policy or attempting any additional resource access.
        from simulation.isolation import prototype
        from unittest.mock import patch
        original = prototype.stage_runtime
        def sleeping_fixture(base, stage):
            manifest = original(base, stage)
            source = b'import time; time.sleep(10)\n'
            (stage / 'fixture.py').write_bytes(source)
            manifest.append({'timeout_test_replacement': 'fixture.py',
                             'sha256': prototype.digest(source)})
            return manifest
        with patch.object(prototype, 'stage_runtime', sleeping_fixture):
            receipt, evidence = prototype.run(Path(os.environ['DEEPEYE_ISOLATION_EVIDENCE_PARENT']),
                                              timeout_ms=100)
        self.assertTrue(receipt.is_file())
        self.assertFalse(evidence['verdict']['passed'])
        self.assertEqual(evidence['error']['type'], 'TimeoutError')
        self.assertTrue(evidence['lifecycle']['terminated_by_launcher'])
        self.assertTrue(evidence['lifecycle']['terminal'])
        self.assertTrue(evidence['lifecycle']['profile_deleted'])
        self.assertEqual(evidence.ownership.unresolved, ())

    def test_persistence_failure_after_process_creation_still_cleans_owned_objects(self):
        # Prepared only: the author job never enables this native test class.
        from simulation.isolation import prototype
        original = prototype.save
        failures = []
        def failing_save(path, value):
            if path.name == 'receipt.json' and isinstance(value, dict) and 'pid' in value:
                failures.append(value['pid'])
                raise OSError('intentional persistence failure after process creation')
            return original(path, value)
        receipt, evidence = prototype.run(Path(os.environ['DEEPEYE_ISOLATION_EVIDENCE_PARENT']),
                                           report_save=failing_save)
        self.assertTrue(failures)
        self.assertEqual(evidence['error']['type'], 'OSError')
        self.assertEqual(evidence['error']['message'], 'intentional persistence failure after process creation')
        self.assertFalse(evidence['verdict']['passed'])
        self.assertFalse(evidence['cleanup']['evidence_complete'])
        self.assertTrue(evidence['cleanup']['resources_complete'])
        self.assertTrue(evidence['lifecycle']['terminal'])
        self.assertTrue(evidence['lifecycle']['profile_deleted'])
        self.assertEqual(evidence.ownership.unresolved, ())
        # Receipt is an earlier acknowledged snapshot. Preserve the returned
        # in-memory result separately; do not relabel that stale file as final.
        recovery = receipt.parent / 'expected-persistence-failure-memory.json'
        original(recovery, evidence)


if __name__ == '__main__':
    unittest.main()
