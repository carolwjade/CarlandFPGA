"""New component-only fake-bus controls. No hardware/network/engine evidence."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import tempfile
import hashlib

CANDIDATE = Path(__file__).resolve().parents[5]
WNEW = Path('C:/Users/CarlJade/.codex/worktrees/a-b56-reader/FPGA多机协作开发')


class Clock:
    component_only = True
    def __init__(self): self.value = 1_000_000_000
    def __call__(self): self.value += 1; return self.value


def context():
    return dict(operation_id='A-PRIVATE-LIVE-TEST', request_hash='a'*64, tested_commit='b'*40,
                build_manifest_sha256='c'*64, boot_id='d'*36, session_id='fresh-session', tag=123,
                clock_domain_id='e'*32)


class Bus:
    """Explicit component fake for the frozen private CSR lane FSM."""
    component_only = True
    def __init__(self, fail=None):
        self.reg = {}; self.generation = 0; self.trigger = 0; self.channel = 0
        self.running = self.valid = False; self.writes = []; self.fail = fail
    def write(self, offset, value):
        self.writes.append((offset,value))
        if offset != 0x0c: self.reg[offset] = value; return
        if value == 1: self.running = self.valid = False; self.reg[0x14] = 0
        elif value == 2:
            self.running = True; self.generation += 1; self.reg[0x14] = self.reg[0x10]
        elif value == 4:
            self.trigger += 1; self.channel = 0; self.valid = True
            if self.fail == 'trigger': raise OSError('component simulated unknown TRIGGER after write')
        elif value == 8:
            self.channel += 1; self.valid = self.channel < 4
            if self.fail == 'ack': raise OSError('component simulated unknown ACK after write')
    def read(self, offset):
        if offset == 0: return 0x44505953
        if offset == 4: return 0x10000
        if offset == 8: return 7 if self.valid else (1 if self.running else 0)
        if offset == 0x18: return self.generation
        if offset == 0x1c: return self.trigger
        if offset == 0x24: return self.trigger*4
        if offset == 0x28: return self.trigger
        if offset == 0x30: return (self.trigger-1)*4+self.channel+1 if self.valid else self.trigger*4
        if 0x80 <= offset <= 0xa4:
            ch=self.channel; quality=(self.reg[0x70] >> (8*ch)) & 255
            raw=(self.reg[0x40+4*ch],ch|(quality<<8),self.reg[0x50+8*ch],self.reg[0x54+8*ch],
                 (self.trigger-1)*4,(self.trigger-1)*4+3,self.reg[0x14],self.trigger,self.generation,987)
            value=raw[(offset-0x80)//4]
            return value+1 if self.fail=='lane' and offset==0x80 else value
        return self.reg.get(offset,0)


class Helpers:
    component_only = True
    RESULT_REGS=tuple(range(0x80,0xa8,4))
    @staticmethod
    def session(bus,tag,generation,trigger):
        if (bus.read(0x14),bus.read(0x18),bus.read(0x1c)) != (tag,generation,trigger): raise ValueError('session changed')
    @staticmethod
    def wait_for(bus,predicate,clock,sleep,deadline,label,check_fault=True):
        if clock() >= deadline: raise ValueError('deadline')
        value=bus.read(8)
        if not predicate(value): raise ValueError(label)
        return value
    @staticmethod
    def counters(bus): return tuple(bus.read(x) for x in (0x24,0x28,0x30))


class NewLiveTests(unittest.TestCase):
    def modules(self):
        codec=CANDIDATE/'competition/deepeye/integration/private_pl_stream.py'
        agent=CANDIDATE/'competition/deepeye/tools/diagnostic/private_pl_live_agent.py'
        self.assertTrue(codec.is_file(), 'new strict stream implementation not present (expected initial RED)')
        self.assertTrue(agent.is_file(), 'new agent implementation not present (expected initial RED)')
        for root in (str(CANDIDATE),str(WNEW)):
            if root not in sys.path: sys.path.insert(0,root)
        def load(name,path):
            if name in sys.modules:return sys.modules[name]
            spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
            sys.modules[name]=module;spec.loader.exec_module(module);return module
        return load('competition.deepeye.integration.private_pl_stream',codec),load('private_pl_agent_component',agent)
    def request(self,c,seq=1):
        return c.encode({'schema':1,'kind':'diagnostic_scan','context':context(),'request_seq':seq,
                         'source_id':4,'source':'software_fixture',
                         'values':[17,4095,32769,65280],'qualities':[2,17,128,254],
                         'original_host_qpc_ns':[1_000_000_001+i+(seq-1)*100 for i in range(4)]})
    def session(self,a,bus=None):
        clock=Clock();bus=bus or Bus();journal=[]
        session=a._LiveSession(bus,Helpers,context(),lambda:clock()/1e9,lambda _:None,journal.append,
                               total_seconds=10,poll_seconds=2,max_scans=3)
        return session,bus,clock,journal
    def test_roundtrip_preserves_original_qpc_and_opaque_quality(self):
        c,a=self.modules();obj=c.decode_request(self.request(c),context(),1)
        self.assertEqual(obj['original_host_qpc_ns'],[1000000001,1000000002,1000000003,1000000004])
        self.assertEqual(obj['qualities'],[2,17,128,254])
    def test_codec_rejects_duplicate_json_fields(self):
        c,a=self.modules()
        with self.assertRaises(ValueError):c.decode_request(b'{"schema":1,"schema":1}\n',context(),1)
    def test_codec_rejects_oversized_and_unterminated(self):
        c,a=self.modules()
        for raw in (b'x'*16385,self.request(c)[:-1]):
            with self.assertRaises(ValueError):c.decode_request(raw,context(),1)
    def test_codec_rejects_extra_field_and_bool_values(self):
        c,a=self.modules();obj=json.loads(self.request(c));obj['movement_authorized']=True
        with self.assertRaises(ValueError):c.decode_request(c.encode(obj),context(),1)
        obj=json.loads(self.request(c));obj['values'][0]=True
        with self.assertRaises(ValueError):c.decode_request(c.encode(obj),context(),1)
    def test_identity_domain_and_sequence_mismatch_reject(self):
        c,a=self.modules()
        for key in ('session_id','clock_domain_id','request_hash'):
            obj=json.loads(self.request(c));obj['context'][key]='bad'
            with self.assertRaises(ValueError):c.decode_request(c.encode(obj),context(),1)
        with self.assertRaises(ValueError):c.decode_request(self.request(c),context(),2)
    def test_qpc_reversal_and_nonfinite_reject(self):
        c,a=self.modules();obj=json.loads(self.request(c));obj['original_host_qpc_ns'][2]=0
        with self.assertRaises(ValueError):c.decode_request(c.encode(obj),context(),1)
        with self.assertRaises(ValueError):c.decode_request(b'{"x":NaN}\n',context(),1)
    def test_one_start_two_triggers_eight_ack_stable_generation(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);s.start()
        x=s.scan(c.decode_request(self.request(c),context(),1));y=s.scan(c.decode_request(self.request(c,2),context(),2))
        self.assertEqual((x['generation'],y['generation']),(1,1));self.assertEqual((x['trigger_id'],y['trigger_id']),(1,2))
        self.assertEqual([r['raw_words'][4] for r in y['captures']],[4]*4)
        self.assertEqual([v for p,v in bus.writes if p==12].count(2),1)
        self.assertEqual([v for p,v in bus.writes if p==12].count(4),2)
        self.assertEqual([v for p,v in bus.writes if p==12].count(8),8)
        self.assertTrue(s.finish('component EOF')['confirmed'])
    def test_unknown_trigger_terminal_no_replay(self):
        c,a=self.modules();s,bus,clock,j=self.session(a,Bus('trigger'));s.start();req=c.decode_request(self.request(c),context(),1)
        with self.assertRaises(OSError):s.scan(req)
        with self.assertRaises(ValueError):s.scan(req)
        self.assertEqual([v for p,v in bus.writes if p==12].count(4),1)
        self.assertTrue(any(x['event']=='trigger_started_unknown' for x in j));self.assertTrue(s.finish('error')['confirmed'])
    def test_unknown_ack_terminal_no_replay(self):
        c,a=self.modules();s,bus,clock,j=self.session(a,Bus('ack'));s.start();req=c.decode_request(self.request(c),context(),1)
        with self.assertRaises(OSError):s.scan(req)
        with self.assertRaises(ValueError):s.scan(req)
        self.assertEqual([v for p,v in bus.writes if p==12].count(8),1)
        self.assertTrue(s.finish('error')['confirmed'])
    def test_bad_raw_lane_rejects_before_ack(self):
        c,a=self.modules();s,bus,clock,j=self.session(a,Bus('lane'));s.start()
        with self.assertRaises(ValueError):s.scan(c.decode_request(self.request(c),context(),1))
        self.assertEqual([v for p,v in bus.writes if p==12].count(8),0);self.assertTrue(s.finish('badlane')['confirmed'])
    def test_duplicate_scan_terminal(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);s.start();req=c.decode_request(self.request(c),context(),1);s.scan(req)
        with self.assertRaises(ValueError):s.scan(req)
        self.assertEqual([v for p,v in bus.writes if p==12].count(4),1);s.finish('duplicate')
    def test_global_deadline_final_stop_once(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);s.start();clock.value+=11_000_000_000
        with self.assertRaises(ValueError):s.scan(c.decode_request(self.request(c),context(),1))
        first=s.finish('expired');self.assertTrue(first['confirmed']);count=len(bus.writes)
        self.assertEqual(s.finish('again'),first);self.assertEqual(len(bus.writes),count)
    def test_eof_and_malformed_input_finish_stop(self):
        c,a=self.modules()
        for data in ([None],[b'{}\n']):
            s,bus,clock,j=self.session(a);out=[];it=iter(data)
            a._serve(s,lambda:next(it,None),out.append,c)
            self.assertTrue(s.cleanup['confirmed']);self.assertEqual(out[-1]['kind'],'diagnostic_stopped')
    def test_signal_failure_finishes_stop(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);out=[]
        def interrupted():raise KeyboardInterrupt('component simulated signal')
        a._serve(s,interrupted,out.append,c);self.assertTrue(s.cleanup['confirmed'])
    def test_host_marks_unknown_before_send_no_reissue(self):
        c,a=self.modules();clock=Clock();owner=c._HostOwner(context(),clock)
        raw=owner.next_request([1,2,3,4],[0,1,2,3]);obj=json.loads(raw)
        self.assertEqual(obj['request_seq'],1);self.assertEqual(len(obj['original_host_qpc_ns']),4)
        with self.assertRaises(ValueError):owner.next_request([1,2,3,4],[0,1,2,3])
        self.assertEqual(owner.state,'FAILED')
    def test_host_rejects_uncorrelated_capture_and_clock_reversal(self):
        c,a=self.modules();clock=Clock();owner=c._HostOwner(context(),clock);owner.next_request([1,2,3,4],[0,1,2,3])
        with self.assertRaises(ValueError):owner.accept(c.encode({'kind':'diagnostic_capture'}))
        self.assertEqual(owner.state,'FAILED')
        clock=Clock();owner=c._HostOwner(context(),clock);clock.value=-1
        with self.assertRaises(ValueError):owner.next_request([1,2,3,4],[0,1,2,3])
    def test_public_host_owner_rejects_component_fake_clock(self):
        c,a=self.modules()
        with self.assertRaises(ValueError):c.HostOwner(context(),Clock())
    def test_stop_survives_journal_throw_before_log(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);s.start();before=len(bus.writes)
        def broken(_):raise OSError('component journal write/flush failure')
        s.journal=broken;cleanup=s.finish('journal failure')
        self.assertEqual(bus.writes[before],(12,1));self.assertTrue(cleanup['confirmed'])
        self.assertTrue(cleanup['secondary_errors'])
    def test_stop_survives_clock_throw_without_false_timing_proof(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);s.start();before=len(bus.writes)
        def broken():raise OSError('component clock failure')
        s.clock=broken;cleanup=s.finish('clock failure')
        self.assertEqual(bus.writes[before],(12,1));self.assertTrue(cleanup['confirmed'])
        self.assertFalse(cleanup['physical_deadline_proven']);self.assertTrue(cleanup['secondary_errors'])
    def test_emergency_stop_bypasses_normal_bus_logging(self):
        c,a=self.modules();raw=Bus()
        class Wrapper:
            def __init__(self):self.mmio=raw;self.bad=False
            def read(self,offset):return raw.read(offset)
            def write(self,offset,value):
                if self.bad:raise OSError('component normal Bus pre-MMIO log failed')
                raw.write(offset,value)
        wrapped=Wrapper();s,bus,clock,j=self.session(a,wrapped);s.start();wrapped.bad=True
        self.assertTrue(s.finish('bus logging failed')['confirmed']);self.assertEqual(raw.writes[-1],(12,1))
    def test_trigger_and_ack_postwrite_journal_fault_never_replayed(self):
        c,a=self.modules()
        for action in (4,8):
            raw=Bus()
            class Wrapper:
                mmio=raw
                def read(self,offset):return raw.read(offset)
                def write(self,offset,value):
                    raw.write(offset,value)
                    if offset==12 and value==action:raise OSError('component postwrite journal failure')
            s,bus,clock,j=self.session(a,Wrapper());s.start();req=c.decode_request(self.request(c),context(),1)
            with self.assertRaises(OSError):s.scan(req)
            with self.assertRaises(ValueError):s.scan(req)
            self.assertTrue(s.finish('postwrite journal')['confirmed'])
            self.assertEqual([v for p,v in raw.writes if p==12].count(action),1)
    def test_constructor_failure_cleanup_uses_independent_raw_mmio(self):
        c,a=self.modules();raw=Bus();raw.running=True;raw.reg[0x14]=123
        class Wrapper:
            mmio=raw
            def write(self,*args):raise OSError('component constructor-path normal logging fault')
            def read(self,*args):raise OSError('component normal Bus read logging fault')
        result=a._stop_without_session(Wrapper(),'constructor clock failed')
        self.assertTrue(result['confirmed']);self.assertEqual(raw.writes,[(12,1)])
        self.assertFalse(result['physical_deadline_proven'])
    def test_primary_decode_error_survives_terminal_stdout_failure(self):
        c,a=self.modules();s,bus,clock,j=self.session(a)
        def write(item):
            if item['kind']=='diagnostic_stopped':raise BrokenPipeError('component terminal stdout failed')
        code=a._serve(s,lambda:b'{}\n',write,c)
        self.assertEqual(code,2);self.assertEqual(s.primary_error['type'],'ValueError')
        self.assertTrue(any(x['type']=='BrokenPipeError' for x in s.secondary_errors));self.assertTrue(s.cleanup['confirmed'])
    def test_host_accepts_two_original_fresh_correlated_frames(self):
        c,a=self.modules();s,bus,clock,j=self.session(a);owner=c._HostOwner(context(),Clock())
        owner.accept_ready(c.encode(c.record('diagnostic_ready',context(),**s.start())))
        for seq in (1,2):
            raw=owner.next_request([17,4095,32769,65280],[2,17,128,254]);request=c.decode_request(raw,context(),seq)
            result=s.scan(request)
            import hashlib
            frame=c.record('diagnostic_capture',context(),request_seq=seq,request_sha256=hashlib.sha256(raw).hexdigest(),**result)
            self.assertEqual(owner.accept(c.encode(frame))['request_seq'],seq)
        with self.assertRaises(ValueError):owner.accept(c.encode(frame))
        self.assertTrue(s.finish('done')['confirmed'])
    def test_host_rejects_bool_float_response_generation_trigger_counters(self):
        c,a=self.modules()
        for field in ('generation','trigger_id','pipeline_counters','final_counters'):
            s,bus,clock,j=self.session(a);owner=c._HostOwner(context(),Clock())
            owner.accept_ready(c.encode(c.record('diagnostic_ready',context(),**s.start())))
            raw=owner.next_request([17,4095,32769,65280],[2,17,128,254]);request=c.decode_request(raw,context(),1)
            result=s.scan(request)
            import hashlib
            frame=c.record('diagnostic_capture',context(),request_seq=1,request_sha256=hashlib.sha256(raw).hexdigest(),**result)
            if field in ('generation','trigger_id'):frame[field]=True
            elif field=='pipeline_counters':frame['captures'][0][field][1]=1.0
            else:frame[field][0]=4.0
            with self.assertRaises(ValueError):owner.accept(c.encode(frame))
            s.finish('typed mismatch')
    def test_host_cannot_extend_diagnostic_age_cap_above_100ms(self):
        c,a=self.modules()
        with self.assertRaises(ValueError):c._HostOwner(context(),Clock(),max_age_ns=100_000_001)
    def test_blocked_original_stdout_is_bounded_and_stop_survives(self):
        c,a=self.modules();s,bus,clock,j=self.session(a)
        from unittest.mock import patch
        with patch.object(a.os,'set_blocking'),patch.object(a.select,'select',return_value=([],[],[])),patch.object(a.os,'write') as write:
            output=a._OutputLines(123,s,c,0.05)
            code=a._serve(s,lambda:None,output,c)
            self.assertEqual(code,2);self.assertTrue(s.cleanup['confirmed']);write.assert_not_called()
    def test_repeated_signal_is_masked_during_raw_stop(self):
        c,a=self.modules();raw=Bus();s,bus,clock,j=self.session(a,raw);s.start()
        from unittest.mock import patch
        def throwing(signum,frame):raise InterruptedError('component second signal')
        handlers={a.signal.SIGINT:throwing,a.signal.SIGTERM:throwing}
        def install(sig,new):old=handlers[sig];handlers[sig]=new;return old
        original_write=raw.write
        def write(offset,value):
            if offset==12 and value==1 and handlers[a.signal.SIGTERM] is not a.signal.SIG_IGN:
                handlers[a.signal.SIGTERM](a.signal.SIGTERM,None)
            original_write(offset,value)
        raw.write=write
        with patch.object(a.signal,'signal',side_effect=install):result=s.finish('first signal')
        self.assertTrue(result['confirmed']);self.assertIs(handlers[a.signal.SIGTERM],throwing)
    def test_physical_limits_reject_before_runtime_or_load(self):
        c,a=self.modules()
        for args in ((0,2,1,50),(True,2,1,50),(10,3,1,50),(10,2,17,50),(10,2,1,101)):
            with self.assertRaises(ValueError):a._session_limits(*args)
    def host_module(self):
        self.modules();path=CANDIDATE/'competition/deepeye/tools/diagnostic/run_private_pl_live.py'
        self.assertTrue(path.is_file(),'new two-phase original-owner supervisor missing (expected RED)')
        name='private_pl_host_component'
        if name in sys.modules:return sys.modules[name]
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module);return module
    def gate_fixture(self,h):
        out=Path(tempfile.mkdtemp(prefix='component-gate-',dir=CANDIDATE.parent))
        class Qpc(Clock):metadata={'domain_id':'e'*32,'kind':'qpc_raw_v1','authenticated':False,'measured_timing':False}
        seed=context();seed.pop('request_hash');seed.pop('clock_domain_id')
        template={'context':seed,'agent_source_commit':'b'*40}
        prepared=h._prepare(out,template,Qpc(),{'component_only':True},{'pid':123,'component_only':True})
        req={'context':prepared['context_seed'],'agent_source_commit':'b'*40,'phase':'private_live','execute_a':True,'attempts':1}
        req['request_hash']=hashlib.sha256(h.canonical(req)).hexdigest()
        request_raw=h.canonical(req);(out/'LIVE_REQUEST.json').write_bytes(request_raw)
        activation={'allowed':True,'attempts':1,'prepared_sha256':hashlib.sha256((out/'HOST_PREPARED.json').read_bytes()).hexdigest(),
                    'request_hash':req['request_hash'],'request_file_sha256':hashlib.sha256(request_raw).hexdigest(),
                    'agent_source_commit':'b'*40,'remote_directory':'/tmp/deepeye-a-private-live-'+req['request_hash'][:16]}
        (out/'ROOT_ACTIVATION.json').write_bytes(h.canonical(activation))
        return out,prepared,req,activation
    def test_two_phase_claim_is_exclusive_binds_same_clock_and_request(self):
        h=self.host_module();out,prepared,req,activation=self.gate_fixture(h)
        result=h._claim(out,prepared);self.assertEqual(result['request']['context']['clock_domain_id'],'e'*32)
        with self.assertRaises((ValueError,FileExistsError)):h._claim(out,prepared)
    def test_activation_rejects_changed_request_or_foreign_prepared(self):
        h=self.host_module()
        for field in ('request','prepared'):
            out,prepared,req,activation=self.gate_fixture(h)
            if field=='request':(out/'LIVE_REQUEST.json').write_bytes(b'{}')
            else:activation['prepared_sha256']='f'*64;(out/'ROOT_ACTIVATION.json').write_bytes(h.canonical(activation))
            with self.assertRaises(ValueError):h._claim(out,prepared)
            self.assertFalse((out/'ACTIVATION_CONSUMED.json').exists())
    def test_prepare_wait_expiry_performs_no_transport(self):
        h=self.host_module();out,prepared,req,activation=self.gate_fixture(h)
        (out/'ROOT_ACTIVATION.json').rename(out/'NOT_ACTIVATED.json')
        from unittest.mock import patch
        with patch.object(h.time,'monotonic',side_effect=[0.0,121.0]),patch.object(h.time,'sleep'):
            with self.assertRaises(TimeoutError):h._wait_activation(out,120)
        self.assertFalse((out/'ACTIVATION_CONSUMED.json').exists())
    def test_credential_read_is_exactly_one_line_without_read_ahead(self):
        c,a=self.modules();chunks=list(b'component-secret\nDATA')
        from unittest.mock import patch
        def read(fd,size):self.assertEqual((fd,size),(77,1));return bytes([chunks.pop(0)])
        with patch.object(a.os,'set_blocking'),patch.object(a.select,'select',return_value=([77],[],[])),patch.object(a.os,'read',side_effect=read):credential=a._read_credential(77)
        self.assertEqual(credential,b'component-secret\n');self.assertEqual(bytes(chunks),b'DATA')
    def test_sudo_zero_or_one_credential_consumption_cannot_enter_fifo(self):
        c,a=self.modules()
        for consumed in (0,1):
            class PrivatePipe:
                def __init__(self):self.data=b'';self.closed=False
                def write(self,data):self.data+=data;return len(data)
                def flush(self):pass
                def close(self):self.closed=True
            pipe=PrivatePipe();fifo_data=b'{"nonsecret":"diagnostic"}\n'
            a._send_sudo_credential(pipe,b'component-secret\n')
            ignored_or_consumed=pipe.data if consumed else b''
            self.assertTrue(pipe.closed);self.assertNotIn(b'component-secret',fifo_data)
            self.assertEqual(pipe.data,b'component-secret\n')
    def test_fifo_validator_rejects_real_regular_file(self):
        c,a=self.modules();root=Path(tempfile.mkdtemp(prefix='component-nonfifo-',dir=CANDIDATE.parent));path=root/'regular'
        path.write_bytes(b'not fifo');value=path.stat()
        with self.assertRaises(ValueError):a._validate_fifo(path,None,value.st_dev,value.st_ino,value.st_uid)
    def test_relay_eof_closes_unique_fifo_writer(self):
        c,a=self.modules()
        class Child:
            def poll(self):return None
        from unittest.mock import patch
        with patch.object(a.os,'set_blocking'),patch.object(a.select,'select',return_value=([111],[],[])),patch.object(a.os,'read',return_value=b''),patch.object(a.os,'close') as close:
            result=a._pump_input(111,222,Child(),1)
            self.assertEqual(result['data_bytes'],0);close.assert_called_once_with(222)
    def test_prepare_gate_cannot_exceed_120_seconds(self):
        h=self.host_module();out=Path(tempfile.mkdtemp(prefix='component-gatecap-',dir=CANDIDATE.parent))
        from unittest.mock import patch
        with patch.object(h.time,'monotonic',side_effect=[0.0,1000.0]),patch.object(h.time,'sleep'):
            with self.assertRaises(ValueError):h._wait_activation(out,121)
    def test_missing_credential_deadline_has_no_read_or_sudo(self):
        c,a=self.modules()
        from unittest.mock import patch
        with patch.object(a.os,'set_blocking'),patch.object(a.select,'select',return_value=([],[],[])),patch.object(a.os,'read') as read,patch.object(a.subprocess,'Popen') as popen:
            with self.assertRaises(ValueError):a._read_credential(77)
            read.assert_not_called();popen.assert_not_called()
    def test_relay_stage_is_exclusive_and_has_only_nonsecret_identity(self):
        c,a=self.modules();out=Path(tempfile.mkdtemp(prefix='component-stage-',dir=CANDIDATE.parent))
        a._relay_stage(out,'unknown','a'*64,'b'*64,(1,2,3),child_pid=123,reason_code='RELAY_ERROR_UNKNOWN')
        raw=(out/'RELAY_unknown.json').read_bytes();obj=json.loads(raw)
        self.assertEqual(obj['fifo_identity'],{'device':1,'inode':2,'owner':3});self.assertEqual(obj['original_child_pid'],123)
        self.assertNotIn(b'component-secret',raw)
        with self.assertRaises(FileExistsError):a._relay_stage(out,'unknown','a'*64,'b'*64,(1,2,3),reason_code='RELAY_ERROR_UNKNOWN')
    def test_isolated_import_check_uses_derived_package_without_preparing(self):
        h=self.host_module();root=Path(tempfile.mkdtemp(prefix='component-import-',dir=CANDIDATE.parent))
        tools=root/'competition/deepeye/tools/diagnostic';tools.mkdir(parents=True)
        integration=root/'competition/deepeye/integration';integration.mkdir(parents=True)
        path=tools/'run_private_pl_live.py';path.write_bytes(Path(h.__file__).read_bytes())
        (integration/'host_clock.py').write_text("def qpc_clock_for_new_run(): raise AssertionError('component import check must not prepare')\n",encoding='utf-8')
        (integration/'private_pl_stream.py').write_text("COMPONENT_ONLY=True\n",encoding='utf-8')
        (tools/'private_pl_live_agent.py').write_text('# component import fixture only\n',encoding='utf-8')
        (tools/'a_b56_memory_safe_collector.py').write_text('# component import fixture only\n',encoding='utf-8')
        template=root/'template.json';template.write_bytes(b'{}');out=root/'not-prepared'
        import subprocess
        result=subprocess.run([sys.executable,'-I','-B',str(path),'--template',str(template),'--template-sha256',hashlib.sha256(b'{}').hexdigest(),
                               '--out',str(out),'--import-check-only'],capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr.decode());self.assertFalse(out.exists())
        self.assertIn(b'imports_and_bytes_only',result.stdout)
    def test_original_ssh_constructor_failure_preserves_wait_and_closes_handles(self):
        h=self.host_module();out=Path(tempfile.mkdtemp(prefix='component-ssh-fail-',dir=CANDIDATE.parent))
        import io
        class Handle:
            closed=False
            def Close(self):self.closed=True
        class Original:
            pid=123;returncode=None;_handle=Handle()
            stdin=io.BytesIO();stdout=io.BytesIO();stderr=io.BytesIO()
            def kill(self):self.returncode=125
            def wait(self,timeout):return self.returncode
        original=Original()
        from unittest.mock import patch
        with patch.object(h.subprocess,'Popen',return_value=original),patch.object(h,'_Job',side_effect=OSError('component job assignment fail')):
            with self.assertRaises(OSError):h._Transport(['component-only-no-SSH'],out,Clock())
        saved=json.loads((out/'SSH_CONSTRUCTOR_TERMINAL.json').read_bytes())
        self.assertEqual(saved['original_pid'],123);self.assertTrue(saved['original_wait_completed'])
        self.assertTrue(saved['credentials_never_sent']);self.assertTrue(original._handle.closed)
        self.assertTrue(original.stdin.closed and original.stdout.closed and original.stderr.closed)
    def test_isolated_real_source_preflight_resolves_without_prepare(self):
        c,a=self.modules();h=self.host_module();root=Path(tempfile.mkdtemp(prefix='real-source-import-',dir=CANDIDATE.parent))
        tools=root/'competition/deepeye/tools/diagnostic';tools.mkdir(parents=True)
        integration=root/'competition/deepeye/integration';integration.mkdir(parents=True)
        copied={tools/'run_private_pl_live.py':Path(h.__file__),tools/'private_pl_live_agent.py':Path(a.__file__),
                integration/'private_pl_stream.py':Path(c.__file__),integration/'host_clock.py':WNEW/'competition/deepeye/integration/host_clock.py',
                tools/'a_b56_memory_safe_collector.py':WNEW/'competition/deepeye/tools/diagnostic/a_b56_memory_safe_collector.py'}
        for dst,src in copied.items():dst.write_bytes(src.read_bytes())
        self.assertEqual(hashlib.sha256((integration/'host_clock.py').read_bytes()).hexdigest(),
                         '091accae52c376d259d0057f7b93b23dc5f4143508025beec88394c4b657e376')
        template=root/'template.json';template.write_bytes(b'{}');out=root/'not-prepared'
        import subprocess
        argv=[sys.executable,'-I','-B','-X','utf8',str(tools/'run_private_pl_live.py'),'--template',str(template),
              '--template-sha256',hashlib.sha256(b'{}').hexdigest(),'--out',str(out),'--import-check-only']
        process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:stdout,stderr=process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill();stdout,stderr=process.communicate();raise
        (root/'preflight.stdout.bin').write_bytes(stdout);(root/'preflight.stderr.bin').write_bytes(stderr)
        (root/'preflight-receipt.json').write_text(json.dumps({'argv':argv,'original_pid':process.pid,'actual_exit':process.returncode,
             'original_wait_completed':True,'copied_source_pins':{str(dst.relative_to(root)):hashlib.sha256(dst.read_bytes()).hexdigest() for dst in copied},
             'QPC_prepare_performed':False,'SSH_board_performed':False},indent=2),encoding='utf-8')
        self.assertEqual(process.returncode,0,stderr.decode());self.assertFalse(out.exists())
        result=json.loads(stdout);self.assertEqual(result['scope'],'imports_and_bytes_only')
        self.assertEqual(result['codec']['sha256'],hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest())
        self.assertEqual(result['host_clock']['sha256'],'091accae52c376d259d0057f7b93b23dc5f4143508025beec88394c4b657e376')
    def test_fixed_private_prelude_has_no_read_ahead_and_expires(self):
        c,a=self.modules();chunks=list(b'DEEPEYE_PRIVATE_INPUT_V1\nDATA')
        from unittest.mock import patch
        def read(fd,size):self.assertEqual((fd,size),(77,1));return bytes([chunks.pop(0)])
        with patch.object(a.select,'select',return_value=([77],[],[])),patch.object(a.os,'read',side_effect=read):
            a._read_prelude(77,a.time.monotonic()+1)
        self.assertEqual(bytes(chunks),b'DATA')
        with patch.object(a.os,'read') as read:
            with self.assertRaises(ValueError):a._read_prelude(77,0)
            read.assert_not_called()
    def test_qualification_blocked_stdout_is_bounded(self):
        c,a=self.modules()
        from unittest.mock import patch
        with patch.object(a.os,'set_blocking'),patch.object(a.select,'select',return_value=([],[],[])),patch.object(a.os,'write') as write:
            with self.assertRaises(ValueError):a._qualification_output({'component_only':True},a.time.monotonic()+1)
            write.assert_not_called()
    def test_qualification_failure_is_durable_without_pynq(self):
        c,a=self.modules();root=Path(tempfile.mkdtemp(prefix='component-qual-fail-',dir=CANDIDATE.parent))
        from types import SimpleNamespace
        args=SimpleNamespace(request=root/'request.json',fifo_inode=2,fifo_owner=3)
        from unittest.mock import patch
        with (patch.object(a.os,'geteuid',return_value=0,create=True),patch.object(a,'_open_fifo',return_value=99),patch.object(a.os,'set_blocking'),
              patch.object(a,'_qualification_output',side_effect=ValueError('component output blocked')),patch.object(a.os,'close')):
            code=a._qualification(args,{'phase':'relay_qualification','execute_a':False})
        self.assertEqual(code,2);record=json.loads((root/'QUALIFICATION_FAILURE.json').read_bytes())
        self.assertEqual(record['reason_code'],'QUALIFICATION_IO_FAILURE');self.assertFalse(record['PYNQ_imported'])


if __name__=='__main__':unittest.main(verbosity=2)
