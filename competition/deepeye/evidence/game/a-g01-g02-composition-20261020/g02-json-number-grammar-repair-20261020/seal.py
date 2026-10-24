from pathlib import Path
import hashlib,json,datetime,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def files(p):return {q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and '.godot' not in q.parts and '__pycache__' not in q.parts and q.name!='lease.private.json'}
pins=json.loads((H/'candidate-pins.json').read_bytes())
for rel,digest in pins['files'].items():assert sha(H/'candidate'/rel)==sha(H/'stage'/rel)==digest
after=json.loads((H/'source-after.json').read_bytes())
assert files(ROOT/'.local/deepeye-implementation-a/competition/deepeye/simulator')==after['product']
for label,folder in [('author','g02-gate-numeric-policy-repair-20261020'),('independent','g02-gate-numeric-independent-20261020')]:assert files(H.parent/folder)==after[label]
if sys.argv[1]=='seal':
 excludes={'lease.private.json','manifest.json','receipt.json','native-complete-response.json','final-result.txt'}
 entries=[]
 for p in sorted(H.rglob('*')):
  if not p.is_file() or p.name in excludes or set(p.relative_to(H).parts)&{'.godot','__pycache__','private-env'}:continue
  entries.append({'path':p.relative_to(H).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 dump(H/'manifest.json',{'schema':1,'files':entries,'exclusions':sorted(excludes|{'private-env/','.godot/','__pycache__/'}),'note':'Receipt/native completion/result are separately bound by receipt hashes; lease is private and excluded.'})
 dump(H/'receipt.json',{'schema':1,'job_id':'child-cff91e0872734285a30a18f970f2929f','agent_id':'/root/g02_json_number_grammar_repair_20261020','candidate_only':True,'product_writes':False,'product_delta':after['product_delta'],'old_evidence_unchanged':True,'contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','formal_cards':'all29 not_run','candidate_pins':pins,'manifest_sha256':sha(H/'manifest.json'),'manifest_entries':len(entries),'findings_sha256':sha(H/'findings.md'),'result_sha256':sha(H/'final-result.txt'),'native_completion_pending':True,'main_review_pending':True,'combined_current_integration_not_run':True,'visual_checks_not_run':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
elif sys.argv[1]=='close':
 result=json.loads((H/'native-complete-response.json').read_bytes());assert result['status']=='completed' and result['terminal'] is True and result['result']['text']==(H/'final-result.txt').read_text(encoding='utf8')
 receipt=json.loads((H/'receipt.json').read_bytes());assert receipt['manifest_sha256']==sha(H/'manifest.json') and receipt['result_sha256']==sha(H/'final-result.txt') and receipt['findings_sha256']==sha(H/'findings.md')
 for row in json.loads((H/'manifest.json').read_bytes())['files']:assert sha(H/row['path'])==row['sha256'],row['path']
 receipt.update(native_completion_pending=False,native_status='completed',native_terminal=True,exact_persisted_result=True,native_completion_sha256=sha(H/'native-complete-response.json'))
 dump(H/'receipt.json',receipt)
else:raise ValueError(sys.argv[1])
receipt=json.loads((H/'receipt.json').read_bytes());print(json.dumps({k:receipt[k] for k in ['manifest_entries','manifest_sha256','result_sha256','native_completion_pending']}))
