# B28 cache resolver bounded child review

Task B-RUNTIME-REPAIR-20261015/v1; work A-B28-CACHE-AUDIT-069cdfb.
Agent /root/b28_cache_audit; lease child-4beac666eca6471aabc262222c7f8668.
Reviewed HEAD: 069cdfbb478bfa67390c61b9d749cab90c5e8327.
Source delta: 3c34470 -> 3d92c8c4afd5174dda15330deb9f8931a41b9fd7.

## Result

No actionable correctness defect identified in the bounded cache binding/manifest delta. This is code-review evidence for the parent, not final acceptance, deployment, continuity acceptance, or runtime/board evidence.

- fpga_mesh/app_server.py:169-175 checks the persisted selector before inspecting the old source. Explicit and Desktop selectors are distinct and normalize the selected path; source cleanup does not invalidate a present binding.
- fpga_mesh/app_server.py:114-130 validates the binding structure, selector, content key and saved manifest digest; a damaged bound snapshot raises rather than selecting another runtime.
- fpga_mesh/app_server.py:70-106 verifies the manifest digest, strict relative paths, case-fold duplicates, exact file inventory, required binaries and payload hashes. Link checks include ancestors. No concrete traversal or fallback defect found in this bounded review.
- fpga_mesh/app_server.py:133-155 publishes a fully written/fsynced binding through exclusive hard-link creation, then reads and validates the winner. Lines 221-238 verify a copied snapshot before rename and verify the published destination afterward.
- tests/test_runtime_cache_reuse.py covers explicit/auto source removal, fresh Python resolution, no old-source inspection, sticky selection, damaged cache and binding failures, malformed paths, failed copies, publication conflict, junction rejection and transport noncreation on integrity failure.

## Limits

The publication-conflict test mocks _bound_runtime; it is not a real concurrent-process race experiment. No actual concurrency failure was demonstrated, so this is a coverage limit, not a blocker. No real executable, model, service, deployment, queue, credential, peer or board operation was performed. No production or test edits were made. No claim is made about unrelated continuity code. The parent reported 77 tests passing and 11/11 manifest checks; this child did not rerun or independently claim those results. No runtime-backed model/effort identification was obtained.

## Commands and observed evidence

1. Validation-only first attempt imported fpga_mesh.local_control and failed ModuleNotFoundError; no project audit occurred before successful validation. Corrected imports supplied by parent: fpga_mesh.child_control.LocalControlFileClient and fpga_mesh.project_cli.discovery. Via existing .local/venv/Scripts/python.exe -B -X utf8 - and asyncio.run(client.call('native_validate', private args)), controller returned status=running, native_agent_id=/root/b28_cache_audit, execution_allowed=true and the assigned work_id. Token is intentionally omitted.
2. Get-Content read root mandatory skill, skill-role.json, references/protocol.md, immutable_scope.md/json, transfer.json and .planning/b28-cache-review/task_plan.md. Existing config selected-field read confirmed node_id=A and project_id=fpga-main.
3. Python canonical JSON SHA256 (ensure_ascii=False, sort_keys=True, separators=(',', ':')) of root immutable_scope.json requirements returned c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804, matching the pinned contract. An additional attempt to read the same document under this historical review worktree returned FileNotFoundError; the required current root contract was read and verified, not inferred from that worktree.
4. git -C .local/a-b28-cache-review rev-parse HEAD returned 069cdfbb478bfa67390c61b9d749cab90c5e8327.
5. git -C .local/a-b28-cache-review diff 3c34470 3d92c8c4afd5174dda15330deb9f8931a41b9fd7 -- fpga_mesh/app_server.py tests/test_runtime_cache_reuse.py; numbered Get-Content of app_server.py corroborated exact lines above.
6. git -C .local/a-b28-cache-review status --short showed only untracked handoffs/node-a/ before this report; no source/test changes observed.
7. Memory quick search produced no task-relevant match; no historical claim was used. rg was unavailable; Select-String was used instead.

## Scope preservation

DEEPEYE-HUMAN-LOCK-20261014/revision1; requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804. H01-H15 preserved unchanged. Transfer generation 2 identifies Desktop director 01a13d7e-dcf1-7272-a738-a637dd62ff9d; ownership untouched. Parent retains critical decisions and acceptance.
