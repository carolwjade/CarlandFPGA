import datetime,json,os,pathlib,subprocess,sys
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
env=dict(os.environ);env['PYTHONPATH']=str(P)+os.pathsep+str(ROOT/'.local/deepeye-host-deps')+os.pathsep+str(H);env['PYTHONDONTWRITEBYTECODE']='1'
tmp=H/'temporary';tmp.mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(tmp)
label=sys.argv[1]
mods=['competition.deepeye.tests.simulation.test_actor_owner','competition.deepeye.tests.simulation.test_actor_lifetime','competition.deepeye.tests.simulation.test_pc_direct_runtime'] if label=='author116' else ['independent_actor_tests']
argv=[str(ROOT/'.local/venv/Scripts/python.exe'),'-B','-X','utf8','-m','unittest',*mods,'-v']
assert not (H/(label+'.result.json')).exists(),'preserve existing test result'
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=P,env=env,capture_output=True,timeout=120)
(H/(label+'.stdout.txt')).write_bytes(r.stdout);(H/(label+'.stderr.txt')).write_bytes(r.stderr)
result={'argv':argv,'cwd':str(P),'environment_overrides':{k:env[k] for k in ['PYTHONPATH','PYTHONDONTWRITEBYTECODE','TEMP','TMP']},'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode}
(H/(label+'.result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2));print(r.stderr.decode('utf-8',errors='replace')[-6000:])
