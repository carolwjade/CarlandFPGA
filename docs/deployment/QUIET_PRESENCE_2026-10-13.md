# Automatic presence announcements disabled

The 2026-10-13 human instruction prohibits unsolicited group announcements about
nodes going online/offline, recovering, reconnecting or changing probe status.
Internal health checks, durable peer delivery, task results and explicit human
status replies continue. This applies to A/B/C and their execution children.

The previous `NodeRuntime._note_peer_status` enqueued a new group report on every
observed transition. That path ran without a model call, so changing an agent's
instructions alone did not stop it. The method now only updates the internal
snapshot used by human queries.

## Existing busy services

Run the reviewed helper using the node's existing Python and actual state path:

```powershell
& <existing-python> <reviewed-checkout>/fpga_mesh/presence_policy.py --state-db <existing-state-dir>/state.sqlite
```

The helper requires an existing database. In one SQLite transaction it installs
`suppress_automatic_peer_presence_v1` and sets `cancelled_at` on matching pending
legacy announcements. The match includes the exact legacy ID shape, Astra role
and complete generated text. New legacy rows are retained as cancelled records.
Sent receipts and all other queues/reports are preserved. Reapplying is
idempotent. It starts no sender and does not restart the service or touch board
operations, configuration or credentials. A send already handed to the network
before the transaction cannot be recalled.

New runtime instances also install this fence to handle pre-update pending rows.
Install reviewed source through the normal idle-fenced update process when
appropriate; the live database fence does not require waiting for that restart.

## Evidence and scope

- Baseline test reproduced two unwanted reports from three presence observations.
- Updated regression keeps snapshot changes and observes zero automatic reports.
- A persistent legacy SQLite connection was tested before and after installation;
  new automatic reports were cancelled while human replies, board reports,
  existing sent receipts and nonmatching IDs/text were preserved.
- Relevant tests: 43 passed. Full repository suite: 315 passed on Windows.
- A live readback at 2026-10-13 07:07 UTC confirmed the trigger and zero pending
  automatic presence reports. The board owner had independently installed an
  A-only emergency guard at 07:05 UTC. At 07:15 UTC it verified the formal fence
  with a rolled-back live transaction and removed only its temporary guard;
  a manual board report sharing the ID prefix remained unaffected.
- First post-install evidence serialization failed on a SQLite Row. The installed
  transaction was inspected read-only afterward; it was not blindly replayed.
- B's private receipt at 07:09 UTC reports its live fence cancelled five newly
  generated announcements (sent=0, pending=0) and its installed B skill was
  updated. C's receipt at 07:11 UTC reports one pending announcement cancelled,
  pending=0, and its installed C skill updated. These are node-reported results,
  distinct from A's local readback and tests.
- C's subsequent [result](evidence/quiet-presence-c-20261013/result.json) records
  23 generated announcements cancelled and zero sent at 07:23 UTC, plus 13
  presence/runtime tests passing against `ba2725890179be264c261d315012f4acf8718732`.
  Its [installed skill rule](evidence/quiet-presence-c-20261013/installed-skill-rule.md)
  is included unchanged. C supplied these two files as a format-patch because
  its GitHub push timed out, reporting source commit
  `f9bad22d629e9b8c7c7ae6a6a25e3ff2757c8523`. A verified the decoded file sizes
  (720 and 1128 bytes), exact Git blob IDs and JSON identity before importing
  them. This verifies received artifact integrity, not independent access to
  C's live database; its unavailable YAML validator remains explicitly not run.
- A's installed PYNQ skill was updated and its rule read back. Repository host
  and client skill templates, main/child policy and operational instructions
  contain the same rule.
- This change contains no physical board measurements. Board execution remains
  with the existing A board-task owner under the original operation/commit IDs.
