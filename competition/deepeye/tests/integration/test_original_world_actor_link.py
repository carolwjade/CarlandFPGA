import unittest
import threading
import copy
from types import SimpleNamespace
from unittest.mock import patch
from competition.deepeye.simulation.authority import actor_composition as actor
from competition.deepeye.simulation.authority import _world_loop as world
from competition.deepeye.simulation.authority import original_world_actor_link as linkmod

class OriginalWorldActionControls(unittest.TestCase):
    def test_retained_receipt_survives_actor_postcheck_exception(self):
        composition = object.__new__(actor.ActorComposition)
        composition._thread = threading.get_ident()
        composition._foreign = threading.Event()
        composition._busy = False
        composition._retired = False
        composition._veto = 0
        composition._primary_error = None
        composition._input_transaction = None
        receipt = SimpleNamespace(pose_revision=8)
        composition._world_action_link = SimpleNamespace(slot=SimpleNamespace(committed=True, receipt=receipt))
        def step(self):
            raise RuntimeError('software fixture: post-CAS failure')
        with patch.object(actor.ActorComposition, '_retire', lambda self, reason: None):
            outcome = actor._entry(step)(composition)
        self.assertTrue(outcome.committed)
        self.assertEqual(outcome.pose_revision, 8)

    def test_receipt_survives_retirement_failure_after_commit(self):
        composition = object.__new__(actor.ActorComposition)
        composition._thread = threading.get_ident()
        composition._foreign = threading.Event()
        composition._busy = composition._retired = False
        composition._veto = 0
        composition._primary_error = None
        composition._errors = []
        composition._candidates = composition._progress = None
        composition._world_pending_stop = False
        composition._input_transaction = None
        composition._world_action_link = SimpleNamespace(slot=SimpleNamespace(
            committed=True, receipt=SimpleNamespace(pose_revision=8)))
        def step(self):
            raise RuntimeError('software post-CAS failure')
        with (patch.object(actor.ActorComposition, '_retire', side_effect=RuntimeError('retire failed')),
              patch.object(actor.ActorComposition, '_dispatch_stop'),
              patch.object(actor.ActorComposition, '_cleanup')):
            outcome = actor._entry(step)(composition)
        self.assertTrue(outcome.committed)
        self.assertEqual(outcome.pose_revision, 8)
        self.assertEqual(len(composition._errors), 1)

    def test_software_forwards_real_sequence_and_interval_once(self):
        self.assertTrue(hasattr(linkmod, '_SoftwareOwner'), 'distinct fixture seam missing')
        for seq in (7, 8):
            owner = linkmod._SoftwareOwner()
            backend = linkmod._SoftwareBackend(owner)
            link = linkmod._software_link_for_test(owner, backend)
            result = link.step(seq, 1_000_000)
            self.assertIs(type(result), linkmod._FixtureReceipt)
            self.assertEqual((result.command_seq, result.end_ns-result.start_ns), (seq, 1_000_000))
            self.assertEqual(backend.events, ['poll', 'commit-enter', 'final-fence', 'cas', 'commit-return'])
            self.assertIs(link.slot.receipt, result)

    def test_poll_precedes_numeric_slot_reservation(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner)
        link = linkmod._software_link_for_test(owner, backend)
        link.step(7, 1_000_000)
        self.assertIsNone(getattr(backend, 'poll_observed_slot', 'missing observation'))
        self.assertIsNotNone(link.slot)

    def test_software_retains_receipt_after_post_return_failure(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner)
        link = linkmod._software_link_for_test(owner, backend)
        with self.assertRaises(RuntimeError):
            link.step(7, 1_000_000, fail_after_return=True)
        self.assertIs(type(link.slot.receipt), linkmod._FixtureReceipt)
        self.assertTrue(link.slot.committed)
        self.assertEqual(link.slot.receipt.command_seq, 7)

    def test_software_pending_publication_is_one_shot_even_if_send_fails(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner, fail_send=True)
        link = linkmod._software_link_for_test(owner, backend)
        link.step(7, 1_000_000)
        with self.assertRaises(RuntimeError):
            link.publish_once()
        with self.assertRaises(ValueError):
            link.publish_once()
        with self.assertRaises(ValueError):
            link.step(8, 1_000_000)
        self.assertEqual(backend.events.count('send'), 1)
        self.assertFalse(link.getter_admitted)

    def test_successful_send_without_getter_admission_keeps_fixture_closed(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner)
        link = linkmod._software_link_for_test(owner, backend)
        link.step(7, 1_000_000)
        link.publish_once()
        self.assertFalse(link.getter_admitted)
        with self.assertRaises(ValueError):
            link.step(8, 1_000_000)
        self.assertEqual(backend.events.count('send'), 1)

    def test_stop_before_final_fence_prevents_software_commit(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner, stop_before_fence=True)
        link = linkmod._software_link_for_test(owner, backend)
        with self.assertRaises(ValueError):
            link.step(7, 1_000_000)
        self.assertNotIn('cas', backend.events)
        self.assertFalse(link.slot.committed)

    def test_fixture_fence_cannot_pass_production_type_gate(self):
        production = object.__new__(linkmod._OriginalWorldActorLink)
        token = object()
        command = SimpleNamespace(boot=token, sequence=7)
        slot = SimpleNamespace(dt_ns=1_000_000, deadline_ns=100_000_000)
        fixture = linkmod._FixtureFence(token, 7, 1_000_000, 2_000_000, 100_000_000)
        with self.assertRaises(ValueError):
            linkmod._check_final(production, command, slot, fixture)

    def test_software_link_rejected_by_production_factory_before_launch(self):
        owner = linkmod._SoftwareOwner()
        fixture = linkmod._software_link_for_test(owner, linkmod._SoftwareBackend(owner))
        config = actor.AuthorityConfig(object.__new__(actor.ActorPolicy), object(), object(), object(),
            object(), 1, 16, 1, 'a'*64)
        with (patch.object(actor, '_production_channels', return_value=object()),
              patch.object(actor, 'ActorRegistry', side_effect=AssertionError('launch attempted'))):
            with self.assertRaises(actor.CompositionRejected):
                actor._create_authority_for_original_world(config, fixture)

    def test_copied_or_reissued_software_link_is_not_a_capability(self):
        owner = linkmod._SoftwareOwner()
        backend = linkmod._SoftwareBackend(owner)
        original = linkmod._software_link_for_test(owner, backend)
        copied = copy.copy(original)
        with self.assertRaises(ValueError):
            copied.step(7, 1_000_000)
        with self.assertRaises(ValueError):
            linkmod._software_link_for_test(owner, backend)
        self.assertEqual(backend.events, [])

    def test_software_seam_refuses_real_root_type(self):
        owner = object.__new__(world._RootWorldOwner)
        with self.assertRaises(ValueError):
            linkmod._software_link_for_test(owner, object())

    def test_source_gate_allows_initial_and_refuses_unadmitted_actions(self):
        gate = getattr(world._RootWorldOwner, 'require_source_pose_current', None)
        self.assertTrue(callable(gate), 'fixed source pose gate missing')
        owner = object.__new__(world._RootWorldOwner)
        owner._thread = threading.get_ident()
        owner._foreign = threading.Event()
        owner._commits = []
        owner._actor_link = None
        self.assertIsNone(gate(owner))
        owner._actor_link = SimpleNamespace(slot=SimpleNamespace(committed=False))
        with self.assertRaises(world.WorldRejected):
            gate(owner)
        owner._actor_link = None
        owner._commits = [SimpleNamespace(committed=True, uncertainty=None)]
        owner._binding = SimpleNamespace(executor=SimpleNamespace(_root=SimpleNamespace(pose_revision=1)))
        owner._renderer_revision = 1
        owner._publication = SimpleNamespace(kind='PUBLISH_VIEW', resolved=True,
            state='APPLIED', revision=1, getter_admitted=False)
        with self.assertRaises(world.WorldRejected):
            gate(owner)
        owner._commits = [SimpleNamespace(committed=False, uncertainty='unknown')]
        owner._publication.getter_admitted = True  # software counterexample, never production admission
        with self.assertRaises(world.WorldRejected):
            gate(owner)

    def test_unretained_world_cannot_issue_a_binding(self):
        method = getattr(world._RootWorldOwner, 'actor_link', None)
        self.assertTrue(callable(method), 'original world actor-link entry is missing')
        unretained = object.__new__(world._RootWorldOwner)
        with self.assertRaises((ValueError, RuntimeError)):
            method(unretained, object())

    def test_missing_production_channels_refuse_before_acquisition(self):
        factory = getattr(actor, '_create_authority_for_original_world', None)
        self.assertTrue(callable(factory), 'private original-world production factory is missing')
        config = actor.AuthorityConfig(object.__new__(actor.ActorPolicy), object(), object(), object(),
            object(), 1, 16, 1, 'a' * 64)
        with (patch.object(actor, 'ActorRegistry', side_effect=AssertionError('registry acquisition')),
              patch.object(actor, 'OwnedMotionExecutor', side_effect=AssertionError('second executor'))):
            with self.assertRaises(actor.ActivationUnavailable):
                factory(config, object())

if __name__ == '__main__':
    unittest.main()
