# Retained actor CPU fixture: prepared, native not_run

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1; H01–H15 canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Sole main: `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation2. This preparation does not grant execution permission or register a product provider.

The fixture emits exactly `DEEPEYE-ACTOR/1 READY\n` on its explicitly inherited output endpoint. `exit` mode accepts only the single byte `X` on its explicitly inherited input endpoint. `natural` mode exits after an integer 1–10000 ms delay. `wait` mode blocks reading its original input endpoint until the parent retires it; no command is sent. It opens no additional handles, models, files, network endpoints, GUI or child processes. READY is a fixture protocol frame, not authenticated AI readiness or a BOOT credential.

The existing `win32.write` uses synchronous WriteFile without timeout/cancellation. This preparation cannot prove a bounded command write. **The harness never calls it. EXIT-write/normal cooperative-command exit remain not_run.** The usable alternative is a named natural-exit case. It does not claim to have tested the EXIT protocol in Windows; protocol behavior is tested only with an in-memory fake `_winapi`.

## Three independently selected future cases

| Case | Mode and explicit test budget | Required observation |
|---|---|---|
| `retained-natural-exit` | natural exit after 2000 ms; readiness=lifetime 8 s; parent polling at most 6 s after launch | Production registry returns its strongly retained original owner. Public poll succeeds while original process is live; exact READY is consumed, then strict terminal observation retires owner. Original-owner cleanup must confirm process/profile/resource release. |
| `fixed-unbound-expiry` | wait; readiness=lifetime 2 s; same bounded polling | Exact fixed-deadline rejection while original process has not yet been observed terminal, then original cleanup. This proves only simultaneous unbound readiness/lifetime expiry, **not** a bound actor's independent lifetime cap. |
| `persistence-after-acquisition` | wait; readiness=lifetime 8 s | A controlled `_persist` seam throws the same OSError after the production owner has registered its original process. Launch retains that exception, cleanup is attempted once, evidence errors and QUARANTINED memory recovery record remain. Old actor receipt bytes are labelled snapshots and never rewritten as final success. |

All are fixture-specific budgets, not production policy or measured guarantees. Max probe 250 ms, sample cap 500 ms, output cap 256 bytes total, stage cap 256 MiB, poll sleep 10 ms. Existing native helper/cleanup calls are synchronous; fixed parent loop bounds do not cancel a stalled native call. No whole-test hard deadline, sample-to-CAS survival, owner-hang recovery or full isolation claim follows. An early deadline/slow probe/startup failure is a real failed attempt; never retry it automatically.

The private fixture reader exists only in `tests/isolation/test_actor_windows_live.py` under main's explicit test-adapter authorization. It uses the production `_entry` guard on the same owner and `_sample`/`_reference` before/after the consuming read, plus epoch/state/ref checks. It reads only the existing owned output reference using `available_output` (helper hard cap8192); it neither accepts handles/PIDs nor releases/mutates owned resources. A post-read rejection may mean bytes were consumed; the read is not retried. This is not production IPC authentication or a new public ActorOwner API.

`run_case` retains `NativeAttempt`, registry, actor and original exception in module `_ATTEMPTS`. Read-only private resource snapshots provide terminal/profile/cleanup evidence; they cannot adopt targets. Poll records state that successful `_sample` implies integer258; raw Wait results are not intercepted or separately claimed. Terminal-confirmed is the strict integer0 observation recorded by the pinned actor source. The final report includes these source/interpretation limits. Actual helper ABI and original-handle behavior remain unexecuted until a main-authorized Windows run.

## Prepare and approve exact bytes before native execution

Ordinary test discovery imports no Win32 DLL and genuinely skips the three native tests:

```powershell
# From product root, with its parent host-deps directory in per-process PYTHONPATH:
python -B -X utf8 -m unittest competition.deepeye.tests.isolation.test_actor_windows_live -v
```

Main must first finish the concurrent actor repair and independently review its final manifest. This preparation never pins its intermediate bytes as an executable candidate. In a fresh dedicated evidence parent, future **offline file staging** can be requested interactively:

```python
from pathlib import Path
from uuid import uuid4
from competition.deepeye.tests.isolation import test_actor_windows_live as probe
attempt, proposal = probe.prepare_stage(Path(EXPLICIT_DEDICATED_EVIDENCE_PARENT), uuid4().hex)
```

Use app-local CPython3.12. `stage_runtime` copies files into fresh `attempt/source-stage`; it does not ACL/link source files. The harness replaces staged `fixture.py` with the reviewed cooperative fixture, hashes **every final staged file**, and emits `allow-proposal.json` with `native_execution=false`, `approved_by=null`, `case=null`. The original stage manifest is saved separately and explicitly identifies its old fixture entry as superseded. It cannot attest the replacement bytes. Staging is not native execution or acceptance.

After reviewing those final runtime/fixture hashes and the repaired source, main creates a separate `allow.json` that retains exact proposal `sources`, `staged_files`, `attempt_directory`, schema and contract, and sets:

```json
{"approved_by":"01a13d7e-dcf1-7272-a738-a637dd62ff9d",
 "native_execution":true,"case":"retained-natural-exit"}
```

This JSON snippet shows the changed fields only; it is not a sufficient allow record. Full sources must include every current isolation/integration Python file, imported pc_direct_runtime, its interface/enums/host-contract/timing documents, the immutable scope, this harness and document. This is a CPU lifecycle dependency set, not a geometry candidate binding. The record is a trusted main artifact, not a cryptographic signature. It requires an ordinary single-link file and exact bytes; source aliases/reparse points, case aliases, traversal, omitted or additional stage files, stale hashes and unrelated cases fail validation before native imports. Protect the dedicated parent and stop other source writers during the authorized run; filesystem checks are not protection against an adversarial same-user TOCTOU writer.

Each run uses an `x`-created `execution-claimed.json` before constructing production ActorRegistry. An attempt/claim is never reused after success, failure or ambiguous interruption. Main selects one case per fresh stage and allow record. No campaign loop runs all cases or retries them.

## Explicit execution gate, for future main use only

This assignment does not run these commands. Actual execution requires Windows CPython3.12 **interactive** (`python -i`) so unresolved live contexts remain available. From that retained interpreter after main authorization:

```python
result = probe.run_case(Path(EXPLICIT_DEDICATED_EVIDENCE_PARENT), Path(EXACT_MAIN_ALLOW_JSON), SELECTED_CASE)
result.passed, result.unresolved, result.cleanup
```

Alternatively native unittest methods require all four explicit environment values `DEEPEYE_ACTOR_NATIVE_OPT_IN=1`, `DEEPEYE_ACTOR_NATIVE_CASE`, `DEEPEYE_ACTOR_NATIVE_EVIDENCE_PARENT`, `DEEPEYE_ACTOR_NATIVE_ALLOW`, plus the interactive flag and exact allow gate. Nonselected native methods skip. Prefer calling one case directly; an ordinary subprocess runner fails before reading an allow file or loading native modules.

Never close an interpreter with unresolved original ownership. `_ATTEMPTS` retains the recovery context even if result persistence fails; subsequent case calls refuse unresolved contexts. Stop the campaign and hand that live context to main. Disk receipts/HANDLE integers/PIDs cannot restore it, and this harness supplies no force discard/reopen/retry operation. A QUARANTINED evidence failure is not relabelled CLOSED even when resources were released. A known-complete expected injection still remains a failed-evidence observation, never actual product success.

Future output: raw fixture bytes (x-created), elapsed parent observations, original reference continuity, terminal/profile/resource outcome, evidence errors, exact primary exception and original receipt snapshot hashes. If result persistence fails, the in-memory event record is the recovery source; never overwrite an older file to hide failure.

Real project AI/inference, verified BOOT/readiness/channel, ai_lease provider routing, continuous IPC, sample-to-CAS liveness, hardware watchdog, physical board, geometry, both complete H12 chains, product Run and all29 formal cards remain **not_run**.
