# A background verification checkpoint, 2026-10-21

The evidence binds software source at b074eaa10012fc5b89f818926195fd24f0bef1bd.
Thirteen R03 software command groups have passing evidence: eight from the first
checker, four targeted dependency rechecks, and the final pipeline selftest.
Pipeline ran 25 methods: 24 passed, one intentional nested-selftest skip. No
product source was altered to obtain these results. The first complete checker
still has its actual failed result; this summary combines exact-source records.

Preserved failures identify missing jsonschema in the chosen interpreter, the
initial eight-process test cap, Windows Git long-path fixture failures, and an
undersized 96 MiB clone quota. The successful test environment reused existing
host dependencies, scoped core.longpaths=true to child processes, and derived
fixture storage limits from the actual Git tree. The containment test intentionally
created one link; the temp monitor counted it without following it. Product
containment checks were unchanged. All recorded original process objects stopped.

The new A-only physical baseline loaded the exact previously reviewed PYNQ base
bit/HWH once and performed 384 actual MMIO comparisons in offsets FC00..FC3C.
All matched. Sixteen original words, observed reset and export state were restored;
independent post-read found FPGA manager operating. Request, source/tested commits,
script and bit/HWH hashes are in summary.json and the raw board report. This is
base-overlay/64-byte BRAM readiness, not DeepEye custom RTL, TTL or control acceptance.
The earlier FPGA configuration was recorded and was not restored.

Five selected Python wheels (3197515 bytes) now match published full hashes and
retained METADATA; ZIP/RECORD validation passed without installing or importing
vendor code. Twenty-five original process objects across successful acquisition
and verification runs stopped. Two earlier attempts remain failed: a trusted
system executable's hard link was refused before resume; a second resumed attempt
was stopped when its two-object native tree violated an incorrect single-process
assumption. No response body survived either. A new, separately selected attempt
used byte-identical single-link curl and a bounded four-object tree. Six AMD wheels
remain missing; project CNN/runtime acceptance is still open.

The saved G03 full48 independent source/data review was adopted after main rehashed
37 retained public files and 4165 external inputs. The worker ended on provider
quota before sealing/completion. Its original native job is cancelled, not relabeled
completed. The maximum saved-vector difference is 3.470108633346818e-18 V/m, below
the unchanged 1.967577343353139e-12 V/m consistency gate. This does not qualify the
receiver voltage budget or absolute physical model. Finite-coil W_B/T preparation
is the next dependency.

The archive contains public source, results, logs and terminal records. Private
reservation material, binaries/wheels, disposable clones and original inherited
environment records are excluded. Process-start derivatives retain relevant fields
and the hashes of originals held locally. Every published ZIP member was compared
byte-for-byte after CRC verification; the index distinguishes these derivatives.

R03, both complete H12 paths and all29 formal cards remain not_run. H01-H15 remain
DEEPEYE-HUMAN-LOCK-20261014/revision1 with requirements SHA256
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.
