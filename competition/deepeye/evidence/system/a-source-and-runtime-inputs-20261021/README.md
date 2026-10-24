# Actual source diagnostic and complete runtime inputs

The new G03 source/voltage implementation uses the installed compatible edge
basis, a discrete Stokes source projection, and an independently implemented
homogeneous conductive/displacement Green-loop reference. Two new control groups
passed. One actual 8-cell solve reused the accepted A/C/W_B and boundary vectors;
no old full48 sampling or control suite was repeated. All nine held process
objects across the retained failed preparation and successful stages terminated.

The diagnostic identifies a real inadequacy: all six interior source entries
are exactly zero on this grid. The eight nonzero projected entries lie on the
prescribed boundary, so the interior solve is boundary-driven. Near/far receiver
voltages differ from the independently calculated reference by 93.4164479% and
78.7469019%. The 1.4124006246694593e-16 backward residual passes its unchanged
128eps gate, but physical accuracy fails. Reference 64/128 differences are
1.27354e-15 / 7.69624e-16 V; this is observed quadrature consistency, not a
rigorous physical error bound. The 56-file author manifest and source/basis
review preserve that distinction. A new internally resolved grid is separate.

All 17 selected runtime wheels are now complete. The last five AMD objects
(gfx110x, core, gfx1103 device SDK, libraries and torch) total 1,287,395,534 bytes.
Each succeeded in one HTTPS GET and one current whole-archive streaming check.
This round needed no tail reconstruction or retry. Their CRC/RECORD/member size,
METADATA and platform tags matched; main independently rehashed the five files
and 101 evidence/source records. All 25 held objects across ten stages stopped.
These newly computed full hashes are not published vendor digests. Twelve prior
successful package records were reused; the earlier gfx1103 curl56 failure and
its separately completed same-object reconstruction retain their original states.

An offline isolated installation and one actual AMD backend check are selected
in a separate task. This checkpoint records complete inputs, not an installation,
GPU kernel, supported-8845H, project CNN or performance result. No driver, global
environment, board or production process changed in the archived operations.

The first new-grid worker hit provider capacity before writing implementation or
running science. Its native job is failed/terminal with zero owned processes;
a separately leased gpt-6-sol worker continues in another directory. The failure
is preserved and is not a completed numerical job.

Public archives exclude vendor wheels, private leases and full environments.
Environment-removed records carry original local hashes; every ZIP member's bytes
and CRC were checked during packaging. H01-H15 and canonical requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 are unchanged.
Formal R03, complete H12 and all29 task cards remain not_run.
