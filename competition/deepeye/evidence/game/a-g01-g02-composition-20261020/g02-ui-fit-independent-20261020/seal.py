import pathlib,json,hashlib,sys,shutil
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[2]
AUTHOR=ROOT/'.planning/deepeye-resume-20261018/g02-ui-fit-continuation-20261020'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def entry(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
assert read(OUT/'audit-after.json')['product_unchanged']
author_pins=read(AUTHOR/'audit-stage.json')['simulator_source_manifest']
source=read(OUT/'audit-before.json')['source_manifest']
assert source==author_pins
preserved=[]
for e in read(AUTHOR/'preserved-log-index.json'):
    p=ROOT/e['path'];assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes'];preserved.append(e)
write(OUT/'preserved-prior-logs-verified.json',preserved)
for label in ['editor696','persistence618','scene-smoke']:
    r=read(AUTHOR/'logs'/label/'result.json')
    assert r['source_before_sha256']==source and r['source_after_sha256']==source
    assert r['exit_code']==0 and r['terminated'] and not r['timed_out']
shutil.copyfile(OUT/'stage/.godot/global_script_class_cache.cfg',OUT/'import-origins.cfg')
cache=(OUT/'import-origins.cfg').read_text(encoding='utf-8')
for rel in ['viewer/main.gd','ui/shell.gd','editor/scene_document.gd','editor/layout_codec.gd','editor/layout_store.gd']:
    assert 'res://'+rel in cache
processes={}
for label,exit_code in [('import',0),('focused',0),('editor696',0),('boundary',1)]:
    r=read(OUT/'logs'/label/'result.json')
    assert r['exit_code']==exit_code and r['terminated'] and not r['timed_out'] and r['source_unchanged']
    assert r['source_before_sha256']==source and r['source_after_sha256']==source
    processes[label]={k:r[k] for k in ['pid','exit_code','timed_out','terminated','started_utc','finished_utc']}
write(OUT/'process-termination.json',processes)
toolchain={'python':{'path':sys.executable,'sha256':sha(pathlib.Path(sys.executable))},'review_runner':entry(OUT/'review.py'),'baseline_head_from_ref':(ROOT/'.git/refs/heads/codex/a/deepeye-implementation-20261014').read_text().strip(),'reused_author_dependency_pins_match':True,'verified_original_log_entries':len(preserved)}
write(OUT/'supplemental-audit.json',toolchain)
cards=read(AUTHOR/'receipt.json')['formal_acceptance'];assert len(cards)==29 and set(cards.values())=={'not_run'}
exclude={'lease.private.json','manifest.json','receipt.json','native-result.txt','native-complete.json','seal-check.json','final-hashes.json'}
files=[]
for p in sorted(OUT.rglob('*')):
    if not p.is_file() or p.name in exclude:continue
    rel=p.relative_to(OUT)
    if any(part in {'.godot','user','cache','temp','__pycache__'} for part in rel.parts):continue
    files.append(entry(p))
manifest={'schema':1,'job_id':'child-11b147871bb64f319d60edc419256d62','work_id':'A-G02-UI-FIT-INDEPENDENT-20261020-v1','agent_id':'/root/g02_ui_fit_review_20261020','task_id':'DEEPEYE-IMPLEMENTATION-20261014','task_version':1,'contract_id':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','status':'bounded_independent_review_completed_with_findings','findings':{'blocker':0,'high':0,'medium':1,'low':1},'formal_acceptance':cards,'artifact_files':files,'exclusions':sorted(exclude),'generated_runtime_cache_excluded':True,'product_source_unchanged':True}
write(OUT/'manifest.json',manifest)
result='Independent G02 UI-fit review completed with findings; main owns acceptance. Fresh focused 180/0 exit 0; editor 696/0 exit 0; import exit 0. Independent boundary 15/1 exit 1: direct-helper 512-character Chinese failure reason expands bottom band and reduces 1080p central area to 57.702546%; ordinary file-operation reachability not established. No blocker/high established; medium layout-boundary finding and low author focused/RED provenance gap. All 101 author artifacts verified; all 17 product sources unchanged. H01-H15 canonical hash preserved; all 29 formal cards remain not_run. No native GUI, board, product Run, service/install/Git mutation, messaging or delegation.\nEvidence='+OUT.relative_to(ROOT).as_posix()+'/\nmanifest_sha256='+sha(OUT/'manifest.json')+'\nfindings_sha256='+sha(OUT/'findings.md')+'\nboundary_result_sha256='+sha(OUT/'logs/boundary/result.json')+'\n'
(OUT/'native-result.txt').write_text(result,encoding='utf-8')
receipt={'schema':1,'job_id':manifest['job_id'],'status':manifest['status'],'manifest':entry(OUT/'manifest.json'),'findings':entry(OUT/'findings.md'),'native_result':entry(OUT/'native-result.txt'),'boundary_result':entry(OUT/'logs/boundary/result.json'),'formal_acceptance':cards,'native_completion_receipt':'native-complete.json (persisted after controller completion)'}
write(OUT/'receipt.json',receipt)
assert all(sha(ROOT/e['path'])==e['sha256'] and (ROOT/e['path']).stat().st_size==e['bytes'] for e in files)
write(OUT/'seal-check.json',{'verified':True,'entries':len(files),'manifest':entry(OUT/'manifest.json'),'receipt':entry(OUT/'receipt.json')})
print(json.dumps({'entries':len(files),'verified':True,'manifest':entry(OUT/'manifest.json'),'receipt':entry(OUT/'receipt.json'),'findings':entry(OUT/'findings.md'),'boundary_result':entry(OUT/'logs/boundary/result.json')},indent=2))
