# Prepared independent review checkpoint — not final completion

Task DEEPEYE-IMPLEMENTATION-20261014/v1; work A-isolation-final-review-20261019-v1;
original job child-5877d2f4017b47a6ba9738620be73eb3; canonical reviewer
`/root/r03_review_20261018`. Original native validation returned
`execution_allowed=true`, status running. H01–H15 canonical hash independently
recomputed as `c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
The original job remains open; no native_complete has been called.

## IL-H1 — prepared native harness can abandon unresolved ownership on console I/O error

Frozen main harness SHA256
`d3990462ec2acf77b4b06212cad39eece16e3cb36efc82ea7ce6dcfa15cc8060`
was copied as `run_native.reviewed.py`, with the companion `plan.reviewed.md`.
The main's new `LIVE_OWNERS` capture before first acquisition and restoration of
pre-observation last-error before real CloseHandle were reviewed.

`hold_unresolved` prints its first status and then reads stdin without containing
I/O exceptions. Either `print` raising OSError/BrokenPipeError or `readline`
raising OSError exits before reaching the retention wait. Top-level handling
calls the same helper and can fail again, allowing interpreter exit despite
live unresolved ownership. Strong Python references alone do not survive exit.

`check_harness.py` independently exercises the actual frozen function with fake
owner, console and Event. A sentinel prevents a real blocking wait. Both
witnesses fail by assertion because no retention wait was reached:
**2 tests / 2 failures / exit 1**. Native main, opt-in, profile, process, ACL and
all Win32 functions were never called. Raw logs are `harness-check.*.log`.

Main was informed. Suggested bounded repair: diagnostic output/status-input
failure must not escape the owner-holding loop; unavailable I/O falls back to a
side-effect-free retaining wait. No retries, reopening, native recovery or
resource replay are needed. Main owns this harness and its repair.

## Other prepared checks

`test_observer_fake.py`: **5 passed / exit 0**, raw logs
`observer-fake.*.log`. Fake delegated functions confirm:

- Wait/Terminate/DeleteProfile return native results and preserve original errors.
- Close readback uses the same original held handle, never PID reopening;
  readback's error state is restored before actual CloseHandle, whose return/error
  is preserved afterward.
- The owner is retained before a first acquisition that raises; original exception
  identity survives. Successful process pair is returned without substitution.
- The actual nested observation wrapper (AST-extracted into fake globals, never
  executing main) retains owner and returned memory when observation save fails.

The named three fixtures and stale-receipt treatment were read in the **original
frozen** 12-file candidate, not in changing product files. Normal/timeout/injected
persistence cases distinguish expected product failure from fixture success.
The third fixture saves returned memory independently rather than relabelling
the earlier stale receipt. The harness keeps returned RunEvidence, uses fresh
exclusive attempt paths and original held-handle readback, and stops a failed
campaign. No execution gate exists in the inspected prepared directory.

Original IL-R1 and its two unchanged failing witnesses were read. They establish
lost second acquisition after first ambiguous registration, across CreatePipe
and process-pair ownership. No claim is made that the changing product repair
is frozen or fixed. Its source was not polled or tested.

## Pending on the same original job

1. Main supplies repaired frozen harness hash; rerun the same two hold witnesses
   against those exact bytes and retain original RED.
2. Main supplies actual repair-author terminal and new 12-file manifest.
3. Compare exact new 12 files against original frozen candidate, inspect IL-R1
   batch retention and unchanged recovery dependencies; run unchanged independent
   witnesses plus actual mocked CreateProcess helper and bounded offline suite
   with real native cases skipped and owned TEMP.
4. Write final findings/receipt, decide the named prepared-fixture source scope
   for main, then native_complete the original job. This is not native execution
   or game/G03/board/formal acceptance.

Only this review's evidence directory has been written. Motion remains frozen;
product, old reports, main harness and isolation source remain read-only. No
native opt-in environment, gate, source/index/service/board/ACL operation,
external transport or additional agent was created. All real native outcomes
and all formal taskbook cards remain `not_run`.
