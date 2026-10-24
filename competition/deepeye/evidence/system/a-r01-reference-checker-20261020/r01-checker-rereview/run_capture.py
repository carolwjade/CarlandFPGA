"""Capture one bounded review command without writing to PRODUCT."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--temp', required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        raise SystemExit('missing command after --')
    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        raise SystemExit('cwd is not a directory: ' + str(cwd))
    temp = Path(args.temp).resolve()
    if not temp.is_dir():
        raise SystemExit('temp is not a directory: ' + str(temp))
    run_dir = ROOT / 'runs' / args.label
    if run_dir.exists():
        raise SystemExit('refusing to overwrite existing run: ' + str(run_dir))
    run_dir.mkdir(parents=True)
    env = os.environ.copy()
    removed_pythonpath = env.pop('PYTHONPATH', None)
    env.update({
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONNOUSERSITE': '1',
        'PYTHONPYCACHEPREFIX': str(temp / 'pycache'),
        'TEMP': str(temp),
        'TMP': str(temp),
    })
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    timed_out = False
    try:
        process = subprocess.run(command, cwd=str(cwd), env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=args.timeout, check=False)
        code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        code = 124
        stdout = error.stdout or b''
        stderr = error.stderr or b''
    finished = datetime.now(timezone.utc).isoformat()
    (run_dir / 'stdout.log').write_bytes(stdout)
    (run_dir / 'stderr.log').write_bytes(stderr)
    (run_dir / 'exit_code.txt').write_text(str(code) + '\n', encoding='utf-8')
    record = {
        'label': args.label,
        'argv': command,
        'cwd': str(cwd),
        'temp': str(temp),
        'started_utc': started,
        'finished_utc': finished,
        'duration_s': round(time.monotonic() - clock, 3),
        'timed_out': timed_out,
        'exit_code': code,
        'stdout': {'bytes': len(stdout), 'sha256': sha256(stdout)},
        'stderr': {'bytes': len(stderr), 'sha256': sha256(stderr)},
        'environment': {
            'PYTHONDONTWRITEBYTECODE': env['PYTHONDONTWRITEBYTECODE'],
            'PYTHONIOENCODING': env['PYTHONIOENCODING'],
            'PYTHONNOUSERSITE': env['PYTHONNOUSERSITE'],
            'PYTHONPYCACHEPREFIX': env['PYTHONPYCACHEPREFIX'],
            'TEMP': env['TEMP'],
            'TMP': env['TMP'],
        },
        'removed_pythonpath': removed_pythonpath,
    }
    (run_dir / 'command.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
