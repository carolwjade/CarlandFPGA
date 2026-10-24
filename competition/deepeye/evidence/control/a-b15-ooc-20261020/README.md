# A independent B15 OOC synthesis checkpoint

Exact B source `df82af1bc91d01aeb9adee19f48c0890dfc1ac5b` was synthesized
with Vivado 2026.1 for `xc7z020clg400-1`, top `deepeye_pwm_applied_capture`,
default COUNT32/WITNESS64/TAG32. The third original batch exited 0 and exported
the DCP/netlist and reports. The first two harness failures remain archived.

Independent source/byte/report review supports **842 LUTs, 1117 FFs,
0 BRAM/DSP and no blackboxes/latches**. One independent native checkpoint
open generated matching reports, but its final fileset-TOP assertion exited 1:
that property was empty for this standalone checkpoint. This is retained as
a failed readback harness, not an end-to-end PASS. No native run was replayed.

Five Synth 8-6014 warnings, incomplete OOC connectivity checking, and ZPS7-1
(PS7 block required) remain visible. There are zero clock objects and no
clock/pin constraints: these counts prove no frequency, CDC/RDC, implementation,
board or system result. G05/B06/R03/all29 formal acceptance stays `not_run`.
H01-H15 and canonical requirement hash are unchanged; see `summary.json`.

`archive-manifest.json` maps byte-identical files to original repository-local
evidence paths. The 47 synthesis inputs and 43 public independent review files
are included, plus both original manifests. Three runtime/assignment records
listed in the review manifest are deliberately not exported. Review job
terminal/result equality was checked locally by the main before publication.
No private leases, credentials, license contents or compiler caches are exported.
Archived scripts retain original context-dependent paths; they are evidence,
not a portable command that authorizes rerunning the experiment.

All runs were hidden/below-normal with private process jobs. Synthesis used
one Vivado thread, 4 GiB and a 240-second deadline; independent readback used
50 seconds/4 GiB. Resource limits and observed durations remain distinct.
This checkpoint adds evidence only; it does not integrate B RTL into A product
sources or replace the latest B handoff review.
