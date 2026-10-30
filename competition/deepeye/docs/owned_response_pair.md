# Original serial raw response pair

Select `ready_result_frames_v1` explicitly in `SerialInvocationLimits` before the first request. The default `single_frame_v1` and its sealing API remain unchanged. Pair mode retains one write, ticket and journal; it accepts exactly two nonempty little-endian length-prefixed frames, with payload limits 2048 and 16384 bytes and total at most 18440 bytes. Fragmented or combined reads are retained as original rows; partial, extra, cancelled, pending, EOF and unknown effects cannot seal. Aggregate request, read and output budgets still apply.

`seal_serial_invocation_response_pair` records the owner QPC observation after original settled reads, returning exact raw frames and wire. This is a host-observed upper bound, not the child's computation completion instant. This raw transport does not validate READY/RESULT JSON, package provenance or authentication and grants no completion, BOOT, movement or board authority.
