# Process-image label clarification

The original raw report in raw/001-findings.md called held members51256 and
22952 the console and worker. The saved receipt does not record per-child
image identities, so those two labels were unproven. The README is corrected
to the actual evidence: launcher22092; held member objects22092/51256/22952,
all signaled, exit0, job active0. No process-image assignment is inferred.

The original raw report, tests, source, receipts and failures remain unchanged.
This is a documentation correction only; no test was replayed or relabelled.
Bounded parser conclusions and all29/R03 not_run remain unchanged.
