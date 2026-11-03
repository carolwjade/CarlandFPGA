"""Synthetic MMIO register model controls. Never a board result."""
import importlib.util
import io
import json
from pathlib import Path
import struct
import binascii
import sys
import unittest

HERE=Path(__file__).resolve().parent
W=Path(r'C:/Users/CarlJade/.codex/worktrees/a-demo-production-channel/FPGA多机协作开发')
sys.path[:0]=[str(HERE),str(W)]
import remote_live_board_a as m
from local_stream_client import StreamClient
from competition.deepeye.golden.codec import trace_candidate as codec
from competition.deepeye.tools.diagnostic.functional50_g05_a import _command
from competition.deepeye.simulation.authority.g05_board_output_v1 import decode_board_output

BUILD='dc4e89ccf3db18c4f9871575efc399ba'
class Journal:
    def __init__(self):self.count=0;self.last=None
    def record(self,v,durable=False):self.count+=1;self.last=v

class Trace:
    def __init__(self):
        self.r={0:0x54353046,4:1,8:4,12:50000000,16:1000000,20:4096,
                0x18:0,0x1c:0,0x2c:0,0x40:0,0x38:0,0x34:0,0x24:0,0x28:0}
        for i in range(4):self.r[0x60+4*i]=(int(BUILD,16)>>(32*i))&m.U32
        self.fifo=bytearray();self.stage={};self.lanes={}
    def read(self,o):
        if o==0x20:return 2| (0x20 if not self.fifo else 0)| (0x10 if self.r[0x18] in (7,9) else 0)
        if o==0x30:return len(self.fifo)
        if o==0x70:return 0x100|self.fifo[0]
        return self.r.get(o,self.stage.get(o,0))
    def write(self,o,v):
        if o!=0x80:self.stage[o]=v;return
        if v==1:self.r[0x2c]=self.stage[0x100];self.r[0x18]=3;self.lanes={}
        elif v==2:
            self.lanes[self.stage[0x110]]=dict(self.stage)
            self.r[0x24]=self.stage[0x110]+1;self.r[0x18]=4 if self.r[0x24]==4 else 3
        elif v==3:
            ch=self.r[0x28] if self.r[0x18]!=3 else 0
            # next association resets on ARM.
            ch=self.stage[0x134]-self.stage[0x134]+len(getattr(self,'frames',[]))
            lane=self.lanes[ch];flags=lane[0x120];valid=bool(flags&1)
            p=dict(index=self.stage[0x134],tick_ms=self.stage[0x138],
                   source_tick_ms=self.stage[0x148] if valid else None,
                   value=lane[0x114] if valid else None,valid=valid,
                   saturated=bool(flags&2),held=bool(flags&4),source_fault=bool(flags&8))
            payload=codec.encode_payload([p],dict(session=self.stage[0x130],config_epoch=1,e=0),ch)
            payload=bytes([2])+payload[1:]
            body=struct.pack('<2sBBBBHI',b'\xa5\x5a',3,0xe4,len(payload),1,self.stage[0x154],self.stage[0x138])+payload
            frame=body+struct.pack('<H',binascii.crc_hqx(body[2:],0xffff))
            if not hasattr(self,'frames'):self.frames=[]
            self.frames.append(frame)
            self.r[0x40]+=1;self.r[0x44]=self.r[0x4c]=0;self.r[0x48]=len(frame)
            self.r[0x50]=self.r[0x34];self.r[0x34]+=len(frame);self.r[0x7c]=self.r[0x34]
            self.fifo.extend(frame);self.r[0x18]=7
        elif v==4:
            self.r[0x28]=len(self.frames);self.r[0x18]=9 if len(self.frames)==4 else 4
        elif v==8:
            self.fifo.pop(0);self.r[0x38]=self.stage[0x164]
        elif v==5:self.r[0x18]=0;self.r[0x28]=0;self.frames=[]

class G05:
    def __init__(self):self.r={0:0x47303550,4:2,8:0,0x10:0};self.writes=[];self.fail_commit=False
    def read(self,o):return self.r.get(o,0)
    def write(self,o,v):
        self.writes.append((o,v));self.r[o]=v
        if o!=0x0c:return
        if v==1:self.r[8]=1
        elif v==2:
            if self.fail_commit:raise OSError('synthetic uncertain COMMIT')
            y,p,profile,speed,ttl,seq,tag=[self.r[0x200+4*i] for i in range(7)]
            signed=lambda x:x if x<32768 else x-65536
            w=[0]*32;w[:6]=[seq,seq,tag,(speed<<8)|profile,(p<<16)|y,ttl]
            w[6]=100;w[8]=100+ttl*50000;w[10]=200
            w[12:15]=[1000000]*3;w[15:18]=[125000+8*signed(y),125000+8*signed(p),25000+500*speed]
            w[18:24]=[1000,0,1000,0,1000,0];w[24:30]=[1001000,0,1001000,0,1001000,0]
            w[30:]=[self.r[0x130],0x47303550]
            for i,x in enumerate(w):self.r[0x300+4*i]=x
            self.r[0x14]=seq;self.r[0x1c]=seq;self.r[8]=0x11
        elif v==4:self.r[8]=0x31
        elif v==5:self.r[8]=0x11
        elif v==3:self.r[8]=3

class Worker(m.LiveBoard):
    def live(self):m.need(not self.closed and not self.poisoned,'CLOSED')

def worker():
    w=Worker(Trace(),G05(),boot_id='synthetic',build_id=BUILD,request_hash='a'*64,
             identity=[1]*13,codec=codec,command_check=_command,output_decode=decode_board_output,journal=Journal())
    w.initialize();return w

def sense(seq,source=None):
    return dict(abi=m.ABI,op='sense',request_seq=seq,source_seq=source or seq,
                adc_tick_ms=100+seq,em_tick_ms=100+seq,counts=[3099,2006,2084,None],quality=7,source_digest='b'*64)

class Controls(unittest.TestCase):
    def test_stream_crosses_legacy_32_and_4096_pop_caps(self):
        w=worker()
        for i in range(1,41):
            r=w.request(sense(i));self.assertEqual(r['result']['correlation'],'FOUR_FRAME_CRC_SOURCE_CONSISTENT')
            self.assertEqual(r['result']['decoded'][3]['points'][0]['value'],None)
        self.assertGreater(w.trace.r[0x38],4096);self.assertEqual(w.last_source,40)
        self.assertFalse(hasattr(w,'events'));self.assertFalse(hasattr(w,'responses'))
    def test_real_decoder_reads_synthetic_capture_not_echo(self):
        w=worker();r=w.request(dict(abi=m.ABI,op='apply',request_seq=1,yaw_q=0,pitch_q=0,speed_code=2,duration_ms=12000))
        self.assertEqual(r['result']['pwm_high'],[125000,125000,26000])
        self.assertEqual(r['result']['measured']['speed_code'],2)
    def test_pause_is_real_zero_capture_then_resume_without_terminal_stop(self):
        w=worker()
        for seq,speed in ((1,2),(2,0),(3,2)):
            r=w.request(dict(abi=m.ABI,op='apply',request_seq=seq,yaw_q=0,pitch_q=0,speed_code=speed,duration_ms=12000))
            self.assertEqual(r['result']['measured']['speed_code'],speed)
        self.assertFalse(w.closed)
        self.assertNotIn((0x0c,3),w.g05.writes)
    def test_tampered_capture_cannot_use_echo_as_measured_output(self):
        w=worker();original=w.g05.read
        w.g05.read=lambda o:original(o)+500 if o==0x344 else original(o)
        with self.assertRaises(ValueError):w.request(dict(abi=m.ABI,op='apply',request_seq=1,yaw_q=0,pitch_q=0,speed_code=2,duration_ms=12000))
        self.assertTrue(w.poisoned)
    def test_unknown_commit_poisoned_no_retry(self):
        w=worker();w.g05.fail_commit=True
        with self.assertRaises(OSError):w.request(dict(abi=m.ABI,op='apply',request_seq=1,yaw_q=0,pitch_q=0,speed_code=2,duration_ms=12000))
        n=len(w.g05.writes)
        with self.assertRaises(ValueError):w.request(sense(2))
        self.assertEqual(len(w.g05.writes),n);self.assertTrue(w.poisoned)
    def test_source_seq_and_null_quality_rejected_before_arm(self):
        w=worker();r=sense(1);r['quality']=15
        with self.assertRaises(ValueError):w.request(r)
        self.assertEqual(w.trace.r[0x2c],0)
    def test_monotonic_tags_and_counter_exhaustion_no_reset(self):
        w=worker();w.trace.r[0x2c]=m.U32
        with self.assertRaises(ValueError):w.request(sense(1))
        self.assertEqual(w.trace.r[0x2c],m.U32)
    def test_client_never_retries_unknown_transport(self):
        out=io.BytesIO();c=StreamClient(out,io.BytesIO(b'bad\n'),boot_id='b',build_id='c',request_hash='d')
        c.ready=True
        with self.assertRaises(ValueError):c.apply(yaw_q=0,pitch_q=0)
        n=len(out.getvalue())
        with self.assertRaises(ValueError):c.apply(yaw_q=0,pitch_q=0)
        self.assertEqual(len(out.getvalue()),n)

if __name__=='__main__':unittest.main()
