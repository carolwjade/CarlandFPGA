# Historical RED wording correction

Independent finding R03-SOI-01 (P3) concerns the original author's interpretation,
not a demonstrated defect in the reviewed replacement.

The old `red-original-v3/source-snapshots/red_controls.py:15` asserted the combined
condition `refused and not committed`. Its failure establishes that the old
composition did not satisfy that combined refusal/no-commit assertion. The saved
result does not separately report the Boolean values or the resulting pose
revision; it therefore does not by itself prove a numeric commit occurred.

Read any stronger historical numeric-commit wording in the unmodified author
report subject to this correction. Raw source, original failures and report bytes
are preserved inside raw-evidence.zip and indexed by archive-index.json. Main did
not rerun the historical failure to support stronger wording.
