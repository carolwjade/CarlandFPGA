# A independent offline review of existing-task preservation

Decision: `EXISTING_TASK_PRESERVATION_OFFLINE_ACCEPTED` for this increment only.

- Tested PR29 head: `abb3ec996e24ca0e91a2063b943f2e736282fdab`
- Source: `fd867aa485d9fe7ea8754ec35aa53f1df1962154`
- Operation: `B-PRESERVE-EXISTING-TASK-20261018-v1`
- Request SHA256: `4b281259bede714c5a13fa307d5835b04d3cac1b41c6b199e481aebbcd34b71c`
- Manifest SHA256: `bd8d72dbcf3c05d258c123540a92c6a0e550f74bfeb0ce654501755239e7758e`
- Controller task `B-RUNTIME-REPAIR-20261015/v1`; manifest task `B-RUNTIME-CONTINUITY-20261016/v1`.

The A main reviewed the actual updater/helper diff and fixture isolation serially. All 20 manifest entries match raw Git blobs, sizes and SHA256. All five changed source files match the source commit and submitted head; the three admission/rollback files match the prior candidate. Standard handoff verification passed. Fresh Git PR ref and API readback both matched the tested head; B's earlier network failure is retained as a separate historical observation.

A reran the requested focused tests on Python 3.12.14 and Windows PowerShell 5.1.26100.9711:

- 18 PowerShell test methods, 46 process scenarios: exit 0, unittest 26.980s, process 27.094s.
- Four unchanged admission/rollback methods on disposable SQLite ledgers: exit 0, unittest 0.177s, process 0.343s.

Exact command arrays, environment overrides and raw unittest stdout/stderr hashes are in `test-commands.json`. The main suite command is `python -X utf8 -B -m unittest tests.test_update_existing_task -v`; the four full admission method names are in the command record. No unrelated historical suite was rerun.

All 46 scenarios recorded zero Set/Register/Unregister/Enable/Disable task mutations, zero install_routing/models_refresh/register-autostart calls, and no more than one stubbed Start-ScheduledTask call per updater invocation. Seven start calls occurred across distinct scenarios. Task XML, custom launcher bytes, identities, action paths, trigger/settings content and UTF-16 snapshot encoding were checked. Invalid inventory/routing and observed boundary changes block the next step; changed definitions are not restored. Apply failure prevents startup; a failed start is not retried. Existing atomic admission protection remains unchanged and passed its isolated tests.

PowerShell ScheduledTasks autoload was disabled and relevant cmdlets shadowed by fixture functions. The stop callback in the real admission tests was mocked. No actual scheduled task, service, App conversation, network permission audit or board was operated. Full private per-process raw evidence is retained under the review planning directory; `fixture-case-summary.json` publishes counts, phases and byte hashes without Windows user SID or full private task identities. The raw public unittest logs are unmodified.

B's preliminary failed assertion is preserved in its original manifest. It expected a snapshot after a routing rejection that correctly occurred before snapshot creation. A read that original log; it was not rerun or rewritten as a passed result.

No blocking defect found in the supported scoped paths. This does not make task compare/start atomic, prevent all concurrent task edits/triggers, or prove real process lineage/source reload. At most one Start refers to one updater invocation, not total executions caused by preserved Task Scheduler triggers/retry policy. Actual maintenance still requires writer/trigger coordination and the existing admission fence. No new deployment archive was built or accepted. Five B live conflicts and the separate isolated merge rehearsal remain outside this review.

Whole PR29, real task inventory, deployment/restart, actual source reload, reconnect, permanent App wake, merge, RTL simulation, synthesis, implementation, physical-board and product acceptance are `not_run`. H01-H15 requirements hash independently recomputed as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Existing product/director ownership and A-only physical-board authority are unchanged. Publication and substantive B readback receipts are recorded separately.
