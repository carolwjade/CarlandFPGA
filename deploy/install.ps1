param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("A", "B", "C")]
    [string]$Node,
    [string]$SourceConfig,
    [string]$DeepSeekKeyFile,
    [string]$InstallRoot
)

$ErrorActionPreference = "Stop"
if (-not $InstallRoot) {
    $InstallRoot = Join-Path (Split-Path -Parent $PSScriptRoot) ".local\deployment"
}
$root = [System.IO.Path]::GetFullPath($InstallRoot)
$nodeDir = Join-Path $root "node-$($Node.ToLower())"
$stateDir = Join-Path $nodeDir ".local\node-$($Node.ToLower())"
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
$installedLines = [System.IO.File]::ReadAllLines($configPath)
if (-not ($installedLines | Where-Object { $_ -match '^turn_timeout_seconds\s*=' })) {
    [System.IO.File]::WriteAllText(
        $configPath, ((@('turn_timeout_seconds = 3600') + $installedLines) -join "`n") + "`n",
        [System.Text.UTF8Encoding]::new($false)
    )
}
if ($DeepSeekKeyFile) {
    $keyPath = [System.IO.Path]::GetFullPath($DeepSeekKeyFile)
    if (-not (Test-Path -LiteralPath $keyPath -PathType Leaf)) {
        throw "DeepSeek key file does not exist: $keyPath"
    }
    $lines = [System.IO.File]::ReadAllLines($configPath)
    $replacement = 'deepseek_key_file = "' + $keyPath.Replace('\', '/') + '"'
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match '^deepseek_key_file\s*=') {
            $found = $true
            $replacement
        }
        else { $line }
    }
    if (-not $found) {
        throw "Installed config lacks deepseek_key_file; update its template first."
    }
    [System.IO.File]::WriteAllText(
        $configPath, (($updated -join "`n") + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Host "Installed node $Node"
Write-Host "Config: $configPath"
Write-Host "State:  $stateDir"
Write-Host "Set non-secret env references before starting; never place secrets in Git."
