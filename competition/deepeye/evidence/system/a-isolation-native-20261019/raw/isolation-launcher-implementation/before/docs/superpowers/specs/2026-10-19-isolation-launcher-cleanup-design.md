# Owner-bound cleanup for the Windows CPU fixture

Task `DEEPEYE-IMPLEMENTATION-20261014/v1`; A Desktop director generation 2.
Contract `DEEPEYE-HUMAN-LOCK-20261014/revision1`, requirements SHA256
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
H01-H15 and all formal acceptance cards remain unchanged. This is the next
bounded G03 dependency under the human's existing autonomous implementation
authorization, not a new acceptance grant.

## Problem and chosen change

The accepted pure coordinator at `42e4786c` does not yet own a real backend.
The current `prototype.py` closes handles without checking results, releases
process handles even when termination is unconfirmed, and can interrupt cleanup
when failure/evidence writes raise. Its helpers can acquire a job or process
before the caller has a complete ownership record. Historical P1b evidence is
read-only and is not rewritten by this repair.

Integrate a small owner-bound registry and Windows backend with the existing
coordinator. Every successful acquisition is recorded in memory immediately,
before formatting, inspection, or persistence callbacks. References are exact
objects acquired by this launcher; process recovery never reopens a numeric PID.
Record successful early release and retain failed/unknown outcomes without
automatically issuing the same close again. A reused numeric handle is a new
acquisition only after the previous instance was confirmed closed.

The backend confirms terminal state by waiting on the original process handle.
It checks for an already terminal process before requesting termination. It
keeps process/thread/job recovery controls when termination is unconfirmed.
Profile deletion requires resolved dependent resources and a known path; a
successful deletion request and observed absence are separate evidence. Unknown
path/close/deletion results do not become success. Helper-owned temporary token,
SID, string, and attribute-list allocations must have explicit cleanup outcomes
or a documented bounded helper contract; no blanket all-resources claim.

The original error, cleanup errors, and evidence-write errors remain distinct.
The final in-memory result exists even if disk evidence fails. Such a run fails
evidence validation. Returning from a run with unresolved resources must preserve
the live ownership object for controlled reconciliation, not discard the only
recovery handles. No automatic retries, global resource searches or PID killing.

Keep existing zero-capability AppContainer policy, Win32k and child restrictions,
two-handle allowlist, Job limits, five-key environment, staged-runtime manifest,
and new-directory-only ACL rules. No services, credentials, board, shared Python
ACLs, or existing profile changes are in scope.

## Validation and sequencing

First reproduce acquisition/cleanup/persistence failures with pure/fake boundary
tests; implementation must pass the existing coordinator and policy tests plus
the new regressions. An independent source review checks exact candidate bytes
before the main runs three bounded native cases: normal, timeout, and evidence
write failure after process creation. Every attempt has a fresh dedicated run
directory and profile. Preserve original errors and all failed attempts.

Native results establish only the named CPU-fixture behavior on this host.
Four-process product isolation, GPU/UI compatibility, board, and G03 formal
acceptance remain `not_run` until their separate requirements are met.

Windows API references used for the design:
- https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess
- https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle
- https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile
