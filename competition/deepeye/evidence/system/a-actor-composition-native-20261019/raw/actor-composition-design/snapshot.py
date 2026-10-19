import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a'
GIT = Path('C:/Users/CarlJade/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')
PIN = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'

def digest(path):
    raw = path.read_bytes()
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

root_paths = [
    'AGENTS.md', '.agents/skills/fpga-multi-node/SKILL.md',
    '.agents/skills/fpga-multi-node/skill-role.json',
    '.agents/skills/fpga-multi-node/references/protocol.md',
    '.planning/deepeye-desktop-handoff-20261015/transfer.json',
    'docs/competition/deepeye-2026/immutable_scope.md',
    'docs/competition/deepeye-2026/immutable_scope.json',
    'docs/competition/deepeye-2026/taskbook_final.md',
    'docs/competition/deepeye-2026/execution_plan_final.json',
    'docs/competition/deepeye-2026/simulation_contract_final.json',
    '.planning/deepeye-resume-20261018/actor-composition-design-assignment.md',
    '.planning/deepeye-resume-20261018/ai-lifetime-design/design.md',
    '.planning/deepeye-resume-20261018/actor-and-r02-main-selection.json',
    '.planning/deepeye-resume-20261018/bridge-and-actor-main-selection.json',
    '.planning/deepeye-resume-20261018/actor-owner-review/findings.md',
    '.planning/deepeye-resume-20261018/actor-owner-review/provider_detached_integration_gap.witness.json',
    '.planning/deepeye-resume-20261018/actor-binding-repair/source-manifest.json',
    '.planning/deepeye-resume-20261018/actor-binding-repair/receipt.json',
    '.planning/deepeye-resume-20261018/actor-binding-repair/native_completion.json',
]
product_paths = ['AGENTS.md'] + ['competition/deepeye/' + p for p in [
    'simulation/isolation/actor_owner.py', 'simulation/isolation/actor_lifetime.py',
    'simulation/isolation/windows_cleanup.py', 'simulation/isolation/owned_resources.py',
    'simulation/isolation/win32.py', 'simulation/isolation/prototype.py',
    'simulation/authority/pc_direct_runtime.py', 'simulation/authority/motion_executor.py',
    'simulation/sensors/forward_profile.py', 'integration/host_envelope.py',
    'integration/pc_direct_watchdog.py', 'integration/boot_profile.py',
    'integration/clock_bounds.py', 'integration/sensor_source.py',
    'ai_pc/host_timing/reference.py', 'simulator/viewer/main.gd',
    'simulator/editor/scene_document.gd', 'simulator/viewer/project.godot',
    'docs/actor_lifetime.md', 'docs/actor_native_probe.md',
    'docs/runtime_checkpoint_20261019.md', 'docs/host_contract.json',
    'docs/host_timing_contract.md', 'docs/boot_profiles.json',
    'docs/pc_direct_runtime.md', 'docs/motion_executor.md',
    'docs/process_isolation_prototype.md',
]] + ['docs/superpowers/specs/2026-10-19-trusted-motion-executor-design.md']
# project.godot is resolved from the actual checked-in viewer location, never guessed.
product_paths = [p for p in product_paths if not p.endswith('project.godot')]
scope = json.loads((ROOT / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
canonical = json.dumps(scope['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert hashlib.sha256(canonical).hexdigest() == PIN
transfer = json.loads((ROOT / '.planning/deepeye-desktop-handoff-20261015/transfer.json').read_bytes())
assert transfer['status'] == 'active' and transfer['director_generation'] == 2
assert transfer['new_director_thread_id'] == '01a13d7e-dcf1-7272-a738-a637dd62ff9d'
inputs = {'root/' + p: digest(ROOT / p) for p in root_paths}
inputs.update({'product/' + p: digest(PRODUCT / p) for p in product_paths})
plan = json.loads((ROOT / 'docs/competition/deepeye-2026/execution_plan_final.json').read_bytes())
selected = {k: plan['tasks'][k] for k in ['C02', 'C03', 'C04', 'C05', 'G03', 'G04', 'G05', 'G06', 'G07']}
anchors = {}
for rel in product_paths:
    if not rel.endswith('.py'):
        continue
    tree = ast.parse((PRODUCT / rel).read_bytes())
    anchors[rel] = {n.name: n.lineno for n in ast.walk(tree)
                    if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
result = dict(schema=1, job_id='child-37334357eaea4e4a91639bad35a47e67',
              agent_id='/root/worker_results_review_20261018',
              requirements_sha256=PIN, source_bytes='raw checkout bytes, not claimed Git blobs',
              product_head=subprocess.check_output([str(GIT), '-C', str(PRODUCT), 'rev-parse', 'HEAD'], text=True).strip(),
              inputs=inputs, selected_task_dependencies=selected, source_anchors=anchors,
              performed='read-only source/design inspection; no product imports, tests, native or network')
target = HERE / 'input-manifest.json'
if target.exists():
    old = json.loads(target.read_bytes())
    changes = [p for p, v in old['inputs'].items() if inputs[p] != v]
    (HERE / 'input-recheck.json').write_text(json.dumps(dict(inputs_unchanged=not changes, changed=changes,
        observed_head=result['product_head']), indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(inputs_unchanged=not changes, changed=changes)))
    assert not changes
else:
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(inputs=len(inputs), requirements_sha256=PIN, product_head=result['product_head'], dependencies=selected)))
