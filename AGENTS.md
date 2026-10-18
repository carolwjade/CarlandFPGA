# CarlandFPGA project rules

<!-- fpga-project-skills:begin -->
## Mandatory project skills

Every new conversation must read `.agents/skills/fpga-multi-node/SKILL.md` and its
node-matched role; use `.agents/skills/pynq-z2-single-node/SKILL.md` for local FPGA
design and verification. A alone operates the physical board. Both skills are
project-local; a new conversation loads the installed version.
Apply the existing human > main > child priority, task ownership and evidence
rules. Skills grant no new role, credentials, cloud scope or service authority.
Keep presence silent unless the human asks; report actual task blockers concisely.
The resident program handles waiting, without model polling.
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


<!-- deepeye-desktop-director-20261015:begin -->
## Human-authorized DeepEye Desktop director replacement

The human explicitly replaced the locked background implementation main on 2026-10-15.
The sole current A implementation director is Desktop App thread
`01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation 2, task
`DEEPEYE-IMPLEMENTATION-20261014/v1`. Read the current activation/evidence record
`.planning/deepeye-desktop-handoff-20261015/transfer.json` before acting.
The former background thread `01a13b40-6aea-7ad2-83ef-14884c00c32c` is retired
and archived: late peer/callback input is reference material only, never permission
to resume product edits, delegate work or reclaim director ownership. Preserve it.
This director and its interactive App workers use Desktop App creation/follow-up
so the Desktop retains writer ownership. Do not call mesh `main_submit` or
`fpga_session_open` to create, adopt or resume this Desktop director. Existing
mesh transport, Flash/max execution and valid native leases remain available;
they do not grant a second main authority. Never clear writer locks or rewrite
SQL to bypass ownership. This scoped human exception leaves other independent
background tasks under the normal multi-node skill. H01-H15 are unchanged.
<!-- deepeye-desktop-director-20261015:end -->
