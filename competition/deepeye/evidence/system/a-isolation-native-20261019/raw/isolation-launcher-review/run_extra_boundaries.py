import json,os,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a/competition/deepeye'
env=dict(os.environ);env['PYTHONPATH']=str(P)+os.pathsep+str(P/'tests/isolation');env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=env['TMP']=str(O/'temp');env.pop('DEEPEYE_ISOLATION_EVIDENCE_PARENT',None)
cmd=[sys.executable,'-B','-X','utf8',str(O/'test_independent_boundaries.py')]
r=subprocess.run(cmd,cwd=P,env=env,capture_output=True,timeout=30)
(O/'independent-boundaries-final.stdout.log').write_bytes(r.stdout);(O/'independent-boundaries-final.stderr.log').write_bytes(r.stderr)
(O/'extra-command-final.json').write_text(json.dumps({'argv':cmd,'cwd':str(P),'exit_code':r.returncode,'native_opt_in':'unset','TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONPATH':env['PYTHONPATH']},indent=2),encoding='utf-8')
print(r.stderr.decode('utf-8','replace'));sys.exit(r.returncode)
