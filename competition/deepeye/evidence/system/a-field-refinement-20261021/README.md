# Receiver error decomposition and new 3D field refinements

This checkpoint preserves newly completed work and its independent main review.
The existing runtime, R03 software, pipe-read and base-board tests were reused.
No old grid solve or reference integral was repeated, and no display was used.

The fixed diagnostic problem remains a genuine 3D curl-curl electric-field
discretization: a finite 0.05 m radius source loop at 2 MHz, conductivity
0.0005 S/m, permittivity 1.77083756256e-10 F/m and permeability
1.2566370614359173e-6 H/m. Two 0.02 m radius receivers lie 0.3 m and 0.5 m
from the source plane. Frozen finite-loop reference values and all numerical
gates are unchanged. This homogeneous coaxial case is a development reference,
not the full heterogeneous and arbitrary-pose sensor-model acceptance.

## New receiver-local diagnostic

The L4 receiver diagnostic evaluated a Green-function quadrature pair only on
264 previously unevaluated receiver-functional edges. No old boundary integral,
operator assembly, factorization, field solve or reference integral was repeated.
The observed quadrature-pair difference was 1.3110258557874867e-16 V/m, below
the existing 1.967577343353139e-12 V/m consistency gate.

The complex voltage difference was decomposed algebraically into the saved
field difference and the receiver-functional difference. Their magnitudes were:

| Component | Near receiver (V) | Far receiver (V) |
| --- | ---: | ---: |
| Field contribution | 1.3161022531225824e-4 | 2.2502311559189667e-5 |
| Receiver-functional contribution | 2.987800507645454e-7 | 2.5077472382463846e-8 |

The decomposition closed exactly in the saved complex arithmetic. Main verified
all 34 manifest files, original completion, source and independent algebraic
closure. The much larger field term justified further field-discretization work;
it does not establish a rigorous total-error bound or a particular spatial axis
as the sole cause.

## L5 propagation-z refinement

Only six selected z intervals were bisected; L4 XY nodes and disk areas were
unchanged. The new mesh has 24x24x34 cells, 63,250 edges and 54,418 interior
unknowns. New geometry controls passed. Exactly one C/A assembly, one COLAMD
factorization and one RHS solve completed, with the exact operators and source
arrays saved before factorization. No L/U copies were materialized for counts.

The solve finished in 57.641 seconds with peak job memory 3,419,066,368 bytes;
all retained process handles signaled and the final active count was zero.
Its backward residual eta was 5.501251487034391e-17, below the unchanged
128eps64 gate 2.842170943040401e-14. Main independently checked the saved
field partition, CSR residual and transposed receiver-functional arithmetic
without another solve, assembly or reference integration.

| Saved result | Near relative reference difference | Far relative reference difference |
| --- | ---: | ---: |
| L4 | 14.9621% | 11.4745% |
| L5 | 11.1375% | 9.2099% |

L5 receiver voltages are (-3.913117653279418e-7 - 0.0009753705970663088j) V
and (-2.4976380169352687e-7 - 0.00021393015200500015j) V. The observed reduction
does not establish convergence or satisfy the taskbook's physical/noise accuracy
gates. L5's 64-file manifest and original completed native receipt are retained.

## L6 outer-XY attempt

One selected outer-XY refinement kept L5 z and source/receiver geometry fixed,
producing a 28x28x34 mesh with 85,434 edges and 74,682 interior unknowns.
Its geometry checks passed. Exact C/A/AII/source/RHS arrays were saved before
the single selected factorization attempt. The actual run then ended with
timeout/exit124 and produced no solved field, receiver voltage or accuracy result.

The original process terminal records 308.954 seconds total elapsed, despite
the selected 120-second timeout threshold. All three retained process handles
eventually signaled; the final active count was zero and peak job memory was
3,728,248,832 bytes. These records prove eventual cleanup, not a 120-second hard
wall-time bound. The evidence does not separate delayed timeout observation,
native termination and cleanup time. No automatic retry, alternate ordering or
second grid run followed. The failed result and exact arrays remain available
for a separately justified continuation; no new L6 voltage is claimed.

## Remaining acceptance

The reviewed next design selects S1: a nonzero, off-axis 3D admittivity-contrast
derivative using saved L5 background operators and a separate magnetic-field
volume/receiver-flux integral. Source review verified nine design artifacts and
27 source pins. Installed conductivity-only primary-secondary helpers and an
electric-field branch with a sigma-only denominator are excluded. S1 has been
assigned, but its numerical result is not included or claimed here. Its proposed
0.1% quadrature and 1% derivative comparisons are new engineering screens, not
the taskbook's formal noise or physical-error gates. Finite-strength heterogeneous
solutions, boundary qualification and noise budgets remain required. Merely
substituting the analytic homogeneous answer or passing a zero-contrast identity
would not meet those requirements.

Original author sources, arrays, process terminals, failure records and main
reviews are included in the archive. Private leases, inherited environments and
installed vendor binaries are excluded. Environment-stripped public derivatives
carry their original local hashes; the original evidence remains local.

No board overlay, physical capture, runtime provider, UI activation or service
change occurs in this checkpoint. R02/G03/R03, both complete H12 paths and all
29 formal task cards remain open. H01-H15 remain fixed by
DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
