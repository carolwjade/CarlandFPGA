# Original chain source pump

`OriginalChainSourcePump(session, functional_source, scanner)` requires the exact original chain-v2 Session, retained World/FunctionalSource, same QPC and owner thread, and the v2 OriginalSourceTraceScan created after source start. It does not start a source. `enable()` is explicit and single-use. On the owner thread, `poll_once(session)` calls the original poll once; a completed sample is admitted into the original scanner and released once. None means no sample. The return otherwise is the original admission.

`history` is a tuple of frozen records carrying strong references to payload, token, entry, draft and admission, with original receiver QPC and release status. `pending` preserves the in-flight pair and entry when available. Exceptions propagate and permanently fail the pump; effects are not retried. The unchanged source and scanner retain their own original histories.

The current scanner rejects further admission after its second prepare: this pump fails closed in that case until the scanner's separate admission lifecycle is explicitly changed. This control cannot guarantee source sampling rate, freshness, physical operation, or acceptance.
