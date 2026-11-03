"""Read-only three-window50MHz HWH checker; no Vivado/MMIO/board imports."""
import argparse,hashlib,json,pathlib,re,xml.etree.ElementTree as ET

BASE_SHA='73a64f2d19e8d13c70af0150eef71bc3092825f95a8481ba0fb4e71ae55c2e5b'
BASE=pathlib.Path('D:/codex-tmp/a324/competition/deepeye/evidence/diagnostic/functional50/a556-fast-longttl-demo-r01/artifacts/functional50_diag.hwh')
VLNVS={'g05_50_0':'carlandfpga.local:diagnostic:deepeye_g05_axi_50:1.0','trace50_0':'carlandfpga.local:diagnostic:deepeye_trace50_axi:1.0','mcu_uart':'xilinx.com:ip:axi_uartlite:2.0'}
PWM={'yaw_pwm_o':'g05_50_candidate_yaw_pwm_o','pitch_pwm_o':'g05_50_candidate_pitch_pwm_o','speed_pwm_o':'g05_50_candidate_speed_pwm_o'}

def need(v,reason):
    if not v:raise ValueError(reason)
def one(items,reason):
    items=list(items);need(len(items)==1,'expected one '+reason);return items[0]
def params(e):return {p.get('NAME'):p.get('VALUE') for p in list(e.findall('./PARAMETERS/PARAMETER'))+list(e.findall('./PARAMETER'))}
def con(e):return {(c.get('INSTANCE'),c.get('PORT')) for c in e.findall('./CONNECTIONS/CONNECTION')}
def port(e,name):return one([p for p in e.findall('./PORTS/PORT') if p.get('NAME')==name],name)
def width(e):return 1 if e.get('LEFT') is None else abs(int(e.get('LEFT'))-int(e.get('RIGHT')))+1
def integer(v):return int(str(v),16 if str(v).lower().startswith('0x') else 10)
def xml(path):
    data=pathlib.Path(path).read_bytes()
    need(0<len(data)<=8*1024*1024 and b'<!DOCTYPE' not in data and b'<!ENTITY' not in data,'bounded plain HWH')
    return ET.fromstring(data),hashlib.sha256(data).hexdigest()
def module(root,name,vlnv=None):
    m=one([m for m in root.findall('./MODULES/MODULE') if m.get('INSTANCE')==name],name)
    need(m.get('FULLNAME')=='/'+name,'module fullname')
    if vlnv:need(m.get('VLNV')==vlnv,'module vlnv '+name)
    return m
def memrange(root,name):
    return one([r for r in root.iter('MEMRANGE') if r.get('INSTANCE')==name and r.get('MASTERBUSINTERFACE')=='M_AXI_GP0'],name+' GP0 range')


def verify(hwh_path,mapping,expected_build_id,baseline_hwh_path=BASE,*,test_fixture=False):
    root,hwh_sha=xml(hwh_path);base,base_sha=xml(baseline_hwh_path)
    need(base_sha==BASE_SHA,'exact original556 HWH pin required')
    need(root.tag=='EDKSYSTEM' and root.get('VIVADOVERSION')=='2026.1','actual2026.1 HWH required')
    need(test_fixture or 'TEST_FIXTURE' not in root.attrib,'synthetic HWH is not actual build evidence')
    need(re.fullmatch('[0-9a-f]{32}',expected_build_id) and int(expected_build_id,16)>0 and expected_build_id!='dc4e89ccf3db18c4f9871575efc399ba','new nonold128bit buildID')
    need(mapping.get('schema')=='DEEPEYE-UART-JOINT50-v1' and mapping.get('bd')=='functional50_diag' and mapping.get('top')=='functional50_diag_wrapper' and mapping.get('master')=='ps7_0/Data','combined mapping identity')
    need(mapping.get('build_id')==expected_build_id and mapping.get('clock_hz')==50000000 and mapping.get('preserved_first_two') is True,'combined identity/clock')
    need(mapping.get('uart')=={'instance':'mcu_uart','baud':115200,'data_bits':8,'parity':False},'selected115200/8N1 UART')
    windows=mapping.get('windows');need(type(windows) is list and len(windows)==3,'exact three windows')
    need([w.get('instance') for w in windows]==list(VLNVS),'stable G05/TRACE/UART mapping order')
    mods={name:module(root,name,vlnv) for name,vlnv in VLNVS.items()}
    private=[m for m in root.findall('./MODULES/MODULE') if m.get('VLNV','').startswith('carlandfpga.local:diagnostic:')]
    need({m.get('INSTANCE') for m in private}=={'g05_50_0','trace50_0'} and len(private)==2,'exact unchanged two private IPs')
    ps=module(root,'ps7_0','xilinx.com:ip:processing_system7:5.5')
    ic=module(root,'axi_gp0','xilinx.com:ip:axi_interconnect:2.1')
    reset=module(root,'rst_fclk0','xilinx.com:ip:proc_sys_reset:5.0')
    master=one([b for b in ps.findall('./BUSINTERFACES/BUSINTERFACE') if b.get('NAME')=='M_AXI_GP0'],'GP0 master')
    slave=one([b for b in ic.findall('./BUSINTERFACES/BUSINTERFACE') if b.get('NAME')=='S00_AXI'],'GP0 slave')
    need(master.get('BUSNAME')==slave.get('BUSNAME'),'actual GP0 interconnect source')
    pp=params(ps);oldps=params(module(base,'ps7_0'))
    selected=[k for k in oldps if k.startswith('PCW_UIPARAM_DDR_')]
    need(selected and all(pp.get(k)==oldps[k] for k in selected),'original DDR HWH parameters changed')
    for k in ('PCW_FPGA0_PERIPHERAL_FREQMHZ','PCW_ACT_FPGA0_PERIPHERAL_FREQMHZ'):need(float(pp[k])==50.,'configured/actual50MHz FCLK0')
    for k in ('PCW_USE_M_AXI_GP0','PCW_EN_CLK0_PORT','PCW_EN_RST0_PORT'):need(integer(pp[k])==1,'required GP0/clock/reset')
    for k in ('PCW_USE_M_AXI_GP1','PCW_EN_CLK1_PORT','PCW_EN_CLK2_PORT','PCW_EN_CLK3_PORT','PCW_EN_RST1_PORT','PCW_EN_RST2_PORT','PCW_EN_RST3_PORT'):need(integer(pp[k])==0,'extra PS domain enabled')
    need(integer(params(ic)['NUM_SI'])==1 and integer(params(ic)['NUM_MI'])==3,'one GP0/threeMI')
    need(params(reset)['C_EXT_RESET_HIGH']=='0' and params(reset)['C_AUX_RESET_HIGH']=='1','reset polarity')
    need(con(port(reset,'dcm_locked'))=={('const_one','dout')},'reset dcm_locked constant')
    for name in ('aux_reset_in','mb_debug_sys_rst'):need(con(port(reset,name))=={('const_zero','dout')},'inert reset input '+name)
    need(integer(params(mods['trace50_0'])['BUILD_ID'])==int(expected_build_id,16),'TRACE actual buildID')
    need('BUILD_ID' not in params(mods['g05_50_0']),'unchanged G05 has no buildID parameter')
    up=params(mods['mcu_uart'])
    for key,value in {'C_BAUDRATE':115200,'C_DATA_BITS':8,'C_USE_PARITY':0,'C_ODD_PARITY':0,'C_S_AXI_ACLK_FREQ_HZ':50000000}.items():need(integer(up[key])==value,'UART parameter '+key)
    ranges=[r for r in root.iter('MEMRANGE') if r.get('MASTERBUSINTERFACE')=='M_AXI_GP0']
    need(len(ranges)==3 and {r.get('INSTANCE') for r in ranges}==set(VLNVS),'exact selected GP0 peripherals')
    spans=[]
    for index,window in enumerate(windows):
        name=window['instance'];obj=mods[name];r=memrange(root,name)
        lo,hi=integer(r.get('BASEVALUE')),integer(r.get('HIGHVALUE'))
        need(window.get('vlnv')==VLNVS[name] and lo==integer(window['base']) and integer(window['range'])==4096 and hi-lo+1==4096 and lo%4096==0 and 0<=lo<=hi<=0xffffffff,'HWH/mapping exact4KiB '+name)
        spans.append((lo,hi))
        if name!='mcu_uart':
            old=memrange(base,name)
            need(lo==integer(old.get('BASEVALUE')) and hi==integer(old.get('HIGHVALUE')),'existing two bases moved')
        bus=one([b for b in obj.findall('./BUSINTERFACES/BUSINTERFACE') if b.get('NAME')=='S_AXI'],name+' S_AXI')
        ibus=one([b for b in ic.findall('./BUSINTERFACES/BUSINTERFACE') if b.get('NAME')=='M%02d_AXI'%index],name+' master')
        need(bus.get('BUSNAME')==ibus.get('BUSNAME') and bus.get('TYPE')=='SLAVE' and bus.get('DATAWIDTH')=='32','actual M0%d routing'%index)
        bp=params(bus);need(bp.get('PROTOCOL')=='AXI4LITE' and bp.get('DATA_WIDTH')=='32' and bp.get('FREQ_HZ')=='50000000','AXI4Lite32/50MHz '+name)
        need(integer(bp['ADDR_WIDTH'])==(4 if name=='mcu_uart' else 12),'physical AXI address width')
    need(all(a[1]<b[0] or b[1]<a[0] for i,a in enumerate(spans) for b in spans[i+1:]),'window overlap')
    clock=port(ps,'FCLK_CLK0');clocknet=clock.get('SIGNAME')
    need(clock.get('CLKFREQUENCY')=='50000000','PS real output50MHz')
    targets=[('ps7_0',ps,'M_AXI_GP0_ACLK'),('rst_fclk0',reset,'slowest_sync_clk')]+[(name,obj,'s_axi_aclk') for name,obj in mods.items()]+[('axi_gp0',ic,n) for n in ('ACLK','S00_ACLK','M00_ACLK','M01_ACLK','M02_ACLK')]
    for name,obj,pname in targets:
        q=port(obj,pname);need(q.get('SIGNAME')==clocknet and con(q)=={('ps7_0','FCLK_CLK0')},'single actual FCLK0 sink '+name+'/'+pname)
    need(con(clock)=={(name,pname) for name,_,pname in targets},'exact FCLK0 endpoints')
    def reset_net(origin,origin_name,pname,sinks):
        pin=port(origin,pname);net=pin.get('SIGNAME');need(pin.get('POLARITY')=='ACTIVE_LOW','reset source polarity')
        for name,obj,sink in sinks:
            q=port(obj,sink);need(q.get('SIGNAME')==net and con(q)=={(origin_name,pname)},'exact reset source '+name+'/'+sink)
        need(con(pin)=={(name,sink) for name,_,sink in sinks},'exact reset destinations')
    reset_net(ps,'ps7_0','FCLK_RESET0_N',[('rst_fclk0',reset,'ext_reset_in')])
    reset_net(reset,'rst_fclk0','interconnect_aresetn',[('axi_gp0',ic,'ARESETN')])
    reset_net(reset,'rst_fclk0','peripheral_aresetn',[(name,obj,'s_axi_aresetn') for name,obj in mods.items()]+[('axi_gp0',ic,n) for n in ('S00_ARESETN','M00_ARESETN','M01_ARESETN','M02_ARESETN')])
    external={p.get('NAME'):p for p in root.findall('./EXTERNALPORTS/PORT')}
    old_external={p.get('NAME'):p for p in base.findall('./EXTERNALPORTS/PORT')}
    need(len(external)==len(root.findall('./EXTERNALPORTS/PORT')) and set(external)==set(old_external)|{'mcu_uart_tx_o','mcu_uart_rx_i'},'exact unchangedPS+3PWM+2UART top closure')
    for name,old in old_external.items():
        q=external[name];need(q.get('DIR')==old.get('DIR') and width(q)==width(old) and con(q)==con(old),'old top port changed '+name)
    for name,pname in PWM.items():
        q=port(mods['g05_50_0'],pname);need(con(q)=={('External_Ports',name)},'real PWM output external connection')
    for name,pname,direction in (('mcu_uart_tx_o','tx','O'),('mcu_uart_rx_i','rx','I')):
        a,b=external[name],port(mods['mcu_uart'],pname)
        need(a.get('DIR')==b.get('DIR')==direction and width(a)==width(b)==1 and a.get('SIGNAME')==b.get('SIGNAME'),'UART scalar direction/net')
        need(con(a)=={('mcu_uart',pname)} and con(b)=={('External_Ports',name)},'UART exact external source/sink')
    for axis in ('yaw','pitch','speed'):
        need(con(port(mods['g05_50_0'],'g05_50_candidate_'+axis+'_capture_i'))=={('const_zero','dout')},'legacy external capture must stay inert')
    return {'status':'synthetic_mechanism_fixture_verified' if test_fixture else 'same_run_joint50_hwh_verified','hwh_sha256':hwh_sha,'baseline_hwh_sha256':base_sha,'build_id':expected_build_id,'windows':windows,'uart_instance':'mcu_uart','uart_clock_hz':50000000,'baud':115200,'data_bits':8,'parity':False,'first_two_preserved':True,'pin_package_and_CDC':'separate implemented netlist reports required','physical_validation':'not_run','formal_all29':'not_run'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--hwh',required=True);p.add_argument('--mapping',required=True);p.add_argument('--build-id',required=True);p.add_argument('--baseline-hwh',default=str(BASE));p.add_argument('--output',required=True);a=p.parse_args()
    result=verify(a.hwh,json.loads(pathlib.Path(a.mapping).read_bytes()),a.build_id,a.baseline_hwh)
    with pathlib.Path(a.output).open('x',encoding='utf8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,sort_keys=True))
