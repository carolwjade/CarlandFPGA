import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
C_TREE = Path('C:/Users/CarlJade/.codex/worktrees/deepeye-c-pr25-review/FPGA多机协作开发')
GIT = Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'

def item(path):
    raw = path.read_bytes()
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

root_inputs = [
    'AGENTS.md', '.agents/skills/fpga-multi-node/SKILL.md', '.agents/skills/fpga-multi-node/skill-role.json',
    '.agents/skills/fpga-multi-node/references/protocol.md',
    '.planning/deepeye-desktop-handoff-20261015/transfer.json',
    'docs/competition/deepeye-2026/immutable_scope.md', 'docs/competition/deepeye-2026/immutable_scope.json',
    'docs/competition/deepeye-2026/taskbook_final.md', 'docs/competition/deepeye-2026/execution_plan_final.json',
    '.planning/deepeye-resume-20261018/actor-progress-design-assignment.md',
    '.planning/deepeye-resume-20261018/actor-composition-main-selection.json',
    '.planning/deepeye-resume-20261018/actor-composition-review/findings.md',
    '.planning/deepeye-resume-20261018/actor-composition-review/progress-final-fence-gap.json',
    '.planning/deepeye-resume-20261018/actor-composition-review/composition_counterexamples.py',
    '.planning/deepeye-resume-20261018/actor-composition-review/progress-gap.result.json',
    '.planning/deepeye-resume-20261018/actor-composition-review/progress-gap.stderr.log',
    '.planning/deepeye-resume-20261018/actor-composition-review/manifest.json',
    '.planning/deepeye-resume-20261018/actor-composition-review/receipt.json',
    '.planning/deepeye-resume-20261018/actor-composition-review/native_complete.json',
    '.planning/deepeye-resume-20261018/actor-composition-design/design.md',
    '.planning/deepeye-resume-20261018/actor-composition-implementation/source-manifest.json',
    '.planning/deepeye-resume-20261018/c-adapter-review/report.md',
]
product_inputs = ['competition/deepeye/' + rel for rel in [
    'simulation/authority/actor_composition.py', 'tests/simulation/test_actor_composition.py',
    'docs/actor_composition.md', 'simulation/authority/pc_direct_runtime.py',
    'simulation/authority/motion_executor.py', 'simulation/isolation/actor_owner.py',
    'simulation/isolation/actor_lifetime.py', 'integration/host_envelope.py',
    'integration/pc_direct_watchdog.py', 'integration/clock_bounds.py', 'integration/sensor_source.py',
    'docs/host_contract.json', 'docs/host_timing_contract.md', 'docs/enums.json', 'docs/interface.json',
    'ai_pc/host_timing/reference.py',
]]
c_inputs = ['competition/deepeye/ai_pc/' + rel for rel in [
    'control_broker/motion_request.py', 'control_broker/mailbox.py', 'control_broker/deadlines.py',
    'model/causal_input.py', 'model/curve_input.py', 'planning/candidate_graph.py']]

scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert hashlib.sha256(canonical).hexdigest() == PIN
transfer = json.loads((ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
assert transfer['status'] == 'active' and transfer['director_generation'] == 2
assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
assert item(ROOT / '.planning/deepeye-resume-20261018/actor-composition-main-selection.json')['sha256'] == '68d826276c8eb4ebdb8ddcb61f8158619b5aa179c57fe904119807e110ade67f'
selected = json.loads((ROOT / '.planning/deepeye-resume-20261018/actor-composition-main-selection.json').read_bytes())
for rel, expected in selected['sources'].items(): assert item(PRODUCT / rel)['sha256'] == expected
inputs = {'root/' + p: item(ROOT / p) for p in root_inputs}
inputs.update({'product/' + p: item(PRODUCT / p) for p in product_inputs})
inputs.update({'C-local-reference/' + p: item(C_TREE / p) for p in c_inputs})
anchors = {}
for base, paths, prefix in [(PRODUCT, product_inputs, 'product/'), (C_TREE, c_inputs, 'C-local-reference/')]:
    for rel in paths:
        if rel.endswith('.py'):
            tree = ast.parse((base / rel).read_bytes())
            anchors[prefix + rel] = {n.name: n.lineno for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
heads = {name: subprocess.check_output([str(GIT), '-C', str(base), 'rev-parse', 'HEAD'], text=True).strip()
         for name, base in [('product', PRODUCT), ('C-local-reference', C_TREE)]}
result = dict(job_id='child-9b77838d22574ae49550293f0b1d61c3', agent_id='/root/worker_results_review_20261018',
    requirements_sha256=PIN, inputs=inputs, source_anchors=anchors, observed_heads=heads,
    source_identity='raw checkout bytes; C local head is a schema/reference read, not fresh remote readback or adoption',
    product_ai_pc_files=[str(p.relative_to(PRODUCT)).replace('\\', '/') for p in (PRODUCT / 'competition/deepeye/ai_pc').rglob('*.py')
                         if '__pycache__' not in p.parts],
    actions='read-only source/evidence/hash inspection; no product imports, tests, IPC, native, network or interpreter operations')
target = HERE / 'input-manifest.json'
if target.exists():
    old = json.loads(target.read_bytes())
    changes = [p for p in old['inputs'] if old['inputs'][p] != inputs[p]]
    (HERE / 'input-recheck.json').write_text(json.dumps(dict(inputs_unchanged=not changes, changed=changes, observed_heads=heads), indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(inputs_unchanged=not changes, changed=changes)))
    assert not changes
else:
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(inputs=len(inputs), requirements_sha256=PIN, observed_heads=heads)))
