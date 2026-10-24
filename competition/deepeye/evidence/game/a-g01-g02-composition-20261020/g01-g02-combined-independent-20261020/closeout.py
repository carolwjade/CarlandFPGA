import json
from pathlib import Path
import finalize as f
import review as v
E=Path(__file__).resolve().parent
result=(E/'final-result.txt').read_text(encoding='utf8')
native=v.read(E/'native-complete-response.json')
assert native['status']=='completed' and native['terminal'] is True and native['result']['text']==result
receipt=v.read(E/'receipt.json')
receipt.update(native_completion_pending=False,native_status='completed',native_terminal=True,exact_persisted_result=True,native_completion_sha256=v.sha(E/'native-complete-response.json'),result_sha256=v.sha(E/'final-result.txt'),findings_sha256=v.sha(E/'findings.md'))
v.dump('receipt.json',receipt)
f.seal()
print(json.dumps(dict(status='completed',terminal=True,exact_persisted_result=True,manifest_sha256=v.sha(E/'non-secret-artifact-manifest.json'),receipt_sha256=v.sha(E/'receipt.json'),result_sha256=v.sha(E/'final-result.txt'))))
