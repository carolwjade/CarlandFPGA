"""Mailbox state/timeline fixtures only: no inference, authentication or board."""
import copy
import dataclasses
import json
from pathlib import Path
import unittest

import boot_profile as boot
from test_host_envelope import encode, telem_document, candidate_document, CONTEXT
try:
    import candidate_mailbox as mailbox
except ModuleNotFoundError as error:
    if error.name != 'candidate_mailbox': raise
    mailbox = None

NS = 1_000_000
PRODUCT = Path(__file__).resolve().parents[1]


class MailboxTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(mailbox, 'selected mailbox implementation is absent')
        self.doc = boot.load_document(PRODUCT/'docs/boot_profiles.json')
        self.ctx = dict(CONTEXT, boot_sha256=boot.canonical_sha256(self.doc).hex())
        self.source, self.clock_domain = object(), object()
        self.owner = self.make()

    def make(self, profile=1, topology=1, source=True, clock=True, bounds=True):
        owner = mailbox.LatestCompletedMailbox(self.doc)
        self.ctx = dict(self.ctx, transport_profile_id=profile, topology_id=topology)
        owner.activate(encode(self.ctx), generation=1, slot_origin_ns=0,
            source=self.source if source else None, clock_domain=self.clock_domain if clock else None,
            bounds=mailbox.TransferBounds(10*NS,5*NS) if bounds else None, now_ns=0)
        return owner

    def observe(self, seq=9, sample=0, now=None, owner=None, mapped=True):
        owner = self.owner if owner is None else owner
        now = sample if now is None else now
        doc = telem_document(context=self.ctx, count=50 if self.ctx['transport_profile_id']==1 else 800,
            seq=seq, tick=seq, receipt=dict(lower_ns=now*NS,upper_ns=now*NS),
            adc_last=dict(lower_ns=sample*NS,upper_ns=sample*NS))
        if not mapped: doc['adc_last_interval_ns']=None
        raw=encode(doc)
        owner.observe(raw, sample_lower_ns=sample*NS if mapped else None, now_ns=now*NS)
        return raw

    def completion(self, seq=9, candidate=1, invocation=None, completed=150, dispatch=0,
                   deadline=2000, source=None, raw=None, generation=1):
        raw=raw or encode(candidate_document(context=self.ctx, candidate_id=candidate,
            observation=dict(context=self.ctx,observed_seq=seq),completed=completed*NS))
        return mailbox.Completion(generation,self.source if source is None else source,
            self.clock_domain,raw,candidate if invocation is None else invocation,
            dispatch*NS,completed*NS,completed*NS,deadline*NS)

    def grant(self, window=0, generation=1):
        return mailbox.SlotGrant(generation,window)

    def arm(self, **kw):
        self.observe(); c=self.completion(**kw);self.owner.complete(c,now_ns=c.completion_upper_ns);return c

    def test_literal_fast_stress_timelines_both_modes(self):
        vectors=json.loads((PRODUCT/'tests/vectors/r03_mailbox_lifecycle.json').read_bytes())
        self.assertEqual(len(vectors['timelines']),12)
        for topology in (1,2):
            for v in vectors['timelines']:
                with self.subTest(mode=topology,name=v['name']):
                    owner=self.make(v['profile'],topology)
                    self.observe(sample=v['sample_ms'],owner=owner)
                    c=self.completion(completed=v['completed_ms'],dispatch=v['sample_ms'],deadline=v['deadline_ms'])
                    self.assertTrue(owner.complete(c,now_ns=v['completed_ms']*NS))
                    got=owner.plan(v['now_ms']*NS,grant=self.grant(v['grant_window']))
                    if v['expected_slot_ms'] is None:self.assertIsNone(got)
                    else:
                        self.assertEqual(got.slot_start_ns,v['expected_slot_ms']*NS)
                        self.assertEqual(got.mode,'HIL_PC_FPGA' if topology==1 else 'PC_DIRECT')
                        self.assertEqual(got.candidate_raw,c.candidate_raw)

    def test_plan_does_not_consume_and_consume_requires_exact_slot(self):
        c=self.arm();g=self.grant()
        self.assertEqual(self.owner.plan(150*NS,grant=g).slot_start_ns,210*NS)
        self.assertIsNone(self.owner.consume(200*NS,grant=g))
        selected=self.owner.consume(210*NS,grant=g)
        self.assertEqual(selected.candidate_raw,c.candidate_raw)
        self.assertIsNone(self.owner.consume(210*NS,grant=g))
        self.assertIsNone(self.owner.plan(211*NS,grant=self.grant(1)))

    def test_late_consume_preserves_candidate_until_next_legal_slot(self):
        self.arm()
        self.assertIsNone(self.owner.consume(211*NS,grant=self.grant()))
        self.assertEqual(self.owner.plan(211*NS,grant=self.grant(1)).slot_start_ns,710*NS)
        self.assertIsNotNone(self.owner.consume(710*NS,grant=self.grant(1)))

    def test_later_arrival_of_older_observation_never_overwrites(self):
        self.observe(seq=9);self.observe(seq=10)
        newer=self.completion(seq=10,candidate=2,completed=150)
        self.owner.complete(newer,now_ns=150*NS)
        old=self.completion(seq=9,candidate=100,completed=250)
        self.assertFalse(self.owner.complete(old,now_ns=250*NS))
        self.assertEqual(self.owner.plan(250*NS,grant=self.grant(1)).candidate_raw,newer.candidate_raw)

    def test_newer_observation_completion_replaces_pending(self):
        self.observe(seq=9);self.observe(seq=10)
        self.owner.complete(self.completion(seq=9,candidate=1),now_ns=150*NS)
        new=self.completion(seq=10,candidate=2,completed=200)
        self.owner.complete(new,now_ns=200*NS)
        self.assertEqual(self.owner.plan(200*NS,grant=self.grant(1)).candidate_raw,new.candidate_raw)

    def test_same_observation_higher_candidate_and_invocation_can_replace(self):
        self.arm();new=self.completion(candidate=2,completed=200)
        self.assertTrue(self.owner.complete(new,now_ns=200*NS))
        self.assertEqual(self.owner.plan(200*NS,grant=self.grant(1)).candidate_raw,new.candidate_raw)

    def test_exact_duplicate_after_consume_cannot_rearm(self):
        c=self.arm();self.owner.consume(210*NS,grant=self.grant())
        self.assertFalse(self.owner.complete(c,now_ns=220*NS))
        self.assertIsNone(self.owner.plan(220*NS,grant=self.grant(1)))

    def test_conflicting_duplicate_cannot_extend_deadline(self):
        c=self.arm();changed=dataclasses.replace(c,deadline_ns=c.deadline_ns+NS)
        with self.assertRaises(ValueError):self.owner.complete(changed,now_ns=160*NS)
        self.assertTrue(self.owner.snapshot()['stopped'])

    def test_retired_candidate_cannot_return_after_newer_consumption(self):
        c=self.arm();new=self.completion(candidate=2,completed=180)
        self.owner.complete(new,now_ns=180*NS);self.owner.consume(210*NS,grant=self.grant())
        self.assertFalse(self.owner.complete(c,now_ns=220*NS))
        self.assertIsNone(self.owner.plan(220*NS,grant=self.grant(1)))

    def test_older_valid_observation_among_four_is_usable_then_eviction_blocks(self):
        for seq in range(9,13):self.observe(seq=seq)
        self.owner.complete(self.completion(seq=9),now_ns=150*NS)
        self.assertIsNotNone(self.owner.plan(150*NS,grant=self.grant()))
        self.observe(seq=13,sample=160,now=160)
        self.assertIsNone(self.owner.plan(160*NS,grant=self.grant()))
        self.assertEqual(self.owner.snapshot()['observation_count'],4)

    def test_duplicate_observation_preserves_original_age_and_conflict_stops(self):
        raw=self.observe();self.owner.observe(raw,sample_lower_ns=0,now_ns=100*NS)
        self.assertEqual(self.owner.snapshot()['observation_count'],1)
        with self.assertRaises(ValueError):self.owner.observe(raw,sample_lower_ns=NS,now_ns=100*NS)

    def test_age_cannot_be_renewed_by_late_completion(self):
        self.observe();c=self.completion(completed=1490,deadline=10000)
        self.owner.complete(c,now_ns=1490*NS)
        self.assertIsNone(self.owner.plan(1490*NS,grant=self.grant(3)))

    def test_unknown_source_clock_bounds_or_sample_has_no_selection(self):
        for which in ('source','clock','bounds','sample'):
            with self.subTest(which=which):
                owner=self.make(source=which!='source',clock=which!='clock',bounds=which!='bounds')
                self.observe(owner=owner,mapped=which!='sample')
                c=self.completion()
                c=dataclasses.replace(c,source=self.source if which!='source' else None,
                    clock_domain=self.clock_domain if which!='clock' else None)
                owner.complete(c,now_ns=150*NS)
                self.assertIsNone(owner.plan(150*NS,grant=self.grant()))

    def test_missing_wrong_generation_and_wrong_window_grants_preserve_pending(self):
        self.arm()
        self.assertIsNone(self.owner.plan(150*NS,grant=None))
        self.assertIsNone(self.owner.plan(150*NS,grant=self.grant(generation=2)))
        self.assertIsNone(self.owner.plan(150*NS,grant=self.grant(1)))
        self.assertIsNotNone(self.owner.plan(150*NS,grant=self.grant()))

    def test_stop_requires_fresh_activation_and_rejects_retired_session(self):
        self.arm();self.owner.stop('operator')
        self.assertIsNone(self.owner.plan(160*NS,grant=self.grant()))
        with self.assertRaises(ValueError):self.owner.activate(encode(self.ctx),generation=2,
            slot_origin_ns=0,source=self.source,clock_domain=self.clock_domain,bounds=None,now_ns=160*NS)
        fresh=dict(self.ctx,session=8)
        self.owner.activate(encode(fresh),generation=3,slot_origin_ns=0,
            source=self.source,clock_domain=self.clock_domain,bounds=mailbox.TransferBounds(0,0),now_ns=170*NS)
        self.ctx=fresh;self.observe(sample=170);c=self.completion(dispatch=170,completed=180,generation=3)
        self.owner.complete(c,now_ns=180*NS)
        self.assertIsNotNone(self.owner.plan(180*NS,grant=self.grant(generation=3)))

    def test_changed_epoch_mode_profile_same_session_never_reactivates(self):
        for change in ({'config_epoch':3},{'topology_id':2},{'transport_profile_id':2}):
            owner=self.make();self.observe(owner=owner)
            with self.assertRaises(ValueError):owner.activate(encode(dict(self.ctx,**change)),generation=2,
                slot_origin_ns=0,source=self.source,clock_domain=self.clock_domain,bounds=None,now_ns=NS)
            self.assertTrue(owner.snapshot()['stopped'])

    def test_new_session_retires_old_completion_context(self):
        c=self.arm();fresh=dict(self.ctx,session=8)
        self.owner.activate(encode(fresh),generation=2,slot_origin_ns=0,
            source=self.source,clock_domain=self.clock_domain,bounds=mailbox.TransferBounds(0,0),now_ns=160*NS)
        with self.assertRaises(ValueError):self.owner.complete(c,now_ns=170*NS)

    def test_clock_regression_and_bad_time_stop(self):
        for bad in (149*NS,True,-1,1.5):
            owner=self.make();self.observe(owner=owner);owner.complete(self.completion(),now_ns=150*NS)
            with self.assertRaises(ValueError):owner.plan(bad,grant=self.grant())
            self.assertTrue(owner.snapshot()['stopped'])

    def test_observation_half_range_and_wrap_stop(self):
        for first,second in ((0,32768),(65535,0),(10,9)):
            owner=self.make();self.observe(seq=first,owner=owner)
            with self.assertRaises(ValueError):self.observe(seq=second,owner=owner)
            self.assertTrue(owner.snapshot()['stopped'])

    def test_defensive_context_profile_and_snapshot(self):
        self.arm();self.doc['profiles']['fast_9600']['window_ms']=1
        self.ctx['session']=999;snap=self.owner.snapshot();snap['observation_sequences'].clear()
        self.assertEqual(self.owner.snapshot()['observation_count'],1)
        self.assertEqual(self.owner.plan(150*NS,grant=self.grant()).slot_start_ns,210*NS)

    def test_selection_and_completion_are_immutable(self):
        c=self.arm();selected=self.owner.plan(150*NS,grant=self.grant())
        with self.assertRaises(dataclasses.FrozenInstanceError):selected.deadline_ns=999
        with self.assertRaises(dataclasses.FrozenInstanceError):c.deadline_ns=999

    def test_source_association_and_causal_completion_are_required(self):
        for field,value in [('source',object()),('clock_domain',object()),('dispatch_lower_ns',151*NS),
                            ('completion_lower_ns',151*NS),('candidate_raw',bytearray(b'{}')),
                            ('invocation_id',True),('deadline_ns',150*NS)]:
            owner=self.make();self.observe(owner=owner);c=dataclasses.replace(self.completion(),**{field:value})
            with self.assertRaises(ValueError):owner.complete(c,now_ns=150*NS)

    def test_observation_mapping_must_remain_conservative(self):
        raw=self.observe()
        with self.assertRaises(ValueError):self.owner.observe(raw,sample_lower_ns=NS,now_ns=NS)

    def test_boot_digest_and_context_are_bound(self):
        owner=mailbox.LatestCompletedMailbox(self.doc)
        with self.assertRaises(ValueError):owner.activate(encode(dict(self.ctx,boot_sha256='0'*64)),generation=1,
            slot_origin_ns=0,source=self.source,clock_domain=self.clock_domain,bounds=None,now_ns=0)

    def test_bounded_session_retirement_and_observation_storage(self):
        for i in range(2,65):
            ctx=dict(self.ctx,session=100+i)
            self.owner.activate(encode(ctx),generation=i,slot_origin_ns=0,
                source=self.source,clock_domain=self.clock_domain,bounds=None,now_ns=i*NS)
        self.assertEqual(self.owner.snapshot()['retired_session_count'],64)
        with self.assertRaises(ValueError):self.owner.activate(encode(dict(self.ctx,session=999)),generation=65,
            slot_origin_ns=0,source=self.source,clock_domain=self.clock_domain,bounds=None,now_ns=65*NS)
        self.assertTrue(self.owner.snapshot()['stopped'])

    def test_different_candidates_cannot_consume_same_slot(self):
        self.arm(completed=100);self.owner.consume(210*NS,grant=self.grant())
        # Original completion was already ready before210; only consumed-slot
        # high-water, rather than transfer cost, must block this second result.
        c=self.completion(candidate=2,completed=180)
        self.owner.complete(c,now_ns=210*NS)
        self.assertIsNone(self.owner.consume(210*NS,grant=self.grant()))
        self.assertIsNotNone(self.owner.consume(710*NS,grant=self.grant(1)))


    def _check_stop_argument_binding(self, shape):
        for topology in (1, 2):
            with self.subTest(mode=topology, shape=shape):
                owner = self.make(topology=topology)
                self.observe(owner=owner)
                old = self.completion()
                self.assertTrue(owner.complete(old, now_ns=150*NS))
                self.assertIsNotNone(owner.plan(150*NS, grant=self.grant()))
                caught = None
                try:
                    if shape == 'unexpected_keyword':
                        owner.stop(reason='emergency', unexpected=True)
                    elif shape == 'too_many_positional':
                        owner.stop('emergency', 'extra')
                    else:
                        owner.stop('emergency', reason='duplicate')
                except (TypeError, ValueError) as error:
                    caught = error
                after = owner.snapshot()
                selected = owner.consume(210*NS, grant=self.grant())
                STOP_BINDING_TRACES.append({
                    'mode': topology, 'shape': shape,
                    'exception': None if caught is None else type(caught).__name__,
                    'snapshot_after_call': after,
                    'candidate_consumed_after_call': None if selected is None else selected.candidate_id,
                })
                self.assertTrue(after['stopped'], 'malformed STOP left activation live')
                self.assertIsNone(after['pending_candidate_id'])
                self.assertEqual(after['observation_count'], 0)
                self.assertIsNone(selected)
                self.assertIsInstance(caught, ValueError)
                self.assertIsInstance(caught.__cause__, TypeError)
                with self.assertRaises(ValueError):
                    owner.activate(encode(self.ctx), generation=2, slot_origin_ns=0,
                        source=self.source, clock_domain=self.clock_domain,
                        bounds=mailbox.TransferBounds(10*NS, 5*NS), now_ns=220*NS)
                self.assertTrue(owner.snapshot()['stopped'])
                with self.assertRaises(ValueError):
                    owner.complete(old, now_ns=221*NS)
                fresh = dict(self.ctx, session=self.ctx['session']+1)
                owner.activate(encode(fresh), generation=3, slot_origin_ns=0,
                    source=self.source, clock_domain=self.clock_domain,
                    bounds=mailbox.TransferBounds(10*NS, 5*NS), now_ns=230*NS)
                self.ctx = fresh
                self.observe(sample=230, owner=owner)
                new = self.completion(candidate=2, dispatch=230, completed=250, generation=3)
                self.assertTrue(owner.complete(new, now_ns=250*NS))
                self.assertEqual(owner.plan(250*NS, grant=self.grant(1, 3)).slot_start_ns, 710*NS)
                self.assertEqual(owner.consume(710*NS, grant=self.grant(1, 3)).candidate_raw, new.candidate_raw)
                self.assertFalse(owner.snapshot()['stopped'])

    def test_malformed_stop_unexpected_keyword_latches_both_modes(self):
        self._check_stop_argument_binding('unexpected_keyword')

    def test_malformed_stop_excess_positional_latches_both_modes(self):
        self._check_stop_argument_binding('too_many_positional')

    def test_malformed_stop_duplicate_reason_latches_both_modes(self):
        self._check_stop_argument_binding('duplicate_reason')

    def test_correctly_shaped_stop_forms_both_modes(self):
        for topology in (1, 2):
            for shape in ('default', 'positional', 'keyword'):
                with self.subTest(mode=topology, shape=shape):
                    owner = self.make(topology=topology)
                    self.observe(owner=owner)
                    owner.complete(self.completion(), now_ns=150*NS)
                    if shape == 'default':
                        owner.stop()
                    elif shape == 'positional':
                        owner.stop('operator')
                    else:
                        owner.stop(reason='operator')
                    self.assertTrue(owner.snapshot()['stopped'])
                    self.assertIsNone(owner.snapshot()['pending_candidate_id'])
                    self.assertIsNone(owner.consume(210*NS, grant=self.grant()))


STOP_BINDING_TRACES = []


if __name__=='__main__':unittest.main(verbosity=2)
