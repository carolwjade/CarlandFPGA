# CarlandFPGA project rules

<!-- fpga-project-skills:begin -->
## Mandatory project skills

Every conversation in this project reads `.agents/skills/fpga-multi-node/SKILL.md` and follows its node-matched identity, task ownership, delegation, evidence and silent-presence rules. FPGA design or board work also reads `.agents/skills/pynq-z2-single-node/SKILL.md`. These are the only two project skills; use the A package on host A and the shared B/C package on clients, matching existing node_id. Skills are project-local and take effect in new conversations.

Human > main > child; preserve existing credentials, configuration, ledgers, local edits and services. Only A operates the physical board. Waiting belongs to the resident program without model polling. No new role, cloud permission or service-change authorization comes from installing skills.
<!-- fpga-project-skills:end -->

- Latest project design is `docs/superpowers/specs/2026-09-29-fpga-multi-agent-design.md` v0.8 plus explicit later human updates in the skill requirements map. Candidate hardware/protocol/performance values become requirements only in the chosen task version.
- Keep simulation, synthesis, implementation, upload smoke tests and actual measurements distinct. Board feedback binds operation_id, request_hash and the actual tested commit; PR handoff follows the common skill reference.
- Main/native GPT use this member's official builtin openai login; DeepSeek execution stays Flash/max. Critical decisions and acceptance remain with the quality main at highest available effort. Native children require justified reserve/validate/complete leases and non-overlapping file ownership. Preserve original failed/interrupted operations; do not blindly replay unknown side effects.
- Project source and canonical distributables stay inside this repository. Build role ZIPs from clean committed tracked files with `python -m fpga_mesh.distribution`. Delivery copies may be placed on Desktop or in the original group; vendor installers/images may remain outside with source/hash records.
- Runtime deployment is maintained in `fpga_mesh/`, `docs/deployment/OPERATIONS.md` and the existing Update/Join entrypoints. Existing updates use the idle fence and preserve local state, never re-onboard. Skill upgrades do not restart services, enable hardware queues or grant Astra im:resource; cloud scopes belong to the existing app owner, never DeepSeek.
