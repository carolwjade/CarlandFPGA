# Root feedback between accepted board captures

The private host `main(..., _causal_source=source, _causal_feedback=consumer)`
can now call trusted Root code after each accepted board capture and before the
next source sample/request. This closes the former collect-all-then-return
interface gap. It supplies a connection for separately owned CPU, broker and
motion processing; it does not implement those dependencies or activate Run.

The reviewed template, complete hash-bound request and one-time activation must
each contain this exact `candidate_feedback_profile`:

```json
{"name":"root_causal_feedback_v1","max_calls":16,"movement_authority":false,"CPU_completion_created":false}
```

Feedback requires explicit causal source mode and a callable consumer in the
original Root host thread. Missing/mismatched declarations fail before SSH.
No CLI parameter, transport response or controller request can select code.
The callback and its complete world/CPU/authority closure must be included in
the separately reviewed Root source package. Structural profile checks and
file hashes do not authenticate arbitrary callbacks or certify model execution.

For each original admitted capture, the host first saves raw response and
candidate bytes. It durably writes `feedback-NN-started.json` with the exact
candidate/capture hashes, invocation index and original host QPC lower bound,
then invokes the consumer exactly once with a JSON-detached candidate record.
Its inputs retain board-returned counts/quality, observation identity and
candidate/staleness flags. They contain no pre-board source floats, layout,
labels, map seed or collision oracle. Caller mutation cannot rewrite saved or
returned captures. The consumer must return `None`; returned authority claims
are rejected. A normal return records the actual QPC upper bound in a separate
`feedback-NN-returned.json`. Neither record creates CPU completion or authority.

A thrown exception, failed evidence write, nonempty return or clock regression
retires the exchange without repeating the consumer or pending injection.
`started` without `returned` preserves an unknown callback outcome. Local input
close/cleanup never proves remote STOP or reverses a possible callback effect.
The separately owned authority remains responsible for its own stop/revoke.

The consumer is synchronous. The host checks its original10s session limit
again on return, including after the final requested capture; a slow final
consumer cannot turn an expired session into success. The enclosing original
60s Job supervisor provides hard process containment during a blocked call.
Source100ms ages, missed slots, invalid vibration windows, pending deadlines,
one-time requests and actual raw terminal/STOP checks are unchanged. Callback
delay can create honest source gaps; no tick is backfilled or renewed.

NEW `test_causal_feedback.py` exercises only this connection with synthetic
board/source helpers: board-returned counts drive a changed next observation,
mutation isolation, exact three-record selection, failure/no retry and final
session expiry. It runs no old suite, SSH, physical board or CPU model. C28's
actual planner package, current-BOOT physical release, complete causal cycles,
both full H12 modes and G03/R03/all29 acceptance remain pending.

Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
