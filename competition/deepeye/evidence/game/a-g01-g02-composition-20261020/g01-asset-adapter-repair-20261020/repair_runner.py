import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[3]
E=pathlib.Path(__file__).resolve().parent
REVIEW=E.parent/'g01-asset-adapter-independent-20261020'
SOURCE=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
OWNED=['viewer/asset_presenter.gd','viewer/main.gd','tests/test_viewer_asset_integration.gd']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v): (E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def manifest(p): return [dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(p.rglob('*')) if f.is_file() and '.godot' not in f.parts]
def contract():
    obj=json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8'))
    pin=hashlib.sha256(json.dumps(obj['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    assert pin=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    transfer=json.loads((ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json').read_text(encoding='utf-8'))
    assert transfer['status']=='active' and transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d' and transfer['director_generation']==2
    return pin
def prepare():
    assert sha(ENGINE)==PIN
    before=manifest(SOURCE); reviewed=json.loads((REVIEW/'source-after.json').read_text(encoding='utf-8'))
    assert before==reviewed['source_manifest']
    terminal=json.loads((REVIEW/'native-complete-response.json').read_text(encoding='utf-8'))
    assert terminal['terminal'] and terminal['status']=='completed'
    dump('source-before.json',dict(requirements_sha256=contract(),engine_sha256=PIN,source_manifest=before,reviewer_terminal=True))
    dest=E/'original-stage'; assert not dest.exists()
    shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('.godot'))
    rows=[]
    for mode,expected in [('bad-license',7),('signature',3),('empty-visual',7),('null',2)]:
        label='negative-'+mode; receipt=REVIEW/(label+'.json'); r=json.loads(receipt.read_text(encoding='utf-8'))
        out=REVIEW/(label+'.stdout.txt'); err=REVIEW/(label+'.stderr.txt')
        assert r['terminal'] and not r['timeout'] and r['exit_code']==1 and r['executable_sha256']==PIN
        assert r['stdout_sha256']==sha(out) and r['stderr_sha256']==sha(err)
        assert 'failures='+str(expected) in out.read_text(encoding='utf-8')
        fixture=REVIEW/('fixture-'+mode)
        for name in OWNED:
            assert sha(fixture/name)==sha(SOURCE/name)
        rows.append(dict(mode=mode,receipt_sha256=sha(receipt),stdout_sha256=sha(out),stderr_sha256=sha(err),failures=expected,original_product_pins_match=True))
    dump('original-red-reuse.json',rows)
    for f in ['test_failure_review.gd','test_independent.gd','test_independent_first_attempt.gd']:
        shutil.copyfile(REVIEW/f,E/f)
    dump('unchanged-oracles.json',[dict(path=f,sha256=sha(E/f),reviewer_sha256=sha(REVIEW/f)) for f in ['test_failure_review.gd','test_independent.gd','test_independent_first_attempt.gd']])
    print('Verified original source, requirements, reviewer terminal and all four preserved RED receipts; copied unchanged oracles.')
def stage(name):
    dest=E/name; assert not dest.exists()
    shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('.godot'))
    shutil.copyfile(E/'test_independent.gd',dest/'tests/test_independent.gd')
    dump(name+'-manifest.json',manifest(dest))
def fixtures():
    for mode in ['bad-license','signature','empty-visual','null']:
        dest=E/('fixture-'+mode); assert not dest.exists()
        shutil.copytree(REVIEW/('fixture-'+mode),dest,ignore=shutil.ignore_patterns('.godot'))
        for f in OWNED: shutil.copyfile(SOURCE/f,dest/f)
        assert sha(dest/'tests/test_failure_review.gd')==sha(E/'test_failure_review.gd')
        dump('fixture-'+mode+'-manifest.json',manifest(dest))
def run(stage,label,script):
    p=E/stage; assert p.is_relative_to(E) and p.is_dir() and sha(ENGINE)==PIN
    assert not (E/(label+'.json')).exists()
    argv=[str(ENGINE),'--headless','--path',str(p)]
    argv+=['--editor','--import'] if script=='import' else ['--script',script]
    env=os.environ.copy()
    for k in ['APPDATA','LOCALAPPDATA']:
        private=E/'user-data'/stage/k; private.mkdir(parents=True,exist_ok=True); env[k]=str(private)
    before=manifest(p); started=time.monotonic(); out=E/(label+'.stdout.txt'); err=E/(label+'.stderr.txt')
    with out.open('wb') as o,err.open('wb') as e:
        proc=subprocess.Popen(argv,cwd=p,stdout=o,stderr=e,env=env); timeout=False
        try: code=proc.wait(timeout=45)
        except subprocess.TimeoutExpired:
            timeout=True; proc.kill(); code=proc.wait(timeout=10)
    result=dict(argv=argv,cwd=str(p),pid=proc.pid,executable_sha256=PIN,exit_code=code,timeout=timeout,terminal=proc.poll() is not None,seconds=time.monotonic()-started,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(out),stderr_sha256=sha(err),source_manifest_before=before,source_manifest_after=manifest(p))
    dump(label+'.json',result)
    print(json.dumps({k:result[k] for k in ['pid','exit_code','timeout','terminal','seconds']}))
    print(out.read_text(encoding='utf-8',errors='replace')[-1800:]); print(err.read_text(encoding='utf-8',errors='replace')[-5000:])
if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='stage': stage(sys.argv[2])
    elif sys.argv[1]=='fixtures': fixtures()
    elif sys.argv[1]=='run': run(*sys.argv[2:])
