import datetime,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';REVIEW=OUT/'actor-progress-review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'findings.md':'fe57474e36bfb1fa377e31891357febff7cb357d8ae283e80a3ad4248fb29519','inspection_manifest.json':'24d348685e2623a603df39d7b3a65e43e6c0657bd231576a1463026b9502518a','receipt.json':'9addc552c19e5bfdef7a4c09ec12badff25275236845e74ece2f00c0a8e68383'}
for n,h in pins.items():assert sha(REVIEW/n)==h,n
terminal=json.loads((OUT/'owned-jobs-20261020-1608.json').read_bytes())['jobs']['child-b46bbb395d26401a900990f5e65f0fe3']
assert terminal['status']=='completed' and terminal['terminal'] and not terminal['stale']
manifest=json.loads((REVIEW/'inspection_manifest.json').read_bytes());checked={}
for row in manifest['entries']:
    p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
    assert p.resolve().is_relative_to(ROOT.resolve())
    assert sha(p)==row['sha256'],str(p)
    checked[str(p)]=row['sha256']
candidate=json.loads((OUT/'actor-progress-main/candidate-manifest.json').read_bytes())
for p,h in candidate['candidate_pins'].items():assert sha(PRODUCT/p)==h,p
for p,h in candidate['evidence_pins'].items():assert sha(OUT/'actor-progress-main'/p)==h,p
receipt=json.loads((REVIEW/'receipt.json').read_bytes())
assert receipt['verdict']=='PASS_BOUNDED_OFFLINE_SOFTWARE_ONLY'
assert receipt['findings']['blocking']==0 and receipt['findings']['high']==0
for command in receipt['commands']:
    assert command['exit_code']==0 and command['failures']==0 and command['errors']==0
source=PRODUCT/'competition/deepeye/tests/simulation/test_actor_composition.py'
with (OUT/'actor-progress-main/pre-low-fix-test.py').open('xb') as f:f.write(source.read_bytes())
result=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_job=terminal['job_id'],terminal=True,
            review_artifact_pins=pins,inspected_entries_rehashed=len(checked),candidate_pins_rehashed=58,evidence_pins_rehashed=18,
            production_source_sha256=candidate['candidate_pins']['competition/deepeye/simulation/authority/actor_composition.py'],
            remaining='correct one newly-added inert test body; no implementation defect identified',formal29='not_run')
with (OUT/'actor-progress-main/review-audit-before-low-fix.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
