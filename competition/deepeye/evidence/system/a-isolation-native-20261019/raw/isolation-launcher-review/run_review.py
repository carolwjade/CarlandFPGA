import json,os,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a/competition/deepeye'
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(P)+os.pathsep+str(P/'tests/isolation')
env['TEMP']=env['TMP']=str(O/'temp');Path(env['TEMP']).mkdir(exist_ok=True)
env.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT',None)
runs=[]
for label,file,expected in [('author-offline',O/'author_unit_suite.py',0),('pair-acquisition-counterexample',O/'test_pair_acquisition.py',1)]:
 cmd=[sys.executable,'-B','-X','utf8',str(file)]
 result=subprocess.run(cmd,cwd=P,env=env,capture_output=True,timeout=60)
 (O/(label+'.stdout.log')).write_bytes(result.stdout);(O/(label+'.stderr.log')).write_bytes(result.stderr)
 runs.append({'label':label,'argv':cmd,'cwd':str(P),'exit_code':result.returncode,'expected_exit_code':expected})
 (O/'commands.json').write_text(json.dumps({'runs':runs,'environment':{'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1','DEEPEYE_ISOLATION_EVIDENCE_PARENT':'unset'}},indent=2),encoding='utf-8')
 print(label,result.returncode,flush=True)
 if result.returncode!=expected:print(result.stderr.decode('utf-8','replace'),flush=True)
sys.exit(0 if all(x['exit_code']==x['expected_exit_code'] for x in runs) else 1)
