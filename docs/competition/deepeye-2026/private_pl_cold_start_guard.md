# Explicit cold-start guard candidate

This agent-only change implements Root's frozen root-design.md. It is not a physical release. All H01–H15 and full H12/100 ms requirements remain unchanged.

Absent `startup_policy` retains the existing operating/configured100 precondition. An explicit cold policy must contain exactly:

```json
{
  "mode": "root_released_unknown_start",
  "expected_boot_id": "<same exact current boot as context>",
  "expected_manager_state": "unknown",
  "expected_fclk0_mhz": 100.0,
  "runtime_source_manifest_sha256": "9b0646628fef08bca9540a40efaf68f2080c785d090fee51c80b61f0a4c713dd",
  "vendor_download_effects_acknowledged": true
}
```

Numeric clock fields reject bool and nonfinite values. The acknowledgement is a request condition; authority still comes from Root's separately reviewed request/source/activation. The unchanged host supervisor already binds full request bytes, request hash, new source commit and prepared identity; no second activation format or host edit is introduced.

Before image programming, `_startup_preflight` checks current boot/manager/configured clock and nine frozen installed PYNQ source files. Each source must be a unique regular single-link file with the exact size and SHA; reads are bounded, symlinks rejected within the runtime package, and fstat identity/size/mtime/ctime/link count are compared before and after. The explicit __init__ pin is included in that bounded path. This verifies file bytes, not loaded-module equivalence under arbitrary concurrent privileged modification.

The existing fsynced `image_load_started_unknown` now carries observed prestate and selected policy. After exactly one unchanged checked download returns, the agent records return, reads the current boot/manager/configured clock again, requires operating/configured100/same boot, repeats existing overlay metadata checks and fsyncs `post_programming_verified`. Only then can application private-PL MMIO/Bus/START be created. Marker, download or postgate errors preserve the original main's primary/secondary and unknown journal evidence; no retry is added. If no application bus exists, no private STOP success is claimed.

PYNQ's unchanged loader configures PS dividers before firmware programming and can perform internal MMIO, shutdown/global-state/cache/firmware/XRT mutations. `unknown` does not mean empty. Root must preserve selected vendor state bytes and separately release any future operation. The gate is before application private-PL MMIO, not before vendor internal MMIO. A getter-derived configured100 is not a running-clock or latency measurement.

Only agent startup guards and journal fsync condition changed. The pinned collector, codec, host clock, host supervisor, relay/FIFO, stream loop and independent STOP implementations are unchanged. Existing ec6 ARM relay qualification remains exact-source-labelled; Root may reuse unchanged closure only after independent comparison, not call it a new-source ARM run.

## New local evidence

`newtest/test_cold_start.py` executes the actual main programming-boundary AST statements using explicitly labelled fake PYNQ/helper/journal/manager/clock, real frozen runtime source bytes and a fake-MMIO trace. Earlier main CLI/FIFO/context validation and later sessions/STOP are outside this test's scope. It is not full-main, vendor-loader or ARM evidence. Runtime hardlink control uses an actual new local hardlink. The real journal post-marker control observes its fsync call. Source-flow traces show marker → one download → post checks/metadata → durable post marker → private MMIO.

New test17 was frozen and run against ec6 before implementation: original target PID46344 waited exit1, 23 failing subcases and 2 errors (missing cold admission/post marker); preserved in `evidence/red`. Initial candidate GREEN17 originalPID14252 waited exit0. A further bounded-init read control first failed against that candidate (originalPID47576 exit1), then the bounded reader repair passed all18 (originalPID25580 waited exit0) in `evidence/green-final`. All four original Jobs reached active0, owned chain stopped and cleanup checked, with no timeout. Configs cap each group at40 s; all actually completed under3 s. Raw stdout/stderr, original-handle results, test/source pins and traces are retained. No old45/384/Godot/solve test group or board/SSH/model operation was run.

Remaining limits: no actual cold download, fresh-QPC multi-scan session, ADC/sensor evidence, causal-model qualification, PC_DIRECT/headless integration or formal acceptance is established. Independent source review and new commit/request/physical release belong to Root.
