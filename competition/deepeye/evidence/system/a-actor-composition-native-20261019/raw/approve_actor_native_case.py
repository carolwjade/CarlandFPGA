"""Main's exact one-case authorization after independent closure and byte audit."""
import datetime,hashlib,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];PRODUCT=ROOT/'.local/deepeye-implementation-a';HERE=OUT/'actor-native-main'
DIRECTOR='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
case=sys.argv[1];cases=('retained-natural-exit','fixed-unbound-expiry','persistence-after-acquisition');assert case in cases
for previous in cases[:cases.index(case)]:
    prev=Path(load(HERE/(previous+'.stage.json'))['attempt_directory'])
    r=load(prev/'main-return.json');assert r['passed_fixture_expectation'] is True and r['unresolved'] is False and r['source_hashes_unchanged'] is True
review=OUT/'actor-native-rereview';receipt=load(review/'receipt.json')
assert sha(review/'receipt.json')=='4d8cde10a943948d82b70daf0a67b3f9eec793315e91f09b1163d182c7a8400d'
assert sha(review/'findings.md')=='964d24c1ac7f6a6732a6aa8af735be69562b00f7df16217d3d706598ad8b783e'
for name,digest in receipt['artifacts'].items():assert sha(review/name)==digest,name
terminal=load(review/'native_complete.json')
if 'content' in terminal:terminal=json.loads(next(c['text'] for c in terminal['content'] if c['type']=='text'))
assert terminal['status']=='completed' and terminal['terminal'] is True
assert sha(review/'source-manifest.json')=='49a6b16e6e1c8d7e87cada6b88cac2052b6d572d5b37fabecbd47558580fc826'
for name,row in load(review/'source-manifest.json')['files'].items():assert sha(PRODUCT/name)==row['sha256'],name
for label,count in [('original9',9),('closure',4),('offline',13)]:
    command=load(review/(label+'.command.json'));assert command.get('exit_code',command.get('returncode'))==0
    log=(review/(label+'.stderr.log')).read_text(encoding='utf-8');assert ('Ran '+str(count)+' tests') in log and '\nOK' in log
transfer=load(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json');assert transfer['status']=='active' and transfer['new_director_thread_id']==DIRECTOR and transfer['director_generation']==2
index=load(HERE/(case+'.stage.json'));attempt=Path(index['attempt_directory']);assert attempt.parent==HERE
assert sha(attempt/'allow-proposal.json')==index['proposal_sha256']
audit=load(attempt/'stage-main-audit.json');assert audit['native_execution'] is False and audit['zip_crc']=='passed' and audit['final_stage_files_verified']==10
assert not (attempt/'execution-claimed.json').exists() and not(attempt/'allow.json').exists()
allow=load(attempt/'allow-proposal.json');assert allow['native_execution'] is False and allow['approved_by'] is None
allow.update(approved_by=DIRECTOR,native_execution=True,case=case)
sys.path[:0]=[str(PRODUCT),str(PRODUCT/'competition/deepeye'),str(ROOT/'.local/deepeye-host-deps')]
from competition.deepeye.tests.isolation import test_actor_windows_live as probe
probe.validate_allow_record(allow,PRODUCT,attempt,case)
assert not any(n.endswith('.isolation.win32') for n in sys.modules)
with (attempt/'allow.json').open('x',encoding='utf-8') as f:json.dump(allow,f,indent=2);f.write('\n')
approval={'approved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main':DIRECTOR,'generation':2,'case':case,'attempt_directory':str(attempt),'human_authorization':'Existing autonomous DeepEye local implementation and independently reviewed CPU lifecycle validation; no new user permission needed','harness_independent_review_accepted':True,'review_receipt_sha256':sha(review/'receipt.json'),'candidate_manifest_sha256':index['candidate_manifest_sha256'],'stage_audit_sha256':sha(attempt/'stage-main-audit.json'),'allow_sha256':sha(attempt/'allow.json'),'scope':'One fresh CPU actor lifecycle fixture only, original registry/process/profile controls; no board/service/model/product Run','no_retry':True,'all29':'not_run'}
with (attempt/'main-approval.json').open('x',encoding='utf-8') as f:json.dump(approval,f,indent=2);f.write('\n')
print(json.dumps(approval))
