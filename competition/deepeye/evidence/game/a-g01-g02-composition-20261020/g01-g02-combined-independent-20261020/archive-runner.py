from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
source=(E/'review.py').read_bytes();rows=[]
for folder in sorted((E/'raw').iterdir()):
 rec=json.loads((folder/'result.json').read_bytes())
 if 'harness_sha256' in rec:
  actual=source.split(b" elif action=='core':",1)[0] if folder.name=='import' else source
  assert sha(actual)==rec['harness_sha256'],folder.name
  (folder/'runner-at-execution.py').write_bytes(actual)
  rows.append(dict(label=folder.name,path=str((folder/'runner-at-execution.py').relative_to(E)),sha256=sha(actual),exact=True))
 else:
  assert sha(source)==rec['script_sha256'];rows.append(dict(label=folder.name,path='review.py',sha256=sha(source),exact=True))
(E/'runner-source-readback.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print('All '+str(len(rows))+' actual execution runner versions preserved and exact hashes read back.')
