"""Strict private original-byte world protocol; import has no native effects."""
import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import struct
from types import MappingProxyType

MAGIC=b'DEYWRL01'
MAX_PAYLOAD=65536
MAX_CONTROL=16384
MAX_UI_STATUS=8192
MAX_CHUNK=45056
MAX_SNAPSHOT=134217728
MAX_CHUNKS=3072
MAX_IO=65536
MAX_FRAMES=8
_HEADER=struct.Struct('>8scQI')
_U64=re.compile(r'(?:0|[1-9][0-9]*)\Z',re.ASCII)
_SHA=re.compile(r'[0-9a-f]{64}\Z',re.ASCII)
_HEX=re.compile(r'(?:[0-9a-f]{8}|[0-9a-f]{16})\Z',re.ASCII)


class WireFault(ValueError):pass


def _keys(value,fields):
    if type(value) is not dict or set(value)!=set(fields):raise WireFault('exact record fields required')


def _u64(value):
    if type(value) is not str or len(value)>20 or not _U64.fullmatch(value) or int(value)>18446744073709551615:
        raise WireFault('canonical U64 required')
    return int(value)


def _label(value):
    if type(value) is not str or not value or len(value.encode('utf-8'))>256 or any(ord(c)<32 for c in value):
        raise WireFault('bounded nonempty label required')


def _sha(value):
    if type(value) is not str or not _SHA.fullmatch(value):raise WireFault('lowercase SHA256 required')


def _real(value,width=None):
    if type(value) is not str or not _HEX.fullmatch(value) or (width and len(value)!=width//4):
        raise WireFault('encoded finite scalar required')
    bits=int(value,16)
    exponent=(bits>>23)&255 if len(value)==8 else (bits>>52)&2047
    if exponent==(255 if len(value)==8 else 2047):raise WireFault('nonfinite scalar rejected')


def _vector(value,count,width):
    if type(value) is not list or len(value)!=count:raise WireFault('exact encoded vector required')
    for scalar in value:_real(scalar,width)


_FREEZE=dict(freeze_id='Label',world_epoch='U64',document_generation='U64',geometry_generation='U64',
    main_instance_id='U64',document_instance_id='U64',workspace_instance_id='U64',drill_root_instance_id='U64',
    source_bundle_sha256='SHA',immutable_payload_sha256='SHA',geometry_state_sha256='SHA')
_COUNTS=dict(nodes=4096,objects=30,surfaces=64,unique_vertices=1000000,indices=3000000,
    required_geometry_nodes=4096,observer_nodes=4096)


def _transform(value,width):
    _keys(value,('basis_columns','origin'))
    if type(value['basis_columns']) is not list or len(value['basis_columns'])!=3:raise WireFault('three basis columns required')
    for column in value['basis_columns']:_vector(column,3,width)
    _vector(value['origin'],3,width)
    if width is None and len({len(item) for col in value['basis_columns'] for item in col}|{len(item) for item in value['origin']})!=1:
        raise WireFault('one frozen real_t width required')


def _pose(value):
    _keys(value,('position_m','orientation_xyzw','speed_m_s'))
    _vector(value['position_m'],3,64);_vector(value['orientation_xyzw'],4,64);_real(value['speed_m_s'],64)
    if all(int(item,16)&0x7fffffffffffffff==0 for item in value['orientation_xyzw']):raise WireFault('nonzero quaternion required')
    speed=int(value['speed_m_s'],16)
    if speed>>63 and speed&0x7fffffffffffffff:raise WireFault('nonnegative speed required')


def _validate(value,kind):
    if type(kind) is tuple:
        if value not in kind or type(value) is not type(kind[0]):raise WireFault('invalid exact enum')
    elif kind=='U64':_u64(value)
    elif kind=='Label':_label(value)
    elif kind=='SHA':_sha(value)
    elif kind=='Freeze':
        _keys(value,_FREEZE)
        for name,schema in _FREEZE.items():_validate(value[name],schema)
    elif kind=='Counts':
        _keys(value,_COUNTS)
        for name,limit in _COUNTS.items():
            if _u64(value[name])>limit:raise WireFault('inventory count over budget')
    elif kind=='Pose':_pose(value)
    elif kind=='F64Transform':_transform(value,64)
    elif kind=='RealTransform':_transform(value,None)
    elif kind=='Base64':
        if type(value) is not str or len(value)>4*((MAX_CHUNK+2)//3):raise WireFault('chunk encoding over budget')
        try:raw=base64.b64decode(value,validate=True)
        except (ValueError,TypeError) as error:raise WireFault('strict base64 required') from error
        if len(raw)>MAX_CHUNK or base64.b64encode(raw).decode('ascii')!=value:raise WireFault('noncanonical base64 chunk')
    else:raise WireFault('unknown schema')


_BODIES={
 'HELLO':('G',dict(launch_challenge='SHA',engine_pid='U64',engine_version='Label',engine_sha256='SHA',source_bundle_sha256='SHA',scalar_width=(32,64),main_instance_id='U64',document_instance_id='U64',workspace_instance_id='U64',drill_root_instance_id='U64',document_generation='U64',geometry_generation='U64',raw_layout_sha256='SHA')),
 'FREEZE_REQUEST':('R',dict(expected_document_generation='U64',expected_raw_sha256='SHA',snapshot_limits_sha256='SHA',model_policy_sha256='SHA')),
 'SNAPSHOT_BEGIN':('G',dict(freeze_identity='Freeze',raw_layout_sha256='SHA',snapshot_bytes='U64',snapshot_sha256='SHA',chunk_count='U64',inventory_counts='Counts')),
 'SNAPSHOT_CHUNK':('G',dict(freeze_id='Label',chunk_index='U64',offset='U64',decoded_length='U64',chunk_sha256='SHA',data_base64='Base64')),
 'SNAPSHOT_END':('G',dict(freeze_identity='Freeze',snapshot_sha256='SHA',decoded_total='U64',chunks='U64',geometry_audit_digest='SHA')),
 'INITIAL_VIEW':('R',dict(freeze_id='Label',geometry_identity='SHA',pose_revision='U64',desired_pose='Pose',desired_transform='F64Transform')),
 'PUBLISH_VIEW':('R',dict(freeze_id='Label',geometry_identity='SHA',expected_previous_revision='U64',pose_revision='U64',desired_pose='Pose',desired_transform='F64Transform',numerical_receipt_digest='SHA')),
 'VIEW_READBACK':('G',dict(freeze_identity='Freeze',publication_operation_id='Label',payload_digest='SHA',state=('APPLIED','APPLYING_UNKNOWN','NOT_SEEN'),pose_revision='U64',drill_root_instance_id='U64',local_transform='RealTransform',global_transform='RealTransform',engine_tick='U64',geometry_audit_digest='SHA')),
 'QUERY_VIEW':('R',dict(freeze_id='Label',publication_operation_id='Label',payload_digest='SHA',expected_pose_revision='U64')),
 'UI_STATUS':('R',dict(freeze_id='Label',status_base64='Base64')),
 'WORLD_STATUS':('G',dict(freeze_identity='Freeze',state=('FROZEN','BOUND_STOPPED','INVALIDATED'),pose_revision='U64',geometry_audit_digest='SHA',engine_tick='U64')),
 'EDIT_REQUEST':('G',dict(freeze_id='Label',request_kind=('edit','load','randomize','reset','unlock'),document_generation='U64')),
 'STOP_NOTICE':('G',dict(freeze_id='Label',source=('human_escape','human_ui','local_fault','channel_fault'),pose_revision='U64')),
 'STOP':('R',dict(freeze_id='Label',reason_code='Label',expected_pose_revision='U64')),
 'STOPPED':('G',dict(freeze_identity='Freeze',pose_revision='U64',last_publication_operation_id='Label',publication_state=('APPLIED','APPLYING_UNKNOWN','NONE'))),
 'UNLOCK_FOR_EDIT':('R',dict(retired_freeze_id='Label',retired_epoch='U64',expected_pose_revision='U64',retirement_record_digest='SHA')),
 'EDITABLE':('G',dict(retired_freeze_id='Label',document_generation='U64',geometry_generation='U64',raw_layout_sha256='SHA')),
 'REFUSAL':('G',dict(refused_operation_id='Label',code=('malformed','over_budget','source_mismatch','instance_lost','mutation','stale_epoch','stale_revision','duplicate_publish','unknown_effect'),owner_state='Label')),
}


def validate_message(message):
    _keys(message,('type','run_id','world_epoch','operation_id','body'))
    name=message['type']
    if type(name) is not str or name not in _BODIES:raise WireFault('unknown message type')
    _label(message['run_id']);_label(message['operation_id']);epoch=_u64(message['world_epoch'])
    direction,fields=_BODIES[name];body=message['body'];_keys(body,fields)
    for key,kind in fields.items():_validate(body[key],kind)
    if name=='UI_STATUS' and not 1<=len(base64.b64decode(body['status_base64'],validate=True))<=MAX_UI_STATUS:
        raise WireFault('UI status decoded bytes over budget')
    if name=='HELLO' and epoch!=0:raise WireFault('HELLO epoch must be zero')
    if name=='INITIAL_VIEW' and body['pose_revision']!='0':raise WireFault('initial revision must be zero')
    if name=='PUBLISH_VIEW' and _u64(body['pose_revision'])!=_u64(body['expected_previous_revision'])+1:raise WireFault('publication revision must increase once')
    if 'freeze_identity' in body and body['freeze_identity']['world_epoch']!=message['world_epoch']:raise WireFault('freeze epoch mismatch')
    if name=='SNAPSHOT_CHUNK' and (_u64(body['decoded_length'])>MAX_CHUNK or _u64(body['chunk_index'])>=MAX_CHUNKS):raise WireFault('chunk over budget')
    if name=='SNAPSHOT_BEGIN' and not (1<=_u64(body['snapshot_bytes'])<=MAX_SNAPSHOT and 1<=_u64(body['chunk_count'])<=MAX_CHUNKS):raise WireFault('snapshot over budget')
    return direction


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise WireFault('duplicate decoded JSON key')
        result[key]=value
    return result


def _depth(value):
    work=[(value,1)]
    while work:
        current,depth=work.pop()
        if depth>32:raise WireFault('JSON depth over budget')
        if type(current) is dict:work.extend((item,depth+1) for item in current.values())
        elif type(current) is list:work.extend((item,depth+1) for item in current)


def decode_payload(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_PAYLOAD:raise WireFault('payload bytes over budget')
    try:
        message=json.loads(raw.decode('utf-8','strict'),object_pairs_hook=_pairs,
            parse_constant=lambda value:(_ for _ in ()).throw(WireFault('nonfinite JSON token')))
        _depth(message);validate_message(message)
    except (UnicodeError,ValueError,TypeError,RecursionError,OverflowError) as error:
        if isinstance(error,WireFault):raise
        raise WireFault('strict JSON payload rejected') from error
    if message['type']!='SNAPSHOT_CHUNK' and len(raw)>MAX_CONTROL:raise WireFault('control payload over budget')
    return message


def encode_payload(message):
    validate_message(message);_depth(message)
    try:raw=json.dumps(message,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    except (ValueError,TypeError,UnicodeError) as error:raise WireFault('JSON encoding rejected') from error
    decode_payload(raw)
    return raw


def _immutable(value):
    if type(value) is dict:return MappingProxyType({key:_immutable(item) for key,item in value.items()})
    if type(value) is list:return tuple(_immutable(item) for item in value)
    return value


@dataclass(frozen=True,eq=False)
class ReceivedFrame:
    payload:bytes
    message:object
    direction:str
    sequence:int
    payload_digest:str
    def as_dict(self):return decode_payload(self.payload)


@dataclass(eq=False)
class Transmission:
    payload:bytes
    payload_digest:str
    frame:bytes
    sequence:int
    deadline_ns:int
    offset:int=0
    started:bool=False
    complete:bool=False
    failed:bool=False


def _received_for_test(message):
    raw=encode_payload(message)
    return ReceivedFrame(raw,_immutable(decode_payload(raw)),_BODIES[message['type']][0],0,hashlib.sha256(raw).hexdigest())


class _WireChannel:
    def __init__(self,original_socket,key,run_id):
        if type(key) is not bytes or len(key)!=32:raise WireFault('private32byte key required')
        _label(run_id)
        self._socket,self._key,self.run_id=original_socket,key,run_id
        self._original_socket=original_socket
        self.tx_sequence=self.rx_sequence=0
        self._rx=bytearray();self._pending=None;self._transactions=[];self._failure=None

    def _check(self):
        if self._failure is not None:raise WireFault('original channel permanently failed')
        if self._socket is not self._original_socket:self._fail('original socket replaced')

    def _fail(self,reason):
        self._failure=reason
        if self._pending is not None:self._pending.failed=True
        raise WireFault(reason)

    def queue(self,message,deadline_ns):
        self._check()
        if self._pending is not None:self._fail('cannot append behind original pending frame')
        if type(deadline_ns) is not int or not 0<deadline_ns<(1<<63):self._fail('fixed deadline required')
        raw=encode_payload(message)
        if validate_message(message)!='R' or message['run_id']!=self.run_id:self._fail('Root direction/run mismatch')
        if self.tx_sequence>(1<<64)-1 or len(self._transactions)>=4096:self._fail('transmission sequence/record budget exhausted')
        header=_HEADER.pack(MAGIC,b'R',self.tx_sequence,len(raw))
        frame=header+raw+hmac.digest(self._key,header+raw,'sha256')
        tx=Transmission(raw,hashlib.sha256(raw).hexdigest(),frame,self.tx_sequence,deadline_ns)
        self._transactions.append(tx);self._pending=tx;self.tx_sequence+=1
        return tx

    def complete_tx(self,tx):
        return any(tx is original for original in self._transactions) and tx.complete and not tx.failed

    def healthy_frame_aligned(self):
        return (self._failure is None and self._socket is self._original_socket and not self._rx
            and self._pending is None)

    def pump(self,now_ns):
        self._check()
        if type(now_ns) is not int or not 0<=now_ns<(1<<63):self._fail('original time sample required')
        budget=MAX_IO;frames=[]
        try:
            tx=self._pending
            while tx is not None and budget:
                if now_ns>=tx.deadline_ns:self._fail('original frame deadline expired')
                remaining=tx.frame[tx.offset:tx.offset+budget];tx.started=True
                try:count=self._socket.send(remaining)
                except BlockingIOError:break
                if type(count) is not int or not 1<=count<=len(remaining):self._fail('unknown or zero socket send progress')
                tx.offset+=count;budget-=count
                if tx.offset==len(tx.frame):tx.complete=True;self._pending=None;break
            while budget and len(frames)<MAX_FRAMES:
                while len(self._rx)>=_HEADER.size and len(frames)<MAX_FRAMES:
                    magic,direction,sequence,length=_HEADER.unpack(self._rx[:_HEADER.size])
                    if magic!=MAGIC or direction!=b'G' or sequence!=self.rx_sequence or not 1<=length<=MAX_PAYLOAD:self._fail('frame header/direction/sequence rejected')
                    total=_HEADER.size+length+32
                    if len(self._rx)<total:break
                    original=bytes(self._rx[:total]);header_payload=original[:-32]
                    if not hmac.compare_digest(hmac.digest(self._key,header_payload,'sha256'),original[-32:]):self._fail('original frame MAC rejected')
                    payload=original[_HEADER.size:-32];message=decode_payload(payload)
                    if validate_message(message)!='G' or message['run_id']!=self.run_id:self._fail('engine direction/run mismatch')
                    received=ReceivedFrame(payload,_immutable(message),'G',sequence,hashlib.sha256(payload).hexdigest())
                    del self._rx[:total];self.rx_sequence+=1;frames.append(received)
                if len(frames)>=MAX_FRAMES:break
                try:chunk=self._socket.recv(min(budget,MAX_PAYLOAD+_HEADER.size+32-len(self._rx)))
                except BlockingIOError:break
                if type(chunk) is not bytes or not chunk:self._fail('original stream EOF/unknown receive')
                if len(chunk)>budget:self._fail('socket exceeded requested receive count')
                self._rx.extend(chunk);budget-=len(chunk)
            return tuple(frames)
        except BaseException as error:
            if self._failure is None:self._failure=type(error).__name__
            if self._pending is not None:self._pending.failed=True
            if isinstance(error,WireFault):raise
            raise WireFault('original socket call failed') from error


class _SnapshotAssembly:
    def __init__(self,begin_frame):
        if type(begin_frame) is not ReceivedFrame or begin_frame.message['type']!='SNAPSHOT_BEGIN':raise WireFault('original begin frame required')
        self.begin=begin_frame;self._body=begin_frame.as_dict()['body'];self._chunks=[]
        self._offset=0;self._failed=False;self._finished=False
        self._sha=hashlib.sha256();self.geometry_audit_digest=None

    def _check(self,frame,kind):
        if self._failed or self._finished:raise WireFault('original snapshot transaction retired')
        if type(frame) is not ReceivedFrame or frame.message['type']!=kind:raise WireFault('snapshot message type rejected')
        for key in ('run_id','world_epoch','operation_id'):
            if frame.message[key]!=self.begin.message[key]:raise WireFault('snapshot transaction mismatch')

    def add(self,frame):
        try:
            self._check(frame,'SNAPSHOT_CHUNK');body=frame.as_dict()['body']
            if (body['freeze_id']!=self._body['freeze_identity']['freeze_id'] or _u64(body['chunk_index'])!=len(self._chunks)
                    or _u64(body['offset'])!=self._offset or len(self._chunks)>=_u64(self._body['chunk_count'])):raise WireFault('snapshot index/offset mismatch')
            raw=base64.b64decode(body['data_base64'],validate=True)
            if not raw or len(raw)!=_u64(body['decoded_length']) or len(raw)>MAX_CHUNK or self._offset+len(raw)>_u64(self._body['snapshot_bytes']):raise WireFault('snapshot chunk length overrun')
            if hashlib.sha256(raw).hexdigest()!=body['chunk_sha256']:raise WireFault('snapshot chunk SHA mismatch')
            self._chunks.append(raw);self._sha.update(raw);self._offset+=len(raw)
        except BaseException:
            self._failed=True;raise

    def finish(self,frame):
        try:
            self._check(frame,'SNAPSHOT_END');body=frame.as_dict()['body']
            if (body['freeze_identity']!=self._body['freeze_identity'] or body['snapshot_sha256']!=self._body['snapshot_sha256']
                or self._sha.hexdigest()!=self._body['snapshot_sha256'] or _u64(body['decoded_total'])!=self._offset
                or self._offset!=_u64(self._body['snapshot_bytes']) or _u64(body['chunks'])!=len(self._chunks)
                or len(self._chunks)!=_u64(self._body['chunk_count'])):raise WireFault('complete snapshot end mismatch')
            raw=b''.join(self._chunks);self.geometry_audit_digest=body['geometry_audit_digest'];self._finished=True
            return raw
        except BaseException:
            self._failed=True;raise


__all__=[]
