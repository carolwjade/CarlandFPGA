import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, time, platform

ROOT = pathlib.Path(__file__).resolve().parents[3]
EVIDENCE = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / '.local/deepeye-implementation-a/competition/deepeye/simulator'
ENGINE = ROOT / '.planning/deepeye-implementation-a/app-worker-ui/godot/Godot_v4.7.2-stable_win64.exe'
PIN = 'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def manifest(folder):
    return [{'path': p.relative_to(folder).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
            for p in sorted(folder.rglob('*')) if p.is_file() and '.godot' not in p.parts]

def write(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

def snapshot(name):
    target = EVIDENCE / name
    assert not target.exists(), str(target)
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns('.godot'))
    write(name + '-manifest.json', manifest(target))
    return target

def run(stage, label, script):
    project = EVIDENCE / stage
    assert project.is_dir() and project.is_relative_to(EVIDENCE)
    assert digest(ENGINE) == PIN
    command = [str(ENGINE), '--headless', '--path', str(project)]
    command += ['--editor', '--import'] if script == 'import' else ['--script', 'res://tests/' + script + '.gd']
    env = os.environ.copy()
    for key in ('APPDATA', 'LOCALAPPDATA'):
        private = EVIDENCE / 'user-data' / stage / key
        private.mkdir(parents=True, exist_ok=True)
        env[key] = str(private)
    start = time.monotonic()
    out = EVIDENCE / (label + '.stdout.txt')
    err = EVIDENCE / (label + '.stderr.txt')
    with out.open('wb') as stdout, err.open('wb') as stderr:
        proc = subprocess.Popen(command, cwd=project, stdout=stdout, stderr=stderr, env=env)
        timed_out = False
        try:
            code = proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            code = proc.wait(timeout=15)
    result = {'argv': command, 'cwd': str(project), 'pid': proc.pid, 'engine_sha256': PIN,
              'source_manifest': manifest(project), 'exit_code': code, 'timeout': timed_out,
              'terminal': proc.poll() is not None, 'seconds': time.monotonic()-start,
              'stdout_sha256': digest(out), 'stderr_sha256': digest(err),
              'stdout': str(out), 'stderr': str(err), 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(label + '.json', result)
    print(json.dumps({k: result[k] for k in ('pid','exit_code','timeout','terminal','seconds')}))
    print(out.read_text(encoding='utf-8', errors='replace')[-8000:])
    print(err.read_text(encoding='utf-8', errors='replace')[-8000:])
    return code

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['snapshot','run','verify'])
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    if args.action == 'snapshot':
        snapshot(args.args[0])
    elif args.action == 'run':
        raise SystemExit(run(*args.args))
    else:
        contract = json.loads((ROOT/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8'))
        actual = hashlib.sha256(json.dumps(contract['requirements'], sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()).hexdigest()
        assert actual == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
        receipt = json.loads((ROOT/'.planning/deepeye-resume-20261018/main-ui-and-g01-adoption-20261020/import-receipt.json').read_text(encoding='utf-8'))
        checks = []
        for row in receipt['imported_exact_files']:
            p = ROOT/'.local/deepeye-implementation-a'/row['target_project_path']
            checks.append({'path': str(p.relative_to(ROOT)), 'sha256': digest(p), 'matches': digest(p)==row['source']['sha256']})
        assert all(row['matches'] for row in checks)
        write('source-pin-check.json', {'requirements_sha256': actual, 'B_sources': checks, 'engine_sha256': digest(ENGINE),
                                      'os': platform.platform(), 'processor': platform.processor(), 'python': platform.python_version()})
        print(json.dumps({'requirements_sha256':actual, 'B_unchanged':len(checks), 'engine_sha256':digest(ENGINE)}))
