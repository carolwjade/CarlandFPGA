import asyncio,json,pathlib,sys
E=pathlib.Path(__file__).resolve().parent
ROOT=E.parents[2]
sys.path.insert(0,str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient
lease=json.loads((E/'lease.private.json').read_bytes())
async def run():
    client=LocalControlFileClient(ROOT/'.local/deployment/node-a/.local/node-a/main-control.json')
    return await client.call('native_validate',dict(job_id=lease['job_id'],lease_token=lease['lease_token'],agent_id='/root/g01_asset_adapter_repair_20261020'))
result=asyncio.run(run())
raw=json.dumps(result,ensure_ascii=False,indent=2)
assert lease['lease_token'] not in raw
with (E/'native-revalidate-response.json').open('x',encoding='utf-8') as f: f.write(raw+'\n')
assert result.get('execution_allowed') is True
print(json.dumps(dict(job_id=lease['job_id'],execution_allowed=True,status=result.get('status'))))
