$ErrorActionPreference = 'Stop'
$taskOwn = $PSScriptRoot
$taskOut = Join-Path $taskOwn 'cleanup-current.json'
if (Test-Path -LiteralPath $taskOut) { throw 'Refusing to overwrite cleanup observation' }
$taskStarted = [DateTime]::UtcNow.ToString('o')
$taskProcs = @(Get-CimInstance Win32_Process)
$taskSim = @($taskProcs | Where-Object { $_.Name -match '^(vsim|vsimk|vlog|vlib|vish|vopt)\.exe$' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine)
$taskOwned = @($taskProcs | Where-Object { $_.Name -match '^(python|pythonw)\.exe$' -and $_.CommandLine -and $_.CommandLine -match 'b-pr30-followup-20261020|5345bee33b45490bbc0c070bd3473a41' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine)
$taskSubst = @(& 'C:/Windows/System32/subst.exe')
$taskSubstExit = $LASTEXITCODE
$taskR = @($taskSubst | Where-Object { $_ -match '^R:' })
$taskRecord = [ordered]@{
    observed_at_utc = $taskStarted
    queries = @('Get-CimInstance Win32_Process filtered for ModelSim binaries', 'Get-CimInstance Win32_Process filtered for original-review Python command lines', 'C:/Windows/System32/subst.exe (read only)')
    all_modelsim_processes = $taskSim
    original_review_python_processes = $taskOwned
    subst_exit_code = $taskSubstExit
    subst_stdout_lines = $taskSubst
    r_drive_mapping_lines = $taskR
    cleanup_observed = ($taskSim.Count -eq 0 -and $taskOwned.Count -eq 0 -and $taskSubstExit -eq 0 -and $taskR.Count -eq 0)
    mutations_performed = @()
    limitation = 'Current process and mapping snapshot; historical stop time is not inferred. Original job terminal failure is independently preserved.'
}
$taskJson = $taskRecord | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($taskOut, $taskJson + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
$taskJson
if (-not $taskRecord.cleanup_observed) { exit 1 }
