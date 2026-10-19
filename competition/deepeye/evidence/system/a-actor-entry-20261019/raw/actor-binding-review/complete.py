import asyncio,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from fpga_mesh.child_control import LocalControlFileClient
def sha(name):return hashlib.sha256((H/name).read_bytes()).hexdigest()
async def main():
 p=json.loads((H.parent/'actor-binding-review-lease.private.json').read_text(encoding='utf-8-sig'));client=LocalControlFileClient(pathlib.Path(p['original_control_file']))
 args={'job_id':'child-f51ad639fe7a4aed9c4f5aff827ccea6','lease_token':p['lease_token'],'agent_id':'/root/pc_direct_review_20261018'}
 valid=await client.call('native_validate',args)
 if valid.get('execution_allowed') is not True:print(json.dumps({k:valid.get(k) for k in ['status','terminal','execution_allowed','reason']}));return
 text=('A-actor-binding-independent-review-20261019-v1 completed bounded software review, no new blocking defect reproduced. Evidence .planning/deepeye-resume-20261018/actor-binding-review/. findings SHA256 '+sha('findings.md')+'; receipt '+sha('receipt.json')+'; manifest '+sha('manifest.json')+'. '
 +'Seven-file candidate manifest98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670 live/frozen/raw-clean verified. Exact original8 source de9ffef018ebb645ff785759442d1487b02b1b84c6e72733e8e263ca30c84f4f passed8/0skip on current source;4 distinct boundary methods passed4/0skip; actual module origins/hashes verified and no isolation.win32 import. AOR-R1 per-target activation dispatch/recheck, AOR-R2 exact int two-phase Wait and AOR-R3 all4 integer masks addressed at software scope. Primary/callback BaseException separation, successor advancement, foreign/malformed old close, evidence-only quarantine late bind and post-terminate malformed terminal/no-retry independently checked. Original68 tests/helpers unchanged, additive Resource import verified; deliberate unwired provider gap preserved, not safety acceptance. Main148 current-G06 joint regression separately owned, not duplicated or claimed. Product/old evidence read-only, no native/stage/registry/service/board/network/Git effects. H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged; formal29/real AI/H12/game/board/Run/native remain not_run. Main owns acceptance.')
 result=await client.call('native_complete',{'job_id':args['job_id'],'lease_token':p['lease_token'],'text':text});assert result.get('status')=='completed' and result.get('terminal') is True
 (H/'native_complete.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result.get(k) for k in ['job_id','work_id','status','terminal']},ensure_ascii=False))
asyncio.run(main())
