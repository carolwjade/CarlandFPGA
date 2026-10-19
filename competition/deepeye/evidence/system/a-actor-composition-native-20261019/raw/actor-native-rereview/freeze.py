from pathlib import Path
import hashlib,json,subprocess,ast
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'.local/deepeye-implementation-a'
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=O.parent/'actor-native-repair/source-manifest.json'
assert sha(manifest.read_bytes())=='415fb81c4c47ae8b1024bc3079f24866094bc737c6ebf3760b522b14b5ca39e3'
assert sha((O.parent/'actor-native-repair/report.md').read_bytes())=='e2fb15ae4ef7ba531964e57d6f3f647a33ed96284142c37a2f76a8c1b783f1c7'
terminal=json.loads((O.parent/'actor-native-repair/native_complete.json').read_text('utf-8'))
assert terminal['status']=='completed' and terminal['terminal'] is True
last=json.loads((O/'closure.command.json').read_text('utf-8'))['after']
files={}
for n,data in last['files'].items():
    raw=(P/n).read_bytes();assert sha(raw)==data['sha256']
    target=O/'frozen'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    result={}
    for mode,args in [('raw',['git','hash-object','--stdin']),('clean',['git','hash-object','--path='+n,'--stdin'])]:
        r=subprocess.run(args,input=raw,cwd=P,capture_output=True);assert r.returncode==0
        result[mode]=r.stdout.decode().strip()
    assert result['raw']==result['clean'],n
    files[n]=dict(data,raw_git_object=result['raw'],clean_git_object=result['clean'])
old=O.parent/'actor-native-review/review_cases.py'
assert (O/'review_cases.py').read_bytes()==old.read_bytes()
assert (O/'exit_boundaries.py').read_bytes()==(O.parent/'actor-native-repair/exit_boundaries.py').read_bytes()
for label,count in [('original9',9),('offline',13),('closure',4)]:
    row=json.loads((O/(label+'.command.json')).read_text('utf-8'))
    assert row['exit_code']==0 and row['before']==row['after']
    log=(O/(label+'.stderr.log')).read_text('utf-8')
    assert 'Ran '+str(count)+' tests' in log
    assert ('OK (skipped=3)' if label=='offline' else 'OK') in log
origins=json.loads((O/'module-origins.json').read_text('utf-8'))
for row in origins.values():assert Path(row['path']).is_relative_to(P) and sha(Path(row['path']).read_bytes())==row['sha256']
owner_ast=ast.parse((P/'competition/deepeye/simulation/isolation/actor_owner.py').read_text('utf-8'))
policy=next(n for n in owner_ast.body if isinstance(n,ast.ClassDef) and n.name=='ActorPolicy')
fields=[n.target.id for n in policy.body if isinstance(n,ast.AnnAssign)];assert len(fields)==14
compat={'basis':'current accepted actor manifest98f792a4 and exact unchanged native helpers; static only',
 'ActorPolicy_fields':fields,'reader_contract':'same exact owner, original output ref/native, guarded _entry, _reference/_sample before/after; helper8192 consumption/test256 cap',
 'exit_contract':'WindowsCleanupBackend.exit_codes[original resource_id], initialized dict; terminated initialized False/sets True only successful owner TerminateProcess; win32.exit_code returns DWORD.value',
 'native_abi_executed':False,'unreviewed_actor_composition_imported':False}
(O/'compatibility.json').write_text(json.dumps(compat,indent=2)+'\n',encoding='utf-8')
frozen={'work_id':'A-actor-native-classification-rereview-20261019-v1','job_id':'child-5c2571e073f543e5aa015745e787cfc7',
 'candidate_manifest_sha256':sha(manifest.read_bytes()),'actor_manifest_sha256':'98f792a4f5d699ab235179dbaa345867c8fd32975ed9c32d8b28e042c773f670',
 'files':files,'original9_sha256':sha(old.read_bytes()),'original9_byte_identical':True,'old_evidence_unchanged':True,
 'requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','native':'not_run'}
(O/'source-manifest.json').write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_manifest_sha256':sha((O/'source-manifest.json').read_bytes()),'files':len(files),'original9_sha256':sha(old.read_bytes())}))
