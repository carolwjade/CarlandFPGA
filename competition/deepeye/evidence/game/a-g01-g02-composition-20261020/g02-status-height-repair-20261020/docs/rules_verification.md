# Frozen rules and trace checks

`tools/check_rules.py` supplies the R01 taskbook check entrypoint. It reads the
existing `rules.json`, `requirements_trace.csv`, immutable human scope and exact
original `amd_guide_20260831.pdf` bytes. It performs no registration, network,
model, hardware or file-write operations.

From the repository root:

```powershell
python -B competition/deepeye/tools/check_rules.py
python -B competition/deepeye/tools/check_rules.py --reference-only --source-pdf C:/explicit/path/amd_guide_20260831.pdf
python -B -m unittest competition.deepeye.tests.test_check_rules -v
```

The default PDF location is
`docs/competition/deepeye-2026/sources/amd_guide_20260831.pdf` within this checkout.
If that checkout does not contain the original, an explicit `--source-pdf` may
name an existing read-only source. The checker reports whether the source is
inside the checkout. It never searches other workspaces, downloads a replacement
or treats the metadata's hash claim as evidence that the PDF exists.

The pinned source SHA-256 is
`c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc`.
The policy table fixes the previously reviewed mapping of 15 official rows,
five core metrics, the two selected specialist metrics, file page numbers and
task owners. It checks cross-file consistency and H01–H15 canonical hash
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` under
`DEEPEYE-HUMAN-LOCK-20261014/revision1`. A changed source or changed mapping needs
a new review. These checks do not reread the PDF's semantics or establish the
current organizer's interpretation.

The five section 3.2 weights are fixed separately: system completeness 20,
PC AI 20, FPGA quality 25, cooperation 20 and engineering innovation 15.
Their total must be 100, with exactly these categories and integer values.
Another 100-point distribution, missing weights, extra categories or floating
point/string/boolean replacements fail the reference check. A metadata claim or
weights copied from another section cannot substitute for this pinned mapping.

Input reads are bounded to 1 MiB per metadata file and 32 MiB for the PDF.
Duplicate JSON keys, nonfinite numbers (including exponent overflow), malformed
CSV, missing or duplicate requirement coverage, changed owners/pages, invalid
types and inconsistent declared statuses are rejected. The output includes the
actual input hashes, source result, declared gates and remaining obligations.

Exit codes:

- `0`: explicitly requested `--reference-only` checks passed, including the
  exact original PDF bytes.
- `1`: invalid, inconsistent or unreadable input.
- `2`: the source is absent or full R01 acceptance is requested. Full R01 remains
  blocked because independent qualification, registration and formal acceptance
  evidence are outside this checker's authority.

`R01` stays `not_run`, `formal_acceptance` and `hardware_enable_eligible` stay
false even if a metadata file declares every gate passed. The four declared
gates keep ROCm project evidence, recognition of the proposed physical task,
physical engineering evidence and R01 separate. A reference check cannot close
any of the 29 formal cards, replace the H01–H15 contract or enable a board run.
