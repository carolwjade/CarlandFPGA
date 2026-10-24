import ast
from collections import defaultdict
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
MAIN = ROOT / '.planning/deepeye-resume-20261018/r01-checker-main'
MANIFEST = MAIN / 'candidate-manifest.json'
PINNED_MANIFEST_SHA = '85a6db6ee4f839685a47770590fcbca6683862927318d94d05f749fad3b3c8cd'
BASE = '889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1'
GIT = Path(r'C:\Users\CarlJade\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path, expected=None):
    path = Path(path)
    actual = sha256(path) if path.is_file() else None
    return {
        'path': str(path),
        'exists': path.is_file(),
        'bytes': path.stat().st_size if path.is_file() else None,
        'sha256': actual,
        'expected_sha256': expected,
        'matches': actual == expected if expected is not None else None,
    }


def git(*args):
    completed = subprocess.run([str(GIT), '-C', str(PRODUCT), *args], capture_output=True, text=True, check=False)
    return {
        'args': list(args),
        'returncode': completed.returncode,
        'stdout': completed.stdout,
        'stderr': completed.stderr,
    }


def import_record(source_path):
    tree = ast.parse(source_path.read_text(encoding='utf-8'), filename=str(source_path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split('.')[0])
    records = []
    for name in sorted(names):
        spec = importlib.util.find_spec(name)
        origin = spec.origin if spec else None
        path = Path(origin) if origin and Path(origin).is_file() else None
        records.append({
            'name': name,
            'origin': origin,
            'sha256': sha256(path) if path else None,
        })
    return records


def main():
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources = []
    for relative, expected in data['source_files'].items():
        path = PRODUCT / relative
        item = file_record(path, expected)
        item['relative_path'] = relative
        item['absent_in_base'] = git('cat-file', '-e', BASE + ':' + relative)['returncode'] != 0
        item['worktree_status'] = git('status', '--short', '--untracked-files=all', '--', relative)
        sources.append(item)

    canonical_by_basename = defaultdict(list)
    canonical_inputs = [
        PRODUCT / 'competition/deepeye/docs/rules.json',
        PRODUCT / 'competition/deepeye/docs/requirements_trace.csv',
        PRODUCT / 'docs/competition/deepeye-2026/immutable_scope.json',
        ROOT / 'docs/competition/deepeye-2026/immutable_scope.json',
        ROOT / 'docs/competition/deepeye-2026/taskbook_final.md',
        ROOT / 'docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf',
    ]
    for path in canonical_inputs:
        canonical_by_basename[path.name].append(file_record(path))

    input_pins = []
    for recorded, expected in data['input_pins'].items():
        name = Path(recorded).name
        candidates = canonical_by_basename.get(name, [])
        matching = [candidate for candidate in candidates if candidate['sha256'] == expected]
        input_pins.append({
            'recorded_path': recorded,
            'recorded_path_exists': Path(recorded).is_file(),
            'expected_sha256': expected,
            'canonical_candidates': candidates,
            'matched_canonical_path': matching[0]['path'] if matching else None,
            'matches': bool(matching),
        })

    evidence = []
    for relative, expected in data['evidence_files'].items():
        item = file_record(MAIN / relative, expected)
        item['relative_path'] = relative
        evidence.append(item)

    cli_command_paths = {}
    for name in ('cli-default-command.json', 'cli-full-command.json', 'cli-reference-command.json'):
        record = json.loads((MAIN / name).read_text(encoding='utf-8'))
        cli_command_paths[name] = [
            {
                'argument': value,
                'is_absolute_windows_path': isinstance(value, str) and len(value) > 2 and value[1:3] == ':\\',
                'exists_as_recorded': Path(value).exists() if isinstance(value, str) and len(value) > 2 and value[1:3] == ':\\' else None,
            }
            for value in record['command']
        ]

    checker = PRODUCT / 'competition/deepeye/tools/check_rules.py'
    tests = PRODUCT / 'competition/deepeye/tests/test_check_rules.py'
    result = {
        'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'root': str(ROOT),
        'product': str(PRODUCT),
        'python_executable': sys.executable,
        'python_version': sys.version,
        'candidate_manifest': file_record(MANIFEST, PINNED_MANIFEST_SHA),
        'candidate_base_head': data['base_head'],
        'product_head': git('rev-parse', 'HEAD'),
        'formal29': data.get('formal29'),
        'candidate_source_count': len(sources),
        'sources': sources,
        'input_pin_count': len(input_pins),
        'input_pins': input_pins,
        'canonical_inputs': {name: records for name, records in canonical_by_basename.items()},
        'evidence_file_count': len(evidence),
        'evidence_files': evidence,
        'recorded_cli_paths': cli_command_paths,
        'checker_imports': import_record(checker),
        'test_imports': import_record(tests),
    }
    output = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'inventory.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'output': str(output),
        'manifest_matches': result['candidate_manifest']['matches'],
        'sources_match': all(item['matches'] for item in sources),
        'all_sources_absent_in_base': all(item['absent_in_base'] for item in sources),
        'inputs_match': all(item['matches'] for item in input_pins),
        'evidence_match': all(item['matches'] for item in evidence),
        'evidence_count': len(evidence),
        'formal29': data.get('formal29'),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
