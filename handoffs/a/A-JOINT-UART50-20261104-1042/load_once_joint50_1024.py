"""1024 joint50 one-load entry, derived from the frozen 791 loader.
Preserves operation, vendor, parser, clock, firmware and single-load checks.
Validates G05/TRACE/UART; returns TRACE MMIO, G05 MMIO, original plan.
Root owns fresh staging, exclusive ownership, approval and physical execution.
"""
import hashlib,json,os,re,stat,sys,time,threading,uuid
from pathlib import Path
from competition.deepeye.tools.diagnostic.functional50_board_a import (need,_bytes,_json,_hash,_no_links,_record,_preserve_vendor_state,_require_no_global_state,_check_vendor_metadata,_ps,_one,identity_words,validate_hwh,kernel_ps_reference,MAX_FILE,VENDOR_STATE_DIR,VLNVS)
import xml.etree.ElementTree as ET
from competition.deepeye.tools.diagnostic.functional50_board_a import _params, _integer
from verify_uart_joint50_hwh import verify as verify_joint_hwh, VLNVS as JOINT_VLNVS

BASELINE_HWH_SHA256='73a64f2d19e8d13c70af0150eef71bc3092825f95a8481ba0fb4e71ae55c2e5b'

def validated_joint_descriptors(hwh_path,mapping,build_id,baseline_hwh_path):
    """Read-only production HWH validation; no PYNQ import, MMIO or load.

    Returns fresh descriptors in G05/TRACE/UART order. The UART base is read
    from the validated HWH, with its same-run mapping checked by the verifier.
    This validation does not authorize hardware or grant MCU ownership.
    """
    raw,_=_bytes(hwh_path,8*1024*1024)
    baseline,_=_bytes(baseline_hwh_path,8*1024*1024)
    need(_hash(baseline)==BASELINE_HWH_SHA256,'baseline HWH pin required')
    need(b'\x00' not in raw and not re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b',raw,re.I),'unsafe HWH')
    need(type(mapping) is dict,'mapping object required')
    result=verify_joint_hwh(hwh_path,mapping,build_id,baseline_hwh_path,test_fixture=False)
    need(result['status']=='same_run_joint50_hwh_verified' and result['hwh_sha256']==_hash(raw) and result['baseline_hwh_sha256']==BASELINE_HWH_SHA256,'validated HWH byte identity mismatch')
    root=ET.fromstring(raw);modules=root.findall('./MODULES/MODULE')
    def module(name,vlnv):
        obj=_one((x for x in modules if x.get('INSTANCE')==name or x.get('FULLNAME','').strip('/')==name),name)
        need(obj.get('INSTANCE')==name and obj.get('FULLNAME')=='/'+name and obj.get('VLNV')==vlnv,'module identity')
        return obj
    ps=module('ps7_0','xilinx.com:ip:processing_system7:5.5');pp=_params(ps)
    for key in ('PCW_USE_S_AXI_GP0','PCW_USE_S_AXI_GP1','PCW_USE_S_AXI_ACP','PCW_USE_S_AXI_HP0','PCW_USE_S_AXI_HP1','PCW_USE_S_AXI_HP2','PCW_USE_S_AXI_HP3'):
        need(_integer(pp.get(key))==0,'unexpected PS port')
    clock=_one((x for x in ps.findall('./PORTS/PORT') if x.get('NAME')=='FCLK_CLK0'),'FCLK0')
    need(clock.get('SIGIS')=='clk' and clock.get('SIGNAME'),'clock output metadata')
    allranges=list(root.iter('MEMRANGE'));descriptors=[]
    need(list(JOINT_VLNVS)==['g05_50_0','trace50_0','mcu_uart'],'joint verifier window order')
    for name,vlnv in JOINT_VLNVS.items():
        obj=module(name,vlnv);_params(obj)
        aperture=_one((x for x in allranges if x.get('INSTANCE')==name),name+' range')
        need(aperture.get('MASTERBUSINTERFACE')=='M_AXI_GP0' and aperture.get('SLAVEBUSINTERFACE')=='S_AXI','wrong AXI interface')
        base=_integer(aperture.get('BASEVALUE'));high=_integer(aperture.get('HIGHVALUE'))
        need(base%4096==0 and high-base+1==4096 and 0<=base<=high<=0xffffffff,'wrong aperture')
        bus=_one((x for x in obj.findall('./BUSINTERFACES/BUSINTERFACE') if x.get('NAME')=='S_AXI'),'S_AXI');_params(bus)
        need(bus.get('VLNV')=='xilinx.com:interface:aximm:1.0','AXI interface VLNV')
        pin=_one((x for x in obj.findall('./PORTS/PORT') if x.get('NAME')=='s_axi_aclk'),'AXI clock')
        need(pin.get('SIGIS')=='clk','AXI clock metadata')
        descriptors.append({'instance':name,'type':vlnv,'phys_addr':base,'addr_range':4096})
    need(descriptors[0]['phys_addr']==0x43C00000 and descriptors[1]['phys_addr']==0x43C10000,'preserved G05/TRACE base mismatch')
    return {'hwh_sha256':result['hwh_sha256'],'baseline_hwh_sha256':result['baseline_hwh_sha256'],'windows':tuple(descriptors)}
def open_stream_from_plan(plan_path):
    """One new owner operation: reconfigures PL and FCLK0, no G05 writes.

    Caller/Root must separately prove exclusive ownership, old SDK termination,
    same-build provenance, and approve exact plan before entering this function.
    """
    data,_=_bytes(plan_path,131072);plan=_json(data)
    keys={'operation_id','request_sha256','build_id','source_commit','boot_id','bit_path','hwh_path','mapping_path','bit_sha256','hwh_sha256','mapping_sha256','operation_parent','baseline_hwh_path','baseline_hwh_sha256'}
    need(type(plan) is dict and set(plan)==keys,'exact plan keys')
    body=dict(plan);request=body.pop('request_sha256');need(type(request) is str and _hash(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==request,'request hash')
    operation=plan['operation_id'];need(type(operation) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',operation) is not None,'operation ID')
    identity_words(plan['build_id']);need(type(plan['source_commit']) is str and re.fullmatch('[0-9a-f]{40}',plan['source_commit']),'source commit')
    need(str(uuid.UUID(plan['boot_id']))==plan['boot_id'],'boot UUID')
    blobs=[];ids=[]
    need(plan['baseline_hwh_sha256']==BASELINE_HWH_SHA256,'baseline HWH pin required')
    for k,limit in (('bit',MAX_FILE),('hwh',8*1024*1024),('mapping',131072),('baseline_hwh',8*1024*1024)):
        b,i=_bytes(plan[k+'_path'],limit);need(_hash(b)==plan[k+'_sha256'],k+' hash mismatch');blobs.append(b);ids.append(i)
    need(len(set(ids))==4,'aliased input files')
    bp,hp=Path(plan['bit_path']),Path(plan['hwh_path'])
    need(bp.suffix=='.bit' and hp.suffix=='.hwh' and bp.parent==hp.parent and bp.stem==hp.stem,'same-name BIT/HWH required')
    mapping=_json(blobs[2]);validated=validated_joint_descriptors(hp,mapping,plan['build_id'],plan['baseline_hwh_path'])
    need(validated['hwh_sha256']==plan['hwh_sha256'] and validated['baseline_hwh_sha256']==plan['baseline_hwh_sha256'],'plan/validated HWH hash mismatch')
    descriptors=validated['windows'];spans=tuple((d['phys_addr'],d['phys_addr']+d['addr_range']-1) for d in descriptors)
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
        for descriptor in descriptors:
            name=descriptor['instance']
            matches=[v for k,v in parser.ip_dict.items() if k.strip('/')==name or str(v.get('fullpath','')).strip('/')==name]
            x=_one(matches,'parser IP '+name);need(int(x['phys_addr'])==descriptor['phys_addr'] and int(x['addr_range'])==descriptor['addr_range']==4096 and x.get('type')==descriptor['type'],'parser window mismatch')
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
        return MMIO(spans[1][0],4096,device=device),MMIO(spans[0][0],4096,device=device),plan
    except BaseException as error:
        try:_record(directory,'failed.json',{'type':type(error).__name__,'message':str(error),'unknown_if_started_without_return':True})
        except BaseException:pass
        raise
