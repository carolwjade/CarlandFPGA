# New work validated without repeating completed tests

This checkpoint preserves three completed increments. Earlier board baseline,
pipeline, PC_DIRECT heartbeat and R03 software checks are reused at their recorded
versions. No new claim is made that those operations ran again.

G03 now has an implemented finite-disk functional W_B and boundary-to-receiver
transfer T. New analytic/matrix controls passed, then one selected 8-cell model
assembled A/C and solved 49 columns in 6.94 seconds. It reused the saved full48
boundary difference instead of recalculating it. Observed voltage changes were
7.266574824975231e-21 and 3.635898391555066e-21 V, with conditional bound
1.453555705290784e-20 V. The largest normalized column residual was
9.13659674250848e-17; kappa2=461.7733816605193 is only a diagnostic. Source and
absolute-voltage equivalence, mesh/domain/continuous-coil accuracy and the receiver
error budget remain open. This fixed-model sensitivity is not G03 acceptance.

B PR30 exact aef19351f1836b23f9a714bc5626db4eb4df98c5 changes two Python
qualification files. Main ran only the 12 new tests and 8 independent diagnostic
cases; all passed. The previous 33 test class bodies were unchanged and were not
rerun. This accepts the bounded Python repair, not the unreviewed op18 RTL campaign.
Feedback was posted once and read back at issuecomment-6310510195 on PR30.

The AMD gfx1103 wheel is now complete: 50,718,246 bytes, computed SHA256
a684f7689d514b20b889c56bb5aa6b137028b8351f3edc4fd4f8c81e81188140.
The first GET failed with curl56 and returned 50,660,462 bytes. A new offline
operation used the previously complete 65,557-byte HTTP206 tail of the same URL,
ETag and AWS version. All 7,773 overlap bytes matched; appending 57,784 bytes
created a new complete file. One streaming validation checked all 5 members,
4 RECORD hashes, CRCs, sizes, METADATA and Tags. Main read the exact terminal result
and independently rehashed the complete file. No request was sent by this recovery,
no code from the wheel ran, and no installation occurred. The failed GET/old partial
remain unchanged; the new hash is not a published vendor digest. Twelve selected
packages are complete; five remaining AMD objects are a separate active assignment.

The archive holds public source, actual outputs and terminal evidence. Vendor
wheels, private lease material and full inherited environments are excluded.
Environment-removed derivatives identify their original local hashes. ZIP CRC and
every member's bytes were verified once during packaging; this is archive integrity,
not another functional test run. New source/absolute-voltage and remaining-package
work is pending outside this frozen checkpoint.

H01-H15 remain DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
R03, complete H12 paths and all29 formal task cards remain not_run.
