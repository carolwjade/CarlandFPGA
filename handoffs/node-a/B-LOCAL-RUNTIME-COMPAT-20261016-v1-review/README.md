# A independent review of B local SDK compatibility port

Decision: `LOCAL_RUNTIME_COMPAT_OFFLINE_ACCEPTED`, scoped to this minimal increment only.

- Tested PR29 commit: `3c7ccdcf9e7beb3b11e3e8edd1ce7e91939d300a`
- Source: `27bc2c54f3469e3a521289fa1bbd6ea8af3451ec`
- Operation: `B-LOCAL-RUNTIME-COMPAT-20261016-v1`
- Request SHA256: `1cd8472f2589a70fff5cda18138f8c23a332e9650a7d6b393268137d69a545eb`
- Manifest SHA256: `12874c9c905f95cb3b9facb7673f8602b1e5e1ede2e73de1c8481631ffe846ad`
- Controller task: `B-RUNTIME-REPAIR-20261015/v1`; manifest task: `B-RUNTIME-CONTINUITY-20261016/v1`.

All 17 manifest entries match raw Git blob bytes, sizes and hashes. All seven source-validation hashes also match the source commit. Source changes are only feishu_channel.py, its two added tests, and the explanatory evidence README. No runtime/test code changed between source and submitted head. The standard handoff verifier passed.

A independently reran exactly the 19 targeted tests, with Python 3.12.14: exit 0, unittest 1.484 seconds, process 1.812 seconds. The original protobuf deprecation and unclosed event-loop warnings remain in raw stderr. An asyncio slow-task diagnostic is also preserved. The exact invocation is in regression.json:

```text
python -X utf8 -B -m unittest tests.test_feishu_channel tests.test_runtime.NodeRuntimeTests.test_feishu_config_and_result_queue_do_not_require_network_at_load tests.test_runtime.NodeRuntimeTests.test_peer_presence_changes_stay_internal_without_model_turn
```

A read the actual source diff, associated call sites and installed SDK source. The change moves only the default SDK import/factory loading to a worker thread; the allowlist, disabled DM policy, strict security mode, injected factory path, ingress/outbox and cross-thread controller delivery are preserved. One additional fresh-process probe using the actual installed lark-channel-sdk 1.4.0 confirms a distinct SDK loop while the controller loop remains running. No channel instance or external network request was made. Probe source, SDK source hash, precise command and raw output are included.

B's baseline raw failure log was verified, not rerun: it contains one behavior assertion failure and one missing-new-helper AttributeError. They are not two independently demonstrated production defects. B's private overlay ZIP is not supplied by the manifest; A does not claim to have reverified its CRC/hash or B's local bytes.

The unclosed-loop warning is not resolved by this acceptance. A fresh-import check cannot prove live connection, shutdown, reconnect, full SDK resource cleanup, or fix an SDK already imported on another loop. Those stages remain not_run, as do whole-PR acceptance, service deployment, permanent App wake, merge, RTL simulation, synthesis, implementation, physical-board and product acceptance. The five B local conflicts and custom launcher remain separate deployment work. Historical owner-v2/cache results are not transferred here and no unchanged historical full suite was rerun.

Serial A-main review; no child or concurrency expansion. H01-H15 hash recomputed: `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Sole product/director ownership and A-only board authority unchanged. No live state, proxy configuration, credentials, SQL, locks, service or scheduled task was modified.

`evidence-hashes.json` indexes raw bytes. Publication and substantive B readback are recorded separately; transport delivery is not substantive acceptance.
