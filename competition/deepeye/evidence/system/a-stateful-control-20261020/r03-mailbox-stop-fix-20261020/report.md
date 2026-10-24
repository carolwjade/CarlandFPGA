# Minimal malformed-STOP replacement proposal

Prepared two exact replacement files in `proposed/`; product remains unchanged.
The implementation adds only `@_entry` immediately above `stop()`. Python binds
the original stop signature inside that existing variadic wrapper, so unexpected
keyword, excess positional arguments and duplicate reason binding now call
`_halt('invalid_stop')` and raise ValueError with original TypeError as cause.
Correct calls retain the original body and reason normalization. No slot,
clock, identity, session-cap, lifecycle-vector or other API policy changed.

| File | Original SHA256 | Proposed SHA256 |
|---|---|---|
| candidate_mailbox.py | c30a52d58a6dde7569ea7f55e751ba766d6887e5858e6b84a1229d8de5cbfca0 | 5ca4aafb97f88b3080cc918e38f6c27a462f4caa7af5fa436eeb663f91d3f1d5 |
| test_candidate_mailbox.py | 3213da1b59984d5f368404ee7b523a89d25fdd08ef832bf9dda6e0c7458510af | 7ff79841abbd6aac12b017a486d296ce58335424471379cfb8af2b020aec9f82 |

Focused diffs are `candidate_mailbox.py.diff` and
`test_candidate_mailbox.py.diff`. Main must apply only the two `proposed/`
files to the corresponding product integration paths after independent review.
The mirror is test support, not another proposed product tree.

Actual test methods: original26 retained plus new4, total30. Three new methods
exercise all three malformed bindings in HIL_PC_FPGA and PC_DIRECT. Each checks
STOP latch, cleared pending/observations, caught ValueError/TypeError cause,
refused210ms consumption, old-session activation rejection, old completion
rejection, and a generation3 fresh-session completion consumed at710ms. The
fourth covers default/positional/keyword valid STOP forms in both modes.
Original12 literal timelines in both modes remain unchanged and run as part
of the original mailbox suite. Only this mailbox suite ran; no245/HIL suite.

| Run | Exit | Test methods | Failed subcases | Errors | Owned-tree seconds |
|---|---:|---:|---:|---:|---:|
| red-01 | 1 | 30 | 6 | 0 | 0.719 |
| green-01 | 1 | 30 | 0 | 3 | 0.641 |
| red-02 | 1 | 30 | 6 | 0 | 0.625 |
| green-02 | 0 | 30 | 0 | 0 | 0.641 |

Both RED runs use original module bytes and reproduce six live-after-error
states, each consuming candidate1 after the caught TypeError. Final red-02
and green-02 use the exact same final test hash. Final GREEN has no failures,
errors, skips or prohibited effects. State traces are in each checks.json.

The initial green-01 failure is retained, not relabeled. Its six STOP state
checks passed, but three mode2 fresh-session controls errored because the test
helper retained self.ctx from the first mode and the new test reused literal
session8. `test-fixture-correction.json` records the precise test-only change
to current session+1. Fresh identity, rather than product policy, was corrected.
The final proposed test contains that correction; new-test-methods.txt and
initial-test-proposal.diff retain the initial template/history. A second RED
followed by GREEN establishes the final test's discriminating behavior.

Each worker used the same byte-pinned reviewed win_job/boundary helpers,
suspended assignment before resume, hidden below-normal private Windows job,
30s, four processes, process384MiB/job512MiB, bounded output/tree budgets and
held-member termination verification. Every job ended empty with all three
retained process handles signaled. Receipt commands use the exact existing
venv interpreter with -I -S -B -X utf8. Dependencies/BOOT/schema/wire are real,
loaded from the owned mirror plus the existing pinned import file records;
no mock validator or product module is used as the tested mailbox. The audit
guard is cooperative, not an OS security sandbox; tree quotas are sampled.

All13 original product input files and the26-file independent-review manifest
were rehashed after final execution. Source snapshots and import-file hashes
bind each run. No claims are made about new HEAD-wide testing. Lifecycle vector
SHA256 remains 9759681356a6068b370cda751c51cc5120cda6cfd5b9c901b9c0998c62eed63c.
The reconstructed initial worker script is separately labeled and checked
against the original executions' recorded self hashes; it is not relabeled
as a contemporaneous source snapshot.

This is a proposed local software fix. No product application, Git action,
runtime transport, inference, service, OS configuration, network, board,
driver or GUI/input was performed. Selection remains non-authorizing.
Main owns independent review/application and formal acceptance. R03/all29
remain not_run. H01-H15/generation2 and canonical requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 remain unchanged.
