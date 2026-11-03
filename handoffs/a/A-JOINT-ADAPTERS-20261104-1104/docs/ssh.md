# Root SSH private-input seam 1077

Task A-B-JOINT-UART-20261104-R01/v1. H01-H15/revision2 requirements SHA256 remains `2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d`; original29 remains unaccepted. This is source preparation only. Activate only after a fresh genuine B motion-ready handoff; the current B MCU debug boundary remains held.

The sole PC gap addressed is the existing PYNQ sudo input before B's ready handshake. `root_ssh1077.py` wraps Root's injected, already reviewed frozen B `SshDisplayClient` class. Import and construction launch nothing and request no credential. It never reads a credential path, imports PYNQ, opens serial/native RPC, loads a product, translates QPC epochs, or adds a source lease. Root retains trusted argv/source pins and constructs the one process factory and stderr file. All active methods must run on the same IO thread that constructed the wrapper.

Use inside HostFollower1060's `client_factory`, which already runs off the NativeClient/UI thread:

```python
def open_reviewed_client():
    raw = RootSshDisplayClient(
        reviewed_b_SshDisplayClient, reviewed_argv,
        credential_supplier=root_private_bytes_supplier,
        process_factory=reviewed_process_factory,
        stderr_sink=root_new_exclusive_stderr_file,
        on_event=nonblocking_transport_audit_sink)
    raw.open()
    return raw

physical = HostFollower(..., client_factory=open_reviewed_client,
    close_client=close_root_ssh_client, ...)
```

`credential_supplier()` must return exactly one nonempty `bytes` line, LF-terminated, no CR/interior LF/NUL, at most4096 bytes. The wrapper calls it once after the one process starts, writes once directly to `stdin.buffer`, and flushes once. The local reference is released; credential bytes are never converted to text, stored in object state, printed, hashed, copied to a file, placed in argv, or passed to event callbacks. Supplier/write exception text is intentionally sanitized because it may contain the input. Audit reports only `credential_written`, phase and error class, without input length or value. The supplier owns any actual secret retrieval; this source does not implement it.

Popen receives piped stdin/stdout in text UTF8 mode and Root's file directly as stderr, so stderr cannot fill an undrained pipe. Windows creation uses CREATE_NO_WINDOW. Stderr sink ownership transfers to the wrapper and is closed after confirmed process exit; do not share it with another writer. The original B bounded reader and `_receive(45)` handshake are reused. There is no heartbeat. The original ready dictionary is returned unchanged and exposed as a defensive `welcome` copy; its actual status can remain result3/unready and is never promoted to physical readiness. Session and `clock_ms` are copied into B's original relative-deadline client. Default `seed_ready_request_id=True` sets B's counter to the actual welcome `request_id` (or0 when absent), so the next B call increments that real counter. No initial pose/motor/status call is invented. The inherited per-command timeout stays unchanged unless Root explicitly supplies another one.

`call`, `pose` and `motor` proxy the reviewed B methods, preserving their session/request/relative deadline behavior. Actual replies remain unedited and can be observed through `ssh_actual_reply`. An explicit STOP is marked attempted before IO; neither unknown-result STOP nor any failed command is replayed/reconnected. After STOP, additional calls are rejected locally. Both source declarations remain the remote profile's actual source; this wrapper does not choose/fabricate them.

`close_root_ssh_client(raw, *, stop_already_attempted)` is the direct HostFollower close callback. With actual prior STOP history it sends no new RPC or device command. Normal default `raw.close()` attempts one STOP only if no STOP has been attempted and the session is live, then sends EOF, calls actual `process.wait()` with no new fixed deadline, joins the existing reader, closes stdout and Root's stderr file, and retains the real return code/handle states. It never calls the frozen B close implementation, so its fixed2s terminate/kill path is not entered. It never fakes `failed=True` for successful normal closure. Actual failed open/call preserves B's genuine failed state. Failed-open cleanup uses EOF/wait and no guessed pre-handshake STOP. A failed actual wait is recorded as unknown, does not imply termination or permit retry, and leaves outputs owned for Root's explicit reconciliation.

`audit` contains actual open/credential-write flags, real PID, STOP reply/error class, EOF/wait/reader/handle outcomes and close errors. All event callbacks must be nonblocking. They receive only explicitly selected protocol/audit values; no credential input is supplied. A callback failure is preserved as a failure and cannot cause a reconnect/replay.

`check_root_ssh1077.py` supplies ten new pure controls using the actual frozen B client with fake process/streams and a literal fixture credential: inert activation, one private write/original handshake/request counter, explicit STOP plus EOF, default one STOP, sanitized supplier failure, malformed welcome, unknown STOP, one-thread ownership, welcome defensive copy, and unknown process-wait outcome. No new code was executed/imported/compiled or tested by the author, per Root's instruction. Root should run these focused controls once and inspect actual outcomes. No real credential, Python/network process, board, or UI action was performed by this source task.
