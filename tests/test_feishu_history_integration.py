import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fpga_mesh.feishu_channel import FeishuNodeService
from fpga_mesh.feishu_history import FeishuHistoryAPI, HistoryAPIError
from tests.test_feishu_history import API, message, page
from tests.test_feishu_channel import FakeChannel, FakeMessage, RecordingController


def response(data=None, code=0):
    return SimpleNamespace(success=lambda: code == 0, code=code,
        raw=SimpleNamespace(content=json.dumps({'code':code, 'data':data}).encode()))


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_original_sdk_app_identity_is_checked_before_queries(self):
        client = SimpleNamespace(config=SimpleNamespace(app_id='cli_other'))
        with self.assertRaisesRegex(ValueError, 'identity'):
            FeishuHistoryAPI(client, expected_app_id='cli_a')
    async def test_real_generated_requests_follow_tokens_and_thread_has_no_time_parameters(self):
        calls = []
        async def alist(req):
            calls.append(req)
            return response(page([message()]))
        async def aget(req):
            calls.append(req)
            return response({'items':[message(req.message_id)]})
        api = FeishuHistoryAPI(SimpleNamespace(im=SimpleNamespace(v1=SimpleNamespace(
            message=SimpleNamespace(alist=alist, aget=aget)))))
        await api.list_messages(container_type='chat', container_id='oc_team', lower_ms=1234,
            upper_ms=4567, page_token='cursor')
        await api.list_messages(container_type='thread', container_id='omt_old', lower_ms=1234,
            upper_ms=4567)
        original = await api.get_message('om_actual')
        self.assertEqual((calls[0].start_time, calls[0].end_time), ('1', '5'))
        self.assertEqual(calls[0].page_token, 'cursor')
        self.assertEqual(calls[0].page_size, 50)
        self.assertEqual(calls[0].sort_type, 'ByCreateTimeAsc')
        self.assertIsNone(calls[1].start_time)
        self.assertIsNone(calls[1].end_time)
        self.assertEqual(calls[2].user_id_type, 'open_id')
        self.assertEqual(original['message_id'], 'om_actual')

    async def test_api_denial_and_sdk_exception_are_errors_not_empty_history(self):
        async def alist(_):
            return response(code=21001)
        resource = SimpleNamespace(alist=alist)
        api = FeishuHistoryAPI(SimpleNamespace(im=SimpleNamespace(v1=SimpleNamespace(message=resource))))
        with self.assertRaises(HistoryAPIError) as denied:
            await api.list_messages(container_type='chat', container_id='oc_team', lower_ms=0, upper_ms=1)
        self.assertEqual(denied.exception.code, 21001)
        async def failure(_):
            raise RuntimeError('secret raw exception')
        resource.alist = failure
        with self.assertRaises(HistoryAPIError) as failed:
            await api.list_messages(container_type='chat', container_id='oc_team', lower_ms=0, upper_ms=1)
        self.assertEqual(str(failed.exception), 'sdk_error')


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def wait_for(self, predicate):
        async with asyncio.timeout(2):
            while not predicate():
                await asyncio.sleep(0.005)

    async def test_original_service_start_reconnect_reject_sink_failure_and_retry_hooks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret = root / 'fake-secret'
            secret.write_text('fake-secret', encoding='utf-8')
            channel, api, received = FakeChannel(), API(), []
            controller = RecordingController()
            async def sink(record):
                received.append(record)
                return True
            service = FeishuNodeService(node_id='A', project_id='fpga-main', group_id='oc_team',
                astra_app_id='cli_a', astra_secret_file=secret, controller=controller,
                channel_factory=lambda **_:channel, history_state_dir=root/'history',
                history_receiver=sink, history_pending=lambda:[], history_api=api, retry_seconds=0.1)
            await service.start()
            try:
                await self.wait_for(lambda: bool(received))
                self.assertEqual(controller.messages, [])
                initial = service.history.last_result['scan_id']
                await asyncio.to_thread(channel.handlers['reconnected'])
                await self.wait_for(lambda: service.history.last_result['scan_id'] != initial)
                api.pages[('chat', None)] = HistoryAPIError('api_error', 21001)
                channel.handlers['reject'](SimpleNamespace(chat_id='oc_team', sender_id='ou_human',
                    message_id='om_rejected', reason='stale'))
                await self.wait_for(lambda: service.history.last_result['status'] == 'gap')
                self.assertIn('21001', service.last_error)
                api.pages[('chat', None)] = page([message()])
                await self.wait_for(lambda: service.history.last_result['status'] == 'covered_visible')
                async def failing(_):
                    raise OSError('do not persist exception text')
                service.ingress.trusted_receiver = failing
                with self.assertRaises(OSError):
                    await channel.handlers['message'](FakeMessage(message_id='om_failed'))
                await self.wait_for(lambda: any(x.get('get') == 'om_failed' for x in api.calls))
                self.assertTrue(any(x['message_id'] == 'om_failed' for x in received))
            finally:
                await service.stop()
            self.assertIsNone(service._history_task)

    async def test_recovery_configuration_requires_durable_sink(self):
        with self.assertRaises(ValueError):
            FeishuNodeService(node_id='A', project_id='p', group_id='oc_team',
                astra_app_id='cli_a', astra_secret_file=Path('unused'), controller=RecordingController(),
                history_state_dir=Path('unused'))

    async def test_source_gate_precedes_connection_and_reconnect_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret = root / 'fake-secret'; secret.write_text('fake-secret')
            events = []
            channel = FakeChannel()
            async def connect(**kwargs):
                self.assertEqual(events, ['gate'])
                events.append('connected')
            channel.connect_until_ready = connect
            def gate():
                events.append('gate')
                return True
            async def begin(document):
                self.assertEqual(events[-1], 'gate' if len(events) > 2 else 'connected')
                events.append('scan')
                return True
            async def sink(record): return True
            service = FeishuNodeService(node_id='A', project_id='fpga-main', group_id='oc_team',
                astra_app_id='cli_a', astra_secret_file=secret, controller=RecordingController(),
                channel_factory=lambda **_: channel, history_state_dir=root/'history',
                history_receiver=sink, history_pending=lambda: [], history_api=API(),
                history_recheck=gate, history_scan_begin=begin, retry_seconds=60)
            await service.start()
            try:
                await self.wait_for(lambda: events.count('scan') == 1)
                await asyncio.to_thread(channel.handlers['reconnected'])
                await self.wait_for(lambda: events.count('scan') == 2)
                self.assertEqual(events, ['gate', 'connected', 'scan', 'gate', 'scan'])
            finally:
                await service.stop()


if __name__ == '__main__':
    unittest.main()
