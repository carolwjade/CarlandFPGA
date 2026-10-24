"""Independent static checks for the bounded R01 checker repair rereview."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PRODUCT = REPO / '.local' / 'deepeye-implementation-a'
STAGE_PRODUCT = ROOT / 'stage-01' / 'product'
ORIGINAL_REVIEW = REPO / '.planning' / 'deepeye-resume-20261018' / 'r01-checker-review'
REPAIR = REPO / '.planning' / 'deepeye-resume-20261018' / 'r01-checker-repair'
PRE_REPAIR = REPAIR / 'pre-repair'
REQUESTED_CANDIDATE = '9582bde875bf1aa2daef6c8f1b3d4925ed67cba0a22cb11f9d7ac0d773291f90'
ORIGINAL_MANIFEST = REPORT = REPO / '.planning' / 'deepeye-resume-20261018' / 'r01-checker-main' / 'candidate-manifest.json'
EXPECTED_WEIGHTS = {
    'system_completeness': 20,
    'pc_ai': 20,
    'fpga_quality': 25,
    'cooperation': 20,
    'engineering_innovation': 15,
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def record(path):
    path = Path(path)
    if not path.exists():
        return {'path': str(path), 'exists': False}
    data = path.read_bytes()
    return {'path': str(path), 'exists': True, 'bytes': len(data), 'sha256': sha256(data)}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def tree_records(root):
    files = sorted(p for p in Path(root).rglob('*') if p.is_file())
    rows = []
    digest = hashlib.sha256()
    for path in files:
        data = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        rows.append({'path': rel, 'bytes': len(data), 'sha256': sha256(data)})
        digest.update(rel.encode('utf-8') + b'\0' + str(len(data)).encode('ascii') + b'\0' + sha256(data).encode('ascii') + b'\n')
    return {'count': len(files), 'tree_sha256': digest.hexdigest(), 'files': rows}


def method_bodies(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
            result[node.name] = ast.dump(node, include_attributes=False)
    return result


def checker_weights(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'ASSESSMENT_WEIGHTS':
            return ast.literal_eval(node.value)
    return None


def line_hit(path, needle):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines, 1):
        if needle in line:
            return {'line': index, 'text': line.strip()}
    return None


def main():
    candidate = record(REPAIR / 'candidate-manifest.json')
    patch = record(REPAIR / 'repair.patch')
    repair_manifest = read_json(REPAIR / 'candidate-manifest.json')
    original_manifest = read_json(ORIGINAL_MANIFEST)
    original_candidate = record(ORIGINAL_MANIFEST)
    source_rel = [
        'competition/deepeye/tools/check_rules.py',
        'competition/deepeye/tests/test_check_rules.py',
        'competition/deepeye/docs/rules_verification.md',
    ]
    source_records = []
    for rel in source_rel:
        before = record(PRE_REPAIR / rel)
        after = record(PRODUCT / rel)
        staged = record(STAGE_PRODUCT / rel)
        source_records.append({
            'path': rel,
            'before': before,
            'after': after,
            'staged': staged,
            'after_matches_manifest': after.get('sha256') == repair_manifest['source_files'].get(rel),
            'staged_matches_after': staged.get('sha256') == after.get('sha256'),
            'before_matches_original_manifest': before.get('sha256') == original_manifest['source_files'].get(rel),
        })
    input_records = []
    for absolute, expected in repair_manifest['input_pins'].items():
        current = record(absolute)
        input_records.append({'path': absolute, 'expected': expected, 'current': current, 'matches': current.get('sha256') == expected})
    evidence_records = []
    for relative, expected in repair_manifest['repair_evidence'].items():
        current = record(REPAIR / relative)
        evidence_records.append({'path': relative, 'expected': expected, 'current': current, 'matches': current.get('sha256') == expected})
    pre = method_bodies(PRE_REPAIR / 'competition/deepeye/tests/test_check_rules.py')
    after = method_bodies(PRODUCT / 'competition/deepeye/tests/test_check_rules.py')
    unchanged = sorted(name for name in pre if name in after and pre[name] == after[name])
    changed = sorted(name for name in pre if name in after and pre[name] != after[name])
    removed = sorted(name for name in pre if name not in after)
    added = sorted(name for name in after if name not in pre)
    rules_path = PRODUCT / 'competition/deepeye/docs/rules.json'
    rules = read_json(rules_path)
    checker_constant = checker_weights(PRODUCT / 'competition/deepeye/tools/check_rules.py')
    rules_weights = rules.get('assessment_weights')
    rules_lines = rules_path.read_text(encoding='utf-8').splitlines()
    weights_start = next((i for i, line in enumerate(rules_lines, 1) if '"assessment_weights"' in line), None)
    weights_end = None
    if weights_start is not None:
        weights_end = next((i for i, line in enumerate(rules_lines, 1) if i >= weights_start and line.strip() == '}'), None)
    doc_text = (PRODUCT / 'competition/deepeye/docs/rules_verification.md').read_text(encoding='utf-8')
    taskbook = REPO / 'docs' / 'competition' / 'deepeye-2026' / 'taskbook_final.md'
    plan = REPO / '.planning' / 'deepeye-resume-20261018' / 'r01-checker-main' / 'plan.md'
    review_tree = tree_records(ORIGINAL_REVIEW)
    pycache = []
    for base in (PRODUCT / 'competition/deepeye', STAGE_PRODUCT / 'competition/deepeye'):
        pycache.extend(str(p) for p in base.rglob('__pycache__') if p.is_dir())
    git = r'C:\Users\CarlJade\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe'
    head = subprocess.run([git, '-C', str(PRODUCT), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    branch = subprocess.run([git, '-C', str(PRODUCT), 'branch', '--show-current'], capture_output=True, text=True)
    result = {
        'schema': 1,
        'work_id': 'A-R01-CHECKER-REREVIEW-20261020-v1',
        'requested_candidate_sha256': REQUESTED_CANDIDATE,
        'candidate_manifest': candidate,
        'candidate_manifest_matches_request': candidate.get('sha256') == REQUESTED_CANDIDATE,
        'repair_patch': patch,
        'repair_patch_matches_manifest': patch.get('sha256') == repair_manifest['repair_evidence'].get('repair.patch'),
        'original_candidate_manifest': original_candidate,
        'repair_manifest_original_candidate': repair_manifest.get('original_candidate_sha256'),
        'original_candidate_pin_matches': original_candidate.get('sha256') == repair_manifest.get('original_candidate_sha256'),
        'sources': source_records,
        'inputs': input_records,
        'repair_evidence': evidence_records,
        'original_review_tree': {'count': review_tree['count'], 'tree_sha256': review_tree['tree_sha256']},
        'original_review_key_files': {
            'findings.md': record(ORIGINAL_REVIEW / 'findings.md'),
            'receipt.json': record(ORIGINAL_REVIEW / 'receipt.json'),
            'runs-summary.json': record(ORIGINAL_REVIEW / 'runs-summary.json'),
            'provenance-check.json': record(ORIGINAL_REVIEW / 'provenance-check.json'),
            'inspection_manifest.json': record(ORIGINAL_REVIEW / 'inspection_manifest.json'),
        },
        'test_methods': {
            'before_count': len(pre),
            'after_count': len(after),
            'unchanged_count': len(unchanged),
            'changed': changed,
            'removed': removed,
            'added': added,
            'original_17_unchanged': len(unchanged) == 17 and not changed and not removed,
        },
        'assessment_weights': {
            'expected': EXPECTED_WEIGHTS,
            'checker_constant': checker_constant,
            'frozen_rules': rules_weights,
            'checker_matches_expected': checker_constant == EXPECTED_WEIGHTS,
            'frozen_rules_match_expected': rules_weights == EXPECTED_WEIGHTS,
            'checker_matches_frozen_rules': checker_constant == rules_weights,
            'exact_key_set': isinstance(checker_constant, dict) and set(checker_constant) == set(EXPECTED_WEIGHTS),
            'all_values_exact_int': isinstance(checker_constant, dict) and all(type(value) is int for value in checker_constant.values()),
            'sum': sum(checker_constant.values()) if isinstance(checker_constant, dict) else None,
            'sum_is_100': isinstance(checker_constant, dict) and sum(checker_constant.values()) == 100,
            'docs_mentions_all_labels_and_values': all(term in doc_text for term in ('system completeness 20', 'PC AI 20', 'FPGA quality 25', 'cooperation 20', 'engineering innovation 15')),
            'rules_json_weight_lines': {'start': weights_start, 'end': weights_end},
        },
        'source_association': {
            'taskbook': {'path': str(taskbook), 'line': line_hit(taskbook, '不拿3.3权重代替'), 'sha256': record(taskbook).get('sha256')},
            'selected_plan': {'path': str(plan), 'line': line_hit(plan, 'No3.3 weights substitution'), 'sha256': record(plan).get('sha256')},
        },
        'pycache_paths': pycache,
        'git': {'head': head.stdout.strip(), 'head_exit': head.returncode, 'branch': branch.stdout.strip(), 'branch_exit': branch.returncode},
        'formal29': 'not_run',
        'R01': 'not_run',
        'formal_acceptance': False,
        'hardware_enable_eligible': False,
    }
    (ROOT / 'review-static.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
