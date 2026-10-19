import datetime,hashlib,json,os,subprocess
from pathlib import Path
E=Path(__file__).resolve().parent
record=json.loads((E/'preflight-started.json').read_bytes())
engine=Path(record['command'][0]);assert hashlib.sha256(engine.read_bytes()).hexdigest()==record['engine_sha256']
for rel,row in record['source_manifest'].items():assert hashlib.sha256((E/'candidate'/rel).read_bytes()).hexdigest()==row['sha256']
env=os.environ.copy();env.update(record['private_environment'])
cmd=[str(engine),'--path',str(E/'candidate/simulator'),'--windowed','--resolution','1280x720','--position','80,80']
with (E/'gui-started.json').open('x',encoding='utf-8') as f:json.dump(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=cmd,work_id='A-G02-NATIVE-UI-20261020-v1',watchdog_seconds=900),f,indent=2)
with (E/'gui.stdout.log').open('xb') as out,(E/'gui.stderr.log').open('xb') as err:
    process=subprocess.Popen(cmd,cwd=E/'candidate/simulator',env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    with (E/'gui-process.json').open('x',encoding='utf-8') as f:json.dump(dict(pid=process.pid,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=cmd),f,indent=2)
    print(json.dumps({'original_gui_pid':process.pid}),flush=True)
    reason='original process exit'
    try:code=process.wait(timeout=900)
    except subprocess.TimeoutExpired:
        reason='bounded review watchdog expired; original owned Popen terminated'
        process.terminate();code=process.wait(timeout=30)
    with (E/'gui-exit.json').open('x',encoding='utf-8') as f:json.dump(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=process.pid,exit_code=code,reason=reason),f,indent=2)
    print(json.dumps({'original_gui_exit':code,'reason':reason}),flush=True)
