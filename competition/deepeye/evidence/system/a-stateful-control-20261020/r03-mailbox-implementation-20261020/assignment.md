# R03 bounded latest-completed mailbox implementation

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work A-R03-MAILBOX-IMPLEMENTATION-20261020-v1.
Owner /root/r02_static_dependency_review_20261020 under sole A Desktop director
01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2. Main selects this bounded
implementation under the existing human authorization, without another approval
round. This is a new assignment after your previous job completed.

Before execution read project skill/node-A role, immutable_scope.md and .json,
active transfer. Verify DEEPEYE-HUMAN-LOCK-20261014/revision1 H01-H15 canonical
requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
Validate this folder's new original job via the existing native_lease_guard_20261020.py.
Never expose private lease contents. Main alone accepts results.

## Exclusive writes

- This assignment folder.
- PRODUCT .local/deepeye-implementation-a/competition/deepeye/integration/candidate_mailbox.py
- PRODUCT .local/deepeye-implementation-a/competition/deepeye/integration/test_candidate_mailbox.py
- PRODUCT .local/deepeye-implementation-a/competition/deepeye/tests/vectors/r03_mailbox_lifecycle.json

These three product paths were selected by main as new, disjoint files. If any
already exists before your initial write, stop that write and report. Do not
edit existing files, C dirty files, schema/BOOT/ABI, actor production gate,
viewer, Git index/commits, services, board or communication. All execution
hidden/headless; human needs display. Use -B and test outputs under your folder.

## Selected design and rationale

Implement a small stateful mailbox over existing schema/timing/slot logic.
Main chooses this integration layer over changing the existing stateless
validator or rewriting the established PC_DIRECT runtime. It retains one
latest usable immutable completion, bounded dedup/high-water state and at most
four same-activation observation references. It does not produce a motion grant,
authenticate a caller, launch inference or activate the product.

Inputs bind the active session, full BOOT digest, mode/profile/epoch, original
observation identity/sample-time lower bound, and original completion/candidate
association. Caller supplies already independently verified source/time context;
record types/hashes/booleans alone are not authentication. Unknown clock/source
context yields no consumable selection. Never rewrite input times or substitute
receipt/completion time for acquisition time. Keep immutable defensive snapshots.

Explicitly define latest ordering from the frozen taskbook/host contract and
existing completion association. A later arrival of an older original observation
must not overwrite a newer completion; identical repeats cannot extend freshness,
conflicting duplicates refuse. Retain high-water protection even after consume.
If source order is ambiguous at half-range or wrap, retire/STOP rather than
invent ordering. STOP/new BOOT/mode/epoch invalidates consumable state and old
identity; restarting requires fresh activation rather than reviving an old one.
Sequence/epoch rollover requires stopped fresh session.

Use boot_profile.late_candidate_action for its established legal-slot arithmetic,
with explicit validation around it: its early ready<=start branch alone does
not enforce start<deadline. Require the actual selected slot to remain strictly
before every age/deadline bound, even when candidate was ready early. Account
for explicit validated USB/packing bounds; wrong/missed slot may defer to the
next complete legal slot without moving any slot or refreshing a candidate.
Grant absent/unknown means no consumption/send. Exactly once per selected slot,
and no unbounded retired-key collection. State transitions and selected timing
must be inspectable. Both H12 modes stay represented; a candidate selection
never fabricates HIL capture or replaces PC_DIRECT heartbeat.

## Plan and tests

Read your completed r03-next-software-gap-review-20261020 plus exact current
taskbook lines128-165/340-348, integration/boot_profile.py, host_envelope.py,
docs/host_timing_contract.md and existing PC_DIRECT completion/observation
types at the actual paths in source-pins.json. Pin exact inputs/current HEAD.
Write a compact design/API note in this folder before implementation; it must
resolve ordering, admission/consumption and bounded retirement semantics.
Use TDD for meaningful state behavior: initial failing tests, minimal source,
targeted final regression. Save argv/cwd/actual exit/duration/stdout/stderr.

Independent literal timeline vectors should cover FAST/STRESS, fixed150/250ms
computation, reversed completion, identical/conflicting duplicates, multiple
missed slots, valid old observation among four/evicted observation, deadline
equality, ready before slot but deadline before slot, missing grant/bounds/
source context, STOP/new BOOT/mode/epoch, regression, half-range and wrap-before-
new-session, repeated attempts after consume, bounded storage and no age renewal.
Vectors are software fixtures, not measured timing. Do not simply mirror method
outputs into expected values.

Run only targeted tests plus relevant existing tests if a new discovered concern
justifies them. Do not rerun all245 or change check_interface.py status.
Finish with source diff, known limitations, exact outputs and nonsecret manifest.
All29 and formal R03 remain not_run; actual completion producer/IPC, B PL history,
hardware measurement and full two-mode runtime remain independent dependencies.
Complete the new original job once with final-result.txt and exact terminal
readback, then stop all writes. Report promptly; do not commit or contact peers.
