# Stateful candidate owner adoption

The composition now owns the lifecycle of a completed candidate instead of
looking up a substitute completion at command time. A private candidate owner
connects the reviewed latest-completed mailbox to the existing authority actor.
It retains one pending original proof and the proof associated with the current
admitted command; later completions cannot renew the current command's deadline.

Verified source observations enter the four-observation mailbox only after runtime
acceptance. A completion is offered after the source/epoch fence and a fresh clock
sample. A new non-STOP command needs an exact validated slot and a fresh time
sample, consumes the pending selection, and then passes the existing progress,
runtime and executor admission checks. Only successful admission associates the
proof. Exact duplicates reuse current proof without consuming a new candidate.
Every input transaction is cleared on exit; retirement clears pending/current
proof before callbacks. Existing final-step numeric checks and pose CAS remain.

The production factory is still closed. BOOT identity, clock-domain consistency,
source authenticity, original completion IPC, exact slot provenance and actual
authority serialization must come from real upstream providers. The mailbox
selection and owner bookkeeping themselves provide none of those authorities.
The independent controls use synthetic upstream/native/time providers.

Main accepted five exact source/doc files after independent review and artifact
verification. The independent eight controls passed, including actual local
runtime/executor admission and numeric CAS, with verified process termination.
Author test groups overlap; original failures and migrations are preserved.
The historical RED assertion supports only the narrower combined refusal/no-commit
failure, as explained in the [correction](../evidence/system/a-stateful-owner-20261021/CORRECTION.md).
See the [review and complete evidence index](../evidence/system/a-stateful-owner-20261021/README.md).

This is bounded host integration. It does not close R03, either full H12 path or
any of the 29 formal cards. Real providers, PC_DIRECT/FPGA runtime interoperability,
clock/IO measurements and board/system acceptance remain required. Software work
ran hidden while the human used the display; no foreground or hardware actions
were used. H01-H15 and the pinned immutable requirements hash are unchanged.
