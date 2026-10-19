# Reviewer tooling failures (preserved, not candidate failures)

1. Initial inspection invoked PowerShell cmdlets under the wrong shell; `Get-ChildItem` was not recognized. This did not execute a candidate test or modify PRODUCT.
2. The first immutable-scope verifier invocation omitted `--expected-sha`; the script exited with argparse status 2.
3. A JSON field-count probe used a wrong schema assumption (`dict.startswith`); it raised `AttributeError` and did not affect files.
4. The corrected verifier invocation used `--base .` instead of the scope directory; it exited 1 with `immutable_scope.json` not found.
5. A one-line Python evidence-index printer used physical newlines in `python -c`; it raised `SyntaxError` before reading/writing evidence.
6. A review-directory scaffold command assumed the dispatcher-created review root did not exist and exited 1 before creating directories.

These are review tooling errors only. Corrected commands and independent results are retained separately.
7. The first independent pin-audit script used the wrong manifest field name `head_advance_by_main_not_this_child` instead of `head_advanced_by_main_not_this_child`; it produced 1 false failure and exit 1. Raw failed output is preserved as `pins-before.failed.stdout.json`; all 48 evidence hashes and six source hashes in that run already matched.
8. A follow-up summary command assumed PowerShell's redirected JSON was UTF-8; it raised `UnicodeDecodeError` at the UTF-16LE BOM. The corrected UTF-16 read confirmed the pin audit passed.
9. One summary command again invoked PowerShell syntax under cmd; it failed before reading the audit or writing review evidence.
10. The first engine-version runner invocation resolved the pinned engine under PRODUCT `.local/deepeye-implementation-a` instead of the manifest's root-relative `.planning/deepeye-implementation-a` path; Resolve-Path failed and no engine process started. The corrected invocation uses the manifest path and a fresh run label.
11. The first corrected Start-Process runner executed the pinned engine and captured stdout, but PowerShell 5.1 returned a null ExitCode even though HasExited was true. The engine-version-02 evidence is preserved; the runner was replaced with a bounded .NET process implementation that records ExitCode after confirmed termination.
12. The first .NET runner read ExitCode after disposing the Process object, so engine-version-03 recorded a null code despite confirmed termination. Its stdout/version remains preserved; the corrected runner snapshots ExitCode/PID before disposal.
14. The first smoke-run command was again invoked under cmd instead of PowerShell; it failed before starting the engine. Corrected PowerShell invocation follows separately.
15. The first flow-counterexample command was invoked under cmd and failed before starting the engine; no run directory or file was created. Corrected PowerShell invocation follows.
16. An engine-provenance probe first opened `Godot_v4.7.2-stable_win64.exe.zip`; that adjacent file is not a ZIP archive and Python raised `BadZipFile`. The actual `Godot_verified_4.7.2_win64.zip` was then inspected successfully and both binary hashes matched provenance.
17. During staging commands, one informational Add-Content call failed on quoting; staging itself had already succeeded and no engine/source state was affected.
18. A git status/diff-check command was invoked under cmd and failed before executing git; corrected PowerShell invocation follows.
19. A prior-RED hash probe resolved manifest-relative paths from repository root instead of the manifest-declared `root`, producing FileNotFoundError before any writes. Corrected under the declared predecessor root.
20. Two read-only prior-RED inspections were invoked under cmd and failed before reading evidence; corrected PowerShell reads follow.
21. One parallel prior-store-probe read was invoked under cmd; no file was read. Corrected PowerShell read follows.

22. Two read-only checkpoint attempts for `g02-layout-persistence-assignment.md` and `g02-layout-persistence-main-selection.json` were launched under the wrong shell; the shell rejected the PowerShell cmdlet before either file was read. Both were then read successfully under PowerShell.
23. A read-only Git diff/status attempt failed because no `git` executable was available on that shell's `PATH`. A subsequent PowerShell `Get-Command`/known-path probe found `C:\Program Files\MWORKS\Syslab 2026b\Tools\Git\cmd\git.exe`; no repository command had run and no files changed.
24. A text-search attempt failed because `rg` was not available on `PATH`; the equivalent read-only search used PowerShell `Select-String`.
25. A read-only exit-code summarizer encountered null content for an older intentionally failed engine-version record and emitted PowerShell errors. No run result was altered; later logs distinguish the preserved null-exit attempt from the corrected exit-0 engine-version run.
26. Three additional read-only `Get-Content` attempts for dispatch/audit/evidence records were launched under the wrong shell and were rejected before reading. Each was repeated successfully under PowerShell.
27. A read-only viewer-signal search was launched under the wrong shell and was rejected before reading. The connection/source evidence was already covered by a successful PowerShell source inspection; no candidate file was changed.
28. A wide, read-only PRODUCT `git status`/`diff --check` probe emitted long-path diagnostics and a line-ending warning from unrelated concurrent/untracked trees. A narrowly scoped six-path status then returned exactly the expected two modifications and four untracked candidate files; no mutation occurred.

29. A read-only stage-copy log read was launched under the wrong shell and was rejected before reading. The staged-tree ledger was then built from direct filesystem hashes instead.
30. The first stage-identity aggregation passed an ordered hashtable to `Measure-Object -Property bytes` and exited before writing the ledger. The corrected pass summed explicit numeric byte values and produced `stage-identity.json`.
31. The first generated test summary used an old placeholder `exit_code.txt` instead of each raw `result.json`; it could have misrepresented a preserved null-exit runner. That version is retained as `test-summary-v1.incorrect-exit-readback.json`; `test-summary.json` now treats `result.json.exit_code` as authoritative and keeps the placeholder value separately.
32. The first corrective test-summary pass attempted `.Trim()` on a null value from a preserved failed run and exited before overwriting the summary.
33. The second corrective pass computed the repository root one level too shallow and failed engine hashing before writing. The final pass uses the verified three-level ancestry of the review root and wrote a valid summary.

34. The first stage-source check compared stage-root-relative files without the `simulator/` project prefix, producing a failed ledger with 92 failure labels. That ledger is retained as `stage-source-check-v1.incorrect-path-scope.json`; no test run was affected.
35. The second stage-source check correctly found the four project dependencies but incorrectly required the product-sibling contract document to exist inside each staged Godot project and expected seven origin lines instead of six. Its failed ledger is retained as `stage-source-check-v2.docs-and-origin-count-mis-scoped.json`; the final check verifies 84 stage source/dependency identities, the contract directly in PRODUCT, and all six actual import/scene origin lines.

36. Three final read-only static-risk searches (class-name collision, dynamic-loading/authority mutation, and viewer signal wiring) were launched under the wrong shell and were rejected before reading. They were rerun under PowerShell; no candidate file or run was affected.

37. One final read-only line-number search was launched under the wrong shell and rejected before reading. Required line locations were already present in successful prior source inspections; no file or run changed.

38. One role-directory listing and one prior-RED directory listing were launched under the wrong shell and rejected before reading; both were repeated under PowerShell.
39. PowerShell 5.1 `ConvertFrom-Json` rejected an embedded backslash sequence in the author manifest while constructing the inspection ledger. The already independently validated `pins-after.stdout.json` and direct byte hashes were used instead; no manifest content was changed.
40. One attempt to append failures 38-39 was launched under the wrong shell and rejected before writing; this corrected append preserves the failure.

41. The first inspection-ledger builder tried to parse `test-summary.json` with PowerShell 5.1 `ConvertFrom-Json`; embedded Windows backslash paths triggered `Unrecognized escape sequence` before the ledger was written. The final builder reads direct hashes and the already-recorded run outcomes without reparsing that field.

42. A wrong-shell command probe was again rejected before executing the intended PowerShell command. No candidate or product file was touched.
43. The first receipt-builder attempt used PowerShell 5.1 `ConvertFrom-Json` on the complex author manifest; Windows path sequences produced a parser error before `receipt.json` was written.
44. One inline Python receipt/validator attempt failed on PowerShell quoting before Python ran; no artifact was written.
45. The first scoped JSON-validation pass scanned every JSON below the review root, including deliberately malformed fixtures under `env/` and UTF-16LE pin outputs, and therefore reported false failures. It was replaced with the scoped BOM-aware validator preserved in `validate_json.py`.
46. A read-only attempt to open `evidence/build_inspection_manifest.py` failed because no such persisted helper exists; the inspection builder had been run inline. No file was modified.
47. A read-only attempt to open `.agents/skills/fpga-multi-node/roles/A.md` failed because that path does not exist; the project role declaration is `skill-role.json`, which was then read successfully. No file was modified.
48. The first `final_scope_audit.py` run expected the deliberately strict final pin audit to report status `passed`; because that audit correctly reported only the concurrent `product_head` mismatch, the helper exited 1 after writing its preserved raw output to `evidence/final-scope-audit-01/`. The helper expectation was corrected for a second fresh run; no PRODUCT or author file changed.
49. A line-ending-sensitive helper patch for the finalized scope auditor did not match its target block and exited before writing; the preserved `final-scope-audit-01` output remained unchanged. A line-oriented replacement then completed the helper correction.
50. The first final inspection-manifest builder assumed dependency entries used a `path` key; the extant ledger uses a different field name, so the builder exited 1 before writing `inspection_manifest.json`. The builder was corrected against the actual ledger. No PRODUCT or author file changed.
51. The corrected final inspection-manifest builder initially parsed the UTF-16LE `pins-before.stdout.json` as UTF-8 and exited before writing. Its JSON loader was made BOM-aware; the existing pin evidence was not changed.
52. The BOM-aware loader edit replaced one following assignment line with an extra loader line. The next builder run exited with `NameError` before writing; the removed `findings` and `base` assignments were restored. No evidence or PRODUCT bytes changed.
53. The first final manifest/receipt consistency checker treated dependency records as if they exposed a generic `sha256` field; they correctly expose `actual_sha256`, so five false dependency failures were emitted after 203 path checks. The checker was corrected. The same pass separately observed an actual external hash drift in the non-owned `task_plan.md`; that is recorded as scope-input drift, not a candidate failure.
54. While diagnosing a later external PRODUCT HEAD advance, one read-only broad `git diff --name-only` head-range inventory exposed path names from unrelated moving R01 work. No such file contents were opened and no product operation was performed. All subsequent checks are restricted to ancestry plus the six reviewed paths and five unchanged dependencies.