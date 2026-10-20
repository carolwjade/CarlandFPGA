"""Recheck original inputs, exact proposed replacements and retained test trees."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PRODUCT = ROOT / '.local/deepeye-implementation-a/competition/deepeye'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def save(name, value):
    with (D / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

pins = load(D / 'input-pins.json')
for name, record in pins['files'].items():
    p = Path(name)
    assert p.stat().st_size == record['bytes'] and sha(p) == record['sha256']
review = D.parent / 'r03-mailbox-independent-20261020'
assert sha(review / 'artifact-manifest.json') == pins['review_manifest_sha256']
for name, record in load(review / 'artifact-manifest.json')['files'].items():
    p = review / name
    assert p.stat().st_size == record['bytes'] and sha(p) == record['sha256']
original = (PRODUCT / 'integration/candidate_mailbox.py').read_bytes()
replacement = (D / 'proposed/candidate_mailbox.py').read_bytes()
assert replacement == original.replace(b"    def stop(self, reason='stop'):\n", b"    @_entry\n    def stop(self, reason='stop'):\n")
assert len(replacement) == len(original) + len(b'    @_entry\n')
assert sha(D / 'proposed/candidate_mailbox.py') == '5ca4aafb97f88b3080cc918e38f6c27a462f4caa7af5fa436eeb663f91d3f1d5'
assert sha(D / 'proposed/test_candidate_mailbox.py') == '7ff79841abbd6aac12b017a486d296ce58335424471379cfb8af2b020aec9f82'
rows = []
for label, exit_code, failures, errors in [('red-01', 1, 6, 0), ('green-01', 1, 0, 3), ('red-02', 1, 6, 0), ('green-02', 0, 0, 0)]:
    r = D / label
    checks, terminal, started = load(r / 'checks.json'), load(r / 'terminal.json'), load(r / 'started.json')
    assert checks['tests_run'] == 30 and len(checks['failures']) == failures and len(checks['errors']) == errors
    assert not checks['skipped'] and not checks['prohibited_attempts']
    assert terminal['exit_code'] == exit_code and terminal['all_processes_terminated'] and terminal['active_processes_final'] == 0
    assert terminal['stop_reason'] is None and all(m['signaled'] and m['wait_result'] == 0 for m in terminal['held_members'])
    assert started['private_job'] and started['assigned_before_resume'] and started['hidden'] and started['priority'] == 'below_normal'
    for name in ('candidate_mailbox.py', 'test_candidate_mailbox.py'):
        assert sha(r / name) == checks['source_snapshots'][name]
    for stream in ('stdout', 'stderr'):
        assert sha(r / (stream + '.txt')) == terminal['logs'][stream]['sha256']
    assert len(checks['stop_binding_traces']) == 6
    stopped = label.startswith('green')
    for trace in checks['stop_binding_traces']:
        assert trace['snapshot_after_call']['stopped'] == stopped
        assert trace['candidate_consumed_after_call'] == (None if stopped else 1)
    rows.append({'run': label, 'exit_code': exit_code, 'tests': checks['tests_run'], 'failure_subcases': failures, 'errors': errors, 'seconds': terminal['seconds'], 'source_snapshots': checks['source_snapshots'], 'held_member_count': len(terminal['held_members']), 'all_held_signaled_and_job_empty': True})
assert (D / 'red-02/test_candidate_mailbox.py').read_bytes() == (D / 'green-02/test_candidate_mailbox.py').read_bytes() == (D / 'proposed/test_candidate_mailbox.py').read_bytes()
assert (D / 'green-02/candidate_mailbox.py').read_bytes() == replacement

# Retain exact initial harness version recovered from the one allowlist edit.
# Compare against the self module hash captured at each original execution.
for filename in ('test_worker.py',):
    current = (D / filename).read_bytes()
    old = current.replace(b"('red-01', 'green-01', 'red-02', 'green-02')", b"('red-01', 'green-01')")
    expected = load(D / 'red-01/checks.json')['module_file_hashes'][str(D / filename)]
    assert hashlib.sha256(old).hexdigest() == expected
    assert expected == load(D / 'green-01/checks.json')['module_file_hashes'][str(D / filename)]
    with (D / 'initial-test-worker-byte-reconstruction.py').open('xb') as f:
        f.write(old)

result = {'work_id': 'A-R03-MAILBOX-STOP-FIX-20261020-v1', 'job_id': 'child-4126792ead044c7da100414b353266f8', 'agent_id': '/root/r02_static_dependency_review_20261020', 'implementation_delta': 'One @_entry decorator above stop; no body or lifecycle/clock/slot change', 'original_module_sha256': pins['original_module_sha256'], 'proposed_module_sha256': sha(D / 'proposed/candidate_mailbox.py'), 'original_test_sha256': pins['original_test_sha256'], 'proposed_test_sha256': sha(D / 'proposed/test_candidate_mailbox.py'), 'vector_sha256_unchanged': pins['vector_sha256'], 'original_product_inputs_unchanged': len(pins['files']), 'old_review_files_rechecked': 26, 'runs': rows, 'final_tests': 30, 'original_tests_retained': 26, 'new_test_methods': 4, 'malformed_stop_mode_shape_pairs': 6, 'product_modified': False, 'main_application': 'pending independent review and main action', 'R03': 'not_run', 'all29': 'not_run', 'requirements_sha256': pins['requirements_sha256']}
save('result.json', result)
report = f'''# Minimal malformed-STOP replacement proposal

Prepared two exact replacement files in `proposed/`; product remains unchanged.
The implementation adds only `@_entry` immediately above `stop()`. Python binds
the original stop signature inside that existing variadic wrapper, so unexpected
keyword, excess positional arguments and duplicate reason binding now call
`_halt('invalid_stop')` and raise ValueError with original TypeError as cause.
Correct calls retain the original body and reason normalization. No slot,
clock, identity, session-cap, lifecycle-vector or other API policy changed.

| File | Original SHA256 | Proposed SHA256 |
|---|---|---|
| candidate_mailbox.py | {result['original_module_sha256']} | {result['proposed_module_sha256']} |
| test_candidate_mailbox.py | {result['original_test_sha256']} | {result['proposed_test_sha256']} |

Focused diffs are `candidate_mailbox.py.diff` and
`test_candidate_mailbox.py.diff`. Main must apply only the two `proposed/`
files to the corresponding product integration paths after independent review.
The mirror is test support, not another proposed product tree.

Actual test methods: original26 retained plus new4, total30. Three new methods
exercise all three malformed bindings in HIL_PC_FPGA and PC_DIRECT. Each checks
STOP latch, cleared pending/observations, caught ValueError/TypeError cause,
refused210ms consumption, old-session activation rejection, old completion
rejection, and a generation3 fresh-session completion consumed at710ms. The
fourth covers default/positional/keyword valid STOP forms in both modes.
Original12 literal timelines in both modes remain unchanged and run as part
of the original mailbox suite. Only this mailbox suite ran; no245/HIL suite.

| Run | Exit | Test methods | Failed subcases | Errors | Owned-tree seconds |
|---|---:|---:|---:|---:|---:|
'''
for row in rows:
    report += f"| {row['run']} | {row['exit_code']} | 30 | {row['failure_subcases']} | {row['errors']} | {row['seconds']:.3f} |\n"
report += '''
Both RED runs use original module bytes and reproduce six live-after-error
states, each consuming candidate1 after the caught TypeError. Final red-02
and green-02 use the exact same final test hash. Final GREEN has no failures,
errors, skips or prohibited effects. State traces are in each checks.json.

The initial green-01 failure is retained, not relabeled. Its six STOP state
checks passed, but three mode2 fresh-session controls errored because the test
helper retained self.ctx from the first mode and the new test reused literal
session8. `test-fixture-correction.json` records the precise test-only change
to current session+1. Fresh identity, rather than product policy, was corrected.
The final proposed test contains that correction; new-test-methods.txt and
initial-test-proposal.diff retain the initial template/history. A second RED
followed by GREEN establishes the final test's discriminating behavior.

Each worker used the same byte-pinned reviewed win_job/boundary helpers,
suspended assignment before resume, hidden below-normal private Windows job,
30s, four processes, process384MiB/job512MiB, bounded output/tree budgets and
held-member termination verification. Every job ended empty with all three
retained process handles signaled. Receipt commands use the exact existing
venv interpreter with -I -S -B -X utf8. Dependencies/BOOT/schema/wire are real,
loaded from the owned mirror plus the existing pinned import file records;
no mock validator or product module is used as the tested mailbox. The audit
guard is cooperative, not an OS security sandbox; tree quotas are sampled.

All13 original product input files and the26-file independent-review manifest
were rehashed after final execution. Source snapshots and import-file hashes
bind each run. No claims are made about new HEAD-wide testing. Lifecycle vector
SHA256 remains 9759681356a6068b370cda751c51cc5120cda6cfd5b9c901b9c0998c62eed63c.
The reconstructed initial worker script is separately labeled and checked
against the original executions' recorded self hashes; it is not relabeled
as a contemporaneous source snapshot.

This is a proposed local software fix. No product application, Git action,
runtime transport, inference, service, OS configuration, network, board,
driver or GUI/input was performed. Selection remains non-authorizing.
Main owns independent review/application and formal acceptance. R03/all29
remain not_run. H01-H15/generation2 and canonical requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 remain unchanged.
'''
with (D / 'report.md').open('x', encoding='utf-8') as f:
    f.write(report)
text = f"A-R03-MAILBOX-STOP-FIX-20261020-v1 prepared two replacement files only in proposed/. candidate_mailbox.py changes only one @_entry decorator above stop; proposed SHA256 {result['proposed_module_sha256']}. Proposed test SHA256 {result['proposed_test_sha256']}. Final exact-test RED exit1 with six malformed-call failures and no errors; final GREEN exit0 with all30 methods passing (original26 plus4 new), both H12 modes, latch/pending-clear/consume-refusal/old-session-rejection/fresh-session success. Initial RED and green-01 test-fixture session-reuse errors retained; corrected final tests verified RED/GREEN without widening implementation. All13 original product inputs and26 review artifacts unchanged; vector untouched. Four hidden private bounded jobs all empty with held handles signaled. Product/Git/runtime/board/network/UI untouched; R03/all29 not_run; H01-H15 canonical SHA256 {pins['requirements_sha256']} and generation2 unchanged. See report.md, result.json, diffs, run receipts/checks and artifact-manifest.json. Main application and acceptance remain pending independent review."
with (D / 'final-result.txt').open('x', encoding='utf-8') as f:
    f.write(text + '\n')

# Exact credential comparison stays internal; output is filenames/count only.
credential = load(D / 'lease.private.json')['lease_token'].encode()
excluded = {'lease.private.json', 'reserve-request.json', 'artifact-manifest.json', 'seal-result.json', 'native-complete-response.json'}
entries, contaminated = {}, []
for p in sorted(D.rglob('*')):
    assert not p.is_symlink()
    if p.is_file() and p.name not in excluded:
        data = p.read_bytes()
        if credential in data:
            contaminated.append(p.relative_to(D).as_posix())
        entries[p.relative_to(D).as_posix()] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
assert not contaminated, 'Public contamination; content withheld'
save('artifact-manifest.json', {'work_id': result['work_id'], 'job_id': result['job_id'], 'agent_id': result['agent_id'], 'created_utc': datetime.now(timezone.utc).isoformat(), 'files': entries, 'excluded': sorted(excluded), 'requirements_sha256': pins['requirements_sha256'], 'product_modified': False, 'R03': 'not_run', 'all29': 'not_run'})
for name, record in load(D / 'artifact-manifest.json')['files'].items():
    p = D / name
    assert p.stat().st_size == record['bytes'] and sha(p) == record['sha256']
sealed = {'public_files': len(entries), 'manifest_sha256': sha(D / 'artifact-manifest.json'), 'readback_all_entries_match': True, 'token_match_file_count': len(contaminated), 'token_match_filenames': contaminated, 'final_tests': 30, 'product_modified': False}
assert credential not in (D / 'artifact-manifest.json').read_bytes()
save('seal-result.json', sealed)
assert credential not in (D / 'seal-result.json').read_bytes()
print(json.dumps(sealed))
