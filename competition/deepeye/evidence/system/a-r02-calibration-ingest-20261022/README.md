# R02 offline calibration command

New software intake for four ADC channels and at least eight independent reference levels. `python integration/input_calibrate.py --levels 8` reports not_run without records; explicit records permit bounded offline least-squares calculation. It never touches devices. See hardware/calibration_format.md.

The final 11-test new module passes. Initial missing-command RED and two demonstrated CLI provenance failures are preserved alongside their fixes. Independent initial and delta reviews are completed and root checked exact source identities. No old pipeline, PC_DIRECT, GPU, science or board suite was rerun. Repeated sampling does not manufacture independent levels; ADC rails, analog saturation and unknown states remain separate. ENOB and physical R02/R03/product acceptance stay not_run. No fake hardware/calibration.json was created.

reviewed-evidence.zip preserves selected raw source, test and review bytes; members.json binds each member. Private leases and generated caches are excluded. A generated-cache transcription typo in the reviewer Markdown is documented in main/review-metadata-note.json; the three product source hashes are exact. The unavailable earlier worker remains cancelled with native stop unconfirmed, untouched original directory and no ownership reassignment. H01-H15 unchanged.
