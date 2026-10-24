import json,os,shutil,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
EXPORT=OUT/'exact-git-blobs'
SCRATCH=OUT/'scratch'
if not SCRATCH.exists():shutil.copytree(EXPORT,SCRATCH)
P=SCRATCH/'competition/deepeye';T=P/'evidence/ai/trace_candidate_decode'
assert (T/'candidate_decode.py').read_bytes()==(T/'independent_review/candidate_snapshot.py').read_bytes()
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(P)+os.pathsep+str(ROOT/'.local/deepeye-host-deps')
env['TEMP']=env['TMP']=str(OUT/'temp');Path(env['TEMP']).mkdir(exist_ok=True)
env.pop('DEEPEYE_FORCE_ARCHIVE',None)
commands=[
 ('motion-author',[str(P/'tests/ai/control_broker/test_motion_request.py')]),
 ('mailbox-author',[str(P/'tests/ai/control_broker/test_mailbox.py')]),
 ('deadlines-author',[str(P/'tests/ai/control_broker/test_deadlines.py')]),
 ('motion-C-main',[str(P/'evidence/ai/motion_request/review_repair2/main_review/independent_motion_review.py'),'--product-root',str(P)]),
 ('motion-A-independent',[str(OUT/'independent_motion.py'),str(P)]),
 ('parser-inventory',[str(P/'tests/ai/data_model/test_force_inventory.py')]),
 ('parser-preprocess',[str(P/'tests/ai/data_model/test_force_preprocess.py')]),
 ('parser-C-main',[str(P/'evidence/ai/data_boundary_repair/main_review/independent_headers.py'),'--product-root',str(P)]),
 ('verifier-pure',[str(P/'tests/ai/data_model/test_verify_data.py')]),
 ('trace-provenance',[str(T/'provenance.py'),'--check-only']),
 ('trace-replay',[str(T/'replay.py')]),
 ('trace-QA',[str(T/'independent_review/probe.py')]),
 ('trace-C-main',[str(T/'main_review/main_probe.py'),'--candidate',str(T/'candidate_decode.py')]),
]
rows=[]
for label,args in commands:
 cmd=[sys.executable,'-B','-X','utf8',*args]
 result=subprocess.run(cmd,cwd=OUT,env=env,capture_output=True,timeout=60)
 (OUT/(label+'.stdout.log')).write_bytes(result.stdout);(OUT/(label+'.stderr.log')).write_bytes(result.stderr)
 row={'label':label,'argv':cmd,'cwd':str(OUT),'exit_code':result.returncode,'stdout':label+'.stdout.log','stderr':label+'.stderr.log'};rows.append(row)
 (OUT/'commands.json').write_text(json.dumps({'environment':{'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1','DEEPEYE_FORCE_ARCHIVE':'unset'},'runs':rows},indent=2),encoding='utf-8')
 print(label,result.returncode,flush=True)
 if result.returncode:print(result.stderr.decode('utf-8','replace')[-3500:],flush=True)
print('all_complete',flush=True)
sys.exit(0 if all(r['exit_code']==0 for r in rows) else 1)
