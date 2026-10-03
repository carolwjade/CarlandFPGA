param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("A", "B", "C")]
    [string]$Node,
    [Parameter(Mandatory = $true)]
    [string]$Config,
    [string]$Python,
    [string]$ReadyFile,
    [string]$WorkspaceFile
)

$ErrorActionPreference = "Stop"
$errorFile = Join-Path (Split-Path -Parent ([System.IO.Path]::GetFullPath($Config))) "runner-error.log"
trap {
    ($_ | Out-String) | Set-Content -LiteralPath $errorFile -Encoding utf8
    exit 1
}
$python = if ($Python) { $Python } else { $env:FPGA_MESH_PYTHON }
if (-not $python) {
    $python = (Get-Command python -ErrorAction Stop).Source
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python executable not found: $python"
}
& $python -c "import sys" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Python executable failed its startup check: $python"
}
$repo = if ($WorkspaceFile) {
    [System.IO.File]::ReadAllText($WorkspaceFile, [System.Text.Encoding]::UTF8).Trim()
} else {
    Split-Path -Parent $PSScriptRoot
}
if (-not (Test-Path -LiteralPath (Join-Path $repo "fpga_mesh") -PathType Container)) {
    throw "FPGA Mesh source package not found under workspace: $repo"
}
$argsList = @("-m", "fpga_mesh.cli", "serve", "--config", $Config)
if ($ReadyFile) {
    $argsList += @("--ready-file", $ReadyFile)
}
Push-Location -LiteralPath $repo
try {
    & $python @argsList
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
