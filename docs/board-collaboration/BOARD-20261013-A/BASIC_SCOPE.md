# Three-machine shared-board basic scope

Human task: `task-ab3be3460087da296f2e5fb7`, version `1791877413189`.
The coordination branch confirms A owns this instruction. This scope narrows the existing board task; it does not start a second hardware executor.

## Completion criteria

1. B and C each submit one identifiable payload to A through the existing Git/manifest handoff. If Git connectivity blocks C, use the incremental bundle route already authorized by the original A owner and preserve its commits for the PR.
2. The original A/root Desktop board owner executes each payload once on the connected board, serially. Preserve the operation ID, request hash, tested commit, command, exit status, stdout and stderr.
3. A returns the actual result or error to the same PR and the submitting peer. B and C each confirm receipt once. These steps establish the basic shared-board workflow under A coordination.

## Existing assignments

| Node | Current work | Operation |
| --- | --- | --- |
| B | `B-base-overlay-bramtest-v2` | `BOARD-20261013-A:B:base-bram-v2` |
| C | `C-board-error-feedback-v3` | `BOARD-20261013-A:C:error-feedback-v3` |

Reuse the existing payloads and credible evidence. Do not rewrite finished tests merely to make them smaller. C's older independent BRAM review is not a prerequisite for this basic closeout. Obsolete GPIO contracts remain historical records and must not be executed.

No extra stress, performance, outage, new RTL, synthesis or implementation campaign is required for this scope. Keep necessary payload review, hash checks and safe board state handling. Do not repeat successful board operations for presentation or documentation.

C's expected exception demonstrates the error-return channel when A captures the expected marker and exit status and C receives that result; it is not a passing functional FPGA test or a board fault.

## Verified state when scope was issued

A's saved real-board runtime probe completed with exit 0. The current A result record still marks B/C payload execution and readback pending. The scope and current assignment notices were transport-acknowledged by both B and C; that alone does not establish their model completion or board acceptance.

Physical-board ownership remains the original A/root Desktop owner recorded locally. The scope-handling session performs no board operation. Existing public evidence: [PR 7](https://github.com/carolwjade/CarlandFPGA/pull/7).
