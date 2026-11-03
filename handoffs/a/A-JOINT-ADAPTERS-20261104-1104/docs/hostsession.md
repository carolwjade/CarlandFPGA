# Root-only1074 already-loaded host transport

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision2`; requirements SHA256 `2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d`. Preserve H01-H15/full H12. Current scope file remains SHA256 `095c7d07e7b02de671ebd63074f057c654e222a8cb7cee788fc7eb9785249c39`, matching the previously canonical-verified revision2 bytes. G03/R03/all29 remain not_run.

`host_board_session.py` derives frozen822 SHA256 `f9171e44467a210c9b61308a558905a69a3fe0a7742a94540c60c677858d9e67`. The new source preserves the exact `_Lines`, `canonical`, `record`, `_owned`, `request`, `sense`, `apply` and `close` ASTs. Original StreamClient SHA256 `3339b8abb515175987732cc550d880c12891ff4ae77552e6a44da47417e60d7a` is checked at explicit staging validation. Source import has no process/network/board effects.

## Integration/API

The new filename remains `host_board_session.py` for the existing controller API. Root's **new** controller process must select this directory before the old822 directory, then verify the imported module's file/hash; a cached old `host_board_session` must not select the old loading launch. Preserve one sole NativeClient/native RPC reader. This transport creates no NativeClient or UART client.

```text
BoardSession(repository_root=..., stage_directory=NEW_LOCAL_STAGE, evidence_directory=NEW_EVIDENCE)
start() -> original init response plus g05_run_id/world_epoch correlation
sense(source_seq=..., adc_tick_ms=..., em_tick_ms=..., counts=..., quality=..., source_digest=...) -> last
apply(yaw_q=..., pitch_q=..., speed_code=..., duration_ms=12000) -> last
request(op, **fields) -> last
close() -> original close result
```

Construct/start/request/close on the same dedicated G05 IO thread. The independent UART actor must first produce its genuine `client_opened` barrier; only then schedule `BoardSession.start()`, which sends original INIT and causes1059 G05 initialization. Neither creating this source nor creating a staging directory initializes G05. Root selects the real world epoch and fresh identity13 later; this task generates neither.

Requests retain the actual physical parent `{boot_id,build_id,request_hash}` ABI, QPC send/return bracket, response SHA, APPLY `host_deadline_qpc_ns`, serial sequence/unknown handling and original necessary per-call bounds. No mission duration/count cap, reconnect or replay is introduced. Wrong new run/world init correlation poisons the client as unknown. `close()` retains the original single STOP admission, EOF, actual wait, bounded stdout/stderr draining and local-SSH termination fallback; its result never claims physical zero capture. Unknown clients do not resend STOP. A failed/uncertain G05 run remains subject to1059's persistent claim and explicit recovery rule.

## New local stage; original1046 remains protected

Root creates a **new local directory**, separate from `joint-board-session-1046`, with this layout:

```text
NEW_LOCAL_STAGE/
  PHYSICAL_PARENT_MANIFEST.json  exact byte-copy of original1046 MANIFEST.json
  loader-plan.json               exact byte-copy of original1046 loader-plan.json
  MANIFEST.json                  NEW10-key additive host manifest below
  UPLOAD_ACTUAL.json             NEW6-key actual additive readback below
  already_loaded_g05_1059.py     adopted exact1059 source
  joint_command_ttl1059.py       adopted exact1059 source
  remote_live_board_a.py         exact frozen791 source, imported only
  g05-config-ROOT-RUN.json        Root's exact15-key1059 config, real selected world epoch
  identity-ROOT-RUN.json         Root's fresh13-word list
  proof1074/BUILD_PLAN.json      exact actual1026 build plan
  proof1074/SOURCE_CLOSURE.json  exact actual1026 source closure
  proof1074/readonly_sources/... all20 actual frozen repository-relative RTL paths
```

Names for config/identity/proof subtree are Root-selected; manifest/config paths must agree. The remote root stays the existing physical1018 stage from the original parent manifest. Do not create another physical operation, edit its14-key plan, rewrite original1046 local metadata, or label this as a new PL load.

The unchanged original1018 dependency closure remains at that remote root. Add only missing1059 files/proofs/config/identity with exclusive creation; already-present files can be read back and reused only at the identical reviewed hash. Do not overwrite a collision. The new host validates all local listed files, and refuses any listed original-parent path whose bytes/length differ from the original parent manifest. The reserved flat names `loader-plan.json`, `MANIFEST.json`, `UPLOAD_ACTUAL.json` and `PHYSICAL_PARENT_MANIFEST.json` are not upload entries. Their local copies/control records are separate from additive remote files.

`MANIFEST.json` has exactly these10 fields:

| Field | Value |
|---|---|
| `schema` | `DEEPEYE-JOINT-HOST-STAGE-1074-v1` |
| `scope_sha256` | Revision2 requirements hash |
| `remote` | Existing1018 remote root, exactly equal to the original manifest |
| `parent_manifest_sha256` | SHA256 of exact local `PHYSICAL_PARENT_MANIFEST.json` copy |
| `loader_plan_sha256` | SHA256 of unchanged local/original remote14-key plan; must match original parent manifest entry |
| `config_relative` | Normalized POSIX relative name of Root's new1059 config |
| `config_sha256` | Exact new config file SHA256 |
| `g05_run_id` | Root-selected fresh1059 run ID |
| `world_epoch` | Root-selected actual positive uint32 epoch, matching config |
| `files` | Relative path -> exact `{"bytes": positive integer, "sha256": lowercase64hex}` for every additive/reused file read back in this package, including config/proofs/identity/source |

`UPLOAD_ACTUAL.json` has exactly these6 fields, recorded by Root **after actual remote readback**:

| Field | Value |
|---|---|
| `schema` | `DEEPEYE-JOINT-HOST-UPLOAD-ACTUAL-1074-v1` |
| `remote` | Same existing1018 remote root |
| `boot_id` | Actual current BOOT, equal to physical plan |
| `files` | Actual read-back descriptors; must exactly equal the new manifest's `files` |
| `loader_plan_sha256` | Actual read-back SHA of the existing remote `loader-plan.json`, unchanged |
| `parent_manifest_sha256` | Retained original parent-manifest copy hash used for this additive staging operation |

These records prove staging/readback only. The remote1059/1031 reader still independently validates actual loaded identity/CSR and capability proof before initialization. Root must not manufacture UPLOAD_ACTUAL from intended files or a transport ACK.

The1059 config remains its exact15-key schema described in1059 HANDOFF. In particular, `approved_plan_path` is the existing remote `/loader-plan.json`, its SHA is unchanged, and `operation_directory` is the original physical plan's `operation_parent/operation_id`. The new source hashes are pinned to adopted1059 entry `56886c15cb44574bc396f95c4a185dba81bc8277e8b730df5d0a6c798d907a01` and capability/decoder `3e62231a59500e9114ebf23d00ccf5f74de69c21d2fa33af42152a33a8eb59b0`.

## Changed launch and evidence

`start()` launches exactly:

```text
<existing sudo/env/SSH route> /usr/local/share/pynq-venv/bin/python3 -I -B -X utf8 <existing1018>/already_loaded_g05_1059.py --allow-g05-run --config <existing1018>/<config_relative> --config-sha256 <config_sha256>
```

There is no old loading entry or `--serve` launch. `STARTED.json` records `new_G05_run_on_existing_physical_parent`, physical parent operation/request/BOOT/build, run/world/config identity, `new_G05_run: true`, `new_PL_operation: false` and `PL_load: false`. Original private route/binary/host-key pins and the private credential's single Root-only in-memory stdin use remain unchanged; worker never reads those private files.

## Root-only controls/status

Run `check_host1074.py` once. It imports inert source, checks original822/StreamClient/adopted1059 pins, proves unchanged transport/request/close ASTs and credential-handling source, and checks pure new argv/path/upload-record rejection and revision2 hashing. It constructs no BoardSession, starts no thread/process, and reads no credentials. SOURCE_ONLY dictionaries are structure fixtures, never actual receipts. Worker did not run it or launch Python/network/board/UI; `SOURCE_CHECKS.json` is absent until Root execution.

Current task delivers source and staging contract only. Root retains the current unknown UART STOP boundary and B's recovery investigation; this task authorizes no live attach or initialization while that boundary remains unresolved.
