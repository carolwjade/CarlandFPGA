"""Software-only wire/sender checks; no native/Godot/display/board proof.

Sender fixtures are uninitialized original-type shells with explicitly mocked
registry/native transport boundaries. Wire tests exercise the real encoder,
HMAC, sequence and direction checks with an in-memory socket substitute.
"""
import base64
import hashlib
import hmac
import importlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from competition.deepeye.simulation.authority import _world_wire as wire

try:
    sender = importlib.import_module('competition.deepeye.tools.diagnostic.demo30h_ui_sender_a')
except ModuleNotFoundError:
    sender = None


def status():
    return dict(connection='connected', coordinator_ready=True,
        stages={key:'pending' for key in ('sensor','board_compression','upload_decode',
                                         'ai_decision','board_readback','motion')},
        data=dict(raw=0, encoded=0, decoded=0, codec_mode='demo', e0_match=None))


def message(raw=b'{}'):
    return dict(type='UI_STATUS', run_id='software-run', world_epoch='1', operation_id='ui-1',
                body=dict(freeze_id='software-freeze', status_base64=base64.b64encode(raw).decode('ascii')))


class SoftwareSocket:
    def __init__(self, incoming=b''):
        self.incoming = incoming
        self.written = bytearray()
    def send(self, raw):
        self.written.extend(raw)
        return len(raw)
    def recv(self, count):
        if not self.incoming:
            raise BlockingIOError
        raw, self.incoming = self.incoming[:count], self.incoming[count:]
        return raw


class UiStatusWireSoftwareTests(unittest.TestCase):
    def test_ui_status_is_bounded_root_control_message(self):
        self.assertEqual(wire.validate_message(message()), 'R')
        self.assertEqual(wire.decode_payload(wire.encode_payload(message())), message())
        wire.encode_payload(message(b'x'*8192))
        for raw in (b'', b'x'*8193):
            with self.subTest(size=len(raw)), self.assertRaises(wire.WireFault):
                wire.encode_payload(message(raw))
        bad = message()
        bad['body']['extra'] = 1
        with self.assertRaises(wire.WireFault):
            wire.encode_payload(bad)
        bad = message()
        bad['body']['status_base64'] = 'e30=\n'
        with self.assertRaises(wire.WireFault):
            wire.encode_payload(bad)

    def test_original_hmac_frame_and_transmission_completion_are_reused(self):
        sock, key = SoftwareSocket(), b's'*32
        channel = wire._WireChannel(sock, key, 'software-run')
        tx = channel.queue(message(), 100)
        header = wire._HEADER.pack(wire.MAGIC, b'R', 0, len(tx.payload))
        self.assertEqual(tx.frame, header + tx.payload + hmac.digest(key, header+tx.payload, 'sha256'))
        self.assertFalse(channel.complete_tx(tx))
        channel.pump(1)
        self.assertTrue(channel.complete_tx(tx))
        self.assertEqual(bytes(sock.written), tx.frame)
        self.assertEqual(channel.tx_sequence, 1)

    def test_original_inbound_hmac_direction_and_sequence_fail_closed(self):
        key = b's'*32
        payload = wire.encode_payload(dict(type='STOP_NOTICE',run_id='software-run',world_epoch='1',
            operation_id='stop-1',body=dict(freeze_id='software-freeze',source='human_escape',pose_revision='0')))
        for direction, sequence, damage in ((b'R',0,False),(b'G',1,False),(b'G',0,True)):
            header = wire._HEADER.pack(wire.MAGIC,direction,sequence,len(payload))
            mac = hmac.digest(key,header+payload,'sha256')
            if damage:
                mac = bytes([mac[0]^1])+mac[1:]
            channel = wire._WireChannel(SoftwareSocket(header+payload+mac), key, 'software-run')
            with self.subTest(direction=direction,sequence=sequence,damage=damage), self.assertRaises(wire.WireFault):
                channel.pump(1)
            self.assertIsNotNone(channel._failure)

    def test_ui_status_cannot_arrive_as_engine_authority_even_with_valid_mac(self):
        key=b's'*32
        payload=wire.encode_payload(message())
        header=wire._HEADER.pack(wire.MAGIC,b'G',0,len(payload))
        channel=wire._WireChannel(SoftwareSocket(header+payload+hmac.digest(key,header+payload,'sha256')),
                                  key,'software-run')
        with self.assertRaises(wire.WireFault):
            channel.pump(1)
        self.assertIsNotNone(channel._failure)


class UiStatusSenderSoftwareTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(sender, 'UI sender is not implemented')
        from competition.deepeye.integration.host_clock import qpc_clock_for_new_run
        clock = qpc_clock_for_new_run()
        self.world = sender.FunctionalWorld(clock, 'software-board-operation', Path.cwd())
        f = object.__new__(sender.FunctionalSource)
        owner = object.__new__(sender.loop._RootWorldOwner)
        native = object.__new__(sender.native_module._OwnedGodot)
        epoch = NS(number=1,identity=dict(freeze_id='software-freeze',world_epoch='1'))
        binding = NS(epoch=epoch)
        link = object.__new__(sender._OriginalWorldActorLink)
        link.owner, link.binding, link.native = owner, binding, native
        f.owner, f.binding, f.link, f.clock = owner,binding,link,clock
        f._thread, f._pending = threading.get_ident(), None
        f.source = NS(_polling=False)
        self.world.source,self.world.owner,self.world.binding = f,owner,binding
        owner._thread,owner._clock = threading.get_ident(),clock
        owner._foreign,owner._busy,owner._vetoed = threading.Event(),False,False
        owner._native,owner._binding,owner._epoch = native,binding,epoch
        owner._state,owner._serial = 'BOUND_STOPPED',0
        owner._publication = NS(resolved=True,state='APPLIED')
        owner._freeze_request = owner._assembly = owner._retirement = owner._em_scope_active = None
        owner._inflight_frames = ()
        native._thread,native.clock_binding = threading.get_ident(),clock
        native._foreign,native._retired,native._busy = False,False,False
        native.state,native.spec,native.hello = 'AUTHENTICATED',NS(run_id='software-run'),object()
        native._containment_deadline = clock()+10_000_000_000
        native._channel = NS(_failure=None,_transactions=[],_pending=None)
        self.owner,self.native,self.calls = owner,native,[]
        self.tx = wire.Transmission(b'',hashlib.sha256(b'').hexdigest(),b'',0,1)
        def send(message, *, deadline_ns):
            self.calls.append(('send',message))
            self.tx.deadline_ns=deadline_ns
            native._channel._transactions.append(self.tx)
            native._channel._pending=self.tx
            return self.tx
        def poll(owner_arg):
            self.calls.append(('owner.poll',None))
            self.tx.started=self.tx.complete=True
            native._channel._pending=None
        patches = [patch.object(sender.native_module,'is_original_owner',return_value=True),
            patch.object(sender._OriginalWorldActorLink,'_registered'),
            patch.object(sender.loop._RootWorldOwner,'_known_binding',return_value=binding),
            patch.object(sender.loop._RootWorldOwner,'_known_epoch',return_value=epoch),
            patch.object(sender.loop._RootWorldOwner,'poll',autospec=True,side_effect=poll),
            patch.object(sender.native_module._OwnedGodot,'healthy_frame_aligned',return_value=True),
            patch.object(sender.native_module._OwnedGodot,'send',side_effect=send),
            patch.object(sender.native_module._OwnedGodot,'complete_tx',side_effect=lambda tx: tx.complete and not tx.failed),
            patch.object(sender.native_module._OwnedGodot,'poll',side_effect=AssertionError('helper swallowed native frames'))]
        for p in patches:
            p.start();self.addCleanup(p.stop)

    def deadline(self):
        return self.world.clock()+500_000_000

    def test_queue_forces_ready_false_and_advance_uses_owner_poll_only(self):
        supplied = status()
        result = sender.queue_demo30h_status(self.world,supplied,deadline_ns=self.deadline())
        self.assertEqual(result.status,'transport_pending')
        self.assertTrue(supplied['coordinator_ready'])
        sent = self.calls[0][1]
        self.assertEqual(sent['operation_id'],'software-run:UI_STATUS:1')
        self.assertEqual(sent['body']['freeze_id'],'software-freeze')
        decoded = json.loads(base64.b64decode(sent['body']['status_base64']))
        self.assertIs(decoded['coordinator_ready'],False)
        self.assertFalse(result.snapshot()['ui_displayed'])
        sender.advance_demo30h_status(result)
        self.assertEqual(result.status,'transport_written')
        self.assertEqual([x[0] for x in self.calls],['send','owner.poll'])
        self.assertFalse(result.snapshot()['ui_displayed'])
        sender.advance_demo30h_status(result)
        self.assertEqual(len(self.calls),2)

    def test_busy_or_unaligned_defers_without_operation_or_native_poll(self):
        for field in ('_busy','_em_scope_active','_inflight_frames'):
            original=getattr(self.owner,field)
            setattr(self.owner,field,True)
            result=sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
            self.assertEqual(result.status,'deferred')
            setattr(self.owner,field,original)
        self.owner._publication.resolved=False
        self.assertEqual(sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline()).status,'deferred')
        self.owner._publication.resolved=True
        with patch.object(sender.native_module._OwnedGodot,'healthy_frame_aligned',return_value=False):
            self.assertEqual(sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline()).status,'deferred')
        self.assertEqual(self.owner._serial,0)
        self.assertEqual(self.calls,[])

    def test_invalid_status_closed_owner_or_long_deadline_reject_before_send(self):
        for changes in ({'coordinator_ready':1},{'extra':1},{'data':{'truth':1}},
                        {'data':{'raw':float('nan')}},{'data':{'raw':'x'*161}}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                sender.queue_demo30h_status(self.world,dict(status(),**changes),deadline_ns=self.deadline())
        self.world._close_attempted=True
        with self.assertRaises(ValueError):
            sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        self.world._close_attempted=False
        with self.assertRaises(ValueError):
            sender.queue_demo30h_status(self.world,status(),deadline_ns=self.world.clock()+3_000_000_000)
        self.assertEqual(self.owner._serial,0)
        self.assertEqual(self.calls,[])

    def test_reserved_control_budget_defers_without_consuming_operation(self):
        self.native._channel._transactions=[None]*4080
        result=sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        self.assertEqual(result.status,'deferred')
        self.assertEqual(result.reason,'control_transport_budget_reserved')
        self.assertEqual(self.owner._serial,0)
        self.assertEqual(self.calls,[])

    def test_failed_original_channel_is_rejected_not_treated_as_deferred(self):
        self.native._channel._failure='software previous unknown frame'
        with self.assertRaises(ValueError):
            sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        self.assertEqual(self.owner._serial,0)
        self.assertEqual(self.calls,[])

    def test_send_exception_retains_original_pending_frame_and_never_requeues(self):
        def fail_after_queue(*args,**kwargs):
            self.tx.started=True
            self.native._channel._pending=self.tx
            raise OSError('software unknown send boundary')
        with patch.object(sender.native_module._OwnedGodot,'send',side_effect=fail_after_queue):
            with self.assertRaises(sender.UiStatusTransportError) as caught:
                sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        result=caught.exception.attempt
        self.assertIs(result.transmission,self.tx)
        self.assertEqual(result.status,'transport_unknown')
        self.assertFalse(result.snapshot()['ui_displayed'])
        with self.assertRaises(ValueError):
            sender.advance_demo30h_status(result)
        self.assertEqual(self.owner._serial,1)

    def test_advance_is_one_nonblocking_owner_poll_and_can_remain_pending(self):
        result=sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        with patch.object(sender.loop._RootWorldOwner,'poll') as owner_poll:
            sender.advance_demo30h_status(result)
            owner_poll.assert_called_once_with()
        self.assertEqual(result.status,'transport_pending')
        self.assertFalse(self.tx.complete)

    def test_failure_retains_original_tx_without_retry_or_false_written(self):
        result=sender.queue_demo30h_status(self.world,status(),deadline_ns=self.deadline())
        self.tx.started=True
        with patch.object(sender.loop._RootWorldOwner,'poll',side_effect=OSError('software transport failure')):
            with self.assertRaises(sender.UiStatusTransportError) as caught:
                sender.advance_demo30h_status(result)
        self.assertIs(caught.exception.attempt,result)
        self.assertIs(result.transmission,self.tx)
        self.assertEqual(result.status,'transport_unknown')
        with self.assertRaises(ValueError):
            sender.advance_demo30h_status(result)
        self.assertEqual([x[0] for x in self.calls],['send'])

    def test_bridge_handler_is_display_only_static_inspection(self):
        bridge=(Path(__file__).resolve().parents[2]/'simulator/runtime/world_motion_bridge.gd').read_text(encoding='utf8')
        self.assertIn('"UI_STATUS": ["freeze_id","status_base64"]',bridge)
        body=bridge.split('func _ui_status(',1)[1].split('\nfunc ',1)[0]
        self.assertIn('status["coordinator_ready"] = false',body)
        self.assertIn('_main.present_demo30h_status(status)',body)
        for forbidden in ('_queue(', '_publish(', '_query(', '_stop(', '_unlock(', 'desired_pose', 'authority'):
            self.assertNotIn(forbidden,body)


if __name__=='__main__':
    unittest.main()
