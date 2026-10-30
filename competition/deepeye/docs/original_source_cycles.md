# Original source scan cycles

`OriginalSourceTraceScan(functional_source, bundle)` retains its original single-attempt default. Trusted Root may select `source_scan_cycle_v2=True` only when constructing against the same freshly started original source, Book and QPC clock, before the first sample. One SourceLedger starts at the original origin and receives every original retained sample in order.

Each `admit(payload)` requires the exact original returned payload, completed Book token and bytes. The v2 `prepare(payload, facts=..., build_binding=...)` requires the latest admitted source slot, and after the first preparation the strictly newer latest original slot after every intermediate sample is admitted. It rechecks the full Book and retained history, stable original token/bytes, no active Book acquisition and original source count. Two preparation attempts are permitted; consumed attempts cannot be restored. A refused or unknown attempt retires the producer. Original input bytes and private companions are strongly retained for each attempt; they do not grant observation, authority or motion.

After two successful v2 preparations, original samples may continue to be admitted to the same ledger while the original source remains valid. A third preparation is refused and retires the producer; no count or ledger is reset.

The ledger's original zero-origin and quality/held-EM rules remain. At each v2 preparation the nominal ADC timestamp and any valid nominal EM timestamp must be no more than 100 ms old in the same observed QPC domain. These nominal grid checks are not proof of actual ADC/EM capture, native atomicity, physical board freshness or final acceptance. Original private companion data is not an AI prompt.
