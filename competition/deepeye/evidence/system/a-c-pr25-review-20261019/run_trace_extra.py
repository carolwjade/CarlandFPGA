import json,os,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
P=OUT/'scratch/competition/deepeye'
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=env['TMP']=str(OUT/'temp')
cmd=[sys.executable,'-B','-X','utf8',str(OUT/'independent_trace.py'),str(P)]
r=subprocess.run(cmd,cwd=OUT,env=env,capture_output=True,timeout=30)
(OUT/'trace-A-independent.stdout.log').write_bytes(r.stdout);(OUT/'trace-A-independent.stderr.log').write_bytes(r.stderr)
(OUT/'trace-extra-command.json').write_text(json.dumps({'argv':cmd,'cwd':str(OUT),'exit_code':r.returncode,'environment_overrides':{'TEMP':env['TEMP'],'TMP':env['TMP'],'PYTHONDONTWRITEBYTECODE':'1'}},indent=2),encoding='utf-8')
print(r.stderr.decode('utf-8','replace'));sys.exit(r.returncode)
