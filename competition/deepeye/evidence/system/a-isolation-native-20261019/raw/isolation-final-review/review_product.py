"""Exact candidate integrity and bounded offline runner; no native opt-in."""
from pathlib import Path
import difflib,hashlib,json,os,shutil,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a';B=P/'competition/deepeye'
A=O.parent/'isolation-pair-repair';OLD=O.parent/'isolation-launcher-review'
PIN='4752b00aa62688041a493e28c0b8bb95bff015dc8f9d11d648c255f7e3d02567'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def check():
    assert sha((A/'source-manifest.json').read_bytes())==PIN
    assert sha((A/'report.md').read_bytes())=='86644a7451273a1d0acc8523404e37268247cb061688a323bb4cfb9627e4a180'
    manifest=json.loads((A/'source-manifest.json').read_text(encoding='utf-8-sig'))
    for name,want in manifest.items():
        for path in (P/name,A/'frozen'/name):
            raw=path.read_bytes();assert {'size':len(raw),'sha256':sha(raw)}==want,str(path)
    assert sha((P/'competition/deepeye/simulation/isolation/resource_cleanup.py').read_bytes())=='4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f'
    assert sha((O.parent/'isolation-launcher-native/run_native.py').read_bytes())=='2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613'
    assert not (O.parent/'isolation-launcher-native/native-execution-gate.json').exists()
    req=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())['requirements']
    assert sha(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    return manifest

mode=sys.argv[1];manifest=check()
if mode=='baseline':
    completion=json.loads((A/'native_completion.json').read_bytes())
    assert completion['job_id']=='child-a2db60ebe47f4c1c9bd1be8cd4c44fc6'
    assert completion['status']=='completed' and completion['terminal'] is True and completion['duplicate'] is False
    previous=json.loads((OLD/'tested-source-manifest.json').read_text(encoding='utf-8-sig'))
    changed=[];diff=[]
    for name,want in manifest.items():
        data=(P/name).read_bytes();dest=O/'frozen'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        old=(OLD/'frozen'/name).read_bytes();assert sha(old)==previous[name]['sha256']
        if data!=old:changed.append(name)
        diff.extend(difflib.unified_diff(old.decode().splitlines(True),data.decode().splitlines(True),fromfile='original/'+name,tofile='repaired/'+name))
    assert len(changed)==4
    (O/'independent-candidate.diff').write_text(''.join(diff),encoding='utf8')
    staged={}
    for src,dest in ((OLD/'test_pair_acquisition.py','test_pair_acquisition.unchanged.py'),
                     (OLD/'test_independent_boundaries.py','test_independent_boundaries.unchanged.py'),
                     (A/'unit_suite.py','unit_suite.unchanged.py')):
        raw=src.read_bytes();(O/dest).write_bytes(raw);staged[dest]={'source':str(src),'sha256':sha(raw)}
    save('product-before.json',{'source_manifest_sha256':PIN,'files':manifest,'changed':changed,'staged':staged,
        'coordinator_sha256':'4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f',
        'author_terminal_sha256':sha((A/'native_completion.json').read_bytes())})
    print('Matched 12 current/frozen sources; exactly4 changed; original witnesses copied unchanged.')
elif mode=='after':
    before=json.loads((O/'product-before.json').read_bytes());assert manifest==before['files']
    for name,record in before['staged'].items():assert sha((O/name).read_bytes())==record['sha256']
    for name,record in manifest.items():assert sha((O/'frozen'/name).read_bytes())==record['sha256']
    save('product-after.json',{'files':manifest,'source_manifest_sha256':PIN,'product_unchanged_during_review':True,
        'staged_witnesses_unchanged':True,'harness_sha256':'2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613'})
    print('Final candidate, harness and witnesses byte-stable.')
else:
    scripts={'offline':'unit_suite.unchanged.py','original-witness':'test_pair_acquisition.unchanged.py',
             'original-boundaries':'test_independent_boundaries.unchanged.py','independent-pairs':'test_pair_helpers_independent.py'}
    temp=O/'temp';temp.mkdir(exist_ok=True)
    env=dict(os.environ);env.update(TEMP=str(temp),TMP=str(temp),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(B)+os.pathsep+str(B/'tests/isolation'))
    env.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT',None)
    cmd=[sys.executable,'-B','-X','utf8',str(O/scripts[mode])]
    run=subprocess.run(cmd,cwd=B,env=env,capture_output=True,timeout=45)
    (O/(mode+'.stdout.bin')).write_bytes(run.stdout);(O/(mode+'.stderr.bin')).write_bytes(run.stderr)
    save(mode+'.command.json',{'command':cmd,'cwd':str(B),'exit_code':run.returncode,'TEMP':env['TEMP'],'TMP':env['TMP'],
        'PYTHONPATH':env['PYTHONPATH'],'native_opt_in':'unset','source_manifest_sha256':PIN})
    print(run.stderr.decode('utf8','replace'));print('EXIT',run.returncode);sys.exit(run.returncode)
