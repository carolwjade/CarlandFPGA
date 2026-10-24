import asyncio,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]))
from fpga_mesh.child_control import LocalControlFileClient
def sha(name):return hashlib.sha256((H/name).read_bytes()).hexdigest()
async def main():
 p=json.loads((H.parent/'actor-native-preparation-lease.private.json').read_text(encoding='utf-8-sig'))
 client=LocalControlFileClient(pathlib.Path(p['original_control_file']))
 args={'job_id':'child-ccfb46268a8e450da682eac66cffe460','lease_token':p['lease_token'],'agent_id':'/root/pc_direct_review_20261018'}
 valid=await client.call('native_validate',args)
 if valid.get('execution_allowed') is not True:
  print(json.dumps({k:valid.get(k) for k in ['status','terminal','execution_allowed','reason']}));return
 text=('A-actor-native-fixture-preparation-20261019-v1 ready for independent review; no native execution. Exact3 NEW product files frozen under .planning/deepeye-resume-20261018/actor-native-preparation/. '
       +'source manifest SHA256 '+sha('source-manifest.json')+'; report '+sha('report.md')+'; receipt '+sha('receipt.json')+'; evidence manifest '+sha('evidence-manifest.json')+'. '
       +'Final13 discovered=10 offline pass/3 native skip, exit0; initial RED6 failures/3 skips preserved. Fixture fixed READY and single-byte X protocol plus natural exit. Test-only guarded consuming reader; no parent WriteFile due missing bounded deadline. Future cases retained-natural-exit, simultaneous unbound readiness/lifetime expiry, and original-acquisition persistence failure. Fresh stage/full rehash/main exact-hash allow/one-shot claim/interactive strong recovery context required. Concurrent repaired actor manifest not bound and runtime staging not run. H01-H15 canonical SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 preserved; actual native/AI/BOOT/ai_lease/H12/geometry/Run/board/all29 remain not_run. No other source edits, service effects or external sends. Main owns acceptance and any actual execution.')
 result=await client.call('native_complete',{'job_id':args['job_id'],'lease_token':p['lease_token'],'text':text})
 assert result.get('status')=='completed' and result.get('terminal') is True,result.get('status')
 (H/'native_completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result.get(k) for k in ['job_id','work_id','status','terminal']},ensure_ascii=False))
asyncio.run(main())
