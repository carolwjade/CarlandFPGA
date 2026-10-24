import ast
import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
CHECKER = PRODUCT / 'competition/deepeye/tools/check_rules.py'
TESTS = PRODUCT / 'competition/deepeye/tests/test_check_rules.py'
RULES = PRODUCT / 'competition/deepeye/docs/rules.json'
PLAN = ROOT / '.planning/deepeye-resume-20261018/r01-checker-main/plan.md'
TASKBOOK = ROOT / 'docs/competition/deepeye-2026/taskbook_final.md'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_hits(path, needle):
    return [
        {'line': number, 'text': text}
        for number, text in enumerate(path.read_text(encoding='utf-8').splitlines(), 1)
        if needle in text
    ]


checker_text = CHECKER.read_text(encoding='utf-8')
tests_text = TESTS.read_text(encoding='utf-8')
tree = ast.parse(checker_text)
imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module)
side_effect_calls = []
reviewed = {'open', 'write_text', 'write_bytes', 'mkdir', 'subprocess.run', 'socket.socket'}
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    if isinstance(node.func, ast.Name) and node.func.id in reviewed:
        side_effect_calls.append({'line': node.lineno, 'name': node.func.id})
    if isinstance(node.func, ast.Attribute) and node.func.attr in reviewed:
        side_effect_calls.append({'line': node.lineno, 'name': node.func.attr})

rules = json.loads(RULES.read_text(encoding='utf-8'))
report = {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hashes': {str(path): sha256(path) for path in (CHECKER, TESTS, RULES, PLAN, TASKBOOK)},
    'checker_assessment_weights_literal_count': checker_text.count('assessment_weights'),
    'tests_assessment_weights_literal_count': tests_text.count('assessment_weights'),
    'rules_assessment_weights': rules.get('assessment_weights'),
    'taskbook_weight_requirement_hits': line_hits(TASKBOOK, '不拿3.3权重代替'),
    'taskbook_track_correction_hits': line_hits(TASKBOOK, '3.3另有学历分组'),
    'plan_weight_requirement_hits': line_hits(PLAN, 'No3.3 weights substitution'),
    'checker_imports': sorted(set(imports)),
    'reviewed_side_effect_calls': side_effect_calls,
    'read_only_open_modes': [
        {'line': number, 'text': text}
        for number, text in enumerate(checker_text.splitlines(), 1)
        if 'path.open(' in text
    ],
}
output = HERE / 'static-audit.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'checker_assessment_weights_literal_count': report['checker_assessment_weights_literal_count'],
    'tests_assessment_weights_literal_count': report['tests_assessment_weights_literal_count'],
    'weight_sum': sum(report['rules_assessment_weights'].values()),
    'reviewed_side_effect_calls': side_effect_calls,
}, ensure_ascii=False))
