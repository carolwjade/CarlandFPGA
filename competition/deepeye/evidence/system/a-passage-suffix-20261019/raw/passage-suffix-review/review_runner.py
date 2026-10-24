"""Bounded independent numerical review, only owned outputs and process env."""
from pathlib import Path
import difflib,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';A=O.parent/'passage-suffix-implementation'
PIN='c4b5b656e78a084e36e8bfcedfdb2f65144226d8af7b336f4588cc4352df6657';HEAD='b19a528344d8675fedb41f37e7de23f1112f1871'
def digest(path):
    data=path.read_bytes();return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def save(name,value):(O/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def check():
    assert digest(A/'source-manifest.json')['sha256']==PIN
    assert digest(A/'report.md')['sha256']=='7330dd0852611d02997eb3c0318afa3336889d579ce1e411716212e1a4028fb7'
    baseline=json.loads((A/'baseline.json').read_bytes());manifest=json.loads((A/'source-manifest.json').read_bytes())
    for name,want in manifest.items():
        assert digest(P/name)==want,name
        assert digest(A/'frozen'/name)==want,name
    deps={name:digest(P/name) for name in baseline['files'] if name not in manifest}
    for name,want in deps.items():assert want==baseline['files'][name],name
    for name,want in baseline['old_evidence'].items():assert digest(R/name)==want,name
    design=R/'.planning/deepeye-resume-20261018/passage-refinement-design/design.md'
    assert digest(design)['sha256']=='2e0b5eaa18f6e1197befc5fd1e76513f3e54b0199823827e2fb6994777800596'
    req=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())['requirements']
    (P/'docs/competition/deepeye-2026/immutable_scope.md').read_text(encoding='utf8')
    assert hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    transfer=json.loads((R/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
    assert transfer['status']=='active' and transfer['director_generation']==2 and transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    head=subprocess.run(['git','-C',str(P),'rev-parse','HEAD'],capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    assert head.returncode==0 and head.stdout.decode().strip()==HEAD
    return {'head':HEAD,'sources':manifest,'dependencies':deps,'old_design_evidence':baseline['old_evidence']}
mode=sys.argv[1];integrity=check()
if mode=='before':
    terminal=json.loads((A/'native_completion.json').read_bytes());assert terminal['status']=='completed' and terminal['terminal'] is True and terminal['duplicate'] is False
    diff=[]
    for name in integrity['sources']:
        current=(P/name).read_bytes();before=(A/'before'/name).read_bytes()
        destination=O/'frozen'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(current)
        diff+=list(difflib.unified_diff(before.decode().splitlines(True),current.decode().splitlines(True),fromfile='base/'+name,tofile='candidate/'+name))
    (O/'independent.diff').write_text(''.join(diff),encoding='utf8')
    historical={p.relative_to(R).as_posix():digest(p) for p in A.rglob('*') if p.is_file() and 'temp' not in p.relative_to(A).parts}
    integrity['author_evidence']=historical
    save('before.json',integrity)
    print('Exact frozen4, unchanged41 dependencies/16 design files and base HEAD verified.')
elif mode=='after':
    before=json.loads((O/'before.json').read_bytes())
    assert all(integrity[k]==before[k] for k in integrity)
    for name,want in before['author_evidence'].items():assert digest(R/name)==want,name
    for name,want in integrity['sources'].items():assert digest(O/'frozen'/name)==want,name
    save('after.json',integrity);print('All source/dependency/author/design evidence stable; HEAD unchanged.')
else:
    temp=O/'temp';temp.mkdir(exist_ok=True)
    env=dict(os.environ);env.update(PYTHONPATH=str(P)+os.pathsep+str(R/'.local/deepeye-host-deps'),PYTHONDONTWRITEBYTECODE='1',TEMP=str(temp),TMP=str(temp))
    env.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT',None)
    cmd=[sys.executable,'-B','-X','utf8']
    if mode=='253':
        cmd+=['-m','unittest','-v']+['competition.deepeye.tests.simulation.'+n for n in ('test_passage_phase','test_motion_executor','test_workspace_boundaries','test_solid_clearance','test_pc_direct_runtime','test_certified_path','test_gate_clearance','test_gate_geometry','test_kinematics')]
    else:cmd+=[str(O/'independent_suffix_cases.py')]
    run=subprocess.run(cmd,cwd=P,env=env,capture_output=True,timeout=90)
    (O/(mode+'.stdout.bin')).write_bytes(run.stdout);(O/(mode+'.stderr.bin')).write_bytes(run.stderr)
    save(mode+'.command.json',{'command':cmd,'cwd':str(P),'exit_code':run.returncode,'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'source_manifest_sha256':PIN,'sources':integrity['sources']})
    print(run.stderr.decode('utf8','replace'));print('EXIT',run.returncode);sys.exit(run.returncode)
