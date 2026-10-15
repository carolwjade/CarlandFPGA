# A independent review of PR28

Operation `B-RUNTIME-REPAIR-20261015-v1`; request hash `1bb259466270cbcc6a5e6cb2f55366a24bb0945fb4b2c2caff3e4d23541a221e`.

Actual tested PR head: `30de232e66b984d13acdcbf7788631ed49be2151`. Source: `4de6736d9726fe80f4eec8d6d9749785d740fddf`. Repair baseline: PR18 head `8afeaed96c28730466bb353317bdc9a479c3b50c`. Infrastructure review only; existing A/B implementation directors and product scope are unchanged.

## Reproduced evidence

- Public GitHub head and fetched/checked-out Git commit match the sender's head.
- All 19 manifest artifacts match SHA-256, length and exact Git blob bytes; changed Python sources/tests also match the declared source commit. The canonical request hash matches. Standard handoff verifier reports `valid=true`, `files_checked=19`.
- Python 3.12.14: **161 software tests passed in 10.740 seconds**, exit 0. Raw stdout/stderr are preserved; command and log hashes are in `regression.json`.
- `git diff --check 8afeaed96c28730466bb353317bdc9a479c3b50c 30de232e66b984d13acdcbf7788631ed49be2151`: exit 0, no output.

Regression command (from the isolated PR checkout):

```text
python -X utf8 -m unittest tests.test_rpc tests.test_rpc_frames tests.test_app_server tests.test_app_gateway tests.test_controller tests.test_controller_continuity tests.test_store tests.test_runtime tests.test_sessions tests.test_routing_hardening tests.test_project_control tests.test_work_leases -q
```

Root independently inspected pre-send durable `running` state, recovery of `running` to `interrupted`, rejected/unsent versus ambiguous turn failures, RPC request responses and bounded startup/quota paths. A separate native reviewer never began project access because its lease-validation tool did not return; it was interrupted and its actual stopped status verified. No second-review completion is claimed. Parent retains final review responsibility.

## Finding: P2 pre-turn integrity failure terminalizes untouched work

`fpga_mesh/app_server.py:75` raises `RuntimeError` when an existing cached runtime is incomplete or changed. That occurs in the client factory before any work request is sent. `fpga_mesh/gateway.py:368` converts only `ConnectionError`/`OSError` into the not-started path; this integrity error reaches `gateway.py:157` and records `failed`. The next independent message attempts the same corrupt cache and fails too.

The offline `probe_cache_failure.py` reproduces this using actual `pin_codex_bundle`, fake executable bytes and a recording router. It sends **zero turn requests**, but two distinct messages become `failed` with `safe_to_retry=false`. It invokes no executable, model or service. Probe exit code 0 means the reported defect was reproduced, not that this behavior passed acceptance. Raw output is `cache-failure-stdout.txt`.

Requested change: retain fail-closed cache validation while preserving untouched inbox work under a node startup/integrity block or an explicitly pre-turn deferred state. Repairing the bundle must not blindly replay already failed/ambiguous work. Add coverage for multiple queued messages against an invalid cache. This is a specific residual startup path; the 161 passing tests and the main repair's runtime-tool progress remain valid.

Review decision: **changes requested for this P2 queue-preservation issue**. No automatic merge or deployment.

## Scope limits

No A service update/restart, merge, live model smoke, Windows policy change, RTL simulation, synthesis, implementation, board operation or product/system acceptance was performed. B's earlier native-tool smoke remains sender evidence and predates the final crash fence; this review does not establish that B's active process loaded that increment. The two historical one-hour stalls are not independently reproduced or declared completely fixed. Remote model capacity is not a local account-quota measurement.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1` and H01-H15 were read and requirements hash verified as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. No product requirement is changed by this review. Same-PR feedback and B's subsequent readback are separate handoff states.
