# Off-axis 3D material-response derivative S1

S1 now produces a nonzero conductivity-and-permittivity response for a compact
3D inclusion and tilted finite transmitter/receiver loops. Its independent
infinite-background magnetic-flux reference passes the selected quadrature
checks. The solved derivative differs by **12.3700174% and 22.2620609%** at the
two receivers, so the fixed **1% accuracy screen fails**. Physical accuracy,
finite-strength heterogeneous response and formal G03 acceptance remain open.

The experiment reuses the saved L5 operator and solves one new material-response
right-hand side at zero contrast strength. It does not reconstruct C or A, rerun
the old total-field solve, or repeat completed runtime/R03/board baselines.

## New execution and independent review

- Original controls failed during Geoana's unconditional Matplotlib import,
  before any numerical checks. All original processes terminated. The original
  29-file evidence set and failed native result are preserved.
- A separate selected continuation changes only its work ID and stage-local
  cache/temp environment. Five scientific/test/worker source files are byte
  identical. The original RED is reused.
- New geometric, three-component receiver-trace, complex material and Green-H
  controls pass. The contrast occupies 64 cells and 300 supported edges.
- New independent H-flux integration passes: relative Born quadrature changes
  are 3.4065e-5 and 5.5180e-8. Primary E-line versus H-flux differences are
  approximately 1.08e-15 and 5.90e-15. The oracle's attempted old-operator read
  is actually rejected. This is in-process audit evidence, not an OS sandbox.
- One COLAMD factorization and one new RHS solve finish in 55.547 seconds with
  peak job memory 3,346,661,376 bytes. Backward eta 2.228706729e-18 passes the
  fixed 128-epsilon screen. The process exits 2 because the separate physical
  comparison screen fails. All nine held processes from the three stages stop.
- Main independently checks 123 source/evidence files, both failed native
  terminal responses, the unchanged scientific sources, complex forcing,
  residual in a separate sparse traversal, compensated receiver reductions and
  H-flux reductions from saved arrays. It performs no Green evaluation, matrix
  assembly or factorization. Two review-harness mistakes and their originals
  are included; the final independent review succeeds in 0.547 seconds.

| Receiver | Solved derivative, V | Independent derivative, V | Absolute difference, V |
|---|---|---|---|
| 1 | 3.1953266595e-11 + 1.4198336220e-10 i | 3.6462161105e-11 + 1.6202638781e-10 i | 2.054392868e-11 |
| 2 | -1.1292620076e-12 - 5.0171939346e-12 i | -1.4542434057e-12 - 6.4536244833e-12 i | 1.472734066e-12 |

Both native jobs are terminal `failed`; the first records a harness import
failure, the second records a completed numerical result failing its accuracy
screen. Failed native responses contain `result: null` and the actual error;
the exact submitted local report is preserved separately. Queue/completion
status is never promoted to physical acceptance.

## Limits and next dependency

The selected zero secondary tangential boundary is approximate. A new targeted
design must distinguish boundary bias from receiver/source/interior discretization
before choosing further solves. S1 is a derivative at zero contrast strength,
not a finite-strength or arbitrary heterogeneous solution. Source noise,
calibration, strong contrasts, independent full-case qualification and product
sensing remain incomplete. Residual size does not establish physical accuracy.

No product sensing, motion authority, C model, private IPC adoption, service,
GUI or board state was changed. All H01-H15 remain fixed under
DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
All 29 formal acceptance cards remain open. Feishu 21001 remains a separate
previously observed communication blocker; no new retry or replay is part of S1.

The ZIP contains exact selected sources, arrays, reports, terminals and main
reviews. JSON records containing inherited environments are published as
explicit derivatives with their original local hashes. Private leases,
tokens, private arguments and vendor binaries are excluded. Archive member
bytes and CRC are checked before the exact Git blobs are published.
