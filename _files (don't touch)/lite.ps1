# CapCut Lite: permanently delete the parts listed in lite-manifest.txt from CapCut (no backup; reinstall CapCut to get them back).
#   lite.ps1 -ApplyAll                              apply every line of lite-manifest.txt to the newest CapCut version
#   lite.ps1 -Apply -Items '{APP}\bun.exe',...      delete only these items
# {APP} = CapCut\Apps\<newest version>, {UD} = CapCut\User Data.
# "BLOCK <item>": delete the folder, then put an empty read-only FILE with the same name in its place,
# so CapCut cannot download or re-create that folder.
param([switch]$Apply, [switch]$ApplyAll, [string[]]$Items)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'CapCut'
$manifest = Join-Path $PSScriptRoot 'lite-manifest.txt'
$ver = Get-ChildItem (Join-Path $root 'Apps') -Directory | ? { $_.Name -match '^\d+(\.\d+)+$' } |
       sort { [version]$_.Name } -Descending | select -First 1
if (-not $ver) { throw "No CapCut version folder found in $root\Apps" }

function Resolve-Item([string]$item) {
    Join-Path $root ($item.Replace('{APP}', "Apps\$($ver.Name)").Replace('{UD}', 'User Data'))
}
function Remove-Part([string]$p) {
    if (-not $p.StartsWith("$root\", [StringComparison]::OrdinalIgnoreCase) -or $p.Contains('..')) { return "skip (outside CapCut): $p" }
    if (-not (Test-Path -LiteralPath $p)) { return "skip (missing): $p" }
    try { Remove-Item -LiteralPath $p -Recurse -Force; "deleted: $p" } catch { "could not delete (in use?): $p" }
}
function Test-Blocker([string]$p) { $f = Get-Item -LiteralPath $p -Force -EA SilentlyContinue; $f -and -not $f.PSIsContainer -and $f.Length -eq 0 -and ($f.Attributes -band [IO.FileAttributes]::ReadOnly) }

if ($ApplyAll) { $Items = Get-Content $manifest | ? { $_ -and -not $_.StartsWith('#') } }
if ($Apply -or $ApplyAll) {
    Get-Process | ? { $_.Path -like "$root\*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
    foreach ($i in $Items) {
        $block = $i.StartsWith('BLOCK ')
        $p = Resolve-Item ($i -replace '^BLOCK ', '')
        if ($block -and (Test-Blocker $p)) { "already blocked: $p"; continue }
        Remove-Part $p
        if ($block -and -not (Test-Path -LiteralPath $p)) { New-Item -ItemType File -Path $p -Force | Out-Null; (Get-Item -LiteralPath $p).Attributes = 'ReadOnly'; "blocked: $p" }
    }
    # Old backup folders from earlier CapCut Lite versions are not used any more.
    foreach ($old in '_removed') { $o = Join-Path $root $old; if (Test-Path -LiteralPath $o) { Remove-Item -LiteralPath $o -Recurse -Force -EA SilentlyContinue; "deleted old backup: $o" } }
}
