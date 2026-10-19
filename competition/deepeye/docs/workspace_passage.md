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
The existing owned numerical motion executor supplies the final callback/CAS,
failure latching and actual-time trace mapping. These preview certificates do
not replace its original clock, source-health or command-deadline checks.

## Complete-step strictly outside red suffix

After a slice first proves whole-body red exit, the preview now continues over
every remaining slice of the **same original canonical plan**. Each suffix slice
must return `SAFE` from the unchanged exit-role six-face checker, with exactly
the six distinct faces, red `STRICT_OUTSIDE_ACTIVE` and the other five
`STRICT_INSIDE`. Thus its full inflated swept body remains outside red and cannot
leave through another face. All existing rho terms, guards and method identities
remain unchanged; this is a finite conjunction of existing interval proofs.

Suffix certificates are retained in order. Only the first arrival window appends
`ARRIVED`; suffix checks append no duplicate arrival or exit-window events. The
candidate uses the original `plan.end`, full covered duration, one revision and
the same end errors/speed-error carry. A private `strict-red-outside-suffix-v1`
trace tag distinguishes the newly accepted proof composition without changing
the workspace VERSION, shared wire or host schemas.

A suffix that is `SAFE` only through `APERTURE` remains `UNKNOWN`. Missing or
non-strict face evidence also remains `UNKNOWN`. An actual suffix `UNKNOWN` or
`VIOLATION_PROVED` retains that distinction. Every rejected suffix returns the
original input state/history, with the checked certificates for audit: no safe
prefix is committed. The original whole-plan slice budget is checked first.
Single-slice arrival, entry roles and the later `ARRIVED_FROZEN` hold are unchanged.
The new strict-suffix composition also refuses a deadline-clipped plan: every
nanosecond of the original requested duration must be covered. A 9,999,999ns
clipped plan cannot satisfy a 10,000,000ns suffix request.

This means the full original dt is certified and committed together; it does not
claim the exact time of red-plane crossing or truncate at the first arrival
window. The existing executor still checks initial/full solid clearance for
**every** original slice before preparing a handle, then performs the unchanged
final fence and one publication. A forbidden or drilling-required final-slice
solid blocks the whole step. No work is moved after the fence.

## Verified boundary and remaining work

The original interrupted implementation's four source/test files were preserved
before main recovery. Independent review executed the existing20 tests, six local
face/direction cases and one complete front-to-back numerical chain of12,449
ten-millisecond steps. That chain reaches `ARRIVED_PREVIEW_ONLY`; it is an offline
evaluator fixture, never an AI input or precomputed controller route. The review
also reproduced a role-string alias defect, corrected by the exact-string guard
and a behavioral regression. None of these checks is a runtime or board trial.

The new numerical regression seeds `EXIT_CROSSING` at z=-15.519/-15.5199 with
yaw7000 produce two slices, 0/7,142,857/10,000,000ns. They now certify the complete
original 10ms and retain only one arrival window. These are explicit internal
phase fixtures, not evidence of the preceding physical/committed route. Six red
face orientations and correct-role same-face apertures are checked likewise.
At z=-15.5184 the suffix has only `APERTURE`, so it remains `UNKNOWN`. The entry
seed z14.4815 still has a blue-to-exit-role envelope gap and remains `UNKNOWN`.
General APERTURE tails, entry role-switch refinement and exact crossing-time
refinement are not solved by the strict suffix rule.

The actual numerical executor regression uses a thin box at z=-16.0414: the
first sweep is `CLEAR`, the final nominal cap contains the box centre, and the
real second-slice solid check blocks the full step (water `UNKNOWN`, hard rock
`DRILLING_REQUIRED`). This does not relabel conservative contact as a proved
collision of an unverified asset. The positive path commits one callback/CAS,
maps only new events to actual fence time, and freezes on a later arrived step;
STOP, deadline equality, world invalidation and TM-R1 regressions remain active.
All36 complete directed face pairs, same-face full U-routes, both real control
topologies, the full fault campaign, actual B collision-body containment,
forbidden-solid/drilling-law integration and real authority/renderer connection
remain separate dependencies. G06/G07 and all formal product acceptance stay
`not_run` until their matching evidence exists. This foundation does not reduce
the taskbook's scope.
