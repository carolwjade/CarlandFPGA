import datetime,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];PRODUCT=ROOT/'.local/deepeye-implementation-a'
assert not (PRODUCT/'competition/deepeye/tools/check_rules.py').exists()
paths=[PRODUCT/'competition/deepeye/docs/rules.json',PRODUCT/'competition/deepeye/docs/requirements_trace.csv',
       PRODUCT/'docs/competition/deepeye-2026/immutable_scope.json',ROOT/'docs/competition/deepeye-2026/immutable_scope.json',
       ROOT/'docs/competition/deepeye-2026/taskbook_final.md',ROOT/'docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with (OUT/'input-manifest.json').open('x',encoding='utf-8') as f:
    json.dump(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pins=pins,work_id='A-R01-CHECKER-20261019-v1',base_head='889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1',formal29='not_run'),f,indent=2);f.write('\n')
print('Frozen six read-only inputs; new checker still absent.')
