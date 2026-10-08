# PYNQ-Z2 Single-Node Skill Implementation Plan

> For agentic workers: implement each task with an observed red/green test cycle and review the generated artifacts before treating the task as complete.

**Goal:** Ship an independently installable PYNQ-Z2 FPGA development skill with reliable local preflight and verifiable handoff to the existing three-node controller.

**Architecture:** The skill stays under skills/pynq-z2-single-node and uses only Python standard-library scripts. It does not import or start fpga_mesh. Its request JSON matches fpga_mesh.hardware.HardwareRequest, and a repository test checks that boundary. Physical board work remains A-only in the mesh.

**Tech Stack:** Codex skill Markdown, Python 3.12 standard library, unittest, optional Vivado Tcl/AMD Vivado MCP and ModelSim.

## Global Constraints

- Target board: AMD PYNQ-Z2, XC7Z020-1CLG400C, Vivado part xc7z020clg400-1.
- Use a PYNQ-Z2-compatible PYNQ 3.1.1 image for future board work; PYNQ 4.0 does not support Z2.
- AD7606, 300 bps, compression ratio, latency and Ryzen AI are candidate requirements, activated only by an approved task profile.
- Preserve simulation, synthesis, implementation and measured hardware evidence as distinct states.
- B/C may develop and simulate; A alone performs board operations.
- Do not enable hardware_enabled, install a speculative Vivado toolchain, or claim on-board acceptance without observed evidence.
- Deliver the skill in the repository, the local Codex skills directory, the FPGA teammate distribution, and the user-required distribution ZIP after validation.

---

### Task 1: Deterministic helpers and tests

**Files:** Create skills/pynq-z2-single-node/scripts/preflight.py, scripts/handoff.py, tests/test_pynq_z2_single_node.py.

**Interfaces:** preflight.py prints schema_version=1, Vivado/ModelSim discovery and board.status=not_checked. handoff.py create --root ROOT --input REQUEST_JSON --output MANIFEST_JSON and verify --root ROOT --manifest MANIFEST_JSON. Request fields match HardwareRequest; stages carry passed/failed/blocked/not_run and optional logs.

- [ ] Write tests for missing tools, request hash compatibility, valid manifest, missing/modified file, path escape, and a passed stage without a log.
- [ ] Run `& 'C:\Users\CarlJade\Documents\ChatGPT\FPGA多机协作开发\.local\venv\Scripts\python.exe' -m unittest discover -s tests -p test_pynq_z2_single_node.py -v`; observe expected failures before scripts exist.
- [ ] Implement only the behavior demanded by those tests; canonicalize the request with sorted compact JSON and SHA-256, as HardwareRequest does.
- [ ] Run the focused tests again and then the full unittest suite. Retain output and exit codes.

### Task 2: Discoverable skill and references

**Files:** Create skills/pynq-z2-single-node/SKILL.md, references/pynq-z2.md, references/telemetry-option.md, optional agents/openai.yaml.

**Interfaces:** Entry skill routes board/version decisions to pynq-z2.md and candidate telemetry methods to telemetry-option.md. The workflow invokes scripts by their public CLI, and labels absent tools and board measurements explicitly.

- [ ] Draft trigger text that selects PYNQ-Z2 local FPGA development and excludes generic multi-machine coordination.
- [ ] Record RTL/golden-model, CDC/RDC and reset, FIFO restart, ModelSim/Vivado, resource/timing and board evidence decision points.
- [ ] Record official AMD/Xilinx URLs, PYNQ version boundary, matching bit/hwh requirement, and optional AMD Vivado MCP.
- [ ] Run `python C:\Users\CarlJade\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/pynq-z2-single-node` with the working Python runtime. Check the actual skill against the provisional-topic boundary and script help.

### Task 3: Integration documentation and package

**Files:** Modify README.md; create docs/deployment/SINGLE_NODE_PYNQ_Z2.md; create docs/superpowers/specs/2026-10-08-pynq-z2-single-node-skill-design.md and this plan.

**Interfaces:** Document request JSON compatible with HardwareRequest, artifact digest verification and A/B/C roles; keep installation independent of the running mesh. Existing fpga_mesh/distribution.py packages committed tracked files.

- [ ] Explain a one-machine workflow from preflight to handoff, with commands that run from the repository root.
- [ ] Show which draft-topic values are optional and how to activate only selected acceptance criteria.
- [ ] Copy the verified skill to the local Codex skills directory.
- [ ] Commit reviewed source, run fpga_mesh.distribution to build teammate ZIP, verify its manifest and CRC.
- [ ] Update the user-required D:\lceda-pro\EasyEDA-Codex-Kit.zip through its safe packaging path and verify inclusion plus prior entries.

### Task 4: Final verification

**Files:** Review all modified files and generated package outputs.

- [ ] Run skill quick validation, CLI help, focused unittest, full unittest, compileall, and ZIP CRC/SHA-256 verification.
- [ ] Run preflight on this computer and record actual Vivado/ModelSim results; do not infer board availability.
- [ ] Reopen the design and plan, check every implemented requirement and absence of secrets or stale package entries.
- [ ] Report only observed local passes and separately name unavailable Vivado/physical-board gates.

