"""NEW software lineage/readback controls. No authenticated Root/native grant.

The lifecycle specimen explicitly replaces the original-link custody check on
a DIFFERENT software book. It tests recorder sequencing, not authentication.
"""
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace as NS
from unittest.mock import patch
import struct
import unittest

from competition.deepeye.simulation.authority import _actor_source_custody as actors
from competition.deepeye.simulation.authority import motion_executor as motion
from competition.deepeye.simulation.authority import original_world_actor_link as links
from competition.deepeye.simulation.authority import _world_loop as worlds
from competition.deepeye.tests.integration import test_source_book_em_receipt as em_fixtures


class ActorSourceCustodyTests(unittest.TestCase):
    def specimen(self):
        f = em_fixtures.ScopedEmReceiptTests()
        f.fixture(); token = f.open(0); f.em(token); f.finish(token, 0)
        book = f.book
        link = NS(book=book, source=f.source, owner=f.world, executor=f.world.executor,
                  claimed=True, slot=None, _registered=lambda: None)
        custody = actors._ActorSourceCustody(actors._KEY, link, book)
        # Explicit software-only specimen: never call the original factory or
        # label this replaced custody boundary an original capability.
        def software_context(transition=None):
            if transition is None:
                if custody.pending is not None:
                    raise ValueError('software source excluded during transition')
            elif transition is not custody.pending or transition.closed:
                raise ValueError('exact pending software transition required')
        context = patch.object(custody, '_context', side_effect=software_context)
        context.start(); self.addCleanup(context.stop)
        book._actor_custody = custody
        boot = object()
        actor = NS(_world_action_link=link, _executor=link.executor, _busy=True,
            _retired=False, _state='ACTIVE', _boot=boot,
            _runtime=NS(_latched=False, _boot=boot, _command=None),
            _executor_activation=boot, _runtime_activation=boot,
            _progress=NS(observe_time=lambda now: now))
        link.composition = actor
        return f, link, custody, actor, boot

    def activate(self, f, link, custody, actor, boot):
        f.clock.now += 1000
        t = custody.reserve(actor, 'BOOT')
        root = link.executor._root
        link.executor._root = replace(root, revision=root.revision+1,
            revoke_generation=root.revoke_generation+1, boot=boot, stopped=False)
        f.clock.now += 1000; custody.finish_nonspatial(t)
        f.clock.now += 1000; t = custody.reserve(actor, 'COMMAND')
        command = motion._Command(boot, b'software-command', 1, f.clock.now,
            f.clock.now+100_000_000, 'fast_9600', 1, 0, 0)
        link.executor._root = replace(link.executor._root,
            revision=link.executor._root.revision+1, command=command)
        actor._input_transaction = NS(request_raw=command.raw)
        actor._command_record = NS(raw=command.raw)
        actor._runtime._command = command
        f.clock.now += 1000; custody.finish_nonspatial(t)

    def test_software_lifecycle_preserves_prefix_origin_and_held_receipt(self):
        f, link, custody, actor, boot = self.specimen()
        original = f.book.evidence()['samples'][0]
        origin = f.source._origin; profile = f.source._profile
        self.activate(f, link, custody, actor, boot)
        token = f.open(10); f.finish(token, 10)
        evidence = f.book.evidence()
        self.assertEqual(3, evidence['schema'])
        self.assertIsNone(evidence['fixed_root_interval'])
        self.assertEqual(original, evidence['samples'][0])
        self.assertEqual(origin, f.source._origin); self.assertIs(profile, f.source._profile)
        self.assertEqual(original['held_em_association']['original_em'],
                         evidence['samples'][1]['held_em_association']['original_em'])
        self.assertEqual([0, 2], [s['numerical_pose_span']['root_revision'] for s in evidence['samples']])
        self.assertEqual(['COMPLETE', 'COMPLETE'],
            [t['state'] for t in evidence['actor_pose_intervals']['transitions']])
        self.assertTrue(all(t['exact_commit_qpc_ns'] is None
            for t in evidence['actor_pose_intervals']['transitions']))

    def test_software_pending_step_excludes_source_without_resuming_failed_book(self):
        f, link, custody, actor, boot = self.specimen()
        self.activate(f, link, custody, actor, boot)
        f.clock.now += 1000; t = custody.reserve(actor, 'STEP')
        with self.assertRaises(ValueError):
            f.book.current_pose_interval()
        # A public book failure is terminal, so this refusal specimen cannot
        # be resumed. It also cannot roll back a later numerical effect.
        self.assertEqual('FAILED', f.book.evidence()['state'])
        self.assertIs(custody.pending, t)

    def test_software_step_closure_starts_span_at_actual_completion_observation(self):
        f, link, custody, actor, boot = self.specimen()
        self.activate(f, link, custody, actor, boot)
        f.clock.now += 1000; t = custody.reserve(actor, 'STEP')
        before = link.executor._root
        end = f.clock.now+10000
        pose = NS(position_m=(.001, 0., 0.), orientation_xyzw=(0., 0., 0., 1.))
        after = replace(before, revision=before.revision+1, pose=pose,
            pose_revision=before.pose_revision+1, executed_until_ns=end)
        link.executor._root = after
        actor._busy = False; actor._runtime._stepping = False
        actor._runtime._executed_until_ns = end
        slot = NS(book_transition=t, uncertainty=None, committed=True,
            receipt=NS(end_ns=end), getter_admitted=True, post_root=after,
            pre_cas_qpc_ns=t.lower+1000, post_cas_observed_qpc_ns=t.lower+2000,
            deadline_ns=end+1000000, publication=NS(operation_id='software-only',
                                                  readback_ns=t.lower+3000))
        link.slot = slot
        f.clock.now = end+1000
        observed = custody.finish_step(slot)
        self.assertEqual(f.clock.now, observed)
        self.assertGreaterEqual(observed, end)
        evidence = f.book.evidence()
        self.assertEqual(observed, evidence['current_pose_interval']['from_qpc_ns'])
        self.assertEqual(1, evidence['current_pose_interval']['pose_revision'])
        self.assertEqual(0, evidence['samples'][0]['held_em_association']['original_em']['pose_revision'])
        self.assertIsNone(t.record['exact_commit_qpc_ns'])
        self.assertEqual('COMPLETE', t.record['state'])

    def test_uncertain_successor_is_retained_and_source_is_terminal(self):
        f, link, custody, actor, boot = self.specimen()
        f.clock.now += 1000; t = custody.reserve(actor, 'BOOT')
        successor = replace(link.executor._root, revision=99)
        link.executor._root = successor
        custody.abort(t, 'software post-effect uncertainty')
        self.assertIs(successor, link.executor._root)
        self.assertEqual('FAILED', f.book.evidence()['state'])
        self.assertEqual(1, len(f.book.evidence()['samples']))
        self.assertEqual('FAILED', t.record['state'])

    def test_default_fixed_book_still_rejects_equal_pose_root_change(self):
        f = em_fixtures.ScopedEmReceiptTests(); f.fixture()
        f.world.executor._root = replace(f.world.executor._root, revision=1,
                                         revoke_generation=1, boot=object())
        with self.assertRaises(ValueError): f.book.current_pose_interval()
        self.assertEqual('FAILED', f.book.evidence()['state'])

    def test_default_fixed_book_keeps_original_revision_snapshot_check(self):
        f = em_fixtures.ScopedEmReceiptTests(); f.fixture()
        # Deliberate private corruption remains a refusal in the fixed default.
        object.__setattr__(f.world.executor._root, 'revision', 1)
        with self.assertRaises(ValueError): f.book.current_pose_interval()

    def test_software_link_cannot_issue_original_actor_book(self):
        with self.assertRaises(ValueError): actors._issue_original_actor_book(NS())

    def test_later_fresh_software_em_is_recorded_under_new_nonspatial_lineage(self):
        f, link, custody, actor, boot = self.specimen()
        original_em = f.book.evidence()['samples'][0]['held_em_association']['original_em']
        self.activate(f, link, custody, actor, boot)
        token = f.open(50); f.em(token, 50); f.finish(token, 50)
        records = f.book.evidence()['samples']
        self.assertEqual(original_em, records[0]['held_em_association']['original_em'])
        current = records[1]['held_em_association']['original_em']
        self.assertEqual(50, current['tick_ms']); self.assertEqual(2, current['root_revision'])
        self.assertEqual(0, current['pose_revision'])

    def test_public_owner_entry_refuses_foreign_object_before_property_access(self):
        class Foreign:
            @property
            def owner(self): raise AssertionError('foreign property must not execute')
        owner = object.__new__(worlds._RootWorldOwner)
        with self.assertRaises(ValueError): owner.actor_source_book(Foreign())
        with self.assertRaises(ValueError): owner.progress_actor_commit(Foreign())

    def test_foreign_custody_object_cannot_be_installed_by_flag(self):
        f = em_fixtures.ScopedEmReceiptTests(); f.fixture()
        f.book._actor_custody = NS(_context=lambda *a: self.fail('foreign callback executed'))
        with self.assertRaises(ValueError): f.book.current_pose_interval()

    def test_abort_retains_unreturned_effect_without_making_a_receipt(self):
        f, link, custody, actor, boot = self.specimen()
        f.clock.now += 1000; t = custody.reserve(actor, 'BOOT')
        link.slot = NS(book_transition=t, effect_observation='candidate_frame_retained_by_revoke',
                       receipt=None)
        custody.abort(t, 'software unreturned numerical effect')
        self.assertEqual('candidate_frame_retained_by_revoke', t.record['effect_observation'])
        self.assertFalse(t.record['returned_receipt_observed'])
        self.assertIsNone(link.slot.receipt)

    def test_equal_pose_revoke_and_foreign_command_are_not_nonspatial_authority(self):
        f = em_fixtures.ScopedEmReceiptTests(); f.fixture()
        before = f.world.executor._root; boot = object()
        after = replace(before, revision=1, revoke_generation=1, boot=boot, stopped=False)
        actors._nonspatial_lineage(before, after, 'BOOT', boot)
        with self.assertRaises(ValueError):
            actors._nonspatial_lineage(before, replace(after, stopped=True), 'BOOT', boot)
        c = motion._Command(boot, b'a', 1, 0, 100, 'fast_9600', 1, 0, 0)
        commanded = replace(after, revision=2, command=c)
        actors._nonspatial_lineage(after, commanded, 'COMMAND', boot, b'a')
        with self.assertRaises(ValueError):
            actors._nonspatial_lineage(after, commanded, 'COMMAND', boot, b'b')
        with self.assertRaises(ValueError):
            actors._nonspatial_lineage(after, replace(commanded, revoke_generation=2), 'COMMAND', boot, b'a')


class EndpointReadbackControls(unittest.TestCase):
    def check(self, translation=F(0), cap=F(1, 100000), matrix_error=F(0)):
        def token(x): return struct.pack('>d', float(x)).hex()
        transform = dict(basis_columns=[[token(1+matrix_error), token(0), token(0)],
            [token(0), token(1), token(0)], [token(0), token(0), token(1)]],
            origin=[token(translation), token(0), token(0)])
        model = NS(half_segment=F(1), radius=F(1, 10), pivot_radius=F(11, 10))
        d = NS(getter_endpoint_cap_m=cap, numeric_m=F(1, 10000)+cap,
            policy_guard_m=F(1, 10000), asset_m=F(3, 1000),
            full_drill_containment_upper_m=F(3, 1000))
        return links._readback_endpoint_bound((0., 0., 0.), (0., 0., 0., 1.),
                                              transform, 64, model, d)

    def test_positive_preallocated_cap_and_asset_accounting(self):
        b = self.check(F(1, 1000000))
        self.assertLess(b.getter_error, F(1, 100000))
        self.assertEqual(F(3, 1000), b.total_error-b.getter_error)

    def test_zero_cap_and_large_actual_translation_refuse(self):
        with self.assertRaises(ValueError): self.check(cap=F(0))
        with self.assertRaises(ValueError): self.check(translation=F(1, 1000))

    def test_basis_error_uses_entire_asset_radius(self):
        with self.assertRaises(ValueError): self.check(matrix_error=F(1, 1000))


if __name__ == '__main__': unittest.main()
