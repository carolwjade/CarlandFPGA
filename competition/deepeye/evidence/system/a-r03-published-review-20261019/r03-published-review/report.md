# Published R03 reference check

Published PR24 HEAD `4523157db12203d127ceb6ae25f2d187e85c9cc9`; implementation source `e7c00d4d7592b2d949a889d0b7ed87b3f649f177`. H01–H15 canonical hash matches the pin.

Full `tools/check_interface.py` executed once. All13 subcommands exited0:246 tests discovered,245 passed,1 intentional nested pipeline skip. The full entrypoint itself exited **2 / blocked**, with full R03 **not_run** and hardware eligibility **false**. This expected incomplete-product status is preserved.

| Subcommand | Discovered | Skipped | Exit |
|---|---:|---:|---:|
| integration/test_wire.py | 11 | 0 | 0 |
| integration/test_motion.py | 9 | 0 | 0 |
| integration/test_host_schema.py | 7 | 0 | 0 |
| integration/test_host_envelope.py | 34 | 0 | 0 |
| integration/test_pc_direct_heartbeat.py | 5 | 0 | 0 |
| integration/test_pc_direct_watchdog.py | 40 | 0 | 0 |
| integration/test_sensor_source.py | 43 | 0 | 0 |
| integration/test_trace_payload.py | 6 | 0 | 0 |
| integration/test_clock_bounds.py | 28 | 0 | 0 |
| integration/test_boot_binding.py | 5 | 0 | 0 |
| integration/test_contract_vectors.py | 3 | 0 | 0 |
| tests/test_boot_profile.py | 30 | 0 | 0 |
| tools/pipeline.py verify --selftest | 25 | 1 | 0 |

The pipeline suite has25 tests after the published ownership-path fix, explaining the one-check increase over prior245/244+skip evidence. All child raw-output hashes match the saved logs. All61 artifact hashes match the actual checkout.

The clean checkout and411 snapshotted files remain unchanged. No default product ledger was created; all29 frozen cards remain not_run. Full register/TRACE/runtime/interop/isolation/measured IO gates remain open as listed in receipt.json. No geometry/UI, old baseline, uncommitted PC adapter, board or live OS-isolation work was run.

Runner-preparation quoting failure is retained separately; it occurred before the entrypoint started. No source, old evidence, service, credentials or external-message effects.
