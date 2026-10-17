"""Fresh-process offline check of the installed SDK import-time loop capture.

Usage: python -B -X utf8 sdk_import_probe.py <candidate checkout>
No channel is constructed, connected, sent or disconnected. The only SDK call is import.
"""
import asyncio
import hashlib
import importlib.metadata
import json
import pathlib
import sys
import threading

sys.path.insert(0,str(pathlib.Path(sys.argv[1]).resolve()))
from fpga_mesh.feishu_channel import _load_default_channel_factory

assert 'lark_channel' not in sys.modules
external_network_attempts=[]
def audit(event,args):
    if event=='socket.connect':
        address=args[1]
        # Windows event loops may construct internal loopback socket pairs.
        if isinstance(address,tuple) and address[0] in ('127.0.0.1','::1'):
            return
        external_network_attempts.append(event)
        raise AssertionError('External network is forbidden in this import-only probe')
    if event=='socket.getaddrinfo' and args[0] not in ('localhost','127.0.0.1','::1',None):
        external_network_attempts.append(event)
        raise AssertionError('External DNS is forbidden in this import-only probe')
sys.addaudithook(audit)

async def main():
    controller_loop=asyncio.get_running_loop()
    controller_thread=threading.get_ident()
    observations={}
    def load():
        observations['different_import_thread']=threading.get_ident()!=controller_thread
        try:asyncio.get_running_loop()
        except RuntimeError:observations['worker_has_no_running_loop']=True
        else:raise AssertionError('Worker unexpectedly has a running loop')
        return _load_default_channel_factory('oc_offline_fixture')
    factory=await asyncio.to_thread(load)
    import lark_channel.ws.client as ws_client
    sdk_loop=ws_client.loop
    try:
        assert callable(factory)
        assert sdk_loop is not controller_loop and not sdk_loop.is_running()
        assert not external_network_attempts
        observations.update(sdk_loop_distinct=True,sdk_loop_running=False,
            controller_still_running=controller_loop.is_running(),sdk_version=importlib.metadata.version('lark-channel-sdk'),
            sdk_ws_source_sha256=hashlib.sha256(pathlib.Path(ws_client.__file__).read_bytes()).hexdigest(),
            external_network_attempts=0,channel_instances=0,live_requests=0,
            scope='Fresh import only; no real connect/disconnect/reconnect or full SDK lifecycle validation')
        print(json.dumps(observations,indent=2))
    finally:
        if sdk_loop is not controller_loop and not sdk_loop.is_running():sdk_loop.close()
asyncio.run(main())
