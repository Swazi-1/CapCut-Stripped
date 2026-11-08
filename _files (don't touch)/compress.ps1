# CapCut Lite: compress (or with -Undo uncompress) CapCut on disk with Windows' own LZX compression.
# Files keep the same content; only the space they use on disk shrinks. Shows a progress bar by bytes done.
param([switch]$Undo, [string[]]$Roots)
if (-not $Roots) {
    $Roots = @("$env:LOCALAPPDATA\CapCut\Apps")
}
$Roots = @($Roots | Where-Object { Test-Path -LiteralPath $_ })
$size = @{}; $total = [double]0
foreach ($r in $Roots) {
    Get-ChildItem -LiteralPath $r -Recurse -File -Force -ErrorAction SilentlyContinue |
        ForEach-Object { $size[$_.FullName.ToLower()] = $_.Length; $total += $_.Length }
}
if ($total -le 0) { return }
$script:done = [double]0
$width = 30
function Show-Bar {
    $p = [math]::Min(100, [int](100 * $script:done / $total))
    $n = [int]($width * $p / 100)
    [Console]::Write("`r  [" + ('#' * $n) + ('-' * ($width - $n)) + ("] {0,3}%  {1,5:N0} / {2:N0} MB " -f $p, ($script:done / 1MB), ($total / 1MB)))
}
Show-Bar
foreach ($r in $Roots) {
    if ($Undo) { $ca = @('/u', "/s:$r", '/exe', '/i') } else { $ca = @('/c', "/s:$r", '/exe:lzx', '/i') }
    $dir = $r
    & compact.exe @ca | ForEach-Object {
        $line = [string]$_
        if ($line -match '([A-Za-z]:\\.*?)\\?\s*$' -and $line -notmatch '\[') { $dir = $matches[1]; return }
        if ($line -match '^(.+?)\s+\d+\s*:\s*\d+\s*=' -or $line -match '^(.+?)\s+\[') {
            $k = (Join-Path $dir $matches[1].Trim()).ToLower()
            if ($size.ContainsKey($k)) { $script:done += $size[$k]; $size.Remove($k); Show-Bar }
        }
    }
}
$script:done = $total; Show-Bar
[Console]::WriteLine()
