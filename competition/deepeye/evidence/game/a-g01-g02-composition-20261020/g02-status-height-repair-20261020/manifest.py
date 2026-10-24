from verify import OUT, ROOT, sha, read, write
from datetime import datetime, timezone
files=[]
for name in ['baseline','candidate','logs','docs']:
    files.extend(p for p in (OUT/name).rglob('*') if p.is_file())
files.extend(p for p in OUT.iterdir() if p.is_file() and p.name not in ['lease.private.json','manifest.json','native-complete.json','receipt.json'])
files.extend([OUT/'stage/tests/review_boundary.gd',OUT/'stage/tests/tooltip_probe.gd'])
entries=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]
write(OUT/'manifest.json',{'scope':'selected durable evidence, source snapshots, raw logs and copied docs; excludes private lease, generated cache/user/temp and self','artifact_files':entries})
for entry in entries:
    p=ROOT/entry['path']; assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
receipt={'task_id':'DEEPEYE-IMPLEMENTATION-20261014','task_version':1,'job_id':'child-eeef333aae7e40aeb9835ac9a822213f','agent_id':'/root/g02_status_height_repair_20261020','status':'candidate ready for independent main review; all 29 formal cards not_run','contract':'DEEPEYE-HUMAN-LOCK-20261014/revision1','requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804','candidate_files':read(OUT/'final-hashes.json'),'manifest_sha256':sha(OUT/'manifest.json'),'final_result_sha256':sha(OUT/'final-result.txt'),'artifact_count':len(entries),'created_utc':datetime.now(timezone.utc).isoformat()}
write(OUT/'receipt.json',receipt)
print({'artifact_count':len(entries),'manifest_sha256':receipt['manifest_sha256'],'receipt_sha256':sha(OUT/'receipt.json'),'final_result_sha256':receipt['final_result_sha256']})
