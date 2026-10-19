import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];PRODUCT=ROOT/'.local/deepeye-implementation-a'
label=sys.argv[1]
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
temp=OUT/(label+'-temp');temp.mkdir(exist_ok=False);env.update(TEMP=str(temp),TMP=str(temp))
cmd=[sys.executable,'-B','-m','unittest','competition.deepeye.tests.test_check_rules.RuleCheckerTests'+('.test_current_artifacts_have_fifteen_official_and_fifteen_human_rows' if label=='red' else ''),'-v']
with (OUT/(label+'.stdout.log')).open('xb') as out,(OUT/(label+'.stderr.log')).open('xb') as err:
    run=subprocess.run(cmd,cwd=PRODUCT,env=env,stdout=out,stderr=err,timeout=60)
with (OUT/(label+'-command.json')).open('x',encoding='utf-8') as f:
    json.dump(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=cmd,cwd=str(PRODUCT),returncode=run.returncode),f,indent=2);f.write('\n')
print(json.dumps({'label':label,'returncode':run.returncode}))
sys.exit(run.returncode)
