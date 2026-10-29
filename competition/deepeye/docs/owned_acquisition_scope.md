# One original EM acquisition scope

The Root-private `_world_loop._make_original_em_scope_factory(owner, binding,
field, source)` binds one retained production Root owner, original QPC/native
acquisition, registered initialized binding, exact field/executor/scene and pump.
Binding is permitted while the pump is NEW. `factory.begin(tick_ms)` requires a
RUNNING pump on that same clock with the EM slot already consumed; it never
creates or retries an acquisition tick. Use the returned context once and pass
only its local `scope.sampler` into the unchanged producer. The pump's stored
`_sampler` must remain the original `field.sample_sigma` bound method.

Scope entry/exit explicitly poll the original owner outside its busy entry, then
check current custody, real time/session/containment, full scene digest, compiled
field policy and original root/revision/revoke/pose identities. A stopped original
initialized executor may sense. These endpoint polls provide no fresh native
interval-atomic audit ACK and grant no motion authority.

The sampler works only during that one context on its original thread. Public
`sample_sigma` retains its full check for every point. Both paths share the same
scalar mathematics, complete original piece order, material priority and None
boundary/unknown semantics. No producer, kernel, RNG order, geometry subset or
gate is changed. Failed scopes are sticky: field/source association is retired,
pump FAILED, slot consumed, no retry/rebind/output. Body exceptions remain primary
if an exit check also fails; secondary errors are retained for Root evidence.
An acquisition may already have consumed RNG/filter state before a failed exit;
the scope never rolls it back or claims zero random consumption.

The software-only test factory returns a different exact type and cannot adopt
real Root/native owners. Literal point and custody controls do not execute a
kernel, model, native engine or board. This conditional source refactoring makes
no speed promise. Root must separately wire the pump and retain final checks after
trusted contact callbacks and before ADC/publication. Existing Root cleanup owns
all sources/worlds/handles; the scope never closes them.

H01–H15 and requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
remain unchanged. Final 1%/100ms, both H12, G03/R03/all29 and complete-chain/native
qualification remain unpassed. Arbitrary hostile private-state mutation/ABA is
outside the existing trusted Root single-writer convention.
