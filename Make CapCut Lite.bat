@echo off
title Make CapCut Lite
echo.
echo  Making CapCut Lite...
echo  (CapCut will be closed. Nothing is deleted - removed parts are kept so you can undo.)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\lite.ps1" -ApplyAll >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=\"$env:LOCALAPPDATA\CapCut\User Data\Config\updateInfo\"; if(Test-Path $f){ (Get-Content $f) -replace 'joinBeta=true','joinBeta=false' | Set-Content $f -Encoding ASCII }"
echo  DONE! Open CapCut and try a quick export.
echo  Tip: in the export window, set Codec to H.264.
echo.
pause
