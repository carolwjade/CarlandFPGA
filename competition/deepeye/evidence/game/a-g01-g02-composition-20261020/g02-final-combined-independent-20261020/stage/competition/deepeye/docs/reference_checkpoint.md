# A reference checkpoint, 2026-10-15

Task DEEPEYE-IMPLEMENTATION-20261014/v1. The current director is Desktop chat
01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2.
DEEPEYE-HUMAN-LOCK-20261014/revision1 and all H01–H15 are unchanged; requirements
SHA256 is c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

Install requirements-host.txt in an isolated Python environment. From this
product directory, run `python -B tools/check_interface.py`. The command runs
the implemented checks and returns 2 while full R03 acceptance gates remain.
`--reference-only` returns zero only for the bounded software checks. Neither
mode enables hardware. `--output evidence/system/r03_validation.json` saves
commands, raw output, source hashes, the bound BOOT candidate and open gates.

PC_DIRECT now transports the exact STATE 0x08 heartbeat through the strict
hardware_bridge → world_authority board_response envelope. It carries health
and clock diagnostics. It cannot carry a physical motion-capture claim in
PC_DIRECT, create a sensor observation or renew an action deadline. The live
heartbeat-loss stop path and authenticated process transport remain runtime
integration work.

BOOT templates are software candidates. `bind_software_documents` binds actual
interface, host-schema, enumeration and timing-document bytes into the complete
SHA256; its first 16 bytes are carried on wire. Recheck the bindings before use.
BOOT_ACK must echo the request sequence, proposed epoch, session, mode, digest,
guard and slots. A byte-identity check is not measurement authentication.

All six exclusive window variants have exact nominal schedules: normal,
CONFIG, one control retry, one EVENT retry, physical GAIN and PC_DIRECT. EVENT
retry uses the otherwise unused retry-request anchor, uplink only, with no
CONFIG/control retry in that window. FAST uses 365 ms and STRESS 5500 ms.
PC_DIRECT reserves TELEM32 + STATE32 + EVENT20 = 84 bytes. Each profile is
checked over all 216 mixed three-window combinations, including partial frames
crossing the sliding-window boundaries. These mixed sequences stress occupancy;
actual mode changes still require STOP, a new session and BOOT. Nominal timing
does not establish measured baud/USB/turnaround/jitter bounds.

The UI checkpoint provides an editable Godot scene and free camera. It is a
development greybox: final B assets, authoritative volume collision, running
AI/board controls and full G02 acceptance are still absent. The sensor module is
an explicitly uncalibrated candidate; an acquisition callback failure now
invalidates old EM values until a later successful sample. Its engineering
kernel does not satisfy independent FDEM validation or G03/G09 by itself.

The local pipeline verifies immutable scope, duplicate work identity, file
ownership, terminal status and evidence/source/command/commit provenance.
Its product runners remain unimplemented. Tests use disposable local ledgers;
they do not operate the resident mesh or accept the 29 product cards.

Remaining R03 work is listed in interface.json and in the validation report:
TRACE/codec framing, register bitfields/reset and matched HWH, stateful
observation/mailbox/request integration, B/C exact-byte interoperability,
process isolation and measured physical bounds. Dependencies must not be marked
passed because these software references exist. Only A operates the board.
