# Complete-duration red-exit passage checkpoint — 2026-10-19

A motion step that first proves complete red-gate exit before its final slice
can now finish the same original duration when every remaining slice proves
the entire drill stays strictly outside the red face and strictly inside the
other five workspace faces. The reducer retains all original slice proofs and
records ARRIVED once. It still rejects a step whose remaining interval lacks
that full certificate; no successfully checked prefix is committed.

This is a bounded G06 numerical implementation increment on base
`b19a528344d8675fedb41f37e7de23f1112f1871`. The four reviewed source/test/documentation
files are identified by manifest
`c4b5b656e78a084e36e8bfcedfdb2f65144226d8af7b336f4588cc4352df6657`.
The selected design, original RED/GREEN logs, source snapshots, independent
tests and main acceptance are retained in the
[raw evidence manifest](../evidence/system/a-passage-suffix-20261019/manifest.json).
Intermediate failures remain tied to their original source versions.

The new branch requires six distinct face certificates in exit role: red uses
`STRICT_OUTSIDE_ACTIVE`, the other five `STRICT_INSIDE`. An APERTURE-only tail,
missing or duplicate face evidence, insufficient slice budget, or a clipped
original duration returns UNKNOWN with the original state and unpublished
events. An actual suffix VIOLATION_PROVED retains that failure classification.
A 9,999,999 ns clipped preview cannot satisfy the new 10,000,000 ns suffix rule.
The full original endpoint, error bounds, speed-error carry and single revision
are retained. A private trace tag distinguishes this proof composition; no wire
schema, workspace method, deadline rule or geometry tolerance was changed.

The unchanged trusted executor checks every original solid sweep before its
existing final runtime fence and single pose/history publication. A collision
or unresolved solid on the last slice rejects the entire step. STOP, world
invalidation and the earliest actual runtime deadline still veto publication.
No geometric work is added after the final fence.

Validation at the frozen four-file manifest:

- The author and independent reviewer each ran the same 253 affected regressions
  with exit 0 and no skips. The final author run is `green-release`; earlier
  `green-final` and RED files are historical candidates, not this final source.
- Seven additional independent methods passed. They include a real three-slice
  acceleration breakpoint with arrival in the middle slice; corrupted
  certificate coverage checks labeled as validation-boundary injections; final
  suffix UNKNOWN/VIOLATION preserving the input state; a real compound casing
  cylinder that blocks only the final solid slice; and actual runtime/executor
  fence, deadline, STOP, world invalidation and one-publication checks.
- The four source files, 41 dependency files, 16 earlier design artifacts and
  author evidence were compared before and after independent testing. The four
  product files are UTF-8 LF and their raw bytes equal their Git-clean bytes.

The numerical phase seeds and software channel fixtures do not prove a complete
preceding traversal or authenticate a live BOOT, source, broker or AI actor.
General APERTURE tails and the blue-entry role-switch margin gap remain
conservative UNKNOWN cases. Complete directed face-pair routes, full same-face
U-routes, the full G06/G07 campaigns, material-state law, causal live sensing,
renderer integration and both actual H12 control chains remain required.

`DEEPEYE-HUMAN-LOCK-20261014/revision1`, all H01–H15 and requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` are unchanged.
All 29 formal taskbook cards remain `not_run`; this increment runs no product
Run, native actor, service, GPU workload or board operation. The separate
Windows CPU isolation execution remains bounded to its previously published
three named fixtures.
