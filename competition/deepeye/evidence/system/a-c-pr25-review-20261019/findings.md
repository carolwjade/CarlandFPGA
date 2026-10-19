# C PR25 new-head independent software review

No blocking defect found in the two named changes at **942fa309ffc8f1d32c816cfa643b009b031d7d0a**. The old nested-STOP and retained-timing witnesses now pass as safety regressions. The TRACE experiment passes the bounded offline decoder checks. This is evidence for the main's software review decision; it is not runtime, public ABI, physical or final product acceptance.

Work `A-C-PR25-REVIEW-20261019-v1`; reviewer `/root/pc_direct_review_20261018`; job `child-e678319dd7f34a93893ddc7e044ee414` authenticated with execution_allowed=true before project work. Sole director remains original A Desktop generation 2. Human contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, H01–H15 and canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` independently verified in ROOT and candidate scope JSON. Both scope documents were read. No requirement amendment.

## Exact identity and artifact checks

| Operation | Source commit | Request SHA256 | Manifest SHA256 | Verified artifacts |
| --- | --- | --- | --- | ---: |
| C-DEEPEYE-REVIEWFIXES-20261018-12 | c770d8235b078fb351e8c4773dd3f7cf51c0768a | ac9671977fa3e3cab5f81a63cdfd5edb06eb7437bfc85812c19b37496d6ab220 | 216270732b1045fbb5eddcbe3f34dfe44df1432a41bfde11b88fd01b19edcaee | 202 |
| C-DEEPEYE-TRACE-CANDIDATE-DECODE-20261018-14 | 3c1e584942bab4207b694f27ed116efb84ceedd7 | 3102d6d5e65dad3dfc6dba65eea465d7ac91816a65413d36b8825e2e71eb800e | 85e2aac41409988a6f0704d438b6a583d6de6530b95052e34cbd82df6df4fa9a | 70 |

HEAD and a clean checkout were checked before review and after tests. Every artifact's source-commit blob equals its current-head blob and the declared size/SHA256. Canonical request hashes were recomputed. All 272 exact blobs, original failure logs and exact handoff manifests are retained under this evidence directory. Checkout hashes, blob IDs and CRLF-only differences are recorded separately; tests used exported **Git blob bytes** copied into isolated scratch, avoiding implicit line-ending substitutions and peer-log writes.

The six original data JSON files are byte-identical to old head `31267d6c4ae284b8788ebb457f49c4ae5a49c60c`. The two newly preserved historical generator snapshots exactly equal that head's former live parsers. They were hashed, not executed. No old acceptance was inherited: current tests loaded the new source. The operation-14 delta from operation-12 final `cdbb6b4daef1ae1df324accd4d5086b48d005c6b` consists only of its new evidence and handoff directories (73 files); no existing production source/test changed in that increment.

Core reviewed source hashes:

- Motion adapter: `18c02349e9ebe1387e6763e90c707de67208407f067088edacffa31ce99dedda`.
- Independent candidate decoder and its QA snapshot: `b02010280b72d3a94842db627f733df9c1fa6ecfe54f572509d57869d2d3d72c`.

## Fresh execution and results

Interpreter: ROOT `.local/venv/Scripts/python.exe -B -X utf8`. `commands.json` contains exact argv, cwd and environment; `trace-extra-command.json` binds the additional suite. Raw stdout/stderr and their SHA256 are retained. All writes, test products and TEMP/TMP stayed under this review directory. No source, old log or default ledger was overwritten. The tested scratch started as exact artifact copies; generated replay/QA output changed only the scratch copies, with the original exports preserved.

| Suite | Actual result | Exit |
| --- | --- | ---: |
| Motion adapter / mailbox / deadlines author suites | 38 / 44 / 34 passed | 0 each |
| C main independent motion suite | 4 passed | 0 |
| A fresh motion witnesses/boundaries | 8 passed | 0 |
| Inventory / preprocessing synthetic parser suites | 26 / 36 passed | 0 each |
| C independent parser headers | 2 passed | 0 |
| Current verifier suite | 57 run: **54 passed, 3 skipped** | 0 |
| TRACE portable provenance | 7 copies, 4 documented pins, lock and import closure checked | 0 |
| TRACE replay | 81 case groups | 0 |
| TRACE independent QA / C main probes | 5 / 4 methods passed | 0 each |
| A additional TRACE boundaries | 5 passed | 0 |

No verified A-local FORCE ZIP path was available; main confirmed that constraint. The three archive-dependent verifier tests skipped explicitly. C's claimed 57/zero-skip run was **not reproduced**. The six separate original-archive CLI scenarios were **not_run** here. No archive was searched for outside the supplied context, downloaded, opened by member, or borrowed from a C-only path. Parser suites used synthetic fixtures; there was no original LAS member read, real-data refit, training or held-out evaluation.

## Findings

1. **Original STOP revocation defect is repaired in this candidate.** Each valid STOP, candidate retirement and new observation changes the generation token. After verifier return or caught exception, an older outer submit observes that change and returns no request bytes. The public STOP remains callable inside verification; it consumes the next candidate/command identity and is not overwritten by outer completion. Our old F02 witness, STOP followed by exception, nested model STOP, newer-but-blocked candidate, replacement observation and command-exhaustion STOP all leave the older request blocked. Older candidate replay is rejected. Exact duplicate observation remains a read/idempotent registration and does not spuriously revoke the outer request.
2. **Timing/source audit aliases are separated.** The verifier receives copied context, observation and timing; retained or forcibly mutated audit objects cannot change retained sample time, returned original deadline or serialized context. Old F01 and combined context/observation/timing mutation tests pass. These are callback alias checks, not proof of authenticated source or trusted clock evidence. Caller-owned negotiated context mutation is still rejected by the adapter's own validation.
3. **Parser and offline-verifier repairs pass the checks actually run.** Synthetic conflicting/late header tests, current helper pins, historical snapshot identity and current-source verifier checks pass. Historical generators are kept as pinned bytes and are not executed. The unavailable real-archive checks remain the explicit gap above; software test success cannot establish full C01 or dataset/model quality.
4. **TRACE remains an isolated candidate decoder.** The executable closure is candidate code plus the small declared stdlib imports; this review opened/imported no B encoder/decoder. It verified current closure and pinned copies, not an unobservable historical claim about the author's reading. QA snapshot equals the tested decoder. Replay covers 8 manual vectors, 32 synthetic streams, 126 frames/1046 points and 34 pinned malformed groups; QA additionally confirms 300 canonical grid positives, 154 noncanonical RAW and 254 alternate-k rejections. C main checks 296 single-wire-bit corruptions, replay eviction, no sequence wrap and alias/retirement behavior. Fresh A cases confirm full tick crossing 2^32 without frame-sequence wrap, duplicate no-point/no-state-renewal behavior, CRC-correct header/full-tick mismatch rejection with recovery, and source import closure.
5. **Production type 7 is still closed.** The unchanged A wire reference shipped in this candidate excludes type 7 and rejects the literal valid candidate frame, while the isolated candidate decoder accepts it. The operation-14 source delta adds no production integration. This review does not enable the public ABI or assert a live A-runtime deployment from a frozen reference check.

No new blocking finding is raised within this scope. Generation fencing and snapshot copying address the prior callback defects; they do not turn the adapter into a thread synchronization primitive or install a trusted runtime verifier. Every decision remains non-authorizing. A's actual authority, authenticated BOOT/source, measured clock/anchor/holdover, liveness and link/slot gates still require real integration.

TRACE's positive-fixture ledger is 1,816 selected valid RAW bytes to 5,346 complete frame bytes / 53,460 8N1 bits: framing expansion on these fixtures, not a real compression or latency result. Public ABI/R03, BOOT/clock, physical units, grouping/scheduling, C05/G06, current runtime, board and final game/system gates remain pending or **not_run**.

## Proposed next action

Main can post the bounded same-PR feedback in `proposed-pr25-feedback.md`, binding both operation/request identities to actual tested head `942fa309...`. Preserve the archive-dependent gap instead of rewriting it as C's zero-skip result. Separate future work must supply authenticated runtime/authority interfaces and independently approved ABI/BOOT/clock/unit/scheduling contracts; this review authorizes no integration or board action.

`before.json`, `manifest-verification.json`, `after.json`, `raw-log-hashes.json` and exact Git exports make the review reproducible. All 272 candidate checkout files and original exported blobs were unchanged at freeze; checkout remained clean. No Git mutation, PR operation, service/profile/ACL/native probe, hardware access, external send or additional agent was used. The old negative witnesses and failure logs remain preserved.
