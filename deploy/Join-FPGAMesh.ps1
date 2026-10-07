<#
Join a public FPGA Mesh source repository and configure one local agent node.
Run from a teammate's Codex session. Human login and Feishu app approval remain
interactive; this script never embeds API keys in Git or the distribution ZIP.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('A', 'B', 'C')]
    [string]$Node,
    [string]$Repository = 'https://github.com/carolwjade/CarlandFPGA.git',
    [string]$Workspace = (Join-Path $HOME 'Documents\CarlandFPGA'),
    [string]$DeepSeekKeyFile = '',
    [string]$SharedSecretFile = '',
    [string]$GroupId = 'oc_e0de73230fd64dd2da3e52fc781dffb1',
    [string]$AstraAppId = '',
    [string]$AstraSecretFile = '',
    [string]$DeepSeekAppId = '',
    [string]$DeepSeekSecretFile = '',
    [string]$PeerA = '',
    [string]$PeerB = '',
    [string]$PeerC = '',
    [string]$BindHost = '',
    [switch]$RegisterApps,
    [switch]$SkipTailscale,
    [switch]$SkipAutostart,
    [switch]$SkipStart,
    [switch]$SetUpFork
)

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath($Workspace)
$parent = Split-Path -Parent $repoRoot
New-Item -ItemType Directory -Path $parent -Force | Out-Null
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required. Install Git for Windows, then rerun this command.'
}
if (-not (Test-Path -LiteralPath $repoRoot)) {
    & git clone --origin upstream $Repository $repoRoot
    if ($LASTEXITCODE -ne 0) { throw 'Git clone failed.' }
} else {
    $actual = (& git -C $repoRoot remote get-url upstream 2>$null)
    if ($LASTEXITCODE -ne 0) {
        $actual = (& git -C $repoRoot remote get-url origin 2>$null)
    }
    if ($LASTEXITCODE -ne 0 -or $actual.TrimEnd('/') -ne $Repository.TrimEnd('/')) {
        throw "Workspace is not the requested repository: $repoRoot"
    }
    $dirty = & git -C $repoRoot status --porcelain
    if (-not $dirty) {
        $remoteName = if ((& git -C $repoRoot remote) -contains 'upstream') { 'upstream' } else { 'origin' }
        & git -C $repoRoot pull --ff-only $remoteName main
        if ($LASTEXITCODE -ne 0) { throw 'Git fast-forward update failed.' }
    } else {
        Write-Warning 'Workspace has local edits; leaving them untouched and using the installed checkout.'
    }
}

$venvPython = Join-Path $repoRoot '.local\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv (Join-Path $repoRoot '.local\venv')
        $created = ($LASTEXITCODE -eq 0)
    }
    if (-not $created -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv (Join-Path $repoRoot '.local\venv')
        $created = ($LASTEXITCODE -eq 0)
    }
    if (-not $created -or -not (Test-Path -LiteralPath $venvPython)) {
        throw 'Python 3.12+ is required. Install it, then rerun this command.'
    }
}
& $venvPython -c 'import sys; assert sys.version_info >= (3,12)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
Push-Location -LiteralPath $repoRoot
try {
    & $venvPython -m pip install -e '.[feishu]'
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    $nodeRoot = Join-Path $repoRoot ('.local\deployment\node-' + $Node.ToLower())
    New-Item -ItemType Directory -Path $nodeRoot -Force | Out-Null
    $feishuRoot = Join-Path $nodeRoot 'feishu'
    if ($RegisterApps) {
        foreach ($role in @('astra', 'deepseek')) {
            $manifest = Join-Path $feishuRoot "$role.json"
            if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
                & $venvPython deploy/register-feishu-apps.py --node $Node --role $role --output-dir $feishuRoot
                if ($LASTEXITCODE -ne 0) { throw "Feishu $role registration failed or expired." }
            }
        }
    }
    $astraManifest = Join-Path $feishuRoot 'astra.json'
    $deepseekManifest = Join-Path $feishuRoot 'deepseek.json'
    if (-not $AstraAppId -and (Test-Path -LiteralPath $astraManifest)) {
        $saved = Get-Content -LiteralPath $astraManifest -Raw | ConvertFrom-Json
        $AstraAppId = $saved.app_id
        $AstraSecretFile = $saved.secret_file
    }
    if (-not $DeepSeekAppId -and (Test-Path -LiteralPath $deepseekManifest)) {
        $saved = Get-Content -LiteralPath $deepseekManifest -Raw | ConvertFrom-Json
        $DeepSeekAppId = $saved.app_id
        $DeepSeekSecretFile = $saved.secret_file
    }

    if (-not $SkipTailscale) {
        $tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
        if (-not $tailscale) {
            $candidate = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
            if (Test-Path -LiteralPath $candidate) { $tailscale = @{ Source = $candidate } }
        }
        if (-not $tailscale) {
            Write-Warning 'Tailscale is not installed; install it and log into the shared tailnet for direct B/C communication.'
        } elseif (-not $BindHost) {
            $tailIp = (& $tailscale.Source ip -4 2>$null | Select-Object -First 1)
            if ($LASTEXITCODE -eq 0 -and $tailIp -match '^100\.') { $BindHost = $tailIp }
        }
    }
    if (-not $BindHost) { $BindHost = '127.0.0.1' }

    $configPath = Join-Path $nodeRoot ("node-$($Node.ToLower()).toml")
    $arguments = @('--node', $Node, '--output', $configPath, '--bind-host', $BindHost)
    foreach ($entry in @(
        @('deepseek-key-file', $DeepSeekKeyFile),
        @('shared-secret-file', $SharedSecretFile),
        @('group-id', $GroupId),
        @('astra-app-id', $AstraAppId),
        @('astra-secret-file', $AstraSecretFile),
        @('deepseek-app-id', $DeepSeekAppId),
        @('deepseek-secret-file', $DeepSeekSecretFile),
        @('peer-a', $PeerA), @('peer-b', $PeerB), @('peer-c', $PeerC)
    )) {
        if ($entry[1]) { $arguments += @('--' + $entry[0], [string]$entry[1]) }
    }
    & $venvPython -m fpga_mesh.onboarding @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Node config generation failed.' }
    & $venvPython -m unittest discover -s tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Self-test failed; service was not started.' }

    if ($SetUpFork) {
        $gh = Get-Command gh -ErrorAction SilentlyContinue
        $ghReady = $false
        if ($gh) {
            & gh auth status *> $null
            $ghReady = ($LASTEXITCODE -eq 0)
        }
        if ($ghReady) {
            & gh repo fork carolwjade/CarlandFPGA --clone=false --remote=true
            if ($LASTEXITCODE -ne 0) {
                Write-Warning 'Fork setup failed; source checkout remains usable.'
            }
        } else {
            Write-Warning 'GitHub CLI login is needed to create your fork and submit pull requests.'
        }
    }
    $codex = Get-Command codex -ErrorAction SilentlyContinue
    $codexReady = $false
    if ($codex) {
        & codex login status *> $null
        $codexReady = ($LASTEXITCODE -eq 0)
    }
    if (-not $codexReady) { Write-Warning 'Log in to Codex with the local ChatGPT subscription.' }
    $keyReady = $DeepSeekKeyFile -and (Test-Path -LiteralPath $DeepSeekKeyFile -PathType Leaf)
    if (-not $keyReady) { Write-Warning 'Provide a local DeepSeek API key file before starting child agents.' }
    if (-not $SkipAutostart -and $codexReady -and $keyReady) {
        & pwsh -NoProfile -File deploy/register-autostart.ps1 -Node $Node -Config $configPath -Python $venvPython -StartNow:$(-not $SkipStart)
        if ($LASTEXITCODE -ne 0) { throw 'Scheduled task registration failed.' }
    } elseif (-not $SkipAutostart) {
        Write-Warning 'Autostart deferred until Codex login and the local DeepSeek key are ready.'
    }
    Write-Host "Workspace: $repoRoot"
    Write-Host "Local config: $configPath"
    Write-Host "Feishu enabled: $([bool]($GroupId -and $AstraAppId -and $AstraSecretFile))"
    Write-Host "Direct mesh enabled: $([bool]$SharedSecretFile)"
    Write-Host 'The public repository can be cloned by anyone; write access requires a fork and pull request or an explicit collaborator grant.'
} finally {
    Pop-Location
}
