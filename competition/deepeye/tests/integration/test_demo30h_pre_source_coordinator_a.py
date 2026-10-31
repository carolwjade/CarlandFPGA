"""Software-only coordinator checks; no native/SSH/source/board proof.

Original lifecycle objects below are uninitialized shells. Only the original
read-only registry checks and preparation constructors are replaced in tests.
There is no fake BOOT, motion provider, or production authority invocation.
"""
import hashlib
import importlib
import json
from pathlib import Path
import pickle
import tempfile
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

try:
    coordinator = importlib.import_module(
        'competition.deepeye.tools.diagnostic.demo30h_pre_source_coordinator_a')
except ModuleNotFoundError:
    coordinator = None


class PreSourceCoordinatorSoftwareTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(coordinator, 'pre-source coordinator is not implemented')
        from competition.deepeye.tools.run_causal_functional_chain import FunctionalWorld, FunctionalSource
        from competition.deepeye.simulation.authority.actor_composition import AuthorityConfig
        from competition.deepeye.simulation.isolation.actor_owner import ActorPolicy
        from competition.deepeye.integration.host_clock import qpc_clock_for_new_run
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        clock = qpc_clock_for_new_run()
        world = FunctionalWorld(clock, 'software-only-operation', Path(self.tmp.name))
        source = object.__new__(FunctionalSource)
        owner, binding = NS(), NS()
        values = NS(initial_state=object(), scene=object(), model=object(), budget=object())
        binding.world_values = values
        causal = NS(state='NEW', _origin=None, _clock=None, _count=0,
                    _last_tick=None, _polling=False)
        book = object.__new__(coordinator.RootSourceBook)
        book._source, book._clock, book._origin = causal, clock, None
        book._state, book._samples, book._active = 'NEW', [], None
        causal._source_book = book
        link = object.__new__(coordinator._OriginalWorldActorLink)
        link.owner, link.binding, link.source, link.book = owner, binding, causal, book
        link.executor, link.native = NS(_max_slices=2), NS(run_id='software-run')
        link.claimed, link.composition = False, None
        projection = object.__new__(coordinator.ProjectionSession)
        projection._owner, projection._link, projection._book = owner, link, book
        source.clock, source._thread = clock, threading.get_ident()
        source.owner, source.binding, source.source, source.book = owner, binding, causal, book
        source.link, source.session = link, projection
        source.composition = source._pending = None
        source._start_attempted = source._activation_attempted = False
        source._retained_samples = []
        world.owner, world.binding, world.source = owner, binding, source
        policy = ActorPolicy('software-run', Path(self.tmp.name), Path(self.tmp.name),
            (('actor.exe', 'a'*64),), 'actor.exe', (), 'C:/Windows', self.tmp.name,
            1024, 100, 100, 1000, 500, 10)
        config = AuthorityConfig(policy, values.initial_state, values.scene, values.model,
                                 values.budget, 100, 2, 100, 'b'*64)
        legacy = dict(session=1, config_epoch=0, boot_sha256='c'*64,
                      transport_profile_id=1, source_id=1, topology_id=1, acquisition_profile_id=1)
        context = dict(operation_id=world.operation_id, request_hash='d'*64,
                       tested_commit='e'*40, build_manifest_sha256='f'*64,
                       boot_id='software-boot-label', session_id='software-session-label',
                       tag=1, clock_domain_id=clock.metadata['domain_id'])
        binding_doc = dict(operation_id=world.operation_id, request_sha256=context['request_hash'],
                           boot_id=context['boot_id'], source_commit=context['tested_commit'], build_id='software-build')
        policy_doc = dict(binding=binding_doc, limits=dict(begin=1, commit=1, stop=1,
                           latch=1, release=1, total_io=300))
        policy_doc['policy_sha256'] = hashlib.sha256(coordinator.g05._canonical(policy_doc)).hexdigest()
        self.args = dict(world=world, authority_config=config, legacy_context=legacy,
            c42_context=context, g05_policy_raw=coordinator.g05._canonical(policy_doc),
            ident='init-software', identity_words=(1,)*13, max_commands=1, max_polls=16,
            duration_ns=2_000_000_000, max_io=300, timeout_ns=1_000_000_000,
            max_source_age_ns=1_000_000_000, select_owner_work_v1=True)
        for cls, method in ((coordinator._OriginalWorldActorLink, '_registered'),
                            (coordinator.RootSourceBook, '_check'),
                            (coordinator.ProjectionSession, '_check')):
            p = patch.object(cls, method)
            p.start()
            self.addCleanup(p.stop)

    def plan(self, **changes):
        return coordinator.validate_pre_source_plan(**dict(self.args, **changes))

    def test_valid_plan_keeps_original_references_and_cannot_serialize(self):
        plan = self.plan()
        self.assertIs(plan.world, self.args['world'])
        self.assertIs(plan.legacy_context, self.args['legacy_context'])
        with self.assertRaises(TypeError):
            pickle.dumps(plan)

    def test_all_cheap_bad_parameters_reject_before_init(self):
        invalid = dict(ident='bad id', identity_words=(True,)*13, max_commands=True,
                       max_polls=3, duration_ns=10_000_000_001, max_io=100,
                       timeout_ns=False, max_source_age_ns=100_000_000,
                       select_owner_work_v1=1, g05_policy_raw=b'{}')
        with patch.object(coordinator, 'OriginalChainReceiptProducer') as producer:
            for key, value in invalid.items():
                with self.subTest(parameter=key), self.assertRaises(ValueError):
                    self.plan(**{key: value})
            with self.assertRaises(ValueError):
                self.plan(max_source_age_ns=3_000_000_000)
            producer.assert_not_called()

    def test_config_copy_context_extra_and_foreign_domain_reject(self):
        from dataclasses import replace
        with self.assertRaises(ValueError):
            self.plan(authority_config=replace(self.args['authority_config'], scene=object()))
        for changes in ({'extra': 1}, {'operation_id': 'other'}, {'clock_domain_id': '0'*32}, {'tag': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.plan(c42_context=dict(self.args['c42_context'], **changes))
        self.args['world'].source.source._count = 1
        with self.assertRaises(ValueError):
            self.plan()

    def software_prepare(self, *, init_error=False):
        """Replace constructors only to exercise ordering/failure, never authority."""
        calls = []
        plan = self.plan()
        chain = object.__new__(coordinator.ChainSessionV2)
        from competition.deepeye.tools.diagnostic.functional50_chain_v2_board_a import Sequence
        chain.s = NS(_unknown=False, _closed=False, _source_pump=None,
                     _proc=object(), _dir=Path(plan.world.operation_id), _clock=plan.world.clock)
        chain.clock, chain.thread = plan.world.clock, threading.get_ident()
        chain.sequence, chain.bundle, chain.duration = Sequence(), object(), None
        phase = NS(owner=chain, kind='init', phase_index=1, status='COMPLETE', unknown=False,
                   request_raw=b'original-software-request', response_raw=b'original-software-response',
                   lower_qpc_ns=1, upper_qpc_ns=2)
        event = object()
        phases = []
        policy_doc = json.loads(plan.g05_policy_raw)
        ready = dict(policy_file_sha256=hashlib.sha256(plan.g05_policy_raw).hexdigest(),
            load_request_hash=policy_doc['binding']['request_sha256'],
            source_commit=policy_doc['binding']['source_commit'], build_id=policy_doc['binding']['build_id'])
        origin = (NS(operation_id=plan.world.operation_id), chain.s._proc, chain.clock,
                  b'software-only-ready', ready, 0, 1, object(), object(), object())
        class SoftwareProducer:
            def __init__(self, world, chain_arg, scanner=None):
                calls.append('producer'); self._history=[]; self._failed=False
                self._chain=chain_arg; self._scanner=None
            def init(self, *args, **kwargs):
                calls.append('init'); chain.sequence.initialized=True
                chain.sequence.ids.add(plan.ident); chain.duration=plan.duration_ns
                if init_error:
                    chain.s._unknown=True; self._failed=True
                    raise OSError('software injected init failure')
                phases.append(phase); self._history.append((event, {}, {'phase_receipt': phase}))
                return event
            def bind_scanner(self, scanner):
                calls.append('bind_scanner'); self._scanner=scanner
            def bind_pump(self, pump):
                calls.append('bind_pump'); chain.s._source_pump=pump
        def scanner(*args, **kwargs):
            calls.append('scanner')
            self.assertTrue(kwargs['defer_start'])
            return NS(_activated=False, _activation_attempted=False, _defer_start=True)
        def pump(*args):
            calls.append('pump'); return NS(enabled=False, failed=False)
        patches = [patch.object(coordinator.ChainSessionV2, '_phase_binding', return_value=origin),
            patch.object(coordinator.ChainSessionV2, 'phase_receipts', new=property(lambda _: tuple(phases))),
            patch.object(coordinator.ChainSessionV2, 'owner_work_v1', new=property(lambda _: False)),
            patch.object(coordinator.ChainSessionV2, 'select_owner_work_v1', side_effect=lambda: calls.append('select_owner')),
            patch.object(coordinator.ssh, '_original_session_origin', return_value=origin),
            patch.object(coordinator.ssh.Session, '_check'),
            patch.object(coordinator, '_check_bundle'),
            patch.object(coordinator, 'OriginalChainReceiptProducer', SoftwareProducer),
            patch.object(coordinator, 'OriginalPhaseReceipt', NS),
            patch.object(coordinator, 'select_demo_age_budget', side_effect=lambda *a, **k: calls.append('age') or object()),
            patch.object(coordinator, 'OriginalG05OperationBinding', side_effect=lambda *a, **k: calls.append('binding') or object()),
            patch.object(coordinator, 'OriginalSourceTraceScan', side_effect=scanner),
            patch.object(coordinator, 'OriginalChainSourcePump', side_effect=pump)]
        # Session is a synthetic shell. The production exact-type check remains
        # exercised by the real constructor, outside these sequencing tests.
        chain.s = object.__new__(coordinator.ssh.Session)
        for k,v in dict(_unknown=False,_closed=False,_source_pump=None,_proc=origin[1],
                        _dir=Path(plan.world.operation_id),_clock=chain.clock,_thread=chain.thread).items():
            setattr(chain.s,k,v)
        for p in patches:
            p.start(); self.addCleanup(p.stop)
        return plan, chain, calls, event

    def test_prepare_exact_order_keeps_source_new_and_pump_disabled(self):
        plan, chain, calls, event = self.software_prepare()
        result = coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertEqual(calls, ['select_owner','producer','init','age','binding','scanner','bind_scanner','pump','bind_pump'])
        self.assertIs(result.init_event, event)
        self.assertEqual(plan.world.source.source.state, 'NEW')
        self.assertFalse(result.pump.enabled)
        snapshot = result.snapshot()
        self.assertFalse(snapshot['resumable'])
        self.assertEqual(snapshot['authority'], 'not_evaluated')
        json.dumps(snapshot)
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        with self.assertRaises(ValueError):
            coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertEqual(calls.count('init'), 1)

    def test_init_exception_retains_original_state_and_never_retries(self):
        plan, chain, calls, _ = self.software_prepare(init_error=True)
        with self.assertRaises(coordinator.PreSourcePreparationError) as caught:
            coordinator.prepare_pre_source_cycle(plan, chain)
        result = caught.exception.cycle
        self.assertIs(result.chain, chain)
        self.assertIsInstance(caught.exception.cause, OSError)
        self.assertTrue(chain.s._unknown)
        self.assertTrue(result.producer._failed)
        self.assertEqual(result.stage, 'init')
        with self.assertRaises(ValueError):
            coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertEqual(calls.count('init'), 1)

    def test_mutated_context_rejects_before_init(self):
        plan, chain, calls, _ = self.software_prepare()
        plan.legacy_context['session'] = 7
        with self.assertRaises(ValueError):
            coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertNotIn('init', calls)

    def test_wrong_actual_ready_policy_rejects_before_any_preparation_effect(self):
        plan, chain, calls, _ = self.software_prepare()
        chain._phase_binding()[4]['policy_file_sha256'] = '0'*64
        with self.assertRaises(coordinator.PreSourcePreparationError) as caught:
            coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertIn('ready/policy/build', str(caught.exception.cause))
        self.assertEqual(calls, [])

    def test_exhausted_age_selection_cap_rejects_before_init(self):
        plan, chain, calls, _ = self.software_prepare()
        with patch.object(coordinator.age_module, '_SELECTED', {i: object() for i in range(16)}):
            with self.assertRaises(coordinator.PreSourcePreparationError) as caught:
                coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertIn('selection cap', str(caught.exception.cause))
        self.assertEqual(calls, [])

    def test_default_preparation_retains_default_age_and_no_owner_work_selection(self):
        self.args.update(max_source_age_ns=None, select_owner_work_v1=False)
        plan, chain, calls, _ = self.software_prepare()
        result = coordinator.prepare_pre_source_cycle(plan, chain)
        self.assertIsNone(result.demo_age_budget)
        self.assertNotIn('age', calls)
        self.assertNotIn('select_owner', calls)


if __name__ == '__main__':
    unittest.main()
