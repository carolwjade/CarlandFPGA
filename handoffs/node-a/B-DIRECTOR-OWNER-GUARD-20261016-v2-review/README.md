# A owner-guard v2 independent review

Decision: `OWNER_GUARD_V2_RECOVERY_OFFLINE_ACCEPTED` for the specified recovery increment only.

- tested_commit: `2057f51ae6fe54ad7a343510c29f27bc60e76d9b`
- source_commit: `0a2afa358c9775fe4d9faee77ec0b0aa4fa9df57`
- operation: `B-DIRECTOR-OWNER-GUARD-20261016-v2`
- request_hash: `14c37945047e2cc53eebc1aae790ee258d2e6e9d337df819a63d57445ecf6c25`
- manifest_sha256: `96cf90fbf84b8f7743551d8e7236c5d6b16085ffd4bcd9313280b06bbaa6a327`
- controller task: `B-RUNTIME-REPAIR-20261015/v1`; manifest task: `B-RUNTIME-CONTINUITY-20261016/v1`.

All 23 artifacts match manifest sizes/hashes and exact Git blobs; source/test bytes also match source commit. Standard handoff verifier passed. A independently ran the same 107 targeted tests on Python 3.12.14, exit 0, unittest 8.108 seconds (process 9.125 seconds). The asyncio debug slow-task notices in the unmodified raw stderr are diagnostic output, not failures.

A independently reproduced both malformed-declaration and wrong-version dead ends at v1 `f26caaeea99fde4378f9a8d12e38aa97ef15eac7`, then ran five v2 probes: malformed closure, wrong-version closure, persisted one-shot unknown attempt, persisted supersession, and transaction rollback. These reopen both fixture ledgers, preserve original envelopes and identity, reject unknown withdrawal and automatic replay, preserve successor holds, and prove all three transition writes roll back together on an injected SQL failure. Zero App client requests. Probe source, exact commands, original negative results and raw outputs are included.

Root read the scoped diff and independently verified the completed native audit report and its actual completed provider/model/effort metadata. No blocking defect was found in supported v2 transitions. A conditional orphan-record idle-check observation is retained in `review.json` and `child-review.md`: no supported write path producing it was found, and it is not claimed as a reproduced normal-operation failure.

`evidence-hashes.json` indexes raw bytes. `regression.json` and `independent-probes.json` contain exact command arrays, interpreter, timing, exit codes and log hashes. To rerun the candidate-only probes from a checkout of the tested commit with this evidence directory available:

```powershell
& <python312> -B -X utf8 <evidence-directory>/independent_probe.py <checkout-of-tested-commit>
```

Use `--v1` with a separate archive of the original v1 commit for the negative reproduction. The script uses disposable offline databases under that checkout's `.local` directory. Its stop callbacks are fixture callbacks only; they never call the real service stop command.

This closes only the v2 code/offline-fixture recovery dead end. PR29 was already at `dcace5700a334ab058522d45ccb6e1d78037f817` when read back; later changes are outside this decision. Whole-PR acceptance, actual App consumption/wake, deployment, reconnect, merge, RTL simulation, synthesis, implementation, physical board and product acceptance are `not_run`. Caller-reported review strings do not authenticate App history. Actual writer inspection and the existing admission/idle fence remain necessary. Old failed/unknown work is not replayed.

DEEPEYE-HUMAN-LOCK-20261014/revision1 H01-H15 canonical requirements hash independently recomputed: `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`. Sole director and implementation ownership unchanged; A alone operates the physical board. Public feedback/readback receipts are recorded separately after publication.
