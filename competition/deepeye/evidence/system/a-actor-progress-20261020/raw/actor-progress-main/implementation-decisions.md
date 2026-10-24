# Main progress implementation decisions (candidate implemented; review pending)

Current stage: the three owned product files are edited. Actual first focused run39/39
passed; after six additional boundary/positive cases, whole affected regression193/193
passed with zero errors/failures/skips. All original24 test method ASTs unchanged.
Original RED3/3 failures retained. Freeze candidate and obtain independent review before
any acceptance/publication; no native AI or production channel claim.

A-ACTOR-PROGRESS-IMPLEMENTATION-20261019-v1, sole A main. Three owned files:
actor_composition.py, test_actor_composition.py, docs/actor_composition.md, plus
this actor-progress-main evidence directory. Exact baseline58 and original3 copies
in main-design-selection.json (SHA d9bf2352aa2d5b9e45007d5d90033dd79a3a2d75e2921da346d968e59cc5cede).

Behavior RED ran once: tests3/failures3/errors0/skips0. Actual numerical CAS committed
despite proposed progress expiry after prepare, inside commit, or whole dt end=deadline.
progress_gap_red.py only attaches planned config attributes to the original exact
config type for preimplementation fixtures; production behavior was not patched.
Do not rerun/overwrite RED. Translate those cases to actual typed records after implementation.

Selected design cb91477153276369c6eaead242cbecb70423804f6939bbbef49a788a931451db.
Implement in existing composition; runtime/executor/ABI/actor sources read-only:
1. Required config progress_max_age_ns and ai_model_sha256; strict int1..2**63-1
   and exact64 lowercase hex. No permissive defaults. Production gate remains
   unconditional unavailable before registry acquisition.
2. Private frozen _CompletedInference: boot, source (exact channel object),
   clock_domain (exact captured authority monotonic callable), candidate_raw bytes,
   invocation_id, dispatch_lower_ns, completion_lower_ns, completion_upper_ns.
   These are verifier results, never credentials; real producer/authentication absent.
3. Private per-activation _ProgressGate: exact BOOT/source/clock/model/max_age,
   activated_at/high-water monotonic, irreversible revoke generation, one immutable
   current command/completion plus high-water command/candidate/invocation IDs.
   No unbounded history or renewed receipt cache.
4. Existing host_envelope model_candidate producer=ai_controller consumer=control_broker;
   motion_request producer=control_broker consumer=world_authority; exact boot context.
   Require candidate/request IDs, observation, entire target equal and approved model.
   Strict ints/no bool/subclasses, dispatch>=activation and
   dispatch<=lower<=claimed candidate completion<=upper<=request issue<=trusted now.
   Derive deadline=lower+fixed_age with overflow rejection, never receipt+age.
5. Exact duplicate bytes and original invocation/completion metadata retain earliest
   deadline; ANY changed metadata rejects (stricter simpler choice than optional
   interval tightening). New candidate/invocation/command IDs must each increase while
   prior gate healthy. Expiry/revoke cannot reset; unrelated completion cannot extend
   an existing command. No ACK/start/heartbeat produces a completion lease.
6. verify_command: original channel verification, validate command shape/context;
   STOP bypasses completion lookup but retires. For movement, bracket private
   channels.completion_for_command(event,boot) with owner veto and trusted monotonic
   high-water checks, then gate.admit. Save command record after admission.
   Runtime still enforces actual observation/heartbeat/TTL/sequence; later error retires.
7. ai_lease MUST call original actor. Capture gate identity/generation first and
   recheck after original sample; strict original lease type, exact boot/instance,
   valid bounded deadline. Gate request must equal command record and, during step,
   actual runtime current command bytes. Return minimum original life/progress deadline.
   No channel callback/IPC/parsing/logging/new time sample in this final seam.
   Existing runtime post-provider clock and executor strict end<deadline cover whole dt.
8. _retire revokes gate before callbacks. _channel_health may observe progress time
   but never renew it. Choose/document initial EMPTY deadline activation+fixed_age
   so first completion must arrive within the fixed budget; no positive lease while EMPTY.
   Preserve actual post-CAS commit despite later veto.
9. Preserve all24 existing test assertions; update only explicit synthetic fixture config/
   completion sources. Add real-fence expiry, end1ns-before/equality min deadline,
   duplicate/nonrenewal, missing/dead/stale, identity/domain/model/bounds/overflow/clock,
   callback expiry/reentry/revoke-during-Wait, STOP without completion. Whole affected
   regression once after focused tests. Independent review required.
No actual native/board/model/Run or product harness import; process-only TEMP/PYTHONPATH,
no pyc. All29 not_run/H01-H15 unchanged.

Parallel G02 child-9660767305774a9bbe4eed3f5859738a owns editor/UI persistence files
and its evidence; last actual resident status RUNNING. Do not touch that ownership.
