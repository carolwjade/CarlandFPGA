# Shared numerical CAS component (candidate; private and default inactive)

`_offboard_motion_component.Component` accepts one existing exact
`OwnedMotionExecutor`; construction does not activate it. Explicit activation
requires a fresh stopped executor and no production BOOT or prior fixture. No
world/native acquisition or second executor is created. The component uses
separate `Command`, `Prepared`, `Fence` and `Receipt` identities, leaves
`root.boot` as None, and cannot satisfy production BOOT/command/fence/receipt
type checks. Python private/type conventions are not an OS boundary. This module
is not imported by Root, production factories, source pump, runner or renderer.
Caller-supplied fixture timestamps are not authenticated QPC, observations, AI,
board commands or production authority.

`OwnedMotionExecutor._prepare_geometry` is shared: it runs original canonical
path, passage transition, full scene sweep and strict CLEAR checks. Production
binding digest tuple is unchanged; fixture digest uses its own domain. Both
paths use exact separate one-use prepared types and the same existing executor
pending registry. Production and fixture call the same `_commit_numeric` body:
receipt/frame/new Root are allocated before final fence evaluation; after the
production callback returns or fixture fence is evaluated, only bounded exact
identity/interval checks and the one root swap occur. No clock, hashing, native
I/O or arbitrary callback is added after the fence. `passage_state` materializes
the original relative transition from the same checked/end fields; it does not
require a production BOOT on the saved fence. <=10 ms, existing collision,
workspace, expiry, sequence and revocation rules remain.

Fixture commit reserves a pending effect before calling executor and retains the
exact returned fixture receipt. New commands and preparation are blocked until
that exact receipt is acknowledged; failed or unknown commit is permanently
blocked. This is process-local bookkeeping, not durable external delivery or an
actual world/publication/action registry. Do not replay an unknown effect.

The two added root writes are fresh `replace` calls: activation increments root
revision and veto generation, command admission increments revision; the CAS
still installs a freshly allocated replacement. Neither reinstalls an older
root or mutates a committed pose in place. Root must independently re-audit the
fixed-root interval proof at the final source candidate before integration.
The original production valid-path digest/check preservation needs independent
review; new controls exercise real numerical fixture geometry, not authenticated
production runtime. No native original-world executor run is claimed. Getter
admission remains false; no getter bound, Godot publication, action registry,
board, H12 or final acceptance is supplied. H01-H15 and production source-age
100 ms gate remain unchanged.

## Root custody exclusion

A fixed, late-imported trusted-process check inspects every exact retained
`_RootWorldOwner` and every exact `_Binding` in its retained `_bindings`, by
executor identity. It includes inactive and retired bindings: the original
owner never removes binding entries on retirement. Component construction,
activation, each active entry and acknowledgement recheck custody. Executor
fixture entry wrappers perform this pure check before the existing transaction
wrapper so an attempted diagnostic entry against a Root-custodied executor
cannot revoke it or change its root/pending store. The fixture branches of the
shared private preparation and commit bodies also check before any effect.
No caller flag, callback, native operation or clock participates. The retained
registry is a trusted-process custody convention, not an OS security boundary;
direct private-object mutation, registry tampering or bypassing Python guards
are outside its proof. No original Root or native owner is instantiated by the
new software-only registry controls. Any future original Root offboard adapter
requires a separately designed Root-issued capability and review; this
component cannot be used as that capability.
