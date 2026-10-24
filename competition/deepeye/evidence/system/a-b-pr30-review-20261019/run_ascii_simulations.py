from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ALIAS = Path('C:/Users/CarlJade/Documents/CodexBuildLinks/deepeye-pr30-20261019')
SOURCE = ALIAS / 'exact-source'
TOOLS = Path('C:/modeltech64_2020.4/win64')
FPGA = SOURCE / 'competition/deepeye/fpga'
EVIDENCE = SOURCE / 'competition/deepeye/evidence'

def load(relative):
    path = EVIDENCE / relative
    spec = importlib.util.spec_from_file_location('pinned_peer_review', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def child(name):
    if name == 'stream':
        module = load('stream/stream-reset-20261018-09/main/main_stream_review.py')
        module.H = EVIDENCE / 'stream/stream-reset-20261018-09/main'
        module.CORE = FPGA / 'codec/deepeye_block_encoder.sv'
        module.TOOLS = TOOLS
        module.run(ALIAS / 'a-stream-ascii-ports', FPGA / 'stream/deepeye_block_stream.sv')
        return
    module = load('codec/block-encoder-20261018-08/main/main_encoder_review.py')
    out = ALIAS / 'a-encoder-ascii-ports'
    out.mkdir(exist_ok=False)
    cases = module.build_cases()
    (out / 'cases.json').write_text(json.dumps(cases, separators=(',', ':')) + '\n', encoding='utf-8')
    (out / 'cases.txt').write_text('\n'.join(' '.join(map(str, [c['id'], c['count'], c['e'], len(c['samples']), c['last_mode'], c['abort_stage'], c['abort_reset'], c['seed'], *c['samples']])) for c in cases) + '\n', encoding='ascii')
    rtl = FPGA / 'codec/deepeye_block_encoder.sv'
    tb = EVIDENCE / 'codec/block-encoder-20261018-08/main/main_encoder_port_tb.sv'
    module.run([TOOLS / 'vsim.exe', '-version'], out, out, 'version')
    module.run([TOOLS / 'vlib.exe', 'work'], out, out, 'vlib')
    module.run([TOOLS / 'vlog.exe', '-sv', '-work', 'work', rtl, tb], out, out, 'vlog')
    do = 'onerror {quit -code 8}\nonbreak {quit -code 7}\nvsim -voptargs=+acc work.main_encoder_port_tb {+INPUT=' + (out / 'cases.txt').as_posix() + '} {+OUTPUT=' + (out / 'ports.txt').as_posix() + '}\nrun -all\nquit -code 0\n'
    (out / 'run.do').write_text(do, encoding='ascii')
    result = module.run([TOOLS / 'vsim.exe', '-c', '-do', out / 'run.do'], out, out, 'vsim', 300)
    assert b'MAIN_PORT_COMPLETE' in result.stdout and not any(marker in result.stdout for marker in (b'MAIN_PORT_FAIL', b'** Error', b'** Fatal'))
    stats = module.verify(cases, out / 'ports.txt')
    receipt = {'status': 'PASS_A_REPLAY_OF_PEER_INDEPENDENT_ENCODER_SUITE', 'rtl_sha256': module.sha(rtl), 'tb_sha256': module.sha(tb), 'checker_sha256': module.sha(module.__file__), 'cases_sha256': module.sha(out / 'cases.json'), 'ports_sha256': module.sha(out / 'ports.txt'), 'stats': stats, 'scope': 'digital simulation only; original cases/checker and exact source; path-safe A invocation'}
    (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))

def main():
    assert ALIAS.is_junction() and ALIAS.resolve() == HERE
    if len(sys.argv) == 2:
        child(sys.argv[1])
        return
    tmp = ALIAS / 'ascii-simulation-temp'
    tmp.mkdir(exist_ok=False)
    environment = os.environ.copy()
    environment.update(TEMP=str(tmp), TMP=str(tmp), PYTHONDONTWRITEBYTECODE='1')
    rows = []
    for name in ('stream', 'encoder'):
        argv = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), name]
        completed = subprocess.run(argv, cwd=ALIAS, env=environment, capture_output=True, timeout=400)
        (HERE / f'{name}-ascii.stdout.txt').write_bytes(completed.stdout)
        (HERE / f'{name}-ascii.stderr.txt').write_bytes(completed.stderr)
        rows.append({'name': name, 'argv': argv, 'cwd': str(ALIAS), 'exit_code': completed.returncode, 'stdout_sha256': hashlib.sha256(completed.stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(completed.stderr).hexdigest()})
        (HERE / 'ascii-simulation-commands.json').write_bytes((json.dumps(rows, ensure_ascii=False, indent=2) + '\n').encode())
        print(name, 'exit', completed.returncode, flush=True)
        if completed.returncode:
            print(completed.stderr.decode('utf-8', errors='replace')[-1500:], flush=True)
            raise SystemExit(completed.returncode)

if __name__ == '__main__':
    main()
