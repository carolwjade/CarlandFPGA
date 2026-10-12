# Progress query fix evidence

Task v1; owner Astra-A; quality route verified gpt-6-astra/ultra.
Base 920ab35; isolated worktree and requested branch created.
No active child file claims at start. Flash read-only inventory job:
child-17923ccbd692440c83777fd2bcc4b2ce.

Root cause and decision are in the task spec. Implementation follows RED/GREEN.
Baseline: 313 tests passed in 29.464 s (baseline.txt). No service, deployment,
configuration or board action. Query-path GREEN and 22 dedicated local integration
tests passed (acceptance-local-final.txt). Full-suite intermediate: 331 passed in
30.228 s (full-suite.txt); this predates four later acceptance tests and recovery
query ordering change, so final full-suite results remain separate.

## Final verified result

Quality main accepts this as a local code checkpoint: 338 tests passed in
30.540 s, exit 0 (full-suite-reviewed.txt), including 25 dedicated tests.
No deployment or three-machine acceptance is claimed. Code publication receipt
will identify the tested source commit and exact remote checkpoint separately.
GitHub upstream ADMIN permission was verified using the existing Git helper;
no credentials or persistent configuration were copied or changed.
Evidence .txt and .json bytes are preserved by the local .gitattributes; manifest
hashes refer to Git blob bytes. Source verification includes LF-normalized hashes.

## Test evidence and interpretation

- red.txt: three intended failures before production changes. The original
  query increments real AppServerGateway task cancellation count from 0 to 1;
  ingress misclassifies it and the version callback is called.
- green-initial.txt: those three pass after classification/isolation.
- red-reporting.txt: missing reporting/status APIs and immediate durable reply;
  includes three fixture timeouts (the temporary Gate also blocked the urgent
  replacement). That fixture was corrected to block only the original work;
  those timeouts are not treated as production failures.
- red-mention-order.txt: two intended failures for display-name routing and
  reversed placeholder metadata; both fixed and covered in later GREEN.
- red-sdk-content.txt: resource-bearing messages were incorrectly accepted as
  queries. Verified local SDK uses resources/content_text; conservative ingress
  flag now prevents Controller from reclassifying the shortened body_text.
- red-recovery-order.txt: saved query callback observed one prior model dispatch;
  final recovery order runs controls, saved queries, then work.
- related.txt: 130 related tests passed in 12.892 s at the first reporting stage.
- acceptance-local-final.txt: 22 dedicated tests passed, covering actual
  Controller/FeishuIngress/AppServerGateway/SQLite/Runtime components and a local
  fake provider. No external model or Feishu endpoint was called by these tests.

Initial PowerShell redirected receipts are UTF-16 and include native stderr
formatting. Later subprocess receipts preserve raw merged stdout/stderr bytes.
The baseline and intermediate regression emit an existing Windows
`ResourceWarning: unclosed event loop`; tests exit 0. It also occurs on unchanged
base 920ab35 and is not attributed to this repair.

## Main quality review

The main traced ingress, SQLite version writes, child version callbacks,
ownership claims, active task cancellation, session run persistence and
runtime result reporting. The direct and Feishu paths now normalize before
any human version mutation. Queries write only inbox/reply bookkeeping.
New execution, compound stop/change messages, and pause retain human priority.
AppServerGateway recovery/no-replay behavior is unchanged and independently
tested. Status reads the full pending inbox, including future retry times;
unverified ledger running/queued values become unknown instead of inventing
activity. Child status is explicitly ledger-only, remote progress unknown.
Main reviewed scope and source diff; no B handoff or outage directory touched.
Flash supplied factual API inventory and a separate bounded diff inspection;
the main retains all acceptance decisions.

## Independent inspection disposition

Flash inspection job child-fa7baffc00884e35879e35a2db92221a completed/current,
read-only, no tests run by the child. Main independently checked its candidates:

- Fixed: absent callback now retains a failed query for delivery recovery;
  pending_inbound counts every kind with separate work/query/control counts;
  pending retry_at is rendered and the footer distinguishes gateway no-replay
  from inbox retry/retirement. Three new failures were captured in
  red-review-semantics.txt, then resolved.
- Fixed compatibility risk: added CLI action progress_status and left existing
  status child-control passthrough intact, with a regression test.
- Kept conservative grammar: only recognized bot-name/placeholder prefixes with
  whitespace qualify. Unknown names, glued text and attachments remain execution
  instructions; expanding fuzzy matching would violate the strict query contract.
  Expired query suppression follows existing expiry semantics intentionally.
- Child raw status values remain explicitly ledger-only observations. Reserved,
  cancelled and interrupted values must not be mislabeled as confirmed running.
  The isolated protocol router has attachment_refs; production ingress also checks
  actual SDK resources/content_text. Both are covered by tests.
- The full-suite Feishu verification URL is a static mock fixture in
  tests/test_feishu_registration.py, not a live approval link or credential.

The final dedicated suite after these changes passes 25 tests
(acceptance-reviewed.txt). The final full-suite receipt is verification.json
and full-suite-reviewed.txt; earlier 335-test receipt is retained separately.

## Coordinated update procedure

Not deployed. Source changes exist only in the isolated task worktree/branch.
The round owner must coordinate after active/outage work ends. From a clean
checkout of the reviewed checkpoint, build with
`python -m fpga_mesh.distribution --profile mesh --output <repository-local ZIP>`.
Record the returned revision and SHA-256. Use the packaged
`deploy/Update-FPGAMesh.ps1 -Node A -Workspace <existing workspace> -Package <ZIP> -CheckOnly`
first, then the same entry without CheckOnly in the coordinated idle window.
Keep existing configuration/credentials/ledgers and do not rerun onboarding.
The existing admission/idle fence must succeed; inspect failures rather than
replaying work. B/C use their own original node updater. Post-update verify
version + status JSON, busy query completion, pause state, new-human priority
and report dedupe with new operation identities. No claim of three-machine
acceptance or physical-board evidence is made by this checkpoint.

## Published reviewed source

PR: https://github.com/carolwjade/CarlandFPGA/pull/3 (OPEN, base main).
Tested source and initial verified remote head:
`2c3e5a3350b7142704b66817391a6ac57b16fd6d`.
Branch: `codex/a/progress-query-fix-20261012`.
The publication-metadata commit follows this source commit; no tested code changed.
No deployment performed. `publication.json` preserves the initial GitHub receipt.
