# R03 mailbox implementation result

Three new files implement a bounded, non-authorizing candidate mailbox over existing ABI/schema/BOOT/slot logic. No existing product file was edited; all nine pinned inputs and four C dirty files are unchanged. No Git index/commit, board, runtime, network, service or UI operation occurred.

`LatestCompletedMailbox` holds one pending immutable completion, the last accepted high-water/fingerprint, at most four observation records and at most64 used session identities. Original observation sequence precedes candidate/invocation ordering; later arrivals of old observation results cannot overwrite newer results. Consumed/old identities cannot rearm. STOP, ambiguous ordering and invalid input fail closed. Fresh generation plus unused session is needed for activation; storage exhaustion refuses activation. `snapshot()` exposes detached bounded state.

`plan()` returns only a scheduling proposal; `consume()` additionally requires the exact fixed slot start, a matching generation/window grant and unused slot. Both original sample age and original candidate deadline bound selection strictly, including early-ready helper branches. Explicit USB/packing costs advance candidate-ready time; missed slots defer without resetting acquisition/complete/deadline timestamps. Unknown source/clock/bounds/mapping/grant cannot be consumed. PC_DIRECT is represented as software decision epochs only, without HIL wire bytes/capture or replacement heartbeat.

## Fresh verification

- `red-01`:26 failures because implementation was absent, exit1. Original tests/vector bytes and logs retained.
- `green-01`:26 tests pass, exit0.
- One test was refined so a second pre-ready candidate directly exercises the consumed-slot high-water rather than merely missing readiness.
- `deadline-negative-control`:only the early-ready strict deadline comparison was removed in an in-memory module copy. One focused test produced four expected failing subcases (before/equal deadline × two modes), exit1; product source unchanged.
- `final-green`:26 tests pass, no skips, exit0;12 hand-derived timelines × HIL/PC_DIRECT give24 mode/timeline subcases. Includes150/250ms FAST/STRESS, multiple missed slots, reversed completion, exact/conflicting repeats, retained/evicted observations, age/no-renewal, deadline equality/early-ready deadline, missing context/grant/bounds, STOP/fresh activation, mode/epoch changes, clock regression, half-range/wrap rejection, immutable snapshots and bounded retirement.

Every command is hidden below normal with a50-second bound, exact argv/cwd/launcher+worker PIDs/duration/exit/raw stdout/stderr and source hashes. Audit hooks record zero process/network attempts and prohibit test writes outside this evidence directory. No245-suite rerun or existing runtime/actor test rerun was needed: their production dependencies are unchanged and the new library is not wired into their activation path. Full final import pins are in `final-green-imports.json` and verified unchanged.

The actual baseline is c77ee6460cc8dad527c4a7c5dad050c62a9be990 plus the new-file hashes. Main separately authorized publication of new TRACE evidence/documents; `result.json` records closeout HEAD/delta separately. It does not claim the suite executed at a later published HEAD.

## Limits retained for main review

This is an author implementation, awaiting independent review/main adoption. Records, opaque identity objects and numeric bounds do not authenticate callers, completion producers, actual measurements or grants. The serialized owner and real BOOT provider must establish identity/session freshness globally and across process restart;64 identities are bounded within this object, not a durable global registry. Slot polling/real dispatch and actual source/clock verification are external obligations. A returned Selection is never a motion/send authorization. No source/model/IPC provider, PL history, HIL request tracker, real capture, viewer Run, native two-mode runtime or ENABLE is installed. Model usefulness and actual timing/bandwidth are not measured here. No schema/BOOT/ABI/enums/production gate changes were made.

The original early-ready helper remains unchanged; this layer enforces its caller-side deadline contract. Shared profile control-primary epochs used for PC_DIRECT are software arbitration points only; production PC_DIRECT still has no fictitious motion downlink. Any real transport connection needs separately selected mode-specific integration.

`design-api.md` and the assignment fix the scope/API choices; `source.diff` contains exactly three new files, and `final-source/` is the frozen deliverable snapshot. H01–H15 canonical hash is unchanged; all29 and R03 remain not_run. Native completion is a separate exact-result receipt, not product acceptance.
