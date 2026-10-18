# Preserve the windowless resident entrypoint

`deploy/register-autostart.ps1` now selects `pythonw.exe` beside the supplied
Python interpreter for the scheduled supervisor action. The original interpreter
still runs the synchronous `service --wait-stopped` check. A missing windowless
sibling fails before querying or changing a scheduled task. Task identity,
arguments, working directory, settings and the existing stop fence are unchanged.

The previous registration script selected `python.exe`, so re-registration could
undo the windowless recovery recorded on October 15. On October 18 the original
task was again found stopped with result `0xC000013A`. The source of that console
control termination is unknown. This change removes the console entrypoint; it
does not establish the origin of the signal or guarantee survival of all process,
host or platform failures.

Two real PowerShell executions with every scheduler cmdlet mocked first failed
against the original script and then passed after the repair. They verify the
windowless action, original quoted arguments and working directory, and rejection
before scheduler access when `pythonw.exe` is missing. No task or service is
modified by these tests. The same-environment Python 3.12.14 console/windowless
interpreters were separately checked for runtime import and service log redirect.

The live recovery changed only the existing `FPGA-Mesh-Node-A` action command
from its venv's `python.exe` to that venv's `pythonw.exe`, after the original
resident had stopped. The authenticated original control endpoint then processed
the B peer receipt and its completion on the existing Desktop main generation 2.
The semantic task-XML comparison shows only that command change. Live recovery
does not prove Feishu API 21001 recovery, peer software upgrades, product runtime
acceptance or physical-board behavior. Hardware remains disabled.

Do not invoke registration merely to validate this source repair while work is
active: the existing registration path stops an existing resident. Apply source
updates through the existing update workflow and preserve local state. Private
task XML, process observations and original failures remain in the October 18
communication-recovery evidence; no credentials or private leases are published.
