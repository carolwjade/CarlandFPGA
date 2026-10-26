# A bounded-reader collector derivative

A owns `competition/deepeye/tools/diagnostic/a_b56_memory_safe_collector.py`.
Its upstream is B collector `collect_private_diag.py` at tested origin
20321845e0913151c1ad879908cb9f8af76ac052, SHA256
0b5fbdb9016eca5858cb1945068bd356d4d84ab7a032c8f5e567131414364384.
The first A commit 9819c688ec3588e6e8e880f04c70d600a53b3aed changes only
`f.read(limit + 1)` to `f.read(stat.st_size + 1)` after the existing validated
file-size checks. Reversing that expression in that commit restores every
upstream byte. The later metadata correction below is separate. Capture, runtime,
snapshot, total limits, path/identity checks and STOP behavior are unchanged.
B retains ownership of its original source and canonical fix task.

A new focused local proof observed the upstream request of 268435457 bytes
for a five-byte input; only that allocation-budget case failed, with seven
filesystem controls passing. The corrected source requested six bytes and
passed all eight cases. Both original Python process handles were waited;
their Job cohorts were empty and all six native handles closed. The ReadSpy
caps forwarding to avoid the oversized allocation in the host test; this is
an actual call-argument proof, not a physical ARM memory guarantee.

The Reader probe is a historical proof with fixed byte pins. Use an absolute
path to the byte-exact collector extracted from commit
9819c688ec3588e6e8e880f04c70d600a53b3aed and a fresh case root. Supplying the
later metadata-corrected collector intentionally refuses the old hash gate;
this command is not a general regression runner for later source revisions:

```text
python -I -B -X utf8 competition/deepeye/tests/diagnostic/bounded_reader/reader_budget_probe.py --collector ABS_COLLECTOR --phase corrected --cases ABS_NEW_CASE_DIR
python -I -B -X utf8 competition/deepeye/tests/diagnostic/bounded_reader/verify_output.py ABS_RAW_STDOUT corrected
```

The probe preserves all fixtures, uses a non-main import and never imports
PYNQ or constructs a runtime. The independent output verifier does not replace
the actual process exit receipt. The committed proof files exactly match the
released evidence source. Do not rerun the old broad software or 384-board suite.

Raw Reader evidence is retained in the director's original repository under
`.planning/deepeye-resume-20261018/a-b56-bounded-reader-20261026/`:
`local-runs/red`, `local-runs/green`, `proof-source`, `runtime-review`, and
`root-reader-patch.json`. Red PID26664 exited1 as intended; green PID33228
exited0. The separate Q2 ARM offline qualification subsequently passed with
all24 original snapshots. A physical request then failed at the exact-dict
metadata guard before download/MMIO; zero captures and no STOP claim resulted.

PYNQ3.0.1 read-only observation on the current board proves that Overlay.ip_dict
is pynqutils.runtime.repr_dict.ReprDict, a subclass of dict. Its private entry
is an ordinary dict, with matching fullpath, VLNV, base0x43c00000 and range4096.
The second A correction changes only the outer `type(ips) is dict` predicate
to `isinstance(ips, dict)`. All nested identity/address/range checks remain.
Reversing this second expression restores every byte of the first A commit.
Nine new host component controls reproduce the subclass rejection before the
patch and pass afterward, including specific nested metadata rejections for
wrong fullpath, VLNV, base and range. An unrelated Mapping remains rejected.
The host subclass is explicitly a surrogate, not the PYNQ implementation.

Metadata evidence and actual local process receipts are under the original
repository's `.planning/deepeye-resume-20261018/a-b56-metadata-readonly-20261026/`.
The old /tmp inputs disappeared across a board restart; they are not replayed
or treated as a current-boot qualification. A new operation/request/source
binding is required for the corrected physical attempt. No PL capture, ADC,
freshness, AI,100ms, fullH12 or product acceptance is implied by this fix.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1 and all H01-H15/full H12 remain
unchanged, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
G03/R03/all29 remain not_run absent their named evidence.
