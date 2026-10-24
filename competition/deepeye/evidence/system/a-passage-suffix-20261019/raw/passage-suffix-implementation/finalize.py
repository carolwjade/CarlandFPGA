import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRODUCT=ROOT/'.local/deepeye-implementation-a'


def digest(path):
    raw=path.read_bytes()
    return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def save(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


sources=load('source-manifest.json')
for relative,expected in sources.items():
    assert digest(PRODUCT/relative)==digest(HERE/'frozen'/relative)==expected
after=load('dependencies-after.json')
for relative,expected in after['unchanged'].items():assert digest(PRODUCT/relative)==expected
for relative,expected in after['old_design_evidence_unchanged'].items():assert digest(ROOT/relative)==expected
assert all(row['equal'] and row['utf8_lf'] for row in load('git-clean-verification.json'))
assert load('green-release.json')['exit_code']==0
assert load('red-corrected.json')['exit_code']==1
assert load('red-duration.json')['exit_code']==1
table='\n'.join(f'| `{name}` | {v["size"]} | `{v["sha256"]}` |' for name,v in sources.items())
report=f'''# Complete-original-dt strict-red suffix implementation

Implemented the selected option A as a four-file numerical candidate, ready for
main's independent review. The reducer now checks remaining original slices after
the first full-body arrival proof; it never commits an arrival prefix. No runtime
or actual executor implementation was modified.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work
`A-passage-suffix-implementation-20261019-v1`; original job
`child-c3c3785d01fc40dea9cde699a48641cd`; canonical agent
`/root/worker_results_review_20261018`. Original-endpoint native validation allowed
execution. A Desktop director generation2 remains sole main. Selected design SHA256
`2e0b5eaa18f6e1197befc5fd1e76513f3e54b0199823827e2fb6994777800596` and base HEAD
`b19a528344d8675fedb41f37e7de23f1112f1871` were verified. H01–H15 and
`DEEPEYE-HUMAN-LOCK-20261014/revision1` remain fixed at canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.

## Bounded implementation and conservative results

After this preview's first full-body ARRIVED, each remaining slice still calls the
unchanged six-face checker with role `exit`. It must be SAFE and contain exactly
six distinct faces: red STRICT_OUTSIDE_ACTIVE, other five STRICT_INSIDE. Every
proof is retained in order. A SAFE/APERTURE-only suffix or missing/non-strict face
proof returns UNKNOWN with the original state/history. A suffix's actual UNKNOWN
or VIOLATION_PROVED is preserved; unknown outer-envelope clearance is not relabeled
as proved contact. Only the first arrival window appends ARRIVED.

The candidate comes from the original plan.end with one revision, complete
original duration and unchanged end error/speed-error carry. Newly composed
suffix traces carry private tag `strict-red-outside-suffix-v1`; workspace VERSION,
geometry methods, rho, path integration, wire/host schemas and actual fence/CAS
remain unchanged. The original max_slices check still runs before any advance.

A further boundary regression established that the new branch could otherwise
accept a direct preview clipped by the original deadline from10,000,000ns to
9,999,999ns. The new suffix composition now requires covered_ns equal the original
requested duration; it returns UNKNOWN on that clipped plan. CP's D-1 deadline law
and all old single-slice/entry behavior were left intact. This guard is conservative
and introduces no timestep extension, event-time root finding or new integration.

The real numerical executor still checks every initial/full solid sweep and then
its final fence/CAS. A last-slice water/rock obstacle prevents the whole step. No
safe prefix, extra grant, duplicate authority, or post-fence geometric work exists.

## Actual TDD and regression evidence

Exact argv/cwd/process-local environment, exit codes and tested four-file hashes
are in each red/green JSON. Untouched subprocess bytes are saved as `.stdout.bin`
and `.stderr.bin`; readable `.log` companions explicitly normalize CRLF to LF.
They are separate from raw evidence. The first RED encountered a missing jsonschema
import in the launcher test environment; it is preserved as setup evidence.
The corrected driver uses existing ROOT `.local/deepeye-host-deps` via process-only
PYTHONPATH, without an install or configuration change.

| Run | Actual result |
| --- | --- |
| Initial RED with missing dependency | 17 discovered, 10 failures plus1 import/setup error, exit1 |
| Corrected original-behavior RED | 43 tests, 12 failures plus5 expected positive-path PreparationRejected errors, exit1 |
| First GREEN | 251 tests passed, exit0 |
| Added rotated-other-face suffix boundary | 252 tests passed, exit0 |
| Complete-original-dt clipping RED | 45 affected tests, 1 genuine failure, exit1 |
| Final GREEN, all affected/unchanged requested suites | **253 tests passed, no skips, exit0** |

Final command runs passage_phase, motion_executor, workspace_boundaries,
solid_clearance, pc_direct_runtime, certified_path, gate_clearance, gate_geometry
and kinematics. No workspace or solid verdict was mocked. Existing TM-R1 tests use
their explicit materialization faults; they still revoke future motion while
preserving committed history, including a caught callback fault. No source or test
outside the four assigned product files was edited.

Meaningful observations (all are explicit internal numerical seeds, not a complete
preceding route or source/BOOT/AI authentication):

- Exit seeds z=-15.519/-15.5199 with yaw7000 now have two ordered certificates over
  0/7,142,857/10,000,000ns, one ARRIVED window and the full original end pose/errors.
  Real executor tests commit exactly one final callback and one root publication,
  map only the new event window to the actual supplied fence, and hold a later
  ARRIVED step. STOP, world invalidation and exact deadline equality still veto.
- z=-15.5184 retains UNKNOWN despite a SAFE suffix because red uses APERTURE only.
  Single-slice arrival and the multi-slice entry seed14.481 stay supported; entry
  seed14.4815 retains its blue-to-exit-role UNKNOWN margin gap.
- All six red-face orientations pass the symmetric strict suffix. Same-face gates
  use the correct red aperture; blue cannot substitute. Tip-only/center-only exits
  remain EXIT_CROSSING. Wrong direction/face, rim grazing, rotation and exact-fixture
  rim contact retain their existing conservative/violation classifications.
- A near-edge rotated fixture proves full red exit in the first SAFE slice, then
  gets ENVELOPE_NOT_CLEAR/UNKNOWN at the right face in the suffix. It returns the
  original state and does not publish the local ARRIVED event.
- The thin box at z=-16.0414 is CLEAR for the first real solid sweep, while its
  centre lies inside the final nominal cap sphere. The actual final-slice solid
  check returns water UNKNOWN or hard-rock DRILLING_REQUIRED with checked_slices2;
  no fence callback or pose publication occurs. This is a real numerical solid
  fixture, not a mocked result or proof about an unverified B mesh.
- Slice budget0/1, original timing, event identity and accumulated numeric/error
  bounds remain enforced. No new arbitrary event split or adaptive subdivision
  was introduced. `numerical-traces.json` preserves full six diagnostic previews,
  private proofs, context, events, intervals and candidate seals.

The old T12 z=-15.519 expectation is retained in before snapshots/history; its
newly provable case is now a positive. The continuing negative uses z=-15.5184.
No old diagnostic logs or formal run records were rewritten.

## Frozen source and byte integrity

| Product path | Bytes | SHA256 |
| --- | ---: | --- |
{table}

All four final files decode as UTF-8 without BOM or CR bytes, and read-only Git
hash-object checks prove raw blob OID equals the path's Git-clean blob OID.
`git-clean-verification.json` records exact commands and both OIDs; no index,
staging, commit or push command was issued. Frozen copies match tested raw bytes.
`source.diff` records the narrow patch from base snapshots.

All **41** recorded unowned dependency files and **16** old design-evidence files
remain byte-for-byte unchanged. This includes the actual executor, workspace/CP/
gate/solid/runtime source, their unchanged regressions, scope and inherited
attributes. Unrelated inherited C-owned bytes were not edited. Exact comparisons
are retained in dependencies-after.json; this is not a whole-product clean-tree
claim. HEAD observed at freeze remains the assigned b19a528 base.

## Remaining dependency and acceptance boundary

Next: main assigns independent exact-byte review, including full-dt proof coverage,
all six suffix certificates, true final-slice solid rejection and final fence/CAS
behavior. General APERTURE tails, blue role-switch refinement, exact crossing-time
localization, all36 complete directed face-pair routes and full same-face U-routes
remain separate work. No new mathematical gap beyond the named conservative cases
was found; the tests do not establish a complete historical traversal.

No service, queue, credential, OS fixture, renderer, runtime provider, hardware,
board, new product Run or formal ledger effect occurred. All29 formal cards,
both actual H12 control chains, complete game/UI/AI/board and final acceptance
remain **not_run**. This candidate does not relax G06's campaign or G07's trials.
'''
(HERE/'report.md').write_text(report,encoding='utf-8',newline='\n')
evidence={p.relative_to(HERE).as_posix():digest(p) for p in sorted(HERE.rglob('*'))
    if p.is_file() and not p.is_relative_to(HERE/'temp')
    and p.name not in ('receipt.json','evidence-manifest.json','native_completion.json','native_completion_text.txt')}
save('evidence-manifest.json',evidence)
receipt={'job_id':'child-c3c3785d01fc40dea9cde699a48641cd','work_id':'A-passage-suffix-implementation-20261019-v1',
    'agent_id':'/root/worker_results_review_20261018','report':digest(HERE/'report.md'),
    'source_manifest':digest(HERE/'source-manifest.json'),'sources':sources,
    'evidence_manifest':digest(HERE/'evidence-manifest.json'),'final_test':load('green-release.json'),
    'tests_passed':253,'tests_skipped':0,'raw_equals_git_clean':True,'utf8_lf':True,
    'dependencies_unchanged':41,'old_design_files_unchanged':16,'formal_acceptance':'not_run',
    'result':'four_file_candidate_frozen_for_independent_review'}
save('receipt.json',receipt)
print(json.dumps({'report':receipt['report'],'source_manifest':receipt['source_manifest'],
    'receipt':digest(HERE/'receipt.json')},indent=2))
