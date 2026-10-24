# Paired-acquisition retention repair

Repaired the independently reproduced IL-R1 blocker within the four assigned
product files. All successful native acquisition members are recorded before a
deferred registration ambiguity is raised. This is a frozen source candidate for
independent re-review, not approval for native execution or final acceptance.

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; work
`A-isolation-pair-repair-20261019-v1`; job
`child-a2db60ebe47f4c1c9bd1be8cd4c44fc6`; canonical agent
`/root/worker_results_review_20261018`. Original-endpoint native validation allowed
execution. Sole main remains Desktop director generation2. H01–H15 and contract
`DEEPEYE-HUMAN-LOCK-20261014/revision1` remain unchanged; canonical requirements
SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` verified.

The previous source manifest was independently read and hashed as
`0bdabec4a3c465e269c090bffd8fb690b2797750f47c4e4c7165e8e4d6a51376`.
All12 baseline candidate files matched that manifest before repair. The original
implementation job and independent review job remain completed history; neither
was reused. Source HEAD assigned by main is `addb2c944ea8f659c48a783c5af1853be8d24d65`;
candidate identity is bound to exact file bytes, not unrelated concurrent work.

## Root cause and bounded repair

The old single-reference registration appended an ambiguous record and immediately
raised. `own_process` and actual `win32.pipe` consequently never registered the
already-successfully acquired second handle. The independent original witnesses
were reproduced unchanged: writer82 and primary-thread92 were absent.

`owned_resources.py` now separates record creation from surfacing ambiguity.
Single `own_handle` retains its original raise behavior. A pair primitive attempts
both in-memory registrations, retains each ambiguity/error, then raises the first
original error. It performs no OS cleanup or reporting callbacks. Actual pipe
registration and CreateProcess's `own_process` use that primitive. Secondary
attribute-list cleanup failure remains separately recorded and does not replace
the deferred primary registration exception.

The same successful-pair boundary also exists at CreateAppContainerProfile:
one successful call returns a profile identity plus its allocated SID. `own_profile`
now records both, binds the SID to the recorded profile and updates the live
profile reference before surfacing an ambiguity. A mocked actual CreateProfile
regression verifies this third path. Other acquisitions in these two source files
return a single owned object per API call; their token/string/descriptor/attribute
operations are sequential allocations with their existing helper contracts.

Unknown releases are still cached and never retried. Pipe tests prove only the
unambiguous companion receives one safe close. A primary-thread companion remains
in recovery ownership if its process binding/terminal state is ambiguous. Both
members' ambiguities remain held when both values collide. The pure coordinator,
Windows backend, launcher, security policy and all other eight candidate files
are unchanged. No extra blocker was established within this assigned boundary.

This remains a trusted-owner, synchronous memory-registration guarantee: Python
memory exhaustion/abrupt owner death and invalid ownership preconditions remain
the pre-existing limitations. The pair path cannot recover resources after losing
the owner process, attest OS identity, or authorize replay.

## Actual RED/GREEN evidence

Independent tests and the offline author driver were copied byte-for-byte into
this new evidence directory. Their source hashes match the original immutable
files before and after execution. Exact argv/cwd/process-local env/exit codes and
source hashes are in per-run JSON; raw stdout/stderr bytes remain unmodified.
Native opt-in was unset, and TEMP/TMP remained inside owned output.

| Run | Actual result |
| --- | --- |
| Unmodified pair witnesses RED | 2 tests, 2 failures, exit1 |
| Added narrow registry/helper regressions RED | 24 tests, 9 failing assertions/subtests, exit1 |
| Unmodified pair witnesses GREEN | 2 tests passed, exit0 |
| Unmodified independent timeout/audit/profile/output checks | 3 tests passed, exit0 |
| Existing offline suite plus six new regression methods, once GREEN | **75 discovered / 72 passed / 3 native opt-in skipped, exit0** |

The added regressions cover process and pipe first/second/both-member ambiguities,
actual mocked CreateProcess plus a secondary attribute release error, preserved
primary error, safe pipe companion close counts, retained primary-thread recovery
control, and profile/SID retention through the actual mocked CreateProfile helper.
The second-member-only process/pipe cases already preserved both resources before
the fix; they remain compatibility checks. First/both-member cases and profile
first-member cases failed on the prior bytes and pass on these repaired bytes.

Only fake acquisitions were executed. No fixture process, AppContainer/profile,
native ACL mutation, service, credential, external message, queue, board or Git
mutation occurred. Existing policy tests exercised filesystem preconditions in
owned temporary folders; their unrelated token-read setup remained stubbed.

## Exact12-file candidate

| Product path | Bytes | SHA256 |
| --- | ---: | --- |
| `competition/deepeye/simulation/isolation/owned_resources.py` | 9095 | `b4c771286306a343d605e3c4d29db554960713f9cce246345e54cbc89829cf4e` |
| `competition/deepeye/simulation/isolation/windows_cleanup.py` | 4184 | `ca1771e1828fb8800b57ab3051f85df2e73601efe5e7874f42c8bca50361102d` |
| `competition/deepeye/simulation/isolation/prototype.py` | 16571 | `af54c6a5240be4e585f1c621034f5b687f79199595b82d54b2278253ceb4e452` |
| `competition/deepeye/simulation/isolation/win32.py` | 17780 | `813bb52876b00fb3843289d6d6de802679064045e0a25f46dd99df7ebced0d1e` |
| `competition/deepeye/simulation/isolation/policy.py` | 7119 | `a1945451dd6324f3cce2768cff8127f1a3755c8856061bf24d954b9a844afa11` |
| `competition/deepeye/tests/isolation/test_owned_resources.py` | 5832 | `b0380e1b2926ce4e10992af86f0d9186f159387771880fd78e6cc8d942ebd77b` |
| `competition/deepeye/tests/isolation/test_windows_cleanup.py` | 13706 | `10957397ba19a743f5bc05685ae2994c1e240f5b30dd741541e53148385f1f4e` |
| `competition/deepeye/tests/isolation/test_prototype_cleanup.py` | 9062 | `c7dfe79aad09418d8901cd1f34c059647ada32b5de086a773304e0bee90bbd24` |
| `competition/deepeye/tests/isolation/test_policy.py` | 11085 | `0596d77ade275426dfbdba6fc897f08eab258b734d324682105427b64afedf8f` |
| `competition/deepeye/tests/isolation/test_windows_live.py` | 4344 | `bfce80b3fa26be12d6f27e6994552a7dab776fd06a0df28860a4863955c5da74` |
| `competition/deepeye/docs/isolation_resource_cleanup.md` | 13427 | `135bee5d4a9fda0786456435b5e72c298e99d39b6a92aacc5635dd4a256c2518` |
| `competition/deepeye/docs/process_isolation_prototype.md` | 11697 | `f6caa7f58d95bf70c418cf3d66dc2f953f1d1480220cfc6bd1e38be78af4cdac` |

`frozen/` contains exact copies of all12 files, including the eight unchanged
candidate files. `repair.diff` contains only the four assigned file changes.
All **236** inherited dependencies and all
**123** saved files in the original author/review directories
are byte-for-byte unchanged; `integrity-after.json` preserves every comparison.
The accepted coordinator remains SHA256
`4e92844915c8e9e9e7e316a1844cb764c2c510f8d5158795de97b832204a235f`.
No source outside the four-file ownership or old evidence was written.

Next dependency: main/independent reviewer rechecks this exact repaired manifest
and original witnesses, then separately authorizes the prepared fresh normal,
timeout and persistence-failure native cases. All native cases, actual OS cleanup,
four-process isolation, G03, runtime/AI/game/hardware/board and formal acceptance
remain **not_run**. Nothing here weakens H01–H15 or accepts the full product.
