import pathlib, json, hashlib, shutil, difflib, subprocess, os, sys
from datetime import datetime, timezone
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
SIM=PRODUCT/'competition/deepeye/simulator'
AUTHOR=ROOT/'.planning/deepeye-resume-20261018/g02-ui-fit-continuation-20261020'
OLD=ROOT/'.planning/deepeye-resume-20261018/g02-ui-fit-implementation-20261020/evidence'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sources(): return {p.relative_to(SIM).as_posix():sha(p) for p in SIM.rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}
def audit():
    scopes={}
    for label,base in [('root',ROOT),('product',PRODUCT)]:
        scope=read(base/'docs/competition/deepeye-2026/immutable_scope.json')
        h=hashlib.sha256(json.dumps(scope['requirements'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        assert h==PIN and [r['id'] for r in scope['requirements']]==['H%02d'%n for n in range(1,16)]
        scopes[label]=h
    transfer=read(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
    assert transfer['status']=='active' and transfer['director_generation']==2
    assert transfer['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    manifest=read(AUTHOR/'manifest.json'); entries=manifest['artifact_files']
    verification=[]
    for e in entries:
        p=ROOT/e['path']; actual={'path':e['path'],'bytes':p.stat().st_size,'sha256':sha(p)}
        actual['match']=actual['bytes']==e['bytes'] and actual['sha256']==e['sha256']; verification.append(actual)
    assert all(e['match'] for e in verification)
    receipt=read(AUTHOR/'receipt.json')
    for e in receipt['candidate_files'].values(): assert sha(ROOT/e['path'])==e['sha256']
    selection=read(ROOT/'.planning/deepeye-resume-20261018/g02-ui-fit-main-selection/decision.json')
    dependencies={}
    for rel,h in selection['source_files'].items():
        actual=sha(PRODUCT/rel); dependencies[rel]={'baseline':h,'candidate':actual}
        if rel.endswith(('project.godot','ui/shell.gd')):
            local=pathlib.Path(rel).relative_to('competition/deepeye/simulator')
            before=OLD/'stage-red'/local; assert sha(before)==h
            target=OUT/'baseline'/local; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(before,target)
            diff=''.join(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(True),(SIM/local).read_text(encoding='utf-8').splitlines(True),fromfile='b45bee84/'+str(local),tofile='candidate/'+str(local)))
            (OUT/(local.name+'.diff')).write_text(diff,encoding='utf-8')
        else: assert actual==h
    runs={}
    for label in ['focused','editor696','persistence618','scene-smoke','red-focused']:
        r=read(AUTHOR/'logs'/label/'result.json'); command=read(AUTHOR/'logs'/label/'command.json')
        runs[label]={'exit_code':r['exit_code'],'timed_out':r['timed_out'],'terminated':r['terminated'],
            'command_has_source_before':'source_before_sha256' in command,'result_has_source_before':'source_before_sha256' in r,'result_has_source_after':'source_after_sha256' in r}
    record={'requirements_sha256':scopes,'author_artifacts':verification,'author_count':len(entries),'author_runs':runs,'dependencies':dependencies,'source_manifest':sources(),'engine_sha256':sha(ENGINE),'author_manifest_sha256':sha(AUTHOR/'manifest.json')}
    assert record['engine_sha256']=='ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
    stage=OUT/'stage'; assert not stage.exists()
    for rel in record['source_manifest']:
        p=stage/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SIM/rel,p)
    shutil.copytree(PRODUCT/'competition/deepeye/docs',OUT/'docs')
    write(OUT/'audit-before.json',record)
    print(json.dumps({'author_entries':len(entries),'all_match':True,'source_count':len(record['source_manifest']),'author_runs':runs},indent=2))
def run(label,args):
    stage=OUT/'stage'; log=OUT/'logs'/label;log.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); overrides={}
    for k,f in [('APPDATA','user'),('LOCALAPPDATA','user'),('XDG_DATA_HOME','user'),('XDG_CACHE_HOME','cache'),('TEMP','temp'),('TMP','temp')]:
        p=OUT/f;p.mkdir(exist_ok=True);overrides[k]=str(p)
    env.update(overrides)
    pins={r:sha(stage/r) for r in read(OUT/'audit-before.json')['source_manifest']}
    argv=[str(ENGINE),'--headless','--path',str(stage),*args,'--log-file',str(log/'engine.log')]
    cmd={'argv':argv,'cwd':str(stage),'env_overrides':overrides,'engine_sha256':sha(ENGINE),'source_before_sha256':pins,'review_probe_sha256':sha(stage/'tests/review_boundary.gd') if (stage/'tests/review_boundary.gd').exists() else None,'started_utc':datetime.now(timezone.utc).isoformat()}
    write(log/'command.json',cmd)
    with (log/'stdout.bin').open('wb') as stdout,(log/'stderr.bin').open('wb') as stderr:
        p=subprocess.Popen(argv,cwd=stage,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        timeout=False
        try: code=p.wait(timeout=45)
        except subprocess.TimeoutExpired: timeout=True;p.kill();code=p.wait(timeout=10)
    after={r:sha(stage/r) for r in pins}
    result={**cmd,'pid':p.pid,'exit_code':code,'timed_out':timeout,'terminated':p.poll() is not None,'source_after_sha256':after,'source_unchanged':pins==after,'finished_utc':datetime.now(timezone.utc).isoformat()}
    write(log/'result.json',result);(log/'exit_code.txt').write_text(str(code)+'\n')
    print(json.dumps({'label':label,'exit_code':code,'timed_out':timeout,'terminated':result['terminated'],'source_unchanged':pins==after}))
    print((log/'stdout.bin').read_text(encoding='utf-8',errors='replace'))
    print((log/'stderr.bin').read_text(encoding='utf-8',errors='replace'))
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='audit':audit()
    elif mode=='import':run('import',['--editor','--quit'])
    elif mode=='focus':run('focused',['--script','res://tests/test_g02_ui_fit.gd'])
    elif mode=='boundary':run('boundary',['--script','res://tests/review_boundary.gd'])
    elif mode=='editor':run('editor696',['--script','res://tests/test_editor_document.gd'])
    elif mode=='after':
        before=read(OUT/'audit-before.json')['source_manifest'];after=sources();write(OUT/'audit-after.json',{'source_manifest':after,'product_unchanged':before==after});assert before==after
