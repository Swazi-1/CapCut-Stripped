# CapCut Lite: move parts out of CapCut into CapCut\_removed (same relative paths), or put them back.
#   lite.ps1 -Apply  -Items '{APP}\bun.exe','{UD}\Cache\effect'   move these items out now
#   lite.ps1 -Undo   -Items '{APP}\bun.exe'                       move these items back
#   lite.ps1 -ApplyAll   apply every line of lite-manifest.txt to the newest CapCut version (used by relite.bat)
#   lite.ps1 -RestoreAll put everything in _removed back (used by restore.bat)
# {APP} = CapCut\Apps\<newest version>, {UD} = CapCut\User Data. Nothing is ever deleted.
param([switch]$Apply, [switch]$Undo, [switch]$ApplyAll, [switch]$RestoreAll, [string[]]$Items)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'CapCut'
$removed = Join-Path $root '_removed'
$manifest = Join-Path $PSScriptRoot 'lite-manifest.txt'
$ver = Get-ChildItem (Join-Path $root 'Apps') -Directory | ? { $_.Name -match '^\d+(\.\d+)+$' } |
       sort { [version]$_.Name } -Descending | select -First 1
if (-not $ver) { throw "No CapCut version folder found in $root\Apps" }

function Resolve-Item([string]$item) {
    $rel = $item.Replace('{APP}', "Apps\$($ver.Name)").Replace('{UD}', 'User Data')
    [pscustomobject]@{ Rel = $rel; Live = Join-Path $root $rel; Parked = Join-Path $removed $rel }
}
function Move-Safe([string]$from, [string]$to) {
    if (-not (Test-Path -LiteralPath $from)) { return "skip (missing): $from" }
    if ((Test-Path -LiteralPath $to -PathType Container) -and -not (Get-ChildItem -LiteralPath $to -Recurse -File -Force -EA SilentlyContinue)) {
        Remove-Item -LiteralPath $to -Recurse -Force   # only empty folders left behind by an earlier restore
    }
    if (Test-Path -LiteralPath $to) {
        # Already parked once (e.g. regrown cache): park the new copy beside it with a timestamp.
        $to = "$to.$(Get-Date -Format yyyyMMdd-HHmmss)"
    }
    New-Item -ItemType Directory -Force (Split-Path $to) | Out-Null
    Move-Item -LiteralPath $from -Destination $to
    "moved: $from -> $to"
}
function Stop-CapCut {
    Get-Process | ? { $_.Path -like "$root\*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

# "BLOCK <item>": park the folder, then put an empty read-only FILE with the same name in its place,
# so CapCut cannot download or re-create that folder. Only 0-byte read-only files are ever removed (on undo).
function Test-Blocker([string]$p) { $f = Get-Item -LiteralPath $p -Force -EA SilentlyContinue; $f -and -not $f.PSIsContainer -and $f.Length -eq 0 -and ($f.Attributes -band [IO.FileAttributes]::ReadOnly) }
function Remove-Blocker([string]$p) { if (Test-Blocker $p) { $f = Get-Item -LiteralPath $p -Force; $f.Attributes = 'Normal'; Remove-Item -LiteralPath $p -Force; "unblocked: $p" } }

if ($ApplyAll) { $Items = Get-Content $manifest | ? { $_ -and -not $_.StartsWith('#') } }
if ($Apply -or $ApplyAll) {
    Stop-CapCut
    foreach ($i in $Items) {
        $block = $i.StartsWith('BLOCK ')
        $r = Resolve-Item ($i -replace '^BLOCK ', '')
        if ($block -and (Test-Blocker $r.Live)) { "already blocked: $($r.Live)"; continue }
        Move-Safe $r.Live $r.Parked
        if ($block) { New-Item -ItemType File -Path $r.Live -Force | Out-Null; (Get-Item -LiteralPath $r.Live).Attributes = 'ReadOnly'; "blocked: $($r.Live)" }
    }
}
if ($Undo) {
    Stop-CapCut
    foreach ($i in $Items) {
        $r = Resolve-Item ($i -replace '^BLOCK ', ''); Remove-Blocker $r.Live
        if (Test-Path -LiteralPath $r.Live) { "skip (already live): $($r.Live)" } else { Move-Safe $r.Parked $r.Live }
    }
}
if ($RestoreAll) {
    Stop-CapCut
    if (-not (Test-Path $removed)) { "nothing to restore"; return }
    Get-Content $manifest | ? { $_.StartsWith('BLOCK ') } | % { Remove-Blocker (Resolve-Item ($_ -replace '^BLOCK ', '')).Live }
    # Put back every parked file whose live path is free; newest parked copies of regrown caches stay parked.
    Get-ChildItem $removed -Recurse -File -Force | % {
        $rel = $_.FullName.Substring($removed.Length + 1); $live = Join-Path $root $rel
        if ($rel -match '\.\d{8}-\d{6}(\\|$)') { return }   # second parked copy of a regrown folder: leave parked
        if (-not (Test-Path -LiteralPath $live)) { New-Item -ItemType Directory -Force (Split-Path $live) | Out-Null; Move-Item -LiteralPath $_.FullName -Destination $live }
    }
    "restored files from $removed"
}
