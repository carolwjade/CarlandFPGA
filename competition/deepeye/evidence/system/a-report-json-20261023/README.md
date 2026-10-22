# Strict scientific report serialization

A new optional-NumPy scalar helper serializes strict UTF-8 JSON before exclusive creation. It rejects unsupported values and nonfinite numbers without creating a file and preserves existing evidence. Actual disk write failures can still leave a partial new file and must be retained.

Four new regression tests passed once with real NumPy (0.023s test time); the legacy writer failed the same new fixtures as expected. The hidden guarded GREEN stage took 0.328s, peaked at 22,339,584 bytes, and all three held processes terminated. Independent source and raw evidence review is included. No old solver, model, UI or board test was replayed. Original candidate audit/solver failures and G03/R03/all29 acceptance remain unchanged.

Archive: 26 indexed members; SHA256 90b2d83116a05e9abf436ec077f4a1ba6b4d78c613dd79c957d959f475d8c09b. Private leases and raw native completion wrappers are excluded; terminal allowlist evidence is included. Historical attempt sources are immutable. The new helper is used by new callers only.
