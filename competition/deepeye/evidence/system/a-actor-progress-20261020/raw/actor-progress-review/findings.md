# Independent review: original actor inference-progress gate

**Verdict: PASS for the bounded offline software scope only.** No blocking, High, or Medium
implementation defect was found. One Low test-quality issue is recorded below. This is not
production, native AI, hardware, game, H01-H15, or formal29 acceptance; the main owns final
acceptance.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`, work
`A-ACTOR-PROGRESS-REVIEW-20261019-v1`, responsible sole main
Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d` generation 2. Review date: 2026-10-19.

## Inputs and identity verified

- Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`; all 15 requirements recomputed from
  `docs/competition/deepeye-2026/immutable_scope.json` to
  `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
  `product_status` remains `all acceptance tasks not_run`.
- Active transfer still names the responsible main above; the retired background director is
  not reactivated.
- `candidate-manifest.json` SHA256 is the pinned
  `23e07f12b6a22b0c264b2c8ed59312e0546a364423d2008d5f63894a8317b17f`.
- All 58 candidate pins match: three changed files plus 55 frozen dependencies. All 18 author
  evidence pins match. The three requested baseline copies match their 58-entry selection;
  the 55 unchanged dependency hashes equal the candidate hashes.
- Selected design is the actual `actor-progress-design/design.md`, SHA256
  `cb91477153276369c6eaead242cbecb70423804f6939bbbef49a788a931451db`.
  Baseline HEAD remains `889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1`.

## Findings

### Low: one named unrelated-completion test does not exercise that scenario

`competition/deepeye/tests/simulation/test_actor_composition.py:347-355` inserts a completion
under key `('unrelated', 99)`, but no subsequent command lookup consumes it. The synthetic
channel at `competition/deepeye/tests/simulation/test_actor_composition.py:45-49` indexes by
`(id(boot), request['candidate_id'])`. The test then advances to the existing bound deadline and
checks a normal step failure (`:352-355`), which proves expiry but not that an unrelated newer
completion cannot extend the current command.

This is a test-quality gap only, severity Low. The product checks request/candidate identity and
the current bound at `competition/deepeye/simulation/authority/actor_composition.py:135-166`,
and independent review cases exercised mismatched candidate ID/target, changed request timing,
changed invocation, exact-byte identity, and monotonic IDs. No source edit is requested by this
review; the author can correct the test name/body in a separately owned follow-up if desired.

No other concrete correctness or maintainability defect was found.

## Requirement audit

| Review item | Evidence and result |
| --- | --- |
| Completion-derived fixed deadline | Deadline is `completion_lower_ns + progress_max_age_ns` at `competition/deepeye/simulation/authority/actor_composition.py:153`; receipt time is not used to renew it. |
| Original association | Exact proof BOOT/source/clock identity at `:131-133`; request/candidate validation and model/target/observation/candidate-ID equality at `:135-145`; original command lookup at `:262-275`. |
| Strict bounds and sums | Exact-int bounded predicate at `:58-61`; initial and completion sums are bounded at `:100` and `:153`; config policy is validated at `:520-524`. |
| Ordered original times | `dispatch <= lower <= claimed_completion <= upper <= request_issue <= now` at `:151-152`. |
| EMPTY initial budget | `:99-100` fixes the initial deadline; `:114-116` refuses an empty/expired gate. |
| Strict ID monotonicity | Same-command changes reject at `:160-163`; newer command requires greater command, candidate, and invocation IDs at `:164-166`. |
| Duplicate nonrenewal | Exact duplicate returns without changing the bound at `:160-163`; changed duplicate revokes via `:122-127`. |
| Irreversible expiry/revoke | `:104-120` retains high water/revocation; `:372-378` revokes before callbacks; owner reentry/foreign rejection at `:186-195`. |
| Original actor mandatory | Every lease request first calls the frozen original `owner._actor.ai_lease` at `:287`; static/cached fallback is absent. |
| Shorter life/progress wins | Returned lease is the exact minimum at `:302`. |
| Post-sample and whole-dt boundary | Runtime re-samples after the AI sample at `pc_direct_runtime.py:429-439`; the frozen executor requires strict `step_end < deadline` at `motion_executor.py:341-353`. |
| Post-CAS truth | A commit remains committed if a later veto occurs at `actor_composition.py:205-216`. |
| Final-seam discipline | `ai_lease` at `:280-302` adds no IPC, channel callback, envelope parse, logging, or new clock read; it uses the original actor sample and the runtime-supplied `now_ns`. |
| Production remains unavailable | `_production_channels` unconditionally raises at `:178-180`; factory calls it before registry construction at `:525`. |
| No fake capability claim | Module/docs explicitly identify synthetic tests and unavailable production at `competition/deepeye/simulation/authority/actor_composition.py:1-5` and `competition/deepeye/docs/actor_composition.md:50-91`. |

## Independent execution

- Preserved author RED: `actor-progress-main/progress_gap_red.py:29-50` produced actual
  `tests=3, failures=3, errors=0`, with `assertFalse(result.committed)` failures showing the old
  behavior committed. The preserved logs were inspected, not rerun or overwritten.
- Author focused evidence remains 39/39, and final author regression remains 193/193; all pinned.
- I independently ran the exact affected 193 once: composition 45, owner 21, lifetime 36,
  runtime 64, executor 27; `failures=0`, `errors=0`, `skipped=0`. All 24 original composition
  test-method ASTs are unchanged.
- Import-origin audit: 35 imported product modules, all under the frozen PRODUCT worktree; every
  one is a pinned candidate file with a matching hash. No root-worktree or unpinned import was
  found. The process used the original venv `python.exe -B`, process-scoped `PYTHONPATH` including
  `.local/deepeye-host-deps`, and TEMP/TMP under review evidence.
- Eight independent adversarial tests passed: candidate-ID mismatch, full-target mismatch,
  changed request issue/completion upper, changed invocation, semantically changed candidate
  bytes, non-increasing candidate ID, non-increasing invocation, and a legitimate newer
  completion that extends and commits. See `counterexamples.py:67-140`,
  `counterexamples_ids.py:63-94`, and `counterexamples-result.json`.
- Final check: all 58 candidate inputs remain byte-identical; all 18 author evidence files remain
  byte-identical; all three baseline source copies and 55 dependency hashes match. No PRODUCT
  write was made by this review.

## Genuine limits

- There is no genuine inference producer, backend, model authentication, bounded persistent IPC,
  or original completion verifier result. Candidate/source/clock checks are in-process object
  correlation only.
- Tests use a synthetic original-verifier fixture and fake clock/actor boundary; they do not
  establish model usefulness, causal source authenticity, native execution, readiness, BOOT
  authenticity, or timing provenance.
- The actor HANDLE sample is synchronous; hang supervision and arbitrary post-sample death races
  are not solved by this numeric gate.
- No native AI, production Run, game/3D/UI, PC-direct/HIL completion, board operation, or formal29
  result was produced. H01-H15 and all29 remain unchanged and `not_run`.