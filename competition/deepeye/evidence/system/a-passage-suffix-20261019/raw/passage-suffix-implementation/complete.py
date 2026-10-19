import asyncio
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from fpga_mesh.child_control import LocalControlFileClient

receipt=json.loads((HERE/'receipt.json').read_text(encoding='utf-8'))
assert not (HERE/'native_completion.json').exists(),'terminal call recorded; do not replay'
assert hashlib.sha256((HERE/'report.md').read_bytes()).hexdigest()==receipt['report']['sha256']
for relative,expected in receipt['sources'].items():
    assert hashlib.sha256((ROOT/'.local/deepeye-implementation-a'/relative).read_bytes()).hexdigest()==expected['sha256']
lease=json.loads((HERE.parent/'passage-suffix-implementation-lease.private.json').read_text(encoding='utf-8-sig'))
assert lease['job_id']==receipt['job_id']
summary=('Selected strict-red-outside complete-original-dt suffix implemented in exactly4 authorized product files. '
    'All remaining original exit-role six-face certificates retained; exactly one ARRIVED; weak APERTURE/blue-role gaps '
    'remain UNKNOWN. Deadline-clipped new suffix is UNKNOWN, with original CP/fence/deadline rules unchanged. '
    'Real numerical executor tests prove full-step one-callback/CAS and true final-slice solid rejection. '
    '253 regressions passed/no skips/exit0; all RED and setup-error evidence preserved. '
    '4 UTF8 LF frozen raw files equal Git clean; 41 dependencies/16 old design files unchanged. '
    'No executor/runtime/provider/OS/service/board/Git-index or external effects. '
    'report_sha256='+receipt['report']['sha256']+'; source_manifest_sha256='+receipt['source_manifest']['sha256']+'. '
    'Evidence .planning/deepeye-resume-20261018/passage-suffix-implementation/. '
    'Ready for main independent review; all29 formal cards/H12 chains/game/AI/board not_run; H01-H15 unchanged.')
(HERE/'native_completion_text.txt').write_text(summary+'\n',encoding='utf-8',newline='\n')
result=asyncio.run(LocalControlFileClient(Path(lease['original_control_file'])).call('native_complete',
    {'job_id':lease['job_id'],'lease_token':lease['lease_token'],'text':summary}))
public={key:result.get(key) for key in ('job_id','status','terminal','result','error','duplicate')}
(HERE/'native_completion.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(public,ensure_ascii=False))
