import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(name):
    path = HERE / name
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


runs_summary = load('runs-summary.json')
inventory = load('inventory-after.json')
requirements = load('requirements-check.json')
provenance = load('provenance-check.json')
pin_comparison = load('pin-comparison.json')
failed = load('failed-attempts.json')

by_label = {item['label']: item for item in runs_summary['runs']}


def command_record(label):
    item = by_label[label]
    result = {
        'label': label,
        'command': item['command'],
        'cwd': item['cwd'],
        'returncode': item['returncode'],
        'stdout_sha256': item['stdout']['sha256'],
        'stderr_sha256': item['stderr']['sha256'],
    }
    if 'report' in item:
        result['report'] = item['report']
    if 'tests_ran' in item:
        result['tests_ran'] = item['tests_ran']
        result['tests_ok'] = item['tests_ok']
    return result

required_labels = [
    'review-tests17',
    'review-cli-default',
    'review-cli-full',
    'review-cli-reference',
    'review-cli-reference-missing',
    'review-taskbook-cwd-default',
    'case-weights-tamper',
    'case-weights-missing',
    'case-deep-json-v2',
    'case-duplicate-key-v2',
    'case-joint-drift',
]

receipt = {
    'schema': 1,
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'task_id': 'DEEPEYE-IMPLEMENTATION-20261014',
    'task_version': 1,
    'work_id': 'A-R01-CHECKER-REVIEW-20261020-v1',
    'main_thread_id': '01a13d7e-dcf1-7272-a738-a637dd62ff9d',
    'main_generation': 2,
    'original_child_job': {
        'job_id': 'child-fc8960d8c9a64b959c5f06e1be252bba',
        'instance_id': 'deepseek-a-29',
        'route': 'deepseek',
        'ownership': '.planning/deepeye-resume-20261018/r01-checker-review',
    },
    'review_scope': {
        'kind': 'bounded offline read-only software review',
        'writable_root': str(HERE),
        'product_write_authority': False,
        'git_commit_or_push': False,
        'peer_or_group_message': False,
        'board_run_hardware_or_service_change': False,
    },
    'verdict': {
        'bounded_scope': 'FAIL',
        'reason': 'assessment_weights substitution and omission both receive reference-only exit 0',
        'blocking_finding_id': 'R01-CHK-01',
        'blocking_finding_severity': 'High',
        'formal_acceptance': False,
        'hardware_enable_eligible': False,
        'R01': 'not_run',
        'formal29': 'not_run',
    },
    'requirements': {
        'canonical_sha256': requirements['canonical_requirements_sha256'],
        'expected_sha256': requirements['expected_requirements_sha256'],
        'match': requirements['matches'],
        'count': requirements['requirements_count'],
        'ids': requirements['requirement_ids'],
        'product_and_root_scope_identical': requirements['scope_files_identical'],
    },
    'candidate': {
        'manifest_sha256': inventory['candidate_manifest']['sha256'],
        'requested_manifest_sha256': inventory['candidate_manifest']['expected_sha256'],
        'manifest_match': inventory['candidate_manifest']['matches'],
        'base_head': inventory['candidate_base_head'],
        'product_head_observed': inventory['product_head']['stdout'].strip(),
        'source_count': inventory['candidate_source_count'],
        'all_source_pins_match': all(item['matches'] for item in inventory['sources']),
        'all_sources_absent_in_base': all(item['absent_in_base'] for item in inventory['sources']),
        'all_sources_untracked': all(item['worktree_status']['stdout'].startswith('??') for item in inventory['sources']),
        'input_pin_count': inventory['input_pin_count'],
        'all_input_pins_match': all(item['matches'] for item in inventory['input_pins']),
        'evidence_pin_count': inventory['evidence_file_count'],
        'all_evidence_pins_match': all(item['matches'] for item in inventory['evidence_files']),
        'source_files': {item['relative_path']: item['sha256'] for item in inventory['sources']},
    },
    'imports': {
        'checker_loaded_file': provenance['checker_module']['loaded_file'],
        'checker_sha256': provenance['checker_module']['sha256'],
        'test_loaded_file': provenance['test_module']['loaded_file'],
        'test_sha256': provenance['test_module']['sha256'],
        'test_method_count': provenance['test_method_count'],
        'python_executable': provenance['python_executable'],
        'python_version': provenance['python_version'],
        'checker_dependencies': inventory['checker_imports'],
        'test_dependencies': inventory['test_imports'],
    },
    'commands': {
        'required_reproduction': [command_record(label) for label in required_labels],
        'additional_corrected_preserved_runs': [command_record(label) for label in ('case-deep-json', 'case-duplicate-key')],
        'run_count': runs_summary['run_count'],
        'run_summary_path': str(HERE / 'runs-summary.json'),
    },
    'checks': {
        'tests17_exit0': by_label['review-tests17']['returncode'] == 0
            and by_label['review-tests17']['tests_ran'] == 17
            and by_label['review-tests17']['tests_ok'] is True,
        'default_full_exit2_blocked': by_label['review-cli-default']['returncode'] == 2
            and by_label['review-cli-default']['report']['status'] == 'blocked',
        'explicit_pdf_full_exit2_blocked': by_label['review-cli-full']['returncode'] == 2
            and by_label['review-cli-full']['report']['status'] == 'blocked',
        'reference_only_exact_pdf_exit0': by_label['review-cli-reference']['returncode'] == 0
            and by_label['review-cli-reference']['report']['status'] == 'reference_checks_passed',
        'reference_only_missing_pdf_exit2': by_label['review-cli-reference-missing']['returncode'] == 2,
        'taskbook_cwd_default_exit2': by_label['review-taskbook-cwd-default']['returncode'] == 2,
        'weight_substitution_falsely_accepted': by_label['case-weights-tamper']['returncode'] == 0
            and by_label['case-weights-tamper']['report']['status'] == 'reference_checks_passed',
        'missing_weights_falsely_accepted': by_label['case-weights-missing']['returncode'] == 0
            and by_label['case-weights-missing']['report']['status'] == 'reference_checks_passed',
        'deep_json_rejected': by_label['case-deep-json-v2']['returncode'] == 1,
        'duplicate_key_rejected': by_label['case-duplicate-key-v2']['returncode'] == 1,
        'joint_drift_rejected': by_label['case-joint-drift']['returncode'] == 1,
        'all_reports_kept_formal_and_hardware_false': all(
            item.get('report', {}).get('formal_acceptance') is False
            and item.get('report', {}).get('hardware_enable_eligible') is False
            and item.get('report', {}).get('R01') == 'not_run'
            for item in runs_summary['runs'] if 'report' in item
        ),
    },
    'product_write_check': {
        'all_source_input_evidence_bytes_unchanged_before_after': pin_comparison['all_pinned_bytes_unchanged'],
        'product_head_before': pin_comparison['product_head']['before'],
        'product_head_after': pin_comparison['product_head']['after'],
        'unrelated_concurrent_head_change_observed_since_first_manual_read': (
            '889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1'
            ' -> ' + pin_comparison['product_head']['after']
        ),
        'review_created_pycache': False,
        'product_tools_or_tests_pycache_created': False,
    },
    'failed_attempts': failed,
    'limits': [
        'No formal R01 acceptance, formal29 completion, registration, qualification, ROCm, physical-task, hardware, board, or system claim.',
        'No semantic current-organizer PDF review; only exact pinned bytes and fixed prior mapping consistency.',
        'No G02 or unrelated moving worktree content inspected or modified.',
        'The production gate remains unavailable and was not turned on.',
    ],
    'artifacts': {
        'findings.md': artifact('findings.md'),
        'inspection_manifest.json': artifact('inspection_manifest.json'),
        'runs-summary.json': artifact('runs-summary.json'),
        'inventory-before.json': artifact('inventory-before.json'),
        'inventory-after.json': artifact('inventory-after.json'),
        'pin-comparison.json': artifact('pin-comparison.json'),
        'provenance-check.json': artifact('provenance-check.json'),
        'requirements-check.json': artifact('requirements-check.json'),
        'static-audit.json': artifact('static-audit.json'),
        'failed-attempts.json': artifact('failed-attempts.json'),
    },
}
output = HERE / 'receipt.json'
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'verdict': receipt['verdict']['bounded_scope'],
    'tests17_exit0': receipt['checks']['tests17_exit0'],
    'all_pins_unchanged': receipt['product_write_check']['all_source_input_evidence_bytes_unchanged_before_after'],
    'findings_sha256': receipt['artifacts']['findings.md']['sha256'],
    'inspection_manifest_sha256': receipt['artifacts']['inspection_manifest.json']['sha256'],
}, ensure_ascii=False))
