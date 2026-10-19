import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PYTHON = ROOT / '.local/venv/Scripts/python.exe'
RUNNER = HERE / 'run_capture.py'
PRODUCT = ROOT / '.local/deepeye-implementation-a'
PDF = ROOT / 'docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf'


def attempt(label, tail):
    command = [
        str(PYTHON), '-B', str(RUNNER), label,
        '--cwd', str(PRODUCT), '--timeout', '60', '--',
        str(PYTHON), '-B', *tail,
    ]
    return {'label': label, 'command': command}


report = {
    'phase': 'initial capture-wrapper invocation before parser correction',
    'returncode': 2,
    'stderr': (
        'usage: run_capture.py [-h] --cwd CWD [--timeout TIMEOUT] label ...\n'
        'run_capture.py: error: the following arguments are required: --cwd\n'
    ),
    'effect': 'No test or checker command launched and no run evidence file was created.',
    'attempts': [
        attempt('review-tests17', [
            '-m', 'unittest',
            'competition.deepeye.tests.test_check_rules.RuleCheckerTests', '-v',
        ]),
        attempt('review-cli-default', ['competition/deepeye/tools/check_rules.py']),
        attempt('review-cli-full', [
            'competition/deepeye/tools/check_rules.py', '--source-pdf', str(PDF),
        ]),
        attempt('review-cli-reference', [
            'competition/deepeye/tools/check_rules.py', '--reference-only',
            '--source-pdf', str(PDF),
        ]),
    ],
    'other_failures': [
        {
            'phase': 'first static audit execution',
            'returncode': 1,
            'error': 'FileNotFoundError: [Errno 2] No such file or directory: rb',
            'cause': 'Review-only audit script called open with rb instead of matching the literal text.',
            'effect': 'No static-audit.json was written; the corrected run is preserved in static-audit.json.',
        },
        {
            'phase': 'first structural counterexample construction',
            'effect': (
                'The generated deep-json and duplicate-key rules files were syntactically malformed, '
                'so their exit-1 runs are preserved as methodology failures rather than parser-depth evidence. '
                'Fresh deep-json-v2 and duplicate-key-v2 cases reach the intended parser paths.'
            ),
            'preserved_runs': ['case-deep-json', 'case-duplicate-key'],
            'corrected_runs': ['case-deep-json-v2', 'case-duplicate-key-v2'],
        },
    ],
}
(HERE / 'failed-attempts.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(HERE / 'failed-attempts.json'), 'attempts': 4}, ensure_ascii=False))
