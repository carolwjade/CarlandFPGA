# Independent HIL request lifecycle review

The focused independent run produced 25 passing tests and one reproducible
failure. One subsequently requested pre-entry ordering control also passed,
without replaying those26 tests. The failure is a narrow mismatch in the advertised foreign-thread
veto/publication boundary. It is not evidence of motion, send permission or
physical execution. Main decides its disposition and any later source change.

Reviewed product tracker SHA256:
`7e3b9f8661eb54b51c504ec1d32adef2c39d7168ae53987a91b65ce4ccd9c77f`.
The product's three new files exactly equal both the author's frozen
`final-source/` and the tested `final-green/` snapshots. All 43 author manifest
entries, 15 original baseline inputs and four separately protected C dirty
files matched their pins before and after this review's controls.

## R03-HIL-IR-01 — P2 candidate: pending foreign STOP is not fenced through publication

Tracker lines 162–164 state that foreign-thread input requests a pending STOP
and the owner drains it before publishing. `api-resolution.md` also promises
that returned results are fenced before publication. `_owner_call`, lines
189–195, rejects a foreign-thread call and sets `_pending_stop`; it does not
immediately mutate the owner's state. The final response fence is line 462.
Lines 463–467 then assign the deadline/capture/qualified state and construct the
returned Association without checking the pending event again. `_entry`, lines
37–52, has no post-call publication fence.

Reproducer `review_controls.py:527`, test
`test_foreign_thread_after_final_fence_cannot_publish_qualified`, uses Python
line tracing only to force an otherwise legal thread scheduling point at
product line 463. It changes no product source, private tracker state, function,
verifier result or frame. The foreign thread calls the public `stop()` method,
is joined within one second, and has finished before the owner resumes.
The verifiers themselves are synchronous, with the same closed synthetic
records used by passing controls.

The literal trace is:

1. Verified synthetic HIL context session23/config_epoch4/profile FAST; observed
   seq70 has sample and receipt100ms.
2. CONTROL3D seq12, first-send120ms, original TTL2500ms, speed8, yaw/pitch0,
   observed_seq70. The original observation limit is1600ms.
3. ACK3D sender seq200 at400ms, request type14/seq12, phase3, fault0,
   capture_seq30, epoch4, quality15, remaining900ms, matching target.
   Synthetic delay bounds are33+7+2=42ms, so deadline=min(2620,1258,1600)=1258ms.
4. After the final fence and before publication, a foreign thread calls
   `stop("foreign after final fence")`. The call is rejected with
   `constructing serialized owner required` and queues STOP.
5. `response` nevertheless returns `qualified=true`, deadline1258000000ns.
   A subsequent owner `snapshot()` drains the pending STOP and reports stopped.
   The already returned frozen Association remains qualified.

The assertion preserving the intended before-publication guarantee fails.
`literal-traces.json` retains the exact raw request/envelope bytes, caller times
and race outcome. `execution-controls/process/stderr.txt` retains the failure
and traceback. No failure was repaired or relabelled as a pass.

This is a **conditional P2 recommendation**, confined to the documented promise.
There is a valid narrower concurrency interpretation: if line462 is explicitly
the operation's linearization point, a foreign call overlapping the response
can be ordered after that response; then the pending event is drained on the
next owner entry. The current prose instead says “before publishing” and does
not expose that cut-off. Main should resolve that exact contract, rather than
infer a continuous authorization lease from a frozen diagnostic.

For the existing before-publication promise, consider coordinating pending STOP
and the diagnostic commit through one explicit serialization/linearization
mechanism shared by both paths, with a focused scheduling control around that
point. Merely moving the final event check a few lines later still leaves an
unspecified interleaving. Alternatively, if owner-entry/final-fence semantics
are deliberately selected by main, document that boundary and the required
next owner check precisely. This review neither selects nor implements a fix.

Main specifically requested that three orderings be distinguished:

| Foreign STOP scheduling | Actual result | Evidence |
| --- | --- | --- |
| Queued and foreign thread joined before the next owner `response` call | The owner-entry `_owner_call` drains STOP. Response returns `qualified=false`, status`stopped`, and check/snapshot remain stopped. | Additional single `pending_before_entry.py` control:exit0, worker50144, tree0.406s; raw packets reused from the saved literal trace. |
| Queued during synchronous capture verifier, joined before verifier returns | Callback-return fence drains STOP and vetoes the response with ValueError; snapshot stopped. | Passing original `test_foreign_thread_inside_verifier_is_fenced`; no rerun. |
| Queued after the final response fence, joined before the response returns | Response returns the1258ms qualified diagnostic; next owner snapshot drains STOP. | Preserved original failing scheduling test at line463. |

The first two are correctly vetoed by current code. The third overlaps an
already in-flight response and can legally be linearized after that diagnostic
if the final fence is the selected commit point. An immutable diagnostic can
also become stale immediately after any legitimate return. Neither fact gives
motion permission or requires endlessly chasing the final machine instruction.
Thus there is no demonstrated original-TTL or observation-age violation here.
The class comment's unqualified “owner drains before publishing” is broader
than the measured behavior. The concrete review recommendation is to resolve
and document that semantic cut-off, with any code change subject to main's
chosen concurrency contract. The retained failure asserts the stronger prose
interpretation, not an independently proven continuous-stop authority promise.

## Confirmed bounded behaviors

The other 25 independent tests passed. Their looped subcases are retained in
the same single run, not a replay of the author's37 or the existing245 suite.

| Area | Independent result |
| --- | --- |
| Original request/TTL | Tick/CRC-only retry preserves object, first packet, first-send and deadline; changed semantic payload latches STOP. |
| Type identity | CONTROL3D, CONFIG and GAIN with the same seq occupy separate keys; ACK request_type5 cannot match a motion request. |
| First ACK lost | STRESS request first-send120ms, sample100ms, late retry/ACK8120ms remains capped at12100ms, never gets a new12s; equality and later retry stay expired. |
| Integer deadline | Receipt lower370ms + remaining900ms − delays42ms gives1228ms; later STATE cannot increase it. One ns before qualifies; equality does not. Delay exhaustion and original-send TTL also cap correctly. |
| Retired history | Superseded, expired, unknown-observation, observation-evicted and request-evicted commands cannot revive via late response/new observation/retry. |
| Source/time | TELEM and EVENT references work as selected fixtures; observation received after the original send cannot backfill it. Unknown source/verifier remains unusable. |
| Capture/epoch | Accepted/applied, incomplete quality, wrong target/epoch/batch/BOOT/request/raw, invalid bounds and remaining TTL above original cannot qualify. Capture wrap is rejected. |
| STOP | Explicit STOP, valid zero-field STOP request, current fault/rejected/stopped response prevent later association/new requests under the activation. |
| Replay/limits | Exact wire duplicate cannot renew; changed identity, backward/half-range/wrapped request/response, evicted-key replay and used-session exhaustion fail closed. Storage is16 requests/four observations/64 sessions. |
| Callbacks | Twelve STOP/reentry/bad-shape/exception combinations across observation/timing/capture fail closed. Foreign-thread STOP during a callback is drained at its return fence. A valid vetoed BOOT proposal is retired. |
| Public input | Bad CRC, TTL, curvature, zero-speed turning, malformed times/call shapes and clock regression reject; snapshot/public fields remain diagnostics. |
| No default authority | Missing dependency refuses BOOT; nonnull record hashes or literal True do not substitute for verifier output; topology2 is rejected without fictional capture. |

## Boundaries evaluated fairly

`Association.qualified` is explicitly a supplied-time diagnostic
(tracker lines121–126), not a motion/send credential. The independent slow
verifier control advances an illustrative external clock from400ms to1000ms
while verifying a request whose deadline is520ms. Returning qualified for the
supplied400ms is expected; the fresh `check(now_ns=1000ms)` expires it. This is
not listed as a defect or proof of actual verifier latency. A real authority
must sample trusted time after verifier work and at each physics/send action.

STATE8 is non-motion health diagnostic input, and does not create an
association. The helper is not a complete board-health watchdog/executor;
authority must independently process fault/heartbeat policy. Similarly,
request retention for CONFIG/GAIN records identity, not their execution
eligibility. No requirement for a fabricated executor or trusted timer is
imposed on this component.

All verifier evidence here is synthetic and explicitly selected by exact
fixture bytes; it authenticates no BOOT handshake, sensor source, clock bound,
independent physical capture, board batch or useful AI. The supplied Python
types and opaque source/batch objects are containers, not credentials.
Actual source eligibility, nonoverlapping measured delays, BOOT/global restart
session uniqueness, authority serialization and both full H12 chains remain
integration work. There was no PC_DIRECT capture substitution.

## Execution and preservation

- Bootstrap `execution/`: exit1 before tracker import/tests because this
  review initially excluded the author's public `reserve-request.json` from
  manifest verification. The original source and streams are retained. Only
  that erroneous public-entry exclusion was corrected; `lease.private.json`
  stayed forbidden. No test was repeated by this correction.
- `execution-controls/`: 26 tests,25 pass/1 fail,0 errors/skips; unittest body
  0.179s, recorded body plus post-run pin verification0.203s, whole tree0.578s.
  Expected review failure exit1 was retained.
- Hidden below-normal private Windows Job Object:40s,512MiB job/256MiB process,
  active limit4, streams2MiB each, owned tree16MiB/500 entries, free reserve10GiB.
  The tree limit is sampled; no OS disk quota is claimed.
- Launcher33928 and actual worker52200 are recorded separately; the third
  retained member31908 also terminated. All three original held OS handles
  were signaled with wait_result0; final active count0, no runner faults.
- The later main-requested prequeued control is separate:exit0, body plus pin
  check0.094s, tree0.406s,20s bound,1MiB streams. Launcher44996, worker50144 and
  member33504 all had held handles signaled, active count0 and no runner faults.
  It reuses the original saved raw bytes and executes only the new ordering.
- Exact argv/cwd/environment, source pins, streams, hashes and imported module
  pins are saved. No prohibited process/network action or unowned write was
  attempted by the controls. Existing host jsonschema dependencies were
  imported read-only; no packages were installed and no mailbox was imported.
- Two earlier read-only attempts to locate stderr guessed `.log`/`.bin`;
  the recorded stream is `stderr.txt`. They had no execution or write effect.

Review work changed only this assigned directory. Product, author evidence,
schema/gate/ABI, Git/index, C dirty bytes, runtime/services/driver, network/peer/
group, board, UI/input and original failures were preserved.

H01–H15 remain fixed under
DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
All29/R03/G05/full H12 remain not_run. Native job completion records delivery
only; it is not main adoption or product acceptance.
