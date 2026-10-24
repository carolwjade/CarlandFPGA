# Independent R01 checker repair rereview

Task: `DEEPEYE-IMPLEMENTATION-20261014/v1`

Work: `A-R01-CHECKER-REREVIEW-20261020-v1`

Responsible main: Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2

## Verdict

**PASS within the bounded repair-rereview scope.** The repair closes `R01-CHK-01`: missing or substituted assessment weights no longer pass the reference-only path. I found no regression in the checked behavior. The original finding and its two false-pass runs remain historical evidence; they are not relabeled PASS. This verdict does not grant formal R01 approval.

## Finding closure

`R01-CHK-01` is closed for the exact repaired candidate pinned by SHA256 `9582bde875bf1aa2daef6c8f1b3d4925ed67cba0a22cb11f9d7ac0d773291f90`.

- The repaired checker defines exactly `system_completeness=20`, `pc_ai=20`, `fpga_quality=25`, `cooperation=20`, and `engineering_innovation=15`; the frozen `rules.json` mapping is identical and sums to 100.
- The checker requires an actual `dict`, an exact five-key set, strict `int` values, exact equality with the reviewed mapping, and sum 100. This rejects absent, incomplete, extra-category, re-associated, boolean, float, and string substitutions.
- The source association is explicit: `docs/competition/deepeye-2026/taskbook_final.md:331` prohibits using 3.3 weights instead, and `.planning/deepeye-resume-20261018/r01-checker-main/plan.md:27` repeats the selected requirement. The frozen weights remain at `competition/deepeye/docs/rules.json:245` through `:251`.
- The test file retains all 17 original method bodies byte-for-byte at the AST level and adds exactly three weight tests. The 20-method suite ran once from the fresh stage and exited `0` with `Ran 20 tests` and `OK`.
- Fresh copies of the original malformed fixtures preserved their rules, trace CSV, and immutable scope. Only their checker copy changed to the repaired source. The repaired checker rejected the unchanged 20/20/30/20/10, sum-100 substitution with exit `1` and the unchanged missing-weights fixture with exit `1`.
- The original 95-file review tree still hashes to `1defa9cfa10cbac4d4020e3a52174068ec884e359af3636afac8374a468a359c`; its two historical malformed runs still record exit `0` as preserved evidence of the defect.

## Regression checks

- Valid pinned-PDF reference-only behavior remains exit `0` with `status: reference_checks_passed`.
- Default invocation remains exit `2` and blocked; explicit-PDF full invocation remains exit `2` and blocked. The normal/default/full map is `0/2/2`.
- All five CLI reports, including both malformed cases, retain `R01: not_run`, `formal_acceptance: false`, and `hardware_enable_eligible: false`.
- All six pinned inputs and all 24 repair-evidence entries rehashed unchanged. The three sources match the repair manifest and fresh stage; their pre-repair copies match the original candidate manifest.
- The original review tree remained 95 files with its pinned tree hash. No `__pycache__` appeared in the R01 checker/test/docs source directories or the fresh stage. Two unrelated pre-existing PRODUCT cache directories under integration and motion authority were observed but untouched.
- Imports resolve from the fresh product stage, not PRODUCT or the original fixture: both checker and test modules have staged origins, with 20 discovered tests. The interpreter was the existing venv Python `3.12.14` running with `-B`, isolated `TEMP`/`TMP`, `PYTHONPYCACHEPREFIX`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, and no `PYTHONPATH`.
- PRODUCT HEAD advanced concurrently from `678e01dd097f326e5bf724dc9db9e6b3e388384d` to `420209a860c037c3fc2a731037de8ec9b62c4107`. The three scoped source files remained untracked and hash-identical; this rereview used their exact hashes rather than HEAD as identity.

## Candidate hashes

- Checker before to after: `6276854e4c336d32d1afc3c110f61c3d112135965ea09997a28af4862042057a` to `c864fb29c13bbe64dba8d6e344ec1f229e6cc757a3e1fa29018264184215384e`.
- Tests before to after: `8a21b7aa71714c2ffacd1c7a002b4280b17c979be1350ddbc5f84a1f9f16feac` to `fcd9ac2be810731c3f4e77f9ccf06152287bea78af774d5f63ca7ddbe02c06ab`.
- Verification document before to after: `2cfdcca1cb0ade6eb50d5aa90ca3f799b1369dbb87e495e605c7f2f0c3e5bc9b` to `451ae603ae206ec7c0a46fb57b347ee506b999f31217c4d326f87b02a45cbf0f`.
- Repair patch: `94423ad780224ddbee0c989ea8402ee61b15a20d66c85e1fb30b40102acf8d2c`.

## Immutable scope

The canonical H01-H15 requirement array independently recomputes to `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`; IDs H01 through H15 match. Root and PRODUCT `immutable_scope.json` are byte-identical at `6a86000e97d1571c0b7b89b9d3cf7facb11d2b6a06455eb1d53e0637676b6bc4`.

## Limits

- This is an offline checker-schema and provenance rereview, not a reinterpretation of the PDF's current organizer semantics.
- No formal R01 acceptance, live organizer rule recognition, registration/qualification, ROCm project, physical engineering gain, hardware eligibility, board operation, service/driver change, or measured task evidence was produced.
- `R01` remains `not_run`; formal acceptance and hardware enable eligibility remain false; all 29 formal cards remain `not_run`; H01-H15 are unchanged.

## Evidence index

- `inspection_manifest.json`: pinned candidate/input/evidence, before/after source hashes, import origins, fixture derivation, 95-file historical tree, all raw run records, and check results.
- `receipt.json`: compact terminal verdict, exit map, tests, pins, and limits.
- `runs/`: exact command records, raw stdout/stderr, exit codes, and stream hashes for the 20-test suite, three normal/default/full CLI cases, two malformed fixtures, static inspection, and provenance.
- `review-static.json` and `provenance.json`: preserved pre-run static inspection and import-origin inputs used by the manifest.
- `artifact-hashes.json`: final evidence-file hashes, written after the report files.
