# Private G02 gate numeric candidate

The four candidate files correct the reproduced gate slack and gate JSON parser loss in the tested domain. They are ready for the main's independent algorithm/source review; they have not been adopted into PRODUCT. All 29 formal cards remain not_run. Contract DEEPEYE-HUMAN-LOCK-20261014/revision1, H01-H15, canonical requirements SHA256 c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 were independently verified for root and PRODUCT; active generation-2 director transfer and node-A identity were read. The assigned native lease was validated with the canonical agent identity before execution.

## Change and adoption

`candidate/editor/scene_document.gd` and `layout_codec.gd` call the same `gate_numeric.gd` predicate. Coordinates must be finite binary64 values within inclusive ±14.85. Same-face circles use exact represented-coordinate subtraction and squared-distance comparison against binary64 .30, equal to twice binary64 .15. Distinct faces remain legal without a same-face distance test. Exact tangencies are accepted; no epsilon, rounded geometry subtraction, rounded squared-distance or sqrt affects acceptance. Existing sqrt only formats rejection text. Python geometry/clearance policies and all B/UI/viewer sources were not edited. Obstacle tolerances remain unchanged.

`gate_json_numbers.gd` structurally extracts only the four coordinate numeric tokens under layout/gates/entry-or-exit/u-or-v, after the engine parses JSON. It uses decoded object keys, refuses duplicate decoded keys throughout the JSON, distinguishes strings/arrays/objects, checks separators/depth/end, and restores exactly rounded gate coordinates before existing schema/hash/geometry validation. No schema or commitment format changes. Existing schema/type/contract/file-size/depth checks and transactional import remain. The emitter still uses full precision. The six-decimal commitment is identity metadata, never geometry precision.

The gate reader needs a bounded exact decimal converter because the engine JSON parser, String.to_float and float(String) all exhibit the same loss. Integer rationals plus adjacent-float exact midpoint comparisons implement binary64 nearest-even, with an approximate starting point used only for performance. Four local steps precede a bounded binary-search fallback; correctness does not depend on approximation quality. Zero, subnormals and tie parity are covered. Literal malformed numeric grammar and numeric tokens longer than 2048 characters reject explicitly; ordinary saved coordinate tokens are within 25 characters. Legal represented values encoded with supported JSON numeral lengths remain supported. This explicit cap is a conservative lexical resource policy, not a new geometric margin.

`candidate-pins.json` records four complete source hashes, exact PRODUCT editor baseline hashes, and `candidate.patch` SHA256. The patch uses simulator-relative paths, allowing clean adoption after matching those baseline bytes. Fresh tests bind the frozen stage source hashes recorded per execution; concurrent PRODUCT UI/viewer/test changes were never overlaid into the stage or adopted here.

## Root cause and retained RED

The baseline accepted 0.2999999995 separation and 14.8500000005 coordinates. Independent expectations use Fraction exact binary64 rationals, Decimal precision 2500, and actual copied/pinned Python Gate plus validate_gate_pair; all agree. Raw little-endian double input avoids assuming the engine's decimal parser is an oracle. The original 2100-case run produced 14280 checks / 5024 failures / exit 1.

Removing slack and adding an exact geometry predicate alone exposed another defect: full-precision JSON emitted all 2100 original inputs exactly when independently parsed by Python, but Godot's parser changed 192 rows. In 48 rows, invalid original geometry became valid: e.g. 14.850000000000001 became 14.85. That caused 144 decode/apply/transaction assertions to fail. Original `raw/transport-diagnostic` text, original/parsed bits, streams and results remain. The exact gate reader removes all 48 bypasses in the tested corpus. No tested geometry or reader mismatch remains against the stated oracles.

The first candidate mistakenly removed the codec's EPSILON constant still used by unrelated obstacle validation. Its real parse/compile errors, 55-second timeout, forced process kill and source pins remain under raw/green; it is not GREEN. The corrected candidate preserves that constant. A separate numeric-grammar RED has two failures for 01 and 1.; the final converter rejects those and the other malformed fixtures.

Two extra signed-zero probes each reported six failed sign-bit assertions. The built-in emitter normalizes -0.0 to token 0.0. This is the existing engine behavior; ±0 are geometrically equal, and the main explicitly does not require preserving their sign in geometry files. The failed probes remain unchanged. The final probe separately asserts existing normalization on all six faces and preservation of raw -0 tokens by the reader. Exact roundtrip claims cover the 1116 legal corpus rows, which contain no negative-zero input, and nonzero scalar bits; they do not claim emitter preservation of negative-zero sign.

Two shell invocations returned exit 1 with no output and created no new process-result directory; explicit copy/readback and separate runner invocations then succeeded. No PASS is inferred from those empty invocations. They did not replace any raw native result.

## Fresh verification

All final runs use the pinned Godot 4.7.2 GUI executable SHA256 ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424 with --headless. Command/result records include argv, PID, executable and exact source hashes, private environment paths, stdout/stderr, real exit and confirmed termination. Each native run is bounded by 55 seconds. The Python independent-oracle subprocess is separately pinned and bounded at 50 seconds.

| Evidence | Fresh result |
| --- | --- |
| Raw geometry + setter + encode/decode/apply + save/reopen | 2100 rows, 14628 checks, 0 failures, exit 0 |
| Full roundtrip bit audit | 1116 valid corpus layouts, 0 coordinate-bit mismatches |
| Gate number reader/structural attacks | 183 decimal fixtures; 427 checks, 0 failures, exit 0 |
| Finite/±0 policy | 195 checks, 0 failures, exit 0 |
| Existing frozen-stage document regression | 696 checks, 0 failures, exit 0 |
| Existing frozen-stage persistence regression | 618 checks, 0 failures, exit 0 |
| Fresh Python Fraction + Decimal + actual Gate re-evaluation | 2100 rows, no oracle disagreement; eight independent limb/unit checks; exit 0 |
| Prior final combined evidence integrity | all 150 persisted manifest entries verified |

The corpus covers all 36 directed face pairs, six face signs, positive/negative offsets near cube edges, both coordinate axes, diagonals, represented nextafter neighbors, translated represented tangencies and subnormal components. Reader fixtures cover exact decimal midpoints and nearest-even neighbors, normal/subnormal transitions, signed zero, exponents, malformed numeric grammar, long numerals, duplicate/escaped keys, fake tokens inside strings, nested decoys, unexpected types and over-depth input. Rejected setter/import paths assert geometry/history preservation. The existing persistence regression also exercises file-store/save failures.

The final five native test runs have unchanged source and PRODUCT maps during each run. Earlier full-PRODUCT maps changed under other authorized owners; exact changed names/hashes are in execution-ledger/source-after. The PRODUCT editor inputs remain byte-identical throughout. This child made no PRODUCT write. The frozen-stage broad regression results do not establish the behavior of subsequently changed PRODUCT UI/viewer/test sources.

The early harness required the entire PRODUCT map to stay unchanged; concurrent external viewer edits therefore caused wrapper exit 1 even for the zero-failure native run under raw/green-exact-reader. Its native exit and full external delta are retained separately. The final harness binds the frozen inputs, rejects any change to PRODUCT editor files, and records the complete unrelated PRODUCT delta rather than inferring this child wrote those files. Final runs have no such deltas.

Expected invalid-input tests retain engine exponent warnings. Existing document/persistence regressions retain Unicode/NUL/invalid-UTF8 fixture diagnostics. Final runs have no script/parse/compile failure. Clean stderr is not claimed.

## Arithmetic and resource review notes

Binary64 magnitudes decode to exact integers in units 2^-1074. Base 2^15 limbs, carry after each operation, and unsigned magnitude subtraction avoid signed-overflow assumptions. A legal coordinate difference is below 29.7 and needs at most 1079 bits / 72 limbs. Squares and their sum fit 144 limbs. Every schoolbook multiply intermediate is at most BASE²-1 <2^30; additions/subtractions and small products are also far below int64 limits. The 2D predicate performs three bounded multiplications. Zero and subnormal values use the same units; no underflow or float cancellation occurs.

The numeric token cap is 2048 characters. After leading-zero removal and decimal-order bounds, a surviving denominator exponent is at most 2372; coefficient, denominator and scaled intermediates stay below 600 base-2^15 limbs. Exponents saturate at magnitude 10000 during scanning, before any overflow. Orders above the supported magnitude reject; orders definitely below half of the minimum subnormal round to signed zero. At most 63 binary-search iterations are needed between positive-zero and the positive 16.0 bit pattern. Midpoint comparison uses integer rationals and selects the even low-order significand bit on equality. At most four gate tokens are converted. Existing JSON size 1 MiB and depth 32 bound scanning; source does no filesystem I/O or evaluation.

This is an implementation proof outline plus bounded evidence, not independent algorithm acceptance or a worst-case runtime guarantee. A reviewer should audit exponent/order early exits, bit decomposition/endianness, integer carries, midpoint tie handling, fallback bounds, lexical path handling, duplicate/escaped key semantics, and the declared numeric-token cap. No dependency/platform installation, Git operation, external message, GUI, product Run, board, service, queue/lock, credential/provider operation or child delegation occurred. No UI/game/route/full-volume crossing/causal sensing/PC AI/control-chain/formal card is accepted by this work.
