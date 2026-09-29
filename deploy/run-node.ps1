param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("A", "B", "C")]
    [string]$Node,
    [Parameter(Mandatory = $true)]
    [string]$Config,
    [string]$ReadyFile
)

$ErrorActionPreference = "Stop"
$python = $env:FPGA_MESH_PYTHON
if (-not $python) {
    $python = (Get-Command python -ErrorAction Stop).Source
}
$repo = Split-Path -Parent $PSScriptRoot
$argsList = @("-m", "fpga_mesh.cli", "serve", "--config", $Config)
if ($ReadyFile) {
    $argsList += @("--ready-file", $ReadyFile)
}
Push-Location $repo
try {
    & $python @argsList
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
