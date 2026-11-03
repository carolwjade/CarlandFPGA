"""Fresh diagnostic or no-motor motion UART child on the unchanged actual physical reader1031.
Import is inert. Root alone constructs after genuine DIAG closure/B recovery.
"""
from dataclasses import asdict,replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat

REQUIREMENTS_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
PHYSICAL_READER_SHA256='d3be22472808418cc9fef164fe8ca3021987b84ecde1cef9261568155e6da57b'
SERVICE_SHA256='6404ce0b0be4b1d1f85615f083c63b6d1df9fef2bd55bbaea022a35032acab13'
CHILD_KEYS={'schema','requirements_sha256','operation_id','parent','predecessor','state_directory','purpose','request_sha256'}
PARENT_KEYS={'plan_path','plan_sha256','actual_operation_directory','load_snapshot_sha256'}
PREDECESSOR_KEYS={'operation_id','binding_sha256','events_sha256','sequence_sha256','closed_record_path','closed_record_sha256'}
# Exactly ten original1031 fields plus two child fields: twelve, not thirteen.
REVIEW_KEYS={'schema','requirements_sha256','review_id','reviewer','profile','transfer','authentic_b_receipt_path','authentic_b_receipt_sha256','source_human_reference','onsite_wiring_reference','child_manifest_path','child_manifest_sha256'}
CLOSED_KEYS={'schema','requirements_sha256','operation_id','physical_parent','state_directory','binding_sha256','events_sha256','sequence_sha256','stop','writer'}
PHYSICAL_PARENT_KEYS={'operation_id','request_sha256','boot_id','build_id','plan_sha256','load_snapshot_sha256'}
STOP_KEYS={'outcome','evidence_path','evidence_sha256'}
WRITER_KEYS={'ssh_result_path','ssh_result_sha256','ps_readback_path','ps_readback_sha256'}
PROBE_KEYS={'schema','requirements_sha256','operation_id','boot_id','state_directory','actors','lock','UART','PL'}
PURPOSE_SCOPE={'DIAGNOSTIC_ONLY':'DIAGNOSTIC_ONLY','MOTION_READY_NO_MOTOR':'MOTION_READY'}
LOCK_PROBE_KEYS={'path','device','inode','mechanism','acquire_returned','release_returned'}


def _need(ok,reason):
    if not ok:raise ValueError(reason)

def _sha(blob):return hashlib.sha256(blob).hexdigest()
def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
def _equal(a,b):return _canonical(a)==_canonical(b)
def _hex(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256 required');return value

def _op(value):
    _need(type(value) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',value) is not None,'bounded operation ID required');return value

def _text(value):
    _need(type(value) is str and 0<len(value)<=1024 and all(ord(c)>=32 for c in value),'bounded review reference required')

def _safe(value):
    path=Path(value);_need(path.is_absolute() and '..' not in path.parts,'absolute non-link path required')
    for item in (path,*path.parents):_need(not item.is_symlink(),'symlink path refused')
    return path

def _fingerprint(info):return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)

def _stable_reads(fd_before,fd_after,path_before,path_after,*,cross_ctime):
    # Preserve each API's full timestamp stability. Windows3.12 reports handle
    # ctime differently from path creation time; POSIX still requires equality.
    common=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns')
    return (_fingerprint(fd_before)==_fingerprint(fd_after)
        and _fingerprint(path_before)==_fingerprint(path_after)
        and all(getattr(fd_before,k)==getattr(path_before,k) and getattr(fd_after,k)==getattr(path_after,k) for k in common)
        and (not cross_ctime or fd_before.st_ctime_ns==path_before.st_ctime_ns and fd_after.st_ctime_ns==path_after.st_ctime_ns))

def _read(path,limit):
    path=_safe(path);path_before=path.lstat()
    with path.open('rb') as file:
        before=os.fstat(file.fileno());_need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded single-link regular evidence required')
        blob=file.read(limit+1);after=os.fstat(file.fileno())
    path_after=path.lstat()
    _need(len(blob)==before.st_size and _stable_reads(before,after,path_before,path_after,cross_ctime=os.name!='nt'),'evidence changed during read')
    return blob,_fingerprint(path_after)

def _json(blob):
    def unique(pairs):
        value={}
        for key,item in pairs:_need(key not in value,'duplicate JSON key');value[key]=item
        return value
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def _validate_child(child,plan,plan_path,plan_sha256,operation_directory):
    _need(type(child) is dict and set(child)==CHILD_KEYS,'exact eight child fields required')
    body=dict(child);request=body.pop('request_sha256');_need(_sha(_canonical(body))==_hex(request),'child request hash mismatch')
    _need(child['schema']=='DEEPEYE-UART-CHILD-OPERATION-v1' and child['requirements_sha256']==REQUIREMENTS_SHA256 and child['purpose'] in PURPOSE_SCOPE,'child schema/contract/purpose mismatch')
    _need(type(child['parent']) is dict and set(child['parent'])==PARENT_KEYS and type(child['predecessor']) is dict and set(child['predecessor'])==PREDECESSOR_KEYS,'exact parent/predecessor fields required')
    parent=child['parent'];pred=child['predecessor']
    _need(_safe(parent['plan_path'])==_safe(plan_path) and parent['plan_sha256']==_hex(plan_sha256) and _safe(parent['actual_operation_directory'])==_safe(operation_directory),'child/actual physical parent arguments mismatch')
    _hex(parent['load_snapshot_sha256'])
    _need(_safe(operation_directory)==_safe(plan['operation_parent'])/plan['operation_id'],'original physical parent operation required')
    _op(child['operation_id']);_op(pred['operation_id'])
    _need(child['operation_id'] not in (plan['operation_id'],pred['operation_id']),'fresh distinct child operation required')
    for key in ('binding_sha256','events_sha256','sequence_sha256','closed_record_sha256'):_hex(pred[key])
    _safe(pred['closed_record_path']);_safe(child['state_directory'])

def _validate_snapshot(snapshot,plan,plan_sha256,operation_directory,physical):
    _need(type(snapshot) is dict and snapshot.get('schema')=='DEEPEYE-ACTUAL-LOADED-SNAPSHOT-1037-v1' and snapshot.get('requirements_sha256')==REQUIREMENTS_SHA256,'actual original load snapshot required')
    _need(snapshot.get('contract')=='DEEPEYE-HUMAN-LOCK-20261014/revision2' and snapshot.get('evidence_kind')=='measured_load_snapshot_only','snapshot evidence boundary mismatch')
    for key in ('operation_id','request_sha256','boot_id','build_id','source_commit','bit_sha256','hwh_sha256','mapping_sha256','baseline_hwh_sha256'):_need(snapshot.get(key)==plan[key],'snapshot/physical plan mismatch '+key)
    _need(snapshot.get('approved_plan_sha256')==plan_sha256 and _safe(snapshot['operation_directory'])==_safe(operation_directory),'snapshot approved parent mismatch')
    _need(physical['operation_id']==plan['operation_id'] and physical['request_hash']==plan['request_sha256'] and physical['boot_id']==plan['boot_id'] and physical['build_id']==plan['build_id'],'actual physical parent binding mismatch')
    _need(snapshot.get('fclk_hz')==physical['fclk_hz']==50000000 and snapshot.get('product_clock_net')==physical['product_clock_net'] and snapshot.get('product_reset_net')==physical['product_reset_net'],'snapshot/current clock/reset mismatch')
    ips=[{'instance':physical[name]['name'],'type':physical[name]['vlnv'],'phys_addr':physical[name]['phys_addr'],'addr_range':physical[name]['addr_range']} for name in ('g05','trace','uart')]
    _need(_equal(snapshot.get('ips'),ips),'snapshot/current three IPs mismatch')
    _need(_equal(snapshot.get('uart'),{key:physical['uart'][key] for key in ('baud','clock_hz','clock_net','data_bits','parity','reset_net','stop_bits')}),'snapshot/current UART metadata mismatch')
    _need(snapshot.get('G05_off') is True and snapshot.get('UART_accessed') is False and snapshot.get('MCU_frame_sent') is False,'original physical snapshot scope mismatch')
    _need(snapshot.get('raw_csr',{}).get('g05',{}).get('0x08')==0 and snapshot.get('raw_csr',{}).get('g05',{}).get('0x10')==0,'snapshot G05 OFF/fault mismatch')

def _validate_closed(closed,child,plan,plan_sha256):
    _need(type(closed) is dict and set(closed)==CLOSED_KEYS,'exact ten predecessor close fields required')
    _need(closed['schema']=='DEEPEYE-ROOT-UART-PREDECESSOR-CLOSED-v1' and closed['requirements_sha256']==REQUIREMENTS_SHA256,'predecessor close contract mismatch')
    pred=child['predecessor'];_need(closed['operation_id']==pred['operation_id'] and _safe(closed['state_directory'])==_safe(child['state_directory']),'closed predecessor/state mismatch')
    expected_parent={'operation_id':plan['operation_id'],'request_sha256':plan['request_sha256'],'boot_id':plan['boot_id'],'build_id':plan['build_id'],'plan_sha256':plan_sha256,'load_snapshot_sha256':child['parent']['load_snapshot_sha256']}
    _need(type(closed['physical_parent']) is dict and set(closed['physical_parent'])==PHYSICAL_PARENT_KEYS and _equal(closed['physical_parent'],expected_parent),'closed physical parent mismatch')
    for key in ('binding_sha256','events_sha256','sequence_sha256'):_need(closed[key]==pred[key],'closed final journal hash mismatch '+key)
    _need(type(closed['stop']) is dict and set(closed['stop'])==STOP_KEYS and closed['stop']['outcome'] in ('ACKNOWLEDGED','UNCERTAIN','NOT_ISSUED'),'actual STOP outcome or uncertainty required')
    _safe(closed['stop']['evidence_path']);_hex(closed['stop']['evidence_sha256'])
    _need(type(closed['writer']) is dict and set(closed['writer'])==WRITER_KEYS,'actual writer proof references required')
    for name in ('ssh_result','ps_readback'):_safe(closed['writer'][name+'_path']);_hex(closed['writer'][name+'_sha256'])

def _validate_writer_proofs(ssh,probe,child,plan,lock_identity):
    _need(type(ssh) is dict and type(ssh.get('returncode')) is int and 0<=ssh['returncode']<=255 and ssh.get('wait_confirmed') is True and ssh.get('reader_thread_stopped') is True and ssh.get('automatic_retry') is False,'actual waited SSH termination and stopped reader required')
    _need(type(probe) is dict and set(probe)==PROBE_KEYS and probe['schema']=='DEEPEYE-ROOT-UART-PS-CLOSED-READBACK-v1' and probe['requirements_sha256']==REQUIREMENTS_SHA256,'actual PS close probe required')
    _need(probe['operation_id']==child['predecessor']['operation_id'] and probe['boot_id']==plan['boot_id'] and _safe(probe['state_directory'])==_safe(child['state_directory']),'PS close probe generation/state mismatch')
    _need(type(probe['actors']) is list and not probe['actors'] and probe['UART'] is False and probe['PL'] is False,'actual PS readback must observe no UART actors without UART or PL effects')
    lock=probe['lock'];_need(type(lock) is dict and set(lock)==LOCK_PROBE_KEYS,'actual lock probe fields required')
    _need(_safe(lock['path'])==_safe(child['state_directory'])/'mcu_uart.owner.lock' and type(lock['device']) is int and type(lock['inode']) is int and (lock['device'],lock['inode'])==lock_identity,'same persistent hardware lock required')
    _need(lock['mechanism']=='fcntl.flock(LOCK_EX|LOCK_NB)' and lock['acquire_returned'] is True and lock['release_returned'] is True,'actual acquired and released OS lock probe required')

def _validate_child_review(review,profile,transfer,manifest_path,manifest_sha256,purpose):
    _need(type(review) is dict and set(review)==REVIEW_KEYS,'exact twelve child review fields required')
    _need(review['schema']=='DEEPEYE-ROOT-UART-CHILD-TRANSFER-REVIEW-v1' and review['requirements_sha256']==REQUIREMENTS_SHA256 and review['reviewer']=='A Root','child Root review contract mismatch')
    for key in ('review_id','source_human_reference','onsite_wiring_reference'):_text(review[key])
    _need(_safe(review['child_manifest_path'])==_safe(manifest_path) and review['child_manifest_sha256']==manifest_sha256,'reviewed child manifest mismatch')
    _need(_equal(review['profile'],profile) and _equal(review['transfer'],transfer) and transfer['scope']==PURPOSE_SCOPE[purpose],'exact reviewed child purpose/scope transfer required')
    _safe(review['authentic_b_receipt_path']);_hex(review['authentic_b_receipt_sha256'])

def _validate_stop_outcome(outcome,terminal):
    if outcome=='ACKNOWLEDGED':
        _need(terminal is not None and terminal['event']=='terminal_stop_result','actual terminal STOP result required')
        status=terminal['result'].get('status',{});_need(status.get('armed') is False and type(status.get('requested_duty_permille')) is int and status['requested_duty_permille']==0,'terminal STOP must report disarmed/OFF')
    elif outcome=='UNCERTAIN':_need(terminal is None or terminal['event']=='terminal_stop_error','STOP uncertainty must remain uncertain')
    else:_need(outcome=='NOT_ISSUED' and terminal is None,'NOT_ISSUED cannot replace actual STOP evidence')

def _validate_fresh_transfer(transfer,old,child_id,purpose):
    _need(transfer['operation_id']==child_id and transfer['scope']==PURPOSE_SCOPE[purpose],'exact child purpose and transfer scope required')
    _need(all(transfer[key]!=old[key] for key in ('transfer_id','mcu_observation_id','evidence_sha256')),'genuine fresh B transfer and observation required')


def _journal(path,expected,operation_id):
    path=_safe(path);path_before=path.lstat();digest=hashlib.sha256();count=0;consumption=None;terminal=None;last_ns=-1
    with path.open('rb') as file:
        before=os.fstat(file.fileno());_need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size>0,'actual final UART journal required')
        while True:
            line=file.readline(2*1024*1024+1)
            if not line:break
            digest.update(line);_need(0<len(line)<=2*1024*1024,'bounded audit JSON line required');value=_json(line)
            _need(type(value) is dict and value.get('operation_id')==operation_id and value.get('simulation') is False and value.get('requirements_sha256')==REQUIREMENTS_SHA256,'actual predecessor audit identity mismatch')
            tick=value.get('monotonic_ns');_need(type(tick) is int and tick>=last_ns,'audit monotonic order');last_ns=tick;count+=1
            if value.get('event')=='transfer_consumption_intent':_need(consumption is None,'one predecessor transfer consumption');consumption={'profile':value['profile'],'transfer':value['transfer']}
            if value.get('event') in ('terminal_stop_result','terminal_stop_error'):terminal=value
        after=os.fstat(file.fileno())
    path_after=path.lstat()
    _need(count>0 and digest.hexdigest()==_hex(expected) and _stable_reads(before,after,path_before,path_after,cross_ctime=os.name!='nt'),'final UART journal hash/stability mismatch')
    return consumption,terminal,_fingerprint(path_after)


def build_actual_reader(service_api,*,approved_plan_path,approved_plan_sha256,actual_operation_directory,transfer_review_path,transfer_review_sha256,child_manifest_path,child_manifest_sha256):
    """Fresh child reader. No PL load, state deletion, B recovery or UART command.
    Frozen physical reader1031 performs all original actual constructor checks.
    """
    _need(os.name=='posix' and os.geteuid()==0 and os.uname().machine=='armv7l','actual root armv7l PS constructor required')
    root_path=_safe(Path(__file__).parent);base_path=root_path/'root_loaded_product1031.py'
    base_blob,base_identity=_read(base_path,1024*1024);_need(_sha(base_blob)==PHYSICAL_READER_SHA256,'unchanged physical reader1031 pin required')
    base=importlib.import_module('root_loaded_product1031');_need(Path(base.__file__)==base_path,'fresh staged physical reader required')
    service_blob,service_identity=_read(service_api.__file__,1024*1024);_need(_sha(service_blob)==SERVICE_SHA256,'unchanged service6404 required')
    manifest_path=_safe(child_manifest_path);manifest_blob,manifest_identity=_read(manifest_path,131072)
    _need(_sha(manifest_blob)==_hex(child_manifest_sha256),'child manifest file hash mismatch');child=_json(manifest_blob)
    plan_blob,plan_identity=_read(approved_plan_path,131072);_need(_sha(plan_blob)==_hex(approved_plan_sha256),'actual approved parent plan hash mismatch');plan=_json(plan_blob)
    _validate_child(child,plan,approved_plan_path,approved_plan_sha256,actual_operation_directory)
    physical=base.build_actual_reader(service_api,approved_plan_path=approved_plan_path,approved_plan_sha256=approved_plan_sha256,actual_operation_directory=actual_operation_directory,transfer_review_path=transfer_review_path,transfer_review_sha256=transfer_review_sha256)

    class ChildRootLoadedProduct(service_api.RootLoadedProduct):
        @property
        def simulation(self):return False

        @property
        def state_directory(self):return _safe(self._child['state_directory'])

        def __init__(self):
            self._physical=physical;self._child=child;self._plan=plan;self._poisoned=False;self._authorized=None;self._uart_mmio=None
            self._watches={base_path:base_identity,_safe(service_api.__file__):service_identity,manifest_path:manifest_identity,_safe(approved_plan_path):plan_identity}
            def pinned(path,expected,limit=131072):
                blob,identity=_read(path,limit);_need(_sha(blob)==_hex(expected),'pinned child evidence hash mismatch '+str(path));self._watches[_safe(path)]=identity;return blob
            self._snapshot=_json(pinned(_safe(actual_operation_directory)/'actual_loaded_snapshot.json',child['parent']['load_snapshot_sha256']))
            actual=asdict(physical.read_current());_validate_snapshot(self._snapshot,plan,approved_plan_sha256,actual_operation_directory,actual)
            state=_safe(child['state_directory']);_need(state.is_dir(),'same existing hardware state directory required')
            pred=child['predecessor'];run=state/'operations'/_sha(pred['operation_id'].encode('ascii'))
            binding_blob=pinned(run/'binding.json',pred['binding_sha256']);binding=_json(binding_blob)
            _need(type(binding) is dict and set(binding)=={'profile','transfer'},'actual predecessor binding required')
            expected=dict(actual,operation_id=pred['operation_id'])
            _need(type(binding['profile']) is dict and set(binding['profile'])=={'expected','run_id','source'} and _equal(binding['profile']['expected'],expected),'predecessor binding must share actual physical parent')
            old_transfer=service_api.BTransfer(**binding['transfer']);old_transfer.validate()
            _need(old_transfer.operation_id==pred['operation_id'] and old_transfer.scope=='DIAGNOSTIC_ONLY','actual predecessor must be DIAGNOSTIC_ONLY')
            self._predecessor_transfer=old_transfer
            sequence=_json(pinned(run/'sequence.json',pred['sequence_sha256']))
            _need(type(sequence) is dict and set(sequence)=={'next_seq'} and type(sequence['next_seq']) is int and 1<=sequence['next_seq']<=0x100000000,'actual final predecessor sequence required')
            consumed=state/'consumed-transfers'/(old_transfer.evidence_sha256+'.json')
            _need(pinned(consumed,pred['binding_sha256'])==binding_blob,'actual consumed predecessor transfer record required')
            consumption,terminal,journal_identity=_journal(run/'uart-events.jsonl',pred['events_sha256'],pred['operation_id']);self._watches[run/'uart-events.jsonl']=journal_identity
            _need(_equal(consumption,binding),'final audit must show actual predecessor transfer consumption')
            closed=_json(pinned(pred['closed_record_path'],pred['closed_record_sha256']));_validate_closed(closed,child,plan,approved_plan_sha256)
            pinned(closed['stop']['evidence_path'],closed['stop']['evidence_sha256'],8*1024*1024)
            _validate_stop_outcome(closed['stop']['outcome'],terminal)
            writer=closed['writer'];ssh=_json(pinned(writer['ssh_result_path'],writer['ssh_result_sha256']));probe=_json(pinned(writer['ps_readback_path'],writer['ps_readback_sha256']))
            lock_path=_safe(state/'mcu_uart.owner.lock');lock_info=lock_path.lstat();_need(stat.S_ISREG(lock_info.st_mode) and lock_info.st_nlink==1,'original persistent lock file required')
            _validate_writer_proofs(ssh,probe,child,plan,(lock_info.st_dev,lock_info.st_ino))
            self._watches[lock_path]=_fingerprint(lock_info)
            child_run=state/'operations'/_sha(child['operation_id'].encode('ascii'));_need(not child_run.exists(),'fresh child operation already exists; no replay')
            self.read_current()

        def read_current(self):
            try:
                _need(not self._poisoned,'child identity uncertainty latched')
                actual=self._physical.read_current()
                for path,identity in self._watches.items():_safe(path);_need(_fingerprint(path.lstat())==identity,'child evidence changed '+str(path))
                _validate_snapshot(self._snapshot,self._plan,approved_plan_sha256,actual_operation_directory,asdict(actual))
                if self._uart_mmio is None:
                    _need(int(self._physical._g05.read(8))==0 and int(self._physical._g05.read(0x10))==0,'actual G05 must be OFF/status0/fault0 before child attach')
                result=replace(actual,operation_id=self._child['operation_id']);result.validate()
                _need(result.request_hash==actual.request_hash,'child must preserve actual physical request hash')
                return result
            except BaseException:self._poisoned=True;raise

        def read_hwh_bytes(self):
            self.read_current();return self._physical.read_hwh_bytes()

        def authorize_transfer(self,profile,transfer):
            _need(type(profile) is service_api.Profile and type(transfer) is service_api.BTransfer,'exact typed profile and transfer required')
            profile.validate();transfer.validate();actual=self.read_current()
            _need(profile.expected==actual and transfer.operation_id==actual.operation_id and transfer.scope==PURPOSE_SCOPE[child['purpose']],'current child purpose/scope transfer required')
            old=self._predecessor_transfer
            _validate_fresh_transfer(asdict(transfer),asdict(old),child['operation_id'],child['purpose'])
            blob,identity=_read(transfer_review_path,131072);_need(_sha(blob)==_hex(transfer_review_sha256),'SHA-pinned child Root review required')
            review=_json(blob);_validate_child_review(review,asdict(profile),asdict(transfer),manifest_path,child_manifest_sha256,child['purpose'])
            receipt_path=_safe(review['authentic_b_receipt_path']);receipt,receipt_identity=_read(receipt_path,8*1024*1024)
            _need(_sha(receipt)==review['authentic_b_receipt_sha256'],'genuine fresh B receipt hash mismatch')
            consumed=_safe(child['state_directory'])/'consumed-transfers'/(transfer.evidence_sha256+'.json');_need(not consumed.exists(),'B evidence was already consumed; no replay')
            self._watches[_safe(transfer_review_path)]=identity;self._watches[receipt_path]=receipt_identity
            self._authorized=(profile,transfer,transfer_review_sha256)

        def authorize_motor(self,profile,transfer):
            raise service_api.ServiceError('first child adapter has no motor release; separate actual Root trial/release review required')

        def open_uart_mmio(self,binding):
            _need(type(binding) is service_api.ProductBinding and self._authorized is not None,'reviewed typed child binding required')
            actual=self.read_current()
            _need(binding==actual==self._authorized[0].expected and self._authorized[1].scope==PURPOSE_SCOPE[child['purpose']],'current reviewed child UART binding mismatch')
            _need(self._uart_mmio is None,'one fresh child UART mapping only')
            self._uart_mmio=self._physical._MMIO(actual.uart.phys_addr,actual.uart.addr_range,device=self._physical._device)
            return self._uart_mmio

    return ChildRootLoadedProduct()
