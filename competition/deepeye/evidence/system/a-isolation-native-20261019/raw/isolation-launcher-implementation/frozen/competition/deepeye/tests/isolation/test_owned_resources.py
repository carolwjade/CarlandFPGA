"""Owner registry contracts with no native resources."""
from types import SimpleNamespace
import unittest
from simulation.isolation.resource_cleanup import Outcome, Provenance
try:
    from simulation.isolation.owned_resources import OwnedResources, OwnedReleaseError
except ImportError:
    OwnedResources = None


class OwnedTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(OwnedResources, 'owner-bound acquisition is missing')
        self.owner = OwnedResources(Provenance('task/v1', 'work', 'owner', (('source', 'a' * 64),)))

    def test_close_unknown_is_still_owned_and_not_retried(self):
        calls = []
        self.owner.bind_releaser(lambda ref: calls.append(ref) or Outcome.UNKNOWN)
        ref = self.owner.own_handle('pipe', 11)
        self.assertEqual(self.owner.release_once(ref), Outcome.UNKNOWN)
        self.assertEqual(self.owner.release_once(ref), Outcome.UNKNOWN)
        self.assertEqual(calls, [ref])
        self.assertIn(ref, self.owner.unresolved)
        with self.assertRaises(OwnedReleaseError):
            self.owner.release_checked(ref)
        self.assertEqual(calls, [ref])

    def test_numeric_reuse_requires_confirmed_previous_close_and_new_instance(self):
        self.owner.bind_releaser(lambda ref: Outcome.CONFIRMED)
        old = self.owner.own_handle('old', 12)
        with self.assertRaises(ValueError):
            self.owner.own_handle('alias', 12)
        self.owner.release_checked(old)
        new = self.owner.own_handle('new', 12)
        self.assertIsNot(old, new)
        self.assertNotEqual(old.resource_id, new.resource_id)
        self.assertNotIn(old, self.owner.unresolved)
        self.assertIn(new, self.owner.unresolved)

    def test_release_exception_retains_exact_error_and_original_reference(self):
        def fail(ref):
            raise OSError('close response lost')
        self.owner.bind_releaser(fail)
        ref = self.owner.own_handle('pipe', 13)
        self.assertEqual(self.owner.release_once(ref), Outcome.UNKNOWN)
        self.assertEqual(self.owner.errors[0].message, 'close response lost')
        self.assertIn(ref, self.owner.unresolved)

    def test_profile_and_process_pair_are_immediately_in_owned_plan(self):
        profile = self.owner.own_profile('fresh-profile', 1000)
        process, thread = self.owner.own_process(SimpleNamespace(hProcess=21, hThread=22, dwProcessId=99))
        self.assertEqual({r.label for r in self.owner.references}, {'profile', 'profile_sid', 'process', 'primary_thread'})
        self.assertEqual(process.native, 21)
        self.assertEqual(thread.native, 22)
        self.assertEqual(process.profile_id, profile.resource_id)
        self.assertTrue(thread.recovery)

    def test_foreign_reference_cannot_close_owned_numeric_handle(self):
        calls = []
        self.owner.bind_releaser(lambda ref: calls.append(ref) or Outcome.CONFIRMED)
        other = OwnedResources(Provenance('task/v1', 'work2', 'owner2', (('source', 'b' * 64),)))
        ref = other.own_handle('foreign', 13)
        with self.assertRaises(ValueError):
            self.owner.release_once(ref)
        self.assertEqual(calls, [])

    def test_new_acquisition_after_unknown_numeric_release_is_retained_as_ambiguous(self):
        self.owner.bind_releaser(lambda ref: Outcome.UNKNOWN)
        old = self.owner.own_handle('old', 12)
        self.owner.release_once(old)
        with self.assertRaises(ValueError):
            self.owner.own_handle('new_acquisition', 12)
        self.assertEqual({ref.label for ref in self.owner.unresolved}, {'old', 'new_acquisition'})
        self.assertTrue(all(ref.ambiguous for ref in self.owner.unresolved))
