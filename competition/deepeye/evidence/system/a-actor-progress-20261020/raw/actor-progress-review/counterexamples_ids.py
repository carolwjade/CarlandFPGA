"""Additional monotonic-ID and exact-byte counterexamples."""
from __future__ import annotations

from dataclasses import replace
import json
import unittest

from competition.deepeye.tests.simulation import test_actor_composition as tc
from competition.deepeye.tests.simulation import test_pc_direct_runtime as rt

c = tc.c


class ProgressIdentityCounterexamples(unittest.TestCase):
    def setUp(self):
        self.fixture = tc.ActorCompositionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.arm()
        self.comp = self.fixture.comp
        self.channels = self.fixture.channels
        self.old = self.comp._progress.bound

    def make_request(self, *, sequence, candidate_id, invocation):
        self.fixture.clock.value += 1_000_000
        self.fixture.f.observe(seq=10)
        context = json.loads(self.comp._boot.context_json)
        target = dict(action=1, yaw_q=0, pitch_q=0, speed_code=5, duration_ms=1000)
        request = rt.request_document(
            context=context,
            command_seq=sequence,
            candidate_id=candidate_id,
            issue=self.fixture.clock.value,
            target_value=target,
            observation=dict(context=context, observed_seq=10),
        )
        candidate = dict(
            schema_version=1,
            kind='model_candidate',
            context=request['context'],
            candidate_id=request['candidate_id'],
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
            invocation,
            request['host_issue_monotonic_ns'],
            request['host_issue_monotonic_ns'],
            request['host_issue_monotonic_ns'],
        )
        self.channels.completions[(id(self.comp._boot), request['candidate_id'])] = proof
        return request, proof

    def event(self, request):
        return self.channels.event(rt.runtime.VerifiedEnvelope(self.comp._boot, rt.encode(request)))

    def test_new_sequence_with_non_increasing_candidate_id_rejects(self):
        request, _ = self.make_request(sequence=4, candidate_id=self.old.candidate_id,
                                       invocation=self.old.invocation_id + 1)
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.event(request))
        self.assertIs(self.comp._progress.bound, self.old)
        self.assertTrue(self.comp._progress.revoked)
        self.fixture.assert_no_pose()

    def test_new_sequence_and_candidate_with_non_increasing_invocation_rejects(self):
        request, _ = self.make_request(sequence=4, candidate_id=4,
                                       invocation=self.old.invocation_id)
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.event(request))
        self.assertIs(self.comp._progress.bound, self.old)
        self.assertTrue(self.comp._progress.revoked)
        self.fixture.assert_no_pose()

    def test_semantically_equal_candidate_bytes_do_not_count_as_exact_duplicate(self):
        record = self.comp._command_record
        original = next(iter(self.channels.completions.values()))
        candidate = rt.runtime.envelope._parse_message(original.candidate_raw)
        changed_bytes = json.dumps(candidate, ensure_ascii=False, separators=(', ', ': ')).encode('utf-8')
        self.assertNotEqual(changed_bytes, original.candidate_raw)
        self.channels.completions[(id(self.comp._boot), self.old.candidate_id)] = replace(
            original, candidate_raw=changed_bytes)
        self.fixture.clock.value += 1_000_000
        with self.assertRaises(tc.c.CompositionRejected):
            self.comp.accept_command(self.channels.event(record))
        self.assertIs(self.comp._progress.bound, self.old)
        self.assertTrue(self.comp._progress.revoked)
        self.fixture.assert_no_pose()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProgressIdentityCounterexamples)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)