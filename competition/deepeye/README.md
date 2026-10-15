# DeepEye implementation

Implementation task `DEEPEYE-IMPLEMENTATION-20261014`, version 1. The approved design is commit `1011259415a0916054eb580687612580bc1e5f09`, taskbook version 5, technical revision 1, in `../../docs/competition/deepeye-2026/`.

Every worker first verifies `DEEPEYE-HUMAN-LOCK-20261014/revision1`: canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. H01-H15 are mandatory. No implementation or timing decision may remove them.

This initial checkpoint provides the A-owned project/resource boundary and prerequisite records. All 29 product acceptance cards remain `not_run`. Simulation, engine startup, exported UI, synthesis, implementation, board IO, AMD inference and formal task success require separate evidence.

- `docs/resource_contract.json`: A/B scene names and file ownership; project and exports have one A writer.
- `docs/rules.json`, `docs/requirements_trace.csv`: verified saved rules mapped to implementation cards; current online refresh, ROCm project execution and physical-task eligibility are separate gates.
- `hardware/environment.json`: current read-only A host inventory; device presence is not inference execution.
- `simulator/`: Windows Godot application. The required engine is 4.7.2-stable with matching templates. Engine hashes and greybox checks are recorded under evidence; those checks do not certify the final game or physical runtime. The initial scene has controls disabled until the authoritative bridge is ready.
- `integration/wire.py` and `motion.py`: bounded ABI3 byte framing and quantized curvature references. These do not authorize motion or inspect world geometry.

Run `python tools/check_interface.py --reference-only` for the implemented software reference checks and exact per-suite results. The full `python tools/check_interface.py` intentionally returns `blocked` with exit code 2 until the remaining R03 gates have evidence. The motion vectors cover the frozen STRESS `(57,0)/(58,0)` and `(40,40)/(41,41)` boundaries, zero-speed turn rejection, both speed profiles and acceleration scaling.

A owns public schemas, orchestration, simulator authority/physics, and all board operations. B owns FPGA/codec and world/assets. C owns PC AI/planning and control broker. Neither B nor C connects to the board. See the frozen taskbook section 9 for the full path map and section 10 for evidence and execution requirements.

Release directory mapping: `docs` covers system/report documentation, `fpga` the programmable logic, `ai_pc` the host model/application, `hardware` physical setup, and `evidence` raw validation outputs. Final `metrics`, deployment and offline release artifacts will be accepted under A04/G08.

The PC_DIRECT STATE8 heartbeat now has an independently reviewed stateful stop gate in `integration/pc_direct_watchdog.py`. It conservatively expires health, latches faults and clock/order violations, and never extends a command deadline or supplies observations. `sensor_source.py` validates the causal source boundary with shared monotonic receiver time. `test_trace_payload.py` keeps unfrozen TRACE payloads quarantined; the missing B codec/C interoperability and register definitions remain full R03 gates. See the corresponding documents in `docs/`.
