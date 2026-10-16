# Project skills 2026.10.15.1

These exact role archives were built with `python -m fpga_mesh.distribution` from clean, committed, tracked source `a722af92d782ae66be396133895952f00855117d`. The manifest revision identifies the packaging source, before these distribution copies were added. `package-verification.json` records both archive and bundled installer SHA256 values. Every listed archive member and ZIP CRC was verified.

This version implements the human-authorized main-chat lifecycle/model selection policy and removes superseded fixed-model/native-special-capability restrictions. Task ownership, actual termination before reassignment, evidence, authenticated provider identity and A-only physical board operation remain required. H01–H15 are unchanged.

A uses the A archive; B and C use the BC archive. Retrieve these committed bytes at the exact publication commit, verify the archive SHA256, extract into a new local staging directory and verify the bundled installer hash before using the archive's `INSTALL.md`. Run that existing installer with the member's original project root and actual node ID. Keep the receiving main's existing ownership, local changes and junction layout; the installer performs its existing lock and rollback checks. Do not re-onboard or restart the controller for a skill upgrade.

Publication and hash verification do not establish a recipient download, installation or new-chat loading. Recipients report those stages separately with local evidence. Existing chats may retain previously loaded instructions; project policy changes do not override tool or platform developer requirements.
