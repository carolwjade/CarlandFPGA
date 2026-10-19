import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent;ROOT=E.parents[2];P=ROOT/'.local/deepeye-implementation-a'
phase=sys.argv[1];assert phase in ('red','green');STAGE=E/(phase+'-cli-stage');STAGE.mkdir(exist_ok=False)
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
temp=E/(phase+'-cli-temp');temp.mkdir(exist_ok=False);env.update(TEMP=str(temp),TMP=str(temp))
rows=[]
for label,desired in [('weights-tamper',1),('weights-missing',1),('unchanged',0)]:
    case=STAGE/label;case.mkdir()
    for rel in ('competition/deepeye/tools/check_rules.py','competition/deepeye/docs/rules.json','competition/deepeye/docs/requirements_trace.csv','docs/competition/deepeye-2026/immutable_scope.json'):
        dest=case/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((P/rel).read_bytes())
    rp=case/'competition/deepeye/docs/rules.json';rules=json.loads(rp.read_bytes())
    if label=='weights-tamper':rules['assessment_weights'].update(fpga_quality=30,engineering_innovation=10)
    if label=='weights-missing':rules.pop('assessment_weights')
    if label!='unchanged':rp.write_text(json.dumps(rules,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cmd=[sys.executable,'-B','competition/deepeye/tools/check_rules.py','--reference-only','--source-pdf',str(ROOT/'docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf')]
    run=subprocess.run(cmd,cwd=case,env=env,capture_output=True,timeout=30)
    for suffix,data in [('stdout.json',run.stdout),('stderr.log',run.stderr)]:
        with (E/(phase+'-'+label+'.'+suffix)).open('xb') as f:f.write(data)
    result=json.loads(run.stdout);assert result['R01']=='not_run' and result['formal_acceptance'] is False and result['hardware_enable_eligible'] is False
    rows.append(dict(label=label,command=cmd,cwd=str(case),desired_exit=desired,actual_exit=run.returncode,status=result['status'],error=result.get('error'),checker_sha256=hashlib.sha256((case/'competition/deepeye/tools/check_rules.py').read_bytes()).hexdigest(),rules_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),stdout_sha256=hashlib.sha256(run.stdout).hexdigest(),stderr_sha256=hashlib.sha256(run.stderr).hexdigest()))
with (E/(phase+'-cli-result.json')).open('x',encoding='utf-8') as f:json.dump(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=phase,cases=rows),f,indent=2);f.write('\n')
print(json.dumps([{'case':r['label'],'actual_exit':r['actual_exit'],'desired_exit':r['desired_exit']} for r in rows]))
assert [r['actual_exit'] for r in rows]==([0,0,0] if phase=='red' else [1,1,0])
sys.exit(1 if phase=='red' else 0)
