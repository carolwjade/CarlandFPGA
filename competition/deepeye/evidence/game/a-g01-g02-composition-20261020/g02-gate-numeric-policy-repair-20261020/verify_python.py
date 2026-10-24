from pathlib import Path
import json,os,subprocess,sys,hashlib,time
H=Path(__file__).resolve().parent;O=H/'raw/python-independent-oracles';O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
argv=[sys.executable,'-B','-X','utf8',str(H/'analyze.py')]
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
rec={'argv':argv,'cwd':str(H),'executable_sha256':sha(Path(sys.executable)),'timeout_seconds':50,'source_sha256':{n:sha(H/n) for n in ['prepare.py','analyze.py','cases.json','reader_cases.py','reader_cases.json','oracle/gate_geometry.py']}}
start=time.monotonic()
with (O/'stdout.txt').open('wb') as so,(O/'stderr.txt').open('wb') as se:
 p=subprocess.Popen(argv,cwd=H,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=p.pid
 try:rec.update(exit_code=p.wait(timeout=50),timed_out=False)
 except subprocess.TimeoutExpired:p.kill();rec.update(exit_code=p.wait(timeout=5),timed_out=True)
rec.update(terminal=p.poll() is not None,elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(O/'stdout.txt'),stderr_sha256=sha(O/'stderr.txt'))
(O/'result.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps(rec));print((O/'stdout.txt').read_text(encoding='utf-8'));print((O/'stderr.txt').read_text(encoding='utf-8'))
assert rec['exit_code']==0 and rec['terminal'] and not rec['timed_out']
