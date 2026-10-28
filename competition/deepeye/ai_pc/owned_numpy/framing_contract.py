"""Independent strict A reader for the frozen C22E v1 diagnostic frames.
No model/core imports, callbacks, transport adoption or completion authority.
"""
import hashlib
import json
import math
import re
import struct

HEADER=struct.Struct('>4sBBHII')
IDENTITY_KEYS={'operation_id','request_hash','tested_commit','package_manifest_sha256',
               'run_id','invocation_id','actor_instance_id'}

def need(condition, message):
    if condition is not True: raise ValueError(message)

def integer(value, low, high):
    need(type(value) is int and low<=value<=high,'strict integer outside bound')
    return value

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key')
        result[key]=value
    return result

def bad_constant(value): raise ValueError('nonfinite JSON')

def document(raw):
    need(type(raw) is bytes,'original bytes required')
    try: return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=bad_constant)
    except (UnicodeError,RecursionError) as error: raise ValueError('invalid bounded JSON') from error

def typed_equal(left,right):
    if type(left) is not type(right): return False
    if type(left) is dict:
        return left.keys()==right.keys() and all(typed_equal(left[k],right[k]) for k in left)
    if type(left) is list:
        return len(left)==len(right) and all(typed_equal(a,b) for a,b in zip(left,right))
    return left==right

def identity(value):
    need(type(value) is dict and value.keys()==IDENTITY_KEYS,'exact identity fields required')
    for name in ('operation_id','run_id','actor_instance_id'):
        need(type(value[name]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}',value[name]) is not None,'identity label invalid')
    for name,size in (('request_hash',64),('tested_commit',40),('package_manifest_sha256',64)):
        need(type(value[name]) is str and re.fullmatch('[0-9a-f]{%d}'%size,value[name]) is not None,'identity digest invalid')
    integer(value['invocation_id'],1,(1<<63)-1)
    return value

def encode_request(value,index,payload,*,kind=1):
    identity(value); integer(index,1,65536)
    need(type(kind) is int and kind in (1,2),'request kind invalid')
    need(type(payload) is bytes,'original request payload bytes required')
    need((kind==1 and len(payload)>0) or (kind==2 and len(payload)==0),'request payload length invalid')
    meta=json.dumps(dict(identity=value,frame_index=index,payload_sha256=hashlib.sha256(payload).hexdigest()),ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')
    need(1<=len(meta)<=2048 and 16+len(meta)+len(payload)<=16384,'whole request bound exceeded')
    return HEADER.pack(b'C22E',1,kind,0,len(meta),len(payload))+meta+payload

def response_total(header):
    need(type(header) is bytes and len(header)==16,'exact 16-byte header required')
    magic,version,kind,flags,meta_size,payload_size=HEADER.unpack(header)
    need(magic==b'C22E' and version==1 and type(kind) is int and kind in (129,130) and flags==0,'response header invalid')
    need(1<=meta_size<=2048 and 1<=payload_size<=4096 and 16+meta_size+payload_size<=6160,'response declared bound invalid')
    return 16+meta_size+payload_size

def decode_response(raw,request):
    need(type(raw) is bytes and len(raw)>=16,'original response required')
    need(len(raw)==response_total(raw[:16]),'exact one whole response only')
    magic,version,kind,flags,meta_size,payload_size=HEADER.unpack(raw[:16])
    rm,rv,rk,rf,rms,rps=HEADER.unpack(request[:16])
    need(rm==b'C22E' and rv==1 and rf==0 and rk in (1,2) and len(request)==16+rms+rps and len(request)<=16384,'request binding invalid')
    request_meta=document(request[16:16+rms]); identity(request_meta['identity'])
    need(kind==(129 if rk==1 else 130),'response kind does not match request')
    meta=document(raw[16:16+meta_size]); payload=raw[16+meta_size:]
    need(type(meta) is dict and meta.keys()=={'identity','frame_index','request_frame_sha256','request_payload_sha256','payload_sha256'},'response metadata exact fields required')
    identity(meta['identity'])
    need(typed_equal(meta['identity'],request_meta['identity']),'original invocation identity mismatch')
    integer(meta['frame_index'],1,65536)
    need(type(request_meta['frame_index']) is int and meta['frame_index']==request_meta['frame_index'],'frame index mismatch')
    need(meta['request_frame_sha256']==hashlib.sha256(request).hexdigest(),'original whole request SHA mismatch')
    need(meta['request_payload_sha256']==hashlib.sha256(request[16+rms:]).hexdigest(),'original request payload SHA mismatch')
    need(meta['payload_sha256']==hashlib.sha256(payload).hexdigest(),'original reply payload SHA mismatch')
    need(payload.endswith(b'\n') and len(payload)==payload_size,'original reply LF/size invalid')
    return payload

def verify_result(payload,expected_raw,oracle_raw):
    actual,expected,oracle=document(payload),document(expected_raw),document(oracle_raw)
    need(type(actual) is dict and type(expected) is dict and actual.keys()==expected.keys(),'result exact schema required')
    probabilities=actual.get('probabilities')
    need(type(probabilities) is list and len(probabilities)==12 and all(type(x) is float and math.isfinite(x) and 0<=x<=1 for x in probabilities),'12 finite actual probabilities required')
    need(type(oracle.get('probabilities')) is list and len(oracle['probabilities'])==12,'pinned oracle probabilities required')
    delta=max(abs(a-b) for a,b in zip(probabilities,oracle['probabilities']))
    need(delta<=1e-6,'Root diagnostic cross-runtime probability tolerance exceeded')
    actual=dict(actual); expected=dict(expected)
    del actual['probabilities']; del expected['probabilities']
    need(typed_equal(actual,expected),'actual nonprobability structure/hash/class/mask/nonmotion changed')
    need(actual.get('movement_authorized') is False and actual.get('motion_bytes') is None and actual.get('formal_acceptance')=='incomplete','diagnostic result must grant no motion or acceptance')
    return {'probability_max_abs_error':delta,'diagnostic_tolerance':1e-6,'movement_authorized':False}

def verify_ended(payload,expected_raw):
    need(typed_equal(document(payload),document(expected_raw)),'actual END receipt differs from frozen one-prefix schema/content')
    return {'movement_authorized':False,'scope':'C local END only; not A STOP or BOOT'}
