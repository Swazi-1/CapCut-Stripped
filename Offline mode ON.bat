@echo off
title CapCut offline mode ON
net session >nul 2>&1
if errorlevel 1 (
  echo  Windows will ask for permission - click Yes.
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\offline.ps1" -On
echo.
echo  CapCut can no longer use the internet.
echo  To undo: run "Offline mode OFF.bat"
echo.
pause
