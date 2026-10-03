param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("A", "B", "C")]
    [string]$Node,
    [Parameter(Mandatory = $true)]
    [string]$Config,
    [Parameter(Mandatory = $true)]
    [string]$Python,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot "run-node.ps1"
$configPath = [System.IO.Path]::GetFullPath($Config)
$pythonPath = [System.IO.Path]::GetFullPath($Python)
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Node config not found: $configPath"
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Python executable not found: $pythonPath"
}
$taskName = "FPGA-Mesh-Node-$Node"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and $existing.Description -notlike "FPGA Mesh $Node controller*") {
    throw "Scheduled task exists and is not owned by FPGA Mesh: $taskName"
}
$shell = (Get-Command pwsh -ErrorAction Stop).Source
$nodeDir = Split-Path -Parent $configPath
$installedRunner = Join-Path $nodeDir "run-node.ps1"
$workspaceFile = Join-Path $nodeDir "workspace.txt"
$readyFile = Join-Path $nodeDir "ready.json"
Copy-Item -LiteralPath $runner -Destination $installedRunner -Force
[System.IO.File]::WriteAllText($workspaceFile, "$repo`n", [System.Text.UTF8Encoding]::new($false))
$arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -Node {1} -Config "{2}" -Python "{3}" -ReadyFile "{4}" -WorkspaceFile "{5}"' -f `
    $installedRunner, $Node, $configPath, $pythonPath, $readyFile, $workspaceFile
$action = New-ScheduledTaskAction -Execute $shell -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew
if ($existing) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Set-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings | Out-Null
} else {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Description "FPGA Mesh $Node controller; event-driven idle" | Out-Null
}
if ($StartNow) {
    Start-ScheduledTask -TaskName $taskName
}
Write-Host "Registered $taskName"
Write-Host "Ready file: $readyFile"
