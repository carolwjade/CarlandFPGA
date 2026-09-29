param(
    [string]$Python = $env:FPGA_MESH_PYTHON,
    [string]$Output = "artifacts/verification"
)

$ErrorActionPreference = "Stop"
if (-not $Python) {
    $Python = (Get-Command python -ErrorAction Stop).Source
}
$repo = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $repo $Output
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Push-Location $repo
try {
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }

    & $Python -m fpga_mesh.cli simulate `
        --root (Join-Path $outDir "sim-state") `
        --output (Join-Path $outDir "local_simulation.json")
    if ($LASTEXITCODE -ne 0) { throw "Local simulation failed" }

    if ($env:DEEPSEEK_API_KEY) {
        & $Python -m fpga_mesh.cli live-check-deepseek `
            --root (Join-Path $outDir "deepseek-home") `
            --output (Join-Path $outDir "deepseek_live_verification.json")
        if ($LASTEXITCODE -ne 0) { throw "DeepSeek live check failed" }
        & $Python -m fpga_mesh.cli balance-check-deepseek `
            --output (Join-Path $outDir "deepseek_balance_summary.json")
        if ($LASTEXITCODE -ne 0) { throw "DeepSeek balance check failed" }
    }
    else {
        Set-Content -LiteralPath (Join-Path $outDir "deepseek_live_verification.SKIPPED") `
            -Value "DEEPSEEK_API_KEY is not present"
    }
}
finally {
    Pop-Location
}
