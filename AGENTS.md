# CarlandFPGA project rules

- This repository contains a three-machine control plane and a separate PYNQ-Z2 single-machine development skill. Use `skills/pynq-z2-single-node/SKILL.md` for local PYNQ-Z2 design, verification, toolchain, and board-work tasks; use `fpga_mesh/` and `docs/deployment/OPERATIONS.md` for group coordination.
- The drilling-logging draft and attached skill packs are references. Do not treat AD7606, 300 bps, compression ratio, latency, Ryzen AI, or the final host application as settled requirements until a task version chooses them.
- In group work, only machine A may operate the physical board. B/C may design and simulate, then hand off a code commit, test plan, and evidence manifest to A.
- Keep simulation, synthesis, implementation, and actual PYNQ-Z2 measurements distinct. Preserve commands, tool versions, reports, logs, and artifact hashes; do not claim board results from a model or simulator.
- Keep project code and distributables inside this repository. Large vendor installers and board images may live outside it with recorded source and hash. Build the FPGA teammate ZIP from committed tracked files with `python -m fpga_mesh.distribution`; unrelated product packages and rules are outside this project.
