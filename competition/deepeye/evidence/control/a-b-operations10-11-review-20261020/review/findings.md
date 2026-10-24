# A independent review: B operations 10 and 11

Task `DEEPEYE-IMPLEMENTATION-20261014` / version `1`; work
`A-B-OPERATIONS10-11-REVIEW-20261020-v1`. Reviewer role is A under the
`fpga-multi-node` skill; sole director is Desktop
`01a13d7e-dcf1-7272-a738-a637dd62ff9d`, generation `2`.

## Conclusion

- Operation 10 passes this bounded, independent, offline Python review on the
  exact pinned downloaded source. The corrected model, the 70 formal tests, the
  12 main bus methods, and the 4 adversarial methods all complete successfully.
- Operation 11 passes only descriptor/fixture arithmetic on the exact pinned
  candidate: 51 accessible words, three equal 64-byte channel slices, 15 logical
  u64 values, 14 synthetic checks, and 10 invalid-descriptor checks.
- No blocking defect or minimal counterexample was found in this bounded scope.
- Operation 11 remains an unpublished-to-runtime candidate. This review grants
  no register/RTL/extension approval and does not change the PUBLIC ABI freeze.
- All 29 formal product cards, `B01`, `B05`, `R03`, RTL simulation/synthesis,
  timing, CDC/RDC, board, deployment, runtime, and system acceptance remain
  `not_run`.

## Input identity and provenance

- Remote draft PR #30 head: `cd48ae70082e33c7a669a6686a0c965f8e541757`.
- GitHub tarball identity: 30,806,609 bytes, SHA-256
  `3e4d738a0ea65e44188c7cb01aaa2e6744be6d9faba9559c2492935e41c28d8e`.
- Four-commit ancestry is recorded in `../lineage-and-blobs.json`; the selected
  downloaded bytes are recorded in `../archive-integrity.json`.
- Operation 10: source `de4e8bdd61e0126988b42c36b9e4e89cabbc3223`, request
  `2a120a721d5fcd29dba0c5b0ff308b2edd6bfff5bfb8a4c3108d5a6233d10174`,
  manifest `f0c8acd38e3b5c5c6aa90a8aab91a26f09ec6010ca9d4462569e47e5f38dd6bf`,
  with 75 manifest artifact entries.
- Operation 11: source `9d8437151359eabec66342985506f13d98ce7b5a`, request
  `b8cf87f58739730a601f72625945246cd5f898f7911274f7bf8d5345c1a0f9e9`,
  manifest `530e993409b55b3a774f0ab62b5bec01a02b9383a03350c8bd927688bfea1b92`,
  with 9 manifest artifact entries.
- Both request hashes independently recompute from their `input.json` using
  canonical UTF-8 JSON. All 99 selected archive entries rehash to their declared
  sizes and SHA-256 values; all 75 operation-10 and 9 operation-11 manifest bytes
  rehash exactly.
- The tested tree is the downloaded `../source/` reference tree. It is not the
  PRODUCT tree and not root `fpga` source.

## Operation 10 review

Inspected before execution: `register_transaction_reference.py`,
`REGISTER_TRANSACTION_REFERENCE.md`, the portable commands in `README.md`,
`test_register_transaction.py`, `main_review.py`, `main_adversarial.py`, and
`MAIN_SPEC.md`.

The model review covered the requested software-only invariants:

- Bus mutation is gated by address/access/type validation; a known writable word
  with zero strobe is a no-op, while NO ACCESS rejects even zero strobe.
- STOP byte-zero side effects precede reserved-bit rejection, without turning
  the rejected command into a success.
- Shadow byte-strobe writes merge and validate the complete word before atomic
  commit; rejected writes leave the previous shadow word intact.
- CONFIG apply captures an immutable payload only after all shadow initialization
  predicates hold; duplicate/conflicting/replayed/epoch-boundary cases remain
  distinct, and successful publication occurs once at a matching boundary.
- Context, BOOT, STOP, fault, CDC eligibility loss, capture-cycle start and reset
  discard or revoke the applicable pending CONFIG, tickets, publication and latch
  coherence according to their specified transitions.
- Capture tickets are opaque, model/context/generation/batch bound and one-shot.
  Values and sequence gates are validated before mutation, including post-Mapping
  revalidation, so a detached/callback result cannot republish revoked state.
- LATCH reads are coherent and detached; eligible provenance requires publication
  and CDC eligibility. Reset clears state while preserving anti-replay/generation
  and bounded high-water information.
- Accessible/snapshot counts, status bits, caller-visible aliases and returned
  object detachment are exercised. These are fixture semantics, not evidence of
  RTL, CDC or hardware behavior.

Independent runs were made once after source inspection, with current venv Python
`8da03db46eee55bac083e84362a6d75bf2c53ed12848b7400757b5fe53a432f2`, `-B -X utf8`,
`PYTHONDONTWRITEBYTECODE=1`, and an evidence-only TEMP below `review/`.

| Run | Exit | Actual result | stdout bytes / SHA-256 | stderr bytes / SHA-256 |
| --- | ---: | --- | --- | --- |
| Formal 70 | 0 | `Ran 70 tests`; `OK` | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 9,826 / `dbcdd6fa93cc601437fd122c2a49e3bdae42fec7c0bc0baa5f02d5325f9b7c5d` |
| Main bus 12 | 0 | 12 tests, 0 failures, 0 errors | 415 / `85614c46c885242588bd8871137441a308449945ed69bf89d0a790ed53a19669` | 1,162 / `b9a7963522f600452d5fefae52d29e711ae40df9e5bfea8787b2083adcc07d0f` |
| Adversarial 4 | 0 | 4 tests, 0 failures, 0 errors | 85 / `3994ec5263abb975646c8b729d4b05a4a7c4d5cec1e681b018806b42ff37c44e` | 601 / `77f9e9c37f23edab3acb07e121b6d213760954b8e608d957f9dd3d0c080e040b` |

The main run reports 1,104 command-strobe cases, 3,000 shadow-reference cases,
128 randomized capture projections, 136 reader-revocation interleavings, 34
invalid captures, and 283 expected rejections. Exact commands and raw byte logs
are under `runs/formal70/`, `runs/main12/`, and `runs/adversarial4/`.

The import probe resolved the model to
`source/competition/deepeye/golden/control/register_transaction_reference.py`
with SHA-256 `d2fad9f6ff4602e896e60d6c30050d4c1f65d07be82dc96965d9f274e0305718`,
and the formal test module to the downloaded
`source/competition/deepeye/tests/control/test_register_transaction.py`.
Probe stdout SHA-256 is
`a767605aca8883516fdd61c2d1d653bece8f771fd894b0906deb821a56a6abf0`.

## Operation 11 review

Inspected before execution: `raw_capture_diagnostic_candidate.json`,
`RAW_CAPTURE_DIAGNOSTIC_CANDIDATE.md`, the evidence README, and
`diagnostic_review.py`.

The candidate is internally consistent in its declared fixture arithmetic:

- A separate 256-byte candidate aperture is requested; no absolute base or HWH
  instance name is invented (`hwh_instance_name` and `physical_base_address` are
  null), and old-overlay probing is explicitly prohibited.
- There are 51 accessible 32-bit rows: 15 common rows and 12 in each of yaw,
  pitch and speed. Each channel owns an equal 64-byte slice. Thirty channel rows
  form the 15 logical u64 low/high pairs.
- The 13 no-access words are consistent: global `0x02c` plus four holes in each
  equal channel slice. `0x02c` is treated as a hole, not as an old-register or
  overlay dependency. There are 48 latched-read rows and three image-read rows.
- The candidate declares candidate-only status, A approval required, AI ingress
  disabled, non-modular counter comparison, overflow rejection/revocation before
  reuse, common latch/provenance, and no reset-valid semantic reuse.
- The descriptor describes a proposal for a new matched HWH aperture, but no HWH
  file was supplied or parsed. Actual HWH matching, register implementation,
  three-channel acquisition, overflow behavior, revocation behavior, coherence
  and runtime exposure are therefore not demonstrated here.

Independent run: exit `0`; stdout 531 bytes / SHA-256
`ebe274ca7320fbb7155667025a492116ff3b160c5c5f216415de96d2940affbc`;
stderr empty / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
The output records 51 accessible words, 3 channels, 15 wide fields, 14 synthetic
cases, and the 10 named invalid descriptors. Raw command/logs are in
`runs/diagnostic14-10/`.

One non-blocking checker-coverage limitation is noted: the checker validates the
top-level `image_values.bank_size_bytes` but does not independently revalidate
every duplicated informational image-size value. The current descriptor values
are consistent, so this is not a demonstrated design defect. No unrelated test
was added or expanded.

## Historical evidence separation

- The preserved original worker source
  `b5e4ee6cdbde370a5b837b6f16b7c4d9962f4a0899092f4d267609baa887ac1a`
  has a historical 70-pass record. It is not the corrected source tested above.
- The preserved WIP main observation remains a negative control with 9 failures
  and 1 error; its `result.json` and 8,833-byte stderr are unchanged.
- The preserved corrected-worker regression remains 2 failures (11,121-byte
  stderr); it is not relabeled as a pass.
- The copied `main/A-review/` belongs to operations 08/09 at head
  `433db2a82854a669778eb8c3cd35c309623a087e`, not to operations 10/11. It is
  reference material, not a current independent A review. The current A result
  is the execution recorded in this directory.

## Pins and write boundary

`pins-before.json` (SHA-256
`b970e06a85cb93181fd4723520d2e49b5780efee2d3af1cdd3726b96e418d0f0`) and
`pins-after.json` (SHA-256
`733e1175fc5817a65460ccb20841ddc200916b0bcd0eecaeba72934e2b13f474`) cover 18
source/evidence/pin files. All 18 match before and after. No downloaded source,
original evidence, product file, or root `fpga` source was modified. Writes are
limited to this `review/` directory.

No code fix, PR comment, Git commit/push, group/peer send, board/Run/RTL
simulation, synthesis/implementation, deployment, driver/service, credential, or
dependency-install operation was performed.
