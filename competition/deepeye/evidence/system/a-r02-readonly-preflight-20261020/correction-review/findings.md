# R02 correction 1 independent final candidate review

Specification verdict: **PASS for Task 1, with the main's explicit JSON-equivalence
adjudication**.

Code-quality verdict: **PASS within the four-file preflight scope**.

Final scoped recommendation: the exact four-file correction candidate is ready
for the responsible main's adoption decision as a read-only inventory tool.
No blocking or additional actionable defect was found in the reviewed change.
The main alone accepts, integrates and publishes. This is not formal R02,
accelerator, calibration, model-benefit, physical-board or product acceptance.

## Review identity and completeness

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work
`A-R02-PREFLIGHT-FIX1-INDEPENDENT-20261020-v1`; original new native job
`child-92ad27ad88fa4d9db393b239dc66d590`, validated before work against canonical
agent `/root/r02_preflight_independent_20261020`.

The whole-plan base remains `f1d8c6d37bf6e17b3b0b92dc4998a4c7f8959bbe`
plus these four uncommitted candidate files. Fresh verification reconstructed
the frozen v1 files from the initial complete diff, verified their original
review hashes, and applied every supplied correction hunk with exact context
and old/new line-count checks. The resulting four files equal the current
candidate text; current byte hashes equal the author green/live before/after
hashes. No unaccounted change exists within these four candidate files.

| File | Exact SHA-256 |
| --- | --- |
| `competition/deepeye/tools/preflight.py` | `94d574a5e6c742fb4948df65e3e9fdfb1137f950ab1b8798317aed1423a7786b` |
| `competition/deepeye/tools/preflight_windows.ps1` | `f1af74889d292b1bacfdc1542e81a14fd0b9cfc01bfb8d02d890d3f75a5599ca` |
| `competition/deepeye/tests/test_preflight.py` | `a0b4e8b02452647d474e135773cd60b2220e963517dc2f43deb20521347bffc2` |
| `competition/deepeye/hardware/preflight.md` | `766283e8bcf090c010c80323526ed3a27a91e7b35fa5114469fa56981db5925f` |

## Findings disposition

**F1 resolved.** `preflight.py:175-180` now supplies the exact fixed collector text
as the final `-Command` argument. The main reads source bytes once with a 1 MiB
bound, decodes strictly and hashes those same bytes before passing that text.
The complete delta adds no script-path invocation, policy flag/settings change,
fallback retry, user command or extra Popen site. The original hidden/below-normal
flags, bounded pipes, 20-second timeout and owned-process cleanup remain. The
saved successful-path receipt and typed observation now substantiate the host
inventory path at these source hashes; the original UnauthorizedAccess failure
is retained unchanged.

**F2 resolved under the explicit main decision.** Documentation now promises
the same JSON object, explaining platform stdout newlines versus the UTF-8 LF
file. The StringIO test no longer asserts a false byte guarantee. The new real
stdout/file pair independently parses to the same JSON object and differs only
by outer CRLF/LF newlines. The two raw hashes are correctly separate:

- CLI stdout: `502c79858308e3f339fcbddac03f6b93fa1f332ecb4e5b98973ef72e99552341`.
- Optional file: `1b9cb19a30e09cb5c9beb7ffab15afeea1672ee10cef8fe8ecc853b7ff03c8f6`.

Exclusive output creation and refusal before queries were preserved. This review
does not silently substitute byte equivalence for the main's chosen semantics.

**F3 resolved.** Both executable matchers and the documentation remove the
unsourced `DEV_17F0` ID-only rule. Tests now reject an unnamed device with that
ID and a `DEV_15020` near match while retaining whole-word NPU/Neural/IPU and
the observed `VEN_1022&DEV_1502` prefix. A name independently matching the
meaningful tokens may still be a candidate, as intended. Candidate selection
does not assert tested accelerator support.

**Diagnostic observation addressed.** Documentation now explicitly describes
UTF-8 replacement decoding and its possible loss of original child bytes,
including that saved raw CLI output cannot recover the earlier child stream.
The main intentionally requested this accurate limitation instead of a new
diagnostics framework. The known limitation is not a blocker for this scope.

## Evidence and regression assessment

Author raw red/green/live streams and receipts were independently hashed. The
new red controls report 16 tests, exit 1, four failures and two errors against
the earlier implementation. The corrected green log reports **16 tests passed
in 0.050 seconds, exit 0**. These are saved author executions, not reruns here.

The added tests meaningfully constrain one bounded source read, strict UTF-8
and source-size rejection before a process starts, reported hash versus exact
final command text, exact fixed command options and a single invocation, the
two ID false positives and selected JSON-equivalence semantics. The original
contract forgery, metadata errors, JSON/typed-group failures, exclusive-output,
unsupported-platform and timeout controls remain in the complete candidate.
No new target imports or framework/integration changes were introduced.

The retained new live receipt records exit 0, no timeout and hidden/below-normal
outer flags; its source hashes match both green and current candidate bytes.
Its observation timestamp is `2026-10-20T06:45:31.2976419Z`. Fresh pure validation
of that saved object returned no inventory errors. Counts are CPU 1, OS 1, GPU 2,
NPU candidates 1, corresponding signed drivers 3, fixed local disks 2. Driver
device IDs correspond exactly to the saved GPU/NPU observations. Selected
package metadata is complete in the recorded interpreter; no runtime/model
support is inferred. The collector digest equals the current fixed PS1 hash.

Fresh `verify_review.py` completed exit 0 under a hidden/below-normal process
with a 30-second cap. It performed byte/diff/receipt/contract checks and pure
validation of saved observations. It ran **no synthetic experiment, test suite,
real CIM collection, target package, model/backend or accelerator operation**.
`verification.json` and its raw streams/receipt retain the checks.

## Preservation and acceptance limits

Both root and product requirements arrays recompute to
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`,
with revision 1 and exact H01-H15. The active transfer retains the sole
generation-2 director. Public historical evidence named by the author receipt,
the original review manifest, historical environment and the protected C dirty
file hashes still match. Private lease/reservation files were not reread or
included in this review's public hash list. Original author correction closure
is completed/terminal with result text equal to its final-result.txt.

The base and staging state are attributed to the retained author Git audit;
no fresh Git command or unrelated branch crawl was performed. No product bytes,
old failures, cards or historical evidence were edited. Only this new review
folder was written. No GUI/display/input, network, peer/group, install, policy,
service/driver, credential/provider, board or further-agent action occurred.

`R02=not_run`, `formal_acceptance=false`; all 29 formal cards remain `not_run`.
Physical-board, calibration, ROCm-project, NPU-runtime and trained-model-benefit
gates remain `not_run`; device compatibility remains `unknown`. Provider-reported
AdapterRAM is not a validated VRAM measurement. The successful inventory is an
observation at its timestamp, not a compatibility or product-readiness verdict.
