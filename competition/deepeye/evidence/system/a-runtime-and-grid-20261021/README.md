# Actual AMD execution and new spatial diagnostics

The selected isolated CPython 3.12 environment now contains all 17 pinned packages
plus pip 25.0.1. One offline hashed install succeeded. One pip check passed; its
success was reused while later metadata harness failures were corrected. Main
independently verified 121 evidence files and all 17 installed METADATA files
against the selected wheel bytes. Original failed free-space gate, Windows pip
launcher protection, stale sdist-vs-built metadata comparison and missing parser
path remain in their original directories. There was no package reinstall.

One actual probe found AMD Radeon 780M/gfx1103, torch 2.12.0+rocm7.14.1 and HIP build
marker 7.14.60850, with no CUDA build marker. One FP32 4x4 matmul and one sync gave
the exact expected 16 values. No CPU/NVIDIA fallback or architecture override ran.
All26 retained handles across 9 stage trees terminated. This is experimental
current-driver execution, not official 8845H support. The loaded HIP runtime DLL
and API version were not collected. The NumPy-absent warning is preserved; no
unselected dependency was added. A real C-owned project CNN, concurrency and
physical-fixture calibration remain required for their respective task gates.

G03 now has a resolved compatible finite-loop source and receiver implementation.
L1 has 896 cells and 32 nonzero interior source edges. L2 refines centralXY to 2016 cells
and 80 source edges. L3 keeps L2XY and halves every z interval to 4032 cells. Each new
grid had exactly one actual A/C assembly, sparse factorization and RHS. Existing
L1/L2 outputs and reference128 were reused, never recomputed for comparisons.

Relative receiver-voltage differences from the pinned homogeneous reference are:

|Grid|Near receiver|Far receiver|
|---|---:|---:|
|L1|42.8865%|34.3817%|
|L2|42.5216%|34.0351%|
|L3|30.1941%|29.9509%|

All three retained solves satisfy the same 128eps backward-residual gate. The
new boundary quadrature pairs satisfy the unchanged consistency gate. These
checks do not certify physical accuracy or total discretization uncertainty.
Axial refinement materially changes the answer; roughly 30% residual errors mean
the model is still unqualified. These homogeneous cases do not replace arbitrary
3D heterogeneous/off-axis cases or the taskbook sensor/unknown/OOD matrices.
L2's raw inherited L1 label is preserved with a separate interpretation record;
the actual L2 geometry and dimensions are verified. L3's new label is correct.

The original PC_DIRECT, pipe-read, 13 R03 software groups and base-BRAM 384/384
results were reused. No old tests, original board load, driver/service changes,
UI/display actions, production activation or full-model training were performed
by this checkpoint. B register/HWH and C project-model dependencies remain open.

All exact final native results, new source/control/solve evidence and main reviews
are archived. Private leases/vendor wheel payloads/full environments are excluded;
environment-removed derivatives retain original local hashes. H01-H15 and canonical
requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804
are unchanged. Formal R02/G03/R03/C03/H12/all29 acceptance remains open.
