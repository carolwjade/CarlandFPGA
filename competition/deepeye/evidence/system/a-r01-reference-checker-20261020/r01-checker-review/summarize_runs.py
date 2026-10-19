import datetime
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
RUNS = HERE / 'runs'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = []
for record_path in sorted(RUNS.glob('*.json')):
    record = json.loads(record_path.read_text(encoding='utf-8'))
    label = record['label']
    stdout_path = RUNS / (label + '.stdout')
    stderr_path = RUNS / (label + '.stderr')
    stdout_text = stdout_path.read_text(encoding='utf-8')
    stderr_text = stderr_path.read_text(encoding='utf-8')
    summary = {
        'label': label,
        'command': record['command'],
        'cwd': record['cwd'],
        'returncode': record['returncode'],
        'stdout': {'bytes': stdout_path.stat().st_size, 'sha256': sha256(stdout_path)},
        'stderr': {'bytes': stderr_path.stat().st_size, 'sha256': sha256(stderr_path)},
    }
    try:
        stdout_json = json.loads(stdout_text)
    except json.JSONDecodeError:
        stdout_json = None
    if stdout_json is not None:
        summary['report'] = {
            'status': stdout_json.get('status'),
            'scope': stdout_json.get('scope'),
            'R01': stdout_json.get('R01'),
            'formal_acceptance': stdout_json.get('formal_acceptance'),
            'hardware_enable_eligible': stdout_json.get('hardware_enable_eligible'),
            'source_status': stdout_json.get('source', {}).get('status'),
            'error': stdout_json.get('error'),
        }
    match = re.search(r'Ran ([0-9]+) tests? in', stderr_text)
    if match:
        summary['tests_ran'] = int(match.group(1))
        summary['tests_ok'] = bool(re.search(r'^OK$', stderr_text, re.MULTILINE))
    records.append(summary)

report = {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'run_count': len(records),
    'runs': records,
}
output = HERE / 'runs-summary.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'run_count': len(records),
    'labels': [record['label'] for record in records],
}, ensure_ascii=False))
