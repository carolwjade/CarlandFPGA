"""Opt-in retained actor fixture. Import/discovery performs no native operations."""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import time
from dataclasses import dataclass,field

FIXTURE_MODULE = 'competition.deepeye.simulation.isolation.actor_fixture'
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
DIRECTOR='01a13d7e-dcf1-7272-a738-a637dd62ff9d'
CASES=('retained-natural-exit','fixed-unbound-expiry','persistence-after-acquisition')
_ATTEMPTS=[]  # Live recovery roots, never reconstructed from a receipt/PID.


def _digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def _ordinary(path,*,directory=False):
    path=Path(path)
    if not path.is_absolute():raise ValueError('absolute path required')
    for part in (path,*path.parents):
        if part.is_symlink() or (hasattr(part,'is_junction') and part.is_junction()) or getattr(part.lstat(),'st_file_attributes',0)&0x400:
            raise ValueError('links/reparse paths forbidden')
    if directory:
        if not path.is_dir():raise ValueError('directory required')
    elif not path.is_file() or path.stat().st_nlink!=1:
        raise ValueError('ordinary single-link file required')
    return path


def _relative(name):
    if type(name) is not str or not name or '\\' in name or ':' in name:
        raise ValueError('simple relative name required')
    p=Path(name)
    if p.is_absolute() or p.as_posix()!=name or any(x in ('','.','..') for x in p.parts):
        raise ValueError('unsafe manifest path')
    return name


def source_names(product):
    base=product/'competition/deepeye'
    files=list((base/'simulation/isolation').glob('*.py'))+list((base/'integration').glob('*.py'))
    files += [base/'simulation/authority/pc_direct_runtime.py']
    files += [base/'docs'/n for n in ('interface.json','enums.json','host_contract.json','host_timing_contract.md')]
    files += [product/'docs/competition/deepeye-2026/immutable_scope.json',product/'docs/competition/deepeye-2026/immutable_scope.md']
    return {p.relative_to(product).as_posix() for p in files}|{
        'competition/deepeye/tests/isolation/test_actor_windows_live.py',
        'competition/deepeye/docs/actor_native_probe.md'}


def _verify_files(root,manifest):
    if type(manifest) is not dict or not manifest:raise ValueError('exact nonempty hash manifest required')
    names=set();total=0
    for name,digest in manifest.items():
        _relative(name)
        if name.casefold() in names:raise ValueError('case alias')
        names.add(name.casefold())
        if type(digest) is not str or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('SHA256 required')
        p=_ordinary(root/name);total+=p.stat().st_size
        if total>268435456 or _digest(p)!=digest:raise ValueError('manifest bytes/budget mismatch')


def validate_allow_record(record,product,attempt,case,*,required_sources=None):
    """Pure file validation. Main authorization is provenance, not cryptography."""
    product=_ordinary(Path(product),directory=True);attempt=_ordinary(Path(attempt),directory=True)
    if type(record) is not dict or type(record.get('schema')) is not int or record['schema']!=1 or record.get('native_execution') is not True:
        raise ValueError('explicit versioned native allow required')
    if record.get('approved_by')!=DIRECTOR or record.get('requirements_sha256')!=CONTRACT:
        raise ValueError('main/contract mismatch')
    if case not in CASES or record.get('case')!=case or record.get('attempt_directory')!=str(attempt):
        raise ValueError('exact one case/attempt required')
    expected=source_names(product) if required_sources is None else required_sources
    if type(record.get('sources')) is not dict or set(record['sources'])!=expected:
        raise ValueError('complete exact source set required')
    _verify_files(product,record['sources'])
    stage=_ordinary(attempt/'source-stage',directory=True)
    _verify_files(stage,record.get('staged_files'))
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if actual!=set(record['staged_files']):raise ValueError('unlisted/missing stage file')
    for p in stage.rglob('*'):_ordinary(p,directory=p.is_dir())
    fixture='competition/deepeye/simulation/isolation/actor_fixture.py'
    if record['staged_files'].get('fixture.py')!=record['sources'].get(fixture):
        raise ValueError('replacement fixture provenance mismatch')
    if 'python.exe' not in record['staged_files']:raise ValueError('runtime executable not bound')
    return record


def _save_new(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def prepare_stage(evidence_parent,attempt_name,product=None):
    """Offline file staging only; never constructs ActorRegistry or loads Win32."""
    if sys.implementation.name!='cpython' or sys.version_info[:2]!=(3,12):raise RuntimeError('CPython3.12 required')
    parent=_ordinary(Path(evidence_parent),directory=True)
    if type(attempt_name) is not str or len(attempt_name)!=32 or any(c not in '0123456789abcdef' for c in attempt_name):raise ValueError('fresh lowercase uuid hex required')
    product=Path(__file__).resolve().parents[4] if product is None else Path(product)
    _ordinary(product,directory=True)
    attempt=parent/attempt_name;attempt.mkdir()  # No exist_ok/reuse/replacement.
    stage=attempt/'source-stage';stage.mkdir()
    from competition.deepeye.simulation.isolation.prototype import stage_runtime
    origin=stage_runtime(Path(sys.base_prefix),stage)
    fixture=product/'competition/deepeye/simulation/isolation/actor_fixture.py'
    (stage/'fixture.py').write_bytes(_ordinary(fixture).read_bytes())
    final={p.relative_to(stage).as_posix():_digest(_ordinary(p)) for p in sorted(stage.rglob('*')) if p.is_file()}
    _save_new(attempt/'origin-stage-manifest.json',{'meaning':'historical stage_runtime input provenance; its fixture entry is superseded','entries':origin})
    proposal={'schema':1,'approved_by':None,'native_execution':False,'requirements_sha256':CONTRACT,
              'case':None,'attempt_directory':str(attempt),'sources':{n:_digest(_ordinary(product/n)) for n in sorted(source_names(product))},'staged_files':final}
    _save_new(attempt/'allow-proposal.json',proposal)
    return attempt,proposal


@dataclass
class NativeAttempt:
    directory:Path
    case:str
    registry:object=None
    actor:object=None
    original_process_reference:object=None
    original_process_resource_id:str|None=None
    primary:BaseException|None=None
    events:list=field(default_factory=list)
    raw:bytes=b''
    cleanup:dict=field(default_factory=dict)
    unresolved:bool=True
    passed:bool=False


def _retain_original_process(context):
    """Keep the acquired reference/id before cleanup; never adopt from a PID."""
    if context.actor is None or context.original_process_reference is not None:return
    try:
        reference=context.actor._original_process
        if reference is not None and type(reference.resource_id) is str and reference.resource_id:
            context.original_process_reference=reference
            context.original_process_resource_id=reference.resource_id
    except BaseException as error:
        context.events.append({'original_process_capture_error':type(error).__name__,'message':str(error)})


def _snapshot(context):
    a=context.actor
    if a is None:return {'state':'no-owner-returned','unresolved':True}
    refs=a._resources.references  # Read-only recovery evidence, not adoption/API.
    process=context.original_process_reference
    resource_id=context.original_process_resource_id
    backend=a._backend
    codes=getattr(backend,'exit_codes',None)
    recorded=bool(type(codes) is dict and type(resource_id) is str and resource_id in codes)
    code=codes[resource_id] if recorded else None
    terminated=getattr(backend,'terminated',None)
    original=bool(process is not None and a._process is process and a._original_process is process and
        process.resource_id==resource_id and process.native==a._original_native and any(r is process for r in refs))
    exit_observation={'resource_id':resource_id,'identity_continuous':original,'exit_code_recorded':recorded,
        'exit_code':code,'exit_code_type':type(code).__name__,
        'exit_code_source':'original WindowsCleanupBackend.wait_terminal exit_codes[resource_id]',
        'owner_terminated':terminated,'owner_terminated_type':type(terminated).__name__,
        'termination_source':'original WindowsCleanupBackend.terminated; successful owner TerminateProcess observation'}
    profile=a._resources.profile
    outcome=lambda r:None if r is None or r.outcome is None else r.outcome.value
    return {'state':a.state,'instance_id':a.instance_id,'original_process_reference_retained':a._process is a._original_process,
        'original_native_unchanged':bool(process is not None and process.native==a._original_native),
        'terminal_confirmed':bool(process and process.terminal_confirmed),'profile_outcome':outcome(profile),
        'original_process_exit':exit_observation,
        'resources':a._resources.summary(),'resources_complete':bool(a._cleanup_result and a._cleanup_result.resources_complete),
        'evidence_complete':not a._evidence_errors,'evidence_errors':[{'type':type(e).__name__,'message':str(e)} for e in a._evidence_errors],
        'primary_error':None if a._primary_error is None else {'type':type(a._primary_error).__name__,'message':str(a._primary_error)},
        'unresolved_resources':[r.resource_id for r in a._resources.unresolved]}


def _fixture_reader(original_owner):
    from competition.deepeye.simulation.isolation.actor_owner import _entry
    from competition.deepeye.simulation.isolation.actor_lifetime import _reference,_sample
    original_endpoint=original_owner._resources.find('output_read')
    original_native=original_endpoint.native
    def endpoint_check(owner):
        if (owner is not original_owner or owner._resources.find('output_read') is not original_endpoint or
                original_endpoint.native!=original_native or original_endpoint.attempted or original_endpoint.ambiguous or
                original_endpoint.release!='kernel' or not owner._resources.owns(original_endpoint)):
            raise ValueError('original output ownership lost')
    @_entry
    def read(owner):
        epoch=owner._epoch;process=_reference(owner);endpoint_check(owner)
        _sample(owner);endpoint_check(owner);before=owner._time()
        data=owner._api.available_output(original_native)  # Consuming read; helper hard-cap8192.
        owner._checkpoint(epoch)
        endpoint_check(owner)
        if _reference(owner) is not process:
            raise ValueError('fixture endpoint continuity changed')
        if type(data) is not bytes or len(data)>256:raise ValueError('fixture output cap exceeded')
        if owner._time()-before>=owner._policy.max_probe_ns:raise ValueError('fixture read exceeded explicit elapsed budget')
        _sample(owner)
        return data
    return read


def run_case(evidence_parent,allow_file,case):
    """Future one-shot native call; use python -i to retain unresolved contexts.

    Never called by offline tests. No EXIT WriteFile: existing synchronous write
    has no deadline/cancellation contract, so normal case uses timed natural exit.
    """
    if os.name!='nt' or sys.implementation.name!='cpython' or sys.version_info[:2]!=(3,12) or not sys.flags.interactive:
        raise RuntimeError('Windows CPython3.12 interactive retained caller required')
    if any(c.unresolved for c in _ATTEMPTS):raise RuntimeError('unresolved original ownership stops campaign')
    product=Path(__file__).resolve().parents[4]
    parent=_ordinary(Path(evidence_parent),directory=True);allow=_ordinary(Path(allow_file))
    if allow.stat().st_size>1048576:raise ValueError('allow record too large')
    record=json.loads(allow.read_text(encoding='utf-8'))
    attempt=Path(record['attempt_directory'])
    if attempt.parent!=parent:raise ValueError('attempt outside explicit dedicated parent')
    validate_allow_record(record,product,attempt,case)
    # An x-created marker retires this case before native module/registry effects.
    _save_new(attempt/'execution-claimed.json',{'case':case,'allow_sha256':_digest(allow),'started_monotonic_ns':time.monotonic_ns()})
    context=NativeAttempt(attempt,case);_ATTEMPTS.append(context)
    from unittest.mock import patch
    from competition.deepeye.simulation.isolation import actor_owner as actor
    from competition.deepeye.simulation.isolation.actor_fixture import ReadyBuffer
    start=time.monotonic_ns()
    expiry=case=='fixed-unbound-expiry'
    life=2_000_000_000 if expiry else 8_000_000_000
    args=('-I','-B','fixture.py','natural','2000') if case=='retained-natural-exit' else ('-I','-B','fixture.py','wait','0')
    policy=actor.ActorPolicy('cpu-fixture-'+attempt.name,attempt,attempt/'source-stage',tuple(sorted(record['staged_files'].items())),
        'python.exe',args,os.environ['SystemRoot'],os.environ['LOCALAPPDATA'],268435456,256,life,life,500_000_000,250_000_000)
    original_persist=actor._persist;injected=OSError('intentional actor persistence failure after acquisition');injections=[]
    def fail_after_acquisition(owner):
        if owner._process is not None:
            injections.append(owner._process.resource_id)
            raise injected
        return original_persist(owner)
    try:
        context.registry=actor.ActorRegistry()
        if case=='persistence-after-acquisition':
            with patch.object(actor,'_persist',fail_after_acquisition):
                context.actor=context.registry.launch(policy)
            raise AssertionError('persistence failure did not occur')
        context.actor=context.registry.launch(policy)
        _retain_original_process(context)
        # Registry and exact object identities remain strongly retained throughout.
        if not any(o is context.actor for o in context.registry._owners):raise AssertionError('factory return not strongly retained')
        fixture_read=_fixture_reader(context.actor)
        frames=ReadyBuffer();end=time.monotonic_ns()+6_000_000_000
        while time.monotonic_ns()<end:
            try:
                context.actor.poll()
                context.events.append({'elapsed_ns':time.monotonic_ns()-start,'operation':'public_poll','wait_result_source':'strict integer258 implied by pinned successful _sample, not separately intercepted'})
                chunk=fixture_read(context.actor)
                if len(context.raw)+len(chunk)>256:raise ValueError('total fixture output cap exceeded')
                context.raw+=chunk;frames.feed(chunk)
            except ValueError as error:
                context.events.append({'elapsed_ns':time.monotonic_ns()-start,'operation':'poll/read retired','error':str(error)})
                if case=='retained-natural-exit':
                    if not frames.raw==b'DEEPEYE-ACTOR/1 READY\n' or not context.actor._process.terminal_confirmed:raise
                    context.passed=True
                elif expiry:
                    if (frames.raw!=b'DEEPEYE-ACTOR/1 READY\n' or time.monotonic_ns()<context.actor._run_deadline or
                            context.actor._ready_deadline!=context.actor._run_deadline or context.actor._process.terminal_confirmed or
                            str(error)!='fixed actor/readiness/sample deadline expired'):raise
                    context.passed=True
                break
            time.sleep(.01)
        else:raise TimeoutError('bounded parent polling deadline expired')
    except BaseException as error:
        context.primary=error
        if context.actor is None and context.registry is not None and context.registry._owners:
            context.actor=context.registry._owners[-1]
        if case=='persistence-after-acquisition':
            context.passed=bool(error is injected and injections and context.actor is not None and context.actor._primary_error is injected)
    finally:
        # Failed launch may retain its owner only in the acquisition registry.
        # Retain that original reference too; launch may have already attempted
        # cleanup. This fallback never replaces the original primary exception.
        _retain_original_process(context)
        if context.actor is not None and not context.actor._cleanup_attempted:
            try:context.actor.close('one-shot CPU fixture final cleanup')
            except BaseException as cleanup_error:context.events.append({'cleanup_exception':type(cleanup_error).__name__,'message':str(cleanup_error)})
        context.cleanup=_snapshot(context)
        context.unresolved=bool(context.cleanup.get('unresolved_resources',True))
        if not context.cleanup.get('resources_complete') or not context.cleanup.get('terminal_confirmed') or context.cleanup.get('profile_outcome')!='confirmed':context.passed=False
        if case=='persistence-after-acquisition':
            context.passed=context.passed and bool(context.cleanup.get('evidence_errors')) and context.cleanup['state']=='QUARANTINED'
        elif context.cleanup.get('state')!='CLOSED':context.passed=False
        if case=='retained-natural-exit':
            observed=context.cleanup.get('original_process_exit',{})
            if not (observed.get('identity_continuous') is True and observed.get('exit_code_recorded') is True and
                    type(observed.get('exit_code')) is int and observed['exit_code']==0 and
                    observed.get('owner_terminated') is False):context.passed=False
        # Never replace actor's possibly stale receipt with a purported final one.
        try:
            with (attempt/'fixture-stdout.bin').open('xb') as stream:stream.write(context.raw)
            receipts=[]
            if context.actor is not None and context.actor._root is not None:
                receipts=[{'path':str(p),'sha256':_digest(p),'meaning':'observed snapshot only; may predate injected failure'} for p in context.actor._root.glob('receipt.json')]
            _save_new(attempt/'fixture-memory-result.json',{'case':case,'passed':context.passed,'unresolved':context.unresolved,
                'normal_exit_success':case=='retained-natural-exit' and context.passed,
                'evidence_success':case=='retained-natural-exit' and context.passed and context.cleanup.get('evidence_complete') is True,
                'result_semantics':'normal_exit_fixture' if case=='retained-natural-exit' else 'expected_negative_fixture',
                'elapsed_ns':time.monotonic_ns()-start,'events':context.events,'cleanup':context.cleanup,'actor_receipt_snapshots':receipts,
                'primary_error':None if context.primary is None else {'type':type(context.primary).__name__,'message':str(context.primary)},
                'runtime_ready_boot_ai_h12_formal':'not_run','exit_write':'not_run: synchronous WriteFile lacks a deadline contract',
                'expiry_meaning':'unbound readiness=lifetime simultaneous expiry only' if expiry else None})
        except BaseException as report_error:
            context.events.append({'memory_result_persistence_error':type(report_error).__name__,'message':str(report_error)})
            context.passed=False  # Live context remains in _ATTEMPTS even when disk fails.
    return context


class OfflinePreparationTests(unittest.TestCase):
    def fixture(self):
        try: return importlib.import_module(FIXTURE_MODULE)
        except ModuleNotFoundError: self.fail('cooperative fixture is not implemented')

    def test_exit_is_one_exact_byte(self):
        f=self.fixture()
        self.assertEqual(f.decode_command(b'X'),'exit')
        for bad in (b'',b'EXIT\n',b'XX',b'x','X',True):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError): f.decode_command(bad)

    def test_ready_frame_is_exact_and_capped(self):
        f=self.fixture(); frames=f.ReadyBuffer()
        self.assertFalse(frames.feed(f.READY[:5]))
        self.assertTrue(frames.feed(f.READY[5:]))
        with self.assertRaises(ValueError): frames.feed(b'junk')
        with self.assertRaises(ValueError): f.ReadyBuffer().feed(b'?'*257)

    def test_mode_and_delay_have_strict_finite_shape(self):
        f=self.fixture()
        self.assertEqual(f.validate_mode('natural',2000),('natural',2000))
        for args in [('natural',True),('natural',0),('natural',10001),('wait',1),('exit',1),('unknown',0)]:
            with self.subTest(args=args),self.assertRaises(ValueError):f.validate_mode(*args)

    def validator(self):
        self.assertIn('validate_allow_record',globals(),'allow gate is not implemented')
        return globals()['validate_allow_record']

    def sample_record(self,root):
        product=root/'product';attempt=root/'attempt';stage=attempt/'source-stage'
        source=product/'competition/deepeye/simulation/isolation/actor_fixture.py'
        source.parent.mkdir(parents=True);source.write_bytes(b'fixture')
        stage.mkdir(parents=True);(stage/'python.exe').write_bytes(b'runtime');(stage/'fixture.py').write_bytes(b'fixture')
        def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
        record={'schema':1,'approved_by':'01a13d7e-dcf1-7272-a738-a637dd62ff9d','native_execution':True,
                'requirements_sha256':'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804',
                'case':'retained-natural-exit','attempt_directory':str(attempt.resolve()),
                'sources':{source.relative_to(product).as_posix():sha(source)},
                'staged_files':{p.name:sha(p) for p in stage.iterdir()}}
        return product,attempt,record

    def test_allow_requires_exact_main_case_and_hashes(self):
        validate=self.validator()
        with tempfile.TemporaryDirectory() as d:
            p,a,r=self.sample_record(Path(d));validate(r,p,a,'retained-natural-exit',required_sources=set(r['sources']))
            for change in ({'native_execution':1},{'case':'fixed-unbound-expiry'},{'approved_by':'other'}):
                with self.subTest(change=change),self.assertRaises(ValueError):validate(r|change,p,a,'retained-natural-exit',required_sources=set(r['sources']))
            (a/'source-stage/fixture.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):validate(r,p,a,'retained-natural-exit',required_sources=set(r['sources']))

    def test_allow_rejects_traversal_and_unlisted_staged_file(self):
        validate=self.validator()
        with tempfile.TemporaryDirectory() as d:
            p,a,r=self.sample_record(Path(d));bad=copy.deepcopy(r);bad['staged_files']['../outside']='0'*64
            with self.assertRaises(ValueError):validate(bad,p,a,'retained-natural-exit',required_sources=set(r['sources']))
            (a/'source-stage/extra').write_bytes(b'extra')
            with self.assertRaises(ValueError):validate(r,p,a,'retained-natural-exit',required_sources=set(r['sources']))

    def test_no_native_module_is_imported_by_offline_helpers(self):
        self.fixture()
        self.assertFalse(any(x.endswith('.isolation.win32') for x in sys.modules))

    def test_stale_source_hash_and_alias_manifest_are_rejected(self):
        validate=self.validator()
        with tempfile.TemporaryDirectory() as d:
            p,a,r=self.sample_record(Path(d));bad=copy.deepcopy(r)
            bad['staged_files']['FIXTURE.py']=r['staged_files']['fixture.py']
            with self.assertRaises(ValueError):validate(bad,p,a,'retained-natural-exit',required_sources=set(r['sources']))
            (p/next(iter(r['sources']))).write_bytes(b'changed source')
            with self.assertRaises(ValueError):validate(r,p,a,'retained-natural-exit',required_sources=set(r['sources']))

    def test_native_entry_is_disabled_before_allow_file_access(self):
        # This test does not change platform/interactive flags to force execution.
        if sys.flags.interactive:self.skipTest('offline test expects ordinary noninteractive runner')
        with self.assertRaises(RuntimeError):run_case(Path('absent'),Path('absent'),'retained-natural-exit')
        self.assertFalse(any(x.endswith('.isolation.win32') for x in sys.modules))

    def test_fixture_uses_only_supplied_endpoints_and_one_byte_command(self):
        from unittest.mock import Mock,patch
        f=self.fixture();kernel=Mock()
        kernel.WriteFile.return_value=(len(f.READY),0);kernel.ReadFile.return_value=(b'X',0)
        with patch.dict(sys.modules,{'_winapi':kernel}):f.main(['exit','0','123','456'])
        kernel.WriteFile.assert_called_once_with(456,f.READY)
        kernel.ReadFile.assert_called_once_with(123,1)

    def test_natural_fixture_never_reads_or_writes_exit(self):
        from unittest.mock import Mock,patch
        f=self.fixture();kernel=Mock();kernel.WriteFile.return_value=(len(f.READY),0)
        with patch.dict(sys.modules,{'_winapi':kernel}),patch('time.sleep') as sleep:f.main(['natural','2000','123','456'])
        kernel.ReadFile.assert_not_called();sleep.assert_called_once_with(2)


@unittest.skipUnless(os.name=='nt' and sys.flags.interactive and os.environ.get('DEEPEYE_ACTOR_NATIVE_OPT_IN')=='1',
                     'native not_run: main exact-hash allow plus explicit interactive opt-in required')
class ActorWindowsLiveTests(unittest.TestCase):
    def selected(self,case):
        if os.environ.get('DEEPEYE_ACTOR_NATIVE_CASE')!=case:self.skipTest('separately selected one-shot case only')
        parent=os.environ.get('DEEPEYE_ACTOR_NATIVE_EVIDENCE_PARENT');allow=os.environ.get('DEEPEYE_ACTOR_NATIVE_ALLOW')
        if not parent or not allow:self.fail('explicit dedicated parent and main allow file required')
        result=run_case(Path(parent),Path(allow),case)
        self.assertTrue(result.passed,result.cleanup)
    def test_retained_return_ready_natural_exit(self):
        self.selected('retained-natural-exit')
    def test_fixed_unbound_readiness_and_lifetime_expiry(self):
        self.selected('fixed-unbound-expiry')
    def test_persistence_failure_after_original_acquisition(self):
        self.selected('persistence-after-acquisition')


if __name__=='__main__':unittest.main()
