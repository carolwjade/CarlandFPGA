param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^100\.(?:\d{1,3}\.){2}\d{1,3}$')]
    [string]$LocalAddress
)

$ErrorActionPreference = 'Stop'
$name = 'FPGA Mesh Tailscale 8787'
$adapter = Get-NetAdapter -Name 'Tailscale' -ErrorAction Stop
if ($adapter.Status -ne 'Up') { throw 'Tailscale adapter is not up.' }
$address = Get-NetIPAddress -InterfaceAlias 'Tailscale' -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -eq $LocalAddress }
if (-not $address) { throw 'LocalAddress is not assigned to Tailscale.' }
$existing = Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue
if ($existing) {
    $existing | Remove-NetFirewallRule
}
New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort 8787 -LocalAddress $LocalAddress `
    -RemoteAddress '100.64.0.0/10' -InterfaceAlias 'Tailscale' `
    -Profile Any | Out-Null
Get-NetFirewallRule -DisplayName $name |
    Select-Object DisplayName, Enabled, Action
