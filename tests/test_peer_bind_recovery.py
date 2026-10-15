"""Unavailable interface must not remove the sole node's local control plane."""
import asyncio
import errno
import os
import socket
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fpga_mesh.child_control import LocalControlClient
from fpga_mesh.http_transport import HttpPeerServer
from fpga_mesh.runtime import NodeConfig, NodeRuntime


class PeerBindRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        config = self.root / 'node-a.toml'
        config.write_text('node_id="A"\nproject_id="fpga-main"\nstate_dir="state"\n'
                          'mode="test_double"\nhardware_enabled=false\n', encoding='utf-8')
        self.config = replace(NodeConfig.load(config), peer_bind_port=0,
                              peer_retry_seconds=0.01)
        self.environment = patch.dict(os.environ, {'FPGA_MESH_SHARED_SECRET': 'local-test-only'})
        self.environment.start()

    async def asyncTearDown(self):
        self.environment.stop()
        self.tmp.cleanup()

    async def test_numeric_address_failure_keeps_original_errno(self):
        runtime = NodeRuntime(self.config)
        server = HttpPeerServer(runtime.peer, shared_secret='local-test-only',
                                host='192.0.2.231', port=0)
        try:
            with self.assertRaises(OSError) as caught:
                await server.start()
            self.assertIn(caught.exception.errno, (errno.EADDRNOTAVAIL, 10049))
        finally:
            await server.close()
            await runtime.stop()

    async def test_absent_address_keeps_local_control_then_recovers_once(self):
        runtime = NodeRuntime(self.config)
        real_start = runtime.peer_server.start
        attempts = 0
        restore = asyncio.Event()

        async def initially_absent():
            nonlocal attempts
            attempts += 1
            if not restore.is_set():
                raise OSError(errno.EADDRNOTAVAIL, 'configured interface absent')
            await real_start()

        try:
            with patch.object(runtime.peer_server, 'start', side_effect=initially_absent):
                await runtime.start()
                snapshot = runtime.snapshot()
                self.assertTrue(snapshot['started'])
                self.assertEqual(snapshot['peer_bind_state'], 'waiting')
                self.assertIsNone(snapshot['peer_listen_port'])
                self.assertIsNotNone(snapshot['peer_bind_error'])
                client = LocalControlClient(host='127.0.0.1', port=runtime.child_control.port,
                                            token=runtime.child_control.token)
                response = await client.call('status', {})
                self.assertIsInstance(response, dict)
                self.assertTrue((self.config.state_dir/'main-control.json').exists())
                restore.set()
                async def recovered():
                    while runtime.snapshot()['peer_bind_state'] != 'listening':
                        await asyncio.sleep(0.005)
                await asyncio.wait_for(recovered(), 2)
                successful_attempt = attempts
                await asyncio.sleep(0.03)
                self.assertEqual(attempts, successful_attempt)
                self.assertIsNone(runtime.snapshot()['peer_bind_error'])
                self.assertEqual(runtime.snapshot()['idle_model_calls'], 0)
                self.assertEqual(runtime.peer_server._server.sockets[0].getsockname()[0],
                                 self.config.peer_bind_host)
        finally:
            await runtime.stop()
        self.assertFalse((self.config.state_dir/'main-control.json').exists())

    async def test_waiting_shutdown_removes_discovery_and_stops_retry(self):
        runtime = NodeRuntime(self.config)
        with patch.object(runtime.peer_server, 'start', side_effect=OSError(10049, 'absent')) as start:
            await runtime.start()
            await runtime.stop()
            count = start.call_count
            await asyncio.sleep(0.03)
            self.assertEqual(start.call_count, count)
            self.assertIsNone(runtime._peer_retry_task)
            self.assertFalse((self.config.state_dir/'child-control.json').exists())
            await runtime.stop()

    async def test_permanent_retry_failure_is_visible_and_not_retried(self):
        runtime = NodeRuntime(self.config)
        with patch.object(runtime.peer_server, 'start', side_effect=[
                OSError(10049, 'absent'), OSError(10048, 'occupied')]) as start:
            try:
                await runtime.start()
                async def failed():
                    while runtime.snapshot()['peer_bind_state'] != 'failed':
                        await asyncio.sleep(0.005)
                await asyncio.wait_for(failed(), 2)
                await asyncio.sleep(0.03)
                self.assertEqual(start.call_count, 2)
                self.assertIsNone(runtime.snapshot()['peer_listen_port'])
                self.assertIn('10048', runtime.snapshot()['peer_bind_error'])
            finally:
                await runtime.stop()

    async def test_permission_error_fails_start_and_cleans_local_endpoints(self):
        runtime = NodeRuntime(self.config)
        with patch.object(runtime.peer_server, 'start', side_effect=OSError(10013, 'denied')):
            with self.assertRaises(OSError):
                await runtime.start()
        self.assertFalse((self.config.state_dir/'main-control.json').exists())

    async def test_cancelled_socket_handoff_closes_owned_socket(self):
        runtime = NodeRuntime(self.config)
        server = runtime.peer_server
        captured = []
        async def cancelled(*args, **kwargs):
            captured.append(kwargs['sock'])
            raise asyncio.CancelledError()
        try:
            with patch('fpga_mesh.http_transport.asyncio.start_server', side_effect=cancelled):
                with self.assertRaises(asyncio.CancelledError):
                    await server.start()
            self.assertEqual(captured[0].fileno(), -1)
        finally:
            await runtime.stop()

    async def test_cancellation_after_accept_registration_closes_server(self):
        runtime = NodeRuntime(self.config)
        real_start = asyncio.start_server
        captured = []
        async def cancel_after_start(*args, **kwargs):
            server = await real_start(*args, **kwargs)
            captured.append(server)
            real_serve = server.start_serving
            async def interrupted():
                await real_serve()
                raise asyncio.CancelledError()
            server.start_serving = interrupted
            return server
        try:
            with patch('fpga_mesh.http_transport.asyncio.start_server', side_effect=cancel_after_start):
                with self.assertRaises(asyncio.CancelledError):
                    await runtime.peer_server.start()
            self.assertFalse(captured[0].is_serving())
            self.assertFalse(captured[0].sockets)
            self.assertIsNone(runtime.peer_server._server)
        finally:
            await runtime.stop()


if __name__ == '__main__':
    unittest.main()
