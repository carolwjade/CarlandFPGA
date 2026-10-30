"""NEW effect-witness controls on distinct software records; no Root grant."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
from competition.deepeye.simulation.authority import motion_executor as motion
from competition.deepeye.simulation.authority import original_world_actor_link as links


class OriginalCommitEffectWitnessTests(unittest.TestCase):
    def records(self):
        pose = SimpleNamespace(position_m=(0., 0., 0.), orientation_xyzw=(0., 0., 0., 1.))
        frame = motion._CommitFrame(None, None, (), (), None, None)
        before = motion._Root(4, 2, pose, 1, object(), frame, object(), object(), False, False, False, 10)
        candidate_frame = motion._CommitFrame(None, None, (), (), frame, None)
        candidate_pose = SimpleNamespace(position_m=(.001, 0., 0.), orientation_xyzw=(0., 0., 0., 1.))
        candidate = replace(before, revision=5, pose=candidate_pose, pose_revision=2,
                            frame=candidate_frame, executed_until_ns=20)
        return before, candidate

    def observe(self, before, candidate, current):
        method = getattr(links, '_candidate_effect_observation', None)
        self.assertTrue(callable(method), 'original candidate effect witness is missing')
        return method(before, candidate, current)

    def test_preallocation_does_not_prove_installation(self):
        before, candidate = self.records()
        self.assertEqual('candidate_not_observed', self.observe(before, candidate, before))

    def test_exact_candidate_current_is_an_observed_effect(self):
        before, candidate = self.records()
        self.assertEqual('candidate_root_current', self.observe(before, candidate, candidate))

    def test_immediate_revoke_retains_observed_candidate_frame(self):
        before, candidate = self.records()
        revoked = replace(candidate, revision=6, revoke_generation=3,
                          stopped=True, command=None)
        self.assertEqual('candidate_frame_retained_by_revoke',
                         self.observe(before, candidate, revoked))

    def test_equal_coordinates_and_foreign_frame_are_not_effect_proof(self):
        before, candidate = self.records()
        foreign_pose = SimpleNamespace(**vars(candidate.pose))
        unrelated = replace(candidate, pose=foreign_pose,
                            frame=motion._CommitFrame(None, None, (), (), before.frame, None))
        self.assertEqual('unclassified_root', self.observe(before, candidate, unrelated))

    def test_wrong_generation_cannot_be_classified_as_immediate_revoke(self):
        before, candidate = self.records()
        unrelated = replace(candidate, revision=9, revoke_generation=8,
                            stopped=True, command=None)
        self.assertEqual('unclassified_root', self.observe(before, candidate, unrelated))

    def test_software_callback_cannot_become_an_original_stage_witness(self):
        before, candidate = self.records()
        stage = getattr(links, '_stage_original_commit_witness', None)
        self.assertTrue(callable(stage))
        executor = object.__new__(motion.OwnedMotionExecutor)
        executor._original_world_witness = SimpleNamespace(
            callback=lambda: self.fail('caller callback must not execute'))
        with self.assertRaises((ValueError, RuntimeError)):
            stage(executor, object(), before, candidate, candidate.frame, object())


if __name__ == '__main__': unittest.main()
