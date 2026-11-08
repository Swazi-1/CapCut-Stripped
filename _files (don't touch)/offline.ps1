# CapCut Lite offline mode. Run elevated (offline-on.bat / offline-off.bat do that).
#   offline.ps1 -On   block outbound internet for every CapCut program (Windows Firewall)
#   offline.ps1 -Off  remove those rules
param([switch]$On, [switch]$Off)
$group = 'CapCut Lite offline'
Remove-NetFirewallRule -Group $group -ErrorAction SilentlyContinue
if ($Off) { Write-Host 'Offline mode OFF: CapCut can use the internet again.'; return }
$root = Join-Path $env:LOCALAPPDATA 'CapCut'
$exes = Get-ChildItem $root -Recurse -Filter *.exe -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike '*\_removed\*' }
foreach ($e in $exes) {
    New-NetFirewallRule -DisplayName "CapCut Lite block $($e.Name)" -Group $group -Direction Outbound -Action Block -Program $e.FullName -Profile Any | Out-Null
    Write-Host "blocked: $($e.FullName)"
}
Write-Host "Offline mode ON: $($exes.Count) CapCut programs blocked."
