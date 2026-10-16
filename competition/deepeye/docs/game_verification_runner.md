# Game verification runner

`tools/verify_game.py` is a fixed, bounded software-reference entrypoint. All
formal game acceptance suites currently return `blocked` (exit 2). It preserves
contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, canonical requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`, including H01–H15.
The requirements hash is recomputed on each invocation, independently of the
hash recorded in the scope file. Source hashes bind working bytes; Git HEAD alone
does not assert a clean checkout or formal acceptance.

Run from `competition/deepeye`, using an existing Python 3.11+ interpreter.
`EVIDENCE` below must be a caller-owned directory outside the product source tree.
No software installation, download, board access, service change or AI execution
is performed.

```text
python -B tools/verify_game.py --suite editor --evidence-dir EVIDENCE
python -B tools/verify_game.py --suite sensors --reference-only --evidence-dir EVIDENCE
python -B tools/verify_game.py --suite timing --reference-only --evidence-dir EVIDENCE
python -B tools/verify_game.py --suite motion_authority --reference-only --evidence-dir EVIDENCE
python -B tools/verify_game.py --suite editor --reference-only --godot-exe EXISTING_GODOT_EXE --evidence-dir EVIDENCE
```

| Suite | Explicit reference-only execution | Formal missing evidence |
|---|---|---|
| `editor` | Real `test_editor_document.gd` headless document/viewer regression checks | 200 real UI actions and recording/replay, layout save/reopen, independent 36 face pairs, resolution/scaling and camera isolation |
| `sensors` | `test_forward_profile.py` plus `test_sensor_source.py` | Independent 3D FDEM/convergence/noise budget, matrix with 30 trials per cell, support/20 Hz/ADC/physical bridge evidence |
| `timing` | `test_pc_direct_watchdog.py` and its real local imports | Complete authenticated PC_DIRECT/HIL control paths, first-send TTL end-to-end faults, model lifecycle and actual capture/board evidence |
| `assets` | Unimplemented; blocked | B-owned `test_asset_contract.gd`, five closed model classes, drill collision envelope, sourced dimensions, licenses, 30-instance loading and real views |
| `secrecy` | Unimplemented; blocked | Four-process OS file/screenshot/debug ACL, paired-world command equivalence and restricted-controller audit |
| `motion_authority` | Real rigid-motion, capsule/plane-section and quantized-command unit suites | Three control topologies, actual authority/physics executor, 1000 independent geometry/fault cases and full-volume crossing traces |

`--actions` and `--trials-per-cell` are recognized only to explicitly return
blocked/exit 2: their requested execution is unimplemented in both formal and
reference modes. They never convert graybox checks into UI actions or repeated
trials. Unknown suites/options are rejected by argument parsing (exit 2).
Every report keeps `formal_acceptance: false` and the formal missing-evidence
list, even when the reference tests succeed.

## Dependencies and bounded execution

- The runner uses its current interpreter with `-B`, fixed test entrypoints and
  bytecode disabled. `timing` requires existing `jsonschema`. In this checkout it
  is available under root `.local/deepeye-host-deps`; a caller may explicitly set
  process-local `PYTHONPATH` to that existing directory. No global PATH is changed.
  The chosen interpreter hash and relevant child environment are recorded.
- `motion_authority` reference mode runs fixed repository-qualified unittest
  modules from the checkout root. It binds both source modules, their tests and
  quantized-command dependencies by hash. Bytecode is disabled and all logs and
  temporary fixtures remain under the evidence directory. This primitive suite
  does not run a scene, authenticated grant, continuous sweep or gate phase machine.
- `editor` requires an explicit existing official Godot Windows 4.7.2 executable.
  Supported executable SHA256 values are
  `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`
  (engine) and `c8f0a6bc45a19b33541501e57f6f7cd972ab18453743266339d495cbbe846643`
  (console launcher, with the matching engine companion). An unknown build or
  missing companion blocks; supporting another build needs a reviewed identity
  update. The actual engine is executed directly and must report
  `4.7.2.stable.official.ed1daf0bf` from a real `--version` call. There is no mock
  fallback.
- The simulator is copied without `.godot` into the new evidence run directory.
  Real engine import and the real copied SceneTree tests run there. This keeps
  import/cache/log outputs away from product inputs. Original and staged source
  manifests must match before execution and remain unchanged afterward.
- Each subprocess has a finite `--timeout-seconds` (default 60, maximum 300).
  Timeout/nonzero exit/runtime error markers/empty or skipped unittest summaries
  fail. A missing executable, source or preflight dependency blocks. There is no
  retry, software installation or automatic model startup. There are at most
  four subprocesses including Git HEAD/version/import in editor mode.

## Evidence and status

Each invocation creates a fresh `EVIDENCE/run-<uuid>/report.json`. Existing runs
are preserved. Fixed filenames are checked for containment, logs use exclusive
creation, source-link escapes are rejected, and output below product sources is
rejected. This is path containment for the runner's fixed trusted programs, not
an OS sandbox for arbitrary hostile executables or local processes.

The UTF-8 report includes absolute argv/cwd, relevant environment, child exit
codes, elapsed time, timeout flags, raw stdout/stderr paths/sizes/SHA256, actual
Git HEAD, source before/after hashes, changed paths, engine identity/version and
staged source manifests for editor. Raw stdout/stderr bytes are saved unchanged;
machine stdout contains JSON with ASCII escapes for Windows console portability.
Missing prerequisites may stop before a test subprocess exists; those reports
have no invented child exit code.

| Exit | Status | Meaning |
|---|---|---|
| 0 | `reference_passed` | All selected software reference programs actually ran successfully and sources stayed unchanged |
| 1 | `failed` | Actual subprocess failure/timeout, invalid success summary/runtime errors or source/engine changes |
| 2 | `blocked` or CLI rejection | Formal gate unimplemented, unsupported count/suite/mode, or missing prerequisites |

The editor currently reports 672 graybox checks, sensors 33+43 software tests and
timing 40 watchdog tests at baseline `d5bf26adcf76f8c9af3165cdd7043cb3ff19649b`.
These counts describe that source checkpoint only. They do not establish G01–G09,
C05/G06, real UI, independent physical validity, cross-process secrecy, complete
PC_DIRECT/HIL motion or physical-board acceptance. Inspect each fresh report.

The current motion reference consists of 28 kinematics, 24 gate-geometry,
29 sufficient-clearance and9 quantized-command tests (90 total). The original
motion checkpoint ran59 before these additions. Formal mode still returns blocked.
The runner now has 19 behavior tests, including a check that the motion source
dependencies are bound without promoting the formal authority gate.

Runner behavior tests are in `tests/test_verify_game.py`. To keep their temporary
fixtures in private evidence, set `TMP`/`TEMP` to the caller's existing private
directory, then run `python -B tests/test_verify_game.py -v`. Those tests validate
the runner itself and do not change product acceptance status.
