"""Run actual R03 software checks; report open acceptance gates explicitly."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import datetime
import importlib.util

PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
PRODUCT=Path(__file__).resolve().parents[1]
REPO=PRODUCT.parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-only',action='store_true',help='Exit zero on software reference checks only; does not grant R03 acceptance')
    parser.add_argument('--output',type=Path,help='Optional JSON evidence path under the product root')
    args=parser.parse_args()
    scope=json.loads((REPO/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    actual=hashlib.sha256(json.dumps(scope['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    if actual!=PIN:
        raise ValueError('immutable human scope hash mismatch')
    interface=json.loads((PRODUCT/'docs/interface.json').read_bytes())
    if interface['immutable_scope_sha256']!=PIN or interface['abi_version']!=3:
        raise ValueError('interface is not bound to approved ABI3/human scope')
    result={'task_id':'DEEPEYE-IMPLEMENTATION-20261014','task_version':1,'requirements_sha256':PIN,
        'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'R03':'not_run','scope':'reference_only' if args.reference_only else 'full_R03',
        'hardware_enable_eligible':False,'checks':[], 'artifact_sha256':{}}
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,check=True).stdout.decode().strip()
    result['source_base_commit']=head
    result['source_identity_note']='Base commit plus actual artifact SHA256; uncommitted files are not relabeled as committed.'
    commands=[['integration/'+name] for name in ('test_wire.py','test_motion.py','test_host_schema.py',
        'test_host_envelope.py','test_pc_direct_heartbeat.py','test_pc_direct_watchdog.py',
        'test_sensor_source.py','test_trace_payload.py','test_clock_bounds.py',
        'test_boot_binding.py','test_contract_vectors.py')]
    commands.extend([['tests/test_boot_profile.py'],['tools/pipeline.py','verify','--selftest']])
    code=0
    for command in commands:
        try:
            run=subprocess.run([sys.executable,'-B','-X','utf8',*command],cwd=PRODUCT,capture_output=True,timeout=180)
            raw=run.stdout+run.stderr; exit_code=run.returncode
        except subprocess.TimeoutExpired as error:
            raw=(error.stdout or b'')+(error.stderr or b'')+b'\nCHECK_TIMEOUT\n';exit_code=124
        result['checks'].append({'command':[sys.executable,'-B','-X','utf8',*command],
            'exit_code':exit_code,'raw_output_sha256':hashlib.sha256(raw).hexdigest(),
            'output':raw.decode('utf-8',errors='strict')})
        if exit_code: code=1
    sys.path.insert(0,str(PRODUCT/'integration'))
    import boot_profile
    try:
        template=boot_profile.load_document(PRODUCT/'docs/boot_profiles.json')
        bound=boot_profile.bind_software_documents(template,PRODUCT)
        mismatches=boot_profile.verify_software_bindings(bound,PRODUCT)
        if mismatches: raise ValueError('BOOT dependency binding mismatch: '+str(mismatches))
        result['bound_software_profile']=bound
        result['bound_software_profile_sha256']=boot_profile.canonical_sha256(bound).hex()
        result['bound_software_profile_sha128']=boot_profile.slot_profile_sha128(bound).hex()
        result['all_mode_schedule_proof']=boot_profile.verify_all_mode_schedules(bound)
    except (ValueError,KeyError,OSError) as error:
        result['binding_error']=str(error);code=1
    for directory in ('docs','integration','tools','tests'):
        for path in sorted((PRODUCT/directory).rglob('*')):
            if path.is_file() and path.suffix in ('.py','.json','.md','.csv') and '__pycache__' not in path.parts:
                # C-owned off-assignment clock originals remain private evidence.
                if 'tests/ai/' in path.relative_to(PRODUCT).as_posix(): continue
                result['artifact_sha256'][path.relative_to(PRODUCT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    result['remaining_gates']=interface['remaining_R03_gates']
    result['software_checks']='passed' if code==0 else 'failed'
    if code==0:
        if args.reference_only:
            result['status']='software_reference_passed'
        else:
            result['status']='blocked';code=2
    else:
        result['status']='failed'
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
