from pathlib import Path
import hashlib,json,subprocess,ast
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
def sha(b):return hashlib.sha256(b).hexdigest()
def save_command(name,args,raw=None):
    r=subprocess.run(args,cwd=P,input=raw,capture_output=True)
    (O/(name+'.stdout.log')).write_bytes(r.stdout);(O/(name+'.stderr.log')).write_bytes(r.stderr)
    (O/(name+'.command.json')).write_text(json.dumps({'argv':args,'cwd':str(P),'exit_code':r.returncode},indent=2)+'\n',encoding='utf-8')
    assert r.returncode==0,r.stderr
    return r.stdout
manifest=O.parent/'actor-native-preparation/source-manifest.json'
assert sha(manifest.read_bytes())=='6474920de9d6ddd99eab6a7aa9ff66010fbcf40ba05a3b29954c4ebe3afdf9fa'
candidate={}
for row in json.loads(manifest.read_text('utf-8'))['files']:
    n=row['path'];raw=(P/n).read_bytes();assert sha(raw)==row['sha256']
    assert raw==(O.parent/'actor-native-preparation/frozen'/n).read_bytes()
    target=O/'frozen'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    raw_id=save_command('raw-'+Path(n).stem,['git','hash-object','--stdin'],raw).decode().strip()
    clean_id=save_command('clean-'+Path(n).stem,['git','hash-object','--path='+n,'--stdin'],raw).decode().strip()
    assert raw_id==clean_id==row['raw_git_object']==row['clean_git_object']
    candidate[n]={'sha256':sha(raw),'bytes':len(raw),'raw_git_object':raw_id,'clean_git_object':clean_id}
refs={}
original=O.parent/'actor-owner-implementation/source-manifest.json'
original_json=json.loads(original.read_text('utf-8'))
for row in original_json['files']:
    if Path(row['path']).name not in ('actor_owner.py','actor_lifetime.py'):continue
    raw=(O.parent/'actor-owner-implementation/candidate'/row['path']).read_bytes();assert sha(raw)==row['sha256']
    target=O/'references'/Path(row['path']).name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
    refs[row['path']]={'source':'frozen original actor candidate','sha256':sha(raw)}
for name in ('windows_cleanup.py','owned_resources.py','resource_cleanup.py','win32.py'):
    n='competition/deepeye/simulation/isolation/'+name
    raw=save_command('reference-'+Path(name).stem,['git','show','3f702903f1e16fa72eae15f03ba431b78de24bd0:'+n])
    assert sha(raw)==original_json['dependencies']['simulation/isolation/'+name]
    (O/'references'/name).write_bytes(raw);refs[n]={'source':'Git3f702903','sha256':sha(raw)}
for f in (O/'references').glob('*.py'):ast.parse(f.read_text('utf-8'))
# Static ABI only: exact policy positional field count and private helper names.
tree=ast.parse((O/'references/actor_owner.py').read_text('utf-8'))
policy=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ActorPolicy')
fields=[n.target.id for n in policy.body if isinstance(n,ast.AnnAssign)]
assert len(fields)==14
static={'original_ActorPolicy_fields':fields,'actual_native_compatibility':'not_run; moving actor repair not accepted here',
 'reader_adapter_imports':['actor_owner._entry','actor_lifetime._reference','actor_lifetime._sample'],
 'cleanup_exit_code_source':'WindowsCleanupBackend.wait_terminal stores original process resource_id -> exit_code; actor _entry only revokes on read failure and does not clean up before harness finally'}
(O/'static-compatibility.json').write_text(json.dumps(static,indent=2)+'\n',encoding='utf-8')
for label in ('offline','independent1','independent2'):
    data=json.loads((O/(label+'.command.json')).read_text('utf-8'));assert data['before']==data['after']
assert json.loads((O/'offline.command.json').read_text('utf-8'))['exit_code']==0
assert json.loads((O/'independent2.command.json').read_text('utf-8'))['exit_code']==1
log=(O/'offline.stderr.log').read_text('utf-8');assert 'Ran 13 tests' in log and 'OK (skipped=3)' in log
log=(O/'independent2.stderr.log').read_text('utf-8');assert 'Ran 9 tests' in log and 'FAILED (failures=1)' in log
witness=json.loads((O/'independent-witnesses.json').read_text('utf-8'))
crash=next(x for x in witness if x['mode']=='crash')
assert crash['passed'] and crash['backend']['exit_codes']['original-process']==17 and crash['backend']['terminated'] is False
assert crash['persisted_result']['passed'] is True
provenance={'candidate_manifest_sha256':sha(manifest.read_bytes()),'candidate':candidate,'references':refs,
 'author_report_sha256':sha((O.parent/'actor-native-preparation/report.md').read_bytes()),
 'author_receipt_sha256':sha((O.parent/'actor-native-preparation/receipt.json').read_bytes()),
 'actor_original_manifest_sha256':sha(original.read_bytes()),'native':'not_run'}
(O/'source-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_provenance_sha256':sha((O/'source-provenance.json').read_bytes()),'offline_pass':10,'native_skips':3,'independent_methods':9,'independent_failed':1}))
