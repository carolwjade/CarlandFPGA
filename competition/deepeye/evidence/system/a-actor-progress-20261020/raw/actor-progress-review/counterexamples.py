"""Independent adversarial scenarios for the frozen actor progress gate."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from competition.deepeye.tests.simulation import test_actor_composition as tc
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt

c = tc.c
BASE = Path(__file__).resolve().parent


class ProgressCounterexamples(unittest.TestCase):
    def setUp(self):
        self.fixture = tc.ActorCompositionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.arm()
        self.comp = self.fixture.comp
        self.channels = self.fixture.channels

    def request_document(self, *, sequence, candidate_id, observation, issue, duration=1000):
        context = json.loads(self.comp._boot.context_json)
        target = dict(action=1, yaw_q=0, pitch_q=0, speed_code=5, duration_ms=duration)
        return rt.request_document(
            context=context,
            command_seq=sequence,
            candidate_id=candidate_id,
            issue=issue,
            target_value=target,
            observation=dict(context=context, observed_seq=observation),
        )

    def proof_for(self, request, *, invocation_id, completion_lower=None, completion_upper=None,
                  candidate_id=None):
        lower = request['host_issue_monotonic_ns'] if completion_lower is None else completion_lower
        upper = request['host_issue_monotonic_ns'] if completion_upper is None else completion_upper
        candidate = dict(
            schema_version=1,
            kind='model_candidate',
            context=request['context'],
            candidate_id=request['candidate_id'] if candidate_id is None else candidate_id,
            model_sha256='a' * 64,
            observation=request['observation'],
            target=request['target'],
            completed_monotonic_ns=request['host_issue_monotonic_ns'],
        )
        proof = c._CompletedInference(
            self.comp._boot,
            self.channels,
            c.monotonic_ns,
            rt.encode(candidate),
            invocation_id,
            request['host_issue_monotonic_ns'],
            lower,
            upper,
        )
        self.channels.completions[(id(self.comp._boot), request['candidate_id'])] = proof
        return proof

    def command_event(self, request):
        return rt.runtime.VerifiedEnvelope(self.comp._boot, rt.encode(request))

    def test_candidate_id_mismatch_is_rejected(self):
        self.fixture.clock.value += 1_000_000
        self.fixture.f.observe(seq=10)
        request = self.request_document(sequence=4, candidate_id=4, observation=10,
                                        issue=self.fixture.clock.value)
        old = self.comp._progress.bound
        self.proof_for(request, invocation_id=old.invocation_id + 1, candidate_id=5)
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.channels.event(self.command_event(request)))
        self.assertTrue(self.comp._progress.revoked)
        self.assertIs(self.comp._progress.bound, old)
        self.fixture.assert_no_pose()

    def test_full_target_mismatch_is_rejected(self):
        self.fixture.clock.value += 1_000_000
        self.fixture.f.observe(seq=10)
        request = self.request_document(sequence=4, candidate_id=4, observation=10,
                                        issue=self.fixture.clock.value)
        old = self.comp._progress.bound
        proof = self.proof_for(request, invocation_id=old.invocation_id + 1)
        candidate = rt.runtime.envelope._parse_message(proof.candidate_raw)
        candidate['target']['duration_ms'] = 999
        self.channels.completions[(id(self.comp._boot), 4)] = replace(proof, candidate_raw=rt.encode(candidate))
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.channels.event(self.command_event(request)))
        self.assertTrue(self.comp._progress.revoked)
        self.assertIs(self.comp._progress.bound, old)
        self.fixture.assert_no_pose()

    def test_changed_request_issue_and_completion_upper_do_not_renew_duplicate(self):
        old = self.comp._progress.bound
        original = next(iter(self.channels.completions.values()))
        self.fixture.clock.value += 10_000_000
        request = self.request_document(sequence=old.command_seq, candidate_id=old.candidate_id,
                                        observation=9, issue=self.fixture.clock.value)
        self.channels.completions[(id(self.comp._boot), old.candidate_id)] = replace(
            original, completion_upper_ns=self.fixture.clock.value)
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.channels.event(self.command_event(request)))
        self.assertTrue(self.comp._progress.revoked)
        self.assertIs(self.comp._progress.bound, old)
        self.assertEqual(self.comp._progress.bound.deadline_ns,
                         original.completion_lower_ns + self.fixture.config.progress_max_age_ns)
        self.fixture.assert_no_pose()

    def test_changed_invocation_for_identical_bytes_does_not_renew(self):
        old = self.comp._progress.bound
        record = self.comp._command_record
        original = next(iter(self.channels.completions.values()))
        self.channels.completions[(id(self.comp._boot), old.candidate_id)] = replace(
            original, invocation_id=original.invocation_id + 1)
        self.fixture.clock.value += 1_000_000
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.channels.event(record))
        self.assertTrue(self.comp._progress.revoked)
        self.assertIs(self.comp._progress.bound, old)
        self.fixture.assert_no_pose()

    def test_new_command_with_later_completion_extends_and_commits(self):
        old = self.comp._progress.bound
        self.fixture.clock.value += 1_000_000
        self.fixture.f.observe(seq=10)
        request = self.request_document(sequence=4, candidate_id=4, observation=10,
                                        issue=self.fixture.clock.value)
        self.proof_for(request, invocation_id=old.invocation_id + 1)
        self.comp.accept_command(self.channels.event(self.command_event(request)))
        current = self.comp._progress.bound
        self.assertGreater(current.command_seq, old.command_seq)
        self.assertGreater(current.candidate_id, old.candidate_id)
        self.assertGreater(current.invocation_id, old.invocation_id)
        self.assertGreater(current.deadline_ns, old.deadline_ns)
        result = self.comp.step(expected_pose_revision=0, dt_ns=1_000_000)
        self.assertTrue(result.committed)
        self.assertEqual(result.pose_revision, 1)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProgressCounterexamples)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)