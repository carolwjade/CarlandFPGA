import datetime,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';REVIEW=OUT/'actor-native-evidence-review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert sha(REVIEW/'findings.md')=='923305d4b0a2045ff2fa2255e282faa9c9f13b581f5c88c0d1a3916739384f07'
assert sha(REVIEW/'receipt.json')=='a43b3dce5435f760480456ec8f88baa8a106b9a61f9b980dd535eda9638f71b5'
r=read(REVIEW/'receipt.json')
for name,h in r['artifacts'].items():assert sha(REVIEW/name)==h,name
terminal=read(REVIEW/'native_complete.json')
if 'content' in terminal:terminal=json.loads(next(c['text'] for c in terminal['content'] if c['type']=='text'))
assert terminal['status']=='completed' and terminal['terminal'] is True and terminal['job_id']=='child-000d3740dbee4f6cb8422c1cc22bf527'
manifest=read(REVIEW/'inspected-manifest.json')['files'];assert len(manifest)==758
for name,row in manifest.items():
    p=Path(name);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],name
cases=read(REVIEW/'reconciliation.json')['cases'];assert len(cases)==3 and all(c['resources_confirmed']==18 and c['passed_fixture_expectation'] is True for c in cases)
assert cases[0]['exit_code']==0 and cases[0]['owner_terminated'] is False and cases[0]['normal_exit_success'] is True
assert all(c['normal_exit_success'] is False and c['evidence_success'] is False for c in cases[1:])
assert cases[2]['state']=='QUARANTINED' and cases[2]['receipt_state']=='ALLOCATING' and cases[2]['evidence_errors']==44
scope=read(PRODUCT/'docs/competition/deepeye-2026/immutable_scope.json')
assert hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
selection={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'director':'01a13d7e-dcf1-7272-a738-a637dd62ff9d','generation':2,'decision':'Accept exact three-file actor native probe and three one-shot actual CPU lifecycle fixture observations; preserve expected failures and evidence incompleteness','candidate_manifest_sha256':'415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3','review_receipt_sha256':sha(REVIEW/'receipt.json'),'findings_sha256':sha(REVIEW/'findings.md'),'files_verified':758,'cases':cases,'resources_confirmed':54,'original_generic_cleanup_success':'false in normal/expiry receipts due expected primary; retained','persistent_failure_receipt':'stale ALLOCATING snapshot; final ownership supported by original retained context/readback','dedicated_interpreter':{'session':48521,'live_revalidated_at':'exec chunk23f95f','closing_permitted_after_live_identity_and_resolved_resource_recheck':True,'main_thread_ends':False},'all29_real_AI_BOOT_Run_H12':'not_run','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'}
with (OUT/'actor-native-main-selection.json').open('x',encoding='utf-8') as f:json.dump(selection,f,indent=2);f.write('\n')
print(json.dumps({'selection_sha256':sha(OUT/'actor-native-main-selection.json'),'verified_files':758,'actual_cases':3,'resolved_resource_references':54,'expected_failures_preserved':True}))
