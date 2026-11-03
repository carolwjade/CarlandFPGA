"""Root-only already-loaded joint product reader. Import has no device effects.

Construction is explicit on root armv7l PS. This module never loads PL, changes
clocks or writes UART. First adapter authorizes DIAGNOSTIC_ONLY transfers only.
"""
from dataclasses import asdict
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import threading
import types
import uuid
import xml.etree.ElementTree as ET

REQUIREMENTS_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
SERVICE_SHA256='6404ce0b0be4b1d1f85615f083c63b6d1df9fef2bd55bbaea022a35032acab13'
LOADER_SHA256='478ee99fa753f2050812c7aec5655ba286004b8262565a5304dad7c2dc8705c7'
HELPER_SHA256='865a857c2455a9cc0254db54eb7b8c71cb16f5416bb299b2711cd9151649268d'
VERIFIER_SHA256='d8a96c5e6c277b8608b89e22bba49fae7425e331af79dfa2d9c14be437550a24'
BASELINE_SHA256='73a64f2d19e8d13c70af0150eef71bc3092825f95a8481ba0fb4e71ae55c2e5b'
PLAN_KEYS={'operation_id','request_sha256','build_id','source_commit','boot_id','bit_path','hwh_path','mapping_path','bit_sha256','hwh_sha256','mapping_sha256','operation_parent','baseline_hwh_path','baseline_hwh_sha256'}
REVIEW_KEYS={'schema','requirements_sha256','review_id','reviewer','profile','transfer','authentic_b_receipt_path','authentic_b_receipt_sha256','source_human_reference','onsite_wiring_reference'}
IP_NAMES=('g05_50_0','trace50_0','mcu_uart')


def _need(ok,reason):
    if not ok:raise ValueError(reason)

def _sha(blob):return hashlib.sha256(blob).hexdigest()

def _hex(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256 required')
    return value

def _text(value):
    _need(type(value) is str and 0<len(value)<=1024 and all(ord(c)>=32 for c in value),'bounded review reference required')
    return value

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')

def _json(blob):
    def unique(pairs):
        value={}
        for key,item in pairs:
            _need(key not in value,'duplicate JSON key');value[key]=item
        return value
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def _safe_path(value):
    path=Path(value)
    _need(path.is_absolute() and '..' not in path.parts,'absolute non-link path required')
    for item in (path,*path.parents):_need(not item.is_symlink(),'symlink path refused')
    return path

def _fingerprint(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)

def _read_regular(value,limit):
    path=_safe_path(value)
    with path.open('rb') as handle:
        before=os.fstat(handle.fileno())
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded single-link regular file required')
        blob=handle.read(limit+1);after=os.fstat(handle.fileno())
    _need(len(blob)==before.st_size and _fingerprint(before)==_fingerprint(after)==_fingerprint(path.lstat()),'file changed during read')
    return blob,_fingerprint(after)

def _validate_review(record,profile_value,transfer_value):
    """Pure structure comparison only. It never grants a live capability."""
    _need(type(record) is dict and set(record)==REVIEW_KEYS,'exact Root review fields required')
    _need(record['schema']=='DEEPEYE-ROOT-DIAGNOSTIC-TRANSFER-REVIEW-v1' and record['requirements_sha256']==REQUIREMENTS_SHA256,'Root review contract mismatch')
    _need(record['reviewer']=='A Root','Root review owner mismatch')
    for key in ('review_id','source_human_reference','onsite_wiring_reference'):_text(record[key])
    _hex(record['authentic_b_receipt_sha256']);_safe_path(record['authentic_b_receipt_path'])
    _need(_canonical(record['profile'])==_canonical(profile_value) and _canonical(record['transfer'])==_canonical(transfer_value),'review/typed transfer or profile mismatch')
    _need(transfer_value['scope']=='DIAGNOSTIC_ONLY','first reader permits DIAGNOSTIC_ONLY only')


def _hwh_uart_context(blob,helper):
    """Read-only extraction from actual validated HWH bytes, no device access."""
    _need(type(blob) is bytes and 0<len(blob)<=8*1024*1024 and b'\x00' not in blob and not re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b',blob,re.I),'bounded plain HWH bytes required')
    root=ET.fromstring(blob)
    def module(name):return helper._one((m for m in root.findall('./MODULES/MODULE') if m.get('INSTANCE')==name),name)
    def port(obj,name):return helper._one((p for p in obj.findall('./PORTS/PORT') if p.get('NAME')==name),name)
    g05=module(IP_NAMES[0]);uart=module(IP_NAMES[2]);up=helper._params(uart)
    gclk=port(g05,'s_axi_aclk');grst=port(g05,'s_axi_aresetn');uclk=port(uart,'s_axi_aclk');urst=port(uart,'s_axi_aresetn')
    clock_net=gclk.get('SIGNAME');reset_net=grst.get('SIGNAME')
    _need(clock_net and reset_net and clock_net==uclk.get('SIGNAME') and reset_net==urst.get('SIGNAME') and grst.get('POLARITY')==urst.get('POLARITY')=='ACTIVE_LOW','actual shared product clock/reset required')
    trace=module(IP_NAMES[1]);tclk=port(trace,'s_axi_aclk');trst=port(trace,'s_axi_aresetn')
    _need(tclk.get('SIGNAME')==clock_net and trst.get('SIGNAME')==reset_net and trst.get('POLARITY')=='ACTIVE_LOW','actual TRACE clock/reset mismatch')
    fields={'clock_hz':helper._integer(up['C_S_AXI_ACLK_FREQ_HZ']),'baud':helper._integer(up['C_BAUDRATE']),'data_bits':helper._integer(up['C_DATA_BITS']),'parity':bool(helper._integer(up['C_USE_PARITY'])),'stop_bits':1,'clock_net':uclk.get('SIGNAME'),'reset_net':urst.get('SIGNAME')}
    _need(helper._integer(uclk.get('CLKFREQUENCY'))==fields['clock_hz']==50000000 and helper._integer(up['C_ODD_PARITY'])==0 and fields['baud']==115200 and fields['data_bits']==8 and fields['parity'] is False,'actual UART 50MHz1152008N1 mismatch')
    return clock_net,reset_net,fields


def build_actual_reader(service_api,*,approved_plan_path,approved_plan_sha256,actual_operation_directory,transfer_review_path,transfer_review_sha256):
    """Construct one foreground PS reader; caller is the sole authorized A Root.

    service_api must be the actual SHA-pinned B module, with its exact typed API.
    A missing future transfer review does not block read-only construction but
    always blocks authorize_transfer and opening UART. No synthetic fallback.
    """
    _need(type(service_api) is types.ModuleType,'actual service module required')
    _hex(approved_plan_sha256);_hex(transfer_review_sha256)
    review_path=_safe_path(transfer_review_path)
    source_root=_safe_path(Path(__file__).parent)
    service_blob,_=_read_regular(service_api.__file__,1024*1024)
    _need(_sha(service_blob)==SERVICE_SHA256,'service source pin mismatch')
    for name in ('ProductBinding','IpDescriptor','UartDescriptor','Profile','BTransfer','RootLoadedProduct'):
        value=getattr(service_api,name,None)
        _need(isinstance(value,type) and value.__module__==service_api.__name__,'exact service API class required '+name)

    class ActualRootLoadedProduct(service_api.RootLoadedProduct):
        @property
        def simulation(self):return False

        def __init__(self):
            _need(os.name=='posix' and os.geteuid()==0 and os.uname().machine=='armv7l','actual root armv7l PS constructor required')
            self._pid=os.getpid();self._thread=threading.get_ident();self._poisoned=False
            self._watches={};self._authorized=None;self._uart_mmio=None
            def pinned(path,limit,expected):
                blob,identity=_read_regular(path,limit);_need(_sha(blob)==_hex(expected),'pinned file hash mismatch '+str(path))
                self._watches[_safe_path(path)]=identity;return blob
            plan_blob=pinned(approved_plan_path,131072,approved_plan_sha256);plan=_json(plan_blob)
            _need(type(plan) is dict and set(plan)==PLAN_KEYS,'exact joint loader plan required')
            body=dict(plan);request=body.pop('request_sha256')
            _need(_sha(_canonical(body))==_hex(request),'approved plan request hash mismatch')
            _need(type(plan['operation_id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',plan['operation_id']) is not None,'operation ID')
            _need(type(plan['build_id']) is str and re.fullmatch('[0-9a-f]{32}',plan['build_id']) is not None and int(plan['build_id'],16)>0,'BUILD_ID')
            _need(type(plan['source_commit']) is str and re.fullmatch('[0-9a-f]{40}',plan['source_commit']) is not None,'source commit')
            _need(str(uuid.UUID(plan['boot_id']))==plan['boot_id'],'BOOT UUID')
            _need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==plan['boot_id'],'constructor BOOT mismatch')
            _need(plan['baseline_hwh_sha256']==BASELINE_SHA256,'original baseline pin required')
            operation=_safe_path(actual_operation_directory)
            _need(operation==_safe_path(plan['operation_parent'])/plan['operation_id'] and operation.is_dir(),'exact original Root operation directory required')
            self._plan=plan;self._operation=operation
            def record(name,limit=131072):
                path=operation/name;blob,identity=_read_regular(path,limit);self._watches[path]=identity;return _json(blob)
            started=record('operation-started.json');loaded=record('load-started.json');returned=record('load-returned.json');clock=record('clock-readback.json')
            _need(type(started) is dict and set(started)=={'operation_id','request_sha256','build_id','boot_id','source_commit','pid','monotonic_ns'},'original operation-started record required')
            for key in ('operation_id','request_sha256','build_id','boot_id','source_commit'):_need(started[key]==plan[key],'operation provenance mismatch '+key)
            _need(type(started['pid']) is int and started['pid']>0 and type(started['monotonic_ns']) is int and started['monotonic_ns']>0,'original start metadata')
            _need(type(loaded) is dict and loaded=={key:plan[key] for key in ('bit_sha256','hwh_sha256','build_id')},'original load-started identity required')
            _need(type(returned) is dict and set(returned)=={'monotonic_ns'} and type(returned['monotonic_ns']) is int and returned['monotonic_ns']>started['monotonic_ns'],'actual load-returned record required')
            _need(type(clock) is dict and set(clock)=={'source','pll_fdiv','div0','div1','other'},'actual clock-readback record required')
            _need(all(type(clock[key]) is int for key in ('source','pll_fdiv','div0','div1')) and [clock[key] for key in ('source','pll_fdiv','div0','div1')]==[0,20,10,2],'recorded product clock mismatch')
            _need(type(clock['other']) is list and len(clock['other'])==3 and all(type(x) is int and 0<=x<=0xffffffff for x in clock['other']),'recorded other PS clocks')
            self._clock_record=clock
            stem='functional50_'+request[:24]
            bit_path=operation/(stem+'.bit');hwh_path=operation/(stem+'.hwh')
            pinned(bit_path,16*1024*1024,plan['bit_sha256'])
            self._hwh_bytes=pinned(hwh_path,8*1024*1024,plan['hwh_sha256'])
            mapping_blob=pinned(plan['mapping_path'],131072,plan['mapping_sha256']);mapping=_json(mapping_blob)
            pinned(plan['baseline_hwh_path'],8*1024*1024,BASELINE_SHA256)
            for name,expected in (('load_once_joint50_1024.py',LOADER_SHA256),('verify_uart_joint50_hwh.py',VERIFIER_SHA256)):
                pinned(source_root/name,1024*1024,expected)
            helper_path=source_root/'snapshot/competition/deepeye/tools/diagnostic/functional50_board_a.py'
            pinned(helper_path,1024*1024,HELPER_SHA256)
            loader=importlib.import_module('load_once_joint50_1024')
            helper=importlib.import_module('competition.deepeye.tools.diagnostic.functional50_board_a')
            verifier=importlib.import_module('verify_uart_joint50_hwh')
            _need(Path(loader.__file__)==source_root/'load_once_joint50_1024.py' and Path(helper.__file__)==helper_path and Path(verifier.__file__)==source_root/'verify_uart_joint50_hwh.py','fresh staged imported source paths required')
            verified=loader.validated_joint_descriptors(hwh_path,mapping,plan['build_id'],plan['baseline_hwh_path'])
            _need(verified['hwh_sha256']==plan['hwh_sha256'] and verified['baseline_hwh_sha256']==BASELINE_SHA256,'actual staged HWH mismatch')
            self._validated=verified['windows'];_need(tuple(d['instance'] for d in self._validated)==IP_NAMES,'three ordered validated IPs required')
            self._clock_net,self._reset_net,self._uart_fields=_hwh_uart_context(self._hwh_bytes,helper)
            from pynq import Clocks,Device,MMIO
            from pynqmetadata.frontends import Metadata
            from pynq.metadata.runtime_metadata_parser import RuntimeMetadataParser
            from pynq.pl_server.embedded_device import EmbeddedDevice,_create_xclbin,_unify_dictionaries
            from pynq.pl_server.xclbin_parser import XclBin
            self._clocks=Clocks;self._MMIO=MMIO;self._ps=helper._ps;self._Device=Device;self._device=Device.active_device
            self._ps(Clocks)
            _need(type(self._device) is EmbeddedDevice and Clocks._instance._slcr_mmio.device is self._device,'same actual PS embedded device required')
            self._parser=RuntimeMetadataParser(Metadata(input=hwh_path))
            xdata=_create_xclbin(self._parser.mem_dict);_unify_dictionaries(self._parser,XclBin(xclbin_data=xdata));self._parser.refresh_hierarchy_dict()
            ips=self._current_ips()
            self._g05=MMIO(ips[0].phys_addr,ips[0].addr_range,device=self._device)
            self._trace=MMIO(ips[1].phys_addr,ips[1].addr_range,device=self._device)
            self.read_current()

        def _assert_owner(self):
            _need(not self._poisoned and os.getpid()==self._pid and threading.get_ident()==self._thread,'one original foreground PS reader required')
            _need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==self._plan['boot_id'],'current BOOT mismatch')
            for path,identity in self._watches.items():
                _safe_path(path);_need(_fingerprint(path.lstat())==identity,'pinned identity file changed '+str(path))

        def _current_ips(self):
            result=[]
            for wanted in self._validated:
                name=wanted['instance'];matches=[(key,obj) for key,obj in self._parser.ip_dict.items() if key.strip('/')==name or str(obj.get('fullpath','')).strip('/')==name]
                _need(len(matches)==1,'actual parser IP must be unique '+name)
                key,obj=matches[0];actual_name=str(obj.get('fullpath') or key).strip('/')
                actual=service_api.IpDescriptor(actual_name,obj.get('type'),int(obj['phys_addr']),int(obj['addr_range']));actual.validate()
                _need(actual.name==name and actual.vlnv==wanted['type'] and actual.phys_addr==wanted['phys_addr'] and actual.addr_range==wanted['addr_range']==4096,'actual parser descriptor mismatch '+name)
                result.append(actual)
            return tuple(result)

        def read_current(self):
            try:
                self._assert_owner();plan=self._plan;observed=self._ps(self._clocks)
                _need(self._Device.active_device is self._device and self._clocks._instance._slcr_mmio.device is self._device,'original owned PS device context changed')
                _need(all(type(observed[key]) is int for key in ('source','pll_fdiv','div0','div1')) and [observed[key] for key in ('source','pll_fdiv','div0','div1')]==[0,20,10,2],'actual live PS clock mismatch')
                _need(tuple(observed['other'])==tuple(self._clock_record['other']),'other live PS clocks changed')
                fclk=50000000*observed['pll_fdiv']//(observed['div0']*observed['div1']);_need(fclk==50000000,'actual product FCLK mismatch')
                for offset,wanted in ((0,0x54353046),(4,1),(8,4),(12,50000000),(16,1000000),(20,4096)):
                    _need(int(self._trace.read(offset))==wanted,'actual TRACE identity mismatch')
                words=[int(self._trace.read(0x60+4*i)) for i in range(4)]
                _need(all(0<=x<=0xffffffff for x in words),'actual TRACE build word range')
                build=''.join(format(x,'08x') for x in reversed(words));_need(build==plan['build_id'],'actual TRACE BUILD_ID mismatch')
                _need(int(self._g05.read(0))==0x47303550 and int(self._g05.read(4))==2,'actual G05 identity mismatch')
                ips=self._current_ips();uart=service_api.UartDescriptor(ips[2].name,ips[2].vlnv,ips[2].phys_addr,ips[2].addr_range,**self._uart_fields)
                actual=service_api.ProductBinding(plan['operation_id'],plan['request_sha256'],plan['boot_id'],build,plan['bit_sha256'],plan['hwh_sha256'],plan['mapping_sha256'],fclk,ips[0],ips[1],self._clock_net,self._reset_net,uart)
                actual.validate();return actual
            except BaseException:
                self._poisoned=True;raise

        def read_hwh_bytes(self):
            self.read_current()
            return self._hwh_bytes

        def authorize_transfer(self,profile,transfer):
            _need(type(profile) is service_api.Profile and type(transfer) is service_api.BTransfer,'exact typed profile and B transfer required')
            profile.validate();transfer.validate();actual=self.read_current()
            _need(profile.expected==actual and transfer.operation_id==actual.operation_id,'current typed transfer binding mismatch')
            blob,identity=_read_regular(review_path,131072)
            _need(_sha(blob)==transfer_review_sha256,'SHA-pinned Root review required')
            review=_json(blob);_validate_review(review,asdict(profile),asdict(transfer))
            receipt_path=_safe_path(review['authentic_b_receipt_path']);receipt,receipt_identity=_read_regular(receipt_path,8*1024*1024)
            _need(_sha(receipt)==review['authentic_b_receipt_sha256'],'retained authentic B receipt hash mismatch')
            self._watches[review_path]=identity;self._watches[receipt_path]=receipt_identity
            self._authorized=(profile,transfer,transfer_review_sha256)

        def authorize_motor(self,profile,transfer):
            raise service_api.ServiceError('first Root adapter has no motor authorization; DIAGNOSTIC_ONLY only')

        def open_uart_mmio(self,binding):
            _need(type(binding) is service_api.ProductBinding and self._authorized is not None,'reviewed exact typed UART binding required')
            actual=self.read_current()
            _need(binding==actual==self._authorized[0].expected and self._authorized[1].scope=='DIAGNOSTIC_ONLY','current reviewed UART identity mismatch')
            _need(self._uart_mmio is None,'one UART mapping only; no automatic reuse')
            self._uart_mmio=self._MMIO(actual.uart.phys_addr,actual.uart.addr_range,device=self._device)
            return self._uart_mmio

    return ActualRootLoadedProduct()
