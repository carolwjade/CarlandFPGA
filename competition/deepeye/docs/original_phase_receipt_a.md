# Original host chain phase receipts

Each v2 `ChainSessionV2` is bound to its original factory-registered Session,
process, QPC, streams, source bundle and sequence. When `_send` has retained
the original request and received one complete, shape-parseable response, it
allocates an `OriginalPhaseReceipt` inside that request/reply path before
returning to the caller. `chain.phase_receipts` returns a tuple of the same
original objects, ordered by one-based phase index; the caller cannot replace
the ledger via that property. `out['phase_receipt']` is the very same object.

The immutable, nonserializable object exposes `owner`, `phase_index`,
`request_id`, `kind`, `operation_id`, `request_raw`, `response_raw`,
`lower_qpc_ns`, `upper_qpc_ns`, `session`, `process`, `stdin`, `stdout`,
`stderr`, `clock`, `session_origin`, `spec`, `ready_raw`,
`ready_lower_qpc_ns`, `ready_upper_qpc_ns`, `source_pump`, `status` and
`unknown`. `source_pump` is the original bound host pump for that phase, or
None before binding. The factory uses a private construction key, and identity
in the original chain ledger is part of the custody check. This is a trusted
in-process convention and does not defend against arbitrary Python execution.

The receipt describes host custody of actual bytes and QPC brackets. It is
not authorization, a BOOT acknowledgment, a hardware timing result, or a
remote board issuer identity. An UNKNOWN response is retained as UNKNOWN;
later semantic validation can still fail even when the raw response said
COMPLETE. A malformed reply is retained in the original response file and
marks the session unknown; it does not become a fabricated phase receipt.
The Root-side producer retains the original receipt in event references and
checks it against the original ledger, raw reply, session, clock and pump.
Independent C48/C49 checks remain responsible for the data and authority.
