@echo off
title Make CapCut Lite
echo.
echo  Making CapCut Lite...
echo  (CapCut will be closed. Removed parts are deleted for good - reinstall CapCut to get them back.)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\lite.ps1" -ApplyAll >nul
echo  Compressing CapCut on disk (a few minutes; CapCut works the same, it just uses less space)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\compress.ps1"
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=\"$env:LOCALAPPDATA\CapCut\User Data\Config\updateInfo\"; if(Test-Path $f){ (Get-Content $f) -replace 'joinBeta=true','joinBeta=false' | Set-Content $f -Encoding ASCII }"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY="
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if defined PY (
  "%PY%" -I "%~dp0_files (don't touch)\patch_cards.py" memory >nul
  for %%W in ("%PY%") do set "PYW=%%~dpWpythonw.exe"
  set "PYF=%~dp0_files (don't touch)\capcut_lite.pyw"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\CapCut Lite.lnk'); $s.TargetPath=$env:PYW; $s.Arguments='\"'+$env:PYF+'\"'; $s.WorkingDirectory=Split-Path $env:PYF; $s.IconLocation=$env:LOCALAPPDATA+'\CapCut\Apps\CapCut.exe,0'; $s.Save()"
  echo  A "CapCut Lite" shortcut is on your desktop. Open CapCut with it to hide the AI cards and buttons.
) else (
  echo  (AI cards part skipped - needs Python. Everything else is done.)
)
echo  DONE! Open CapCut and try a quick export.
echo  Tip: in the export window, set Codec to H.264.
echo.
pause
