"""Root-only physical display hook. Import does not read files or open IO.
Original native own-pose records stay intact; only actually admitted samples
reach the reviewed B mapper/follower on the same PC QPC clock.
"""
import copy
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path,PurePosixPath
import queue
import re
import sys
import types

CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
CHILD_KEYS={'schema','requirements_sha256','operation_id','parent','predecessor','state_directory','purpose','request_sha256'}
REVIEW_KEYS={'schema','requirements_sha256','review_id','reviewer','profile','transfer','authentic_b_receipt_path','authentic_b_receipt_sha256','source_human_reference','onsite_wiring_reference','child_manifest_path','child_manifest_sha256'}
HOST_FOLLOWER_SHA256='616524111778447165778d631048059d36b488e7ddb4959aceccfd7c04613328'
ROOT_SSH_SHA256='b3c2a2edd02a298caa14f57e9e0988f276667181a9666025021d855bc960e44d'
RUNTIME_KEYS={'schema','requirements_sha256','admission_mode','world_epoch','profile_path','profile_sha256','transfer_path','transfer_sha256','review_path','review_sha256','child_manifest_path','child_manifest_sha256','child_manifest_remote_path','b_package_path','ssh_argv','limits','stderr_path','io_timeout_s'}


def need(ok,reason):
    if not ok:raise ValueError(reason)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
def sha(blob):return hashlib.sha256(blob).hexdigest()
def document(path,expected):
    path=Path(path);need(path.is_absolute() and '..' not in path.parts and not path.is_symlink(),'absolute reviewed local file required')
    data=path.read_bytes();need(0<len(data)<=2*1024*1024 and sha(data)==expected,'reviewed file hash mismatch '+str(path))
    def unique(pairs):
        out={}
        for key,value in pairs:need(key not in out,'duplicate JSON key');out[key]=value
        return out
    return json.loads(data,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def source_module(name,path,expected):
    path=Path(path);need(path.is_absolute() and sha(path.read_bytes())==expected,'reviewed source pin '+name)
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def admission_key(mode,state):
    prefix='board_request' if mode=='BOARD_PWM' else 'pc_command'
    seq=state[prefix+'_seq'];digest=state['board_receipt_sha256' if mode=='BOARD_PWM' else 'pc_command_sha256'];deadline=state['deadline_usec']
    need(type(seq) in (int,float) and seq==int(seq) and 0<int(seq)<=2**53,'actual admitted command sequence required')
    need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,'actual admitted command hash required')
    need(type(deadline) is str and deadline.isascii() and deadline.isdecimal() and str(int(deadline))==deadline,'actual native deadline required')
    return int(seq),digest,deadline

class AdmissionGate:
    def __init__(self,mode):
        need(mode in ('BOARD_PWM','PC_DIRECT'),'frozen actual admission mode');self.mode=mode;self.key=None
    def accepted(self,response):
        need(type(response) is dict and response.get('ok') is True and response.get('deferred') is not True,'actual successful native admission required')
        self.key=admission_key(self.mode,response['state'])
    def permits(self,sample):
        state=sample['native']
        if self.key is None:return False
        if state.get('fault') or state.get('ready') is not True or state.get('phase')=='ARRIVED':return False
        if state.get('admission_mode',self.mode)!=self.mode:return False
        return admission_key(self.mode,state)==self.key

def admitted_mailbox_class(base):
    class ActualAdmittedMailbox(base):
        def publish(self,actual_sample,*,world_epoch):
            need(world_epoch==self.world_epoch,'new epoch requires new physical mailbox')
            need(type(actual_sample) is dict and set(actual_sample)=={'native','host'},'original validated native state required')
            mode=actual_sample['native'].get('admission_mode')
            # BOARD794 has no mode field; actual Root admission establishes it.
            # PC_DIRECT carries a validated explicit mode. Never insert a field.
            need(mode==self.admission_mode or mode is None and self.admission_mode=='BOARD_PWM','actual frozen source mode mismatch')
            packet=dict(run_id=self.run_id,source=self.source,**copy.deepcopy(actual_sample))
            with self._condition:
                if self._closed:raise RuntimeError('closed physical mailbox cannot restart')
                self._latest=packet;self._version+=1;self._condition.notify();return self._version
    return ActualAdmittedMailbox

def validate_runtime(runtime,profile,transfer,review,child,*,mode,epoch,physical_plan):
    need(type(runtime) is dict and set(runtime)==RUNTIME_KEYS and runtime['schema']=='DEEPEYE-JOINT-PHYSICAL-RUNTIME-1078-v1' and runtime['requirements_sha256']==CONTRACT_SHA256,'exact reviewed physical runtime required')
    need(runtime['admission_mode']==mode and canonical(runtime['world_epoch'])==canonical(epoch),'physical runtime actual mode/epoch mismatch')
    source='FPGA_OUTPUT' if mode=='BOARD_PWM' else 'PC_DIRECT'
    need(type(profile) is dict and set(profile)=={'expected','run_id','source'} and profile['source']==source,'actual physical profile source mismatch')
    need(type(profile['run_id']) is str and profile['run_id'].isascii() and 0<len(profile['run_id'])<=128,'actual physical run ID required')
    need(type(child) is dict and set(child)==CHILD_KEYS and type(review) is dict and set(review)==REVIEW_KEYS,'exact eight child and twelve Root review fields required')
    expected=profile['expected'];body=dict(child);request=body.pop('request_sha256')
    need(child['schema']=='DEEPEYE-UART-CHILD-OPERATION-v1' and child['requirements_sha256']==CONTRACT_SHA256 and child['purpose']=='MOTION_READY_NO_MOTOR' and sha(canonical(body))==request,'new reviewed no-motor motion child required')
    need(transfer['scope']=='MOTION_READY' and transfer['operation_id']==child['operation_id']==expected['operation_id'],'fresh child MOTION_READY transfer required')
    need(review['reviewer']=='A Root' and review['schema']=='DEEPEYE-ROOT-UART-CHILD-TRANSFER-REVIEW-v1' and review['requirements_sha256']==CONTRACT_SHA256 and canonical(review['profile'])==canonical(profile) and canonical(review['transfer'])==canonical(transfer),'genuine Root child/profile/transfer review mismatch')
    remote=runtime['child_manifest_remote_path']
    need(type(remote) is str and remote.startswith('/') and '..' not in PurePosixPath(remote).parts and str(PurePosixPath(remote))==remote,'normalized actual PS child manifest path required')
    need(review['child_manifest_path']==remote and review['child_manifest_sha256']==runtime['child_manifest_sha256'],'reviewed PS child manifest path/hash mismatch')
    for field,parent in (('boot_id','boot_id'),('build_id','build_id'),('request_hash','request_sha256'),('bit_sha256','bit_sha256'),('hwh_sha256','hwh_sha256'),('mapping_sha256','mapping_sha256')):need(expected[field]==physical_plan[parent],'physical UART/G05 parent mismatch '+field)
    need(type(runtime['ssh_argv']) is list and runtime['ssh_argv'] and all(type(x) is str and x for x in runtime['ssh_argv']),'Root reviewed actual SSH argv required')
    need(type(runtime['limits']) is dict and type(runtime['io_timeout_s']) in (int,float) and math.isfinite(runtime['io_timeout_s']) and runtime['io_timeout_s']>0,'Root reviewed B limits/timeout required')
    need(Path(runtime['stderr_path']).is_absolute(),'new Root stderr file must be absolute')

def transport_status(snapshot):
    worker=snapshot.get('worker') or {};audit=snapshot.get('transport_audit') or {}
    closed=(worker.get('finished') is True and audit.get('transport_outcome')=='process_exited'
        and type(audit.get('returncode')) is int
        and all(audit.get(key) is True for key in ('stdin_closed','wait_completed','reader_joined','stdout_closed','stderr_closed')))
    successful=(closed and audit['returncode']==0 and audit.get('close_errors')==[]
        and worker.get('error') is None and worker.get('stop_error') is None and worker.get('close_error') is None
        and worker.get('stop_attempted') is True and worker.get('stop_reply') is not None)
    return {'transport_closed':closed,'physical_io_clean':successful,'formal_actuator_acceptance':'not_run'}

class PhysicalLink:
    def __init__(self,*,runtime_path,runtime_sha256,mode,epoch,physical_plan,owning_directory,mailbox_class,b_pins,credential_supplier,process_factory):
        need(callable(credential_supplier) and callable(process_factory),'Root must inject existing credential and process callbacks')
        runtime=document(runtime_path,runtime_sha256)
        profile=document(runtime['profile_path'],runtime['profile_sha256']);transfer=document(runtime['transfer_path'],runtime['transfer_sha256']);review=document(runtime['review_path'],runtime['review_sha256']);child=document(runtime['child_manifest_path'],runtime['child_manifest_sha256'])
        validate_runtime(runtime,profile,transfer,review,child,mode=mode,epoch=epoch,physical_plan=physical_plan)
        package=Path(runtime['b_package_path']);need(package.is_absolute(),'reviewed B package path required')
        for relative,expected in b_pins.items():need(sha((package/relative).read_bytes())==expected,'reviewed B source pin '+relative)
        sys.path[:0]=[str(package),str(package/'baseline_mtr4')]
        model=importlib.import_module('drill_live_link.model');follower=importlib.import_module('drill_live_link.follower');adapter=importlib.import_module('drill_live_link.session_client');ssh=importlib.import_module('fpga_link.ssh_client')
        for module,relative in ((model,'drill_live_link/model.py'),(follower,'drill_live_link/follower.py'),(adapter,'drill_live_link/session_client.py'),(ssh,'baseline_mtr4/fpga_link/ssh_client.py')):need(Path(module.__file__)==package/relative,'actual reviewed B API import path')
        self.api=types.SimpleNamespace(FollowMapper=model.FollowMapper,Follower=follower.Follower,SshClientAdapter=adapter.SshClientAdapter)
        self.host=source_module('root_host_follower1078',owning_directory/'joint-host-follower-1060/host_follower1060.py',HOST_FOLLOWER_SHA256)
        self.ssh=source_module('root_host_ssh1078',owning_directory/'joint-host-ssh-client-1077/root_ssh1077.py',ROOT_SSH_SHA256)
        self.runtime,self.profile,self.mode,self.epoch=runtime,profile,mode,epoch
        self._supplier,self._process_factory,self._ssh_class=credential_supplier,process_factory,ssh.SshDisplayClient
        self.mailbox=admitted_mailbox_class(mailbox_class)(run_id=profile['run_id'],world_epoch=canonical(epoch).decode('utf8'),admission_mode=mode)
        self.gate=AdmissionGate(mode);self.events=queue.SimpleQueue();self.worker=None;self.reference=None;self._closing=False;self._transport_audit=None
        self.limits=model.Limits(**runtime['limits'])
    def _event(self,event):self.events.put(event)
    def _client_factory(self):
        sink=Path(self.runtime['stderr_path']).open('xb',buffering=0);raw=None
        try:
            raw=self.ssh.RootSshDisplayClient(self._ssh_class,self.runtime['ssh_argv'],credential_supplier=self._supplier,process_factory=self._process_factory,stderr_sink=sink,timeout=self.runtime['io_timeout_s'],on_event=self._event)
            welcome=raw.open();status=welcome.get('status',{})
            need(welcome.get('declared_source')==self.profile['source'] and welcome.get('simulation') is False and welcome.get('service_event')=='uart_connected','actual connection source/simulation identity required')
            need(welcome.get('transfer_scope')=='MOTION_READY' and welcome.get('actuator_READY_authorized') is True and welcome.get('mcu_feedback_ready_observed') is True,'actual healthy reviewed motion connection required')
            need(status.get('result_code')==0 and status.get('last_joho_error')==0 and status.get('armed') is False and status.get('requested_duty_permille')==0 and status.get('yaw_feedback',{}).get('fresh') is True and status.get('pitch_feedback',{}).get('fresh') is True,'actual current READY/OFF/fresh gimbal feedback required')
            return raw
        except BaseException:
            if raw is None:sink.close()
            else:
                try:raw.close(stop_already_attempted=raw.audit['stop_attempted'])
                except BaseException as error:self._event({'event':'factory_terminal_close_error','error_type':type(error).__name__})
            raise
    def start_from_initial(self,sample):
        if self.worker is not None or self._closing:return
        state=sample['native'];need(not state['fault'] and state['running'] is False and state['speed_m_s']==0,'reference must be actual own-pose before motion')
        self.reference=copy.deepcopy(state['orientation_xyzw'])
        self.events.put({'event':'actual_initial_reference','reference_xyzw':copy.deepcopy(self.reference),'native_revision':state['revision'],'original_host':copy.deepcopy(sample['host'])})
        self.worker=self.host.HostFollower(self.mailbox,api=self.api,client_factory=self._client_factory,run_id=self.profile['run_id'],source=self.mailbox.source,reference_xyzw=self.reference,limits=self.limits,motor_enabled=False,close_client=self.ssh.close_root_ssh_client,on_event=self._event).start()
    def can_start_board(self):
        if self.worker is None or self._closing:return False
        state=self.worker.snapshot();return state.get('client_opened') is True and not state['finished'] and state['error'] is None
    def health(self):
        if self.worker is None:return
        state=self.worker.snapshot()
        if not self._closing and (state['error'] is not None or state['finished']):raise RuntimeError('PHYSICAL_WORKER_TERMINAL:'+str(state['error'] or state['reason']))
    def admitted(self,response):self.gate.accepted(response)
    def publish(self,sample):
        if self._closing or not self.gate.permits(sample):return False
        self.mailbox.publish(sample,world_epoch=canonical(self.epoch).decode('utf8'));return True
    def close(self,reason,*,wait=False):
        self._closing=True;self.mailbox.close(reason)
        if self.worker is not None:return self.worker.close(reason,wait=wait)
        return True
    def drain(self):
        while True:
            try:record=self.events.get_nowait()
            except queue.Empty:return
            if record.get('event')=='ssh_transport_closed':self._transport_audit=copy.deepcopy(record['audit'])
            yield record
    def outcome(self):return transport_status(self.snapshot())
    def snapshot(self):
        return {'enabled':True,'motor_enabled':False,'reference_xyzw':copy.deepcopy(self.reference),'worker':None if self.worker is None else self.worker.snapshot(),'transport_audit':copy.deepcopy(self._transport_audit),'formal_actuator_acceptance':'not_run'}
