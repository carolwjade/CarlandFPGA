# A G01/G02 composition checkpoint

The simulator now uses B's reviewed procedural assets through an A-owned presentation adapter, including explicit diagnostics and visible fallback when asset metadata, factory signatures or renderable geometry are invalid. Labels and picking follow the full transformed fallback geometry. Presentation geometry is separate from motion authority: B declares a 0.80 m visual drill and a separate disabled 1.04 m capsule. The disabled capsule is not adopted as motion authority.

The editor fits and scrolls at the tested viewport sizes, preserves disabled run/control state, and validates gate coordinates with the same exact binary64 geometric policy as the Python authority. Saving/opening restores the four real gate coordinates with nearest-even decimal conversion; malformed JSON number spellings are rejected across the structural walk. A path guard now permits legitimate U+FFFD filenames while checking encoded zero bytes, removing the erroneous startup NUL diagnostics.

## Independent evidence

Main rehashed the final combined review's 402 files, checked its original completed native result, and inspected all 15 bounded process receipts and raw streams. Fresh headless results: editor 696/0; persistence 628/0; UI fit 266/0; viewer integration 136/0; Unicode file I/O 6/0; numeric 14628/0 over 2100 cases; reader 427/0. Independent Fraction/current-Gate analysis found zero disagreements and 1116 exact legal coordinate roundtrips. Four unchanged asset-failure oracles passed 14/0, 10/0, 14/0 and 16/0. The identical Unicode test failed 3/6 against the old store and passed against the candidate.

Grammar/state 176/0 and B asset 622/0 are reused at verified exact transitive dependency, engine, harness, log and terminal hashes. They are not fresh composition runs. Original failed assertions, preparation errors and intentional malformed-input diagnostics are retained. The combined ordinary startup/checks have no inherited NUL, parse or script errors; deliberately malformed inputs still emit their recorded diagnostics.

The exact numeric, reader and grammar tests/inputs are committed under simulator/tests and simulator/grammar-fixtures. Run them with the pinned Godot 4.7.2 executable using --headless --path <simulator> --script res://tests/<name>.gd in a private copied checkout and private APPDATA/LOCALAPPDATA/TEMP roots. Numeric and grammar tests write observation JSON under res://tests. publication-inputs.json records all required paths. Existing read-only oracle logic and complete command receipts remain in the review archive.

## Native evidence and limits

Earlier frozen G02 native evidence establishes actual save, clear, reopen of two water objects, an orbit interaction and scrollbar dragging at a 1920x1080 client viewport. It does not establish a hard-rock edit, a post-open resave bit roundtrip or valid wheel routing. The installed UI helper sent those wheel events to the wrong coordinates. The later G01 native attempt was closed for the human to use the display; its title-bar capture is unusable. Current G01 visual quality and valid native wheel routing remain not_run. Subsequent work is entirely background/headless.

All 29 formal task cards remain not_run. No game-quality, physical collision/crossing, calibrated sensing, PC AI, board, control-chain or system acceptance is granted. H01-H15 and the pinned requirements hash remain unchanged. Negative zero is geometry-equivalent; no signed-zero bit preservation is claimed. The JSON work is a bounded number-grammar repair, not a complete independent JSON implementation.

## Archive policy

manifest.json covers the actual included immutable bytes. Original complete manifests remain under each source directory; archive-omissions.json explicitly lists source files omitted for generated environments, attribute metadata or conservative credential-field syntax. Original local evidence is preserved. Small source clones are retained for direct failure-fixture reproduction and deduplicated by Git, rather than erased. The archive excludes vendor engines and private leases. Main adoption records bind exact source bytes; package-only .gitattributes rules preserve those tested bytes on checkout without changing runtime semantics.
