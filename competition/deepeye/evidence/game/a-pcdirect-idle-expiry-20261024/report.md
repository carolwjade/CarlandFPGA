# PC_DIRECT idle expiry selection

The owner loop now checks the original runtime command/heartbeat expiry after
the existing actor poll. Expired ACTIVE admission retires through the existing
stop/revoke transaction without preparing or committing another motion step.
Prior committed pose, pose_revision and frame facts are retained. The frozen
ExpiryStatus is diagnostic output; it grants no readiness or motion authority.

The four selected files are exact author-manifest bytes. Root and independent
review checked original clock/latch/history semantics, initial unbound and
never-commanded waiting, exception/reentry/foreign-call vetoes, original-deadline
retention, fresh time after actor poll and late-input rejection. Final CAS fences,
v2 windows, executor and production factory refusal are unchanged.

Saved evidence contains one import failure before any test method, two new
behavioral RED failures and GREEN03's fourteen new method passes (0.604s).
The positive case performs a real numerical software CAS first, then observes
idle stop with zero additional prepare/CAS. No historical test methods were
selected, and Root/reviewer did not rerun tests. Three of four attempts were used.

This is offline software evidence with synthetic clock/channel/native boundaries.
No physical board, authenticated provider, useful CPU AI, actual native actor or
Godot run occurred. The owner loop must still run; this API does not supply an
independent owner-death or kernel scheduling deadline. Both full H12 paths and
G02 remain open; G03/R03/all29 remain not_run. H01-H15 are unchanged.

The archive explicitly enumerates frozen author/reviewer evidence, the reviewed
plan and Root selection. Private control files, credentials, databases, caches,
native executables and unrelated historical archives are excluded.
