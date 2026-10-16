# A independent B28-R1 cache resolver review

Decision: **B28-R1 offline acceptance passed**. This closes the scoped source-cleanup resolver finding in code and non-executable fixtures. It is not whole-PR29, continuity, deployment, live reconnect or product acceptance.

- PR29 tested head: `069cdfbb478bfa67390c61b9d749cab90c5e8327`
- Source: `3d92c8c4afd5174dda15330deb9f8931a41b9fd7`
- Operation: `B28-CACHE-RESOLVER-20261016-v1`
- Request SHA256: `143acc3923a92f1e950ca30d3a2b9af8be038adcf9c9f98bb9366611cdc469fa`
- Sender manifest SHA256: `f5c7e902af0825be44fcb8938a805b0fa07704a51ba142620d1ea69ab5b98ce1`
- Controller task: `B-RUNTIME-REPAIR-20261015/v1`; referenced handoff task: `B-RUNTIME-CONTINUITY-20261016/v1`.

All 11 artifacts match their sizes, SHA256 and actual Git blob bytes. Python source/test files also match the declared source commit. Standard handoff verifier reports valid=true, files_checked=11, exit0. The source remained unchanged through verification. `git diff --check 3c34470 069cdfbb478bfa67390c61b9d749cab90c5e8327` exits0 without output.

Python3.12.14: **77 related software tests passed in2.666s**, exit0:

```text
python -X utf8 -m unittest tests.test_runtime_cache_reuse tests.test_app_server tests.test_runtime_integrity tests.test_app_gateway
```

The unchanged original independent A B28-R1 reproducer is retained as `test_original_r1.py` (SHA256 `2c6134eb6ef27eb2834e5ffecfd6d38bc27a73776af03b115ece86852e802349`). Its **2 formerly failing explicit/automatic cleanup cases now pass in0.121s**, exit0. Command and raw logs are in `original-r1.json` and `original-r1-stderr.txt`.

Root inspected exact cache delta and independently verified the separate native review. The persisted selector is consulted before original-source discovery; its bound manifest/content key/inventory/files are checked on every resolution. A corrupt bound cache rejects without source, arbitrary-cache or shim fallback. New tests cover full source removal, a fresh Python process, sticky selector separation, invalid paths, manifest and payload corruption, junction rejection and transport noncreation. Existing initialization-versus-post-turn failure handling remains scoped by the related regression.

`child-review.md` contains the bounded code audit. `native-completion.json` records its verified terminal result and actual completed turn provider/model/effort (`openai/gpt-6-astra/medium`). Parent owns the acceptance decision. The publication-conflict test mocks a race; a real simultaneous-launcher experiment was not performed and no concurrency failure was demonstrated. Same-user hostile rewriting and modification between validation/launch remain explicitly outside this binding guarantee.

No service reload, real executable/model reconnect, merge, continuity integration acceptance, A27 combined regression, RTL simulation, synthesis, implementation, board or product acceptance was performed. The earlier cab13dc continuity checkpoint/147-test evidence remains separate. Existing directors, workers and service state were not changed by this review.

H01-H15 preserved: `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements hash independently recomputed as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
