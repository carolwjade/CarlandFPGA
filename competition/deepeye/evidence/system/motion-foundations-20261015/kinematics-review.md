# G06 motion core: final independent evidence after director repair

`DEEPEYE-IMPLEMENTATION-20261014/v1`;
`A-g06-core-independent-review-20261015-v1`; `/root/g06_core_review`.
Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements canonical hash
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The director remains Desktop `01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2.

F01's reproduced accelerating-distance inverse defects are resolved on source
SHA256 `5cab98c7100385a4bf290fc74c6e7173f56f328272c278ea6ce8ecb37542e043`.
The director changed the root calculation and added a regression. This agent
read the changed lines and regression, independently reran the probes, and did
not modify product files. The original failures and source hashes remain in
`review_initial.md`, `receipt_initial.json`, and the original raw logs.

The fix uses `hypot(v0, sqrt(2*a)*sqrt(s))` for positive acceleration before the
rationalized division, preserving the small inputs before squaring. The braking
branch is unchanged. The independently inspected new test uses an 80-digit
Decimal oracle and covers zero and multiple positive initial speed scales.

## Fresh results on the repaired source

| Evidence | Result |
|---|---|
| Existing tests | 35/35 passed, including the new regression |
| Independent 65-digit RK4 matrix ODE | 144 paths; 612 time samples; all checks passed |
| Largest-angle/convergence supplement | 8 existing plus 4 complementary cases passed |
| Extreme acceleration inverse | 60 cases; no exception; maximum time relative error `3.3306690738754696e-16` |
| Braking inverse | 47 cases; no exception |
| Ordinary stop-neighborhood inverse | 128 points, one to 32 ULPs before endpoints; no exception |
| Source consistency | All seven pinned review files identical before/after repaired-source verification |

Maximum ordinary trajectory errors stayed unchanged: position
`1.771306270934503e-15 m`, rotation matrix `2.886803361553668e-16`, arc length
`1.9595642886116587e-19 m`, and speed `1.3766765505351941e-17 m/s`.
The independent oracle derives the taskbook parameters itself and integrates
the matrix ODE; it does not call production helpers for expected poses.
`after_fix/commands.json` records exact executable, arguments, timestamps,
return codes and SHA256 of each raw log. `after_fix/existing_tests.raw.log`
contains the actual `Ran 35 tests` and `OK` output. Full values are in
`after_fix/independent_results.json` and `after_fix/inverse_edge_results.json`.

## Remaining braking precision and scale

The 128 strictly interior normal-scale samples have maximum time difference
`0.03366864286363125 ns` and speed difference `8.41716074289474e-12 m/s`.
Including the 47 wider braking probes gives a maximum time difference
`0.03728490322828293 ns` and speed difference `9.321225863455789e-12 m/s`.
The latter is the stored endpoint at initial speed `0.001 m/s`: the code returns
the documented earliest plateau time of `4000000 ns`, while the exact Decimal
interpretation of the rounded float distance `2e-6 m` gives
`3999999.962715097 ns`. This is endpoint distance quantization at a square-root
singularity, not a second observed exception.

For director scale assessment, the largest difference is less than 0.038 of
the API's minimum 1 ns integer time sampling interval. Even multiplying this
time difference by the global maximum speed `0.25 m/s` yields less than
`9.322e-12 m`, over seven orders of magnitude below the frozen `1e-4 m`
analytic gate-volume error scale. Pose-by-distance uses the requested distance
directly, so that conservative comparison is larger than its direct positional
effect. No tested normal-scale braking error exceeds the frozen physical or
geometric scales. The director retains the acceptance decision.

The unchanged braking formula still has poor *relative* precision for
subnormal squared speeds/distances: at `v0=2e-162 m/s`, `s=5e-324 m`, the
elapsed result is `2.340013603199533e-153 ns` versus Decimal
`3.0528039928965544e-153 ns`. This absolute scale is outside the physical
resolution of the scene, but it prevents any claim of uniform relative accuracy
over every finite floating-point input. It is preserved as a numerical limit.

## Scope and completion

The requested independent kinematics evidence and repaired-source verification
are complete. All H01–H15 remain mandatory. No G06, R03, board, game, collision,
gate-traversal, authority or system acceptance is claimed. The module still
requires caller-enforced authorization and continuous full-body collision,
including subdivision when a 10 ms step exceeds the 0.05-degree sweep limit.
No source, gate geometry, service, board, account, provider, external message,
commit, or contract was changed by this agent. Final artifact hashes are in
`receipt_final.json`; the native terminal result is recorded separately through
`fpga_native_complete`.
