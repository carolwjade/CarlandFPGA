import asyncio,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from fpga_mesh.child_control import LocalControlFileClient
def sha(name):return hashlib.sha256((H/name).read_bytes()).hexdigest()
async def main():
 p=json.loads((H.parent/'entry-bridge-review-lease.private.json').read_text(encoding='utf-8-sig'));client=LocalControlFileClient(pathlib.Path(p['original_control_file']))
 args={'job_id':'child-f337f8c19052446ab2e5fbec9f7cd26b','lease_token':p['lease_token'],'agent_id':'/root/pc_direct_review_20261018'}
 valid=await client.call('native_validate',args)
 if valid.get('execution_allowed') is not True:print(json.dumps({k:valid.get(k) for k in ['status','terminal','execution_allowed','reason']}));return
 text=('A-entry-bridge-independent-review-20261019-v1 completed bounded exact-byte numerical review; no new blocking defect reproduced. '
  +'Evidence .planning/deepeye-resume-20261018/entry-bridge-review/ findings SHA256 '+sha('findings.md')+'; receipt '+sha('receipt.json')+'; manifest '+sha('manifest.json')+'. '
  +'Candidate manifest cb904c57a2f985ff02ddb67e5b426968ecf4a22a1b03ecca2d382f99901ece19 verified5 live/frozen/raw/clean and18 unaffected dependencies unchanged. 265 regressions pass/0skip in disjoint239+26 runs; initial argv omission retained and only missing26 added. Five independent methods have success evidence: four initial pass plus corrected valid zero-speed/yaw0 single method; original invalid zero-speed/yaw7000 guard error and script retained. Six normals/direct curve intervals, uniform-vs-point source error, genuine ramp late-other-face rollback after bridge, work budget, same-face/no-exit/full-dt/red suffix, zero speed and speed carry boundaries checked. Conditional analytic uniform support and original-plan ENTERED proof composition inspected; no acceptance beyond numerical assumptions. 23 pinned files unchanged, no source repair/native/actor/service/board/network/Git effects. H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 preserved; all29/G06/G07/real AI/H12/game/board/Run remain not_run. Main owns acceptance.')
 result=await client.call('native_complete',{'job_id':args['job_id'],'lease_token':p['lease_token'],'text':text});assert result.get('status')=='completed' and result.get('terminal') is True
 (H/'native_complete.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result.get(k) for k in ['job_id','work_id','status','terminal']},ensure_ascii=False))
asyncio.run(main())
