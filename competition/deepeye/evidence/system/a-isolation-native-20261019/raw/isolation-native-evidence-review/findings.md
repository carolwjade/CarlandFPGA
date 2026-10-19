# Independent review of saved attempt-01 native evidence

The three named CPU fixture outcomes reconcile with their original process
handle readbacks, cleanup records and profile-absence observations. No blocking
inconsistency was found in this saved-evidence scope. This reviewer did not rerun
native operations, reopen a process, probe a profile or read truth canary content.

Work A-isolation-native-evidence-review-20261019-v1; job
`child-a17dc889e3c346bc9306dfe3d17f3f2f`; reviewer `/root/r03_review_20261018`.
Original lease validated execution_allowed=true. H01–H15 canonical requirements
hash remains `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Main retains acceptance/publication. All formal cards remain `not_run`.

## Exact execution inputs and evidence

The live harness equals reviewed SHA256
`2db0dda152a2fdbfd8aff7dcbef6de3d144a920d08532f8ba4900b0fbc8ed613`.
Gate and saved preflight are equal and bind the active generation2 main, source
review, byte bridge and manifest
`21c42710a33a2c1be2355129cfb113e5f23e261571dd8d8a35a2845f38fe7e63`.
All12 current source bytes match that manifest and the saved preflight. Fifteen
additional runtime/supporting source hashes match the gate, including the
unchanged accepted coordinator and original fixture. Runtime binary inputs were
hashed in place only, never copied or executed by this review.

`campaign-result.json` records exactly the three named cases, each one test,
test_passed=true, skipped=0. All three original unittest logs independently show
one test and OK with no skip. The campaign's saved observation/memory hashes
match each original raw JSON file. Case runtime manifests match their recorded
hashes and runtime input pins; staged fixture source matches the original in
normal/save-failure cases and exactly `import time; time.sleep(10)` in timeout.
No sandbox policy was relaxed to produce the results.

The parent supplied official exec session87134 exit0. This review independently
checked on-disk campaign/log outcomes; it did not rerun or requery that shell
session. The receipt explicitly preserves this provenance distinction.

## Three outcomes

| Case / run | Product verdict | Original process readback and cleanup |
|---|---|---|
| Normal / r-b28da98e58a4 | PASS, CPU_P1a_only | PID24092, held handle580; terminal wait0 before one successful close; exit0xC0000008; no launcher termination;24 resources confirmed; profile deletion HRESULT0 and independent absence=true. |
| 100ms timeout / r-907c4422cd96 | Expected FAIL, TimeoutError | PID6860, held handle896; wait100ms=258, wait0=258, terminate0xDEAD succeeds, wait5000ms=0, independent terminal before one close; exit0xDEAD;24 resources confirmed; profile absent. |
| Persistent receipt-save failure / r-ffb7afd7d63a | Expected FAIL, original OSError retained | PID10244, held handle880; wait0=258, terminate0xDEAD succeeds, wait5000ms=0, independent terminal before one close;22 resources confirmed; profile absent. Evidence completeness remains false. |

Each process handle matches the single original successful CreateProcess return,
owned process reference and independent terminal-before-close event. It is closed
exactly once afterward. Every saved resource outcome is confirmed, with no
ambiguous or unresolved reference; the observer's unresolved lists are empty.
Profile names/run IDs are distinct. Exactly one successful DeleteProfile event
per case matches its owned fresh profile; lifecycle and main's separate path-stat
observation both report absence. This is review of the saved actual readbacks,
not an assertion from a new current-OS probe.

Normal/timeout suspended-process inspection confirms AppContainer identity,
zero capabilities, Win32k and child restrictions, Job membership and limits
0x2108 /one process /256MiB /UI0xff. Inheritance remains only the two pipe ends,
with the parent endpoints non-inheritable and the intentionally excluded canary
left inheritable as a positive challenge. Environment has the same five keys.
The save-failure case fails before trusted inspection/resume in the verified
source path; it demonstrates cleanup, not successful token/mitigation attestation.

The normal exit0xC0000008 is the already-reviewed strict-invalid-handle protocol,
not exit0 relabelled as success. Raw fixture stdout contains ordered
positive_controls, boundaries, then excluded_handle_attempt for the excluded
handle. CPU arithmetic result23 and authorized pipe controls pass first; truth
path and all five parent-process access attempts return access denied5. The
expected fatal handle probe follows those records under strict_handle mitigation.
Only that narrow order and native status support the fatal-denial verdict. No
truth file content was opened by this reviewer. Recorded last-error122 on a
successful native return is preserved prior error state, not a failed close.

## Persistent-save failure and stale receipt

The save-failure receipt is an earlier snapshot: it has no PID, verdict, finish
time or final lifecycle. It is preserved and never promoted to a final result.
`main-returned-memory.json` supplies the final failed result: original
`OSError: intentional persistence failure after process creation`, resources
complete, no unresolved owners, evidence_complete=false,50 audit errors and52
evidence errors. The separately saved expected-persistence-failure memory JSON
equals this returned-memory object. Raw receipt and memory hashes are recorded
separately. The fixture test passes because this failure and safe cleanup were
expected; product verdict remains false. Timeout likewise remains a product
failure despite its passing cleanup test.

## Review integrity and limits

`verify_native_evidence.py` performs only file/JSON/hash reconciliation and
literal protocol checks, without importing Win32 or launching fixtures. It
records47 exact source/evidence files plus15 supporting runtime/source hashes,
then rechecks evidence stability. `evidence-hashes.json` and
`supporting-source-hashes.json` name the exact inputs; `verified-cases.json` and
`receipt.json` contain concise reconciled outcomes. The verifier exits0.

An initial verifier assertion expected LF-only unittest log separators. Actual
Windows raw logs use CRLF. Original failing logs are preserved as
verify-attempt-1.*.log; only the review's text interpretation was corrected to
normalize CRLF before matching. Native evidence/source was untouched and no
native test was rerun. All hashes continue to bind the original raw bytes.

These are actual saved outcomes for exactly three CPU fixtures. They do not
establish four-product-process isolation, GPU/ROCm/UI capture, meaningful live
AI, live game/control chains, G03, R03, board or all29-card acceptance. No source,
old evidence, service, credential, board, publication or formal-ledger change
was performed. Only this new review directory was written.
