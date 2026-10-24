# Viewer-private owned Windows file commit

Godot `LayoutStore.save_new_async(path, text)` and the awaited shell Save As use
one retained worker, one one-shot Python helper and the reviewed
`layout_commit_windows.commit_new` leaf. The synchronous `save_new` API remains
a finite compatibility wait over that same worker; it contains no old
check/write/Godot-rename algorithm. Layout bytes are private geometry data,
never an AI/provider input, control capability, resource or executable content.

For a source checkout, launch with the approved existing Python installation:

```powershell
& <approved-python.exe> -I -B <simulator/native/run_viewer.py> --godot <absolute-reviewed-Godot.exe> --run-dir <owned-viewer-data-directory>
```

`--validate-only` checks the selected engine, helper bundle and existing Python
identity without opening the viewer. The launcher uses its actual
`sys.executable`, verifies pinned engine and small Python identity members, and
creates an allowlisted child environment. Provider/FPGA credentials, PATH and
PYTHONPATH are not inherited. It binds only this child process; it changes no
global environment, credential, provider, listener, service or installed config.
The launcher needs the existing venv's normal prefix initialization; do not add
`-S` to its own command on CPython3.12. The helper still uses isolated `-I -S`.
The standard library and existing CPython installation remain trusted; the
small identity manifest is not a complete runtime anti-tamper closure.

The helper is bound by the raw SHA256 of `layout_commit_bundle.json` and its
fixed sibling helper/leaf entries. A fixed quote-free hex bootstrap passes no
target or layout in argv. Isolated Python flags `-I -S -B -u` exclude implicit
script imports and bytecode writes; checked raw helper/leaf bytes are compiled
directly. The binary protocol is DLC1/DLR1, metadata at most4096 bytes, opaque
strict UTF8 payload at most1MiB, response at most16384 and stderr at most4096.
There is one commit call and no partial-write retransmission.

Only supported ordinary fixed local NTFS paths with direct HarddiskVolume drive
mapping are accepted by the native leaf. UNC/device/ADS/traversal/reserved and
visibly invalid namespaces are rejected before parent creation. Missing parents
may be created recursively by the worker after trusted-runtime preflight;
this convenience step is separate and non-atomic, may occur before the leaf
rejects an unsupported volume/ancestor, and never removes created parents.
The leaf alone exclusively creates/retains the source HANDLE through checked
write, flush, readback and no-replace publication. There is no Godot rename,
target deletion, path cleanup, orphan adoption, sweep or unsafe fallback.
Privileged namespace/filter/ACL manipulation, drive remapping and power-loss
durability are outside this bounded scope.

The UI waits5000ms while frames advance. On expiry it says the result is unknown
and the file may exist, permits ordinary editing and retains the unresolved
save fence. Save/Open remain inhibited until the worker and original helper
are observed terminal. The helper's process-local watchdog starts before stdin
and leaf loading, and exits124 after6s under ordinary scheduling. Exit124 does
not establish whether publication happened. Interpreter startup, scheduler or
kernel stalls may leave a job unresolved: no live join, replay or cancellation
claim follows a timeout. Same-path unknown results remain fenced for this
process; restart performs no automatic recovery or replay.

The worker owns its pipes. It records the exact original child exit with
`OS.get_process_exit_code>=0`. Only after a completed worker is joined, and
while exclusively owning the unreleased original map entry, one cleanup-only
`OS.kill` is consumed before its call. Its return is not termination evidence.
Godot attempts both original handle closes but does not expose their result;
map absence is not kernel-handle-close verification. An uncertain exit/map
remains retained. A late valid response is separate evidence and never replaces
the earlier unknown or reapplies saved geometry.

An exported PCK is not a Python filesystem sidecar. Export delivery requires a
separate explicit, reviewed runtime/helper installation and equivalent pins;
this source-tree launcher does not claim exported readiness. Missing bindings
fail closed before helper launch. File privacy is a viewer boundary, not proof
that other OS processes cannot access a user-chosen path.

The native leaf's completed19 NTFS tests are reused unchanged. New focused
caller verification is `tests/test_layout_commit_bridge.gd`, with separate
explicitly pinned test-only adapters for before-publication stall, response
loss after real publication, delayed response, trailing stdout and split frame. These
adapters are not production switches. No historical suites are rerun here.
Headless software evidence does not close mouse/DPI UI, G02/H09/fullH12 or all29
acceptance. H01-H15 remain mandatory.

The worker accumulates partial blocking header/body reads, observes the original
child's exact exit, then drains bounded stdout/stderr one byte at a time.
This helper and the pinned adapters spawn no children or extra pipe writers;
production stderr is bounded4096, so it cannot fill the pipe before exit. Under
these conditions zero from the final read is the scoped drain endpoint. Godot
does not expose the underlying Win32 read error, so this is not a new general
EOF/error-code guarantee. No `PeekNamedPipe` length query or log suppression is
used. Truncated/oversized/trailing output remains unknown.
