param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("A", "B", "C")]
    [string]$Node,
    [string]$SourceConfig,
    [string]$InstallRoot = "$env:LOCALAPPDATA\FPGA-Mesh"
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($InstallRoot)
$nodeDir = Join-Path $root "node-$($Node.ToLower())"
$stateDir = Join-Path $nodeDir "state"
$configPath = Join-Path $nodeDir "node-$($Node.ToLower()).toml"

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
if (-not $SourceConfig) {
    $SourceConfig = Join-Path $PSScriptRoot "configs\node-$($Node.ToLower()).toml"
}
if (-not (Test-Path -LiteralPath $SourceConfig)) {
    throw "Config not found: $SourceConfig"
}
if (-not (Test-Path -LiteralPath $configPath)) {
    Copy-Item -LiteralPath $SourceConfig -Destination $configPath
}

Write-Host "Installed node $Node"
Write-Host "Config: $configPath"
Write-Host "State:  $stateDir"
Write-Host "Set non-secret env references before starting; never place secrets in Git."
