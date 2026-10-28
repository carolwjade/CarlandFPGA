"""Stdlib-only immutable product/runtime closure and permanent one-use controls."""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import sys
import threading
CONTRACT='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
WORK='A-PC-AI-C22-OWNED-PRODUCT-PROVIDER-20261028-v1'
def need(value,message):
    if value is not True: raise ValueError(message)

def pin(path):
    size=0; digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            size+=len(block);digest.update(block)
    return {'bytes':size,'sha256':digest.hexdigest()}

def plain(path):
    path=Path(path)
    need(path.is_absolute(),'absolute existing source required')
    for item in (path,*path.parents):
        need(not item.is_symlink() and not (hasattr(item,'is_junction') and item.is_junction()) and not (getattr(item.lstat(),'st_file_attributes',0)&0x400),'aliases/reparse points forbidden')
    need(path.is_file() and path.stat().st_nlink==1,'ordinary single-link file required')
    return path

def pin_host_system_dll(path,expected):
    """Only the four original System32 inventory DLLs may retain nlink2."""
    path=Path(path)
    fixed={
        'C:/Windows/System32/kernel32.dll':{'bytes':861992,'sha256':'e132eba4166256e2f414b91fe7d5386590bc5ea8626aee5af9c9738383cf2ae1'},
        'C:/Windows/System32/advapi32.dll':{'bytes':795272,'sha256':'b864e1468a01a44f1901e03c05c1029e71655dd9abddd6d840bcfff5e7227d44'},
        'C:/Windows/System32/userenv.dll':{'bytes':236768,'sha256':'aeb1a6a15397bee7a0ebc67b8188f751e10089c0adadfd86146496c5faae914c'},
        'C:/Windows/System32/ole32.dll':{'bytes':1720576,'sha256':'1053ffb858cddbe29eaaa6a5b0836b88c7cd11fbd58605288600e507c06db443'},
    }
    selected=next((value for name,value in fixed.items() if path==Path(name)),None)
    need(path.is_absolute() and selected is not None and type(expected) is dict and expected==selected,'exact original host System32 DLL path/pin required')
    for item in (path,*path.parents):
        need(not item.is_symlink() and not (hasattr(item,'is_junction') and item.is_junction()) and not (getattr(item.lstat(),'st_file_attributes',0)&0x400),'host DLL aliases/reparse points forbidden')
    def check(s):
        need(stat.S_ISREG(s.st_mode) and s.st_nlink==2 and not (getattr(s,'st_file_attributes',0)&0x400),'original regular host DLL nlink2 required')
    def family(s):
        return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))
    def common(s):
        return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,stat.S_IFMT(s.st_mode))
    a=path.lstat();check(a);size=0;h=hashlib.sha256()
    with path.open('rb') as f:
        b=os.fstat(f.fileno());check(b)
        for block in iter(lambda:f.read(1024*1024),b''):size+=len(block);h.update(block)
        c=os.fstat(f.fileno());check(c)
    z=path.lstat();check(z)
    actual={'bytes':size,'sha256':h.hexdigest()}
    need(family(a)==family(z) and family(b)==family(c) and common(a)==common(b)==common(c)==common(z) and actual==selected,'host DLL original path/handle identity or hash changed')
    return actual


def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key'); result[key]=value
    return result

def load(path,maximum=16*1024*1024):
    raw=plain(path).read_bytes(); need(len(raw)<=maximum,'JSON byte cap exceeded')
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    need(type(value) is dict,'JSON object required'); return value

def digest(value): need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'full lowercase SHA256 required')

def relative(value):
    need(type(value) is str and value and '\\' not in value and ':' not in value,'simple relative destination required')
    path=PurePosixPath(value)
    need(not path.is_absolute() and path.as_posix()==value and all(x not in ('','.','..') and x[-1:] not in (' ','.') and not any(c in x for c in '<>"|?*\0') and x.split('.')[0].upper() not in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(10)),*(f'LPT{i}' for i in range(10))} for x in path.parts),'unsafe stage destination')
    return value

def verify_rows(rows,prefix=None):
    need(type(rows) is list and 1<=len(rows)<=20000,'bounded explicit file list required')
    names=set(); total=0
    for row in rows:
        need(type(row) is dict and row.keys()=={'source','path','bytes','sha256'},'exact stage pin fields required')
        name=relative(row['path']); digest(row['sha256'])
        need(type(row['bytes']) is int and row['bytes']>=0,'strict byte count required')
        need(name.casefold() not in names and (prefix is None or name.startswith(prefix)),'case duplicate/outside fixed stage tree')
        names.add(name.casefold())
        need(pin(plain(row['source']))=={'bytes':row['bytes'],'sha256':row['sha256']},'source pin mismatch: '+name)
        total+=row['bytes']
    return total

def write_new(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False); stream.write('\n');stream.flush();os.fsync(stream.fileno())

def copy_rows(rows,target):
    for row in rows:
        src=plain(row['source']); need(pin(src)=={'bytes':row['bytes'],'sha256':row['sha256']},'source changed before stage copy')
        dst=target/relative(row['path']);dst.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as reader,dst.open('xb') as writer:
            for block in iter(lambda:reader.read(1024*1024),b''): need(writer.write(block)==len(block),'short local stage write')
            writer.flush()  # Ephemeral stage; closed and fully hash-read back below.
        need(pin(dst)=={'bytes':row['bytes'],'sha256':row['sha256']},'stage bytes mismatch')



def require_execution(config):
    need(config.get('execute') is True,'execution disabled; explicit new qualification config required')

class OneUseLifecycle:
    """Consume before effects; failed or duplicate requests never reopen a phase."""
    def __init__(self): self.state='NEW';self.thread=threading.get_ident()
    def _move(self,old,new):
        need(threading.get_ident()==self.thread,'original lifecycle thread required')
        need(self.state==old,'one-use lifecycle order/reuse rejected')
        self.state=new
    def claim_start(self): self._move('NEW','STARTING')
    def mark_ready(self): self._move('STARTING','READY')
    def claim_observe(self): self._move('READY','OBSERVING')
    def mark_result(self): self._move('OBSERVING','RESULT_VERIFIED')
    def claim_end(self): self._move('RESULT_VERIFIED','ENDING')
    def mark_ended(self): self._move('ENDING','ENDED')

def require_private_origins(host,*,all_loaded=False):
    """Deny stale helper imports before any native helper can be executed."""
    for name in ('serial_session','framing_contract','native_readback'):
        module=sys.modules.get(name)
        if module is None:
            need(all_loaded is False,'fixed private module did not load')
        else:
            file=getattr(module,'__file__',None)
            need(type(file) is str and Path(file).absolute()==Path(host)/ (name+'.py'),'fixed private module origin mismatch: '+name)

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def package_root(): return Path(__file__).absolute().parent

def repository_root(): return package_root().parents[3]

def ordinary_directory(path):
    path=Path(path)
    need(path.is_absolute() and path.is_dir(),'absolute existing ordinary directory required')
    for item in (path,*path.parents):
        need(not item.is_symlink() and not (hasattr(item,'is_junction') and item.is_junction()) and not (getattr(item.lstat(),'st_file_attributes',0)&0x400),'directory aliases/reparse points forbidden')
    return path

def source_plan():
    root=ordinary_directory(repository_root())
    spec=load(package_root()/'deployment.json')
    need(spec['requirements_sha256']==CONTRACT and spec['schema']==1,'fixed contract/spec required')
    inventory=load(package_root()/'source-inventory.json')
    need(inventory.keys()=={'schema','requirements_sha256','files'} and inventory['schema']==1 and inventory['requirements_sha256']==CONTRACT,'fixed product inventory schema required')
    names=set();total=0
    for row in inventory['files']:
        need(row.keys()=={'path','bytes','sha256'},'fixed source inventory fields required')
        name=relative(row['path']);digest(row['sha256'])
        need(name.casefold() not in names,'duplicate product source path')
        names.add(name.casefold());expected={k:row[k] for k in ('bytes','sha256')}
        need(pin(plain(root/name))==expected,'product source mismatch: '+name)
        total+=row['bytes']
    paths=set()
    for row in spec['host_files']+spec['child_files']:
        if 'product_path' in row:
            name=relative(row['product_path']);paths.add(name)
            need(name.casefold() in names,'unbound product closure path')
            need(pin(plain(root/name))=={k:row[k] for k in ('bytes','sha256')},'qualified product closure bytes changed')
    scope=load(root/'docs/competition/deepeye-2026/immutable_scope.json')
    need(hashlib.sha256(canonical(scope['requirements'])).hexdigest()==CONTRACT and [x['id'] for x in scope['requirements']]==['H%02d'%i for i in range(1,16)],'H01-H15 canonical scope mismatch')
    return spec,dict(schema=1,source_root=str(root),requirements_sha256=CONTRACT,source_files=len(inventory['files']),source_bytes=total,source_inventory_sha256=pin(package_root()/'source-inventory.json')['sha256'],qualification_only=True,production_factory_open=False,BOOT_created=False,actor_launches=0,model_calls=0)

def runtime_plan(root,manifest_path,manifest_sha256,spec):
    root=ordinary_directory(root);digest(manifest_sha256)
    need(Path(manifest_path)==root/'runtime-manifest.json','fixed external runtime manifest location required')
    need(pin(plain(manifest_path))['sha256']==manifest_sha256,'external runtime manifest raw SHA mismatch')
    manifest=load(manifest_path,2*1024*1024)
    need(manifest.keys()=={'schema','numpy_version','files'} and manifest['schema']==1 and manifest['numpy_version']=='2.5.4','fixed portable runtime schema required')
    rows=manifest['files']
    need(type(rows) is list and len(rows)==3252 and hashlib.sha256(canonical(rows)).hexdigest()==spec['runtime_files_sha256'],'exact original 3252-member runtime inventory required')
    need(sum(r['bytes'] for r in rows)==92179831,'fixed original runtime byte total required')
    base=spec['base_runtime_inventory'];base_path=root/'base-runtime-inventory.json'
    need(pin(plain(base_path))=={k:base[k] for k in ('bytes','sha256')},'original base Python binary/source inventory raw SHA required')
    base_files=load(base_path)['runtime']['files']
    need(len(base_files)==2305 and all(any(r['path']=='runtime/'+name and {k:r[k] for k in ('bytes','sha256')}==expected for r in rows) for name,expected in base_files.items()),'original 2305-member base inventory must match fixed runtime')
    resolved=[]
    for row in rows:
        need(row.keys()=={'path','bytes','sha256'},'exact portable runtime pin fields required')
        name=relative(row['path']);need(name.startswith('runtime/'),'fixed external runtime tree only')
        resolved.append(dict(row,source=str(root/name)))
    verify_rows(resolved,'runtime/')
    host=[r for r in spec['host_files'] if 'external_path' in r]
    need(len(host)==145 and hashlib.sha256(canonical(host)).hexdigest()==spec['host_dependency_files_sha256'],'exact qualified host dependency inventory required')
    verify_rows([dict(path=r['path'],source=str(root/relative(r['external_path'])),bytes=r['bytes'],sha256=r['sha256']) for r in host],'deps/')
    return manifest,resolved

def resolved_plan(spec,runtime_root,tested_commit):
    root=repository_root();runtime_root=Path(runtime_root)
    def resolve(row):
        path=root/relative(row['product_path']) if 'product_path' in row else runtime_root/relative(row['external_path'])
        return dict(path=row['path'],source=str(path),bytes=row['bytes'],sha256=row['sha256'])
    plan=dict(spec)
    plan['host_files']=[resolve(r) for r in spec['host_files']]
    plan['child_files']=[resolve(r) for r in spec['child_files']]
    plan['published_head']=tested_commit
    plan['diagnostic']={k:str(root/relative(v)) if k.endswith('_path') else v for k,v in spec['diagnostic'].items()}
    return plan

def child_layout(config,rows):
    return dict(schema=1,requirements_sha256=CONTRACT,runtime_closure_sha256=config['runtime_manifest_sha256'],numpy_version='2.5.4',files=[{k:r[k] for k in ('path','bytes','sha256')} for r in rows])

def _stage_inputs(config,spec,runtime_rows):
    """Keep the original relative child paths; no per-file caller source input."""
    root=Path(config['runtime_root'])
    plan=resolved_plan(spec,root,config['tested_commit'])
    rows=plan['child_files']+runtime_rows
    need(len({r['path'].casefold() for r in rows})==len(rows),'child/runtime path collision')
    for row in runtime_rows:
        need(Path(row['source'])==root/relative(row['path']) and row['path'].startswith('runtime/'),'fixed external runtime source derivation required')
    need(sum(r['bytes'] for r in rows)<=268435456,'retained stage cap exceeded')
    return plan,rows

def _external_members(root,spec,runtime_rows,product_rows=(),phase='bare'):
    """The source root has fixed host roles; only the policy list enters child."""
    root=ordinary_directory(root)
    names={relative(row['path']) for row in runtime_rows}
    names|={relative(row['external_path']) for row in spec['host_files'] if 'external_path' in row}
    names|={'runtime-manifest.json','base-runtime-inventory.json'}
    if phase!='bare':names.add('prepared-source-plan/intent.json')
    if phase in ('copy_complete','prepared'):
        names|={relative(row['path']) for row in product_rows}|{'child-layout.json'}
    if phase=='prepared':names.add('prepared-source-plan/complete.json')
    actual={item.relative_to(root).as_posix() for item in root.rglob('*') if item.is_file()}
    need(actual==names,'external source members differ from exact fixed roles; no partial/extra source accepted')
    directories=set()
    for name in names:
        path=Path(name).parent
        while path!=Path('.'):
            directories.add(path.as_posix());path=path.parent
    actual_dirs={item.relative_to(root).as_posix() for item in root.rglob('*') if item.is_dir()}
    need(actual_dirs==directories,'external source members include unexpected directories')
    for item in root.rglob('*'):
        if item.is_dir():ordinary_directory(item)
        else:plain(item)

def _file_identity(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink,info.st_mode,getattr(info,'st_file_attributes',0))

def _same_source_identity(before,opened,finished,after):
    # Windows lstat and fstat expose different ctime semantics; compare each
    # family strictly across time and the shared file identity across families.
    def common(info):
        return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,stat.S_IFMT(info.st_mode),getattr(info,'st_file_attributes',0))
    return (all(info.st_nlink==1 and stat.S_ISREG(info.st_mode) for info in (before,opened,finished,after))
        and _file_identity(before)==_file_identity(after) and _file_identity(opened)==_file_identity(finished)
        and common(before)==common(opened)==common(finished)==common(after))

def _stable_pin(path):
    source=plain(path);before=source.lstat();digest=hashlib.sha256();size=0
    with source.open('rb') as stream:
        opened=os.fstat(stream.fileno())
        for block in iter(lambda:stream.read(1024*1024),b''):size+=len(block);digest.update(block)
        finished=os.fstat(stream.fileno())
    after=plain(source).lstat()
    need(_same_source_identity(before,opened,finished,after),'source path/handle identity changed across hash')
    return dict(bytes=size,sha256=digest.hexdigest())

def _copy_product_sources(rows,root):
    """Copy only the fixed product rows; never duplicate the runtime tree."""
    for row in rows:
        source=plain(row['source']);expected={k:row[k] for k in ('bytes','sha256')}
        need(_stable_pin(source)==expected,'fixed product source changed before preparation')
        target=root/relative(row['path']);target.parent.mkdir(parents=True,exist_ok=True);ordinary_directory(target.parent)
        before=source.lstat();digest=hashlib.sha256();size=0
        with source.open('rb') as reader,target.open('xb') as writer:
            opened=os.fstat(reader.fileno())
            for block in iter(lambda:reader.read(1024*1024),b''):
                size+=len(block);digest.update(block);need(writer.write(block)==len(block),'short fixed product source copy')
            finished=os.fstat(reader.fileno());writer.flush();os.fsync(writer.fileno())
        after=plain(source).lstat()
        need(_same_source_identity(before,opened,finished,after),'fixed product source identity changed during copy')
        need(dict(bytes=size,sha256=digest.hexdigest())==expected and _stable_pin(target)==expected,'fixed product source/destination hash mismatch')

def _preparation_intent(config,config_sha256,rows):
    digest(config_sha256)
    normalized={k:v for k,v in config.items() if k!='execute'}
    return dict(schema=1,phase='started_unknown_no_retry',preparation_execute=False,preparation_config_raw_sha256=config_sha256,
        config_without_execute_sha256=hashlib.sha256(canonical(normalized)).hexdigest(),
        requirements_sha256=CONTRACT,source_inventory_sha256=config['source_inventory_sha256'],runtime_manifest_sha256=config['runtime_manifest_sha256'],
        product_source_root=str(repository_root()),actor_policy_source_root=str(Path(config['runtime_root'])),
        child_files_sha256=hashlib.sha256(canonical([{k:r[k] for k in ('path','bytes','sha256')} for r in rows])).hexdigest(),runtime_files_copied=0)

def _prepared_completion(intent_path,layout_path,product_count):
    return dict(schema=1,status='prepared_direct_source_only',intent_sha256=pin(intent_path)['sha256'],child_layout_pin=pin(layout_path),
        product_files_copied=product_count,runtime_files_copied=0,source_and_destination_hashes_verified=True,source_handle_identity_before_after_verified=True,
        actor_launches=0,model_calls=0)

def _prepare_in_place(config,config_sha256,spec,runtime_rows):
    need(config['execute'] is False,'preparation requires false execution config')
    root=ordinary_directory(config['runtime_root']);plan,rows=_stage_inputs(config,spec,runtime_rows)
    _external_members(root,spec,runtime_rows,phase='bare')
    verify_rows(plan['child_files'])
    marker=root/'prepared-source-plan';marker.mkdir(exist_ok=False)
    write_new(marker/'intent.json',_preparation_intent(config,config_sha256,rows))
    _copy_product_sources(plan['child_files'],root)
    write_new(root/'child-layout.json',child_layout(config,rows))
    _external_members(root,spec,runtime_rows,plan['child_files'],phase='copy_complete')
    for row in rows:need(_stable_pin(root/row['path'])=={k:row[k] for k in ('bytes','sha256')},'prepared source pin mismatch')
    write_new(marker/'complete.json',_prepared_completion(marker/'intent.json',root/'child-layout.json',len(plan['child_files'])))
    _verify_prepared_stage(config,spec,runtime_rows)
    return dict(status='prepared_direct_source_only',path=str(root),child_source_files=len(rows),private_stage_files=len(rows)+1,
        product_files_copied=len(plan['child_files']),runtime_files_copied=0,actor_launches=0,model_calls=0)

def _verify_prepared_stage(config,spec,runtime_rows):
    root=ordinary_directory(config['runtime_root']);plan,rows=_stage_inputs(config,spec,runtime_rows)
    _external_members(root,spec,runtime_rows,plan['child_files'],phase='prepared')
    marker=root/'prepared-source-plan';intent=load(marker/'intent.json',65536)
    raw_sha=intent.get('preparation_config_raw_sha256');digest(raw_sha)
    need(intent==_preparation_intent(config,raw_sha,rows),'prepared source config/root/identity binding changed')
    need(load(root/'child-layout.json',2*1024*1024)==child_layout(config,rows),'exact current direct-source child layout required')
    need(load(marker/'complete.json',65536)==_prepared_completion(marker/'intent.json',root/'child-layout.json',len(plan['child_files'])),'prepared source completion descriptor changed; no partial state accepted')
    for row in rows:need(_stable_pin(root/row['path'])=={k:row[k] for k in ('bytes','sha256')},'prepared source pin mismatch')
    return plan,rows,pin(root/'child-layout.json')

def prepare_child(config_path,config_sha256):
    """Prepare 15 fixed product sources beside runtime; copy no runtime files."""
    config,spec,manifest,rows=_configuration(config_path,config_sha256,execute=False)
    return _prepare_in_place(config,config_sha256,spec,rows)

def _configuration(path,sha,*,execute):
    digest(sha);need(pin(plain(path))['sha256']==sha,'config raw SHA mismatch')
    config=load(path,65536)
    if execute: require_execution(config)
    keys={'schema','work_id','requirements_sha256','purpose','execute','source_inventory_sha256','runtime_root','runtime_manifest_path','runtime_manifest_sha256','run_id','operation_id','tested_commit','system_root','local_appdata','final_dir','outer_config_path','outer_config_normalized_sha256'}
    need(config.keys()==keys and type(config['schema']) is int and config['schema']==1,'exact new product qualification config required')
    need(config['work_id']==WORK and config['requirements_sha256']==CONTRACT and config['purpose']=='one_new_fixed_FORCE_numpy_product_qualification','fixed work/contract/purpose required')
    for name in ('run_id','operation_id'):
        need(type(config[name]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}',config[name]) is not None,'strict new operation/run required')
    need(type(config['tested_commit']) is str and re.fullmatch('[0-9a-f]{40}',config['tested_commit']) is not None and config['tested_commit']!='0'*40,'full actual integrated source commit required')
    spec,report=source_plan();digest(config['source_inventory_sha256'])
    need(report['source_inventory_sha256']==config['source_inventory_sha256'],'fixed product source inventory changed')
    manifest,rows=runtime_plan(config['runtime_root'],config['runtime_manifest_path'],config['runtime_manifest_sha256'],spec)
    return config,spec,manifest,rows

def preflight(config_path,config_sha256):
    config,spec,runtime,rows=_configuration(config_path,config_sha256,execute=True)
    final=Path(config['final_dir']);need(final.is_absolute() and not final.exists(),'new evidence target required; no replay')
    ordinary_directory(final.parent)
    slot=Path(config['runtime_root'])/'operation-slots'/config['operation_id']
    need(not slot.exists(),'operation launch slot already consumed')
    for name in ('system_root','local_appdata'):ordinary_directory(config[name])
    for row in spec['fixed_host_system_dlls']:
        pin_host_system_dll(row['path'],{k:row[k] for k in ('bytes','sha256')})
    plan,child_rows,layout_pin=_verify_prepared_stage(config,spec,rows)
    verify_rows(plan['host_files']);verify_rows(plan['child_files'])
    need(sum(r['bytes'] for r in child_rows)+layout_pin['bytes']<=268435456,'layout-inclusive retained stage cap exceeded')
    outer=load(config['outer_config_path'],65536)
    need(outer.keys()=={'command','cwd','env','timeout_seconds','result_dir'} and type(outer['timeout_seconds']) is int and outer['timeout_seconds']==60,'exact original 60-second supervisor config required')
    expected=[str(Path(config['runtime_root'])/'runtime/python.exe'),'-I','-S','-B','-X','utf8',str(package_root()/'qualification.py'),'--config',str(Path(config_path).absolute()),'--config-sha256',config_sha256]
    need(outer['command']==expected and Path(outer['cwd'])==repository_root(),'fixed product qualification command/cwd required')
    normalized=dict(outer);normalized['command']=[*expected[:-1],'CONFIG_SHA256']
    digest(config['outer_config_normalized_sha256'])
    need(hashlib.sha256(canonical(normalized)).hexdigest()==config['outer_config_normalized_sha256'],'normalized original supervisor binding changed')
    result=Path(outer['result_dir']);need(result.is_absolute() and not result.is_relative_to(final),'separate original supervisor receipts required')
    temp=result.parent/'temp';ordinary_directory(temp)
    need(outer['env']=={'SystemRoot':config['system_root'],'WINDIR':config['system_root'],'TEMP':str(temp),'TMP':str(temp),'LOCALAPPDATA':config['local_appdata']},'fixed minimal outer environment required')
    release=dict(config,source_plan_sha256=config['source_inventory_sha256'],runtime_closure_sha256=config['runtime_manifest_sha256'])
    return release,plan,runtime,child_rows
