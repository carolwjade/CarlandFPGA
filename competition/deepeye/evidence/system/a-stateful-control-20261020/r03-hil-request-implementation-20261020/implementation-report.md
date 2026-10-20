# HIL original-request tracker implementation

Three new files implement the main-selected diagnostic request association/deadline component, based on `0f1c80be5cf1140d743d125fcfee36c4c4ee5792` plus exact new-source hashes. It does not send, authorize motion, install a provider or activate HIL. Existing mailbox, source/schema/BOOT, C dirty files and production gates remain unchanged. Main owns independent review/adoption.

`HilRequestTracker` preserves the original `(session,type,seq)`, semantic payload, exact first packet, latest retry packet, first-send, original TTL, original observation/sample lower bound and target. A retry may change tick/CRC; it cannot change payload or renew first-send/deadline. CONFIG/GAIN are separate non-motion identities; BOOT wire handling is excluded and belongs to the real BOOT verifier. CONTROL3D uses existing action/TTL/curvature validation. Superseding, STOP, expiry and observation eviction cannot be undone by late response/retry/new observation. History is16 requests, four observations, three request-type high waters and64 used/proposed sessions; exhaustion refuses rather than forgetting retirement.

Current ACK3D/STATE3D are parsed through the existing sealed host/wire validation. Captured phase, no fault, complete quality, exact target, retained original observation and explicit independent timing/capture results are needed for qualified diagnostic association. STATE8/non-motion replies never qualify. Nonnull hashes, dataclass types or literal booleans do not authenticate measurements. Missing verifiers/evidence/source remain unusable. The existing control_epoch==context.config_epoch rule is retained strictly; no new epoch interpretation or ABI amendment was invented.

Deadline uses the frozen min formula with original first-send/TTL, conservative receipt lower bound, explicit serial/USB/clock delay upper bounds, original sample age cap and previous deadline. Equality to supplied now expires. The eight literal JSON traces include first ACK lost and response8s later, original12s cap, ordinary retries, receive interval uncertainty, delay exhaustion, sample age, exact equality and previous deadline tightening. Tests build full raw packet CRC using independent stdlib binascii rather than production wire.encode.

BOOT/source/timing/capture are explicit synchronous trusted callbacks. STOP and invalid/reentrant public calls change a veto generation, including malformed call-shape errors caught inside callbacks. Returned results are fenced before publication. Foreign-thread calls reject and queue a STOP for the owner, drained by the fence. A structurally valid verified BOOT proposal is retired before the final fence so an aborted proposal cannot clear its own STOP by replay. Records are frozen, snapshots detached and no asynchronous provider is installed.

## Actual tests retained

| Attempt | Actual result |
|---|---|
| red-01 |34 tests fail because tracker absent; exit1 |
| green-01 |34 tests pass; exit0 |
| strict-field-red |37 tests, one failure reproduces mutable verifier raw acceptance; exit1. Foreign-thread fence and session-exhaustion tests pass. |
| final-green |37 tests pass, no skips/failures/errors; exit0. Strict original raw bytes and exact run-id type are enforced. |

The final tests cover eight independent literal deadline traces, retry bytes/time identity, changed payload, distinct request types, superseded/stopped/expired requests, lost ACK, old/evicted/unknown observations, CRC/TTL/curvature, target/capture/epoch mismatch, missing/wrong BOOT/request/time/capture/source evidence, health-only STATE8, out-of-order ACK/STATE, response replay, request/capture rollover, malformed/regressing times,12 callback STOP/reentry/bad-shape/failure combinations, verified BOOT veto/replay, foreign-thread veto, public call shapes, bounded histories and defensive records.

All attempts use exact project Python -B -X utf8, hidden below-normal processes and50-second bounds. Raw stdout/stderr, argv/cwd/environment overrides, launcher and actual worker PIDs, duration, exits, pre/post new-source hashes, frozen attempt source and imported-module hashes are retained. Audit records show zero process/network attempts, and writes during tests are restricted to this task folder. Initial missing-file design-plan lookup was corrected to the actual path named by assignment; it was read-only and did not execute product code.

No full245 or existing runtime test rerun: no existing module was changed and this component remains unwired. No mailbox import, model/native runtime, physical capture, measured USB/clock run, OS/service/driver/board/UI/peer action, Git staging or commit occurred. Fifteen baseline input pins include the three completed mailbox files; all four C dirty files are separately protected. Current closeout HEAD is recorded separately, never promoted to a claim of tests at a different later HEAD.

## Limitations requiring future integration

All provider results in these tests are synthetic fixtures. Actual verifier authenticity, nonoverlapping hard delay bounds, board capture/batch/request attribution, matched image, source eligibility and useful AI remain external. A malicious trusted verifier concealing internal failures/fabricating evidence is outside the valid provider contract; local identity objects/types cannot make it trustworthy. Global/restart session uniqueness remains the BOOT provider's responsibility;64-session retirement is object-local.

`now_ns` is the caller's evaluation instant. This component does not sample a hardware/host clock around potentially slow verification, create a timer or grant a continuing lease. The real authority must obtain fresh time and recheck the returned deadline after provider work and at every actual physics/send step. Association.qualified is a diagnostic for the supplied evaluation instant, never a motion/send credential. This is not a durable physical evidence recorder: the caller must retain original raw envelopes and actual verifier records for acceptance. Snapshot state is bounded diagnostics, not proof of authentic execution.

Response order policy conservatively stops on changed/backward/ambiguous sender identities and capture rollback; a new verified BOOT is required. New valid commands may follow ordinary expiry only under the still-active context and its genuine upstream gates. A real HIL authority/executor and B request/history/physical capture still need independent mode-specific integration. PC_DIRECT is refused by this component rather than given fictional board capture; its own chain remains intact.

See `api-resolution.md`, frozen `final-source/`, `source.diff`, `result.json` and the manifest. H01–H15 and canonical requirements hash remain unchanged. All29/R03/G05 and full two-mode H12 runtime remain not_run. Native job completion is bookkeeping, not main acceptance.
