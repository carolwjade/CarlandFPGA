# Root-only1037 load entry source

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision2`; requirements SHA256 `2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d`. H01-H15 preserved. Current scope file SHA256 is still `095c7d07e7b02de671ebd63074f057c654e222a8cb7cee788fc7eb9785249c39`, identical to the bytes whose canonical requirement hash this worker previously verified. The new Root control independently recalculates the canonical hash.

`load_joint1037.py` is import-inert and denies execution without `--allow-board-load`. Root must first finish the actual new BIT/HWH/timing/DRC/CDC review, verify sole physical ownership/old-owner termination, and retain its original real-disk/operation staging checks. This source does not establish those external preconditions.

Stage the entry as a sibling of the adopted1024 loader and verifier under the fresh PS stage root. Preserve the original `snapshot/competition/deepeye/tools/diagnostic/functional50_board_a.py` namespace hierarchy. All three sources are SHA-pinned; namespace `__init__.py` additions and foreign preloaded modules are refused. No dependency fallback or alternate loader exists.

Root runs the local `check_load_entry1037.py` once before adoption. It contains new import/AST and pure negative controls, including missing-flag denial, exact14-key request binding, LE BUILD_ID reconstruction, fresh G05 OFF/status/fault checks, bounded readonly CSR fixture access, clock types, unsafe XML and UART metadata rejection, and adopted source/contract pins. Fixtures are source-mechanism evidence only. Worker did not run this check or any new Python process; `SOURCE_CHECKS.json` is intentionally absent until Root executes it.

After Root stages/reviews the exact approved14-key plan, the single physical invocation is:

```text
<PS-python> -I -B -X utf8 <fresh-stage>/load_joint1037.py --allow-board-load --plan <absolute-approved-plan.json> --plan-sha256 <exact-plan-file-SHA256>
```

The entry invokes the adopted `open_stream_from_plan` exactly once and requires its original TRACE MMIO/G05 MMIO/plan tuple. It does not initialize G05. It then checks current BOOT and PS source0/PLL20/div10/div2 plus unchanged other clock registers; the actual operation-copy BIT/HWH bytes; all three validated HWH windows; product clock/reset nets; UART50MHz1152008N1 metadata; ten readonly TRACE words including its LE BUILD_ID; and four readonly G05 words with fresh status0/fault0. UART base comes from validated HWH, and the build ID comes exclusively from the approved plan.

On success, the original `_record` writes `actual_loaded_snapshot.json` under the original operation directory with O_EXCL/fsync and the same JSON is emitted to stdout. All fields are plain bounded JSON. This is a measured load snapshot. It creates no Profile, BTransfer or transfer permission; reader1031 will later independently reread CSR and identity records. No MCU frame, UART read/write, ARM, motor operation, reset or extra clock write occurs. The process may exit0 after the snapshot without cleaning up/reloading PL or vendor state.

If load or readback fails, no automatic retry/cleanup occurs. A best-effort new `actual-load-snapshot-failed.json` preserves uncertainty when an operation directory exists; Root must inspect the original load-started/load-returned/failed records before any further action. A started/existing operation is refused before the loader call. No replay of an unknown load.

Entry SHA256: `6dfe9a13022d6be38ee6241176d264d35c741d6aeac75126ffbfce4fea2c5f50`.

Only this new `joint-load-entry-1037` directory was written. No existing loader, reader, build, B file, `.local/deepeye` state, board, vendor, UART, network or UI was changed. G03/R03/all29 remain not_run.
