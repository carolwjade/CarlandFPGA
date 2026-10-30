# Original world actor link (private, production unavailable)

This private association borrows the retained Root world, its original world
service, frozen binding, source, field, QPC clock and executor. Issuance and
claim are identity-bound and one-use. It creates no second world or executor.
The production factory calls the fixed production channel factory before actor
launch. That channel factory is unavailable in the current implementation, so
this route cannot activate production today.

On the bound path, the original world is polled after preparation and before
the original executor's commit call. Its final callback performs bounded
identity/veto checks around the original runtime callback and forwards that
runtime's actual `StepFence`, including sequence, interval and deadline. The
reserved slot retains the exact returned `CommitReceipt` and post-CAS root
before runtime regains control. The original world can attempt publication
once after actor/runtime unwind; failed or unknown effects are retained and
are not resent. A later veto cannot turn a retained receipt into no effect.

Readback transform differences are observations, not an error bound. No
reviewed getter bound is installed: `getter_admitted` remains false. APPLIED
alone does not authorize a next source or create an occurred-action record.
The current source book is fixed to its original root revision; the Root runner
must guard *every* source acquisition against unresolved/unadmitted action
state, including paths that do not use that book.

The `_SoftwareWorldActorLink` and its exact fixture owner/backend/fence/receipt
are separate software-only controls. They cannot adopt an actual Root or
native owner or enter the production factory. Their fake CAS/send events test
ordering, retained effects and rejection only: they do not establish a real
BOOT, authenticated channel, source freshness, real geometry CAS, native
readback, board action, either complete H12 chain, G03, R03, or all29.


The fixed `RootWorldOwner.require_source_pose_current()` entry returns normally
for initial stopped diagnostics and rejects a pending or uncertain action, or
an action whose current renderer revision lacks admitted actual getter proof.
Root must wire it into every original service/source-book acquisition entry;
the link itself does not wire those entry points.
