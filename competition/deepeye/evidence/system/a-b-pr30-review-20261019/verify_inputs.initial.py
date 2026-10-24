from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WT = Path('C:/Users/CarlJade/.codex/worktrees/deepeye-b-pr30-review/FPGA多机协作开发')
HEAD = '433db2a82854a669778eb8c3cd35c309623a087e'
OPERATIONS = [
    ('B-DEEPEYE-BLOCK-ENCODER-20261018-08', '854f092b0d79c014bbd8669ae407d88c0375933b0c672f494f964b6ad2c414ab', '1d9241391495c931a925203b8b9efb2f7e2cf31256042aae997c009b2e186440'),
    ('B-DEEPEYE-STREAM-RESET-20261018-09', 'e6149beab779f6df7db1e8f780ef1c2d1ad5e555b780684500ba82cce37766a3', '34ee72df3b3b2dee80402865d79dcdc1084b128ed3ae41487bca073b1261d126'),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.run(['git', '-C', str(WT), *args], capture_output=True, check=True).stdout

def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert not git('status', '--porcelain')
scope = json.loads((WT / 'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8'))
assert sha(json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) == 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
results = []
for operation, expected_manifest, expected_request in OPERATIONS:
    relative = f'handoffs/b/{operation}/manifest.json'
    raw = (WT / relative).read_bytes()
    assert sha(raw) == expected_manifest
    assert raw == git('show', f'{HEAD}:{relative}')
    manifest = json.loads(raw)
    assert manifest['request_hash'] == expected_request
    assert sha(json.dumps(manifest['request'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) == expected_request
    command = [sys.executable, '-B', '-X', 'utf8', str(ROOT / '.agents/skills/fpga-multi-node/scripts/handoff.py'), 'verify', '--root', str(WT), '--manifest', str(WT / relative)]
    run = subprocess.run(command, capture_output=True)
    (HERE / f'{operation}.verify.stdout.txt').write_bytes(run.stdout)
    (HERE / f'{operation}.verify.stderr.txt').write_bytes(run.stderr)
    assert run.returncode == 0, run.stderr.decode(errors='replace')[:500]
    records = []
    process = subprocess.Popen(['git', '-C', str(WT), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for path, expected in manifest['files'].items():
            target = WT / path
            assert target.resolve().is_relative_to(WT.resolve()) and not target.is_symlink()
            actual = {'sha256': file_hash(target), 'size': target.stat().st_size}
            assert actual == expected, (path, actual, expected)
            for revision in (HEAD, manifest['request']['code_commit']):
                process.stdin.write(f'{revision}:{path}\n'.encode())
                process.stdin.flush()
                header = process.stdout.readline().decode().strip().split()
                assert len(header) == 3 and header[1] == 'blob', (path, header)
                remaining = int(header[2]); h = hashlib.sha256()
                while remaining:
                    block = process.stdout.read(min(1024 * 1024, remaining))
                    assert block, path
                    h.update(block); remaining -= len(block)
                assert process.stdout.read(1) == b'\n'
                assert h.hexdigest() == expected['sha256'] and int(header[2]) == expected['size'], (path, revision)
            records.append({'path': path, **actual})
    finally:
        process.stdin.close()
        code = process.wait(timeout=30)
        assert code == 0, process.stderr.read().decode(errors='replace')[:500]
    results.append({'operation_id': operation, 'request_hash': expected_request, 'manifest_sha256': expected_manifest, 'tested_commit': HEAD, 'source_commit': manifest['request']['code_commit'], 'standard_verify_exit_code': run.returncode, 'standard_verify_command': command, 'file_count': len(records), 'records': records})
(HERE / 'input-verification.json').write_bytes((json.dumps(results, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps([{'operation_id': row['operation_id'], 'count': row['file_count'], 'exact_source_and_head_blobs': True} for row in results]))
