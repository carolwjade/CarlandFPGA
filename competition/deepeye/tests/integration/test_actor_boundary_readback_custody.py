"""NEW C38 counterexamples, software boundaries only; no native grants."""
import copy
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
from competition.deepeye.simulation.authority import _world_loop as world
from competition.deepeye.simulation.authority import original_world_actor_link as links
from competition.deepeye.tests.integration import test_actor_source_custody as fixtures


class ActorBoundaryReadbackControls(unittest.TestCase):
    def specimen(self):
        case=fixtures.ActorSourceCustodyTests();self.addCleanup(case.doCleanups)
        f,link,custody,actor,boot=case.specimen()
        return f,link,custody,actor,boot

    def test_old_span_has_real_strict_separation_from_nonspatial_lower_bound(self):
        f,link,custody,actor,boot=self.specimen()
        original=type(f.clock).__call__
        def advancing(clock):
            value=original(clock)
            if clock is f.clock:clock.now+=1
            return value
        with patch.object(type(f.clock),'__call__',advancing):
            f.clock.now+=1000;t=custody.reserve(actor,'BOOT')
        self.assertLess(custody.closed_spans[-1]['through_qpc_ns'],t.lower)
        self.assertEqual(custody.closed_spans[-1],t.record['old_pose_span'])

    def test_tied_original_observations_refuse_before_transition(self):
        f,link,custody,actor,boot=self.specimen();before=link.executor._root
        with patch.object(type(f.clock),'__call__',lambda clock:clock.now):
            f.clock.now+=1000
            with self.assertRaises(ValueError):custody.reserve(actor,'BOOT')
        self.assertIs(before,link.executor._root)
        self.assertEqual([],custody.transitions);self.assertIsNone(custody.pending)

    def publication(self):
        owner=object.__new__(world._RootWorldOwner)
        owner._native=NS(run_id='software-readback-run')
        owner._number=1;owner._retired_epochs=set()
        identity={'freeze_id':'software-freeze','drill_root_instance_id':'1'}
        epoch=NS(identity=identity)
        view=NS(pose=NS(position_m=(0.,0.,0.),orientation_xyzw=(0.,0.,0.,1.),speed_m_s=0.),pose_revision=1)
        _,transform=world._desired(view)
        message=dict(body=dict(desired_transform=transform))
        pub=world._Publication('PUBLISH_VIEW','software-publication',epoch,1,message,b'payload','a'*64,1000)
        def make(transform):
            body=dict(freeze_identity=identity,publication_operation_id=pub.operation_id,
                payload_digest=pub.digest,drill_root_instance_id='1',state='APPLIED',
                pose_revision='1',local_transform=transform,global_transform=transform)
            return NS(payload_digest='b'*64,as_dict=lambda:dict(type='VIEW_READBACK',run_id=owner._native.run_id,
                                         world_epoch='1',body=body))
        old=make(transform)
        pub.readback=pub.admitted_readback=old
        pub.readback_ns=pub.admitted_readback_ns=100
        pub.admitted_readback_digest=old.payload_digest
        pub.state='APPLIED';pub.resolved=True;pub.getter_admitted=True
        owner._publication=pub;owner._renderer_revision=1
        owner._hello=NS(as_dict=lambda:dict(body=dict(scalar_width=64)))
        owner._time=lambda:200;owner._audit_identity=lambda body:epoch
        changed=copy.deepcopy(transform);changed['origin'][0]=world._f64(.01)
        return owner,pub,old,make(changed)

    def test_later_received_frame_cannot_replace_admitted_endpoint(self):
        owner,pub,old,replacement=self.publication()
        owner._inflight_frames=(replacement,)
        with self.assertRaises(ValueError):owner._accept_frame(replacement)
        self.assertIs(old,pub.readback);self.assertEqual(100,pub.readback_ns)

    def test_same_original_frame_is_idempotent_without_renewing_time(self):
        owner,pub,old,replacement=self.publication();owner._inflight_frames=(old,)
        owner._accept_frame(old)
        self.assertIs(old,pub.readback);self.assertEqual(100,pub.readback_ns)

    def test_source_gate_refuses_replaced_pointer_despite_old_flags(self):
        owner,pub,old,replacement=self.publication()
        slot=world._Commit(None,b'command',0,1000,committed=True)
        slot.publication=pub;slot.closed=True;slot.completion_observed_qpc_ns=150
        slot.getter_admitted=True;slot.admitted_readback=old;slot.admitted_readback_ns=100
        slot.admitted_readback_digest=old.payload_digest
        runtime=NS(_latched=False,_executed_until_ns=150)
        link=NS(slot=slot,composition=NS(_retired=False,_runtime=runtime))
        owner._actor_link=link;owner._actor_links={id(link):link};owner._commits=[slot]
        owner._binding=NS(executor=NS(_root=NS(pose_revision=1,executed_until_ns=150)))
        owner._check_thread=lambda:None
        pub.readback=replacement
        with self.assertRaises(ValueError):owner.require_source_pose_current()

    def test_two_nonspatial_gaps_preserve_prefix_and_supply_actual_current_read(self):
        case=fixtures.ActorSourceCustodyTests();self.addCleanup(case.doCleanups)
        f,link,custody,actor,boot=case.specimen()
        first=f.book.evidence()['samples'][0]
        case.activate(f,link,custody,actor,boot)
        current=f.book.current_pose_interval()
        self.assertEqual(2,current['valid_span']['root_revision'])
        self.assertEqual(list(link.executor._root.pose.position_m),current['pose']['position_m'])
        self.assertLessEqual(current['pose_read']['begin_qpc_ns'],current['pose_read']['end_qpc_ns'])
        self.assertEqual(first,f.book.evidence()['samples'][0])
        for t in custody.transitions:
            self.assertLess(t.record['old_pose_span']['through_qpc_ns'],t.lower)
            self.assertIsNone(t.record['exact_commit_qpc_ns'])

    def test_exact_admitted_binding_passes_but_changed_observation_time_refuses(self):
        owner,pub,old,replacement=self.publication()
        slot=world._Commit(None,b'command',0,1000,committed=True)
        slot.publication=pub;slot.getter_admitted=True
        slot.admitted_readback=old;slot.admitted_readback_ns=100
        slot.admitted_readback_digest=old.payload_digest
        links._require_admitted_readback(pub,slot)
        pub.readback_ns=101
        with self.assertRaises(ValueError):links._require_admitted_readback(pub,slot)


if __name__=='__main__':unittest.main()
