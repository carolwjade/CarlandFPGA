# Finite Root-to-native renderer session

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
H01-H15 remain mandatory. This is renderer delivery and native presentation
readback only. Full Run, CPU/AI/board integration, H12, G03/R03 and all29
acceptance remain unestablished.

The trusted serialized Root creates
`RendererSession(absolute_new_directory, run_id)` from
`competition.deepeye.tools.diagnostic.renderer_session`. The directory's
parent must exist. An existing directory is refused, preserving all earlier
files. The constructor publishes a bounded bootstrap with schema 1, run ID,
random 128-bit hex correlation nonce, `max_messages` (2..16, including close)
and `lifetime_ms` (1..8000). Bootstrap is at most 1024 UTF-8 bytes. All message,
ready, ACK and terminal records are at most 4096 bytes.

The library launches no processes and performs no waiting loops. The caller
owns the Godot process, deadlines, original handles and cleanup. Start the
existing reviewed Godot with the actual simulator project and explicit args:

```text
Godot.exe --headless --path <simulator> --script res://viewer/authority_session.gd -- --session-dir <absolute_new_directory>
```

After `read_ready()` returns its correlated asset report, Root uses
`publish(frame_from_executor(original_executor))`. It normally reads one
`read_ack()` before publishing the next frame. These methods return `None`
while their specific response is absent; the caller must impose bounded
waiting. `publish` copies and validates the existing exact renderer frame
whitelist before writing. It does not claim to authenticate the frame's
original command. Wrong-run or stale structurally valid frames are rejected
by the native bridge and produce a negative ACK. Extra scene/seed/obstacle/
editor/oracle fields are refused by the Python whitelist before publication.

For each publication Root exclusively creates a private temporary file,
serializes a complete finite JSON document, flushes/fsyncs it, atomically
creates the final name with a no-overwrite hardlink, then unlinks the temp.
This requires an existing local filesystem supporting hardlinks. It does not
fall back to overwriting or non-atomic writes. Failure retires the session;
the unknown publication is never retried. Names are `frame-000001.json` onward.
Each envelope has exactly `sequence`, `nonce`, `run_id`, `kind="frame"`,
and `frame`. One message may be outstanding. The final slot is reserved for
`close()`, whose envelope omits `frame` and uses `kind="close"`.

The Godot SceneTree entry point loads the actual original `main.tscn`, binds
the explicit bootstrap run with `bind_authority_renderer`, and retains its
original drill target/body. READY reports the actual asset identity, mesh
count, presenter state/diagnostics and closed control gates. Missing/fallback
assets are reported, never promoted to complete body-model acceptance.
No first-frame auto-binding, duplicate drill, motion planning, physics update,
control endpoint, network listener, BOOT or action authority is introduced.

Godot reads only the next expected filename within its finite lifetime,
consuming that slot before parsing or applying it. Oversize, malformed,
unknown-kind, foreign correlation/sequence and extra-field envelopes fail
without calling the pose bridge. A valid envelope delegates all frame/run/
revision/geometry checks to the existing bridge. A negative ACK still
consumes the slot. A later out-of-order filename is never applied ahead of
the expected slot; if that slot never arrives, lifetime expiration ends the
process. The script does not enumerate or consume unrelated directory files.
The trusted writer's bounded slot count limits protocol files; external
writers are outside the directory's ownership assumption.

Each native `ack-NNNNNN.json` has exactly `sequence`, `nonce`, `run_id`,
`accepted`, `error`, `native` and `gates_closed`. `native` is obtained through
the actual viewer's `read_authority_presentation()`, not echoed input. Root
checks correlation, sequence, status, whitelist, native run/revisions and
STOP snapshot. Godot publishes its complete ACK through a private temp file
and rename in this single-writer directory. Existing ACK/temp names cause
failure; ACK publication is never retried after a possible pose effect.
Terminal state is `terminal.json` with `nonce`, `run_id`, `status`,
`last_sequence`, actual `native` and `gates_closed`. Close ends normally;
timeout, message budget, changed gates or ACK failure end unsuccessfully.
`read_terminal()` can observe the terminal file after the send deadline.

Nonce/run/sequence checks are correlation and structural checks, not source
authentication or protection against another actor with write access to this
owned directory. Python rejects duplicate JSON keys and nonfinite constants;
native parsing uses Godot's JSON object parser followed by exact field checks,
not a claim of canonical-byte JSON authentication. No native ACK or STOP flag
feeds back into Python full-volume physics, certifies collision freedom, or
enables the Run/continue/pause controls. A stopped presentation is not a
trusted STOP/action ACK for the control chain.

Focused tests exercise new-directory preservation, complete write-once files,
one outstanding message, foreign/malformed/oversize ACK retirement, frame
whitelist, count/lifetime and close. The separate owned native harness
starts one real hidden headless Godot process in a fresh complete source-only
stage. It dynamically creates synthetic-admission owner commits only after
READY, sends two distinct newly committed poses and a real owner revoke STOP,
and reads correlated actual transforms. Wrong-run/stale frames are sent via
the library. A final test-only raw tail sends extra-truth/foreign/unknown/
malformed envelopes and close to exercise native refusal without loosening
the production Python whitelist. It does not replay old fixtures or run old
suites, and synthetic admission does not establish live sensing/model/board
or complete H12 evidence.
