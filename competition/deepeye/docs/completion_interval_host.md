# Explicit completion interval host path

The original scalar v1 validator remains the default. Explicit `enable_completion_interval=True` selects the C43 v2 candidate and requires original source, dispatch, previous and age bounds. The effective exclusive deadline is the minimum of the original lower observation plus age and all supplied original deadlines. Upper is a host-observed complete-result upper bound, not a CPU completion instant. Missing evidence does not create a scalar or a grant.

`adapt_action_candidate` retains the requested target and refuses durations exceeding the original caps; STOP carries no positive lease. Returned objects are consistency records only, not `_CompletedInference`, BOOT, authentication or movement authority. Production source/actor/callsite integration and physical/board acceptance remain separate.
