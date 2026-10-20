import pathlib, json, hashlib, shutil, subprocess, os, sys
from datetime import datetime, timezone
OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
SIM = PRODUCT / 'competition/deepeye/simulator'
REVIEW = ROOT / '.planning/deepeye-resume-20261018/g02-ui-fit-independent-20261020'
ENGINE = ROOT / '.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
OWNED = ['ui/shell.gd', 'tests/test_g02_ui_fit.gd']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sources(base): return {p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}
def setup():
    scopes={}
    for label, base in [('root', ROOT), ('product', PRODUCT)]:
        obj=read(base/'docs/competition/deepeye-2026/immutable_scope.json')
        h=hashlib.sha256(json.dumps(obj['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        assert h==PIN and [r['id'] for r in obj['requirements']]==['H%02d'%n for n in range(1,16)]
        scopes[label]=h
    transfer=read(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
    assert transfer['status']=='active' and transfer['director_generation']==2
    assert transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    expected={'ui/shell.gd':'35ba00bb15690419efe1c82398a4ea2fc64e19b46bafbf876480d0166980a004','tests/test_g02_ui_fit.gd':'2df86d207e6483fe633f855133d0c9465527caa51ceecb8a22345225999f400e','project.godot':'f713d8279b16a9710cc9a2a892a54c620a64dbeb36179fa4ac4cd3c7651d26f2'}
    for p,h in expected.items(): assert sha(SIM/p)==h,(p,sha(SIM/p))
    assert sha(ENGINE)=='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
    assert sha(REVIEW/'findings.md')=='cc0467ddaa950eed8c5ee815ed678d1a561ba2e648228e78fe49702ec099c5af'
    manifest=sources(SIM)
    for target in ['baseline','stage']:
        base=OUT/target; assert not base.exists()
        for rel in manifest:
            dest=base/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(SIM/rel,dest)
    shutil.copytree(PRODUCT/'competition/deepeye/docs', OUT/'docs')
    probe=REVIEW/'stage/tests/review_boundary.gd'
    shutil.copyfile(probe,OUT/'independent-boundary-original.gd')
    shutil.copyfile(probe,OUT/'stage/tests/review_boundary.gd')
    write(OUT/'audit-before.json',{'scopes':scopes,'transfer_status':transfer['status'],'source_manifest':manifest,'engine_sha256':sha(ENGINE),'independent_probe_sha256':sha(probe)})
    print(json.dumps({'sources':len(manifest),'scope_hashes':scopes,'starting_hashes':expected,'independent_probe_sha256':sha(probe)}))
def sync():
    for rel in OWNED: shutil.copyfile(SIM/rel,OUT/'stage'/rel)
    before=read(OUT/'audit-before.json')['source_manifest']
    current=sources(SIM)
    assert all(current[p]==h for p,h in before.items() if p not in OWNED)
    assert set(current)==set(before)
    assert sha(OUT/'stage/tests/review_boundary.gd')==sha(OUT/'independent-boundary-original.gd')
def run(label,args):
    stage=OUT/'stage'; log=OUT/'logs'/label; log.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); overrides={}
    for k,f in [('APPDATA','user'),('LOCALAPPDATA','user'),('XDG_DATA_HOME','user'),('XDG_CACHE_HOME','cache'),('TEMP','temp'),('TMP','temp')]:
        p=OUT/f; p.mkdir(exist_ok=True); overrides[k]=str(p)
    env.update(overrides)
    pins=sources(stage); product_before=sources(SIM)
    argv=[str(ENGINE),'--headless','--path',str(stage),*args,'--log-file',str(log/'engine.log')]
    cmd={'argv':argv,'cwd':str(stage),'env_overrides':overrides,'engine_sha256':sha(ENGINE),'source_before_sha256':pins,'product_before_sha256':product_before,'started_utc':datetime.now(timezone.utc).isoformat()}
    write(log/'command.json',cmd)
    with (log/'stdout.bin').open('wb') as stdout,(log/'stderr.bin').open('wb') as stderr:
        process=subprocess.Popen(argv,cwd=stage,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        timeout=False
        try: code=process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            timeout=True; process.kill(); code=process.wait(timeout=10)
    after=sources(stage); product_after=sources(SIM)
    result={**cmd,'pid':process.pid,'exit_code':code,'timed_out':timeout,'terminated':process.poll() is not None,'source_after_sha256':after,'product_after_sha256':product_after,'source_unchanged':pins==after,'product_unchanged':product_before==product_after,'finished_utc':datetime.now(timezone.utc).isoformat()}
    write(log/'result.json',result); (log/'exit_code.txt').write_text(str(code)+'\n')
    print(json.dumps({'label':label,'exit_code':code,'timed_out':timeout,'terminated':result['terminated'],'source_unchanged':pins==after,'product_unchanged':product_before==product_after}))
    print((log/'stdout.bin').read_text(encoding='utf-8',errors='replace'))
    print((log/'stderr.bin').read_text(encoding='utf-8',errors='replace'))
    assert not timeout and result['terminated'] and pins==after and product_before==product_after
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='setup': setup()
    elif mode=='sync': sync()
    elif mode=='run': run(sys.argv[2],sys.argv[3:])
