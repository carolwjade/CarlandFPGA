import json
import unittest
from dataclasses import replace
from competition.deepeye.integration import candidate_mailbox as mailbox, completion_interval as interval, host_envelope
from competition.deepeye.simulation.authority import actor_composition as actor, candidate_owner as owner

CTX = dict(session=7, config_epoch=2, boot_sha256="a"*64, transport_profile_id=1, source_id=3, topology_id=1, acquisition_profile_id=1)
NOW = 5000000000

def record():
    doc = dict(schema_version=2, kind="model_candidate", context=CTX, candidate_id=1, model_sha256="b"*64, observation={"context":CTX, "observed_seq":9}, target=dict(action=1,yaw_q=0,pitch_q=0,speed_code=5,duration_ms=1), completion_observed_interval_ns={"lower_ns":NOW-1000,"upper_ns":NOW-100}, basis="host_dispatch_to_complete_result_observed_v1")
    bounds = mailbox.ObservedIntervalBoundsV2(100000000,NOW+90000000,NOW+80000000,None)
    return owner._CompletedInference(None,None,None,json.dumps(doc,separators=(",", ":")).encode(),1,NOW-1000,NOW-500,NOW-100,bounds)

class OriginalModuleControls(unittest.TestCase):
    def test_import_identity_and_exact_bounds(self):
        self.assertIs(owner.mailbox, mailbox)
        self.assertIs(actor._validate_interval_candidate, mailbox._validate_interval_candidate)
        p = record()
        result = mailbox._validate_interval_candidate(p, CTX, NOW, 100000000)
        self.assertIs(type(result), interval.IntervalCandidate)
        self.assertEqual(result.valid_until_ns, NOW+80000000)
        action = interval.adapt_action_candidate(result,host_issue_ns=NOW,now_ns=NOW,previous_deadline_ns=NOW+2000000)
        self.assertIs(action.candidate, result)
        self.assertEqual(action.authority,"none")

    def test_reject_forged_bounds_or_mismatched_observation(self):
        p = record()
        class Other(mailbox.ObservedIntervalBoundsV2): pass
        b = p.observed_interval_v2
        with self.assertRaises(ValueError):
            mailbox._validate_interval_candidate(replace(p, observed_interval_v2=Other(b.max_age_ns,b.source_deadline_ns,b.dispatch_deadline_ns,b.previous_deadline_ns)), CTX,NOW,100000000)
        with self.assertRaises(ValueError):
            mailbox._validate_interval_candidate(replace(p, completion_upper_ns=NOW-99), CTX,NOW,100000000)
        with self.assertRaises(ValueError):
            mailbox._validate_interval_candidate(p, CTX,NOW,99999999)

    def test_defaults_preserve_opt_in(self):
        self.assertFalse(actor.AuthorityConfig.__dataclass_fields__["enable_completion_interval_v2"].default)
        self.assertIsNone(owner._CompletedInference.__dataclass_fields__["observed_interval_v2"].default)
