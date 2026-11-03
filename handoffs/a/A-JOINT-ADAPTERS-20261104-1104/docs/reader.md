# Fresh UART child reader1057

Source candidate only; Root owns execution/acceptance. All writes by this worker are confined to this new directory. Frozen1031, service6404, stdio1041, actual parent plan/load and all old journals remain untouched. Contract DEEPEYE-HUMAN-LOCK-20261014/revision2, requirements SHA256 2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d; H01-H15/full29 preserved, G03/R03/all29 remain not_run.

Factory: build_actual_reader(service_api, *, approved_plan_path, approved_plan_sha256, actual_operation_directory, transfer_review_path, transfer_review_sha256, child_manifest_path, child_manifest_sha256). Retain flat frozen1031/1024/verifier/helper snapshot and existing B package. The new module is import-inert and imports no PYNQ. Its explicit root/armv7l constructor verifies the sibling1031 source SHA d3be22472808418cc9fef164fe8ca3021987b84ecde1cef9261568155e6da57b and service SHA6404ce0b0be4b1d1f85615f083c63b6d1df9fef2bd55bbaea022a35032acab13, then calls frozen1031's actual constructor/readback unchanged. No old authorization method or old _authorized state is reused or changed.

The wrapper validates the physical parent first and replaces only ProductBinding.operation_id with the approved child ID. The actual physical request hash is unchanged. BOOT/build/artifact hashes, runtime parser descriptors, PS clock and real TRACE/G05 reads remain from frozen1031. It additionally pins/watches child, actual parent snapshot, final predecessor journals/consumed receipt, Root close record and authentic termination/lock readback files. G05 status0/fault0 is read before the first child UART mapping, without resetting hardware. read_hwh_bytes remains actual parent bytes. No new load/start/return record is manufactured.

The future trusted Root entry MUST pass root.state_directory to unchanged ProductUartService.attach. This property returns the one SHA-bound child state directory, not a new per-run directory or caller override. The unchanged service acquires its persistent OS hardware lock and preserves consumed-transfer/operation/sequence state. Reader constructor only observes the existing lock file; it neither acquires, deletes nor breaks it. Service/entry source remains Root's trusted boundary. No alternate directory may be used to evade a prior failed operation.

Child manifest: exactly EIGHT fields, bounded duplicate-key-rejecting JSON:

1. schema = DEEPEYE-UART-CHILD-OPERATION-v1
2. requirements_sha256 = fixed revision2 hash
3. operation_id = fresh bounded ASCII child ID, distinct from physical parent and predecessor
4. parent = exactly plan_path, plan_sha256, actual_operation_directory, load_snapshot_sha256
5. predecessor = exactly operation_id, binding_sha256, events_sha256, sequence_sha256, closed_record_path, closed_record_sha256
6. state_directory = same persistent absolute hardware UART directory
7. purpose = explicitly DIAGNOSTIC_ONLY or MOTION_READY_NO_MOTOR
8. request_sha256 = canonical UTF-8 sorted compact JSON SHA of the other seven fields

The snapshot path is derived as actual_operation_directory/actual_loaded_snapshot.json. Original fourteen-key parent plan remains unchanged. The child request digest is authorization context, never substituted for the physical load request. Purpose is SHA-bound; DIAGNOSTIC_ONLY requires exactly a DIAGNOSTIC_ONLY transfer, MOTION_READY_NO_MOTOR requires exactly MOTION_READY. There is no default or automatic scope upgrade.

Root close record: exactly TEN fields:

- schema = DEEPEYE-ROOT-UART-PREDECESSOR-CLOSED-v1
- requirements_sha256
- operation_id = actual predecessor ID
- physical_parent = exactly operation_id, request_sha256, boot_id, build_id, plan_sha256, load_snapshot_sha256
- state_directory
- binding_sha256
- events_sha256
- sequence_sha256
- stop = exactly outcome, evidence_path, evidence_sha256
- writer = exactly ssh_result_path, ssh_result_sha256, ps_readback_path, ps_readback_sha256

STOP evidence_path names retained actual raw evidence bytes; NO new STOP-document schema is needed. For actual1063, use outcome UNCERTAIN and preserve its actual uart-events.jsonl bytes (SHA32c3d13b7ed3a31a01f7002902566dcd465d973dc989692920b4cc66227bb51b). Final journal must actually show terminal_stop_error; fake ACK is refused. ACKNOWLEDGED is accepted only with an actual terminal_stop_result reporting unarmed/duty0; this does not imply MCU readiness. NOT_ISSUED cannot replace an actual terminal event. All uncertainty and raw TX/RX evidence remain intact.

writer.ssh_result_path refers to actual completed transport proof with integer returncode, wait_confirmed=true, reader_thread_stopped=true, automatic_retry=false. A normal nonzero exit such as actual1063 exit2 proves termination only; it remains a failed physical attach. No local SSH PID is represented as a PS PID. writer.ps_readback_path refers to actual retained1064 schema DEEPEYE-ROOT-UART-PS-CLOSED-READBACK-v1, exactly schema/requirements_sha256/operation_id/boot_id/state_directory/actors/lock/UART/PL. Require actors=[], UART=false, PL=false, and lock with exactly path/device/inode/mechanism/acquire_returned/release_returned. Its mechanism is fcntl.flock(LOCK_EX|LOCK_NB), actual acquire/release returned, and its path/dev/inode must identify the same existing persistent lock file. No new probe is required just for formatting. Root authors the O_EXCL closed record only after observing the actual writer end and actual PS/lock readback; claimed booleans without retained SHA-pinned raw mechanism evidence are insufficient.

Predecessor paths derive from state_directory/operations/SHA256(predecessor.operation_id)/{binding.json,uart-events.jsonl,sequence.json}; final bytes must match the manifest and close record. The existing consumed-transfers/evidence_sha256.json must match the actual predecessor binding bytes. No state is cleared. Fresh child operation and fresh evidence must not already exist. The new BTransfer uses the child ID and genuinely distinct transfer/observation/evidence identities. Actual1063 sent one STOP seq1, got no RX, left next_seq2 and terminal_stop_error; future B last_seq is unknown until a new actual B observation and is never inferred/reset by this reader.

New Root transfer review: exactly TWELVE fields. The actual frozen1031 source has TEN keys (older prose saying eleven was wrong; no old file is edited). Retain schema, requirements_sha256, review_id, reviewer, profile, transfer, authentic_b_receipt_path, authentic_b_receipt_sha256, source_human_reference, onsite_wiring_reference, and add only child_manifest_path and child_manifest_sha256. New schema is DEEPEYE-ROOT-UART-CHILD-TRANSFER-REVIEW-v1. profile is the exact typed child's full asdict(Profile); transfer is exact typed asdict(BTransfer), with scope exactly matching SHA-selected purpose. Canonical comparison rejects bool/int or float/int substitutions. Real receipt bytes are read/pinned. Root must independently review genuine fresh B recovery/initialization/sole-writer evidence and human/onsite wiring before authorization. For MOTION_READY, B must actually report current READY/OFF/unarmed/duty0 with both fresh healthy feedback channels; unchanged service rechecks actual feedback during STOP+STATUS attach. DIAGNOSTIC_ONLY cannot promote failure or FAULT evidence to motion readiness. The trusted Root record cannot cryptographically establish external origin by itself.

Motor always denies in this first adapter, for both purposes. Later release requires actual Root-observed signed direction/feedback trials (the planned yaw±15°, pitch±10° observations), retained fresh raw evidence and a separate SHA-pinned Root motor-release review bound to the exact child manifest/profile/transfer and operator authorization. That is a future source/activation seam, not a boolean flag, fabricated test, auto trial, hardcoded command script or new human confirmation flow. Existing human authorization remains the authority. No release token is accepted or created here.

Root-only new pure check: check_child_reader1057.py with approved Python -I -S -B -X utf8. It imports the new module inertly, checks source/AST/purpose/review boundaries and reads actual1063/1064 retained failure evidence. Cross-platform path-remapped dictionaries are explicitly synthetic mechanism fixtures only; no child approval, Root close/release record or B READY is written. Worker did not run Python, tests, board, UART, network, UI, Vivado or any process. Future trusted entry/pins are separate work; loaded1041/1031 remain unchanged.


Actual1068 compatibility: Root staged closed-record.json SHA646233d66e78a1750c399a9a52ab859b9d6a67b088bd93322565d47618648b99 and prepared1070 child-manifest.json SHA60d7b4f0074f24eccbe0dbf8a31672eb248ca33e4edc76bb3baabfc26e127b58, canonical child request9ea8eb9204302d2613990ddea11315515c4f6b1ae5401abfb96af4ca9784d429. Their exact key/digest/purpose/closure metadata match this reader. Prepared1070 intent is DIAGNOSTIC_ONLY and grants no attach permission; B currently owns MCU debugging. No new probe, transfer, review or hardware execution was performed by this worker.

First Root pure run failed and is preserved under red-first-pure-run/. Root then measured Python3.12.14 Windows handle ctime1793745659210842500 versus path lstat creation time1793745659209843700; both API observations, bytes and all cross-identity/mtime fields were stable. New1057 _read/_journal retain full fd-before/after equality and full path-before/after equality, cross-check dev/ino/mode/nlink/size/mtime, and additionally require cross-API ctime equality on POSIX. Thus Linux production strictness is retained; Windows pure controls no longer equate different timestamp meanings. Original1031 is unchanged. Root must execute the new controls once after this necessary fix.
