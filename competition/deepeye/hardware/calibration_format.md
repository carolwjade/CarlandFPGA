# R02 four-channel calibration records (schema 1)

Run from `competition/deepeye`:

```text
python integration/input_calibrate.py --levels 8
python integration/input_calibrate.py --levels 8 --input /path/to/records.json --output /path/to/new-report.json
```

No input returns `not_run` (exit 3). A complete offline calculation returns `computed` (exit 0); incomplete or unsafe-to-fit data returns `incomplete` (exit 3); malformed data or file errors return `invalid` (exit 2). These are **calculation statuses**, not physical calibration acceptance. Output defaults to stdout. An explicit output creates a new file only: existing records/reports are never overwritten. No device, model, network, service or UI is accessed. No default `hardware/calibration.json` is produced.

Input is UTF-8 JSON, maximum 4 MiB; duplicate keys, nonfinite numbers, unexpected fields and malformed identities are rejected. Fields are required unless their permitted value explicitly includes null. Input remains unchanged. The report binds its exact raw-byte SHA256; rejected records remain in that original file, with issue paths pointing to affected records. Keep the original input beside the report. It is the caller's responsibility to retain and authenticate the acquisition evidence; a hash does not prove measurement.

Oversized input is rejected after a bounded read; its `input_sha256` is null because the complete file was not read. A prefix hash is never presented as file identity. An output-write failure preserves the identity and diagnostic calculation of the input already read, reports `invalid` with `file_error`, and leaves an existing output untouched. A partial new output from an actual filesystem write failure is retained for inspection and is not a successful report.

| Root field | Meaning |
|---|---|
| schema | Integer 1 |
| source_mode | `sensor_live`, `twin_fixture`, or `software_fixture`; `geo_replay` is digital and cannot calibrate ADC inputs |
| operation_id | Nonempty acquisition operation identifier |
| request_hash | Full lowercase 64-digit SHA256 of the original request |
| tested_commit | Full lowercase 40-digit Git commit actually used during acquisition |
| captured_at_utc | ISO timestamp with an explicit UTC offset |
| channels | Exactly four records, unique `A0`, `A1`, `A2`, `A3` |

Provenance strings are declared, not authenticated by this tool. Fixtures use `software_fixture` and must never be presented as board measurements. Physical modes require reference_kind `independent_measurement`; merely programming a DAC setpoint is insufficient. Physically verify that voltage reference, raw acquisition, time, operating conditions and the claimed commit belong to the same operation before acceptance.

Each channel object contains exactly:

| Field | Meaning |
|---|---|
| channel_id | A0-A3 |
| signal_chain_id | Identifier for the measured wiring/configuration; retain its separate physical record |
| gain | Fixed numeric gain 1, 2, 4 or 8; only A0 has the documented PGA, other channels require 1 |
| nominal_adc_bits / container_bits | Explicit 12 / 16. Neither states ENOB. |
| packing | `right_aligned` (code=word, top 4 padding bits zero) or `left_aligned` (code=word>>4, bottom 4 bits zero). No packing is inferred. |
| range_v | `[low, high]` in volts at the documented analog **header** input, within 0-3.3 V; this is not permission to apply 3.3 V to a bare XADC input. Use actual confirmed safe bounds. |
| reference_instrument | Independent reference instrument/record identifier; fixture text for fixtures |
| levels | Up to 256 level records, at least `--levels` complete independent points required |

Each level contains exactly `level_id` (unique in its channel), `target_v` (planned level), `reference_kind`, `reference_v` (independent measured header voltage), `reference_uncertainty_v` (nonnegative measurement uncertainty), and `samples`. A target is a plan label, not the reference measurement. Physical acquisition should document the uncertainty basis separately. For fixtures, reference_kind is `software_fixture`; for physical modes it is `independent_measurement`.

Each sample contains exactly `sample_id` (unique throughout the dataset), `raw_word` (integer uint16), and `analog_saturation` (`false`, `true`, or `null` for unknown). These analog flags are declared observations, not inferred from the ADC code. Preserve the method/evidence for determining analog saturation in the acquisition record. There are 1-4096 samples per level. A reference uncertainty interval must remain inside the declared input range. Planned levels must be distinct; measured reference uncertainty intervals must not overlap. A 64-machine-epsilon separation guard addresses floating-point resolution only; it is not a new physical accuracy threshold.

Repetitions count once and are averaged within a level. Any ADC rail (code 0 or 4095), declared analog saturation, unknown analog state, out-of-range point or insufficient/ambiguous level set blocks fitting the entire affected channel. A rail is an ADC endpoint observation, not proof of analog amplifier saturation. No bad sample is silently removed. Other complete channels can have diagnostic fits while the whole report remains incomplete. Structural errors invalidate the whole input.

The least-squares model is `header_voltage = offset_v + volts_per_code * mean_code`, equally weighted per level. The report includes point means and residuals in volts, maximum absolute and RMS residual. Repeating one level cannot increase its weight or manufacture eight independent levels. Degenerate ADC spread and nonpositive slope cannot yield calibration coefficients. No fit-error acceptance limit is invented here. Do not combine different gain settings or wiring configurations into one channel fit; separate them into different operations.

`physical_verification`, `r02_acceptance`, and `r03_acceptance` remain `not_run` even with complete declared measurements. ENOB also remains `not_run`: DC offset/gain/linearity cannot measure ENOB. ENOB needs a separately selected method and actual dynamic/noise evidence. This tool does not accept an ENOB claim from metadata. Actual calibrated records and independently verified hardware evidence are still required for the taskbook `hardware/calibration.json` and R02 exit. H01-H15, the A-only board operator, the two H12 paths, and existing B/C ownership are unchanged.
