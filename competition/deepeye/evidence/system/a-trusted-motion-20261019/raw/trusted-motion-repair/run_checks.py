import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
label, mode = sys.argv[1:]
tests = ['competition.deepeye.tests.simulation.test_motion_executor.MotionExecutorTests.' + name for name in (
    'test_later_materialization_failure_retires_pending_without_losing_committed_history',
    'test_caught_materialization_failure_in_final_callback_vetoes_publication',
)]
if mode == 'full':
    tests = ['competition.deepeye.tests.simulation.' + name for name in (
        'test_motion_executor', 'test_passage_phase', 'test_workspace_boundaries',
        'test_solid_clearance', 'test_pc_direct_runtime',
    )]
elif mode != 'focused':
    raise ValueError('unknown check mode')
env = dict(os.environ)
env['PYTHONPATH'] = str(PRODUCT) + os.pathsep + str(ROOT / '.local/deepeye-host-deps')
command = [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v', *tests]
assert not (OUT / (label + '.command.json')).exists(), 'Preserve original attempt'
result = subprocess.run(command, cwd=PRODUCT, env=env, capture_output=True)
(OUT / (label + '.stdout.log')).write_bytes(result.stdout)
(OUT / (label + '.stderr.log')).write_bytes(result.stderr)
(OUT / (label + '.command.json')).write_text(json.dumps({
    'command': command, 'cwd': str(PRODUCT), 'PYTHONPATH': env['PYTHONPATH'],
    'exit_code': result.returncode,
}, indent=2) + '\n', encoding='utf-8')
print(result.stderr.decode('utf-8', 'replace')[-5500:])
raise SystemExit(result.returncode)
