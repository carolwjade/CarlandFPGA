"""A-only functional50 board entry. Import is inert; no board call at import.

Run only after Root independent review and same-build/owner clearance. An input
plan and this module do not themselves authorize any hardware operation.
"""
import hashlib
import json
import os
import re
import stat
import sys
import time
import threading
import uuid
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

READS = frozenset((0,4,8,12,16,20,0x18,0x1c,0x20,0x24,0x28,0x2c,0x30,0x34,0x38,0x40,0x44,0x48,0x4c,0x50,0x60,0x64,0x68,0x6c,0x70,0x7c))
WRITES = frozenset((0x80,0x100,0x104,0x108,0x110,0x114,0x118,0x11c,0x120,*range(0x130,0x158,4),0x160,0x164))
IDENTITY = {0:0x54353046,4:1,8:4,12:50000000,16:1000000,20:4096}
VLNVS = {'g05_50_0':'carlandfpga.local:diagnostic:deepeye_g05_axi_50:1.0',
         'trace50_0':'carlandfpga.local:diagnostic:deepeye_trace50_axi:1.0'}
MAX_FILE=16*1024*1024
VENDOR_STATE_DIR=Path('/usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/pl_server')
MAX_VENDOR_METADATA=24*1024*1024


def need(ok, text):
    if not ok: raise ValueError(text)


def validate_io(kind, offset, value):
    need(type(kind) is str and type(offset) is int and offset%4==0,'invalid operation')
    if kind=='read': need(offset in READS and value is None,'read offset refused')
    elif kind=='write':
        need(offset in WRITES and type(value) is int and 0<=value<=0xffffffff,'write refused')
        if offset==0x80: need(value in (1,2,3,4,5,8),'command refused')
    else: raise ValueError('operation kind refused')
    return kind,offset,value


def identity_words(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{32}',value) is not None and int(value,16)!=0,'BUILD_ID required')
    n=int(value,16)
    return tuple((n>>(32*i))&0xffffffff for i in range(4))


def kernel_ps_reference(text):
    need(type(text) is str and len(text)<=131072,'clock summary size')
    matches=[line.split() for line in text.splitlines() if line.split() and line.split()[0]=='ps_clk']
    fields=_one(matches,'kernel ps_clk')
    need(len(fields)>=5 and fields[4]=='50000000','kernel ps_clk is not 50MHz')
    return 50000000


def _one(seq, label):
    xs=list(seq);need(len(xs)==1,'expected exactly one '+label);return xs[0]


def _params(node):
    out={}
    for x in node.findall('./PARAMETERS/PARAMETER')+node.findall('./PARAMETER'):
        name=x.get('NAME');need(name and name not in out,'duplicate parameter');out[name]=x.get('VALUE')
    return out


def _integer(text):
    need(type(text) is str and re.fullmatch(r'(?:0[xX][0-9a-fA-F]+|[0-9]+)',text) is not None,'bad HWH integer')
    return int(text,16 if text.lower().startswith('0x') else 10)


def validate_hwh(raw, mapping, build_id):
    identity_words(build_id)
    need(type(raw) is bytes and 0<len(raw)<=8*1024*1024 and b'\x00' not in raw and not re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b',raw,re.I),'unsafe HWH')
    root=ET.fromstring(raw);need(root.tag=='EDKSYSTEM' and root.get('VIVADOVERSION')=='2026.1' and 'TEST_FIXTURE' not in root.attrib,'HWH format')
    need(type(mapping) is dict and mapping.get('bd')=='functional50_diag' and mapping.get('top')=='functional50_diag_wrapper' and mapping.get('master')=='ps7_0/Data' and mapping.get('build_id')==build_id,'mapping identity')
    windows=mapping.get('windows');need(type(windows) is list and len(windows)==2,'two windows required')
    need([(x.get('instance'),x.get('vlnv')) for x in windows]==list(VLNVS.items()),'window identity')
    modules=root.findall('./MODULES/MODULE')
    def module(name,vlnv):
        x=_one((x for x in modules if x.get('INSTANCE')==name or x.get('FULLNAME','').strip('/')==name),name)
        need(x.get('INSTANCE')==name and x.get('FULLNAME')=='/'+name and x.get('VLNV')==vlnv,'module identity');return x
    ps=module('ps7_0','xilinx.com:ip:processing_system7:5.5')
    mods=[module(k,v) for k,v in VLNVS.items()]
    private=[x for x in modules if x.get('VLNV','').startswith('carlandfpga.local:diagnostic:')]
    need(len(private)==2 and {x.get('VLNV') for x in private}==set(VLNVS.values()),'private IP aliases')
    pp=_params(ps)
    for k in ('PCW_USE_M_AXI_GP0','PCW_EN_CLK0_PORT','PCW_EN_RST0_PORT'):need(_integer(pp.get(k))==1,'required PS port')
    for k in ('PCW_USE_M_AXI_GP1','PCW_USE_S_AXI_GP0','PCW_USE_S_AXI_GP1','PCW_USE_S_AXI_ACP','PCW_USE_S_AXI_HP0','PCW_USE_S_AXI_HP1','PCW_USE_S_AXI_HP2','PCW_USE_S_AXI_HP3','PCW_EN_CLK1_PORT','PCW_EN_CLK2_PORT','PCW_EN_CLK3_PORT','PCW_EN_RST1_PORT','PCW_EN_RST2_PORT','PCW_EN_RST3_PORT'):need(_integer(pp.get(k))==0,'unexpected PS port')
    for k in ('PCW_FPGA0_PERIPHERAL_FREQMHZ','PCW_ACT_FPGA0_PERIPHERAL_FREQMHZ'):
        value=pp.get(k)
        need(type(value) is str and len(value)<=40,'FCLK0 metadata')
        try: rate=Decimal(value)
        except InvalidOperation: raise ValueError('FCLK0 metadata')
        need(rate.is_finite() and rate==50,'FCLK0 metadata')
    bp=_params(mods[1]).get('BUILD_ID','').lower().replace('_','')
    if bp.startswith("128'h"):bp=bp[5:]
    elif bp.startswith('0x'):bp=bp[2:]
    need(re.fullmatch('[0-9a-f]{1,32}',bp) is not None and int(bp,16)==int(build_id,16),'HWH BUILD_ID')
    need('BUILD_ID' not in _params(mods[0]),'G05 has no BUILD_ID')
    allranges=list(root.iter('MEMRANGE'));gp0=[x for x in allranges if x.get('MASTERBUSINTERFACE')=='M_AXI_GP0']
    need(len(gp0)==2 and {x.get('INSTANCE') for x in gp0}==set(VLNVS),'GP0 aliases')
    spans=[]
    for expected,node in zip(windows,mods):
        name=expected['instance'];r=_one((x for x in allranges if x.get('INSTANCE')==name),name+' range')
        need(r in gp0 and r.get('SLAVEBUSINTERFACE')=='S_AXI','wrong AXI interface')
        base=_integer(r.get('BASEVALUE'));high=_integer(r.get('HIGHVALUE'))
        need(base%4096==0 and high<=0xffffffff and high-base+1==4096 and base==_integer(str(expected.get('base'))) and _integer(str(expected.get('range')))==4096,'wrong aperture')
        bus=_one((x for x in node.findall('./BUSINTERFACES/BUSINTERFACE') if x.get('NAME')=='S_AXI'),'S_AXI');pars=_params(bus)
        need(bus.get('TYPE')=='SLAVE' and bus.get('VLNV')=='xilinx.com:interface:aximm:1.0' and bus.get('DATAWIDTH')=='32' and pars.get('DATA_WIDTH')=='32' and pars.get('ADDR_WIDTH')=='12' and pars.get('PROTOCOL')=='AXI4LITE' and pars.get('FREQ_HZ')=='50000000','AXI metadata')
        spans.append((base,high))
    need(spans[0][1]<spans[1][0] or spans[1][1]<spans[0][0],'overlapping windows')
    clock=_one((x for x in ps.findall('./PORTS/PORT') if x.get('NAME')=='FCLK_CLK0'),'FCLK0')
    need(clock.get('SIGIS')=='clk' and clock.get('CLKFREQUENCY')=='50000000' and clock.get('SIGNAME'),'clock output metadata')
    for node in mods:
        pin=_one((x for x in node.findall('./PORTS/PORT') if x.get('NAME')=='s_axi_aclk'),'AXI clock')
        links={(x.get('INSTANCE'),x.get('PORT')) for x in pin.findall('./CONNECTIONS/CONNECTION')}
        need(pin.get('SIGIS')=='clk' and pin.get('SIGNAME')==clock.get('SIGNAME') and links=={('ps7_0','FCLK_CLK0')},'AXI clock connection')
    return tuple(spans)


def _bytes(path, limit):
    p=Path(path); _no_links(p)
    with p.open('rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'input file refused')
        data=f.read(limit+1);after=os.fstat(f.fileno())
    need(len(data)==before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'input changed')
    return data,(before.st_dev,before.st_ino)


def _no_links(path):
    need(path.is_absolute() and '..' not in path.parts,'absolute non-symlink path required')
    for item in (path,*path.parents):
        need(not item.is_symlink(),'symlink path refused')


def _hash(data): return hashlib.sha256(data).hexdigest()

def _json(data):
    def unique(pairs):
        out={}
        for key,value in pairs:
            need(key not in out,'duplicate JSON key')
            out[key]=value
        return out
    return json.loads(data,object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def _record(directory, name, data):
    payload=(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()
    fd=os.open(str(directory/name),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())


def _ps(clock):
    z=clock._instance; r=z._slcr_registers
    return {'source':int(r.FPGA0_CLK_CTRL.SRCSEL),'pll_fdiv':int(r.IO_PLL_CTRL.PLL_FDIV),'div0':int(r.FPGA0_CLK_CTRL.DIVISOR0),'div1':int(r.FPGA0_CLK_CTRL.DIVISOR1),
            'other':tuple(int(z._slcr_mmio.read(x)) for x in (0x180,0x190,0x1a0))}


def _require_no_global_state(vendor):
    try:
        (vendor/'global_pl_state.json').lstat()
    except FileNotFoundError:
        return
    raise ValueError('existing vendor global state refused')


def _vendor_identity(st):
    return (st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def _preserve_vendor_state(directory, vendor):
    _require_no_global_state(vendor)
    before_dir=directory/'vendor-before';before_dir.mkdir(mode=0o700)
    source=vendor/'_current_metadata.pkl'
    try:
        before=source.lstat()
    except FileNotFoundError:
        _require_no_global_state(vendor)
        _record(before_dir,'receipt.json',{'global_state_absent':True,'metadata_exists':False})
        return None
    need(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_VENDOR_METADATA,'vendor metadata refused')
    fd=os.open(str(source),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
    with os.fdopen(fd,'rb') as f:
        opened=os.fstat(f.fileno())
        need((before.st_dev,before.st_ino,before.st_size)==(opened.st_dev,opened.st_ino,opened.st_size) and stat.S_ISREG(opened.st_mode),'vendor metadata changed')
        data=f.read(MAX_VENDOR_METADATA+1);after=os.fstat(f.fileno())
    need(len(data)==before.st_size and _vendor_identity(opened)==_vendor_identity(after) and _vendor_identity(before)==_vendor_identity(source.lstat()),'vendor metadata changed')
    target=before_dir/'_current_metadata.pkl'
    fd=os.open(str(target),os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    saved=target.read_bytes()
    need(len(saved)==len(data) and _hash(saved)==_hash(data),'vendor metadata backup mismatch')
    _require_no_global_state(vendor)
    _record(before_dir,'receipt.json',{'global_state_absent':True,'metadata_exists':True,'metadata_bytes':len(data),'metadata_sha256':_hash(data)})
    return _vendor_identity(before)


def _check_vendor_metadata(vendor, expected):
    source=vendor/'_current_metadata.pkl'
    try:
        current=source.lstat()
    except FileNotFoundError:
        need(expected is None,'vendor metadata changed after backup')
        return
    need(expected is not None and stat.S_ISREG(current.st_mode) and _vendor_identity(current)==expected,'vendor metadata changed after backup')


_KEY=object()
# Original same-process load custody; populated only after ready readback.
_G05_LOADS={}
_G05_CLAIMED=set()
_G05_PORTS={}
class _TracePort:
    def __init__(self,key,mmio,directory,boot):
        need(key is _KEY,'internal port only');self._mmio=mmio;self._dir=directory;self._boot=boot;self._pid=os.getpid();self._count=0;self._failed=False;self._ids=set();self._commands={1:0,2:0,3:0,4:0,5:0,8:0}
    def _call(self,kind,offset,value,request_id):
        validate_io(kind,offset,value)
        need(not self._failed and os.getpid()==self._pid and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==self._boot,'owner/boot changed')
        need(type(request_id) is str and re.fullmatch('[A-Za-z0-9_-]{1,64}',request_id) is not None and request_id not in self._ids and self._count<5000,'one-use request/limit')
        if kind=='write' and offset==0x80:
            limits={1:1,2:4,3:4,4:4,5:1,8:4096};need(self._commands[value]<limits[value] and (value==1 or self._commands[1]==1),'command quota/ARM')
        self._count+=1;n=self._count;self._ids.add(request_id)
        _record(self._dir,'io-%05d-started.json'%n,{'id':request_id,'kind':kind,'offset':offset,'value':value,'pid':self._pid,'monotonic_ns':time.monotonic_ns()})
        if kind=='write' and offset==0x80:self._commands[value]+=1
        try:
            output=self._mmio.read(offset) if kind=='read' else self._mmio.write(offset,value)
            _record(self._dir,'io-%05d-returned.json'%n,{'id':request_id,'kind':kind,'value':output,'monotonic_ns':time.monotonic_ns()})
            return output
        except BaseException:
            self._failed=True
            # Absence of returned record preserves an unknown effect.
            raise
    def read32(self,offset,request_id):return self._call('read',offset,None,request_id)
    def write32(self,offset,value,request_id):return self._call('write',offset,value,request_id)


def open_from_plan(plan_path):
    """One new owner operation: reconfigures PL and FCLK0, no G05 writes.

    Caller/Root must separately prove exclusive ownership, old SDK termination,
    same-build provenance, and approve exact plan before entering this function.
    """
    data,_=_bytes(plan_path,131072);plan=_json(data)
    keys={'operation_id','request_sha256','build_id','source_commit','boot_id','bit_path','hwh_path','mapping_path','bit_sha256','hwh_sha256','mapping_sha256','operation_parent'}
    need(type(plan) is dict and set(plan)==keys,'exact plan keys')
    body=dict(plan);request=body.pop('request_sha256');need(type(request) is str and _hash(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==request,'request hash')
    operation=plan['operation_id'];need(type(operation) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',operation) is not None,'operation ID')
    identity_words(plan['build_id']);need(type(plan['source_commit']) is str and re.fullmatch('[0-9a-f]{40}',plan['source_commit']),'source commit')
    need(str(uuid.UUID(plan['boot_id']))==plan['boot_id'],'boot UUID')
    blobs=[];ids=[]
    for k,limit in (('bit',MAX_FILE),('hwh',8*1024*1024),('mapping',131072)):
        b,i=_bytes(plan[k+'_path'],limit);need(_hash(b)==plan[k+'_sha256'],k+' hash mismatch');blobs.append(b);ids.append(i)
    need(len(set(ids))==3,'aliased input files')
    bp,hp=Path(plan['bit_path']),Path(plan['hwh_path'])
    need(bp.suffix=='.bit' and hp.suffix=='.hwh' and bp.parent==hp.parent and bp.stem==hp.stem,'same-name BIT/HWH required')
    mapping=_json(blobs[2]);spans=validate_hwh(blobs[1],mapping,plan['build_id'])
    need(os.geteuid()==0 and os.uname().machine=='armv7l' and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==plan['boot_id'],'root/architecture/BOOT mismatch')
    parent=Path(plan['operation_parent']);_no_links(parent);need(parent.is_dir(),'owned operation parent')
    directory=parent/operation;directory.mkdir(mode=0o700)
    _record(directory,'operation-started.json',{'operation_id':operation,'request_sha256':request,'build_id':plan['build_id'],'boot_id':plan['boot_id'],'source_commit':plan['source_commit'],'pid':os.getpid(),'monotonic_ns':time.monotonic_ns()})
    try:
        _record(directory,'vendor-preservation-started.json',{'monotonic_ns':time.monotonic_ns()})
        vendor_identity=_preserve_vendor_state(directory,VENDOR_STATE_DIR)
        stem='functional50_'+request[:24];bit=directory/(stem+'.bit');hwh=directory/(stem+'.hwh')
        for p,b in ((bit,blobs[0]),(hwh,blobs[1])):
            fd=os.open(str(p),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        _require_no_global_state(VENDOR_STATE_DIR)
        _check_vendor_metadata(VENDOR_STATE_DIR,vendor_identity)
        from pynq import Bitstream, Clocks, MMIO, Device
        from pynqmetadata.frontends import Metadata
        from pynq.metadata.runtime_metadata_parser import RuntimeMetadataParser
        from pynq.pl_server.embedded_device import EmbeddedDevice, _create_xclbin, _unify_dictionaries, bit2bin
        from pynq.pl_server.xclbin_parser import XclBin
        device=Device.active_device;need(type(device) is EmbeddedDevice,'exact embedded device required')
        refs=[Path(x) for x in ('/sys/firmware/devicetree/base/ps-clk/clock-frequency','/sys/firmware/devicetree/base/clocks/ps-clk/clock-frequency','/sys/firmware/devicetree/base/ps_clk/clock-frequency','/sys/firmware/devicetree/base/clocks/ps_clk/clock-frequency')]
        raw_refs=[x.read_bytes() for x in refs if x.is_file()]
        need(all(len(x)==4 and int.from_bytes(x,'big')==50000000 for x in raw_refs),'PS device-tree reference mismatch')
        summary=Path('/sys/kernel/debug/clk/clk_summary').read_text()
        kernel_ps_reference(summary)
        before=_ps(Clocks);need(Clocks._instance._slcr_mmio.device is device,'clock device identity mismatch')
        need(before['source']==0 and before['pll_fdiv']==20 and before['div0']==5 and before['div1']==2,'unexpected initial PS clocks')
        _record(directory,'parser-started.json',{'hwh_sha256':plan['hwh_sha256'],'monotonic_ns':time.monotonic_ns()})
        parser=RuntimeMetadataParser(Metadata(input=hwh));xdata=_create_xclbin(parser.mem_dict);_unify_dictionaries(parser,XclBin(xclbin_data=xdata));parser.refresh_hierarchy_dict();parser.bin_data=bit2bin(blobs[0]);parser.xclbin_data=xdata;parser.dtbo_data=None
        for i,name in enumerate(VLNVS):
            matches=[v for k,v in parser.ip_dict.items() if k.strip('/')==name or str(v.get('fullpath','')).strip('/')==name]
            x=_one(matches,'parser IP '+name);need(int(x['phys_addr'])==spans[i][0] and int(x['addr_range'])==4096 and x.get('type')==VLNVS[name],'parser window mismatch')
        _record(directory,'parser-returned.json',{'monotonic_ns':time.monotonic_ns(),'xclbin_sha256':_hash(xdata)})
        fw=Path('/lib/firmware')/(stem+'.bin');bs=Bitstream(str(bit),partial=False,device=device)
        _record(directory,'firmware-write-started.json',{'path':str(fw),'sha256':_hash(parser.bin_data)})
        fd=os.open(str(fw),os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o644)
        with os.fdopen(fd,'wb') as f:f.write(parser.bin_data);f.flush();os.fsync(f.fileno())
        _record(directory,'firmware-write-returned.json',{'sha256':_hash(fw.read_bytes())});need(_hash(fw.read_bytes())==_hash(parser.bin_data),'firmware readback mismatch')
        bs.binfile_name=fw.name;bs.firmware_path=fw
        _record(directory,'clock-write-started.json',{'fclk':0,'div0':10,'div1':2,'before':before})
        Clocks.set_pl_clk(0,div0=10,div1=2)
        _record(directory,'clock-write-returned.json',{'monotonic_ns':time.monotonic_ns()})
        after=_ps(Clocks);_record(directory,'clock-readback.json',after)
        need(after['source']==0 and after['pll_fdiv']==20 and after['div0']==10 and after['div1']==2 and after['other']==before['other'],'clock readback mismatch')
        _record(directory,'load-started.json',{'bit_sha256':plan['bit_sha256'],'hwh_sha256':plan['hwh_sha256'],'build_id':plan['build_id']})
        _require_no_global_state(VENDOR_STATE_DIR)
        _check_vendor_metadata(VENDOR_STATE_DIR,vendor_identity)
        bs.download(parser=parser)
        _record(directory,'load-returned.json',{'monotonic_ns':time.monotonic_ns()})
        ps_after=_ps(Clocks);need(ps_after==after,'PS clocks changed during load')
        port=_TracePort(_KEY,MMIO(spans[1][0],4096,device=device),directory,plan['boot_id'])
        for off,expected in IDENTITY.items():need(port.read32(off,'identity-%x'%off)==expected,'TRACE identity mismatch')
        for i,word in enumerate(identity_words(plan['build_id'])):need(port.read32(0x60+4*i,'build-%d'%i)==word,'TRACE build mismatch')
        _record(directory,'ready.json',{'build_id':plan['build_id'],'trace_base':spans[1][0],'g05_writes':0,'clock':ps_after,'pid':os.getpid()})
        binding=tuple((k,plan[k]) for k in ('operation_id','request_sha256','boot_id','source_commit','build_id'))
        _G05_LOADS[port]=(device,MMIO,tuple(spans),binding,parser,blobs[1],os.getpid(),port._mmio,threading.get_ident())
        return port
    except BaseException as error:
        try:_record(directory,'failed.json',{'type':type(error).__name__,'message':str(error),'unknown_if_started_without_return':True})
        except BaseException:pass
        raise


def main():
    need(len(sys.argv)==2,'usage: functional50_board_a.py PLAN.json')
    port=open_from_plan(sys.argv[1]);print(json.dumps({'state':'ready','pid':os.getpid()}),flush=True)
    for line in sys.stdin:
        need(len(line)<=4096,'request too long');cmd=_json(line)
        need(type(cmd) is dict and set(cmd)=={'id','kind','offset','value'},'exact request fields')
        value=port._call(cmd['kind'],cmd['offset'],cmd['value'],cmd['id'])
        print(json.dumps({'id':cmd['id'],'returned':value}),flush=True)

if __name__=='__main__':main()
