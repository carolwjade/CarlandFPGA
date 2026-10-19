import datetime,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
review=OUT/'actor-composition-review';author=OUT/'actor-composition-implementation'
expected={'findings.md':'10f9c9096446d6e428c1480cee9fba2cc3f9f6f713c9f46024014f0a6e04eff9','receipt.json':'df3621179ea1c43036449c12b769cc4787c14dc821e5e73d684f57646dce2f54','manifest.json':'7bc0e27d805df7f35ad28110b06d651fda7cb98b99ac3361fcc3fa1ff02b6494'}
for name,h in expected.items():assert sha(review/name)==h,name
for row in read(review/'manifest.json')['files']:
    p=review/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
terminal=read(review/'native_complete.json');assert terminal['job_id']=='child-f77104b71ea14097ba5a69ae79badaca' and terminal['status']=='completed' and terminal['terminal'] is True
assert sha(author/'source-manifest.json')=='11663f50a276bee91cb77e27693d33e101d72a47c64cba23e269d10589ea034e'
selected={}
for row in read(author/'source-manifest.json')['files']:
    assert sha(PRODUCT/row['path'])==row['sha256'];selected[row['path']]=row['sha256']
before=read(review/'before.json')['files'];after=read(review/'after.json')['files'];assert len(before)==58 and before==after
for name,h in before.items():assert sha(PRODUCT/name)==h,name
for label,n in [('regression172',172),('independent5',5),('progress-gap',1)]:
    r=read(review/(label+'.result.json'));assert r['tests']==n and r['failures']==r['errors']==r['skipped']==0 and r['successful'] is True
    command=read(review/(label+'.command.json'));assert command.get('exit_code',command.get('returncode'))==0
    for module,entry in r['module_origins'].items():
        path=Path(entry['path']);assert path.is_relative_to(PRODUCT) and sha(path)==entry['sha256'],module
gap=read(review/'progress-final-fence-gap.json');assert gap['committed_after_synthetic_progress_loss'] is True and gap['actual_revision']==1
decision={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main':'01a13d7e-dcf1-7272-a738-a637dd62ff9d','generation':2,'selection':'accept exact three-file deliberately unavailable production library at bounded software scope','sources':selected,'author_manifest_sha256':sha(author/'source-manifest.json'),'independent_review':expected,'independent_terminal':terminal['job_id'],'verified_source_files':58,'tests':'172 + 5 distinct protection methods; additional negative witness separately classified','negative_witness':gap,'next_dependency':'original authenticated causal channel and bounded progress freshness/deadline integrated into final fence; accepting verifier alone insufficient','production_activation':'unavailable before registry acquisition; keep gate','native_AI_BOOT_Run_both_full_H12_formal29':'not_run','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'}
with (OUT/'actor-composition-main-selection.json').open('x',encoding='utf-8') as f:json.dump(decision,f,indent=2);f.write('\n')
print(json.dumps({'decision':decision['selection'],'sources':len(selected),'deps':58,'sha256':sha(OUT/'actor-composition-main-selection.json')}))
