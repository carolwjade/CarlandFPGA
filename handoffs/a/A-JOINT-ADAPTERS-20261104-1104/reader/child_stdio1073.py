"""Explicit reviewed UART-child entry on the same actual physical product.
Import is inert. Root alone executes after genuine new B transfer and closure.
"""
import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys

REQUIREMENTS_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
SOURCE_PINS={
    'root_motion_reader1057.py':'4a23dcf5bc38c07bbc9459d9abd741c0faf86730c1efd3277a68def4a8f0046f',
    'root_loaded_product1031.py':'d3be22472808418cc9fef164fe8ca3021987b84ecde1cef9261568155e6da57b',
    'load_once_joint50_1024.py':'478ee99fa753f2050812c7aec5655ba286004b8262565a5304dad7c2dc8705c7',
    'verify_uart_joint50_hwh.py':'d8a96c5e6c277b8608b89e22bba49fae7425e331af79dfa2d9c14be437550a24',
    'snapshot/competition/deepeye/tools/diagnostic/functional50_board_a.py':'865a857c2455a9cc0254db54eb7b8c71cb16f5416bb299b2711cd9151649268d',
    'b_live/baseline_mtr4/fpga_link/__init__.py':'d08591c5944154e31d5e64b242f77a473597c0d4518f69769d258dee0bd90fb4',
    'b_live/baseline_mtr4/fpga_link/bridge_stdio.py':'9f89955347b28796026bb6704009332c3c18d14c5ccf6d46b20bb258c0a9f52d',
    'b_live/baseline_mtr4/fpga_link/session.py':'5e7765a01e49b1b7c324d338773b7689f140c8fe6dd09f044d27cd62438a39ba',
    'b_live/baseline_mtr4/fpga_link/ssh_client.py':'1dbda9cd8c06d68b073035c949884dd2d6b89f7e52ff4b8ad6d89cd024e54d99',
    'b_live/baseline_mtr4/fpga_link/uartlite.py':'29cc8160790bdc2d6fa25be1de1994dc39586fba3d884b9826a2d2c030eed778',
    'b_live/baseline_mtr4/motor_runtime/variable_session.py':'1d5ce3f2aea1849b7e55e164e6c8d1db9e5d333e8a821f1feac9e3416f4d1d38',
    'b_live/baseline_mtr4/pc/__init__.py':'6928c27bc0a83f2243336100a0770b681e872865a81859e1aa4fac1f32d0c6d0',
    'b_live/baseline_mtr4/pc/bridge.py':'30a00e99f89613ff17b28de7b12d4945236c238c37ac3286d2e610eb95cd67cc',
    'b_live/baseline_mtr4/pc/codec.py':'62cf254d4d4b519578da364b49f0555d61de386ee1430e664e63013fadbed006',
    'b_live/baseline_mtr4/pc/transport.py':'601a0b0544dc0749ffe7f254b2dcd953565a7652168f6714d623a1087ad33fcd',
    'b_live/drill_live_link/__init__.py':'b9f07fd214ecbd2529b7c321e364c3098246f11df60c7a490b3c32540d0c81b3',
    'b_live/drill_live_link/follower.py':'6b975c4cb3ad23723b131ee088edfaa9810fa387af0be61382497ffe088a1134',
    'b_live/drill_live_link/model.py':'249d0e6c253de8f91402ba5e35f0d385eea789a886c14ea249ad092bf5a69333',
    'b_live/drill_live_link/session_client.py':'431d2466061a441365d0a1f99e2b6a08d7d3f9fbbc9a7110f222c434cb6eab1d',
    'b_live/product_uart_service.py':'6404ce0b0be4b1d1f85615f083c63b6d1df9fef2bd55bbaea022a35032acab13',
    'b_live/product_uart_stdio.py':'3bef22726e97eb7c950d7b3c3d7a1914367eed51c2a28d74015e3ae6017502c1',
}
TRANSFER_KEYS={'operation_id','transfer_id','mcu_observation_id','last_seq','evidence_sha256','scope'}
PROFILE_KEYS={'expected','run_id','source'}
CHILD_KEYS={'schema','requirements_sha256','operation_id','parent','predecessor','state_directory','purpose','request_sha256'}
CHILD_REVIEW_KEYS={'schema','requirements_sha256','review_id','reviewer','profile','transfer','authentic_b_receipt_path','authentic_b_receipt_sha256','source_human_reference','onsite_wiring_reference','child_manifest_path','child_manifest_sha256'}
PURPOSE_SCOPE={'DIAGNOSTIC_ONLY':'DIAGNOSTIC_ONLY','MOTION_READY_NO_MOTOR':'MOTION_READY'}


def _need(value,reason):
    if not value:raise ValueError(reason)

def _sha(blob):return hashlib.sha256(blob).hexdigest()

def _hex(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256 required')
    return value

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')

def _safe_path(value):
    path=Path(value);_need(path.is_absolute() and '..' not in path.parts,'absolute non-link path required')
    for item in (path,*path.parents):_need(not item.is_symlink(),'symlink path refused')
    return path

def _identity(info):return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)

def _read_pinned(value,expected,limit):
    path=_safe_path(value);_hex(expected)
    with path.open('rb') as handle:
        before=os.fstat(handle.fileno())
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded single-link regular input required')
        blob=handle.read(limit+1);after=os.fstat(handle.fileno())
    _need(len(blob)==before.st_size and _identity(before)==_identity(after)==_identity(path.lstat()),'input changed during read')
    _need(_sha(blob)==expected,'input SHA256 mismatch '+str(path))
    return blob

def _json(blob):
    def unique(pairs):
        value={}
        for key,item in pairs:
            _need(key not in value,'duplicate JSON key');value[key]=item
        return value
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def _documents(profile,transfer,review,receipt_path,receipt_sha256,child,manifest_path,manifest_sha256,selected_purpose):
    """Pure explicit-purpose cross-check, never physical authority."""
    _need(type(profile) is dict and set(profile)==PROFILE_KEYS,'exact reviewed profile fields required')
    _need(type(transfer) is dict and set(transfer)==TRANSFER_KEYS,'exact real B transfer fields required')
    _need(type(child) is dict and set(child)==CHILD_KEYS,'exact eight child manifest fields required')
    body=dict(child);request=body.pop('request_sha256');_need(_sha(_canonical(body))==_hex(request),'canonical child request mismatch')
    _need(child['schema']=='DEEPEYE-UART-CHILD-OPERATION-v1' and child['requirements_sha256']==REQUIREMENTS_SHA256,'revision2 child manifest required')
    _need(selected_purpose in PURPOSE_SCOPE and child['purpose']==selected_purpose and transfer['scope']==PURPOSE_SCOPE[selected_purpose],'explicit selected child purpose/scope mismatch')
    _need(transfer['operation_id']==child['operation_id'],'fresh transfer must name actual child operation')
    _need(type(review) is dict and set(review)==CHILD_REVIEW_KEYS and review['schema']=='DEEPEYE-ROOT-UART-CHILD-TRANSFER-REVIEW-v1' and review['requirements_sha256']==REQUIREMENTS_SHA256,'exact twelve-field revision2 child Root review required')
    _need(_canonical(review['profile'])==_canonical(profile) and _canonical(review['transfer'])==_canonical(transfer),'Root review/profile/transfer mismatch')
    _need(_safe_path(review['child_manifest_path'])==_safe_path(manifest_path) and review['child_manifest_sha256']==_hex(manifest_sha256),'reviewed child manifest file mismatch')
    _need(_safe_path(review['authentic_b_receipt_path'])==_safe_path(receipt_path) and review['authentic_b_receipt_sha256']==_hex(receipt_sha256),'Root review/authentic receipt mismatch')

def _parser():
    parser=argparse.ArgumentParser(description='Root-only already-loaded PS child service; explicit diagnostic or motion-no-motor purpose')
    parser.add_argument('--allow-reviewed-child-uart',action='store_true',help='explicitly permit only this SHA-reviewed child UART attach')
    parser.add_argument('--purpose',choices=tuple(PURPOSE_SCOPE),required=True)
    for name in ('approved-plan','approved-plan-sha256','operation-directory','transfer-review','transfer-review-sha256','profile','profile-sha256','transfer','transfer-sha256','b-receipt','b-receipt-sha256','child-manifest','child-manifest-sha256'):
        parser.add_argument('--'+name,required=True)
    return parser

def _load_apis(stage):
    for relative,expected in SOURCE_PINS.items():_read_pinned(stage/relative,expected,2*1024*1024)
    paths=(stage,stage/'snapshot',stage/'b_live',stage/'b_live/baseline_mtr4')
    sys.path[:0]=[str(path) for path in paths]
    service=importlib.import_module('product_uart_service')
    facade=importlib.import_module('product_uart_stdio')
    reader=importlib.import_module('root_motion_reader1057')
    for module,relative in ((service,'b_live/product_uart_service.py'),(facade,'b_live/product_uart_stdio.py'),(reader,'root_motion_reader1057.py')):
        _need(Path(module.__file__)==stage/relative,'fresh staged API import required '+relative)
    _need(service.REQUIREMENTS_SHA256==reader.REQUIREMENTS_SHA256==REQUIREMENTS_SHA256,'revision2 API contract mismatch')
    _need(reader.PURPOSE_SCOPE==PURPOSE_SCOPE,'pinned child purpose API mismatch')
    return service,facade,reader

def _run_loaded(args,protocol_reader,protocol_writer):
    _need(args.allow_reviewed_child_uart,'explicit reviewed child UART permission required')
    stage=_safe_path(Path(__file__).parent)
    service_api,stdio_api,reader_api=_load_apis(stage)
    review=_json(_read_pinned(args.transfer_review,args.transfer_review_sha256,131072))
    profile_doc=_json(_read_pinned(args.profile,args.profile_sha256,131072))
    transfer_doc=_json(_read_pinned(args.transfer,args.transfer_sha256,131072))
    _read_pinned(args.b_receipt,args.b_receipt_sha256,8*1024*1024)
    child=_json(_read_pinned(args.child_manifest,args.child_manifest_sha256,131072))
    _documents(profile_doc,transfer_doc,review,args.b_receipt,args.b_receipt_sha256,child,_safe_path(args.child_manifest),args.child_manifest_sha256,args.purpose)
    root=reader_api.build_actual_reader(service_api,approved_plan_path=_safe_path(args.approved_plan),approved_plan_sha256=args.approved_plan_sha256,actual_operation_directory=_safe_path(args.operation_directory),transfer_review_path=_safe_path(args.transfer_review),transfer_review_sha256=args.transfer_review_sha256,child_manifest_path=_safe_path(args.child_manifest),child_manifest_sha256=args.child_manifest_sha256)
    state=root.state_directory
    _need(state==_safe_path(child['state_directory']),'actual child-bound persistent hardware state required')
    actual=root.read_current()
    profile=service_api.Profile(actual,profile_doc['run_id'],profile_doc['source']);profile.validate()
    _need(_canonical(asdict(profile))==_canonical(profile_doc),'reviewed profile does not match actual loaded product')
    transfer=service_api.BTransfer(**transfer_doc);transfer.validate()
    reader_api._validate_child_review(review,asdict(profile),asdict(transfer),_safe_path(args.child_manifest),args.child_manifest_sha256,args.purpose)
    service=None
    try:
        service=service_api.ProductUartService.attach(root,profile,transfer,state)
        return stdio_api.serve_loaded_product(service,protocol_reader,protocol_writer)
    finally:
        # The unchanged service owns terminal STOP, audit and unknown handling.
        # Its close is idempotent after the existing facade's STOP/EOF cleanup.
        if service is not None:service.close()

def main(argv=None):
    parser=_parser();args=parser.parse_args(argv)
    if not args.allow_reviewed_child_uart:parser.error('--allow-reviewed-child-uart is required for any physical attach')
    _need(os.name=='posix' and os.geteuid()==0 and os.uname().machine=='armv7l','actual root armv7l PS execution required')
    # Keep a dedicated copy of the original stdout pipe for protocol JSON.
    # Both Python and native PYNQ output on fd1 go to stderr thereafter.
    sys.stdout.flush();sys.stderr.flush()
    protocol_fd=os.dup(sys.stdout.fileno())
    try:
        protocol_writer=os.fdopen(protocol_fd,'w',buffering=1,encoding='utf8',errors='strict',newline='\n')
    except BaseException:
        os.close(protocol_fd);raise
    try:
        os.dup2(sys.stderr.fileno(),sys.stdout.fileno())
        with redirect_stdout(sys.stderr):
            return _run_loaded(args,sys.stdin,protocol_writer)
    except Exception as error:
        print(json.dumps({'event':'child_cli_error','error_type':type(error).__name__,'error':str(error)[:256],'retry':False},sort_keys=True),file=sys.stderr,flush=True)
        return 2
    finally:
        protocol_writer.close()


if __name__=='__main__':raise SystemExit(main())
