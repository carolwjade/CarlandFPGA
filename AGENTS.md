# CarlandFPGA project rules

<!-- fpga-project-skills:begin -->
## Mandatory project skills

Every conversation in this project reads `.agents/skills/fpga-multi-node/SKILL.md` and follows its node-matched identity, task ownership, delegation, evidence and silent-presence rules. FPGA design or board work also reads `.agents/skills/pynq-z2-single-node/SKILL.md`. These are the only two project skills; use the A package on host A and the shared B/C package on clients, matching existing node_id. Skills are project-local and take effect in new conversations.

Human > main > child; preserve existing credentials, configuration, ledgers, local edits and services. Only A operates the physical board. Waiting belongs to the resident program without model polling. No new role, cloud permission or service-change authorization comes from installing skills.
<!-- fpga-project-skills:end -->

- Latest project design is `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.8 plus explicit later human updates in the skill requirements map. Candidate hardware/protocol/performance values become requirements only in the chosen task version.
- Keep simulation, synthesis, implementation, upload smoke tests and actual measurements distinct. Board feedback binds operation_id, request_hash and the actual tested commit; PR handoff follows the common skill reference.
- Human authorization 2026-10-15: the responsible main may create, continue, interrupt/terminate and archive multiple work chats or native children as needed, and choose any actually available model and supported reasoning effort without per-step human permission. Use this member's existing authenticated providers. Desktop/native work uses recorded task and non-overlapping file ownership; a mesh native lease is optional for that route, not an execution prerequisite. Mesh-managed jobs retain their own lease/idempotency checks. The main owns critical decisions and acceptance. Verify actual termination before reassigning files, preserve failed/interrupted evidence, and do not replay unknown side effects. See the current collaboration protocol; superseded fixed Flash/max, highest-effort and native-special-capability restrictions no longer apply.
- Project source and canonical distributables stay inside this repository. Build role ZIPs from clean committed tracked files with `python -m fpga_mesh.distribution`. Delivery copies may be placed on Desktop or in the original group; vendor installers/images may remain outside with source/hash records.
- Runtime deployment is maintained in `fpga_mesh/`, `docs/deployment/OPERATIONS.md` and the existing Update/Join entrypoints. Existing updates use the idle fence and preserve local state, never re-onboard. Skill upgrades do not restart services, enable hardware queues or grant Astra im:resource; cloud scopes belong to the existing app owner, never DeepSeek.

<!-- deepeye-human-lock:begin -->
## DeepEye human-locked final acceptance scope

For every DeepEye proposal, fusion, implementation, review, new main/work chat,
and subagent, read `docs/competition/deepeye-2026/immutable_scope.md` and `.json`
before work. Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Preserve every H01-H15 requirement. This direct human scope overrides AI plans,
scores, deadlines, budgets and fallback suggestions. Only a new explicit human
instruction can amend it. Preserve game-level 3D/UI, framed hollow cube, solid
drill/obstacles with volume collision, live free camera/editing/random placement,
free blue/red equal-size entry/exit circles and full correct crossing, hidden
truth and causal sourced sensor observations, meaningful PC AI and both PC-direct
and PC-AI-to-FPGA-to-simulator control. No 2D/video/precomputed-route replacement,
truth leak, or FPGA-only control restriction. Every handoff carries this contract
and verifies the pinned hash before task execution. Children cannot edit it.
<!-- deepeye-human-lock:end -->
