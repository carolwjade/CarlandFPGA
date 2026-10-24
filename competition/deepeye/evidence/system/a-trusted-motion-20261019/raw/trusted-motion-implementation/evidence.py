from pathlib import Path
import hashlib,json,os,subprocess,sys
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'
prior=json.loads((OUT.parent/'trusted-motion-design/dependency_manifest.json').read_text(encoding='utf8'))
NAMES=list(json.loads((OUT.parent/'trusted-motion-design/source_before.json').read_text(encoding='utf8')))
OWNED=['competition/deepeye/simulation/authority/motion_executor.py','competition/deepeye/simulation/authority/motion/passage_phase.py','competition/deepeye/tests/simulation/test_motion_executor.py','competition/deepeye/docs/motion_executor.md']
NAMES=sorted(set(NAMES+OWNED+['docs/superpowers/specs/2026-10-19-trusted-motion-executor-design.md']))
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def snapshot(label):
    d={p:hashlib.sha256((PRODUCT/p).read_bytes()).hexdigest() if (PRODUCT/p).exists() else None for p in NAMES}
    save(label+'.json',d)
    req=json.loads((PRODUCT/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())['requirements']
    h=hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert h=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    p=subprocess.run(['git','-C',str(PRODUCT),'rev-parse','HEAD'],capture_output=True)
    save(label+'-metadata.json',{'head':p.stdout.decode().strip(),'head_exit':p.returncode,'requirements_hash':h})
    return d
if sys.argv[1]=='snapshot':snapshot(sys.argv[2])
else:
    label=sys.argv[1];cmd=[sys.executable,'-B','-X','utf8','-m','unittest','-v',*sys.argv[2:]]
    env=os.environ.copy();env['PYTHONPATH']=str(PRODUCT)+os.pathsep+str(ROOT/'.local/deepeye-host-deps');env['PYTHONDONTWRITEBYTECODE']='1'
    p=subprocess.run(cmd,cwd=PRODUCT,env=env,capture_output=True)
    (OUT/(label+'.stdout.log')).write_bytes(p.stdout);(OUT/(label+'.stderr.log')).write_bytes(p.stderr)
    save(label+'.command.json',{'command':cmd,'cwd':str(PRODUCT),'PYTHONPATH':env['PYTHONPATH'],'exit_code':p.returncode})
    print(p.stderr.decode('utf8','replace'));print('EXIT',p.returncode)
    sys.exit(p.returncode)
