"""Check implemented ABI references; keep the full R03 gate closed while partial."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
PRODUCT=Path(__file__).resolve().parents[1]
REPO=PRODUCT.parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-only',action='store_true',help='Run bounded framing/quantized motion references, not full R03 acceptance')
    parser.add_argument('--output',type=Path,help='Optional JSON evidence path under the product root')
    args=parser.parse_args()
    scope=json.loads((REPO/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    actual=hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    if actual!=PIN:
        raise ValueError('immutable human scope hash mismatch')
    interface=json.loads((PRODUCT/'docs/interface.json').read_bytes())
    if interface['immutable_scope_sha256']!=PIN or interface['abi_version']!=3:
        raise ValueError('interface is not bound to approved ABI3/human scope')
    result={'task_id':'DEEPEYE-IMPLEMENTATION-20261014','task_version':1,'requirements_sha256':PIN,'R03':'not_run','scope':'reference_only' if args.reference_only else 'full_R03','checks':[]}
    if not args.reference_only:
        result.update(status='blocked',remaining_gates=interface['remaining_R03_gates'])
        code=2
    else:
        code=0
        for rel in ('integration/test_wire.py','integration/test_motion.py'):
            run=subprocess.run([sys.executable,'-X','utf8',rel],cwd=PRODUCT,capture_output=True)
            raw=run.stdout+run.stderr
            result['checks'].append({'command':['python','-X','utf8',rel],'exit_code':run.returncode,'raw_output_sha256':hashlib.sha256(raw).hexdigest(),'output':raw.decode('utf-8',errors='strict')})
            if run.returncode: code=1
        result['status']='passed' if code==0 else 'failed'
    if args.output:
        target=(PRODUCT/args.output).resolve()
        target.relative_to(PRODUCT)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return code


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,OSError) as error:
        print(json.dumps({'status':'failed','error':str(error),'R03':'not_run'}))
        raise SystemExit(1)
