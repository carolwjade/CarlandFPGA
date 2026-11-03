# RootLoadedProduct adapter 1031

Owned scope: this new directory only. Contract DEEPEYE-HUMAN-LOCK-20261014/revision2, requirements SHA256 2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d. H01-H15 remain fixed. A Root alone operates the PS/board; this worker performed file operations only.

Entry point:

    build_actual_reader(service_api, *, approved_plan_path, approved_plan_sha256,
                        actual_operation_directory, transfer_review_path,
                        transfer_review_sha256)

It returns a concrete subclass of the exact SHA-pinned B service RootLoadedProduct ABC. Importing this file defines stdlib helpers only. Construction requires root, armv7l and current BOOT before any PYNQ import. The adapter creates read-only-use G05/TRACE MMIO mappings and a parser of the actual operation HWH; it never creates Overlay/Bitstream, downloads, resets, writes clocks or writes UART. First adapter scope is always DIAGNOSTIC_ONLY. authorize_motor always raises.

Root staging must place root_loaded_product1031.py, load_once_joint50_1024.py and verify_uart_joint50_hwh.py as siblings in a fresh PS stage root, with the unchanged functional50_board_a.py under snapshot/competition/deepeye/tools/diagnostic/. Add the fresh absolute stage root and snapshot root to sys.path before importing. Stage the verified B service package with all of its existing dependency paths and hashes preserved, and pass that actual imported module as service_api. Its own ProductUartService.attach still checks all package dependencies. The source pins are constants in this reader and DELIVERY.json. No existing operation or worker is reused by this delivery.

The approved plan is the adopted1024 fourteen-field plan. Its entire file SHA and canonical request hash must both match. actual_operation_directory must equal operation_parent/operation_id exactly. The adapter requires the actual operation-started.json, load-started.json, load-returned.json and clock-readback.json written by the original loader, with identity and clock fields checked. It reads and hashes the operation's functional50_<request first24>.bit/.hwh, plan mapping and pinned original baseline during construction; validates the actual staged HWH through1024; caches the actual HWH bytes; and retains stable file fingerprints. No multi-megabyte artifact hashing occurs in read_current.

Each read_current checks PID/thread, current /proc BOOT and watched-file fingerprints; reads actual PS SLCR clocks through the old _ps(Clocks); verifies source0/pll20/div10/div2 and unchanged other PS clocks; reads TRACE ID/version/channels/rate/tick/FIFO identity and four actual little-endian BUILD_ID words; and reads G05 ID and ABI2. It deliberately does not constrain G05 status after STOP. Three fresh typed IP descriptors come from the maintained RuntimeMetadataParser.ip_dict and must match the verified actual HWH windows. The returned ProductBinding is assembled from these actual observations and retained proven load artifacts, never copied from Profile.expected. The UART timing/net/reset fields come from actual HWH ports and parameters. The dedicated UART is mapped only after a successful real review and another full read_current, in the same owned embedded device context. It can be mapped only once by this instance.

Root review record: exactly these top-level keys, no approved/READY booleans:

- schema: DEEPEYE-ROOT-DIAGNOSTIC-TRANSFER-REVIEW-v1
- requirements_sha256: the fixed revision2 requirements SHA above
- review_id: Root's nonempty bounded reference
- reviewer: A Root
- profile: exact dataclasses.asdict(service_api.Profile) for this real operation/run/source, including the complete expected ProductBinding
- transfer: exact dataclasses.asdict(service_api.BTransfer), including operation_id, transfer_id, mcu_observation_id, last_seq, evidence_sha256 and scope=DIAGNOSTIC_ONLY
- authentic_b_receipt_path: absolute, regular, single-link, no-symlink path to the retained authentic B transfer receipt on the PS
- authentic_b_receipt_sha256: SHA256 of those actual receipt bytes
- source_human_reference: retained reference to the genuine human instruction/wiring confirmation
- onsite_wiring_reference: retained reference to Root's onsite power/ground/TX/RX/no-XDS check

The nested profile expected binding pins operation_id, request_hash, boot_id, build_id, bit_sha256, hwh_sha256 and mapping_sha256, plus actual FCLK, three IP descriptors and clock/reset nets. Root authors this review only after authentic B unique-writer handoff and genuine human/onsite wiring confirmation for the new actually loaded generation. Compute transfer_review_sha256 from the finished local review file and pass it explicitly. Do not create a placeholder review or fabricate receipt/READY evidence. No real review or receipt is created by this delivery. Missing records, mismatched typed values, a changed SHA, foreign generation, missing retained receipt or MOTION_READY scope all refuse authorization. The authentic origin and human authority are Root's trusted boundary; a Python dictionary or subclass cannot cryptographically prove them.

The first adapter supports the B service's diagnostic STATUS/STOP path only, including its real FAULT-disarmed reply behavior. Current MCU evidence remains FAULT4/no servo feedback under B ownership. No ARM, pose, follow or motor authorization is provided. A final diagnostic transfer must await the new actual loaded identity and real B handoff. RootSIM/native Follower/QPC stay on the PC; this reader and UART service run on the PS.

New pure check: run check_reader1031.py once with the approved Python and -I -S -B -X utf8. It imports the reader without invoking its constructor, checks source/AST/review shapes, and reads the pinned actual1026 HWH solely for XML metadata extraction. It imports the old inert helper only for its pure XML helpers; it runs no old tests. It does not import PYNQ or create any Root capability. Worker did not launch Python. Root must retain its actual output and exit code separately.

Actual1026 HWH used by the metadata control: D:/codex-tmp/a324/.local/a1026/p/functional50_diag.gen/sources_1/bd/functional50_diag/hw_handoff/functional50_diag.hwh, SHA256 ae54a0add90e0ba80da1143ab260d6c9945421b54ae62cec4adb6704eaec59f4. This is generated metadata only; it is not a BIT, routed design, PYNQ parser, CSR, UART, board or final acceptance result. No arbitrary runtime/operation cap is introduced. G03/R03/all29 remain not_run.
