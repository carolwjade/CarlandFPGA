"""Manifest owned evidence only. Never read the private input lease."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).absolute().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
excluded={'lease.private.json','evidence-manifest.json','terminal-hashes.json','native-complete-response.json'}
files={str(p.relative_to(H)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(H.rglob('*')) if p.is_file() and p.name not in excluded}
(H/'evidence-manifest.json').write_text(json.dumps({'excluded_names':sorted(excluded),'files':files},indent=2)+'\n',encoding='utf-8')
if (H/'native-complete-response.json').exists():
    result=json.loads((H/'native-complete-response.json').read_bytes())
    assert result['status']=='completed' and result['terminal'] is True
    assert result['result']['text']==(H/'final-result.txt').read_text(encoding='utf-8')
    for rel,item in files.items():assert (H/rel).stat().st_size==item['bytes'] and sha(H/rel)==item['sha256']
    names=['receipt.json','findings.md','audit-result.json','independent-oracle-before-simulation.json','evidence-manifest.json',
           'final-result.txt','native-complete-response.json','native-complete-execution.json','cleanup-current.json']
    hashes={name:sha(H/name) for name in names}
    (H/'terminal-hashes.json').write_text(json.dumps({'status':'completed','terminal':True,'exact_persisted_result':True,'files':hashes},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'manifest_sha256':sha(H/'evidence-manifest.json'),'receipt_sha256':sha(H/'receipt.json'),'findings_sha256':sha(H/'findings.md')}))
