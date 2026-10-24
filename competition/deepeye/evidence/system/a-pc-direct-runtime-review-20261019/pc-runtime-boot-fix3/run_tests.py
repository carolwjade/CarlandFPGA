import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
ENV = os.environ.copy()
ENV.update(PYTHONPATH=str(PRODUCT) + os.pathsep + str(ROOT / '.local/deepeye-host-deps'),
           PYTHONDONTWRITEBYTECODE='1', TEMP=str(OUT), TMP=str(OUT))
PATHS = json.loads((OUT / 'source-before.json').read_text())


def hashes():
    return {p: hashlib.sha256((PRODUCT / p).read_bytes()).hexdigest() for p in PATHS}


def run(name, args, expected):
    before = hashes()
    command = [sys.executable, '-B', '-X', 'utf8'] + args
    result = subprocess.run(command, cwd=PRODUCT, env=ENV, capture_output=True)
    for suffix, payload in (('stdout.txt', result.stdout), ('stderr.txt', result.stderr)):
        with (OUT / (name + '.' + suffix)).open('xb') as stream:
            stream.write(payload)
    after = hashes()
    record = {'command': command, 'cwd': str(PRODUCT), 'exit_code': result.returncode,
              'source_before': before, 'source_after': after,
              'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
              'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()}
    with (OUT / (name + '.json')).open('xb') as stream:
        stream.write((json.dumps(record, indent=2) + '\n').encode())
    print(json.dumps({'name': name, 'exit_code': result.returncode,
                      'tail': result.stderr.decode('utf-8', 'replace')[-180:]}))
    assert before == after and result.returncode == expected


if sys.argv[1] == 'red':
    run('red', ['-m', 'unittest', 'competition.deepeye.tests.simulation.test_pc_direct_runtime', '-v'], 1)
elif sys.argv[1] == 'green':
    run('green', ['-m', 'unittest', 'competition.deepeye.tests.simulation.test_pc_direct_runtime', '-v'], 0)
    run('reviewer-probe', [str(OUT / 'new_probes.py')], 0)
else:
    raise ValueError('red or green required')
