# Private JSON number grammar follow-on for main review

Prepared a minimal additive repair to reviewed patch `e403b274483c3074423950a4d12a358a0b95b4263345cfd62c339e7429e3c292`. Only `editor/gate_json_numbers.gd` changes: the existing structural walker checks each numeric token with the unchanged `GateNumeric._valid_decimal_token` helper before recording any genuine gate token. Exact numeric conversion remains restricted to the four existing `layout.gates.{entry,exit}.{u,v}` object paths. The unchanged arithmetic, codec and document retain their exact reviewed bytes. No PRODUCT file was edited or adopted. Main owns review, integration and acceptance; all 29 formal cards remain `not_run`.

Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, every H01-H15, and canonical requirements SHA256 `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804` were verified in root and PRODUCT. Active generation-2 transfer, node-A role and existing node identity were read. The original job `child-cff91e0872734285a30a18f970f2929f` validated before work. No new job, child, writer, queue or lock was created.

## Change and reproduction

The independently recorded root cause was the numeric branch of the structural walker: it collected numeric-looking characters at every path, but only the four true gate paths subsequently reached the existing grammar validator through exact decimal conversion. Consequently, Godot's permissive parser could accept `01`, `1.` and `1.e0` in non-gate fields. This follow-on adds one grammar call in that same branch and reuses the token for gate extraction; it does not add another parser or change schema, geometry, rounding or negative-zero policy.

The four original independent `grammar-fixtures/*.json` were copied byte-for-byte and their hashes were checked before and after testing. The three invalid saved envelopes now reject and the valid `1e+0` control still decodes. Original actual RED evidence remains in the independent evidence directory (`raw/baseline-grammar`, `raw/candidate-grammar`), both untouched. Fresh corrected RED against the exact reviewed candidate has 48 expected assertion failures, exit 1, no script errors and actual terminal=true. This includes accepted malformed non-gate numbers and resulting live-document replacement. GREEN checks the same intended grammar behavior on the final candidate.

## Actual background software evidence

Every Godot command uses the pinned Godot 4.7.2 executable SHA256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`, `--headless`, private APPDATA/cache/temp paths and `CREATE_NO_WINDOW`. No window/focus/mouse/keyboard/capture/display-setting operation was performed, including after the human's background-only instruction. Each of the ten bounded subprocess records has actual argv, PID, executable hash, stdout/stderr hashes, source-before/after maps, exit, timeout and terminal evidence. None timed out or had a parse/compile/script error. `execution-ledger.json` indexes the records. The runner's exact three source versions are retained and checked against their recorded hashes.

| Run | Actual result |
|---|---|
| Corrected baseline grammar RED | 176 assertions, 48 failures, exit 1, terminal=true |
| Corrected final grammar | 176 assertions, zero failures, exit 0 |
| Strengthened final state guard | 176 assertions, zero failures, exit 0; full undo/redo contents and document metadata preserved |
| Original numeric corpus, one final-candidate replay | 2,100 rows, 14,628 assertions, zero failures, exit 0 |
| Original decimal/structural reader corpus, one final replay | 183 cases, 427 assertions, zero failures, exit 0 |
| Independent Python reread, final analysis | 2,100 Fraction/current-Python-Gate decisions agree, 1,116 exact legal wire/reopen bit sequences match, exit 0 |

The 81 new reader rows compare syntax expectations with CPython `json.loads`, not the candidate's helper. They cover invalid and valid numerals in ordinary objects, nested arrays and obstacle position fields; genuine gate fields; strings containing malformed numeric decoys and escaped quotes/backslashes; fake paths through arrays; a long valid non-gate coefficient exceeding the gate-only 2,048-character support limit; finite values far outside the gate range; underflow/overflow spellings; and a high-precision non-gate decimal. Every accepted non-gate-only row compares serialized parsed data before and after restoration, proving this repair leaves the engine's non-gate values unchanged in these contexts. This is not a new guarantee that those values have arbitrary precision.

Six full-codec obstacle envelopes vary `position.x` with the three malformed spellings and three equivalent valid spellings. CPython independently rereads their saved complete texts. Every malformed envelope rejects; valid variants decode. Rejected imports start with a real obstacle, edited gates and nonempty undo and redo histories. The guard compares gates, obstacles, commitment, actual undo/redo arrays, selection, next object ID, seed metadata and layout origin. Rejection may append the existing warning event; log silence is not claimed. Source inspection confirms `apply_layout_text` returns on decode failure before geometry/history replacement.

The 2,100-row oracle uses exact Python `Fraction` over represented binary64 inputs and the privately copied actual Python Gate implementation, current hash `5e33a60927334cee4473d5f78afc248f04d3a5ef00db465b2bcdf14c1adc3839`. It does not reuse candidate arithmetic. Earlier unchanged arithmetic-only audit and independent decimal-midpoint evidence are reused solely at the exact unchanged `gate_numeric.gd` pin. The new numeric and reader corpus runs check the changed walker in use. No combined current G01/G02 integration, GUI, board or product acceptance is inferred.

Godot emits retained `Exponent too high` warnings for intentional overflow spellings in three new non-gate reader contexts and two existing reader rejection contexts. These are engine warnings, not hidden script errors. Numeric syntax validity is kept separate from finite-value/schema policy. Valid non-gate overflow spelling still reaches the same existing engine representation, while genuine gate coordinates keep the existing finite-range conversion rules.

## Preserved local negative evidence

The first new test harness incorrectly seeded a water obstacle with material priority 1; the existing codec requires priority 2. Its initial RED has 40 failures and the first attempted GREEN has one fixture failure (`obstacle legal control exports`), both exit 1 and terminal=true. Their exact harness source and fixture corpus are preserved. The fixture was corrected with the existing `add_obstacle` API, without a product change. The corrected RED/GREEN then exercised actual full-codec obstacle cases. A final targeted rerun strengthened the history guard from depths to actual history contents; no candidate code changed between these successful runs.

One subsequent analysis invocation selected a new label before the runner recognized it. It raised `IndexError` before starting a subprocess. `raw/analyze-state-final/runner-startup-failure.json` retains that distinction (no child PID or child completion is invented). The runner dispatch was corrected; `raw/analyze-final` records the successful bounded Python analysis. An earlier successful analysis remains separately retained.

## Integrity and portable handoff

All 173 author-manifest entries and all 98 independent-manifest entries were rehashed. Full before/after maps verify both entire original evidence directories unchanged, excluding private lease material that was never read into tool output. PRODUCT has no before/after file delta. The final four stage files exactly match `candidate-pins.json`. `source-before.json`, `source-after.json` and the runtime records retain exact source maps.

`candidate-additive.patch`, SHA256 `adc0dc6be11966438812e2e7c756c570d345dc5c7509fbba40d1a0de6664f708`, is a portable unified patch against the reviewed four-file candidate, not against the original PRODUCT baseline. Main can first adopt the reviewed base patch `e403b274483c3074423950a4d12a358a0b95b4263345cfd62c339e7429e3c292`, then this additive patch. A private line-by-line patch application reconstructed the exact final reader bytes and hash in `patch-application/editor/gate_json_numbers.gd` without Git or PRODUCT writes.

| Candidate path | SHA256 |
|---|---|
| `editor/gate_json_numbers.gd` | `8554c99c1d8b70c9ef7471b3eb06ee994aef6f33397a2612f09d5c55aa73a3fa` |
| `editor/gate_numeric.gd` | `9356b645b4ce947c9825b3766a6f6e2f690ceca08bdb888ce2faf884f84cd461` |
| `editor/layout_codec.gd` | `adb5c7f1c24390ba6aa8456e40e713ac55a1dd80c2a866b9802e3775ee4826ef` |
| `editor/scene_document.gd` | `2bcc0c620333582361706f0b23b7e4bcc54b31a4e2a0cc6618935dcd296bdd6f` |

Additional lexical work is linear in the total number-token text within the unchanged codec 1 MiB/depth caps; at most four tokens still receive exact conversion. The direct reader retains its existing reliance on callers for the file-byte cap. No performance benchmark or universal latency guarantee is claimed. This bounded work establishes tested JSON NUMBER grammar behavior across the existing structural walk; it does not claim full JSON conformance, such as all possible engine string/literal/parser divergences.

No GUI, product Run, network/peer publication, Git, physical board, service, provider/credential, queue/lock, or child operation occurred. The candidate is ready for main's independent review. Visual checks and combined integration remain main-owned pending work. All 29 formal cards remain `not_run`.
