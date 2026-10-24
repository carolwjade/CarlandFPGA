import datetime,json,os,pathlib,subprocess,sys
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
label=sys.argv[1];assert label.replace('-','').isalnum()
assert not (H/(label+'.json')).exists()
env=os.environ.copy();env['PYTHONPATH']=str(P)+os.pathsep+str(ROOT/'.local/deepeye-host-deps')
env['PYTHONDONTWRITEBYTECODE']='1';(H/'temporary').mkdir(exist_ok=True)
env['TEMP']=env['TMP']=str(H/'temporary')
argv=[sys.executable,'-B','-X','utf8','-m','unittest','competition.deepeye.tests.isolation.test_actor_windows_live','-v']
start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(argv,cwd=P,env=env,capture_output=True)
(H/(label+'.stdout.txt')).write_bytes(r.stdout);(H/(label+'.stderr.txt')).write_bytes(r.stderr)
out={'argv':argv,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode}
(H/(label+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(r.stderr.decode('utf-8'));print(json.dumps(out,ensure_ascii=False))
