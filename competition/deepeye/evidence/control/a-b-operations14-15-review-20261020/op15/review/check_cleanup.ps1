$ErrorActionPreference = 'Stop'
$evidenceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$commandFiles = Get-ChildItem -LiteralPath $evidenceRoot -Recurse -Filter record.json -File | Where-Object { $_.FullName -match '\\commands\\' }
$knownIds = @($commandFiles | ForEach-Object { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).pid })
$live = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -in $knownIds -or ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'b-op15-independent-20261020[\\/](review|mutants|same_tag_probe)\.py') })
$mappingLines = @(& subst)
$result = [ordered]@{ observed_at_utc = (Get-Date).ToUniversalTime().ToString('o'); known_command_records = $commandFiles.Count; known_pids_still_live = @($live | Select-Object ProcessId,ParentProcessId,Name,CommandLine); subst_lines = $mappingLines; accidental_unowned_temp_absent = -not (Test-Path -LiteralPath (Join-Path (Split-Path $evidenceRoot -Parent) 'recheck_unused.tmp')) }
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'cleanup-current.json') -Encoding utf8
$result | ConvertTo-Json -Depth 6
