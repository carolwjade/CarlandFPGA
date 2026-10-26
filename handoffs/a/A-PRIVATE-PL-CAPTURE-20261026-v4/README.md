# A actual private digital PL diagnostic

Operation A-PRIVATE-PL-CAPTURE-20261026-v4, request465fc5373ab574b1f9c737812e7330cf40b2086a8bcf2fd650ca58bfff867e6f.
Actual tested collector commit8b6e130c9d760ed9b4a935d8d5f6090203fa73b6,
SHA256723435f542b050405d8a6286a806a6561fbb613e6608ebf5f84407c7418407e6.
Later documentation/evidence commits do not change that source binding.

A downloaded the checked B bitstream once, established private4KiB MMIO,
triggered one scan and independently double-read all four raw lanes. Values
17,4095,32769,65280, original fixture QPCs and opaque qualities match.
Actual generation1/trigger1/tag97262253 and counters0,0,0→4,1,4 match four ACKs.
Final STOP returned status0 and active_tag0; original SSH and collector exited0.
All24 fresh snapshot disk hashes match selected inputs. The independent raw
review passed323 critical checks without rerunning the board.

board-evidence.zip contains exact original public RESULT, MMIO journal,
fixture, process/host receipts, snapshot readback and a scoped public summary.
manifest.json pins every archive member. A retains the full private original
request, marker, source/release/boot/runtime and review records locally.
The earlier MemoryError and exact-dict failures remain unchanged.

This is source4/software_fixture digital evidence. It does not establish ADC,
causal sensor-model validity, AI decisions, freshness,100ms, simulator motion,
fullH12 or final product acceptance. All H01-H15/revision1 are unchanged.
No old384 baseline, old software group or failed numerical solve was replayed.
