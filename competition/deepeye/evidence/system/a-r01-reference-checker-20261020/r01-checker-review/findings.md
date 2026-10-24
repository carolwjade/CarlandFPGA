# Independent R01 checker review

Task: `DEEPEYE-IMPLEMENTATION-20261014/v1`

Work: `A-R01-CHECKER-REVIEW-20261020-v1`

Original child/job: `child-fc8960d8c9a64b959c5f06e1be252bba` on `deepseek-a-29`

Responsible main: Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2

## Verdict

**FAIL for the bounded R01 reference-checker scope.** One substantive false-pass defect remains: `assessment_weights` is never validated. A substituted 100-point distribution and a missing weights object both produced exit `0` with `status: reference_checks_passed` when `--reference-only` was combined with the actual pinned PDF.

This verdict does not grant or deny formal R01 acceptance. `R01` remains `not_run`, `formal_acceptance` and `hardware_enable_eligible` remain false, all formal29 cards remain `not_run`, and no hardware, board, registration, service, or product authority was exercised.

## Finding

### R01-CHK-01 High: weight substitution or omission is accepted as a reference pass

The taskbook requires `python tools/check_rules.py` to reject using 3.3 weights instead of the selected 3.2 basis: `docs/competition/deepeye-2026/taskbook_final.md:331`. The main's selected design repeats this obligation: `.planning/deepeye-resume-20261018/r01-checker-main/plan.md:27`.

The frozen metadata contains the selected five weights at `.local/deepeye-implementation-a/competition/deepeye/docs/rules.json:245` through `:251`: 20, 20, 25, 20, 15, summing to 100. However, `validate_metadata` in `.local/deepeye-implementation-a/competition/deepeye/tools/check_rules.py:105` never reads that field and returns coverage at `:162` without checking its presence, keys, integer types, exact values, or source association. `make_result` at `:179` then grants exit `0` when the PDF bytes and `--reference-only` are valid. The checker and test file each contain zero literal references to `assessment_weights` (`static-audit.json`).

Independent isolated-copy counterexamples:

- `runs/case-weights-tamper.json`: changed the 100-point distribution to 20, 20, 30, 20, 10 while retaining all fixed rows, then ran `--reference-only --source-pdf <actual pinned PDF>`. Exit was `0`, report status `reference_checks_passed`, source `passed`, R01 `not_run`, formal/hardware false.
- `runs/case-weights-missing.json`: removed `assessment_weights` entirely. Exit was `0`, report status `reference_checks_passed`, source `passed`, R01 `not_run`, formal/hardware false.

Impact: this is a false success only inside the explicitly requested reference-check scope, but that success is enough to publish invalid rules/trace metadata as if the R01 source/weight check passed. It directly violates the taskbook's no-3.3-substitution requirement. It is not evidence of formal R01, registration, real physical-task recognition, ROCm completion, or hardware readiness.

Required repair: require `assessment_weights` to be an exact object with exactly the five selected keys, strict integer values exactly equal to the reviewed 3.2 mapping, and sum 100; reject absent, extra, boolean, changed, or differently associated weights; add regression tests for missing and changed values; retain exit `1` for invalid metadata. Do not accept metadata claims as formal acceptance.

## Verified behavior

- The 17-method suite ran once independently from PRODUCT: exit `0`, `Ran 17 tests`, `OK`. Raw streams and hashes are in `runs/review-tests17.*`.
- Recorded CLI behavior reproduced exactly in outcome: default full exit `2` blocked; explicit-PDF full exit `2` blocked; explicit-PDF reference-only exit `0` reference checks passed. Every report kept `R01: not_run`, `formal_acceptance: false`, and `hardware_enable_eligible: false`.
- Reference-only without the pinned PDF was independently run: exit `2`, source blocked, R01 `not_run`.
- The taskbook working-directory form, `python -B tools/check_rules.py` from `competition/deepeye`, also exited `2` blocked with no traceback.
- All applicable CLI reports were JSON on stdout with empty stderr, including malformed input failures.
- Corrected structural counterexamples behaved safely: a real 4000-level JSON array exited `1` with `maximum recursion depth exceeded`; a duplicate root key exited `1` with `duplicate JSON key`.
- Joint rule/trace drift moved ROCm to page 3 and owner R01; exit was `1` with a page-mapping rejection.
- Existing tests exercise missing trace rows, duplicate trace rows, owner/page/source drift, declared type failures, status type failures, CSV schema/extra-column/1 MiB bounds, nonfinite constants, exponent overflow, missing/forged PDF, and claim-only status handling. These passed, apart from the missing weight coverage above.
- Static inspection found only standard-library imports and one read-only `path.open('rb')`; no network, registration, subprocess, hardware, model, or file-write operation is added by the checker.

## Pin and scope checks

- Candidate manifest SHA256: `85a6db6ee4f839685a47770590fcbca6683862927318d94d05f749fad3b3c8cd`; matches the requested pin.
- All three candidate source pins match: checker `6276854e4c336d32d1afc3c110f61c3d112135965ea09997a28af4862042057a`, tests `8a21b7aa71714c2ffacd1c7a002b4280b17c979be1350ddbc5f84a1f9f16feac`, documentation `2cfdcca1cb0ade6eb50d5aa90ca3f799b1369dbb87e495e605c7f2f0c3e5bc9b`.
- The manifest names exactly three PRODUCT source paths. Each is untracked and absent at base `889d7d6ebf0e2719aeb64cf13e3be6ebca2a2bc1`; current hashes still match the manifest.
- All six input pins match: rules, trace CSV, both immutable-scope copies, taskbook, and the 950952-byte PDF at `c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc`.
- All 25 main evidence pins match.
- Canonical H01-H15 requirements hash independently recomputes to `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`; 15 IDs H01-H15 match and the two immutable-scope copies are byte-identical.
- The three candidate files, all six inputs, and all 25 evidence files remained hash-unchanged through review. No `__pycache__` appeared in the checker/test directories or review scope. The PRODUCT HEAD advanced concurrently from `889d7d6e...` to `678e01dd...` due unrelated active work; no G02 or unrelated moving file was inspected or modified. The R01 candidate paths remained untracked and hash-stable.

## Limits

- This review covers bounded offline schema, provenance, exact-byte, and exit-report behavior only.
- It does not establish current organizer semantics from the PDF; the checker's fixed table is only checked for consistency with the pinned prior mapping.
- No live registration, qualification, ROCm project, physical task recognition, hardware execution, board run, measurement, or formal acceptance was performed.
- Formal29 remains `not_run`; H01-H15 remain unchanged.
- Initial review-runner invocations that failed before launching tests, two intentionally preserved malformed structural construction attempts, and one static-audit script typo are recorded in `failed-attempts.json` and the corresponding preserved run files. They did not mutate PRODUCT and do not change the weight finding.

## Evidence index

- `inspection_manifest.json`: all inspected pins, origins, commands, artifacts, and before/after hashes.
- `receipt.json`: terminal command/test summary and bounded-scope verdict.
- `runs-summary.json` and `runs/`: raw stdout/stderr, commands, exit codes, and hashes.
- `inventory-before.json`, `inventory-after.json`: candidate/source/input/evidence pin comparisons.
- `provenance-check.json`: exact test/checker import origins and 17 discovered methods.
- `requirements-check.json`: canonical H01-H15 hash.
- `static-audit.json`: zero weight-field references, source citations, imports, and side-effect inspection.
