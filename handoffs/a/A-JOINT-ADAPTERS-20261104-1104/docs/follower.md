# PC host physical follower 1060

Task: A-B-JOINT-UART-20261104-R01/v1. Contract DEEPEYE-HUMAN-LOCK-20261014/revision2; requirements SHA256 `2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d`. Canonical requirements hash was independently read/verified before this source task. H01-H15 and original29 acceptance stay intact.

`host_follower1060.py` is import-inert. It imports only stdlib and receives the already-reviewed B classes through `api.FollowMapper`, `api.Follower`, and `api.SshClientAdapter`. It never imports B packages, changes package paths/config, creates NativeClient, reads native RPC, opens a network/process/UART/MMIO connection, handles credentials, or controls simulation. Root owns dependency source pinning and all hardware authority. FollowMapper/Follower are the frozen B1040 source used unchanged, with PC `time.perf_counter_ns` for both map and tick. The mapper's original acquisition interval and native grant remain unchanged; target events are derived own-pose targets and never actual angle/RPM telemetry.

Root initializes the mailbox/worker only when a new actual accepted motion-ready operation and source have been reviewed. Never activate this on the current unknown STOP1 / unresolved UART state. In the eventual host controller, construct once beside the existing unique native reader:

```python
display_mailbox = LatestDisplayMailbox(run_id=run_id, world_epoch=epoch, admission_mode=mode)
physical = HostFollower(display_mailbox, api=reviewed_b_api,
    client_factory=open_reviewed_client, run_id=run_id,
    source=display_mailbox.source, reference_xyzw=actual_reference,
    limits=reviewed_limits, motor_enabled=False,
    close_client=close_reviewed_client_without_rpc_replay,
    on_event=nonblocking_actual_feedback_sink).start()
```

The existing sole polling loop retains `sample = native.state()`. Add exactly this publication after that successful read, without changing its nested native/host records:

```python
display_mailbox.publish(sample, world_epoch=epoch)
```

No queue of poses is introduced: the mailbox replaces older snapshots, and the one IO thread pushes only the latest returned publication. While B's synchronous call is pending, Root's native/UI reader continues independently; pending publications collapse to the newest. The positive-call guard also peeks for a newer terminal/fault publication before any next pose/motor/keepalive call. After the first actual accepted sample, a source gap runs out the original B mapper deadline; it cannot receive an extended clock by repeated local ticks. Before that first source there is no positive command or lease to renew: the worker idles until an actual publication or Root close, without an arbitrary elapsed-time cap. Clock-domain translation is not performed.

Startup ordering is explicit: `snapshot()['client_opened']` becomes true, and `client_factory_returned` carries `client_opened=True`, only after the real client factory/open returned and B mapper/adapter/follower construction completed. Root's nonblocking coordinator waits for this actual barrier before initializing G05, because the first UART mapping must observe fresh G05 OFF/status0. It should additionally require `finished=False` and `error=None`. Root publishes only the first actual valid Native admission and later real continuous samples, and closes the mailbox on terminal/fault. This avoids racing G05 initialization with the actual first UART map.

Finally, default close is nonblocking and immediately closes the mailbox/discards pending positive targets:

```python
physical.close('root_terminal')
# Root may wait from final cleanup, outside a UI/native poll callback:
physical.close('root_terminal', wait=True)
```

All client/follower/STOP/transport-close operations run on that single IO thread. The factory must create AND open SshDisplayClient with `keepalive=False` there and return its raw instance. Its existing startup timeout remains unchanged. The optional `close_client(raw, *, stop_already_attempted)` callback owns actual EOF/wait policy; it must not replay commands or fake transport flags. Worker itself never kills/waits for a process. Without that callback, frozen `raw.close()` runs unchanged; its possible second STOP RPC receives B stdio's cached STOP result rather than generating a second device STOP. No `failed=True` fabrication is used. Follower STOP is attempted at most once even when its result is unknown. Close errors and actual STOP errors are retained in `snapshot()`.

The event callback runs on the IO thread and must be nonblocking. Each `client_reply` contains a deep copy of the unedited actual returned record before B Follower validation, so rejected result3 and unready feedback remain visible. `derived_target` is explicitly a computed target; `client_factory_returned` reports only factory completion. `observed_host_qpc_ns` is a separate receipt timestamp and never replaces source timestamps. Only the latest event/raw reply is retained locally; Root may journal events. No synthetic READY, measured RPM, or measured angle is supplied. A failing callback closes the worker rather than losing evidence and continuing positive IO.

Motor enable is an explicit constructor boolean, false by default; there is no live toggle or authority grant in this worker. Both `PC_DIRECT` and actual `FPGA_OUTPUT` bindings are supported and fixed for a run. A new run/source/epoch requires a new mailbox/worker; closed instances cannot restart.

`check_host_follower1060.py` contains the original eight controls (Root reported all eight passed), plus one new focused idle/barrier control. The new control deliberately waits350ms before the first fresh publication, showing that no positive command, STOP or closure occurs solely because the original250ms source age elapsed; it then accepts a fresh actual sample. Run the new control against the preserved `host_follower1060.before_idle_revision.py` with `--worker-source` for RED, then the changed source for GREEN. The original files and hashes are retained unchanged. The author did not run/import/compile either changed worker or controls; Root owns actual execution and evidence. Existing post-first-source freshness/expiry controls remain unchanged. No physical/network/UI effects occurred.
