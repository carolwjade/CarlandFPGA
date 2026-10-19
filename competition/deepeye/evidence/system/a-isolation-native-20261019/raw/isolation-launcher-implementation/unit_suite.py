"""Run only selected offline cases. Never permit a real native fixture."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = Path.cwd()
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'tests/isolation'))
os.environ.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT', None)
temporary = HERE / 'temporary'
temporary.mkdir(exist_ok=True)
original_temp = tempfile.TemporaryDirectory


def owned_temp(*args, **kwargs):
    kwargs['dir'] = temporary
    return original_temp(*args, **kwargs)


# Existing policy ACL tests fail in lexical/empty-directory validation before
# native ACL calls. Stub the otherwise unrelated real token read in their setup.
from simulation.isolation import win32


class OfflineResult(unittest.TextTestResult):
    def startTest(self, test):
        self.token_patch = None
        if test.__class__.__module__ == 'test_policy':
            self.token_patch = patch.object(win32, 'user_sid', return_value='S-1-5-21-offline-test')
            self.token_patch.start()
        super().startTest(test)

    def stopTest(self, test):
        if self.token_patch is not None:
            self.token_patch.stop()
        super().stopTest(test)


with patch.object(tempfile, 'TemporaryDirectory', owned_temp):
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'test_owned_resources', 'test_windows_cleanup', 'test_prototype_cleanup',
        'test_resource_cleanup', 'test_policy', 'test_windows_live'])
    result = unittest.TextTestRunner(verbosity=2, resultclass=OfflineResult).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
