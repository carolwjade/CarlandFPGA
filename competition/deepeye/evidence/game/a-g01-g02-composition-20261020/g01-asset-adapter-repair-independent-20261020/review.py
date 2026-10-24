import datetime, difflib, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time
E=pathlib.Path(__file__).resolve().parent
ROOT=E.parents[2]
REPAIR=E.parent/'g01-asset-adapter-repair-20261020'
OLD=E.parent/'g01-asset-adapter-independent-20261020'
SOURCE=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(n,v): (E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def manifest(p): return [dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(p.rglob('*')) if f.is_file() and '.godot' not in f.parts]
def prepare():
    scope=read(ROOT/'docs/competition/deepeye-2026/immutable_scope.json')
    pin=hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    transfer=read(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
    assert transfer['status']=='active' and transfer['director_generation']==2 and transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    assert sha(ENGINE)==PIN
    assert sha(REPAIR/'repair-receipt.json')=='9056113536888d0e24ce92aa9015e0019cb7016cd00ef770bbae78a00b5155e2'
    source=manifest(SOURCE)
    assert source==read(REPAIR/'source-after.json')['source_manifest']
    terminal=read(REPAIR/'native-complete-response.json')
    assert terminal['terminal'] and terminal['status']=='completed' and terminal['result']['text']==(REPAIR/'final-result.txt').read_text(encoding='utf-8')
    seal=read(REPAIR/'main-sealed-artifact-manifest.json')
    for row in seal['files']:
        assert 'lease.private' not in row['path']
        p=REPAIR/row['path']; assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
    diff=''
    for row in read(REPAIR/'repair-receipt.json')['changed_owned_files']:
        name=row['path']; assert sha(SOURCE/name)==row['sha256']
        diff+=''.join(difflib.unified_diff((REPAIR/'original-stage'/name).read_text(encoding='utf-8').splitlines(True),(SOURCE/name).read_text(encoding='utf-8').splitlines(True),fromfile='before/'+name,tofile='candidate/'+name))
    assert diff==(REPAIR/'repair.diff').read_text(encoding='utf-8')
    dump('source-before.json',dict(requirements_sha256=pin,engine_sha256=PIN,source_manifest=source,author_terminal=True,author_exact_result=True,sealed_files=len(seal['files']),sealed_manifest_sha256=sha(REPAIR/'main-sealed-artifact-manifest.json'),diff_exact=True))
    dest=E/'fresh-stage'; assert not dest.exists()
    shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('.godot'))
    shutil.copyfile(OLD/'test_independent.gd',dest/'tests/test_independent.gd')
    dump('fresh-stage-manifest.json',manifest(dest))
    for mode in ['bad-license','signature','empty-visual','null']:
        dest=E/('fixture-'+mode); assert not dest.exists()
        shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('.godot'))
        shutil.copyfile(OLD/'test_failure_review.gd',dest/'tests/test_failure_review.gd')
        shutil.copyfile(OLD/('fixture-'+mode)/'review-mode.txt',dest/'review-mode.txt')
        shutil.copyfile(OLD/('fixture-'+mode)/'world/asset_library.gd',dest/'world/asset_library.gd')
        # Only the original exact B factory mutation and oracle are introduced.
        for row in source:
            if row['path']!='world/asset_library.gd': assert sha(dest/row['path'])==row['sha256']
        assert sha(dest/'tests/test_failure_review.gd')==sha(OLD/'test_failure_review.gd')
        dump('fixture-'+mode+'-manifest.json',manifest(dest))
    print('Verified contract, active transfer, exact source/diff, author actual terminal and '+str(len(seal['files']))+' sealed artifacts; prepared five fresh private stages.')
def run(stage,label,script,summary):
    p=E/stage; assert p.is_relative_to(E) and p.is_dir() and sha(ENGINE)==PIN
    assert not (E/(label+'.json')).exists()
    argv=[str(ENGINE),'--headless','--path',str(p)]+(['--editor','--import'] if script=='import' else ['--script',script])
    env=os.environ.copy()
    for key in ['APPDATA','LOCALAPPDATA']:
        private=E/'user-data'/stage/key; private.mkdir(parents=True,exist_ok=True); env[key]=str(private)
    before=manifest(p); started=time.monotonic(); out=E/(label+'.stdout.txt'); err=E/(label+'.stderr.txt')
    with out.open('wb') as o,err.open('wb') as e:
        proc=subprocess.Popen(argv,cwd=p,stdout=o,stderr=e,env=env); timeout=False
        try: code=proc.wait(timeout=45)
        except subprocess.TimeoutExpired:
            timeout=True; proc.kill(); code=proc.wait(timeout=10)
    stdout=out.read_text(encoding='utf-8',errors='replace'); stderr=err.read_text(encoding='utf-8',errors='replace')
    eligible=code==0 and not timeout and (summary in stdout) and 'SCRIPT ERROR' not in stdout+stderr and 'ERROR:' not in stdout+stderr
    result=dict(argv=argv,cwd=str(p),pid=proc.pid,executable_sha256=PIN,exit_code=code,timeout=timeout,terminal=proc.poll() is not None,seconds=time.monotonic()-started,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(out),stderr_sha256=sha(err),source_manifest_before=before,source_manifest_after=manifest(p),expected_summary=summary,eligible=eligible,unicode_nul_diagnostics=(stdout+stderr).count('NUL'))
    dump(label+'.json',result)
    print(json.dumps({k:result[k] for k in ['pid','exit_code','timeout','terminal','eligible','expected_summary','unicode_nul_diagnostics']}))
    assert eligible,stderr
def reuse():
    source={r['path']:r for r in manifest(SOURCE)}; rows=[]
    jobs=[(REPAIR,'frozen-integration',136),(REPAIR,'frozen-editor',696),(REPAIR,'frozen-persistence',628),(REPAIR,'frozen-g02-ui-fit',266),(E.parent/'g01-asset-adapter-implementation-20261020','final-assets',622)]
    for folder,label,total in jobs:
        receipt=folder/(label+'.json'); r=read(receipt)
        out=folder/(label+'.stdout.txt'); err=folder/(label+'.stderr.txt')
        assert r['terminal'] and not r['timeout'] and r['exit_code']==0 and r.get('executable_sha256',r.get('engine_sha256'))==PIN
        assert sha(out)==r['stdout_sha256'] and sha(err)==r['stderr_sha256']
        text=out.read_text(encoding='utf-8'); errors=err.read_text(encoding='utf-8')
        assert f'checks={total} failures=0' in text and 'SCRIPT ERROR' not in text+errors
        if total==622:
            assert errors.count('ERROR:')==1 and "ERROR: DeepEyeObstacleGeometry: unknown obstacle kind 'bogus_kind'; valid kinds: water, hard_rock, fault, void, casing" in errors
            assert '_test_obstacle_unknown_kind (res://tests/test_asset_contract.gd:274)' in errors
        else: assert 'ERROR:' not in text+errors
        before={x['path']:x for x in r.get('source_manifest_before',r.get('source_manifest',[]))}
        after={x['path']:x for x in r.get('source_manifest_after',r.get('source_manifest',[]))}
        names=list(source) if total!=622 else [n for n in source if n.startswith(('world/','assets/')) or n in ['project.godot','tests/test_asset_contract.gd']]
        for n in names:
            assert source[n]['sha256']==before[n]['sha256']==after[n]['sha256'],(label,n)
            assert sha(pathlib.Path(r['cwd'])/n)==source[n]['sha256']
        rows.append(dict(label=label,checks=total,failures=0,argv=r['argv'],cwd=r['cwd'],pid=r['pid'],terminal=True,timeout=False,exit_code=0,receipt_sha256=sha(receipt),stdout_sha256=sha(out),stderr_sha256=sha(err),verified_dependencies=names,unicode_nul_diagnostics=(text+errors).count('NUL'),warnings=errors.count('WARNING'),eligible=True))
    dump('exact-evidence-reuse.json',rows)
    print('Verified exact executing source dependencies, argv, terminal, exit and raw logs for 136/696/628/266/622 evidence.')
def finish():
    before=read(E/'source-before.json'); current=manifest(SOURCE)
    assert before['source_manifest']==current
    assert sha(ENGINE)==PIN
    for row in read(REPAIR/'main-sealed-artifact-manifest.json')['files']:
        assert sha(REPAIR/row['path'])==row['sha256']
    old_red=[]
    for mode,failures in [('bad-license',7),('signature',3),('empty-visual',7),('null',2)]:
        label='negative-'+mode; r=read(OLD/(label+'.json'))
        assert r['terminal'] and not r['timeout'] and r['exit_code']==1
        for ext in ['stdout','stderr']: assert sha(OLD/(label+'.'+ext+'.txt'))==r[ext+'_sha256']
        assert 'failures='+str(failures) in (OLD/(label+'.stdout.txt')).read_text(encoding='utf-8')
        old_red.append(dict(label=label,failures=failures,receipt_sha256=sha(OLD/(label+'.json')),terminal=True,exit_code=1))
    dump('original-red-readback.json',old_red)
    results=[]
    for label in ['fresh-import','fresh-independent','fresh-bad-license','fresh-signature','fresh-empty-visual','fresh-null']:
        r=read(E/(label+'.json')); assert r['eligible'] and r['terminal'] and not r['timeout'] and r['exit_code']==0
        for ext in ['stdout','stderr']: assert sha(E/(label+'.'+ext+'.txt'))==r[ext+'_sha256']
        m={x['path']:x['sha256'] for x in r['source_manifest_before']}
        for row in current:
            if label.startswith('fresh-') and label not in ['fresh-import','fresh-independent'] and row['path']=='world/asset_library.gd': continue
            assert m[row['path']]==row['sha256'],(label,row['path'])
        if label=='fresh-independent': assert m['tests/test_independent.gd']==sha(OLD/'test_independent.gd')
        if label not in ['fresh-import','fresh-independent']: assert m['tests/test_failure_review.gd']==sha(OLD/'test_failure_review.gd')
        results.append({k:r[k] for k in ['expected_summary','pid','exit_code','timeout','terminal','unicode_nul_diagnostics']})
    processes=json.loads((E/'terminal-process-readback.json').read_text(encoding='utf-8-sig')); assert processes['matching_process_count']==0
    dump('source-after.json',dict(source_manifest=current,product_unchanged=True,sealed_repair_artifacts_unchanged=True,engine_sha256=PIN,requirements_sha256=before['requirements_sha256']))
    dump('independent-review-receipt.json',dict(task='DEEPEYE-IMPLEMENTATION-20261014/v1',job_id='child-754808b3064e4a158cfff208a1baaaf3',agent='/root/g01_asset_adapter_repair_independent_20261020',contract='DEEPEYE-HUMAN-LOCK-20261014/revision1',requirements_sha256=before['requirements_sha256'],source_before_sha256=sha(E/'source-before.json'),source_after_sha256=sha(E/'source-after.json'),repair_receipt_sha256=sha(REPAIR/'repair-receipt.json'),diff_exact=True,unchanged_original_oracles=True,fresh_runs=results,reuse_receipt_sha256=sha(E/'exact-evidence-reuse.json'),product_unchanged=True,sealed_repair_artifacts_unchanged=True,processes_remaining=0,new_actionable_findings=[],F1_F4='original failing oracles now pass; no new actionable defect found in bounded source review',all_29_formal_cards='not_run',native_ui='not_run',engine_clean=False,adoption_owner='sole A main'))
    print('Final integrity verified: product unchanged, original RED retained, 885 sealed artifacts unchanged, all six fresh processes terminal, zero remaining owned processes.')
def seal():
    files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ['lease.private.json','non-secret-artifact-manifest.json'] and '.godot' not in p.parts]
    dump('non-secret-artifact-manifest.json',dict(schema=1,files=files,excludes=['lease.private.json','self','generated .godot cache']))
    print('Non-secret manifest files='+str(len(files)))
if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='run': run(*sys.argv[2:])
    elif sys.argv[1]=='reuse': reuse()
    elif sys.argv[1]=='finish': finish()
    elif sys.argv[1]=='seal': seal()
