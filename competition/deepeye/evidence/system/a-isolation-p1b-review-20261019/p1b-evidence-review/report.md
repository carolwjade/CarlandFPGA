# Independent static P1b evidence review

The stored evidence supports three **finite, specified-object denial observations**: section, SID-scoped named pipe, and DebugActiveProcess against the held test victim. It also supports native bootstrap/control operation and the recorded successful lifecycle of the completed runs. It does **not** establish universal IPC/security denial, loopback permission denial, robust cleanup under arbitrary logging failure, or execution of the four product processes. G03 remains **not_run**.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-G03-P1B-EVIDENCE-REVIEW-20261018-v1`; reviewer `/root/pc_direct_review_20261018`; new job `child-a2ca95206f644546849283858b350ece`. Sole director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. Root and product requirements match H01–H15 canonical SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Historical job `child-acd1ad0ee1d84b31baab02ffa6298966` was read as completed history and was never reused.

Reviewed history: `.planning/deepeye-implementation-a/process-isolation-p1b-prototype-20261016/`. This review wrote only the new `p1b-evidence-review/` directory. No audit/runner/cases/build/finalizer/native EXE or OS helper was executed or imported. The only executable test code was the previously read json-only parser suite, staged byte-for-byte into this review directory. No new profile, native fixture process, IPC object, ACL or service was created or queried.

## Integrity and provenance

- All **224** manifest paths, sizes and SHA256 values match. There are **227** historical files: `manifest.json`, final `receipt.json` and `native_complete.json` are intentionally outside the manifest to avoid recursive finalization. Receipt → manifest/report/audit hashes match; the stored native completion names the expected historical job and completed state. All 227 file hashes are unchanged across this review.
- **17 native run receipts** bind their per-run C source, private launcher, parser, staged EXE/model, exact request.bin and stdout.bin. Offline request decoding independently verifies the 2312-byte layout, magic/version/mode, nonce, model path, source observations and case target fields. Raw response frames match receipt frames and the expected PID/nonce/mode. The victim's deliberate ready/termination path is checked separately rather than forced through a normal complete-phase parser.
- Native v1 image SHA `876ffb2586f377f6f427d1048f952b031691319503935a970528bb4916bb42e9` accounts for **11** runs; v2 SHA `ada3f11d5cdd3d32edec9375726020c721b9b4efb5586c3a7b09c4c4e142e115` accounts for **6**. Per-run C/image pairs match the two build receipts; all compile/objdump/disassembly log hashes match. Saved import listings contain KERNEL32.dll only. Both original `xdata section corrupt` warnings remain present. Successful loader/API execution does not establish exception-unwind correctness.
- The saved source hashes of all seven original P1a helpers/tests still match the read-only product files. Final cases.py is manifest-bound, but its historical versions were not captured at each object creation. I do not assign the final fixture code retroactively to every earlier attempt.

These hashes establish consistency of supplied historical bytes and their recorded relationships. They are not a fresh observation of a native process or an independent cryptographic attestation of the historical OS.

## Evidence categories

| Category | Bounded conclusion supported by raw bindings | Expansion rejected |
| --- | --- | --- |
| Native bootstrap v1/v2 | Ordinary and restricted model/authorized-pipe controls compute dot=23; saved parent restriction readbacks precede resume | Generic runtime/GPU/ROCm compatibility |
| Specified section | Ordinary exact-name dual canaries pass; parent reopens same names; restricted benign map/canary succeeds while truth NtOpenSection reports `0xc0000022` | All shared-memory APIs/namespaces denied |
| SID-scoped pipe | Same actual NT names and instance objects are used; ordinary benign/truth controls pass; restricted benign PID/nonce handshake succeeds, truth NtOpenFile reports `0xc0000022`, and no restricted truth connection is recorded | Universal pipe isolation or namespace-independent denial |
| Specified debugger victim | Same held PID/creation-time identity; ordinary attach, seven events, breakpoint/continue/detach and debugger-absent readback pass; restricted DebugActiveProcess reports Win32=5; victim remains alive until owner cleanup | All debugging/injection/process APIs denied |
| LOCAL pipe #1/#2 | Ordinary controls pass; restricted benign and truth both fail with Win32=2 or `0xc0000034` | Permission denial: object reachability/binding for the restricted client remains unproven |
| IPv4 loopback | Original same ephemeral listener/port and ordinary nonce/canary control work; restricted socket setup works, connect remains 10035 and select times out with no restricted accept | Permission denial: this remains `unclassified_network_failure`, not WSAEACCES evidence |

For the native restricted cases, saved trusted-parent inspections show exact SID, zero capabilities, Win32k/child/StrictHandle raw values 1/1/3, Job flags `0x2108`, active-process limit 1, 256MiB process-memory limit, UI restrictions `0xff` and actual membership. Inheritance is exactly the two intended pipe handles; environment keys are the documented five. These are reconciled saved parent records, not a new process inspection.

## Resource lifecycle and limitations

There are 18 native run-directory intents: **17 created native children** plus the initial failed pre-create host attempt. Eight native profiles and two P1a baseline profiles give **10 unique profiles**, below the recorded cap 16. Saved completed receipts record all 17 native children terminal, seven launcher-handle closes per run, and successful profile deletion/absence for the eight native profiles. Case records separately show fixture section/pipe handles closed, server threads joined, loopback socket closed and no unbound pipe client PID/nonce accepted. The debugger victim's own handle is held through the test, then terminated and confirmed terminal.

The two P1a baseline processes are different from the 17 native children. Their outer two-test suite passed: one normal fixture has the expected strict-invalid-handle termination (`0xc0000008`) and passed verdict, while the intentional sleeper timed out, was terminated, and correctly has a failed fixture verdict. Both saved profile-deletion/terminal records are present. This is not two successful normal model runs.

The initial `bootstrap-control-13332ce012/receipt.json` remains truncated with its original SHA `94db57bedfcde94f2fa9b929db588eb57790419ec7562f5d07d7708584d9ca1d`. Its events contain no created/resumed child or profile, and the preserved source places process creation after the failing persistence operation. However, the failed owner PID and individual remaining-handle close acknowledgements are absent. The reported exit1/OS teardown explanation cannot be promoted to a complete independently bound owner-cleanup ledger.

The historical audit's PID/creation-time checks show no same-identity live process **at that audit time**; they are not current liveness checks or an indefinite guarantee. Child-loaded module paths/hashes were not sampled independently: host System32 hashes and static imports do not replace that proof. Debug event handles inside the child depend on OS teardown, without individual external handle-list verification.

Concrete source concerns remain suitable for the next implementation task:

1. `runner.py` invokes `event()`/`persist()` inside process termination, per-handle close and final cleanup. A logging/serialization failure can interrupt the very cleanup needed to contain it. The original failed attempt already exhibits incomplete close telemetry.
2. `close()` removes a handle from ownership tracking before close/logging completion, and cleanup marks the Run closed even after a cleanup error. Future recovery must retain unresolved resource ownership instead of treating attempted cleanup as completed.
3. `paired()`'s aggregate `cleanup_complete` reflects child Runs, not fixture handle/thread/socket success. The old audit separately checked those fields and they pass here; the aggregate alone would be insufficient in a future failure.

Normal paired cleanup deletes the profile after child termination but before closing externally held fixture resources. Current records eventually show all closed; this review does not endorse that sequence as a complete production exception policy.

## Smallest next task

Propose a **pure resource-cleanup coordinator and fault-injection tests**, before another native probe or product activation. Candidate new ownership, subject to main's owner check:

```
competition/deepeye/simulation/isolation/resource_cleanup.py
competition/deepeye/tests/isolation/test_resource_cleanup.py
competition/deepeye/docs/isolation_resource_cleanup.md
```

Use an injected fake backend to demonstrate that log/fsync/serialization failure never skips remaining terminate/wait/close actions; retain the primary failure and each unresolved resource; allow profile cleanup only after confirmed child termination and the defined owned-resource phase. Record owner identity and source/fixture manifest before future acquisition. Test failures at every logging/cleanup boundary deterministically, with no real profiles, OS fixtures or ACL changes. A later separately scoped launcher version may adopt it while preserving all old evidence. This is a proposal for main assignment, **not work executed or permission to activate native probes in this review**. It needs no shared-runtime/global/Desktop ACL modification.

Fresh verification here is **12 pure parser tests passed**. Exact command, parser hashes, raw test log, 224-file verification, request/response binding rows and before/after historical hashes are in `receipt.json` and accompanying JSON files. Actual four-product-process execution, screen/window/GDI/GPU/WGC/DXGI isolation, meaningful AI/ROCm, full PC_DIRECT/HIL, game and physical-board acceptance remain **not_run**; H01–H15 remain unchanged.
