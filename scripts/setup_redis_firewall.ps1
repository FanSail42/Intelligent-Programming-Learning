#Requires -RunAsAdministrator
<#
  Allow local Redis (D:\develop\Redis-x64-3.2.100) through Windows Firewall.
  Right-click -> Run with PowerShell (as Administrator)
#>

$ErrorActionPreference = "Stop"
$redisExe = "D:\develop\Redis-x64-3.2.100\redis-server.exe"

if (-not (Test-Path $redisExe)) {
    Write-Error "Redis not found: $redisExe"
}

$ruleNames = @(
    "Huibian Redis Server (Program)",
    "Huibian Redis Port 6379"
)

foreach ($name in $ruleNames) {
    Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue
}

New-NetFirewallRule `
    -DisplayName "Huibian Redis Server (Program)" `
    -Direction Inbound `
    -Action Allow `
    -Program $redisExe `
    -Profile Domain, Private, Public `
    -Enabled True `
    -Description "Allow Redis server executable for Huibian project"

New-NetFirewallRule `
    -DisplayName "Huibian Redis Port 6379" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 6379 `
    -Profile Domain, Private, Public `
    -Enabled True `
    -Description "Allow Redis default port for Huibian project"

Write-Host ""
Write-Host "Firewall rules added:" -ForegroundColor Green
Get-NetFirewallRule -DisplayName "Huibian Redis*" |
    Format-Table DisplayName, Enabled, Direction, Action -AutoSize

Write-Host "Testing Redis..." -ForegroundColor Cyan
$cli = "D:\develop\Redis-x64-3.2.100\redis-cli.exe"
if (Test-Path $cli) {
    & $cli -a lifan ping 2>$null
}

Write-Host ""
Write-Host "Done. Restart backend if it was running." -ForegroundColor Green
Read-Host "Press Enter to close"
