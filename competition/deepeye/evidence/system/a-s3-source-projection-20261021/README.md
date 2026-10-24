# S3 cell-source projection result

The new dimensionless cell-edge weak-load implementation passed constant/affine
and compatible-charge controls. Fixed cell Gauss2/4 source and source-difference
pairs passed0.001. One new source-difference solve preserved the S2 boundary;
the unchanged1% receiver screen failed at13.3085987173% and3.2110499868%.

Independent review used saved arrays only, including compensated loads/traces
and one CSR residual; it confirmed both arithmetic and the physical-screen
failure. No old Green targets, operators, tests or board operations were rerun.
The original NumPy-bool JSON failure, partial file and failed native operation
remain intact; a separate operation fixed exactly the bool conversion and work ID.

The archive includes the selected design, both author operations, both independent
reviews and main acceptance. Environment fields alone are removed in named public
derivatives; original local hashes are recorded. Known private lease tokens are
excluded. ZIP CRC and every member byte/hash were checked before publication.
This diagnostic does not isolate the remaining model error or qualify G03,
noise, finite-contrast sensing, R03, hardware or full H01-H15 acceptance.
