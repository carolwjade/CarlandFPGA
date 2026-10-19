# Workspace boundary and passage previews

`simulation/authority/motion/workspace_boundaries.py` combines six workspace
faces with one phase-selected circular aperture. `passage_phase.py` reduces
their continuous certificates into an ordered passage preview. Both consume
the reviewed `CanonicalPath` numeric foundation. They do not apply a pose,
authenticate a controller, or grant movement.

H01-H15 remain fixed under `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements
SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The workspace is the closed cube `[-15,15]^3`; rendering remains a hollow
edge frame. Entry and exit retain the taskbook's freely placed, equal-size
blue and red circles. Existing gate validation rejects overlapping or
edge-crossing circles; its UI tolerance never enlarges physical clearance.

## Inputs and continuous proof

`Envelope(half_segment_m, radius_m, pivot_radius_m, reference, exact_fixture)`
declares a covering capsule and a covering pivot-radius bound. The constructor
requires positive radius, `Rb >= half_segment + radius`, a provenance label,
and explicit fixture semantics. This does not verify B's actual asset or pivot.
The common mathematical fixture `h=.4 m, r=.12 m` has total capsule length
1.04 m; it is an outer envelope, not an assertion that the drill is 1.04 m long.

`prepare(path, layout, envelope, start_monotonic_ns=..., deadline_monotonic_ns=...,
hard_stop=...)` obtains slices from the canonical path and binds its provenance,
timing, layout and envelope. It accepts no externally supplied arbitrary slices.
`check_slice(prepared, index, role)` requires an exact built-in string `entry`
or `exit`; semantic string aliases cannot select one gate under the other label.

For each face with outward normal `n`, whole-body support is
`n·p - 15 ± (h*abs(n·u) + r)`. Directed interval bounds include explicit pose,
numeric and additional model errors. Full-interval inflation retains at least
`max(.0005, Rb*Theta) + K*L²/8 + position_error + Rb*angle_error + additional_margin`.
Every non-active face must contain the entire inflated swept capsule. At the
active face, the whole interval must stay strictly on one side or obtain the
existing aperture certificate with the correct direction and angular bound.
The larger supplied `Rb` also enlarges the gate helper's error allowance.

Only the blue hole is active on entry, and only the red hole after entry.
Same-face gates never form a union of apertures. Deep interior turns do not
need a gate-angle certificate. A proof can return `SAFE`, `UNKNOWN`, or
`VIOLATION_PROVED`; an outer capsule failing clearance alone is `UNKNOWN`.
The latter violation verdict is limited to explicit exact-fixture wall/rim
witnesses and cannot establish collision of an unverified visual model.
Insufficient work budget returns `UNKNOWN` without omitting a face.

## Ordered preview state

`initialize` requires the whole body strictly outside the blue face, strictly
inside the other five faces, and aligned inward. A failed initial witness
returns no state. Its result and all later previews have `motion_grant=False`.

`preview` checks the run, scene revision, epoch, gates, envelope, owner reference,
starting pose and expected revision. It carries inherited pose and speed error
bounds and evaluates every slice before producing a candidate state. Ordered
events are `INITIAL_OUTSIDE`, `ENTRY_WINDOW`, `ENTERED`, `EXIT_WINDOW`, `ARRIVED`.
Full-body side witnesses, rather than the center or tip, establish entry/arrival.
STOP, expiry and an already arrived state hold position. A mismatch, insufficient
error budget or failed slice keeps the original state and cannot commit a good
prefix. Numeric timestamps and identity labels remain owner assertions, not
authentication or proof of previous physical execution.

`required_inherited_errors(state, dt_ns)` supplies conservative speed-error carry
for the next canonical step. Resetting accumulated errors is rejected.
`atomic_cas_completed` remains false: a real authority must recheck STOP/deadline,
context and pose revision immediately before committing pose and phase together.
Persistent failure latching, original clock ownership and executed-trace storage
belong to that future executor.

## Verified boundary and remaining work

The original interrupted implementation's four source/test files were preserved
before main recovery. Independent review executed the existing20 tests, six local
face/direction cases and one complete front-to-back numerical chain of12,449
ten-millisecond steps. That chain reaches `ARRIVED_PREVIEW_ONLY`; it is an offline
evaluator fixture, never an AI input or precomputed controller route. The review
also reproduced a role-string alias defect, corrected by the exact-string guard
and a behavioral regression. None of these checks is a runtime or board trial.

The implementation conservatively returns `UNKNOWN` when arrival occurs before
the last slice of a multi-slice plan; event-window refinement remains incomplete.
All36 complete directed face pairs, same-face full U-routes, both real control
topologies, the full fault campaign, actual B collision-body containment,
forbidden-solid/drilling-law integration and real authority/renderer connection
remain separate dependencies. G06/G07 and all formal product acceptance stay
`not_run` until their matching evidence exists. This foundation does not reduce
the taskbook's scope.
