#1087 raw non-MTR4 pattern actor — source only

Preserve human lock revision2, H01-H15 and requirements SHA256 `2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d`. Current scope bytes remain SHA256 `095c7d07e7b02de671ebd63074f057c654e222a8cb7cee788fc7eb9785249c39`, identical to previously canonical-verified revision2. G03/R03/all29 remain not_run.

`raw_pattern1087.py` is import-inert, denies runtime without the explicit flag, and never controls MCU/debugger state. Startup only invokes the pinned1041 import bootstrap/actual1031 read-only parent factory, acquires the existing UART hardware lock, maps the HWH-derived actual UART descriptor with the same Device, checks status exactly `0x04`, and emits JSON `raw_pattern_ready`. It does not transmit or consume startup RX bytes. FD1 is isolated from native/PYNQ output as in1059.

Stage the source flat beside the existing1018 `diagnostic_stdio1041.py`, reader1031 and unchanged1041 dependency closure. Root-only launch:

```text
<PS-python> -I -B -X utf8 <stage>/raw_pattern1087.py --allow-non-mtr4-pattern --approved-plan <actual14-key-plan> --approved-plan-sha256 <file-SHA> --operation-directory <originalphysical1018directory> --build-review <actualBUILD_REVIEW1039.json> --build-review-sha256 beb8c519ec26998d03a6393a358e9dbe253d86d640de1cc2babf1ff3ee7fedf9 --raw-operation-id <freshRootID>
```

The existing `/home/xilinx/deepeye-uart-state/mcu_uart.owner.lock` is opened without creation using `O_RDWR|O_NOFOLLOW`, checked as one regular inode and acquired with `LOCK_EX|LOCK_NB`. Parent path/inode stability and actual physical identity are checked at phase boundaries. A new exclusive `raw-operations/<freshRootID>/journal.jsonl` records actual parent, lock inode, raw statuses, byte-write/read intents and returns, failures and actual lock release. Existing MTR4 operation/sequence/consumed-transfer state is untouched. No fake BTransfer,1031 authorization call or MTR4 telemetry is created.

## Immediate B→A-first ordering

Latest B340 reports possible remaining XDS-TX→PB7 connection; isolation is unresolved. **Do not dispatch A TX8.** B's passive XDS_RX input does not itself justify any active A transmission.

1. Root starts this actor and confirms `raw_pattern_ready`, actual binding/pid/lock inode and empty/error-free status. Default transmission is false.
2. B alone verifies its actual CPU halt/debug-free UART setting, then explicitly sends the eight known bytes from B toward A. A does not control the MCU.
3. After Root retains/reviews B's genuine **sent-completion** receipt, Root dispatches RX8. The≤5000ms read window starts at that request, after B sent the bytes; it does not include peer-message latency. A reads the eight retained FPGA FIFO bytes without prefix stripping or flushing.
4. A TX8 remains unused until XDS-TX isolation is actually confirmed, B has verified the **MCU's actual RX FIFO capacity** can hold eight bytes, and Root receives a new genuine B capture-ready receipt. Do not infer MCU FIFO depth from FPGA UARTLite's16-byte RX FIFO. B's CPU/peripheral hold policy and FIFO-depth evidence are B's responsibility.

Directions are independent: RX8 may run before TX8; each direction has exactly one attempt per raw operation. Root, not an audit-hash field, decides when each phase is authorized. The code never interprets a peer body as human authority.

## Exact stdin commands

TX8/RX8 each require exactly these fields; op is `tx8` or `rx8`:

```json
{"op":"rx8","request_id":"ROOT_SELECTED_ID","capture_id":"REAL_B_CAPTURE_ID","b_receipt_sha256":"ACTUAL_64_LOWERCASE_HEX_SHA","timeout_ms":5000}
```

Identifiers are bounded ASCII; the SHA is an audit reference to Root's retained authentic B receipt. No arbitrary payload/hex field exists. TX always uses `55a533cc0ff06996`, once, and waits for observed TX-empty within the per-call window. Its return proves only local writes/TX-empty; `B_receive_proven` stays false until B supplies its actual RXDATA readback. RX collects exactly eight bytes/raw register values/statuses and reports pattern equality. Error/extra pending bytes are recorded and left unread; no prefix is ignored or FIFO flushed. A failed/uncertain phase poisons the actor and is never replayed.

Close is exactly `{"op":"close","request_id":"ROOT_SELECTED_CLOSE_ID"}`, or stdin EOF. Both release ownership only: no TX, MTR4 STOP/ARM, UART control/reset, PL reload, clock or G05/TRACE write. Closing does not return a new protocol data frame; Root waits for the actual process exit and retained lock-release journal. FPGA/MCU readiness, actuator operation and MTR4 validity are not inferred from this raw test.

`check_pattern1087.py` supplies new import/AST/pure mock controls for Root to run once. It includes RX-before-TX, startup/no-TX, unknown startup data left unread, fixed TX bytes, extra RX untouched, errors, timeout/no retry, flag denial and pins. Worker did not execute Python/tests or perform lock/board/network/process/UI actions. `SOURCE_CHECKS.json` is absent until Root executes it. Source availability alone does not authorize B to hold the CPU or A to transmit.
