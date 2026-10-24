# CarlandFPGA project rules

- This repository contains a three-machine control plane and a separate PYNQ-Z2 single-machine development skill. On machine A, use `skills/pynq-z2-single-node/SKILL.md` for local design, verification, toolchain, and physical board work. On B/C, use the node-matched installed client skill ZIP for design and Git handoff; the repository copy includes A's board upload entrypoint and is not the client workflow. Use `fpga_mesh/` and `docs/deployment/OPERATIONS.md` for group coordination.
- The drilling-logging draft and attached skill packs are references. Do not treat AD7606, 300 bps, compression ratio, latency, Ryzen AI, or the final host application as settled requirements until a task version chooses them.
- In group work, only machine A may operate the physical board. B/C may design and simulate, then submit a code commit, test plan, and evidence manifest through a repository PR. A reports actual board results against that PR's operation ID, request hash, and tested commit.
- Keep simulation, synthesis, implementation, and actual PYNQ-Z2 measurements distinct. Preserve commands, tool versions, reports, logs, and artifact hashes; do not claim board results from a model or simulator.
- Keep project code and distributables inside this repository. Large vendor installers and board images may live outside it with recorded source and hash. Build the FPGA teammate ZIP from committed tracked files with `python -m fpga_mesh.distribution`; unrelated product packages and rules are outside this project.

## Autonomous routing (human update 2026-10-15)

- Human authorization 2026-10-15: the responsible main may create, continue, interrupt/terminate and archive multiple work chats or native children as needed, and choose any actually available model and supported reasoning effort without per-step human permission. Use this member's existing authenticated providers. Desktop/native work uses recorded task and non-overlapping file ownership; a mesh native lease is optional for that route, not an execution prerequisite. Mesh-managed jobs retain their own lease/idempotency checks. The main owns critical decisions and acceptance. Verify actual termination before reassigning files, preserve failed/interrupted evidence, and do not replay unknown side effects. See the current collaboration protocol; superseded fixed Flash/max, highest-effort and native-special-capability restrictions no longer apply.

- Read the current project-local collaboration skill and protocol at `../../.agents/skills/fpga-multi-node/` (the owning repository root). The active Desktop director remains 01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2; read `../../.planning/deepeye-desktop-handoff-20261015/transfer.json`. Do not resume the retired background director or create a second writer.
- Preserve task/version, work identity, non-overlapping files, actual termination evidence and independent verification.

## Official model updates v0.8 (2026-10-10)

- Main and native GPT use this member's existing official Codex login; DeepSeek uses its existing separate authenticated provider when selected. Model and reasoning depth are main-selected from actual supported options. Do not copy cross-role credentials or fabricate model access.
- Use `fpga_models_refresh` or `project_cli models_refresh` to refresh the actual official model/effort catalog and native role files. The human update page opens with `deploy/更新官方模型.cmd`. Refresh makes no inference call and retains current tasks, leases and credentials. Newly discovered official visible models get native roles automatically; `official-latest` follows the official default. Missing legacy names remain explicitly documented aliases until listed by the official catalog.
- Role definitions apply to newly loaded conversations. An already generating turn keeps its model. Supported model access must be verified by actual completed turns; catalog membership alone is not an access guarantee.

## In-place distribution and Astra files (2026-10-11)

- Existing nodes use `deploy/Update-FPGAMesh.ps1`: update changed source files only, preserve local configuration/credentials/state, and do not rerun onboarding. The updater fences ledger admission and verifies idle before stopping the existing service.
- Astra requires tenant scope `im:resource` for file upload/readback. Astra-A received explicit human authorization and its grant was verified. Existing B/C must obtain their own app owner's authorization on the existing Astra app; an update ZIP cannot grant a cloud scope. Run `python -m fpga_mesh.feishu_permissions --config <existing-config>` for a read-only audit. Never add file scope to DeepSeek or change the human > main > child priority.

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
