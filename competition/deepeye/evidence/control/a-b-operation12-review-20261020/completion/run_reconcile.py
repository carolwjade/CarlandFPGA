"""Capture the new evidence reconciliation command in its owned directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

own=Path(__file__).resolve().parent
out=own/'audit-attempt-02'
out.mkdir(exist_ok=False)
temp=own/'temp'; temp.mkdir(exist_ok=True)
argv=[sys.executable,'-B','-X','utf8',str(own/'reconcile.py')]
env={**os.environ,'TEMP':str(temp),'TMP':str(temp),'PYTHONDONTWRITEBYTECODE':'1'}
started=datetime.now(timezone.utc).isoformat()
p=subprocess.run(argv,cwd=own.parents[2],env=env,capture_output=True,timeout=180)
finished=datetime.now(timezone.utc).isoformat()
for stream,data in [('stdout',p.stdout),('stderr',p.stderr)]: (out/(stream+'.bin')).write_bytes(data)
record={'argv':argv,'cwd':str(own.parents[2]),'exit_code':p.returncode,'started_utc':started,'finished_utc':finished,'environment':{k:env[k] for k in ['TEMP','TMP','PYTHONDONTWRITEBYTECODE']},'stdout':{'bytes':len(p.stdout),'sha256':hashlib.sha256(p.stdout).hexdigest()},'stderr':{'bytes':len(p.stderr),'sha256':hashlib.sha256(p.stderr).hexdigest()}}
(out/'command.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
print(p.stdout.decode('utf-8'));print(p.stderr.decode('utf-8'),file=sys.stderr)
sys.exit(p.returncode)
