param(
  [Parameter(Mandatory=$true)][string]$Label,
  [Parameter(Mandatory=$true)][string]$Engine,
  [Parameter(Mandatory=$true)][string]$Project,
  [Parameter(Mandatory=$true)][string]$Script,
  [int]$TimeoutSeconds = 180,
  [switch]$VersionOnly
)
$ErrorActionPreference='Stop'
$review=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runRoot=Join-Path $review ('runs\' + $Label)
if (Test-Path -LiteralPath $runRoot) { throw "run directory already exists: $runRoot" }
New-Item -ItemType Directory -Path $runRoot | Out-Null
$envNames=@('APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME')
$envPaths=@{}
foreach($name in $envNames){
  $sub=$name.ToLowerInvariant().Replace('_','-')
  $p=Join-Path $review ("env\runs\$Label\$sub")
  New-Item -ItemType Directory -Path $p -Force | Out-Null
  $envPaths[$name]=$p
}
if($VersionOnly){
  $argv=@('--version')
}else{
  $argv=@('--headless','--path',$Project,'--script',$Script)
}
$stdout=Join-Path $runRoot 'stdout.log'
$stderr=Join-Path $runRoot 'stderr.log'
$record=[ordered]@{
  label=$Label; engine=$Engine; argv=$argv; project=$Project; script=$Script; version_only=[bool]$VersionOnly;
  timeout_seconds=$TimeoutSeconds; environment=$envPaths; started_utc=(Get-Date).ToUniversalTime().ToString('o')
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runRoot 'command.json') -Encoding utf8
$joined=($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$psi=New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName=$Engine
$psi.Arguments=$joined
$psi.UseShellExecute=$false
$psi.CreateNoWindow=$true
$psi.WindowStyle=[System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.RedirectStandardOutput=$true
$psi.RedirectStandardError=$true
foreach($name in $envNames){ $psi.EnvironmentVariables[$name]=[string]$envPaths[$name] }
$p=New-Object System.Diagnostics.Process
$p.StartInfo=$psi
$started=$p.Start()
$outStream=[System.IO.File]::Create($stdout)
$errStream=[System.IO.File]::Create($stderr)
try {
  $outTask=$p.StandardOutput.BaseStream.CopyToAsync($outStream)
  $errTask=$p.StandardError.BaseStream.CopyToAsync($errStream)
  $timedOut=$false
  if(-not $p.WaitForExit($TimeoutSeconds*1000)){
    $timedOut=$true
    try { $p.Kill() } catch {}
  }
  $p.WaitForExit()
  $null=$outTask.GetAwaiter().GetResult()
  $null=$errTask.GetAwaiter().GetResult()
} finally {
  $outStream.Dispose(); $errStream.Dispose()
}
$exitCode=$p.ExitCode
$processId=$p.Id
$p.Dispose()
$result=[ordered]@{
  label=$Label; timed_out=$timedOut; exit_code=$exitCode; pid=$processId;
  stdout_path=$stdout; stderr_path=$stderr; finished_utc=(Get-Date).ToUniversalTime().ToString('o');
  argv=$argv; environment=$envPaths; process_started=$started
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runRoot 'result.json') -Encoding utf8
Set-Content -LiteralPath (Join-Path $runRoot 'exit_code.txt') -Value $exitCode -Encoding ascii
Set-Content -LiteralPath (Join-Path $runRoot 'process_exited.txt') -Value $true -Encoding ascii
Write-Output ($result | ConvertTo-Json -Depth 6)
if($timedOut){ exit 124 }
exit ([int]$exitCode)

