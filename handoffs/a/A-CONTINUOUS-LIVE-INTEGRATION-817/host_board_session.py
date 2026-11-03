"""Root-only contained persistent SSH transport; no effects on import.

No mission duration/count ceiling. One in-flight call, necessary per-call bounds,
no reconnect/resend, pipe EOF + actual FPGA TTL are terminal safety backstops.
"""
import hashlib,json,pathlib,queue,shlex,subprocess,threading,time
from local_stream_client import StreamClient

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

class _Lines:
    def __init__(self,pipe):
        self.pipe=pipe;self.q=queue.Queue(maxsize=2);self.timeout=35.;self.error=None
        self.thread=threading.Thread(target=self._read,daemon=True,name='board800-stdout');self.thread.start()
    def _read(self):
        try:
            while True:
                line=self.pipe.readline(32770)
                self.q.put(line,timeout=3)
                if not line or len(line)>32768:return
        except BaseException as e:self.error=type(e).__name__
    def readline(self,limit):
        try:return self.q.get(timeout=self.timeout)
        except queue.Empty:raise TimeoutError('BOARD_RESPONSE_UNKNOWN_NO_REPLAY')

class BoardSession:
    def __init__(self,*,repository_root,stage_directory,evidence_directory):
        self.root=pathlib.Path(repository_root);self.stage=pathlib.Path(stage_directory)
        self.evidence=pathlib.Path(evidence_directory);self.evidence.mkdir()
        self.plan=json.loads((self.stage/'loader-plan.json').read_bytes())
        self.manifest=json.loads((self.stage/'MANIFEST.json').read_bytes())
        self.proc=None;self.client=None;self.closed=False;self.stderr_count=0;self.stderr_error=None
        self.log=(self.evidence/'requests.jsonl').open('xb',buffering=0)
        self.owner=threading.get_ident();self.last=None
    def record(self,value):self.log.write(canonical(value)+b'\n')
    def _owned(self):
        if threading.get_ident()!=self.owner or self.closed:raise ValueError('ROOT_SINGLE_IO_THREAD')
    def start(self):
        self._owned();assert self.proc is None
        assert not (self.evidence/'STARTED.json').exists()
        actual=json.loads((self.stage/'UPLOAD_ACTUAL.json').read_bytes())
        assert actual['files']==self.manifest['files'] and actual['boot_id']==self.plan['boot_id']
        route=json.loads((self.root/'.planning/deepeye-resume-20261018/board-preflight-20261021/started.private.json').read_bytes())['argv'][:-1]
        assert route[-1]=='xilinx@fe80::200:5ff:fe6b:1f5%8';route[-1]='xilinx@fe80::200:5ff:fe6b:1f5%9'
        assert hashlib.sha256(pathlib.Path(route[0]).read_bytes()).hexdigest()=='98d447730047f5df91373e852d057928a921c3d1e89938700ab656ba84b19dc8'
        assert hashlib.sha256(pathlib.Path(route[14].split('=',1)[1]).read_bytes()).hexdigest()=='31a10124495b85e9b62bbf46418393124888b2f381f9a4d1334521760ada4418'
        remote=self.manifest['remote']
        args=['/usr/local/share/pynq-venv/bin/python3','-I','-B',remote+'/remote_live_board_a.py','--serve','--source-root',remote+'/snapshot','--plan',remote+'/loader-plan.json','--identity-json',remote+'/identity.json','--journal',remote+'/live800.jsonl']
        command="/usr/bin/sudo -S -p '' /usr/bin/env BOARD=Pynq-Z2 XILINX_XRT=/usr "+' '.join(shlex.quote(x) for x in args)
        (self.evidence/'STARTED.json').write_bytes(canonical(dict(operation_id=self.plan['operation_id'],request_hash=self.plan['request_sha256'],boot_id=self.plan['boot_id'],new_unique_operation=True,monotonic_ns=time.monotonic_ns()))+b'\n')
        self.proc=subprocess.Popen(route+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
        (self.evidence/'PROCESS.json').write_bytes(canonical(dict(pid=self.proc.pid,started=True))+b'\n')
        self.lines=_Lines(self.proc.stdout)
        self.stderr_file=(self.evidence/'stderr.bin').open('xb',buffering=0)
        def drain():
            try:
                while True:
                    data=self.proc.stderr.read(4096)
                    if not data:return
                    remaining=max(0,2*1024*1024-self.stderr_count)
                    self.stderr_file.write(data[:remaining]);self.stderr_count+=len(data)
            except BaseException as e:self.stderr_error=type(e).__name__
        self.stderr_thread=threading.Thread(target=drain,daemon=True,name='board800-stderr');self.stderr_thread.start()
        # Existing private input is consumed once, never printed/hashed/copied.
        credential_path=self.root/'.local/a429/sudo-line.private.bin'
        credential=credential_path.read_bytes()
        assert 1<=len(credential)<=1024 and credential.endswith(b'\n') and credential.count(b'\n')==1
        assert self.proc.stdin.write(credential)==len(credential);self.proc.stdin.flush();del credential
        self.client=StreamClient(self.proc.stdin,self.lines,boot_id=self.plan['boot_id'],build_id=self.plan['build_id'],request_hash=self.plan['request_sha256'])
        result=self.client.initialize();self.lines.timeout=6.;self.record(dict(event='init-returned',response=result,host_qpc_ns=time.perf_counter_ns()));return result
    def request(self,op,**fields):
        self._owned();assert self.client is not None
        before=time.perf_counter_ns();self.record(dict(event='request-intent',op=op,fields=fields,host_before_ns=before))
        response=self.client.request(op,**fields);returned=time.perf_counter_ns()
        self.last=dict(response=response,host_before_ns=before,host_returned_ns=returned,response_sha256=hashlib.sha256(canonical(response)).hexdigest())
        if op=='apply':
            r=response['result'];ttl=fields['duration_ms']*1000000
            assert 0<r['remaining_ns']<=ttl and returned>=before
            # Host send precedes actual COMMIT. Either lower bound suffices;
            # their minimum also accounts conservatively for returned remaining.
            self.last['host_deadline_qpc_ns']=min(before+ttl,before+r['remaining_ns'])
        self.record(dict(event='request-returned',**self.last));return self.last
    def sense(self,*,source_seq,adc_tick_ms,em_tick_ms,counts,quality,source_digest):
        return self.request('sense',source_seq=source_seq,adc_tick_ms=adc_tick_ms,em_tick_ms=em_tick_ms,counts=counts,quality=quality,source_digest=source_digest)
    def apply(self,*,yaw_q,pitch_q,speed_code,duration_ms=12000):
        return self.request('apply',yaw_q=yaw_q,pitch_q=pitch_q,speed_code=speed_code,duration_ms=duration_ms)
    def close(self):
        self._owned();stop=None;error=None
        try:
            if self.client is not None and self.client.ready and not self.client.closed and not self.client.unknown:
                stop=self.request('stop')
        except BaseException as e:error=type(e).__name__
        finally:
            waited=False;killed=False
            if self.proc is not None:
                try:self.proc.stdin.close()
                except OSError:pass
                try:self.proc.wait(timeout=5);waited=True
                except subprocess.TimeoutExpired:
                    self.proc.kill();killed=True;self.proc.wait(timeout=5);waited=True
                self.lines.thread.join(timeout=2);self.stderr_thread.join(timeout=2)
                self.stderr_file.close()
                if waited:self.proc._handle.Close()
            result=dict(stop_response=stop,stop_error=error,wait_confirmed=waited,killed=killed,exit_code=None if self.proc is None else self.proc.returncode,physical_zero_capture_proven=False)
            (self.evidence/'CLOSED.json').write_bytes(canonical(result)+b'\n');self.log.close();self.closed=True
        return result
