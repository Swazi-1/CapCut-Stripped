@echo off
title Undo CapCut Lite
echo.
echo  Putting normal CapCut back (CapCut will be closed)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\lite.ps1" -RestoreAll >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=\"$env:LOCALAPPDATA\CapCut\User Data\Config\updateInfo\"; if(Test-Path $f){ (Get-Content $f) -replace 'joinBeta=false','joinBeta=true' | Set-Content $f -Encoding ASCII }"
echo.
echo  DONE! CapCut is back to normal.
echo  If you turned on offline mode, also run "Offline mode OFF.bat".
echo.
pause
