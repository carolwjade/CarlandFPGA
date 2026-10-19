from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'exact-source'
TOOLS = Path('C:/modeltech64_2020.4/win64')
FPGA = SOURCE / 'competition/deepeye/fpga'
EVIDENCE = SOURCE / 'competition/deepeye/evidence'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def stream_child():
    file = EVIDENCE / 'stream/stream-reset-20261018-09/main/main_stream_review.py'
    spec = importlib.util.spec_from_file_location('reviewed_b_stream', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CORE = FPGA / 'codec/deepeye_block_encoder.sv'
    module.TOOLS = TOOLS
    module.run(HERE / 'a-stream-public-ports', FPGA / 'stream/deepeye_block_stream.sv')

def main():
    if sys.argv[1:] == ['--stream-child']:
        stream_child()
        return
    assert json.loads((HERE / 'input-verification.json').read_text(encoding='utf-8'))[-1]['tested_commit'] == '433db2a82854a669778eb8c3cd35c309623a087e'
    sources = [FPGA / 'codec/deepeye_block_encoder.sv', FPGA / 'stream/deepeye_block_stream.sv',
               EVIDENCE / 'stream/stream-reset-20261018-09/main/main_stream_review.py',
               EVIDENCE / 'stream/stream-reset-20261018-09/main/main_stream_ports.sv',
               EVIDENCE / 'codec/block-encoder-20261018-08/main/main_encoder_review.py',
               EVIDENCE / 'codec/block-encoder-20261018-08/main/main_encoder_port_tb.sv']
    before = {str(p.relative_to(SOURCE)): sha(p) for p in sources}
    (HERE / 'simulation-source-before.json').write_bytes((json.dumps(before, indent=2) + '\n').encode())
    tmp = HERE / 'simulation-temp'
    tmp.mkdir(exist_ok=False)
    environment = os.environ.copy()
    environment.update(TEMP=str(tmp), TMP=str(tmp), PYTHONDONTWRITEBYTECODE='1')
    jobs = [
        ('stream', [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--stream-child']),
        ('encoder', [sys.executable, '-B', '-X', 'utf8', str(EVIDENCE / 'codec/block-encoder-20261018-08/main/main_encoder_review.py'), '--rtl', str(FPGA / 'codec/deepeye_block_encoder.sv'), '--tb', str(EVIDENCE / 'codec/block-encoder-20261018-08/main/main_encoder_port_tb.sv'), '--modelsim-home', str(TOOLS.parent), '--output', str(HERE / 'a-encoder-public-ports')]),
    ]
    rows = []
    for name, argv in jobs:
        start = datetime.now(timezone.utc).isoformat()
        completed = subprocess.run(argv, cwd=HERE, env=environment, capture_output=True, timeout=300)
        (HERE / f'{name}.stdout.txt').write_bytes(completed.stdout)
        (HERE / f'{name}.stderr.txt').write_bytes(completed.stderr)
        rows.append({'name': name, 'argv': argv, 'cwd': str(HERE), 'started_utc': start, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'exit_code': completed.returncode, 'stdout_sha256': hashlib.sha256(completed.stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(completed.stderr).hexdigest()})
        (HERE / 'simulation-commands.json').write_bytes((json.dumps(rows, ensure_ascii=False, indent=2) + '\n').encode())
        print(name, 'exit', completed.returncode, flush=True)
        if completed.returncode:
            print(completed.stderr.decode('utf-8', errors='replace')[-1200:], flush=True)
            raise SystemExit(completed.returncode)
    after = {str(p.relative_to(SOURCE)): sha(p) for p in sources}
    assert before == after
    (HERE / 'simulation-source-after.json').write_bytes((json.dumps(after, indent=2) + '\n').encode())

if __name__ == '__main__':
    main()
