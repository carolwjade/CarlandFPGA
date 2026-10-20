# Bounded R01 source-refresh review

No defect found within the assigned artifact, metadata, and source-receipt scope. The final local audit passed 61/61 checks and exited 0. This is factual independent review evidence for the main; it grants no adoption, publication, or formal acceptance.

## Assignment and prerequisites

- Work: A-R01-SOURCE-REFRESH-INDEPENDENT-20261020-v1, agent /root/r01_source_refresh_independent_20261020.
- Original job: child-6ff6b0ece2704e3e9726e816b0c07d9d. The original helper returned execution_allowed=true before review.
- Current node configuration identifies A, project fpga-main. The transfer is active for director 01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2.
- Root and product immutable-scope requirements both reproduce canonical SHA-256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 and exactly H01-H15.
- Read-only Git returned product HEAD c0745419d7a317011d747f124544c98a900b1863. Current original rules bytes equal that commit's Git blob.

## Candidate integrity and minimal change

All ten candidate paths, byte lengths and SHA-256 values match the manifest, with no extra files. The candidate manifest SHA-256 is 85903a54312424fef5b5f6976730121a5ad4844f1ea1f15f777a7c8fa343ddf6. Complete per-file hashes are in review-evidence.json and the nonsecret manifest.

Original rules SHA-256: 52e6c8b395b544a744c2aee570cd14b2a443b92f6fd0d78c0c6fd6512019d7b1.
Candidate rules SHA-256: 50e19ea0513e4f7a66c5f5793223d190838afaf5a012c659ee7183068efcd4d9.

Both structural comparison and exact byte replacement confirm only:

- source.latest_online_refresh
- source.online_refresh_evidence
- source.online_refresh_scope

All official requirement text, page/owner mappings, human track, registration claims, metrics, assessment weights, physical-task interpretation, and gate statuses are unchanged. This check does not reinterpret the source or accept requirements.

## PDF and catalogue correspondence

The candidate PDF, original newly downloaded PDF, and repository's frozen source PDF are byte-identical: 950,952 bytes, SHA-256 c6ad82acd4f7bdcd13bd412e232ed85d05f2a87dd5e2cdd04f9d219f88b569fc.

The earlier catalogue and the Chinese-titled catalogue each report and contain 23 records with code 200. Their complete id-to-object-path maps agree. The candidate sanitized catalogue is exactly the expected projection of all 23 Chinese raw rows, including title and selected metadata, with URL query and fragment removed. Only id 25 has both 2026 and AMD in the title:

全国大学生嵌入式芯片与系统设计竞赛'2026FPGA赛道选题指南-AMD

Its query-free object path is the original pinned official URL, ending:

/profoss/upload/2026/08/31/8c7a809f-f0b8-42e4-996a-3a5f2f132288.pdf

The PDF receipt binds the earlier untitled catalogue, SHA-256 277c50128b3037b929c9ecab393fd6d60d4f4a095e1b5c9f996e66740dd7382b. The Chinese catalogue receipt binds its separate raw body, SHA-256 0a39cd6f266a09e053bb825085d48293fccf3f0112a7cd6e8e98a7673f24da3a. Their distinct identities are preserved; correspondence is established by the full object-path maps, including id 25.

The PDF receipt records HTTP 200, application/pdf, Content-Length 950952, default HTTPS certificate verification, the same actual body length/hash, and no account credentials. The preserved fetch script uses the catalogue-issued URL unchanged through standard urllib HTTPS retrieval. This corroborates the saved retrieval record; no new network observation was made during this review.

Every included receipt remains byte-identical to the original. Corresponding body byte lengths/hashes and fetch-script hashes match. The old unsigned PDF request remains 403; the original HTTPS catalogue certificate failure remains recorded. The unsigned API's preserved body has code 1001 and message 时间戳无效, supporting the invalid-timestamp explanation rather than an account-denial claim. The public frontend and request scripts agree on millisecond timestamp, 16-character alphanumeric nonce, sorted parameter envelope and uppercase MD5 signing; the frontend hash is bound to the signed receipt.

## Query handling and wording

No raw catalogue body is packaged. A local value scan finds no original temporary object authorization URL/query, object signature/key value, or frontend signing constant in any candidate file. No such values were printed by this review.

The main clarified that fixed pageNum/pageSize query parameters in the original safe API401 receipt are intentional evidence and may remain. Exactly two candidate URL fields contain these parameters: requested_url and final_url in fpga-public-list.retrieval.json. They contain no temporary object authorization or client signing values. Candidate README refers specifically to temporary URL queries; result.json's "sanitized copies remove every query" describes the sanitized catalogue copies and is consistent with that clarified scope.

Candidate README/result truthfully qualify HTTP catalogue transport, point-in-time observation, possible updates elsewhere/later, original 403 and 401 observations, lack of account/registration changes, and the preliminary diagnostic disclosure. The disclosure is acknowledged in the assignment and candidate; this review did not replay the original conversation output.

## Published metadata validator

The review executed the existing published check_rules.py pure metadata definitions unchanged through AST selection, using standard-library namespaces. It did not import or run the module, its main routine, file helpers, network code, or full test suite.

Inputs:

| Input | SHA-256 |
|---|---|
| Candidate rules.json | 50e19ea0513e4f7a66c5f5793223d190838afaf5a012c659ee7183068efcd4d9 |
| Current requirements_trace.csv | 4fe991b4247cadbe87cfaf7b0dc77d3e4a7a9e0956ccbfc5dffbd25a5f397b08 |
| Current immutable_scope.json file bytes | 6a86000e97d1571c0b7b89b9d3cf7facb11d2b6a06455eb1d53e0637676b6bc4 |
| Published check_rules.py | c864fb29c13bbe64dba8d6e344ec1f229e6cc757a3e1fa29018264184215384e |

Exact output:

```json
{"human_requirements":15,"official_requirements":15,"core_metrics":5,"special_metrics":2,"requirements_sha256":"c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"}
```

This validator checks declared mapping consistency; the separate byte/receipt/catalogue audit supports the added source-observation fields.

The product worktree's default original-PDF source path is absent. For the main's planned post-adoption reference-only CLI, supply the adopted evidence PDF explicitly:

```text
<root>/.local/venv/Scripts/python.exe -B -X utf8 <product>/competition/deepeye/tools/check_rules.py --reference-only --source-pdf <product>/competition/deepeye/evidence/system/a-r01-official-source-refresh-20261020/current-amd-guide.pdf
```

That full CLI was not run by this child, per assignment.

## Formal boundaries and preservation

All 29 actual execution-plan task statuses remain not_run. All 30 trace rows remain not_run, all 15 official requirement statuses remain not_run, R01 and the ROCm/physical-recognition/physical-engineering gates remain not_run, and independent registration evidence remains false. Formal acceptance and hardware-enable eligibility remain false.

Still absent from this review: independent registration/qualification evidence, organizer recognition of the proposed real physical task, actual ROCm project and physical engineering evidence, and separately reviewed formal acceptance integration. Source identity is not any of those gates.

The 43 files in the original evidence/candidate directory were unchanged across the audit; all 36 directly read input files also retained their hashes. Review writes are confined to this directory. No extra network, GUI/display, board, service, installation, Git write, peer/group send, provider/credential change, or subagent operation was performed.

## Review-tool diagnostics

The first ad hoc execution-plan projection expected a list and received the actual task dictionary (KeyError: 0); the corrected read-only projection confirmed all 29 not_run.

The initial full local audit passed 60/61 checks and exited 1 because the reviewer associated the unsigned API receipt with fetch-catalog.py. Inspection showed its actual source is fetch-index.py, exactly matching the recorded SHA-256 27630e493a16c616ff51fb6dacfa936fae105b39f1b12a74c8f4b062aeea0397. The first script/report/output/command/input snapshot were retained, then only that reviewer association was corrected. The final audit passed 61/61, exit 0; no candidate or original evidence correction was needed.
