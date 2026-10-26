# A bounded-reader collector derivative

A owns `competition/deepeye/tools/diagnostic/a_b56_memory_safe_collector.py`.
Its upstream is B collector `collect_private_diag.py` at tested origin
20321845e0913151c1ad879908cb9f8af76ac052, SHA256
0b5fbdb9016eca5858cb1945068bd356d4d84ab7a032c8f5e567131414364384.
The separate A file changes only `f.read(limit + 1)` to
`f.read(stat.st_size + 1)` after the existing validated file-size checks.
Reversing that expression restores every upstream byte. Capture, runtime,
snapshot, total limits, path/identity checks and STOP behavior are unchanged.
B retains ownership of its original source and canonical fix task.

A new focused local proof observed the upstream request of 268435457 bytes
for a five-byte input; only that allocation-budget case failed, with seven
filesystem controls passing. The corrected source requested six bytes and
passed all eight cases. Both original Python process handles were waited;
their Job cohorts were empty and all six native handles closed. The ReadSpy
caps forwarding to avoid the oversized allocation in the host test; this is
an actual call-argument proof, not a physical ARM memory guarantee.

Run the committed probe with an absolute collector path and a fresh case root:

```text
python -I -B -X utf8 competition/deepeye/tests/diagnostic/bounded_reader/reader_budget_probe.py --collector ABS_COLLECTOR --phase corrected --cases ABS_NEW_CASE_DIR
python -I -B -X utf8 competition/deepeye/tests/diagnostic/bounded_reader/verify_output.py ABS_RAW_STDOUT corrected
```

The probe preserves all fixtures, uses a non-main import and never imports
PYNQ or constructs a runtime. The independent output verifier does not replace
the actual process exit receipt. The committed proof files exactly match the
released evidence source. Do not rerun the old broad software or 384-board suite.

Raw local evidence is retained in the director's original repository under
`.planning/deepeye-resume-20261018/a-b56-bounded-reader-20261026/`:
`local-runs/red`, `local-runs/green`, `proof-source`, `runtime-review`, and
`root-reader-patch.json`. Red PID26664 exited1 as intended; green PID33228
exited0. This source node precedes a distinct Q2 ARM offline qualification and
a separate physical request; neither hardware success nor final acceptance
follows from the local proof.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1 and all H01-H15/full H12 remain
unchanged, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
G03/R03/all29 remain not_run absent their named evidence.
