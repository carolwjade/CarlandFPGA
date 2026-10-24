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


if __name__ == '__main__':
    unittest.main()
