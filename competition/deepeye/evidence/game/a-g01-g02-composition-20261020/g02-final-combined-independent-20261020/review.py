from pathlib import Path
import hashlib, json, shutil, os, subprocess, sys, datetime, time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
PSIM=PRODUCT/'competition/deepeye/simulator'
UI=HERE.parent/'g02-status-height-repair-20261020'
FACE=HERE.parent/'g02-face-matrix-adapt-20261020'
STAGE=HERE/'stage'
SIM=STAGE/'competition/deepeye/simulator'
ENGINE=ROOT/'.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64_console.exe'
PYTHON=ROOT/'.local/venv/Scripts/python.exe'
PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
EXPECTED={'ui/shell.gd':'bf61c548fec75793773606e9203666efa0acdf497ecce67535ca9d7d1255bbcc','tests/test_g02_ui_fit.gd':'2c95090dceb98518c331dbb803f1bd1bb4e9d438439b58173e2bee78aa857db4','project.godot':'f713d8279b16a9710cc9a2a892a54c620a64dbeb36179fa4ac4cd3c7651d26f2'}
FACEPINS={'test_gate_face_pairs.gd':'62233b3304d6378ccafd5ff76268322d7735fdab87ba4e84632852d1b355d49e','test_gate_face_matrix.py':'e34e8ed095e97d192dfd7c27c87c3473249b7d09a2bdd560350138eb5073e0fa'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sources(base): return {p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}
def audit_prior():
    records=[]
    for label,base,count,expected in [('ui',UI,201,'956612eee2f3659b340bcc50807e78ae16b0263aab1a377010c8c5fc4bf4f41f'),('face',FACE,87,'9db95deca604092b568454992337f752f80993eb8addb646e464aeb7498c7b48')]:
        manifest=read(base/'manifest.json'); rows=manifest.get('files',manifest.get('artifact_files'))
        assert len(rows)==count and sha(base/'manifest.json')==expected
        for row in rows:
            p=(ROOT if label=='ui' else base)/row['path']
            assert p.name!='lease.private.json'
            assert p.stat().st_size==row.get('bytes',row.get('size')) and sha(p)==row['sha256'],str(p)
        receipt=read(base/'receipt.json'); assert receipt['manifest_sha256']==expected
        complete=read(base/'native-complete-response.json')
        assert complete['terminal'] is True and complete['status']=='completed'
        assert complete['result']['text']==(base/'final-result.txt').read_text(encoding='utf-8')
        records.append({'label':label,'entries':count,'manifest_sha256':expected,'receipt_sha256':sha(base/'receipt.json'),'terminal':True,'result_exact':True})
    return records
def setup():
    dump(HERE/'initial-audit-error.json',{'command':'initial read-only metadata inspection assumed files key for both manifest formats','exit_code':1,'error':"KeyError: files",'product_writes':False,'correction':'UI uses artifact_files with root-relative paths; face uses files with evidence-relative paths'})
    prior=audit_prior(); dump(HERE/'prior-integrity-before.json',prior)
    scopes={}
    for label,base in [('root',ROOT),('product',PRODUCT)]:
        obj=read(base/'docs/competition/deepeye-2026/immutable_scope.json')
        h=hashlib.sha256(json.dumps(obj['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert h==PIN and [r['id'] for r in obj['requirements']]==['H%02d'%i for i in range(1,16)]
        scopes[label]=h
    t=read(ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json')
    assert t['status']=='active' and t['director_generation']==2 and t['new_director_thread_id']=='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
    for p,h in EXPECTED.items(): assert sha(PSIM/p)==h
    for p,h in FACEPINS.items(): assert sha(FACE/'candidate'/p)==h
    product=sources(PSIM)
    fs=read(FACE/'source_manifest.json')
    # Every effective dependency is copied from the adapted pinned stage first,
    # then all current PRODUCT simulator files replace its older UI overlay.
    for row in fs['files']:
        rel=row['path']; src=FACE/'stage'/rel
        assert sha(src)==row['effective_sha256'],rel
        dst=STAGE/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    for rel,h in product.items():
        src=PSIM/rel; dst=SIM/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        assert sha(dst)==h
    # Detect a stale non-UI dependency rather than silently adopting it.
    for row in fs['files']:
        rel=row['path']
        if '/simulator/' in rel:
            simrel=rel.split('/simulator/',1)[1]
            if simrel not in ['ui/shell.gd','tests/test_g02_ui_fit.gd']:
                assert sha(SIM/simrel)==row['effective_sha256'],rel
        elif (PRODUCT/rel).exists(): assert sha(PRODUCT/rel)==row['effective_sha256'],rel
    for name in FACEPINS:
        dst=SIM/'tests'/name if name.endswith('.gd') else STAGE/'competition/deepeye/tests/simulation'/name
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(FACE/'candidate'/name,dst)
    probe=UI/'independent-boundary-original.gd'
    assert sha(probe)=='964ad14344b9c111eb1a2ac2c00a7f5aafc6b362dd00d1f7e53f6159fa797623'
    shutil.copyfile(probe,SIM/'tests/review_boundary.gd')
    shutil.copytree(PRODUCT/'competition/deepeye/docs',STAGE/'competition/deepeye/docs')
    # Bind the executable to the already verified adaptation record.
    prev=read(FACE/'raw/godot-adapted/command.json')
    assert sha(ENGINE)==prev['executable_sha256']
    reused=[]
    for label,marker in [('editor696-candidate','696'),('persistence618-candidate','618')]:
        r=read(UI/'logs'/label/'result.json')
        assert r['exit_code']==0 and r['terminated'] and not r['timed_out'] and r['source_unchanged'] and r['product_unchanged']
        assert r['product_before_sha256']==product==r['product_after_sha256']
        for rel,h in product.items(): assert r['source_before_sha256'][rel]==h==r['source_after_sha256'][rel]
        output=(UI/'logs'/label/'stdout.bin').read_text(encoding='utf-8')
        assert marker in output and 'failures=0' in output
        reused.append({'label':label,'result_sha256':sha(UI/'logs'/label/'result.json'),'stdout_sha256':sha(UI/'logs'/label/'stdout.bin'),'exit_code':0,'source_pins_match':True,'fresh_rerun':False})
    dump(HERE/'reused-broad-regressions.json',reused)
    dump(HERE/'source-manifest.json',{'scopes':scopes,'director_generation':2,'director':t['new_director_thread_id'],'product_before':product,'stage_before':sources(STAGE),'engine_sha256':sha(ENGINE),'exact_ui_pins':EXPECTED,'face_candidate_pins':FACEPINS,'probe_sha256':sha(probe),'dependency_origin':'adapted b45 raw-object stage; simulator replaced with all final PRODUCT simulator bytes','product_head_parent_record':'6c51b2d5304dc3bf9735a304931e8001b22e7541 (evidence-only movement; source bytes are identity)'})
    print(json.dumps({'prior_entries':[201,87],'product_files':len(product),'stage_files':len(sources(STAGE)),'reused':[696,618],'engine_sha256':sha(ENGINE)}))
def run(label,args,python=False):
    out=HERE/'raw'/label; out.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); overrides={'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(STAGE)}
    for k in ['APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']:
        d=HERE/'tmp'/label/k.lower(); d.mkdir(parents=True,exist_ok=True); overrides[k]=str(d)
    env.update(overrides)
    argv=([str(PYTHON),'-B','-X','utf8'] if python else [str(ENGINE),'--headless','--path',str(SIM)])+args
    cwd=STAGE if python else SIM
    before=sources(STAGE); prod=sources(PSIM)
    record={'argv':argv,'cwd':str(cwd),'environment_overrides':overrides,'executable_sha256':sha(Path(argv[0])),'source_before':before,'product_before':prod,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':50}
    dump(out/'command.json',record)
    start=time.monotonic()
    with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
        p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid
        try: record.update(exit_code=p.wait(timeout=50),timed_out=False)
        except subprocess.TimeoutExpired:
            p.kill(); record.update(exit_code=p.wait(timeout=5),timed_out=True)
    after=sources(STAGE); pa=sources(PSIM)
    record.update(terminated=p.poll() is not None,source_after=after,product_after=pa,source_unchanged=before==after,product_unchanged=prod==pa,elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'))
    record['added_stage_files']=sorted(set(after)-set(before))
    record['changed_stage_files']=[k for k in before if k in after and before[k]!=after[k]]
    dump(out/'result.json',record)
    so=(out/'stdout.txt').read_text(encoding='utf-8',errors='replace'); se=(out/'stderr.txt').read_text(encoding='utf-8',errors='replace')
    print(json.dumps({k:record[k] for k in ['pid','exit_code','timed_out','terminated','source_unchanged','product_unchanged','added_stage_files','changed_stage_files']}))
    print('\n'.join(line for line in so.splitlines() if line.startswith(('TESTS','RESULT','BOUNDARY_','UI_FIT_STATUS','UI_FIT_TOOLTIP','EDITOR_POLICY_ROW','PY_POLICY_ROW','IMPORT_ORIGINS','EXTRA_','FAIL'))))
    print(se[-2500:])
    assert record['exit_code']==0 and record['terminated'] and not record['timed_out'] and record['product_unchanged']
    if label=='import':
        assert not record['changed_stage_files'] and all(k.endswith('.gd.uid') and (STAGE/k[:-4]).exists() for k in record['added_stage_files'])
    else: assert record['source_unchanged']
    assert not any(s in so+'\n'+se for s in ['SCRIPT ERROR','Parse Error'])
if __name__=='__main__':
    if sys.argv[1]=='setup': setup()
    elif sys.argv[1]=='run': run(sys.argv[2],sys.argv[3:])
    elif sys.argv[1]=='python': run(sys.argv[2],sys.argv[3:],True)
