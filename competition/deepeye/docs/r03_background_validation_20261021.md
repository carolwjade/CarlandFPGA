# R03 current software validation

At source b074eaa10012fc5b89f818926195fd24f0bef1bd all 13 selected software
groups have passing exact-source evidence, including PC_DIRECT heartbeat and
watchdog plus pipeline ownership/provenance checks. Pipeline reports 24 passed
and one intentional nested-selftest skip. See the
[checkpoint, preserved failures and individual command results](../evidence/system/a-background-checkpoint-20261021/README.md).

Use the existing jsonschema host dependency directory for these tests. On Windows,
scope Git core.longpaths=true to the test process; do not change global Git settings.
Pipeline's two disposable local shared clones need storage based on the current
tracked tree. Its containment test intentionally creates a temporary link. Keep
original process ownership and resource bounds while allowing that selected fixture.
The recorded scripts bind exact commands, environmental changes and live limits.

The first checker execution remains failed. Passing coverage is composed from its
eight successful groups and five targeted rechecks at unchanged source bytes;
this is not a claim that a later full-checker invocation occurred.

Formal R03 still needs current B/C byte interoperability, register/reset/HWH
integration, real runtime/source/clock/slot/IO evidence and both complete H12 chains.
The separate successful base-overlay BRAM operation establishes only current
physical baseline readiness. No formal task card was promoted by either result.
H01-H15 and their pinned canonical requirements hash are unchanged.
