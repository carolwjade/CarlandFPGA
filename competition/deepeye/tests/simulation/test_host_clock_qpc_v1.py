"""New same-domain routing controls; native/upstream and fixed leaf are seams.

No old TestCase is inherited or run. All clock injection is a module-private
fixed-leaf seam; production accepts only the exact QPC binding.
"""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from . import test_actor_owner as owners
from . import test_candidate_owner as fixture
from ...integration import host_clock as clocks, candidate_mailbox as mailbox

c, rt = fixture.c, fixture.rt
S, E = 210_000_000, 220_000_000


class QpcChannels(fixture.StatefulChannels):
    def __init__(self,fixture,binding):
        super().__init__(fixture); self.binding=binding

    def mailbox_activation_for_boot(self,boot):
        return fixture.co._MailboxActivation(boot,self,self.binding,0,0,0)


class QpcCompositionTests(owners.OwnerFixture):
    def setUp(self):
        super().setUp()
        self.clock.value=S
        self.leaf_patch=patch.object(clocks,'_qpc_leaf',side_effect=self.clock)
        self.leaf_patch.start(); self.addCleanup(self.leaf_patch.stop)
        self.binding=clocks.qpc_clock_for_new_run()
        self.f=rt.PcDirectRuntimeTests(); self.f.setUp(); self.f.clock=self.clock
        geom=fixture.ac.mt.MotionExecutorTests(); geom.setUp()
        initial=fixture.ac.mt.p.initialize(geom.ctx,
            fixture.ac.mt.RigidState((0,0,15.6),(0,1,0,0),.25),
            fixture.ac.mt.gc.ErrorBounds(0.,0.,0.),pose_revision=0,monotonic_ns=0,
            error_budget_reference='new QPC fixture; raw epoch/native/upstream synthetic').state
        self.config=c.AuthorityConfig(self.policy,initial,geom.scene,geom.model,geom.budget,
            500_000_000,16,100_000_000,'a'*64,mailbox.PcDirectWindowV2(10_000_000))
        self.comp=None; self.addCleanup(self.close_fixture)

    close_fixture=fixture.CandidateOwnerTests.close_fixture
    proof=fixture.CandidateOwnerTests.proof
    offer=fixture.CandidateOwnerTests.offer
    record=fixture.CandidateOwnerTests.record
    slot=fixture.CandidateOwnerTests.slot
    command=fixture.CandidateOwnerTests.command
    step=fixture.CandidateOwnerTests.step
    assert_no_pose=fixture.CandidateOwnerTests.assert_no_pose

    def activate(self):
        self.channels=QpcChannels(self.f,self.binding)
        with patch.object(c,'_production_channels',return_value=self.channels):
            self.comp=c.create_authority(self.config,host_clock=self.binding)
        self.comp.accept_boot(self.channels.ready)
        self.f.binding=self.comp._boot
        self.f.owner=SimpleNamespace(
            board=lambda r:self.comp.accept_board(self.channels.event(r)),
            observe=lambda r:self.comp.accept_observation(self.channels.event(r)))
        self.f.beat()

    def pending(self):
        self.activate(); self.f.observe(); proof=self.proof(); self.offer(proof)
        return proof

    def arm(self):
        proof=self.pending(); self.clock.value=S+1; self.command(proof)

    def test_same_exact_binding_reaches_registry_handle_progress_candidates_and_runtime(self):
        self.arm()
        self.assertIs(self.comp._clock,self.binding)
        self.assertIs(self.comp._registry._clock,self.binding)
        self.assertIs(self.comp._runtime._clock,self.binding)
        self.assertIs(self.comp._progress.clock_domain,self.binding)
        self.assertIs(self.comp._candidates._clock,self.binding)
        self.assertTrue(self.step().committed)
        self.assertEqual(self.comp._executor.renderer_view().pose_revision,1)
        self.assertTrue(any(row[0]=='wait' for row in self.api.calls))

    def test_second_binding_original_completion_domain_refuses(self):
        self.activate(); self.f.observe()
        with self.assertRaises(c.CompositionRejected):
            self.offer(self.proof(clock_domain=clocks.qpc_clock_for_new_run()))
        self.assert_no_pose()

    def test_slot_callback_refresh_to_E_is_not_replaced_with_nominal_time(self):
        proof=self.pending(); original=self.channels.verify_slot
        def slow(event,boot):
            result=original(event,boot); self.clock.value=E; return result
        with patch.object(self.channels,'verify_slot',slow):
            with self.assertRaises(c.CompositionRejected): self.command(proof)
        self.assert_no_pose()

    def test_original_progress_expiry_at_final_fence_rejects_real_cas(self):
        self.config=replace(self.config,progress_max_age_ns=5_000_000)
        self.arm(); original=self.comp._executor.commit_step
        def final(prepared,callback):
            self.clock.value=215_000_000
            return original(prepared,callback)
        with patch.object(self.comp._executor,'commit_step',final):
            self.assertFalse(self.step().committed)
        self.assert_no_pose()

    def test_original_handle_probe_at_exact_budget_refuses(self):
        self.arm()
        self.api.wait_hook=lambda:setattr(self.clock,'value',self.clock.value+1_000_000)
        self.assertFalse(self.step().committed); self.assert_no_pose()

    def test_factory_cannot_use_callable_or_open_production_with_qpc(self):
        with patch.object(c,'ActorRegistry') as registry:
            with self.assertRaises(ValueError): c.create_authority(self.config,host_clock=lambda:0)
            with self.assertRaises(c.ActivationUnavailable):
                c.create_authority(self.config,host_clock=self.binding)
            registry.assert_not_called()
        with patch.object(owners.a,'_native_api',side_effect=AssertionError('no acquisition')):
            with self.assertRaises(ValueError): owners.a.ActorRegistry(host_clock=lambda:0)

    def test_legacy_none_keeps_both_existing_monotonic_defaults(self):
        self.channels=fixture.StatefulChannels(self.f)
        with patch.object(c,'monotonic_ns',self.clock),\
             patch.object(c,'_production_channels',return_value=self.channels):
            self.comp=c.create_authority(self.config)
        self.assertIs(self.comp._clock,self.clock)
        self.assertIs(self.comp._registry._clock,self.clock)
        self.assertIs(self.comp._runtime._clock,self.clock)
