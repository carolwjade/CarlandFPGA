# Windows launcher cleanup implementation plan

Goal: make the existing CPU fixture's actual acquisition and cleanup path obey
the accepted one-attempt coordinator contract, without changing sandbox policy.
Design: `docs/superpowers/specs/2026-10-19-isolation-launcher-cleanup-design.md`.

1. Record original HEAD, source and dependency hashes, ownership, canonical H01-H15
   hash, and the original controller lease. Preserve inherited dirty files.
2. Add failing pure/fake boundary tests for resource acquisition followed by
   persistence failure; early close failure; reused handle identity; job/process
   helper failure; terminal readback failure; profile absence unknown; final
   evidence failure. Do not launch an OS fixture during authoring.
3. Implement minimal registry/backend integration in `simulation/isolation/`
   and update the actual `prototype.py` call path. Keep the accepted pure
   coordinator unchanged unless the main assigns a separately justified repair.
4. Run coordinator/policy/new unit tests, preserve RED/GREEN output and exact
   source hashes, document residual limitations, then complete the author job.
5. Independently inspect exact source and add bounded adversarial checks. Resolve
   findings before native execution. Main then runs fresh normal/timeout/write
   failure OS fixtures with preserved receipts and independent terminal/profile
   readback. No re-use or deletion of historical attempts.
6. Commit only reviewed explicit files, publish relevant evidence to existing
   PR24, and continue dependency work. Do not change any formal card from
   `not_run` based solely on this CPU fixture.
