# CarlandFPGA project rules

<!-- fpga-multi-node:begin -->
## Mandatory project collaboration skill

Every conversation in this project must read `.agents/skills/fpga-multi-node/SKILL.md`
and follow its node-matched role, task ownership, delegation and evidence rules.
Apply the existing human > main > child priority; this skill grants no new role,
credentials, cloud permissions, board access or service-change authorization.
Keep presence silent unless the human asks; report actual task blockers concisely.
Waiting is handled by the resident program, with no model polling.
<!-- fpga-multi-node:end -->

- A uses the host package; B/C install the shared client package matched to their existing node_id. The unified skill owns coordination, model dispatch, recovery and PR handoff; do not copy these procedures into separate skills.
- A's local design and board workflow remains `skills/pynq-z2-single-node/SKILL.md`. B/C use their existing board-free PYNQ client skill. Only A operates the physical board; simulations, synthesis, implementation, upload probes and actual measurements remain distinct.
- The drilling-logging draft and attached packs are references. AD7606, 300 bps, compression, latency, Ryzen AI and the host application become requirements only when chosen by the current task version.
- Preserve credentials, node configuration, local edits, task ledgers and original operation evidence. No automatic replay of failed/interrupted/unknown side effects, no overlapping write ownership. Native GPT requires a special capability reason and reserve/validate/complete lease; DeepSeek stays Flash/max with no prescribed count. Critical decisions and acceptance belong to the quality main model at its highest available effort.
- Main/native GPT use this member's official builtin openai login; DeepSeek uses the existing separate direct provider. Do not introduce inference routers or copy credentials. Model discovery does not prove actual access.
- Keep project source and canonical distributables inside the repository. Build ZIPs from clean committed tracked files using `python -m fpga_mesh.distribution`; a requested desktop copy is a delivery copy. Vendor installers/images may remain outside with source and hash recorded.
- Runtime code lives in `fpga_mesh/`; deployment commands remain in `docs/deployment/OPERATIONS.md`, `deploy/HUMAN_STEPS.md` and `docs/deployment/IN_PLACE_UPDATE_2026-10-11.md`. Existing-node updates preserve state and use the idle fence; skills do not restart services or grant Astra/DeepSeek cloud scopes.
