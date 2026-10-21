# S2: corrected boundary evidence, accuracy gate still open

A new electric-current Green implementation and compatible receiver controls pass. The saved source moments supply tangential Born boundary edge averages; both fixed quadrature pairs pass. One new `-AIB*gB` correction solve reuses the unchanged L5 operator and S1 derivative.

The correction backward error is **1.3843e-15**, below the fixed **2.8422e-14** gate. Corrected receiver discrepancies are **12.6766%** and **4.3707%**, so the unchanged **1%** physical-comparison diagnostic fails. The second receiver improves from S1; this does not establish overall accuracy or a unique error decomposition. This known-source Born boundary is not a generic heterogeneous exterior model.

Main independently checks all 96 author files and 51 source pins, the actual original failed native job, and saved matrix/forcing/residual/receiver arithmetic. Its controls review took 0.375 s and actual-array review 0.625 s, with no Green evaluation, matrix assembly or factorization. All 12 original author process handles are signaled. Exact failures, the original native response, independent design, and review are in `evidence.zip`; `archive-index.json` binds every member. Environment-only public derivatives retain their original local hashes.

Previously completed software, R03 and 384/384 base-overlay board tests were not repeated. Finite-strength heterogeneity, physical noise calibration, G03/R03 and all 29 formal task cards remain open. H01-H15 and requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` are unchanged.
