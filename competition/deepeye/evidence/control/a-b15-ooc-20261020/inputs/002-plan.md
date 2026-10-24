# A-side background synthesis of the B operation 15 candidate

Main authorization: the existing DeepEye implementation task and the human's
instruction to run software tests in the background. Sole A Desktop director:
01a13d7e-dcf1-7272-a738-a637dd62ff9d, generation 2.

Preserve DEEPEYE-HUMAN-LOCK-20261014/revision1 and all H01-H15. Canonical
requirements SHA256:
c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804.

Selected B source: df82af1bc91d01aeb9adee19f48c0890dfc1ac5b, PR30.
Copy exactly the three Git blobs for deepeye_atomic_pwm,
deepeye_pwm_coherent_capture and deepeye_pwm_applied_capture into this exclusive
evidence directory. Do not edit B's code or any existing worktree files.

Perform one Vivado 2026.1 batch out-of-context synthesis for
xc7z020clg400-1, top deepeye_pwm_applied_capture, original defaults
COUNT_W=32, WITNESS_W=64, TAG_W=32. Limit general.maxThreads to 1 and the
new process tree to below-normal priority, 4 GiB committed memory and 240 s.
Use the existing licensed batch launcher, without launching its GUI shortcut.
Fail closed on Tcl error, a missing output, unexpected top/part, black boxes,
or inferred latches. Preserve warnings and resource reports.

Use an ASCII temporary directory junction pointing to this repository-owned
directory because the repository's Windows short name still contains Chinese.
This is an alias, not a source/build copy outside the repository. Record and
verify its resolved target; never replace an existing alias.

Do not add a clock or pin constraint, change defaults, implement/place/route,
generate a bitstream, open hardware tools, touch the board, change services,
drivers, execution policy or user windows. Without a selected system clock,
there is no timing-frequency or interface acceptance claim.

Before acceptance, independently review exact inputs, hidden invocation,
logs, output and manifest. This adds candidate synthesis evidence only.
G05, B06, R03 and all 29 formal taskbook cards remain not_run.
