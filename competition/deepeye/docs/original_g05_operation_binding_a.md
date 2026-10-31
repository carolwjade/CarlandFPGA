# Original G05 operation association

`OriginalG05OperationBinding(world, producer, config, init_receipt, *, legacy_context, c42_context)` binds the retained original world, link, source/book/projection, host chain, producer, exact init phase and process/stream/QPC association. It independently snapshots both context objects and refuses their mutation; the two namespaces are not converted or equated. It does not create an actor, boot binding, or hardware authority.

`claim_for_factory(config, capability, chain)` consumes one attempt and returns frozen `OriginalG05FactoryRefs`, whose `source_config_attached` reports only the attachment state at claim. A claim can precede source startup. After actual source startup and the original `observe_config` call, `attach_source_config(original_config_ref)` checks the exact retained config object, source clock/origin and existing projection identity labels. `check_source_config()` verifies the same retained config and labels before observations. The class does not create the source config or opaque IDs. Failures are latched and never retried.

The host receipt establishes only actual host-side association. C48 validation and original actor/runtime gates remain separate; there is no claim of ABI3 BOOT, STATE8, motion, board or final acceptance.
