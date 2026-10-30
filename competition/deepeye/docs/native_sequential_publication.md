# Bounded sequential native publications

The original `world_motion_bridge.gd` now admits at most16 noninitial publications
per successfully frozen epoch. `INITIAL_VIEW` remains separate at revision0.
Every next publication requires the current actual previous revision and its
increment, unchanged geometry identity and a unique operation ID. The preceding
publication must retain its original Main getter/readback and have passed the
original audit. There is no additional motion, BOOT or source authentication.

After header admission, the bridge first marks its existing record APPLYING and
invalidates its readback prerequisite, then consumes quota and updates the
operation metadata. This precedes fallible pose/transform decoding, allocations,
hashing and the original node write. Decode/write/getter/audit uncertainty never
clears a reservation for another try. Actual getter data becomes a usable
APPLIED prerequisite only after the original audit succeeds. No effect is
retried, rolled back or inferred from an ACK alone.

STOP permanently disables admission in that original frozen epoch. Query,
malformed input, failed writes, STOP and unlock do not reset quota. Only a new
legal freeze whose snapshot capture and audit complete resets the counter and
bounded publication-operation set. Unresolved publication state also prevents
unlock. The existing global operation ledger and epoch checks retain their
replay protection. The set contains at most INITIAL_VIEW plus16 noninitial IDs.

A query for a known older publication in the current epoch refuses with
unknown_effect; it cannot turn an old applied effect into NOT_SEEN or replay it.
Current-publication queries retain the existing one-query behavior, actual
getter and payload/revision correlation. An unresolved current effect reports
APPLYING_UNKNOWN rather than a false APPLIED. No wire fields or body schemas
changed; `readback_validated` is private retained bridge state.

Original Main/token/reference ownership, static geometry/source-profile audit,
native transform readback, managed-writer coverage and STOP/retirement guards
remain in place. This change does not enable `diagnostic_step_once`, construct a
Python executor, synthesize BOOT/commands/receipts or open production Run. Root
must separately supply legal original numerical actions and one unresolved
host-side publication at a time.

The NEW `native_sequential_publication_controls.gd` runs only isolated software
custody fixtures in real headless Godot. It calls the product bridge's original
handlers and actual Node3D transforms/getters, with explicit software Main,
audit and queue fixtures. It covers two distinct actual poses/revisions,16/17
quota, pre-decode reservation, unresolved write/getter, failed post-audit, STOP,
duplicate/stale operation/revision/epoch and old-publication query refusal.
Fresh fixture quota is checked, while legal game-world refreeze/retirement is
source-reviewed here rather than claimed as an original Main execution.

TDD evidence: original RED Godot30528 completed21checks/20fail, then GREEN10700
passed21/21. A final source refinement poisons the existing record before new
allocation; final GREEN31304 passed21/21 in a separate fresh stage. All original
Wait/exit/Job0/six-close receipts and failures remain under task39 evidence.
The unchanged supervisor limits are60s,512MiB per process and1GiB per Job, hidden
headless execution with direct log files. No old test suite or original world
operation was replayed. No UI, assets, physical board or full-chain acceptance
is implied by these isolated controls.

The11 writer paths and21 source-profile paths remain the same; this bridge's
bytes have changed. Any subsequent original-world run needs a fresh complete
source stage and refreshed writer/profile/bundle hashes. Do not adopt an old
closed engine or substitute this file into an already frozen source owner.

H01–H15 and requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
are unchanged. Genuine numerical/BOOT/action integration, full Run/CPU/physical
board, formal100ms, both H12, G03/R03/all29 and complete chain remain unpassed.
