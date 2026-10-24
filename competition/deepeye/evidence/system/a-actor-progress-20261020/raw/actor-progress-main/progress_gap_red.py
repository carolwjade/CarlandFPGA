"""Three behavior-first RED witnesses; synthetic records are not authentication.

Only the preimplementation fixture attaches planned config fields to the exact
frozen config type. Current code ignores them. No product behavior is patched.
"""
from types import SimpleNamespace
from unittest.mock import patch
from competition.deepeye.tests.simulation.test_actor_composition import ActorCompositionTests, c, rt

class ProgressWitness(ActorCompositionTests):
    def setUp(self):
        super().setUp()
        self.started=self.clock.value
        self.deadline=self.started+5_000_000
        object.__setattr__(self.config,'progress_max_age_ns',5_000_000)
        object.__setattr__(self.config,'ai_model_sha256','a'*64)
        def completion(event,boot):
            request=rt.runtime.envelope._parse_message(self.channels._verify(event).raw)
            candidate={'schema_version':1,'kind':'model_candidate','context':request['context'],
                'candidate_id':request['candidate_id'],'model_sha256':'a'*64,
                'observation':request['observation'],'target':request['target'],
                'completed_monotonic_ns':self.started}
            return SimpleNamespace(boot=boot,source=self.channels,clock_domain=c.monotonic_ns,
                candidate_raw=rt.encode(candidate),invocation_id=request['candidate_id'],
                dispatch_lower_ns=self.started,completion_lower_ns=self.started,
                completion_upper_ns=self.started)
        self.channels.completion_for_command=completion

    def test_expiry_after_real_geometry_must_not_commit(self):
        self.arm();original=self.comp._executor.prepare_step
        def prepare(*args):
            value=original(*args);self.clock.value=self.deadline;return value
        with patch.object(self.comp._executor,'prepare_step',prepare):
            result=self.step()
        self.assertFalse(result.committed,'inference completion expired after geometry')
        self.assert_no_pose()

    def test_expiry_only_inside_commit_must_reach_final_fence(self):
        self.arm();original=self.comp._executor.commit_step
        def commit(prepared,before_commit):
            self.clock.value=self.deadline;return original(prepared,before_commit)
        with patch.object(self.comp._executor,'commit_step',commit):
            result=self.step()
        self.assertFalse(result.committed,'early progress snapshot cannot survive to CAS')
        self.assert_no_pose()

    def test_full_step_end_on_progress_deadline_must_fail(self):
        self.arm()
        result=self.comp.step(expected_pose_revision=0,dt_ns=5_000_000)
        self.assertFalse(result.committed,'whole dt must end strictly before progress expiry')
        self.assert_no_pose()
