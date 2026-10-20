# Read-only host preflight

From `competition/deepeye` in the product checkout:

```powershell
python -B tools/preflight.py
python -B tools/preflight.py --inventory-only
python -B tools/preflight.py --inventory-only --output C:/existing-evidence-folder/new-host-inventory.json
```

The default command emits JSON on stdout and exits **2** even after a complete
inventory. `--inventory-only` exits **0** only when all required host queries and
selected package metadata collection complete and validate. Missing distributions
are an observed `not_installed` state; damaged metadata is an error. Exit 0 means
inventory collection only. **R02 stays `not_run`; formal acceptance stays false.**
Physical board, calibration, ROCm project execution, NPU runtime and model benefit
remain `not_run`; device compatibility remains `unknown`. This command does not
update historical `hardware/environment.json`, acceptance cards or other evidence.

No files are written by default. `--output` exclusively creates one new file
containing the same JSON object in UTF-8 with LF newlines. Platform text stdout
may use different newlines, so the streams do not promise identical raw bytes.
The parent must already exist.
An existing file is refused before any collector runs. Failed observations may
therefore be retained as separate historical files. A disk/write failure reports
an error on stdout; a partially written file is not a valid receipt.

Before querying, the command checks the contract identity, revision, exact H01-H15
membership and actual requirements digest against the pinned
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
Canonical requirements use UTF-8, `ensure_ascii=False`, sorted keys and compact
comma/colon separators. The output includes actual contract and collector source
digests; a declared digest alone cannot pass the check.

The fixed collector is read once with a 1 MiB byte bound, strictly UTF-8 decoded,
and those same bytes are hashed. Its exact decoded text is the final `-Command`
argument of one system Windows PowerShell process. No script path is invoked or
dot-sourced; there is no user command input, policy option, policy/settings change,
or fallback/retry. The process performs local CIM reads with no profile, no
interaction, a hidden window and below-normal priority. It is limited
to 20 seconds, with no retry; timeout kills and waits for this owned process only.
Pipe captures are bounded to 1 MiB JSON and 64 KiB stderr. Failures preserve
available stdout/stderr diagnostics as UTF-8 replacement-decoded strings. These
strings may lose undecodable child bytes; saved raw CLI output cannot recover
the original child stream. Unsupported platforms exit 2.

Typed groups report CPU, OS, video controllers, candidate NPU PnP devices,
corresponding signed drivers and fixed local logical disks. Query errors remain
attached to their groups. Successful empty GPU/NPU/driver arrays mean no matching
rows in that query; they do not prove absence, compatibility or unsupported status.
The CIM `AdapterRAM` field can be limited by the driver/provider and is not a
validated physical VRAM measurement. NPU name tokens are whole words `NPU`,
`Neural`, `IPU`, or the observed AMD PCI prefix `VEN_1022&DEV_1502`.
`Input` alone never matches. These are candidate observations, not accelerator tests.

Package versions use only `importlib.metadata` in the current interpreter for
torch, onnxruntime, onnxruntime-directml, onnx, rocm, rocm-bootstrap, numpy,
setuptools and typing-extensions. The interpreter version, architecture and
executable identify this scope; other virtual environments are not scanned.
No target package is imported; no model, GPU enumeration API, board, network,
resolver, installation, service or driver change is performed. No user identity,
serial numbers, process listings or registry inventories are collected.

Deterministic boundary tests (no live CIM queries):

```powershell
python -B -m unittest discover -s competition/deepeye/tests -p test_preflight.py -v
```

Run the test command from the repository/product root. Host inventory alone cannot
establish eligibility, ROCm support, trained-model benefit or physical readiness.
