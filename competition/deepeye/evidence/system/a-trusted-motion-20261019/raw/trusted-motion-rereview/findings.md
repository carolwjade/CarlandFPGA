# TM-R1 narrow repair: independent rereview

**TM-R1 is fixed at the reviewed frozen bytes; no new blocking finding in this narrow repair.** Independently rerun full 137 methods, byte-identical original eight methods, and three new safe-continuation methods all pass (exit 0 each). This supports bounded local software approval of the repair; main retains integration, publication and acceptance decisions. All 29 formal cards remain not_run.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work `A-trusted-motion-rereview-20261019-v1`; native job `child-44006d600dab476bb7425fbe2554b664`; reviewer `/root/pc_direct_review_20261018`. New lease validation returned execution_allowed=true before project operations. Original A Desktop director generation 2 remains the sole main. Human contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 and canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` were independently verified unchanged.

## Tested identity and delta

The repaired source manifest SHA256 is **1165585bb6e1bb049edb15a8df67e31f371203f6b6d22a03774d0e3ee5251533**. All four entries match current source, main's frozen files and this rereview's snapshots:

| Path relative to competition/deepeye | SHA256 |
| --- | --- |
| simulation/authority/motion_executor.py | e897764801a57e0add376c8949e4c9bbec14663b092d75a82be739b7290dfd62 |
| simulation/authority/motion/passage_phase.py | 19ba2644db3b9bf3e78af7dddc896ee2e5ebea1cc6363b936aea5110928df6fe |
| tests/simulation/test_motion_executor.py | 6f475a2fc2071df8fd2e8f2d82c434ab9c4a9d0d402b3df6b18c8a8ede48cf90 |
| docs/motion_executor.md | 144bb611ebc5c5a1aff1568cb8b37759962c4aa2f0fd32e3469d2d30759a1390 |

Among the original 35 relevant files, exactly three paths changed: executor, its test file and its documentation. The remaining 32 are unchanged; that count includes passage_phase.py, which also appears in the four-file candidate manifest. Before copies match the previous review's snapshots. `repair.diff` records the complete source/test/doc delta. The pre-existing passage AST prefix remains equal; the helper itself is byte-identical to the prior candidate.

The entire production-code delta is a try/except around the later materialization call at `motion_executor.py:193`: catch BaseException, call `_revoke('passage materialization failed')`, then bare re-raise. No nested `_entry` guard, new authenticator, time-mapping change, geometry change or post-fence work was added. `_revoke` retires pending handles, changes root identity, clears the command and stops while preserving pose/frame/history and any existing trial-failure latch.

## Independent behavior checks

| Fresh command group | Result |
| --- | --- |
| Same five-module full suite selected by main | 137 passed, exit 0 |
| Original independent script, copied byte-for-byte | 8 passed, exit 0 |
| Separately named safe-continuation suite | 3 passed, exit 0 |

Exact argv, cwd, interpreter flags and environment are in `commands.json`; original raw stdout/stderr are saved for all three groups. Commands used ROOT `.local/venv/Scripts/python.exe -B -X utf8`, product cwd and per-process product/dependency PYTHONPATH. TEMP/TMP were confined to this evidence directory. The outer orchestration also exited 0. No stale log was reused as current test execution.

The new safety continuation preserves the original observer's scenario but asserts the repaired behavior rather than relabeling its unsafe exit-0 observation as a security pass:

1. After one real numerical commit, standalone materialization raises the exact original MemoryError object. Already committed frame/pose/history remain available. A later successful passage read does not reactivate the store; another prepare with the old admission is rejected and pose revision stays 1.
2. A pending handle existing before a KeyboardInterrupt materialization fault is retired. The exact cancellation object propagates, and attempting to commit that handle never invokes its fence. Unknown failure does not newly set trial_failed.
3. A ValueError materialization fault caught inside the final callback still revokes the root. Returning a structurally valid later fence cannot publish; the already committed frame and pose remain unchanged, callback count is one, and the store stays stopped.

The main's two new regression methods also pass independently in the full suite, covering standalone pending MemoryError/ValueError/KeyboardInterrupt and the caught callback case. Normal nested prepare access still works, including the real-runtime numerical integration fixture. The original eight methods continue to check successful suffix call placement, time-gap mapping/prior-event preservation, identity/deadline/duration checks, retired handles, overlap, world invalidation and trial latch behavior. Successful post-fence geometry/hash/materialization/replace guards remain satisfied.

No unsafe continuation was reproduced at the repaired bytes. Source and tests agree on the intended policy: stop and require recovery admission after the unknown materialization fault, preserve the committed effect, and infer neither collision nor arrival. Already committed motion must not be rolled back or replayed.

## Scope limits and handoff

This is a narrow repair review, not an additional full fault campaign or proof against total process memory exhaustion. The injected allocation failure is confined to materialization; the process must still be able to record revocation. Original RED logs and the prior unsafe observer remain unchanged in their original evidence directories.

All 35 relevant source/input byte streams were unchanged across this rereview. Only `.planning/deepeye-resume-20261018/trusted-motion-rereview/` was written. No product repair, Git mutation, Run/provider activation, live OS fixture, service, hardware/board, credentials, external send or additional agent occurred.

Genuine BOOT/source/clock/AI-lifetime providers, world/asset containment and registry delivery, renderer/material behavior, both live control chains, actual runtime/game/board and all 29 formal cards remain pending/not_run. No deferred production feature was treated as a new blocker here. Main can take the next integration decision using this exact manifest and the preserved original failure/repair chain.
