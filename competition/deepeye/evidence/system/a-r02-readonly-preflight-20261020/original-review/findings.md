# Independent R02 preflight review

Specification verdict: **CHANGES_REQUIRED**.

Code-quality verdict: **CHANGES_REQUIRED**.

This is evidence for the responsible main, who retains acceptance. It reviews
Task 1 at base `f1d8c6d37bf6e17b3b0b92dc4998a4c7f8959bbe` plus the four
uncommitted files listed in `verification.json`. There is no accepted product
head. Current bytes match the complete supplied diff and both author receipts.

## Required corrections

1. **P1 — The delivered collector command cannot perform its intended inventory
   on the authorized host.** `competition/deepeye/tools/preflight.py:177`
   invokes the script with `-File`. The original `live.receipt.json` records exit
   2 without timeout; its hash-verified stdout records collector exit 1 and
   `UnauthorizedAccess` because script loading is disabled. `observations` is
   null. Thus the plan's one actual host inventory was attempted but not
   obtained. The successful synthetic suite does not establish the collector's
   successful path. Preserve this historical failure. A separate minimal
   fixed-text `-Command` correction is suitable for main review under the
   conditions below; the current revision is not a usable completed host
   inventory delivery. This finding confirms the author's disclosed limitation.

2. **P2 — The promised identical output bytes are false on Windows, and the test
   masks the difference.** `competition/deepeye/hardware/preflight.md:20-21`
   promises exactly stdout's UTF-8 JSON bytes. The file is opened with
   `newline="\n"` (`preflight.py:250`) while `sys.stdout.write(payload)` at line
   279 uses the Windows text stream. The real saved stdout has 79 CRLFs and the
   file has none. They parse identically, but their verified SHA-256 values are
   respectively `8c7d0ae31fd0f8c3e7e27130af418406456da52fb75590bf355410538d7e1722`
   and `3677c06cacbb6d7890ddd006e1212f33a952e651fd7aecda17a7ec8d8ecc918a`.
   `tests/test_preflight.py:180-186` substitutes StringIO, eliminating the newline
   translation being promised. Either emit one explicitly encoded byte payload
   to both streams with a meaningful byte-level check, or make an explicit
   main-approved JSON-equivalence contract/documentation change and adjust the
   test. Do not continue promising byte identity from a StringIO test. This is
   independently confirmed against the retained live output.

3. **P2 — Remove or substantiate the added `DEV_17F0` candidate rule.**
   `preflight.py:98` and `preflight_windows.ps1:44` classify an unnamed
   `PCI\VEN_1022&DEV_17F0...` device as an NPU candidate. The supplied authoritative
   brief identifies the observed AMD prefix as `VEN_1022&DEV_1502`; no source for
   `17F0` appears in the candidate, report or saved evidence supplied for review.
   `tests/test_preflight.py:110` only repeats this newly chosen expectation, and
   `hardware/preflight.md:45` presents both prefixes without provenance. The
   focused synthetic check confirms the new rule matches an "Unknown device".
   Remove `17F0` consistently from both matchers/test/docs, or provide a recorded
   authoritative source and label its scope. This is an unsupported observation
   heuristic, not evidence that `17F0` is an incorrect device ID and never proof
   of tested accelerator support. No network/hardware lookup was performed.

## Nonblocking diagnostic observation

`preflight.py:216-218` replacement-decodes child stdout/stderr as UTF-8 and then
discards those raw bytes. The retained live error contains nine replacement
characters in the non-ASCII path. The author's raw *CLI* output cannot recover
the earlier original *collector* bytes. A single fake process with stderr
`b'path-\xff'` independently reproduces this loss without starting PowerShell.
The error code and English denial reason remain usable, so this does not change
the three required corrections. Consider bounded base64 diagnostics with their
encoding/status, or accurately document decoded-only diagnostics, when revising
the error boundary. Do not describe the current structured diagnostics as
lossless raw collector evidence.

## Assessment of the fixed-text `-Command` proposal

Acceptable in principle for a separate minimal correction, **unverified** here.
Supply the reviewed collector text directly as the final `-Command` argument in
the existing argument-list Popen call, with no user-supplied code, interpolation,
extra command, `-ExecutionPolicy` option or policy-setting changes. Read the
fixed collector bytes once, hash those same bytes, decode them strictly and pass
that exact text, so reported source identity corresponds to the code submitted
to PowerShell. Merely using `-Command` to invoke/dot-source the `.ps1` path does
not establish that the script-loading failure has been addressed.

Retain NoProfile/NonInteractive, hidden/below-normal flags, owned-process
kill/wait, bounded pipes and the existing 20-second collection budget. Do not add
an automatic retry after `-File`, which would violate the single-invocation/no-
retry contract. Preserve the original failure as a separate historical receipt.
An authorized later successful-path run with new candidate hashes and new
evidence is still required before saying this collector works on the host.
This review did not execute the proposal or collect inventory.

## Verified strengths and scope boundaries

- Both root and product requirements arrays independently canonicalize to
  `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`,
  with revision 1 and exact H01-H15. The active transfer names the assigned
  generation-2 director. No human requirement or formal card was amended.
- The command keeps `R02=not_run`, `formal_acceptance=false` and incomplete
  hardware/calibration/model/runtime gates. Successful empty device lists are
  correctly scoped as query observations. The current missing-package states
  concern this interpreter only and make no accelerator/runtime claim.
- Code inspection supports metadata-only distribution lookup, strict JSON
  parsing, typed group validation, exclusive output creation before collection,
  and no target-backend imports. No new concrete defect was found in those
  scoped paths. This does not replace full runtime or formal acceptance.
- Hash-verified author logs show 14 deterministic tests passed in 0.055 seconds,
  exit 0, at these exact four file hashes. The independent review did **not**
  rerun that suite. Fresh `verify_review.py` finished exit 0 in a hidden,
  below-normal process with a 30-second cap; it audited diff reconstruction,
  candidate and receipt hashes, contracts, saved live semantics, current
  protected-file hashes, and two focused synthetic boundaries only.
- The four protected C dirty-file hashes still match the saved audit. No fresh
  Git command was run; base and staging state are attributed to the retained
  author audit. No product file, protected byte or evidence failure was edited.
- No real CIM, model/backend, board, network, GUI/input, driver/policy/service,
  credential/provider, Git mutation, peer/group operation or further agent was
  used. Only this review folder was written. All 29 formal cards remain
  `not_run`; there is no board, system, model-benefit or product acceptance.

## Evidence

`verification.json`, `verification.receipt.json`, `verification.stdout.txt` and
`verification.stderr.txt` retain the fresh audit. Candidate hashes and author
receipt/log hashes are recorded in `verification.json`. Review helper and
deliverable hashes are listed in `review-hashes.json`. Native validation and
closure are recorded in the original job's `native-*-response.json` files.
