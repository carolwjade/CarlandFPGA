"""NEW error-routing identity controls; no actor launch, BOOT or numeric CAS."""
import threading
from types import SimpleNamespace as NS
import unittest

from competition.deepeye.simulation.authority import actor_composition as actors


class ActorStepCommitIdentityTests(unittest.TestCase):
    def fixture(self):
        # Deliberately unactivated software state, never a production factory
        # result. Only the actual wrapper/method's error routing is exercised.
        owner = object.__new__(actors.ActorComposition)
        owner._thread = threading.get_ident()
        owner._foreign = threading.Event()
        owner._busy = owner._retired = owner._world_pending_stop = False
        owner._veto = 0
        owner._input_transaction = owner._primary_error = None
        owner._errors = []
        owner._state = 'SOFTWARE_UNACTIVATED_FIXTURE'
        old = NS(committed=True, receipt=NS(pose_revision=7))
        owner._world_action_link = NS(slot=old)
        owner._checkpoint = lambda *args: None
        owner._active = owner._channel_health = lambda: None
        owner._remember = lambda error: owner._errors.append(error)
        def retire(reason):
            owner._retired = True
        owner._retire = retire
        owner._cleanup = lambda: None
        return owner, old

    def test_entry_failure_cannot_reissue_a_previous_committed_slot(self):
        owner, old = self.fixture()
        def step(owner):
            raise RuntimeError('new call failed before a new numeric slot')
        result = actors._entry(step)(owner)
        self.assertFalse(result.committed)
        self.assertIsNone(result.pose_revision)
        self.assertIs(old, owner._world_action_link.slot)

    def test_entry_failure_keeps_newly_committed_receipt_truth(self):
        owner, old = self.fixture()
        new = NS(committed=True, receipt=NS(pose_revision=8))
        def step(owner):
            owner._world_action_link.slot = new
            raise RuntimeError('software post-return failure')
        result = actors._entry(step)(owner)
        self.assertTrue(result.committed)
        self.assertEqual(8, result.pose_revision)

    def test_runtime_rejection_cannot_reissue_previous_receipt(self):
        owner, old = self.fixture()
        owner._runtime = NS(step=lambda **kwargs: NS(committed=False))
        result = actors.ActorComposition.step.__wrapped__(
            owner, expected_pose_revision=7, dt_ns=1_000_000)
        self.assertFalse(result.committed)
        self.assertIsNone(result.pose_revision)

    def test_runtime_post_return_rejection_preserves_new_slot_only(self):
        owner, old = self.fixture()
        new = NS(committed=True, receipt=NS(pose_revision=8))
        def rejected_after_new_receipt(**kwargs):
            owner._world_action_link.slot = new
            return NS(committed=False)
        owner._runtime = NS(step=rejected_after_new_receipt)
        result = actors.ActorComposition.step.__wrapped__(
            owner, expected_pose_revision=7, dt_ns=1_000_000)
        self.assertTrue(result.committed)
        self.assertEqual(8, result.pose_revision)


if __name__ == '__main__':
    unittest.main()
