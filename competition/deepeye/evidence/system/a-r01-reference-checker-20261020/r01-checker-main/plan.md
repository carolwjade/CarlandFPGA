# R01 rule trace checker: main-selected bounded implementation

Task DEEPEYE-IMPLEMENTATION-20261014/v1, work A-R01-CHECKER-20261019-v1.
Sole A Desktop main01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2 owns:
- PRODUCT competition/deepeye/tools/check_rules.py (new)
- PRODUCT competition/deepeye/tests/test_check_rules.py (new)
- PRODUCT competition/deepeye/docs/rules_verification.md (new)
- .planning/deepeye-resume-20261018/r01-checker-main/ evidence only.
No existing rules/CSV/contracts/taskbook/pipeline or peer/worker sources may be edited.
Progress candidate frozen under independent review; G02 author owns its editor/UI files.

Human already authorized following taskbook dependencies without stepwise permission.
Existing R01 taskbook specifies the checker, rules.json and requirements_trace.csv.
Main read both existing data files: fifteen official constraints plus H01-H15, five core
metrics, two selected specialist metrics, all statuses not_run. Checker is absent.
Primary PDF exists in ROOT but is absent in PRODUCT checkout. Do not copy or silently search
outside product by default. An explicit --source-pdf may use the already verified primary
original read-only; output must identify that source path and portability limitation.

Choose a standalone stdlib checker over modifying pipeline (no need to change orchestration)
or installing PDF tools at runtime (known exact original byte hash already fixes identity).
Recheck actual original SHA c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc.
Scope integrity checks recompute immutable requirements canonical hash c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
Pinned policy table covers original official IDs/pages/owner cards; cross-check exact CSV
against immutable H mappings and rule rows. Require strict bounded shapes, duplicate-key/row
rejection, valid statuses, concrete five-core/two-special coverage, correct pinned source and
separate ROCm/physical-recognition/physical-engineering gates. No3.3 weights substitution.

CLI stdout JSON only: malformed/inconsistent metadata or changed source -> exit1 failed;
missing original -> exit2 blocked; valid reference checks + --reference-only -> exit0;
default full command retains R01 not_run/blocked even if files claim passed. No model,
network, hardware, registration change, installer or artifact write. A future independent
acceptance integration is required before a full R01 pass; metadata claims never confer it.
No optional output writer is needed: caller captures stdout at its owned evidence path.

Write behavior tests first and preserve actual missing-entrypoint RED. Then implement, run
focused tests and actual CLI default/reference paths with original PDF. Preserve every raw
exit/log and hash; independently review before acceptance/publication. Do not rerun unrelated
193 progress/native/Godot suites. This is schema/provenance/trace validation, not fresh online
rules retrieval, actual registration verification, organizer qualification or measurements.
