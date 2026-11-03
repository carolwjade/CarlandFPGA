"""Root-only contained transport for a NEW G05 run on the existing joint load.

Import is inert. Original822 request/deadline/close behavior and StreamClient ABI
are retained. Only reviewed additive staging and the remote launch are changed.
No mission duration/count ceiling, reconnect, replay or PL-loading launch path.
"""
import hashlib,json,os,pathlib,queue,re,shlex,stat,subprocess,threading,time
import local_stream_client as _stream_source
from local_stream_client import StreamClient

SCOPE_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
ORIGINAL822_SHA256='f9171e44467a210c9b61308a558905a69a3fe0a7742a94540c60c677858d9e67'
STREAM_SHA256='3339b8abb515175987732cc550d880c12891ff4ae77552e6a44da47417e60d7a'
ENTRY1059_SHA256='56886c15cb44574bc396f95c4a185dba81bc8277e8b730df5d0a6c798d907a01'
CAPABILITY1059_SHA256='3e62231a59500e9114ebf23d00ccf5f74de69c21d2fa33af42152a33a8eb59b0'
MANIFEST_KEYS={'schema','scope_sha256','remote','parent_manifest_sha256','loader_plan_sha256',
               'config_relative','config_sha256','g05_run_id','world_epoch','files'}
UPLOAD_KEYS={'schema','remote','boot_id','files','loader_plan_sha256','parent_manifest_sha256'}
PLAN_KEYS={'operation_id','request_sha256','build_id','source_commit','boot_id','bit_path','hwh_path',
           'mapping_path','bit_sha256','hwh_sha256','mapping_sha256','operation_parent',
           'baseline_hwh_path','baseline_hwh_sha256'}
CONFIG_KEYS={'schema','requirements_sha256','approved_plan_path','approved_plan_sha256',
             'operation_directory','build_review_path','build_review_sha256','build_plan_path',
             'source_closure_path','rtl_root','identity_path','identity_sha256','run_id',
             'world_epoch','source_pins'}

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def _need(ok,reason):
    if not ok:raise ValueError(reason)

def _json(blob):
    def unique(pairs):
        out={}
        for key,value in pairs:
            _need(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
        return out
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))

def _hex(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256_REQUIRED')
    return value

def _relative(value):
    _need(type(value) is str and 0<len(value)<=1024 and '\\' not in value and
          all(ord(c)>=32 for c in value),'POSIX_RELATIVE_PATH_REQUIRED')
    path=pathlib.PurePosixPath(value)
    _need(path.parts and not path.is_absolute() and '..' not in path.parts and '.' not in path.parts and str(path)==value,'NORMALIZED_RELATIVE_PATH_REQUIRED')
    return path

def _remote(value):
    _need(type(value) is str and value.startswith('/') and len(value)<=1024 and
          all(ord(c)>=32 for c in value) and '..' not in pathlib.PurePosixPath(value).parts and
          str(pathlib.PurePosixPath(value))==value,'ABSOLUTE_EXISTING_REMOTE_REQUIRED')
    return value

def _read_regular(path,limit=2*1024*1024):
    path=pathlib.Path(path)
    _need(path.is_absolute() and '..' not in path.parts,'ABSOLUTE_LOCAL_STAGE_REQUIRED')
    for item in (path,*path.parents):_need(not item.is_symlink(),'LOCAL_SYMLINK_REFUSED')
    with path.open('rb') as stream:
        before=stream.fileno();a=os.fstat(before)
        _need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and 0<a.st_size<=limit,'BOUNDED_SINGLE_LINK_FILE_REQUIRED')
        blob=stream.read(limit+1);b=os.fstat(before)
    key=lambda value:(value.st_dev,value.st_ino,value.st_mode,value.st_nlink,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
    _need(len(blob)==a.st_size and key(a)==key(b)==key(path.lstat()),'LOCAL_FILE_CHANGED')
    return blob

def _pinned(path,expected,limit=2*1024*1024):
    blob=_read_regular(path,limit)
    _need(hashlib.sha256(blob).hexdigest()==_hex(expected),'LOCAL_FILE_HASH_MISMATCH '+str(path))
    return blob

def remote_argv(manifest):
    """Pure argv construction; this function never opens a process or file."""
    remote=_remote(manifest['remote']);relative=str(_relative(manifest['config_relative']))
    return ['/usr/local/share/pynq-venv/bin/python3','-I','-B','-X','utf8',
            remote+'/already_loaded_g05_1059.py','--allow-g05-run','--config',remote+'/'+relative,
            '--config-sha256',_hex(manifest['config_sha256'])]

def validate_upload(manifest,plan,actual):
    """Pure actual-readback structure comparison; it does not perform upload."""
    _need(type(actual) is dict and set(actual)==UPLOAD_KEYS and actual['schema']=='DEEPEYE-JOINT-HOST-UPLOAD-ACTUAL-1074-v1',
          'EXACT_ACTUAL_ADDITIVE_UPLOAD_READBACK_REQUIRED')
    _need(actual['files']==manifest['files'] and actual['boot_id']==plan['boot_id'] and
          actual['remote']==manifest['remote'] and actual['loader_plan_sha256']==manifest['loader_plan_sha256'] and
          actual['parent_manifest_sha256']==manifest['parent_manifest_sha256'],'ACTUAL_UPLOAD_PHYSICAL_PARENT_MISMATCH')

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
        self.plan=_json(_read_regular(self.stage/'loader-plan.json',131072))
        manifest_raw=_read_regular(self.stage/'MANIFEST.json')
        self.manifest=_json(manifest_raw);self.manifest_sha256=hashlib.sha256(manifest_raw).hexdigest()
        self._validate_stage()
        self.proc=None;self.client=None;self.closed=False;self.stderr_count=0;self.stderr_error=None
        self.log=(self.evidence/'requests.jsonl').open('xb',buffering=0)
        self.owner=threading.get_ident();self.last=None
    def _validate_stage(self):
        m=self.manifest;p=self.plan
        _pinned(self.stage/'MANIFEST.json',self.manifest_sha256)
        _need(type(m) is dict and set(m)==MANIFEST_KEYS and m['schema']=='DEEPEYE-JOINT-HOST-STAGE-1074-v1' and
              m['scope_sha256']==SCOPE_SHA256,'EXACT_ADDITIVE_HOST_MANIFEST_REQUIRED')
        _need(type(p) is dict and set(p)==PLAN_KEYS,'UNCHANGED14_KEY_PHYSICAL_PLAN_REQUIRED')
        parent=_json(_pinned(self.stage/'PHYSICAL_PARENT_MANIFEST.json',m['parent_manifest_sha256']))
        _need(parent['remote']==_remote(m['remote']) and parent['scope_sha256']==SCOPE_SHA256 and
              parent['operation_id']==p['operation_id'] and parent['boot_id']==p['boot_id'],'ORIGINAL_PHYSICAL_PARENT_MISMATCH')
        plan_blob=_pinned(self.stage/'loader-plan.json',m['loader_plan_sha256'],131072)
        _need(m['loader_plan_sha256']==parent['files']['loader-plan.json']['sha256'] and
              _json(plan_blob)==p,'ORIGINAL_PHYSICAL_PLAN_BYTES_REQUIRED')
        body=dict(p);request=body.pop('request_sha256')
        _need(hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==request,'PHYSICAL_REQUEST_HASH_MISMATCH')
        _need(type(m['g05_run_id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}',m['g05_run_id']) is not None and
              type(m['world_epoch']) is int and 1<=m['world_epoch']<=0xffffffff,'EXPLICIT_ROOT_RUN_WORLD_REQUIRED')
        _need(type(m['files']) is dict and m['files'],'ACTUAL_ADDITIVE_FILE_CLOSURE_REQUIRED')
        reserved={'MANIFEST.json','UPLOAD_ACTUAL.json','PHYSICAL_PARENT_MANIFEST.json','loader-plan.json'}
        for name,meta in m['files'].items():
            relative=_relative(name)
            _need(name not in reserved and type(meta) is dict and set(meta)=={'bytes','sha256'} and
                  type(meta['bytes']) is int and 0<meta['bytes']<=16*1024*1024,'EXACT_ADDITIVE_FILE_DESCRIPTOR_REQUIRED')
            blob=_pinned(self.stage/pathlib.Path(*relative.parts),meta['sha256'],16*1024*1024)
            _need(len(blob)==meta['bytes'],'ADDITIVE_FILE_LENGTH_MISMATCH')
            if name in parent['files']:
                _need(meta==parent['files'][name],'EXISTING_PARENT_FILE_MUST_NOT_CHANGE')
        _need(m['files']['already_loaded_g05_1059.py']['sha256']==ENTRY1059_SHA256 and
              m['files']['joint_command_ttl1059.py']['sha256']==CAPABILITY1059_SHA256,'ADOPTED1059_SOURCE_PINS_REQUIRED')
        _need(str(_relative(m['config_relative'])) in m['files'] and
              m['files'][m['config_relative']]['sha256']==_hex(m['config_sha256']),'EXPLICIT_REMOTE_CONFIG_PIN_REQUIRED')
        config=_json(_pinned(self.stage/pathlib.Path(*_relative(m['config_relative']).parts),m['config_sha256'],131072))
        _need(type(config) is dict and set(config)==CONFIG_KEYS and
              config['schema']=='DEEPEYE-ALREADY-LOADED-G05-RUN-1059-v1' and config['requirements_sha256']==SCOPE_SHA256 and
              config['run_id']==m['g05_run_id'] and config['world_epoch']==m['world_epoch'],'ROOT_CONFIG_RUN_WORLD_MISMATCH')
        _need(config['approved_plan_path']==m['remote']+'/loader-plan.json' and
              config['approved_plan_sha256']==m['loader_plan_sha256'] and
              config['operation_directory']==str(pathlib.PurePosixPath(p['operation_parent'])/p['operation_id']),
              'CONFIG_MUST_REFERENCE_EXISTING_PHYSICAL_PARENT')
        _need(config['source_pins']=={'already_loaded_g05_1059.py':ENTRY1059_SHA256,
                                      'joint_command_ttl1059.py':CAPABILITY1059_SHA256},'CONFIG_NEW_SOURCE_PINS_MISMATCH')
        _pinned(pathlib.Path(_stream_source.__file__).resolve(),STREAM_SHA256)
    def record(self,value):self.log.write(canonical(value)+b'\n')
    def _owned(self):
        if threading.get_ident()!=self.owner or self.closed:raise ValueError('ROOT_SINGLE_IO_THREAD')
    def start(self):
        self._owned();assert self.proc is None
        assert not (self.evidence/'STARTED.json').exists()
        self._validate_stage()
        actual=_json(_read_regular(self.stage/'UPLOAD_ACTUAL.json'))
        validate_upload(self.manifest,self.plan,actual)
        route=json.loads((self.root/'.planning/deepeye-resume-20261018/board-preflight-20261021/started.private.json').read_bytes())['argv'][:-1]
        assert route[-1]=='xilinx@fe80::200:5ff:fe6b:1f5%8';route[-1]='xilinx@fe80::200:5ff:fe6b:1f5%9'
        assert hashlib.sha256(pathlib.Path(route[0]).read_bytes()).hexdigest()=='98d447730047f5df91373e852d057928a921c3d1e89938700ab656ba84b19dc8'
        assert hashlib.sha256(pathlib.Path(route[14].split('=',1)[1]).read_bytes()).hexdigest()=='31a10124495b85e9b62bbf46418393124888b2f381f9a4d1334521760ada4418'
        args=remote_argv(self.manifest)
        command="/usr/bin/sudo -S -p '' /usr/bin/env BOARD=Pynq-Z2 XILINX_XRT=/usr "+' '.join(shlex.quote(x) for x in args)
        with (self.evidence/'STARTED.json').open('xb') as stream:
            stream.write(canonical(dict(scope='new_G05_run_on_existing_physical_parent',
                                        physical_parent_operation_id=self.plan['operation_id'],
                                        request_hash=self.plan['request_sha256'],boot_id=self.plan['boot_id'],
                                        build_id=self.plan['build_id'],g05_run_id=self.manifest['g05_run_id'],
                                        world_epoch=self.manifest['world_epoch'],config_sha256=self.manifest['config_sha256'],
                                        stage_manifest_sha256=self.manifest_sha256,
                                        new_G05_run=True,new_PL_operation=False,PL_load=False,
                                        monotonic_ns=time.monotonic_ns()))+b'\n')
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
        result=self.client.initialize()
        assert result.get('scope_sha256')=='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'
        assert type(result.get('initial_speed_code')) is int and result['initial_speed_code']==2 and result.get('speed_applied') is False
        assert result.get('formal_acceptance')=='not_run'
        if result.get('g05_run_id')!=self.manifest['g05_run_id'] or result.get('world_epoch')!=self.manifest['world_epoch']:
            self.client.unknown=True
            raise ValueError('REMOTE_INIT_RUN_WORLD_MISMATCH_NO_REPLAY')
        self.lines.timeout=6.;self.record(dict(event='init-returned',response=result,host_qpc_ns=time.perf_counter_ns()));return result
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
