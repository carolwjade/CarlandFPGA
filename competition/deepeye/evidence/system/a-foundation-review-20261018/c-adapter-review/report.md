# C PR25 current adapter review

Exact HEAD `31267d6c4ae284b8788ebb457f49c4ae5a49c60c`, source `c00f932568aece85e9a2febe47e63528a977ea0f`. The current adapter exists; the old no-adapter conclusion is superseded. The existing A review already targets this exact head and source. Its two callback findings remain reproducible.

**Recommendation:** reuse the strict, non-authorizing serializer/context/original-deadline software evidence. Block automatic runtime output with reentrant callbacks until C fixes F02 on a new exact commit. This review adopts no source and grants no runtime/product acceptance.

## F02 — P2: STOP can be followed by older in-flight motion

`motion_request.py:425` calls the verifier and `:430` emits without checking whether callback state changed. In a single thread, verifier `safe_stop` emits candidate11/command_seq0, then the outer call emits older candidate10/command_seq1 SET_TARGET. Both pass current A stateless validation. The expected-safe assertion fails on exact current source; no actual motion occurs.

C should bind/recheck a state or revocation generation around the callback. STOP must remain immediately available and retire the older in-flight submit. Callback mutation/retirement must yield no outer motion bytes. A authority must independently retain STOP/candidate/session history; a newer command sequence alone cannot revive the old target.

## F01 — P3: callback timing aliases returned audit

`motion_request.py:416/422/430` shares the same OriginalTiming between trusted RuntimeCheck and returned RequestDecision. Forced `object.__setattr__` through a retained callback check changes deadline2020000000 to1001020000000 while request bytes stay unchanged. This requires trusted same-process code bypassing frozen dataclass; it is not a JSON/OS/authority escape. Return reconstructed audit values and independently recompute deadlines in authority.

## Evidence

-135 source-commit Git blobs and corresponding HEAD blobs match the handoff; request hash and manifest SHA256 match the assigned pins. Exact artifacts are exported. Twelve checkout files differ by CRLF; raw checkout hashes remain separately recorded.
-Existing review artifacts and source hashes match. Its107 regressions,17 independent checks, public65536 STOP allocation check and other vectors were reused; no full359-suite repeat.
-Five fresh positive tests passed, covering9 TTL boundary vectors, seven context mismatches, no-verifier/STOP behavior, observation sequence wrap and current A compatibility.
-Two expected-safe tests remain RED (exit1, two assertions, zero errors), reproducing F02/F01. The RED result is not reported as safety PASS.
-A motion.py has changed since the prior review to rational arithmetic. All42 ROM entries match the frozen reference; targeted requests pass current A validation.

All29 full product cards remain `not_run`. No source writes, adoption, motion/board action, service or external-message effects. Full hashes, raw logs, precise counterexample records and boundaries are in `report.json`, `targeted_results.json`, `handoff_verification.json` and `prior_evidence_reuse.json`.
