# A independent review of B operation16

Target `f7736ac737d1c7b256974beb1574b94096819270`, source parent
`45fe6cd9c19d6056bf1867cc4255ac6a47ddddd5`, operation
`B-DEEPEYE-PWM-RUNNER-QUALIFICATION-20261020-16`.
Main verified all 450 independent review artifacts and exact completed job result.

The two original A negative fixtures are repaired; 23 unit tests and 23 portable
tests pass. All 211 handoff artifacts, 4,732 preserved old files and archived
source logs were checked. Reclassification reproduces 33 saved scenarios and
208,667 reported positive samples; no new simulator/RTL run occurred.

Two existing P2 gaps still block full runner qualification:
1. Invalid-width guard classification accepts substring diagnostics and an
   additional unrelated Fatal line.
2. Ordinary positive groups accept a CODE7_OBSERVED probe record that belongs
   only to group30.

Three malformed fixture inputs plus two healthy controls and exact candidate/
baseline/test/TB snapshots are included. `archive-manifest.json` maps short
byte-identical archive names to original review paths; locate `findings.md`,
`counterexamples.json` and `counterexamples/...` through that map. Original
nonzero reviewer harness logs are retained. These are parser counterexamples,
not observed RTL failures or demonstrated regressions.

This public archive retains 427 selected review files: reports, scripts, logs,
counterexamples, source snapshots and historical fixture copies. The exact
omitted paths are listed in `archive-manifest.json`; private lease contents
are absent. The complete 450-file identity manifest remains included.
An omitted file is not claimed to be physically in this archive.
Context-dependent scripts may require the original exact-source fixtures.

H01-H15 unchanged. G05/B06/R03/all29/board/system remain not_run. The three B15
RTL blob identities are unchanged at B16, but that identity fact is not a new
synthesis run. Existing source defects are returned to B under original ownership.
