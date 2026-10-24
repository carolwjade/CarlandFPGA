import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[3]
E=pathlib.Path(__file__).resolve().parent
AUTHOR=E.parent/'g01-asset-adapter-implementation-20261020'
SOURCE=ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v): (E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def manifest(p): return [dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(p.rglob('*')) if f.is_file() and '.godot' not in f.parts]
def pins(label):
    receipt=json.loads((AUTHOR/'implementation-receipt.json').read_text(encoding='utf-8'))
    imp=json.loads((E.parent/'main-ui-and-g01-adoption-20261020/import-receipt.json').read_text(encoding='utf-8'))
    checks=[]
    for row in receipt['changed_owned_files']:
        p=SOURCE/row['path']; checks.append(dict(path=row['path'],sha256=sha(p),expected=row['sha256'],matches=sha(p)==row['sha256']))
    bchecks=[]
    for row in imp['imported_exact_files']:
        p=ROOT/'.local/deepeye-implementation-a'/row['target_project_path']; bchecks.append(dict(path=row['target_project_path'],sha256=sha(p),expected=row['source']['sha256'],matches=sha(p)==row['source']['sha256']))
    contract=json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8'))
    ch=hashlib.sha256(json.dumps(contract['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    completion=json.loads((AUTHOR/'native-complete-response.json').read_text(encoding='utf-8'))
    assert completion['terminal'] and completion['status']=='completed' and completion['native_agent_id']=='/root/g01_asset_adapter_impl_20261020'
    result=dict(candidate=checks,B=bchecks,requirements_sha256=ch,engine_sha256=sha(ENGINE),author_terminal=True,source_manifest=manifest(SOURCE),candidate_manifest_sha256=sha(AUTHOR/'source-after-manifest.json'))
    dump(label+'.json',result)
    assert all(x['matches'] for x in checks+bchecks) and ch=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804' and sha(ENGINE)==PIN
    print(json.dumps(dict(candidate_pins=len(checks),B_pins=len(bchecks),requirements_sha256=ch,author_terminal=True)))
def freeze():
    pins('source-before')
    dest=E/'frozen-stage'; assert not dest.exists()
    shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('.godot'))
    dump('frozen-stage-manifest.json',manifest(dest))
def run(stage,label,script):
    p=E/stage; assert p.is_relative_to(E) and p.is_dir() and sha(ENGINE)==PIN
    argv=[str(ENGINE),'--headless','--path',str(p)]
    argv+=['--editor','--import'] if script=='import' else ['--script',script]
    env=os.environ.copy()
    for k in ['APPDATA','LOCALAPPDATA']:
        private=E/'user-data'/stage/k; private.mkdir(parents=True,exist_ok=True); env[k]=str(private)
    before=manifest(p); started=time.monotonic(); out=E/(label+'.stdout.txt'); err=E/(label+'.stderr.txt')
    with out.open('wb') as o,err.open('wb') as e:
        proc=subprocess.Popen(argv,cwd=p,stdout=o,stderr=e,env=env)
        timeout=False
        try: code=proc.wait(timeout=45)
        except subprocess.TimeoutExpired:
            timeout=True; proc.kill(); code=proc.wait(timeout=10)
    result=dict(argv=argv,cwd=str(p),pid=proc.pid,executable_sha256=PIN,exit_code=code,timeout=timeout,terminal=proc.poll() is not None,seconds=time.monotonic()-started,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(out),stderr_sha256=sha(err),source_manifest_before=before,source_manifest_after=manifest(p))
    dump(label+'.json',result)
    print(json.dumps({k:result[k] for k in ['pid','exit_code','timeout','terminal','seconds']}))
    print(out.read_text(encoding='utf-8',errors='replace')[-10000:]); print(err.read_text(encoding='utf-8',errors='replace')[-5000:])
if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    elif sys.argv[1]=='pins': pins(sys.argv[2])
    elif sys.argv[1]=='run': run(*sys.argv[2:])
