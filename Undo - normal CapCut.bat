@echo off
title Undo CapCut Lite
echo.
echo  Putting normal CapCut back (CapCut will be closed)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.Path -like \"$env:LOCALAPPDATA\CapCut\*\" } | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep 2"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY="
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if defined PY "%PY%" -I "%~dp0_files (don't touch)\patch_cards.py" revert >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item ([Environment]::GetFolderPath('Desktop')+'\CapCut Lite.lnk') -ErrorAction SilentlyContinue"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\lite.ps1" -RestoreAll >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=\"$env:LOCALAPPDATA\CapCut\User Data\Config\updateInfo\"; if(Test-Path $f){ (Get-Content $f) -replace 'joinBeta=false','joinBeta=true' | Set-Content $f -Encoding ASCII }"
echo.
echo  DONE! CapCut is back to normal.
echo  If you turned on offline mode, also run "Offline mode OFF.bat".
echo.
pause
