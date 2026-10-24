"""Explicit source-tree viewer launch. Uses this trusted Python installation.

No PATH discovery, shell, provider probe, global environment change or service.
Exported PCK applications require a separately reviewed physical sidecar install.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

GODOT_SHA256 = 'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
RUNTIME_SHA256 = '2572eb57f5771bdb1ea4343e48591ca61650ef5dd828193d08c05d259a17d784'
BUNDLE_SHA256 = '9e9c766ec7ad0268810c0b22ad26144fd481ef6984a6295e68608ec30c04f9de'

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def binding():
    return {'executable':str(Path(sys.executable).resolve()),'prefix':str(Path(sys.prefix).resolve()),'base_prefix':str(Path(sys.base_prefix).resolve())}

def child_environment(run_dir, source=None):
    source=os.environ if source is None else source
    run_dir=Path(run_dir).resolve()
    allowed={'SYSTEMROOT','WINDIR','COMSPEC','SYSTEMDRIVE','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}
    env={k:v for k,v in source.items() if k.upper() in allowed}
    for name in ('TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME'):
        dest=run_dir/name.lower();dest.mkdir(parents=True,exist_ok=True);env[name]=str(dest)
    env['DEEPEYE_LAYOUT_RUNTIME']=json.dumps(binding(),ensure_ascii=True,separators=(',',':'))
    return env

def verify_installation(godot):
    native=Path(__file__).resolve().parent
    godot=Path(godot)
    if not godot.is_absolute() or not godot.is_file() or digest(godot)!=GODOT_SHA256:
        raise ValueError('Godot executable does not match the reviewed source-tree engine')
    runtime_file=native/'layout_runtime.json'
    if digest(runtime_file)!=RUNTIME_SHA256:
        raise ValueError('Runtime identity manifest mismatch')
    runtime=json.loads(runtime_file.read_text(encoding='utf-8'))
    current=binding()
    if digest(current['executable']) not in runtime['executable_sha256']:
        raise ValueError('Run this launcher with the approved existing Python interpreter')
    for entry in runtime['dependencies']:
        if digest(Path(current[entry['origin']])/entry['path'])!=entry['sha256']:
            raise ValueError('Approved Python installation identity mismatch')
    bundle_file=native/'layout_commit_bundle.json'
    if digest(bundle_file)!=BUNDLE_SHA256:
        raise ValueError('Layout helper bundle mismatch')
    bundle=json.loads(bundle_file.read_text(encoding='utf-8'))
    if set(bundle)!={'schema','helper','leaf'} or bundle['schema']!=1:
        raise ValueError('Layout helper bundle schema mismatch')
    for key in ('helper','leaf'):
        entry=bundle[key]
        if set(entry)!={'path','sha256'} or Path(entry['path']).name!=entry['path'] or digest(native/entry['path'])!=entry['sha256']:
            raise ValueError('Layout helper member mismatch')
    return native.parent

def viewer_command(godot, project, headless=False):
    return [str(godot)]+(['--headless'] if headless else [])+['--path',str(project)]

def main(argv=None):
    parser=argparse.ArgumentParser(description='Launch the configured DeepEye source-tree viewer')
    parser.add_argument('--godot',required=True,type=Path,help='Explicit absolute reviewed Godot executable')
    parser.add_argument('--run-dir',required=True,type=Path,help='Owned viewer userdata/cache/temp directory')
    parser.add_argument('--validate-only',action='store_true')
    parser.add_argument('--headless',action='store_true',help='Explicitly run without display/GPU UI')
    args=parser.parse_args(argv)
    try:
        project=verify_installation(args.godot)
        if args.validate_only:
            print('Source-tree engine, helper bundle and existing Python identity verified; no viewer launched.')
            return 0
        env=child_environment(args.run_dir)
        child=subprocess.Popen(viewer_command(args.godot,project,args.headless),env=env,cwd=project,shell=False)
        print('DEEPEYE_VIEWER_CHILD_PID='+str(child.pid),flush=True)
        code=child.wait()
        print('DEEPEYE_VIEWER_CHILD_EXIT='+str(code),flush=True)
        return code
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('Viewer launch unavailable: '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
