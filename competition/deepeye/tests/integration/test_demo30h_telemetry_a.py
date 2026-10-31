"""New observation-only report controls; no native, board or network."""
import binascii,importlib.util,struct,unittest
from pathlib import Path
from competition.deepeye.tools.diagnostic import functional50_b131_loader as loader

class TelemetryControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bundle=loader.load_selected(Path(__file__).resolve().parents[4]);cls.codec=cls.bundle.adapter.codec
 def module(self):
  spec=importlib.util.find_spec('competition.deepeye.tools.diagnostic.demo30h_telemetry_a')
  self.assertIsNotNone(spec,'new telemetry interface missing')
  from competition.deepeye.tools.diagnostic import demo30h_telemetry_a as telemetry
  return telemetry
 def point(self,index,value,tick):return dict(index=index,tick_ms=tick,value=value,valid=True,saturated=False,held=False,source_fault=False,source_tick_ms=tick)
 def meta(self,e=0):return dict(session=7,config_epoch=3,e=e,first_sequence=12)
 def test_private_singleton_raw_and_bytes(self):
  mod=self.module();pt=self.point(2,1234,100000);packet=bytearray(self.codec.encode_frame([pt],{'session':7,'config_epoch':3,'e':0},2,12));packet[3]=0xe4;packet[12]=2;packet[-2:]=struct.pack('<H',binascii.crc_hqx(packet[2:-2],0xffff));raw=bytes(packet)
  result=mod.inspect_capture((dict(channel=2,**pt),),(raw,),metadata=self.meta(),layout='trace94_private_1us_v2',bundle=self.bundle,companions=(b'abc',))
  self.assertEqual(result['frames'][0]['mode'],'raw');self.assertEqual(result['points'][0]['difference'],0);self.assertEqual(result['time_unit'],'us');self.assertEqual(result['bytes']['frame_wire'],len(raw));self.assertEqual(result['bytes']['companion_supplied'],3);self.assertIsNone(result['bytes']['captured_upload']);self.assertFalse(result['board_verified'])
 def test_candidate_multisample_lossy_report(self):
  mod=self.module();pts=[self.point(i,100+i,1000+i*10) for i in range(8)];raw=self.codec.encode_frame(pts,{'session':7,'config_epoch':3,'e':1},1,12);out=mod.inspect_capture(tuple(dict(channel=1,**p) for p in pts),(raw,),metadata=self.meta(1),layout='candidate_abi3_type7_v1',bundle=self.bundle,transport_capture=b'abcde')
  self.assertEqual(len(out['points']),8);self.assertEqual(out['frames'][0]['mode'],'rice');self.assertTrue(any(x['difference']!=0 for x in out['points']));self.assertEqual(out['bytes']['captured_upload'],5);self.assertEqual(out['bytes']['baseline_u16'],16);self.assertEqual(out['bytes']['frame_wire'],len(raw));self.assertEqual(out['bytes']['payload']+out['bytes']['frame_overhead'],len(raw))
 def test_bad_crc_and_source_identity_rejected(self):
  mod=self.module();pt=self.point(2,1234,10);frame=self.codec.encode_frame([pt],{'session':7,'config_epoch':3,'e':0},2,12);bad=frame[:-1]+bytes([frame[-1]^1]);expected=(dict(channel=2,**pt),)
  with self.assertRaises(ValueError):mod.inspect_capture(expected,(bad,),metadata=self.meta(),layout='candidate_abi3_type7_v1',bundle=self.bundle)
  wrong=dict(expected[0]);wrong['index']=3
  with self.assertRaises(ValueError):mod.inspect_capture((wrong,),(frame,),metadata=self.meta(),layout='candidate_abi3_type7_v1',bundle=self.bundle)
if __name__=='__main__':
 import sys
 ids=['__main__.TelemetryControls.test_private_singleton_raw_and_bytes'] if '--red' in sys.argv else ['__main__.TelemetryControls.test_private_singleton_raw_and_bytes','__main__.TelemetryControls.test_candidate_multisample_lossy_report','__main__.TelemetryControls.test_bad_crc_and_source_identity_rejected']
 print('selected_test_ids:',*ids,flush=True);r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(ids));raise SystemExit(not r.wasSuccessful())
