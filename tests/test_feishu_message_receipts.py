import unittest
from types import SimpleNamespace as N
from fpga_mesh.feishu_channel import FeishuIngress


class MessageReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.messages = []
        async def receive(message):
            self.messages.append(message); return True
        self.ingress = FeishuIngress(node_id='A', project_id='fpga-main', group_id='oc_team',
            app_id='cli_a', controller=N(), allowed_sender_ids={'ou_human'}, trusted_receiver=receive)

    def message(self, **changes):
        fields = dict(chat_id='oc_team', chat_type='group', sender_type='user', sender_id='ou_human',
            body_text='', content_text='@FPGA Astra A', raw_content_type='text',
            message_id='om_mention', create_time=1792200000000, raw={'content':'{"text":"@_user_1"}'},
            mentions=(N(name='FPGA Astra A', is_bot=True, open_id='ou_bot'),), mentioned_bot=True)
        return N(**{**fields, **changes})

    async def test_bare_mention_has_a_durable_readable_envelope(self):
        self.assertTrue(await self.ingress.ingest(self.message()))
        self.assertEqual(len(self.messages), 1)
        self.assertIn('@FPGA Astra A', self.messages[0].payload['text'])
        self.assertEqual(self.messages[0].payload['feishu']['body_text'], '')
        self.assertEqual(self.messages[0].payload['feishu']['raw_message']['content'], '{"text":"@_user_1"}')

    async def test_file_reference_is_preserved_without_claiming_download(self):
        msg = self.message(body_text='<file key="file_fake"/>', content_text='', raw_content_type='file',
            resources=[N(type='file', file_key='file_fake', file_name='要求.pdf', duration_ms=None,
                         cover_image_key=None)])
        await self.ingress.ingest(msg)
        saved = self.messages[0].payload['feishu']
        self.assertEqual(saved['resources'][0]['file_key'], 'file_fake')
        self.assertEqual(saved['resources'][0]['file_name'], '要求.pdf')
        self.assertFalse(saved['attachments_downloaded'])

    async def test_batch_preserves_each_original_identity(self):
        a=self.message(message_id='om_a', body_text='one')
        b=self.message(message_id='om_b', body_text='two')
        batch=self.message(message_id='om_b', body_text='one\ntwo', batched_sources=[a,b])
        self.assertTrue(await self.ingress.ingest(batch))
        self.assertEqual([m.platform_message_id for m in self.messages], ['om_a','om_b'])

