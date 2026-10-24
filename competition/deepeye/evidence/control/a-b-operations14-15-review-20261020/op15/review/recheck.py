import importlib.util,json
from pathlib import Path
D=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('own',D/'review.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=[]
for c,w,t in [(4,8,8),(2,2,1),(32,64,64)]:
    name=f'positive-{c}-{w}-{t}';p=D/'attempt03';rows=[[int(x,16)for x in line.split()]for line in (p/(name+'.vec')).read_text().splitlines()[1:]];scenarios=json.loads((p/(name+'.scenarios.json')).read_bytes());r=m.check(p/(name+'.trace'),rows,scenarios,c,w,t);r.update(name=name,checker_sha256=m.sha(D/'review.py'),chronology='Accepted-command ledger added after fresh run; rechecked saved exact trace, not a pre-run freeze.');m.save(D/(name+'.command-ledger-check.json'),r);out.append({'name':name,'error_count':r['error_count'],'edges':r['edges']})
m.save(D/'command-ledger-recheck.json',out);print(json.dumps(out))
