import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOST_DEPS = ROOT / '.local/deepeye-host-deps'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit('usage: run_capture.py LABEL --cwd PATH [--timeout SECONDS] -- COMMAND...')
    label = argv.pop(0)
    cwd = None
    timeout = 60.0
    while argv and argv[0] != '--':
        option = argv.pop(0)
        if option == '--cwd' and argv:
            cwd = Path(argv.pop(0))
        elif option.startswith('--cwd='):
            cwd = Path(option.split('=', 1)[1])
        elif option == '--timeout' and argv:
            timeout = float(argv.pop(0))
        elif option.startswith('--timeout='):
            timeout = float(option.split('=', 1)[1])
        else:
            raise SystemExit('unknown or incomplete option before --: ' + option)
    if argv[:1] == ['--']:
        argv.pop(0)
    if cwd is None or not argv:
        raise SystemExit('usage: run_capture.py LABEL --cwd PATH [--timeout SECONDS] -- COMMAND...')
    command = argv

    runs = HERE / 'runs'
    runs.mkdir(exist_ok=True)
    temp = HERE / 'temp' / label
    temp.mkdir(parents=True, exist_ok=False)
    stdout_path = runs / (label + '.stdout')
    stderr_path = runs / (label + '.stderr')
    command_path = runs / (label + '.json')
    for path in (stdout_path, stderr_path, command_path):
        if path.exists():
            raise SystemExit('refusing to overwrite evidence: ' + str(path))

    env = os.environ.copy()
    env.update(
        PYTHONDONTWRITEBYTECODE='1',
        PYTHONIOENCODING='utf-8',
        PYTHONPATH=str(HOST_DEPS),
        TEMP=str(temp),
        TMP=str(temp),
    )
    started = datetime.datetime.now(datetime.timezone.utc)
    started_monotonic = time.monotonic()
    with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=out,
            stderr=err,
            timeout=timeout,
            check=False,
        )
    elapsed = time.monotonic() - started_monotonic
    record = {
        'label': label,
        'at_utc': started.isoformat(),
        'elapsed_seconds': round(elapsed, 6),
        'command': command,
        'cwd': str(cwd.resolve()),
        'returncode': completed.returncode,
        'python_executable': sys.executable,
        'python_version': sys.version,
        'environment': {
            'PYTHONDONTWRITEBYTECODE': env['PYTHONDONTWRITEBYTECODE'],
            'PYTHONIOENCODING': env['PYTHONIOENCODING'],
            'PYTHONPATH': env['PYTHONPATH'],
            'TEMP': env['TEMP'],
            'TMP': env['TMP'],
        },
        'stdout': {
            'path': str(stdout_path),
            'bytes': stdout_path.stat().st_size,
            'sha256': digest(stdout_path),
        },
        'stderr': {
            'path': str(stderr_path),
            'bytes': stderr_path.stat().st_size,
            'sha256': digest(stderr_path),
        },
    }
    command_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'label': label,
        'returncode': completed.returncode,
        'stdout_sha256': record['stdout']['sha256'],
        'stderr_sha256': record['stderr']['sha256'],
    }, ensure_ascii=False))
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
