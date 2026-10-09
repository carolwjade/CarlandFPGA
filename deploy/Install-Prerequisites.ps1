<# Idempotently install machine tools required by a teammate node where possible. #>
$ErrorActionPreference = 'Stop'

function Refresh-UserPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = ($machine, $user, $env:Path | Where-Object { $_ }) -join ';'
}

function Find-Tool([string]$Name, [string[]]$Candidates) {
    $found = Get-Command $Name -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            $env:Path += ';' + (Split-Path -Parent $candidate)
            return $candidate
        }
    }
    return ''
}

function Ensure-Package([string]$Tool, [string]$Package, [string[]]$Candidates) {
    if (Find-Tool $Tool $Candidates) { return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Warning "$Tool is missing and winget is unavailable. Install $Package through the official installer, then rerun onboarding."
        return
    }
    Write-Host "Installing $Package through winget..."
    try {
        & winget install --id $Package -e --source winget --accept-package-agreements --accept-source-agreements --silent
        if ($LASTEXITCODE -ne 0) { Write-Warning "winget could not install $Package; retry after any Windows approval." }
    } catch {
        Write-Warning "Could not install $Package automatically: $($_.Exception.Message)"
    }
    Refresh-UserPath
    if (-not (Find-Tool $Tool $Candidates)) {
        Write-Warning "$Tool is still unavailable. Complete installation or restart the shell, then rerun onboarding."
    }
}

$programFiles = $env:ProgramFiles
$localPrograms = Join-Path $env:LOCALAPPDATA 'Programs'
Ensure-Package git 'Git.Git' @(
    (Join-Path $programFiles 'Git\cmd\git.exe'),
    (Join-Path $localPrograms 'Git\cmd\git.exe'))
Ensure-Package gh 'GitHub.cli' @(
    (Join-Path $programFiles 'GitHub CLI\gh.exe'),
    (Join-Path $localPrograms 'GitHub CLI\gh.exe'))
Ensure-Package tailscale 'Tailscale.Tailscale' @(
    (Join-Path $programFiles 'Tailscale\tailscale.exe'))

$pythonReady = $false
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3 -c 'import sys; assert sys.version_info >= (3,12)' 2>$null
    $pythonReady = ($LASTEXITCODE -eq 0)
}
if (-not $pythonReady) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c 'import sys; assert sys.version_info >= (3,12)' 2>$null
        $pythonReady = ($LASTEXITCODE -eq 0)
    }
}
if (-not $pythonReady) {
    $bundled = Join-Path $HOME '.cache\codex-runtimes'
    $pythonReady = @(Get-ChildItem -Path (Join-Path $bundled '*\dependencies\python\python.exe') -File -ErrorAction SilentlyContinue).Count -gt 0
}
if (-not $pythonReady) {
    Ensure-Package py 'Python.Python.3.12' @(
        (Join-Path $localPrograms 'Python\Python312\python.exe'))
}
