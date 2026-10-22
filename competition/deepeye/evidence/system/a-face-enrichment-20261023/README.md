# Conforming face enrichment: implementation verified, source screen unresolved

The new experimental implementation adds H(curl)-conforming two-cell face bubbles, exact polynomial mass/curl moments, source functionals and deterministic disjoint-patch selection. Independent review confirmed the mathematics, new controls and execution boundary. These are added approximation directions, rather than another evaluation of the previously solved coarse system.

Twelve physical cases passed 114 polynomial and 60 manufactured-source checks, with selection and negative controls. The first GREEN ran once in 1.797s, with a 60,125,184-byte job peak. The original missing-implementation RED and the explicitly recorded control-scale and stdout-only source revisions are preserved. No prior project test or solver was replayed.

One actual indicator evaluated all 113,088 new directions in 2.578s, with a 71,553,024-byte job peak. Its fixed source-functional consistency screen failed: relative infinity difference 0.0012562635425821533 exceeds 0.001. The worker exited 2, all three held processes terminated, source hashes were unchanged and both actual BLAS thread counts remained one. Strict JSON and stdout were fully persisted; this failure is scientific, not a report-writing failure.

The result defines zero enrichment candidates and selects no solve. The source gate stopped selection before its concentration test; zero coverage does not establish a diffuse residual. Gauss4 exactness for the represented cubic current is not a certificate for the physical primary source. Neither source rule is proved closer to the true answer by this pair alone.

Root accepts the bounded new implementation/control evidence and the preserved failed screen. The original failed GMRES info3, earlier malformed report and physical receiver errors remain unchanged. Receiver accuracy, finite-strength/noise/OOD/training, G03/R03 and all29 formal acceptance remain unqualified/not_run. H01-H15 and both control routes remain mandatory. No product model is integrated from this experiment.

Next work should address the newly unresolved source moments under a separately pinned assignment, reusing the saved coarse field, local moments and Gauss4 source outputs. A prospective Gauss8 evaluation has 32,768 new primary targets and 768 source-patch incidences; its resource estimate, new quadrature control and source consistency must be reviewed before execution. No old solver or automatic retry is selected by this record.

Archive: 134 indexed members, SHA256 feb72183fbef7806fe61e55f9d20a1583d6404ea2f40891f13205fd66d18d048. Exact experimental source, original failed screen, design, independent review and root decision; private leases/native wrappers excluded. Reproduction requires the pinned original input layout and scientific environment. This archive does not install a qualified runtime model.
