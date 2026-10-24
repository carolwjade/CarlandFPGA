import asyncio,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from fpga_mesh.child_control import LocalControlFileClient
def sha(name):return hashlib.sha256((H/name).read_bytes()).hexdigest()
async def main():
 p=json.loads((H.parent/'actor-native-repair-lease.private.json').read_text(encoding='utf-8-sig'));client=LocalControlFileClient(pathlib.Path(p['original_control_file']))
 args={'job_id':'child-bc0ea14b25eb4fbfbcbf1e2e3606266e','lease_token':p['lease_token'],'agent_id':'/root/pc_direct_review_20261018'}
 valid=await client.call('native_validate',args)
 if valid.get('execution_allowed') is not True:print(json.dumps({k:valid.get(k) for k in ['status','terminal','execution_allowed','reason']}));return
 text=('A-actor-native-classification-repair-20261019-v1 frozen for independent review. Exact2 modified harness/doc plus unchanged fixture in3-file bundle. Evidence .planning/deepeye-resume-20261018/actor-native-repair/. source manifest SHA256 '+sha('source-manifest.json')+'; report '+sha('report.md')+'; receipt '+sha('receipt.json')+'; manifest '+sha('manifest.json')+'. '
 +'ANH-R1 fixed: retain exact original process ref/resource_id; after normal cleanup require its recorded builtin int exit0 and backend.terminated exactly False, preserve value/type/source and continuity separately from cleanup. Missing/bool/float/subclass/nonzero/other-process/owner-terminated outcomes fail in memory and persisted result. Expected negative cases retain fixture expectation but normal_exit_success/evidence_success False. Original9 reviewer source/assertions unchanged:RED9/1failure toGREEN9pass; added3 methods with10-entry matrix RED13subfailures toGREEN3pass. Existing13 discovered=10offline pass/3native genuine skip. Primary/cleanup-once/unknown strong recovery/exclusive result writes preserved. Only2 product paths changed; actor/G06/fixture and old evidence unchanged, hashes not oldHEAD used. No actual native/registry/process/stage/network/service/board/Git effects. H01-H15 canonical c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 unchanged; real AI/BOOT/ai_lease/fullH12/Run/game/board/all29 remain not_run. Main acceptance and fresh exact allow/native remain pending independent review.')
 result=await client.call('native_complete',{'job_id':args['job_id'],'lease_token':p['lease_token'],'text':text});assert result.get('status')=='completed' and result.get('terminal') is True
 (H/'native_complete.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result.get(k) for k in ['job_id','work_id','status','terminal']},ensure_ascii=False))
asyncio.run(main())
