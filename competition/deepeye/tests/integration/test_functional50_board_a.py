import unittest
from competition.deepeye.tools.diagnostic import functional50_board_a as m

class PureBoundary(unittest.TestCase):
    def test_register_whitelist_and_commands(self):
        self.assertEqual(m.validate_io('read',0x60,None),('read',0x60,None))
        self.assertEqual(m.validate_io('write',0x80,5),('write',0x80,5))
        self.assertEqual(m.validate_io('write',0x80,8),('write',0x80,8))
        for a in [('read',0x81,None),('read',0x100,None),('write',0x60,1),('write',0x80,6),('write',0x080,True),('write',4096,0),('read',0,None),('write',0x100,-1)]:
            if a==('read',0,None): continue
            with self.subTest(a=a),self.assertRaises(ValueError):m.validate_io(*a)
    def test_build_and_identity(self):
        self.assertEqual(m.identity_words('0123456789abcdef0123456789abcdef'),(0x89abcdef,0x01234567,0x89abcdef,0x01234567))
        for v in ('0'*32,'g'*32,'ab',None):
            with self.assertRaises(ValueError):m.identity_words(v)

    def test_reference_and_duplicate_json(self):
        self.assertEqual(m.kernel_ps_reference(' ps_clk 3 3 0 50000000 0 0 50000 Y\n'),50000000)
        for text in ('ps_clk 3 3 0 100000000', 'ps_clk 3 3 0 50000000\nps_clk 3 3 0 50000000'):
            with self.assertRaises(ValueError):m.kernel_ps_reference(text)
        with self.assertRaises(ValueError):m._json('{"a":1,"a":2}')

    def test_hwh_refuses_alias_clock_and_wrong_build(self):
        import xml.etree.ElementTree as E
        root=E.Element('EDKSYSTEM',VIVADOVERSION='2026.1'); modules=E.SubElement(root,'MODULES')
        def mod(name,vlnv):return E.SubElement(modules,'MODULE',INSTANCE=name,FULLNAME='/'+name,VLNV=vlnv)
        def param(parent,name,value): E.SubElement(parent,'PARAMETER',NAME=name,VALUE=value)
        ps=mod('ps7_0','xilinx.com:ip:processing_system7:5.5');pp=E.SubElement(ps,'PARAMETERS')
        for name in ('PCW_USE_M_AXI_GP0','PCW_EN_CLK0_PORT','PCW_EN_RST0_PORT'):param(pp,name,'1')
        for name in ('PCW_USE_M_AXI_GP1','PCW_USE_S_AXI_GP0','PCW_USE_S_AXI_GP1','PCW_USE_S_AXI_ACP','PCW_USE_S_AXI_HP0','PCW_USE_S_AXI_HP1','PCW_USE_S_AXI_HP2','PCW_USE_S_AXI_HP3','PCW_EN_CLK1_PORT','PCW_EN_CLK2_PORT','PCW_EN_CLK3_PORT','PCW_EN_RST1_PORT','PCW_EN_RST2_PORT','PCW_EN_RST3_PORT'):param(pp,name,'0')
        for name in ('PCW_FPGA0_PERIPHERAL_FREQMHZ','PCW_ACT_FPGA0_PERIPHERAL_FREQMHZ'):param(pp,name,'50.0000000')
        E.SubElement(E.SubElement(ps,'PORTS'),'PORT',NAME='FCLK_CLK0',SIGIS='clk',CLKFREQUENCY='50000000',SIGNAME='clk0')
        mapping={'bd':'functional50_diag','top':'functional50_diag_wrapper','master':'ps7_0/Data','build_id':'1'*32,'windows':[]}
        for i,(name,vlnv) in enumerate(m.VLNVS.items()):
            obj=mod(name,vlnv);par=E.SubElement(obj,'PARAMETERS')
            if i:param(par,'BUILD_ID',"128'h"+'1'*32)
            bus=E.SubElement(E.SubElement(obj,'BUSINTERFACES'),'BUSINTERFACE',NAME='S_AXI',TYPE='SLAVE',VLNV='xilinx.com:interface:aximm:1.0',DATAWIDTH='32');bpar=E.SubElement(bus,'PARAMETERS')
            for k,v in [('DATA_WIDTH','32'),('ADDR_WIDTH','12'),('PROTOCOL','AXI4LITE'),('FREQ_HZ','50000000')]:param(bpar,k,v)
            port=E.SubElement(E.SubElement(obj,'PORTS'),'PORT',NAME='s_axi_aclk',SIGIS='clk',SIGNAME='clk0');E.SubElement(E.SubElement(port,'CONNECTIONS'),'CONNECTION',INSTANCE='ps7_0',PORT='FCLK_CLK0')
            base=0x40000000+i*4096;E.SubElement(root,'MEMRANGE',INSTANCE=name,MASTERBUSINTERFACE='M_AXI_GP0',SLAVEBUSINTERFACE='S_AXI',BASEVALUE=hex(base),HIGHVALUE=hex(base+4095));mapping['windows'].append({'instance':name,'vlnv':vlnv,'base':hex(base),'range':4096})
        raw=E.tostring(root);self.assertEqual(m.validate_hwh(raw,mapping,'1'*32),((0x40000000,0x40000fff),(0x40001000,0x40001fff)))
        with self.assertRaises(ValueError):m.validate_hwh(raw,mapping,'2'*32)
        with self.assertRaises(ValueError):m.validate_hwh(raw.replace(b'50000000',b'10000000'),mapping,'1'*32)
        ranges=list(root.iter('MEMRANGE'));ranges[1].set('BASEVALUE',ranges[0].get('BASEVALUE'));ranges[1].set('HIGHVALUE',ranges[0].get('HIGHVALUE'));mapping['windows'][1]['base']=mapping['windows'][0]['base']
        with self.assertRaises(ValueError):m.validate_hwh(E.tostring(root),mapping,'1'*32)
if __name__=='__main__': unittest.main(verbosity=2)
