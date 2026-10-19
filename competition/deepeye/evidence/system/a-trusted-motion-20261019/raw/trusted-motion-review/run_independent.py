import json,os,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'.local/deepeye-implementation-a'
env=dict(os.environ);env['PYTHONPATH']=str(P)+os.pathsep+str(R/'.local/deepeye-host-deps');env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=env['TMP']=str(O/'temp')
cmd=[sys.executable,'-B','-X','utf8',str(O/'test_independent_motion.py')]
run=subprocess.run(cmd,cwd=P,env=env,capture_output=True,timeout=60)
(O/'independent.stdout.log').write_bytes(run.stdout);(O/'independent.stderr.log').write_bytes(run.stderr)
(O/'independent-command.json').write_text(json.dumps({'argv':cmd,'cwd':str(P),'exit_code':run.returncode,'environment':{'PYTHONPATH':env['PYTHONPATH'],'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1'}},indent=2),encoding='utf-8')
print(run.stderr.decode('utf-8','replace'));sys.exit(run.returncode)
