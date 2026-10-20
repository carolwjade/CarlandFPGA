# R02 Read-only Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supply the missing taskbook `tools/preflight.py` command with reproducible, background-only host inventory and truthful incomplete R02 gates.

**Architecture:** A standalone standard-library Python command invokes a fixed local PowerShell collector once on Windows. Structured group errors and package metadata remain observations, separate from compatibility, model, calibration and physical-board acceptance. Normal output is JSON on stdout; an optional new output file uses exclusive creation.

**Tech Stack:** Python 3.12 standard library, Windows PowerShell CIM read queries, unittest.

## Global Constraints

- Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; sole director `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2. Main alone accepts and publishes.
- Read project AGENTS.md, multi-node skill and role, active transfer, and immutable_scope.md/json before execution.
- Preserve all H01–H15 under `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
- User reserves the display and input. All subprocesses hidden, bounded and below normal priority. No GUI, screenshots, browser, focus, keyboard or mouse operations.
- No board connection, model/backend import or execution, GPU enumeration API, network, package install, driver/service/configuration change or peer/group communication.
- Existing linked product worktree is `.local/deepeye-implementation-a`, branch `codex/a/deepeye-implementation-20261014`, base `f1d8c6d37bf6e17b3b0b92dc4998a4c7f8959bbe`. Four unrelated existing C dirty files remain byte-identical and unstaged.
- This task creates only four named product files below. Do not rewrite `hardware/environment.json`, other hardware evidence, the immutable contract or acceptance cards. Main owns this plan; all 29 formal cards remain `not_run`.
- Recorded Desktop/native ownership suffices; this task uses no new mesh lease. Do not create/resume another director, clear locks or start a service.

### Task 1: Deliver the standalone inventory command

**Files:**
- Create `competition/deepeye/tools/preflight.py`: CLI, contract verification, bounded collector invocation, result classification and optional exclusive output.
- Create `competition/deepeye/tools/preflight_windows.ps1`: fixed local read-only CIM queries and UTF-8 JSON stdout.
- Create `competition/deepeye/tests/test_preflight.py`: meaningful deterministic tests of failure boundaries and output semantics.
- Create `competition/deepeye/hardware/preflight.md`: command examples, scope, gates and output interpretation.
- Worker evidence only in `.planning/deepeye-resume-20261018/r02-preflight-implementation-20261020/`; brief/report/ledger in this plan's SDD directory.

**Interface and behavior:**

1. `python -B tools/preflight.py` collects a host inventory, reports `R02: not_run`, `formal_acceptance: false` and exits 2 because this command alone cannot establish the full card.
2. `--inventory-only` exits 0 only for complete, well-formed required host queries and metadata collection. It still reports `R02: not_run`, all physical/calibration/ROCm-project/NPU-runtime gates as `not_run` or `unknown`. Unsupported platform, query failure, malformed output, bad contract, timeout or incomplete required group exits 2 and reports the actual problem. Do not add a success override or accepted-evidence input.
3. Default stdout JSON only, no product/evidence writes. `--output PATH` writes the same JSON to a new file with exclusive creation. No overwrite and no parent-directory creation; an existing file is rejected before invoking the collector. No append/resume. This allows reviewers to retain historical failures.
4. Verify the canonical requirements array against the pinned constant before querying. Verify contract identity/revision and exact H01–H15 membership; never trust only the declared hash. Report actual contract digest and collector source digest. Invalid contract must not run a subprocess.
5. The collector reports observation UTC and separate typed groups for CPU, OS, GPU, candidate NPU PnP devices, corresponding driver records, and fixed local logical disks. Preserve useful actual names/versions/architecture/memory, device IDs, driver versions/dates and disk total/free bytes. Do not gather secrets, user identity, serial numbers, process listings or registry inventories.
6. CPU and OS must be nonempty with required type-correct fields; successful empty GPU/NPU/driver lists mean only that this query found no matching rows. Empty lists must not become proven hardware absence or supported/unsupported verdicts. Preserve per-group failed query messages; a partial result is not a successful inventory.
7. NPU detection is a labeled candidate observation. Match meaningful name tokens (`NPU`, `Neural`, word `IPU`, `AMD IPU Device`) and the known AMD device vendor/device prefix where applicable. Do not match `Input` by a broad substring. Never classify a matched device as a tested accelerator.
8. Obtain selected installed package versions using `importlib.metadata` in the current interpreter only: torch, onnxruntime, onnxruntime-directml, onnx, rocm, rocm-bootstrap, numpy, setuptools, typing-extensions. Do not import any target package or start a resolver. Distinguish not installed from metadata error. Report interpreter version/architecture/executable and metadata-only scope. No claim that this scans every environment.
9. One fixed PowerShell collector invocation, no user-supplied code/host/command. Use the system Windows PowerShell executable, NoProfile/NonInteractive, hidden and below-normal Windows creation flags; max 20 seconds. Validate bounded JSON (at most 1 MiB), duplicate keys, required shape, booleans versus integers and nonfinite values. Capture subprocess failure/timeout precisely, kill/wait only this owned process on timeout and retain available diagnostics in structured output. No retries. No visible child windows.
10. `hardware/environment.json` is historical input context only. This command neither updates it by default nor grants eligibility, ROCm device support, trained model benefit, board or calibration readiness.
11. Keep implementation focused. No service integration, new generic process framework, pipeline acceptance change or external dependency.

- [ ] Write behavioral tests first; run them once and retain the expected missing-command failure.
- [ ] Implement the minimal collector, validation, CLI and documentation. Test missing packages, malformed/partial queries, NPU false positives, timeout, unsupported OS, forged contract and exclusive-output refusal without touching the actual display or devices.
- [ ] Run targeted unittest tests in a hidden bounded process. Retain raw stdout/stderr, command, timestamps, exit status and exact source hashes.
- [ ] Run one actual `--inventory-only` host collection into a new owned evidence file. Do not run a model, board, package install or full acceptance suite. Retain current source hashes, command and returned JSON.
- [ ] Self-review exact four files and preserve all four C dirty files. Main performs separate independent review before adoption/publication. Worker must not stage, commit or push.
- [ ] Return status, exact changed-file hashes, bounded test/live results, limitations and a short report. No formal card closure.
