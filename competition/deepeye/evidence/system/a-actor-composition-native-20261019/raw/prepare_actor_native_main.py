"""Main-owned offline staging only; never enables or executes native cases."""
import datetime,hashlib,json,sys,uuid
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
case=sys.argv[1]
assert case in ('retained-natural-exit','fixed-unbound-expiry','persistence-after-acquisition')
HERE=OUT/'actor-native-main';HERE.mkdir(exist_ok=True)
index=HERE/(case+'.stage.json');assert not index.exists()
candidate=OUT/'actor-native-repair/source-manifest.json'
assert sha(candidate)=='415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3'
for row in json.loads(candidate.read_bytes())['files']:assert sha(PRODUCT/row['path'])==row['sha256']
for row in json.loads((OUT/'actor-binding-repair/source-manifest.json').read_bytes())['files']:assert sha(PRODUCT/row['path'])==row['sha256']
terminal=json.loads((OUT/'actor-native-repair/native_complete.json').read_bytes());assert terminal['status']=='completed' and terminal['terminal'] is True
sys.path[:0]=[str(PRODUCT),str(PRODUCT/'competition/deepeye'),str(ROOT/'.local/deepeye-host-deps')]
from competition.deepeye.tests.isolation import test_actor_windows_live as probe
attempt,proposal=probe.prepare_stage(HERE,uuid.uuid4().hex,PRODUCT)
assert proposal['native_execution'] is False and proposal['approved_by'] is None and proposal['case'] is None
assert not any(n.endswith('.isolation.win32') for n in sys.modules)
for name,digest in proposal['sources'].items():assert sha(PRODUCT/name)==digest
for name,digest in proposal['staged_files'].items():assert sha(attempt/'source-stage'/name)==digest
record={'case_prepared':case,'attempt_directory':str(attempt),'prepared_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_sha256':sha(attempt/'allow-proposal.json'),'candidate_manifest_sha256':sha(candidate),'source_files':len(proposal['sources']),'stage_files':len(proposal['staged_files']),'stage_bytes':sum((attempt/'source-stage'/n).stat().st_size for n in proposal['staged_files']),'python_version':sys.version,'python_base_prefix':sys.base_prefix,'native_execution':False,'native_modules_imported':False,'all29':'not_run'}
with index.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
