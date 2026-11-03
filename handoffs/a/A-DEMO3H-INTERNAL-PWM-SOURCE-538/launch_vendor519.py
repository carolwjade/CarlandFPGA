"""A519 exact Root-released vendor child; no board/device/network helpers."""
import hashlib,json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((D/'BUILD_PLAN.json').read_bytes());release=json.loads((D/'Root-review.json').read_bytes())
if not(release['approved'] is True and release['operation_id']==p['operation_id'] and release['build_id']==p['build_id'] and release['plan_sha256']==sha(D/'BUILD_PLAN.json')):raise ValueError('concrete Root-reviewed A519 candidate required')
for name,pin in p['frozen_inputs'].items():
 if sha(D/name)!=pin:raise ValueError('frozen candidate changed:'+name)
if (D/'VENDOR_STARTED.json').exists():raise ValueError('one-use vendor launch consumed; never replay')
with (D/'VENDOR_STARTED.json').open('x') as f:json.dump(dict(operation_id=p['operation_id'],argv=p['vendor_argv'],board=False,internal_loopback_demo=True),f)
result=subprocess.run(p['vendor_argv'],cwd=D,creationflags=subprocess.CREATE_NO_WINDOW,check=False)
with (D/'VENDOR_RETURNED.json').open('x') as f:json.dump(dict(returncode=result.returncode,board=False),f)
raise SystemExit(result.returncode)
