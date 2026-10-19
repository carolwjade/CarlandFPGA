from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[2];A=O.parent/'isolation-pair-repair'
baseline=json.loads((A/'baseline.json').read_bytes())
def digest(path):
    data=path.read_bytes();return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
results={}
for category in ('dependencies','historical'):
    checks={}
    for name,want in baseline[category].items():
        checks[name]={'expected':want,'actual':digest(R/name)}
        checks[name]['equal']=checks[name]['actual']==want
    results[category]=checks
    failed=[name for name,result in checks.items() if not result['equal']]
    print(category,len(checks),'drift',len(failed))
    if failed:print(json.dumps(failed,ensure_ascii=False))
    assert not failed
(O/'dependency-stability.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
