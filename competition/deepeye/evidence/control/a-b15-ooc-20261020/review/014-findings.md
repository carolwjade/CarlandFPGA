# Independent B15 OOC synthesis audit

**Source/export evidence: PASS within the exact pinned B15 OOC scope.** The
successful original fix2 synthesis and its artifacts are supported. The one
independent checkpoint read opened and emitted consistent native reports, but
its **review harness exited 1** on an invalid fileset-TOP assumption. That
failure is preserved; no second native attempt was made. Main alone accepts.

Review work `A-B15-OOC-SYNTHESIS-INDEPENDENT-20261020-v1`; original job
`child-58299e747e5d461d968856af2c562567`; agent
`/root/r02_static_dependency_review_20261020`.

## Exact source and original runs

All **47** frozen public input files were hashed against
`background-synthesis-main-20261020/synthesis-public-inputs.json`, before
and after review. Local Git `cat-file blob` independently confirms all three
snapshots against **df82af1bc91d01aeb9adee19f48c0890dfc1ac5b**, including
their Git blob IDs, lengths and SHA256. No Git write or fetch occurred.

| Source | SHA256 |
| --- | --- |
| deepeye_atomic_pwm.sv | 9dc8ecf96e59a2ae8467bda64572f62eb602d52db535733f236f64ff97c43428 |
| deepeye_pwm_coherent_capture.sv | 4baddfc31248c49000c00ac74bc2319cef6c9016c7df3f1822030c69cd82f456 |
| deepeye_pwm_applied_capture.sv | d8c33ebad98acca113e18dbc5831643646663b946714af139d8b1637047356f3 |

The target is `deepeye_pwm_applied_capture`, `xc7z020clg400-1`, default
COUNT32/WITNESS64/TAG32. The source header, generated Verilog declarations and
native checkpoint ports agree on **43 logical ports / 798 bit-level ports**.
This is an internal module, not a package-pin/public-ABI declaration. The
newer B operation16/source state is outside this review's source conclusion.

| Original A batch | Actual exit | Meaning |
| --- | ---: | --- |
| initial | 1 | synth_design completed; incorrect comparison of design NAME to HDL top failed the A harness |
| fix1 | 1 | identity/utilization/DRC emitted; checkpoint exporter rejected the junction root |
| fix2 | 0 | exact single PASS marker, DCP/netlist/facts/utilization/DRC present, no error lines |

The source hashes are identical across these runs. Fix1 records fileset TOP
separately from design NAME; fix2 exports under a real `artifacts` child.
Both original failed batches and their missing outputs remain preserved.
The Python runner's own exit0 is not a batch-pass result; the JSON batch exit,
native log, exact marker and output artifacts govern the verdict.

Original runs used suspended creation, private-job assignment before resume,
hidden/below-normal flags, maxThreads1, 4 GiB committed-job cap and their
original **240-second** deadline. Observed peaks were below that cap. Their
65.625/50.016/47.937-second durations are not reclassified as 50-second runs.
No completed synthesis runner was rerun.

## Checkpoint and resource evidence

The full retained DCP passed stdlib ZIP CRC checks. The one native readback
used the original fix2 DCP, Vivado 2026.1, one thread, CREATE_NO_WINDOW/SW_HIDE,
below-normal private job, **50 seconds / 4 GiB**. It ran **25.344 s**, peaked
at **1,782,493,184 committed bytes**, and timed out false. It performed one
open_checkpoint and no synthesis, implementation or board operation.

Native reports independently identify `deepeye_pwm_applied_capture`, part
`xc7z020clg400-1`, **2397 hierarchical cells**, **0 blackboxes**, **0 latches**,
**0 clock objects**, and the exact 798 port names/directions. Utilization is
**842 LUTs, 1117 FFs, 0 RAMB36/RAMB18/DSP**; hierarchy totals agree with the
original report. All native input bytes, including DCP/harness/Tcl, stayed
unchanged. `static-review-result.json` and `readback-report-audit.json` retain
the independent checks and raw command/exit evidence.

**Reviewer harness defect:** `readback.tcl` tested fileset TOP after opening
a standalone checkpoint. Here that property is empty; current design object
NAME is `checkpoint_synthesized`. The native utilization report's Design and
hierarchy identify the correct HDL top. The assertion therefore failed after
all useful reports were written. The raw result remains **batch exit1** and
`native_end_to_end_harness_pass=false`; offline report verification is exit0.
For a future separately selected harness, use the native netlist/design-top
identity appropriate to standalone DCPs instead of assuming fileset TOP is
populated. No second open_checkpoint or retrospective PASS marker was created.

The private job's residual member was explicitly terminated, followed by
kill-on-job-close. A narrow check found no existing process for the owned root
PID. No unrelated process was queried or terminated. The sole authorized ASCII
junction is retained, pointing to this review folder; it is not a source copy.

## Every warning remains qualified

- Five **Synth 8-6014** warnings remove procedural temporary elements:
  witness_now, rise_mask, fall_mask, elapsed and coherent_candidate. At
  coherent-capture source lines 230/233/234/272/300, blocking assignments
  calculate local values before same-process use. Removal of their unused
  inferred sequential forms is consistent with this source structure; this
  synthesis observation does not independently prove RTL behavior.
- **DRC 23-814** states that not all connectivity DRCs may run for OOC designs.
  It appears in fix1/fix2 logs and cannot be turned into complete connectivity
  acceptance.
- The DRC report contains **ZPS7-1, Warning, PS7 block required**. The isolated
  PL module lacks the integrated Zynq PS7 block. This is consistent with its
  OOC scope, but is not a warning-free system/board DRC result.

The independent checkpoint-opening log emitted no warning lines, but that
does not erase these original synthesis/DRC warnings. There is no clock
constraint and zero clock objects; timing/frequency, CDC/RDC, implementation,
pin integration and board behavior remain **not_run**. No achievable-rate,
physical timing or functional-validation claim follows from resource counts.

No source/export defect was found in the pinned result. Review development
failures are also retained: an offline port regex initially rejected legal
`[31:0]name` syntax, and a pre-native check initially confused the VBS launcher
hash with vivado.bat's hash. Both were corrected before their successful
corresponding check; the latter created no native process. The single actual
native readback's TOP assertion failure remains separately failed.

H01-H15 canonical SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`
and the sole active generation-2 A director were verified. All29, G05/B06/R03,
timing/frequency, CDC/RDC, implementation and board remain `not_run`.
Only the owned review folder and explicitly authorized junction were written.
No install/network, product/source/Git mutation, service/driver, board,
GUI/display/input, peer/group message or further agent operation occurred.
License configuration was consumed internally; no license content was copied
or printed. Main retains acceptance and any future experiment decision.
