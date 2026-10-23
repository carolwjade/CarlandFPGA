"""New v2 controls only; upstream source, bounds and clock are synthetic."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

from competition.deepeye.integration import boot_profile as boot, candidate_mailbox as mailbox

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_host_envelope import encode, telem_document, candidate_document, CONTEXT

NS = 1_000_000
S, E, W = 210*NS, 220*NS, 10*NS


def prepared(*, policy=True, width=W, topology=2, completed=150*NS,
             deadline=2000*NS, bounds=(10*NS, 5*NS), origin=0,
             source=True, clock=True, sample=0):
    """Synthetic upstream records, with real envelope and mailbox validation."""
    document = boot.load_document(Path(__file__).resolve().parents[1]/'docs/boot_profiles.json')
    context = dict(CONTEXT, topology_id=topology, boot_sha256=boot.canonical_sha256(document).hex())
    src, domain = object() if source else None, object() if clock else None
    owner = mailbox.LatestCompletedMailbox(document)
    options = dict(pc_direct_window_v2=mailbox.PcDirectWindowV2(width)) if policy else {}
    owner.activate(encode(context), generation=1, slot_origin_ns=origin, source=src,
        clock_domain=domain, bounds=None if bounds is None else mailbox.TransferBounds(*bounds),
        now_ns=origin, **options)
    observed = telem_document(context=context, count=50, seq=9, tick=9,
        receipt=dict(lower_ns=origin, upper_ns=origin),
        adc_last=dict(lower_ns=origin, upper_ns=origin))
    owner.observe(encode(observed), sample_lower_ns=sample, now_ns=origin)
    raw = encode(candidate_document(context=context, candidate_id=1,
        observation=dict(context=context, observed_seq=9), completed=completed))
    proof = mailbox.Completion(1,src,domain,raw,1,origin,completed,completed,deadline)
    owner.complete(proof, now_ns=completed)
    return owner, proof


def consume(owner, now, window=0):
    return owner.consume_pc_direct_v2(now, grant=mailbox.SlotGrant(1, window))


class PcDirectWindowV2Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(getattr(mailbox, 'PcDirectWindowV2', None),
                             'explicit PC_DIRECT v2 policy is required')

    def test_fixed_first_window_half_open_and_original_deadline(self):
        for now, expected in ((S-1,False),(S+1,True),(E,False),(E+1,False)):
            with self.subTest(now=now):
                owner, proof = prepared()
                got = consume(owner, now)
                self.assertEqual(got is not None, expected)
                if got is not None:
                    self.assertIs(type(got), mailbox.PcDirectWindowSelection)
                    self.assertEqual((got.slot_start_ns,got.window_close_ns,got.consumed_at_ns),
                                     (210000000,220000000,210000001))
                    self.assertEqual(got.candidate_raw,proof.candidate_raw)
        for now, expected in ((215*NS-1,True),(215*NS,False),(215*NS+1,False)):
            with self.subTest(deadline_now=now):
                owner,_ = prepared(deadline=215*NS)
                self.assertEqual(consume(owner,now) is not None,expected)

    def test_ready_must_precede_nominal_slot_even_inside_window(self):
        for extra, expected in ((0,True),(1,False)):
            with self.subTest(extra=extra):
                owner,_ = prepared(completed=200*NS,bounds=(10*NS,extra))
                self.assertEqual(consume(owner,S+1) is not None,expected)

    def test_grant_index_cannot_slide_with_now(self):
        owner,_ = prepared()
        self.assertIsNone(consume(owner,710*NS+1,0))
        got = consume(owner,710*NS+1,1)
        self.assertEqual((got.slot_start_ns,got.window_index),(710000000,1))
        owner,_ = prepared(deadline=710*NS)
        self.assertIsNone(consume(owner,710*NS,1))

    def test_once_consume_duplicate_and_newer_late_result_no_fallback(self):
        owner,proof = prepared()
        self.assertIsNotNone(consume(owner,S+1))
        self.assertFalse(owner.complete(proof,now_ns=S+1))
        self.assertIsNone(consume(owner,S+1))
        owner,proof = prepared()
        document = candidate_document(context=owner._context,candidate_id=2,
            observation=dict(context=owner._context,observed_seq=9),completed=S+1)
        newer = replace(proof,candidate_raw=encode(document),invocation_id=2,
                        completion_lower_ns=S+1,completion_upper_ns=S+1)
        self.assertTrue(owner.complete(newer,now_ns=S+1))
        self.assertIsNone(consume(owner,S+1))
        self.assertFalse(owner.complete(proof,now_ns=S+1))
        self.assertEqual(owner.snapshot()['pending_candidate_id'],2)

    def test_policy_and_entry_mixing_stops_instead_of_falling_back(self):
        for entry in ('consume','plan'):
            with self.subTest(entry=entry):
                owner,_ = prepared()
                with self.assertRaises(ValueError):
                    getattr(owner,entry)(S,grant=mailbox.SlotGrant(1,0))
                self.assertTrue(owner.snapshot()['stopped'])
        owner,_ = prepared(policy=False)
        with self.assertRaises(ValueError): consume(owner,S+1)
        self.assertTrue(owner.snapshot()['stopped'])
        for topology in (1,2):
            with self.subTest(legacy_topology=topology):
                owner,_ = prepared(policy=False,topology=topology)
                self.assertIsNone(owner.consume(S+1,grant=mailbox.SlotGrant(1,0)))
                owner,_ = prepared(policy=False,topology=topology)
                self.assertIsNotNone(owner.consume(S,grant=mailbox.SlotGrant(1,0)))

    def test_invalid_policy_topology_and_bounded_schedule(self):
        class IntSubclass(int): pass
        for width in (0,-1,True,IntSubclass(W),500*NS,mailbox.MAX_TIME+1):
            with self.subTest(width=width),self.assertRaises(ValueError): prepared(width=width)
        with self.assertRaises(ValueError): prepared(topology=1)
        with self.assertRaises(ValueError): prepared(origin=mailbox.MAX_TIME-100*NS)
        owner,_ = prepared()
        with self.assertRaises(ValueError): consume(owner,S+1,mailbox.MAX_TIME)
        self.assertTrue(owner.snapshot()['stopped'])

    def test_unknown_original_evidence_and_bad_generation_refuse(self):
        for options in (dict(source=False),dict(clock=False),dict(bounds=None),dict(sample=None)):
            with self.subTest(options=options):
                owner,_ = prepared(**options)
                self.assertIsNone(consume(owner,S+1))
        owner,_ = prepared()
        self.assertIsNone(owner.consume_pc_direct_v2(S+1,grant=mailbox.SlotGrant(2,0)))

    def test_regression_stop_and_bad_grant_are_irreversible(self):
        for bad in (True,mailbox.SlotGrant(True,0),mailbox.SlotGrant(1,True)):
            with self.subTest(bad=bad):
                owner,_ = prepared()
                with self.assertRaises(ValueError): owner.consume_pc_direct_v2(S+1,grant=bad)
                self.assertTrue(owner.snapshot()['stopped'])
        owner,_ = prepared()
        self.assertIsNone(consume(owner,S-1))
        with self.assertRaises(ValueError): consume(owner,S-2)
        self.assertIsNone(consume(owner,S+1))
        owner,_ = prepared(); owner.stop('operator')
        self.assertIsNone(consume(owner,S+1))

    def test_ready_and_original_sample_deadline_sums_are_bounded(self):
        owner,_ = prepared(bounds=(mailbox.MAX_TIME,1))
        with self.assertRaises(ValueError): consume(owner,S+1)
        origin = mailbox.MAX_TIME-1000*NS
        owner,_ = prepared(origin=origin,completed=origin+150*NS,
                           deadline=mailbox.MAX_TIME,sample=origin)
        with self.assertRaises(ValueError): consume(owner,origin+S+1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
