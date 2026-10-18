"""Exercise registration with PowerShell cmdlets mocked; never modify a task."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SHELL = shutil.which("pwsh") or shutil.which("powershell")
ROOT = Path(__file__).resolve().parents[1]
WRAPPER = r"""
$ErrorActionPreference = 'Stop'
$global:capture = @{ lookups = 0; writes = 0; starts = 0; error = $null }
function Get-ScheduledTask {
    $global:capture.lookups += 1
    return $null
}
function New-ScheduledTaskAction {
    param($Execute, $Argument, $WorkingDirectory)
    return @{ Execute = $Execute; Arguments = $Argument; WorkingDirectory = $WorkingDirectory }
}
function New-ScheduledTaskTrigger { return @{ Mock = 'trigger' } }
function New-ScheduledTaskSettingsSet { return @{ Mock = 'settings' } }
function Register-ScheduledTask {
    param($TaskName, $Action, $Trigger, $Settings, $Description)
    $global:capture.writes += 1
    $global:capture.task = $TaskName
    $global:capture.action = $Action
}
function Set-ScheduledTask { throw 'Unexpected existing-task mutation' }
function Stop-ScheduledTask { throw 'Unexpected resident stop' }
function Start-ScheduledTask { $global:capture.starts += 1 }
try {
    & $env:FPGA_TEST_SCRIPT -Node A -Config $env:FPGA_TEST_CONFIG -Python $env:FPGA_TEST_PYTHON -StartNow
} catch {
    $global:capture.error = $_.Exception.Message
}
$global:capture | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $env:FPGA_TEST_CAPTURE -Encoding UTF8
if ($global:capture.error) { exit 1 }
"""


@unittest.skipUnless(os.name == "nt" and SHELL, "Windows PowerShell registration")
class AutostartRegistrationTests(unittest.TestCase):
    def run_registration(self, *, windowless):
        with tempfile.TemporaryDirectory(prefix="fpga-registration-") as folder:
            root = Path(folder)
            # Empty executable fixtures are never launched: existing-task lookup
            # is mocked to return none and every scheduler mutation is mocked.
            python = root / "python.exe"
            python.write_bytes(b"fixture only")
            pythonw = root / "pythonw.exe"
            if windowless:
                pythonw.write_bytes(b"fixture only")
            config = root / "node config.toml"
            config.write_text("# preserved fixture\n", encoding="utf-8")
            wrapper = root / "mock-registration.ps1"
            wrapper.write_text(WRAPPER, encoding="utf-8-sig")
            capture = root / "capture.json"
            env = dict(os.environ, FPGA_TEST_SCRIPT=str(ROOT / "deploy/register-autostart.ps1"),
                       FPGA_TEST_CONFIG=str(config), FPGA_TEST_PYTHON=str(python),
                       FPGA_TEST_CAPTURE=str(capture))
            result = subprocess.run([SHELL, "-NoProfile", "-NonInteractive", "-File", str(wrapper)],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertTrue(capture.exists(), result.stdout + result.stderr)
            record = json.loads(capture.read_text(encoding="utf-8-sig"))
            self.assertEqual(config.read_text(encoding="utf-8"), "# preserved fixture\n")
            return result, record, pythonw, config

    def test_resident_action_uses_same_environment_windowless_python(self):
        result, record, pythonw, config = self.run_registration(windowless=True)
        self.assertEqual(result.returncode, 0, record)
        self.assertEqual(record["action"]["Execute"], str(pythonw))
        self.assertEqual(record["action"]["WorkingDirectory"], str(ROOT))
        self.assertEqual(record["action"]["Arguments"],
                         f'-m fpga_mesh.supervisor --config "{config}" '
                         f'--ready-file "{config.parent / "ready.json"}" '
                         f'--log-file "{config.parent / "service.log"}"')
        self.assertEqual((record["task"], record["writes"], record["starts"]),
                         ("FPGA-Mesh-Node-A", 1, 1))

    def test_missing_windowless_interpreter_fails_before_scheduler_access(self):
        result, record, _, _ = self.run_registration(windowless=False)
        self.assertNotEqual(result.returncode, 0, record)
        self.assertIn("pythonw.exe", record["error"])
        self.assertEqual((record["lookups"], record["writes"], record["starts"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
