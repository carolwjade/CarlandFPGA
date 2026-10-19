import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
MAIN = ROOT / '.planning/deepeye-resume-20261018/r01-checker-main'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path, role):
    path = Path(path)
    return {
        'role': role,
        'path': str(path),
        'exists': path.is_file(),
        'bytes': path.stat().st_size if path.is_file() else None,
        'sha256': sha256(path) if path.is_file() else None,
    }


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


identity = {
    'task_id': 'DEEPEYE-IMPLEMENTATION-20261014',
    'task_version': 1,
    'work_id': 'A-R01-CHECKER-REVIEW-20261020-v1',
    'child_job_id': 'child-fc8960d8c9a64b959c5f06e1be252bba',
    'instance_id': 'deepseek-a-29',
    'route': 'deepseek',
    'main_thread_id': '01a13d7e-dcf1-7272-a738-a637dd62ff9d',
    'main_generation': 2,
    'ownership': '.planning/deepeye-resume-20261018/r01-checker-review',
}

references = [
    record(ROOT / '.agents/skills/fpga-multi-node/SKILL.md', 'mandatory project skill'),
    record(ROOT / '.agents/skills/fpga-multi-node/skill-role.json', 'A host role'),
    record(ROOT / '.agents/skills/fpga-multi-node/references/protocol.md', 'collaboration protocol'),
    record(ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json', 'main transfer identity'),
    record(ROOT / 'docs/competition/deepeye-2026/immutable_scope.md', 'human immutable contract text'),
    record(ROOT / 'docs/competition/deepeye-2026/immutable_scope.json', 'human immutable contract source'),
    record(ROOT / 'docs/competition/deepeye-2026/taskbook_final.md', 'taskbook including R01'),
    record(ROOT / 'docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf', 'exact pinned PDF bytes used by CLI'),
    record(MAIN / 'candidate-manifest.json', 'candidate manifest'),
    record(MAIN / 'plan.md', 'selected bounded implementation design'),
    record(PRODUCT / 'competition/deepeye/tools/check_rules.py', 'product checker under review'),
    record(PRODUCT / 'competition/deepeye/tests/test_check_rules.py', 'product tests under review'),
    record(PRODUCT / 'competition/deepeye/docs/rules_verification.md', 'product checker documentation'),
    record(PRODUCT / 'competition/deepeye/docs/rules.json', 'frozen rules input'),
    record(PRODUCT / 'competition/deepeye/docs/requirements_trace.csv', 'frozen trace input'),
    record(HERE / 'assignment.md', 'original assignment'),
    record(HERE / 'dispatch-result.json', 'original queued dispatch record'),
    record(HERE / 'dispatch-started.json', 'original dispatch payload'),
]

artifact_names = [
    'findings.md',
    'inventory-before.json',
    'inventory-after.json',
    'pin-comparison.json',
    'provenance-check.json',
    'requirements-check.json',
    'static-audit.json',
    'runs-summary.json',
    'failed-attempts.json',
    'run_capture.py',
    'inventory.py',
    'compare_pins.py',
    'provenance_check.py',
    'requirements_check.py',
    'static_audit.py',
    'summarize_runs.py',
    'make_failed_attempts.py',
    'prepare_cases.py',
    'prepare_structural_cases.py',
    'build_inspection_manifest.py',
    'build_receipt.py',
]
artifacts = [record(HERE / name, 'review artifact') for name in artifact_names]

runs = []
for path in sorted((HERE / 'runs').iterdir()):
    if path.is_file():
        runs.append(record(path, 'command raw evidence'))

inventory = load('inventory-after.json')
provenance = load('provenance-check.json')
requirements = load('requirements-check.json')
pin_comparison = load('pin-comparison.json')
static_audit = load('static-audit.json')
runs_summary = load('runs-summary.json')
failed_attempts = load('failed-attempts.json')

manifest = {
    'schema': 1,
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'identity': identity,
    'scope': {
        'kind': 'independent read-only bounded software review',
        'writable': str(HERE),
        'product_write_authority': False,
        'git_commit_or_push': False,
        'peer_or_group_message': False,
        'board_run_hardware_or_service_change': False,
        'formal_acceptance': False,
        'R01': 'not_run',
        'formal29': 'not_run',
    },
    'python': {
        'executable': provenance['python_executable'],
        'version': provenance['python_version'],
        'executable_sha256': sha256(Path(provenance['python_executable'])),
        'flags': ['-B'],
        'environment': ['PYTHONDONTWRITEBYTECODE=1', 'PYTHONIOENCODING=utf-8', 'process-scoped PYTHONPATH=.local/deepeye-host-deps'],
    },
    'candidate': {
        'requested_manifest_sha256': '85a6db6ee4f839685a47770590fcbca6683862927318d94d05f749fad3b3c8cd',
        'base_head': inventory['candidate_base_head'],
        'product_head_at_inventory': inventory['product_head']['stdout'].strip(),
        'source_count': inventory['candidate_source_count'],
        'source_files': inventory['sources'],
        'input_count': inventory['input_pin_count'],
        'input_files': inventory['input_pins'],
        'evidence_count': inventory['evidence_file_count'],
        'evidence_files': inventory['evidence_files'],
        'all_source_and_input_and_evidence_matches': all((
            all(item['matches'] for item in inventory['sources']),
            all(item['matches'] for item in inventory['input_pins']),
            all(item['matches'] for item in inventory['evidence_files']),
        )),
    },
    'immutable_requirements': {
        'contract_id': requirements['contract_id'],
        'revision': requirements['revision'],
        'ids': requirements['requirement_ids'],
        'canonical_sha256': requirements['canonical_requirements_sha256'],
        'expected_sha256': requirements['expected_requirements_sha256'],
        'match': requirements['matches'],
        'product_and_root_scope_identical': requirements['scope_files_identical'],
    },
    'import_origins': {
        'checker_loaded_file': provenance['checker_module']['loaded_file'],
        'checker_sha256': provenance['checker_module']['sha256'],
        'test_loaded_file': provenance['test_module']['loaded_file'],
        'test_sha256': provenance['test_module']['sha256'],
        'test_method_count': provenance['test_method_count'],
        'test_methods': provenance['test_methods'],
        'checker_static_imports': inventory['checker_imports'],
        'test_static_imports': inventory['test_imports'],
        'external_or_host_dependency_modules_imported_by_checker': [],
        'host_dependency_path_resolved_for_scoping_only': str(ROOT / '.local/deepeye-host-deps'),
    },
    'static_audit': static_audit,
    'runs': {
        'count': runs_summary['run_count'],
        'summary_path': str(HERE / 'runs-summary.json'),
        'details': runs_summary['runs'],
        'raw_files': runs,
    },
    'failed_attempts': failed_attempts,
    'before_after_pins': pin_comparison,
    'references': references,
    'review_artifacts': artifacts,
    'limits': [
        'No formal R01, formal29, registration, qualification, ROCm, physical-task, hardware, or board acceptance.',
        'No fresh semantic PDF interpretation; only exact bytes and the previously reviewed fixed mapping consistency.',
        'A bounded software review found one false reference-pass defect; it does not authorize opening the unavailable production gate.',
        'Unrelated moving G02 and other active worktree files were not inspected or modified.',
    ],
}
output = HERE / 'inspection_manifest.json'
output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'reference_count': len(references),
    'run_count': len(runs),
    'artifact_count': len(artifacts),
    'candidate_pins_match': manifest['candidate']['all_source_and_input_and_evidence_matches'],
    'requirements_match': manifest['immutable_requirements']['match'],
    'before_after_unchanged': pin_comparison['all_pinned_bytes_unchanged'],
}, ensure_ascii=False))
